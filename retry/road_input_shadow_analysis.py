"""Saved-data-only spatial/temporal analysis of paired road-input captures."""
import argparse
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR','/tmp/haic-road-shadow-mpl')
os.environ.setdefault('XDG_CACHE_HOME','/tmp/haic-road-shadow-cache')
Path(os.environ['XDG_CACHE_HOME']).mkdir(parents=True,exist_ok=True)
import cv2
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np


def components(mask):
    n,labels,stats,_=cv2.connectedComponentsWithStats(mask.astype(np.uint8),connectivity=4)
    return {'count':n-1,'areas_descending':sorted(stats[1:,cv2.CC_STAT_AREA].tolist(),reverse=True)[:8]}


def summarize(npz,row):
    P=npz['pixel_raw_road'].astype(bool);V=npz['visible_GT'].astype(bool);A=npz['full_GT'].astype(bool)
    fp=P&~V;fn=V&~P;roi=np.zeros((84,84),bool);roi[24:57,3:81]=True
    boundary=cv2.morphologyEx(V.astype(np.uint8),cv2.MORPH_GRADIENT,np.ones((3,3),np.uint8)).astype(bool)
    occlusion=cv2.dilate((A&~V).astype(np.uint8),np.ones((3,3),np.uint8)).astype(bool)
    hud=npz['HUD'].astype(bool) if 'HUD' in npz.files else np.indices((84,84))[0]>=74
    image=npz['observation'][-1];details={}
    for name,mask in [('full',np.ones_like(roi)),('control_ROI',roi),('visible_boundary',boundary),('occlusion_vicinity',occlusion),('HUD',hud)]:
        details[name]={'false_road':int((fp&mask).sum()),'missing_road':int((fn&mask).sum())}
    error=fp|fn;gray=image[fn&roi]
    details['missing_ROI_gray_u8']={'count':len(gray),'min':int(gray.min()) if len(gray) else None,'median':float(np.median(gray)) if len(gray) else None,'max':int(gray.max()) if len(gray) else None,'below_or_at_original_lower_bound':int(np.count_nonzero(gray/255.<=.32)),'above_or_at_original_upper_bound':int(np.count_nonzero(gray/255.>=.47))}
    details['raw_error_components']=components(error&roi)
    for arm in ['pixel','visible_GT_shadow']:
        closed=npz[arm+'_closed_road'];allowed=npz[arm+'_allowed'];details[arm]={'closed_components':components(closed&roi),'allowed_components':components(allowed),'start':row[arm]['start'],'connected_goal':row[arm]['connected_goal'],'target':row[arm]['target'],'action':row[arm]['action'],'labels_defined':row[arm]['start'] is not None}
    details.update(step=row['step'],before_time=row['before_time'],after_time=row['after_time'],damage_before=row['truth_before']['damage'],damage_after=row['truth_after']['damage'],collision_after_action=row['collision_after_action'],action_delta=row['metrics']['action_delta'],regions_nonexclusive=True,HUD_fallback='native captured coverage' if 'HUD' in npz.files else 'bottom slab rows>=74 only; no extending-bar coverage claim',IoU_is_not_causality=True)
    return details


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--case-dir',type=Path,required=True)
    D=parser.parse_args().case_dir.resolve();rows=[json.loads(x) for x in (D/'paired-trace.jsonl').read_text().splitlines()];by_step={r['step']:r for r in rows};summaries=[]
    for path in sorted(D.glob('paired-step-*.npz')):
        step=int(path.stem.split('-')[-1]);summaries.append(summarize(np.load(path),by_step[step]))
    chosen=[s for s in [24,145,212,213,218] if (D/f'paired-step-{s:04d}.npz').exists()]
    fig,axes=plt.subplots(len(chosen),3,figsize=(11,3.0*len(chosen)),squeeze=False)
    for i,step in enumerate(chosen):
        a=np.load(D/f'paired-step-{step:04d}.npz');r=by_step[step];P=a['pixel_raw_road'].astype(bool);V=a['visible_GT'].astype(bool)
        ax=axes[i,0];ax.imshow(a['observation'][-1],cmap='gray',vmin=0,vmax=255)
        for arm,color in [('pixel','#f04ea0'),('visible_GT_shadow','#00bed1')]:
            path=np.asarray(r[arm]['path'])
            if len(path):ax.plot(42+1.3608*path[:,0],63-1.701*path[:,1],color=color,lw=1.2,label=arm)
            target=r[arm]['target']
            if target is not None:ax.scatter([42+1.3608*target[0]],[63-1.701*target[1]],s=45,marker='x',color=color)
        ax.set_title(f'Step {step}, pre t={r["before_time"]:.2f}s\nSteer delta={r["metrics"]["action_delta"][0]:+.5f}',fontsize=9);ax.legend(fontsize=6,loc='lower left')
        e=np.zeros((84,84),np.uint8);e[P&~V]=1;e[V&~P]=2;axes[i,1].imshow(e,cmap=ListedColormap(['#eeeeee','#d94040','#3584d4']),vmin=0,vmax=2);axes[i,1].set_title('Raw error\nRed=false road, blue=missing road',fontsize=9)
        p=a['pixel_allowed'].astype(bool);v=a['visible_GT_shadow_allowed'].astype(bool);e=np.zeros((84,84),np.uint8);e[p&v]=1;e[p&~v]=2;e[v&~p]=3;axes[i,2].imshow(e,cmap=ListedColormap(['#eeeeee','#aaa','#f04ea0','#00bed1']),vmin=0,vmax=3);axes[i,2].set_title('Allowed\nGray=both, pink=pixel, cyan=GT',fontsize=9)
        for ax in axes[i]:ax.axhline(61,color='orange',ls=':',lw=.7);ax.set_xlim(0,83);ax.set_ylim(83,0);ax.set_xticks([0,42,83]);ax.set_yticks([0,24,56,61,83]);ax.set_aspect('equal')
    fig.suptitle('Original observation / isolated visible-GT shadow; only fixed original actions executed',fontsize=11);fig.tight_layout();fig.savefig(D/'paired-scenes.png',dpi=140);plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(10,6),sharex=True);steps=[r['step'] for r in rows]
    axes[0].plot(steps,[r['metrics']['false_road_cells'] for r in rows],label='raw false road');axes[0].plot(steps,[r['metrics']['missing_road_cells'] for r in rows],label='raw missing road');axes[0].legend();axes[0].set_ylabel('Full-image cells')
    axes[1].plot(steps,[r['metrics']['closed_road_difference_cells'] for r in rows],label='after crop/close');axes[1].plot(steps,[r['metrics']['allowed_difference_cells'] for r in rows],label='allowed');axes[1].legend();axes[1].set_ylabel('Different cells')
    axes[2].plot(steps,[r['metrics']['action_delta'][0] for r in rows]);axes[2].set_ylabel('Shadow - original steer');axes[2].set_xlabel('Fixed original action index')
    contact=next((r['step'] for r in rows if r['collision_after_action']),None)
    for ax in axes:
        if contact:ax.axvline(contact,color='red',ls='--',label='first contact occurs after this action')
        ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(D/'temporal-differences.png',dpi=150);plt.close(fig)
    report={'captured_scene_count':len(summaries),'selected_figure_steps':chosen,'first_contact_after_action':contact,'spatial_scenes':summaries,'no_new_policy_or_env_calls':True,'regions_nonexclusive':True,'labels_None_not_a_component_result':True,'closed_road_representation':'distance>0 reproduces the original binary closed road','causal_limit':'Same-state one-step shadows do not show closed-loop rescue or identify collision cause; raw mask IoU is insufficient.'}
    (D/'spatial-analysis.json').write_text(json.dumps(report,indent=2)+'\n')
    for name in ['spatial-analysis.json','paired-scenes.png','temporal-differences.png']:(D/name).chmod(0o600)
    print(json.dumps({'scene_count':len(summaries),'selected':[s for s in summaries if s['step'] in chosen]}))


if __name__=='__main__':main()
