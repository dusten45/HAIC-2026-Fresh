"""Saved-data provenance and projection audit, with no simulator imports."""
import argparse
import json
import time
from pathlib import Path
import cv2
import numpy as np
from retry.path271_run import read,save
from retry.lineage339_stage import verify


def rotation(angle):
    c,s=np.cos(angle),np.sin(angle);return np.array([[c,-s],[s,c]])


def centers(gt):
    hull=gt['hull']
    return np.array([rotation(-hull['angle'])@(rotation(o['body']['angle'])@np.array(o['fixture']['geometry']['pos'])+np.array(o['body']['position'])-hull['position']) for o in gt['obstacles']])


def pixels(points):return np.asarray(points)*np.array([1.3608,-1.701])+np.array([41.542,62.4475])


def components(frame):
    image=frame.astype(np.float32)/255
    road=((image>.32)&(image<.47)).astype(np.uint8);road[61:]=0
    closed=cv2.morphologyEx(road,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    holes=((closed!=0)&(road==0)&(image>=.64)&(image<=.71)).astype(np.uint8);holes[61:]=0
    count,labels,stats,centroids=cv2.connectedComponentsWithStats(holes,connectivity=8)
    result=[]
    for i in range(1,count):
        x,y,w,h,area=map(int,stats[i]);cx,cy=map(float,centroids[i])
        if not (3<=area<=30 and 2<=w<=9 and 2<=h<=9):continue
        yy,xx=np.where(labels==i)
        result.append(dict(component_label=i,bbox=[x,y,w,h],area=area,centroid=[cx,cy],
            metric=[(cx-41.542)/1.3608,(62.4475-cy)/1.701,1.2],
            pixel_xy=np.stack([xx,yy],axis=1).tolist(),gray_values=frame[yy,xx].tolist(),
            touches_top=bool(y==0),HUD_excluded=bool(y+h<=61),
            source_condition='Non-road bright pixels filled by7x7road closing; all accepted detector conditions reproduced.'))
    return result


def track(rows):
    tags=[];prior=[];records=[];births={};max_error=0.
    for r in rows:
        step=r['step'];t=r['tracker'];assert t['before']==prior
        transformed=[];removed=[]
        for index,(point,tag) in enumerate(zip(t['before'],tags)):
            x,y,radius,age=point
            if t['affine'] is not None:
                pixel=np.asarray(t['affine'])@np.array([41.542+1.3608*x,62.4475-1.701*y,1])
                x,y=(pixel[0]-41.542)/1.3608,(62.4475-pixel[1])/1.701
                mode='accepted_optical'
            else:
                delta=.08*(t['previous_yaw']+t['current_yaw'])/2
                offset=np.array([x,y])-np.array([0.,t['current_speed']*.08]);c,s=np.cos(delta),np.sin(delta)
                x,y=float(c*offset[0]+s*offset[1]),float(-s*offset[0]+c*offset[1]);mode='frozen_HUD_fallback'
            eligible=age<8 and abs(x)<=35 and -5<=y<=35
            item=dict(tag=tag,source_index=index,before=point,predicted=[float(x),float(y),radius,age+1],mode=mode,age_gate=age<8,spatial_gate=bool(abs(x)<=35 and -5<=y<=35))
            if eligible:transformed.append(item)
            else:removed.append(dict(item,reason='age_expiry' if age>=8 else 'spatial_expiry'))
        associations=[]
        for j,(x,y,radius) in enumerate(t['direct']):
            uid=f'{step}:{j}';kept=[]
            for item in transformed:
                distance=float(np.hypot(item['predicted'][0]-x,item['predicted'][1]-y))
                if distance>2:kept.append(item)
                else:
                    associations.append(dict(old_tag=item['tag'],new_tag=uid,distance_m=distance,rule='Delete prior within2m; append current age0, no persistent-object-ID matching.'))
            transformed=kept+[dict(tag=uid,source_index=None,before=None,predicted=[x,y,radius,0],mode='direct_birth')]
            births[uid]=dict(step=step,direct_index=j,point=[x,y,radius])
        actual=np.asarray(t['after'],float).reshape(-1,4);expected=np.asarray([q['predicted'] for q in transformed],float).reshape(-1,4)
        assert actual.shape==expected.shape
        error=float(np.max(np.abs(actual-expected))) if actual.size else 0.;max_error=max(max_error,error);assert error<1e-10,(step,error)
        tags=[q['tag'] for q in transformed];prior=t['after']
        records.append(dict(step=step,tags=tags,points=transformed,expiries=removed,associations=associations,optical_reason=t['optical_reason'],affine=t['affine'],affine_determinant=None if t['affine'] is None else float(np.linalg.det(np.asarray(t['affine'])[:,:2]))))
    return dict(records=records,births=births,maximum_reconstruction_error=max_error)


def run(R):
    D=R/'stage339';p=verify(R,True);assert read(D/'reproduction-receipt.json')['passed'] and read(D/'diagnostic-receipt.json')['passed'];assert not (D/'audit-private.json').exists()
    start,cpu=time.perf_counter(),time.process_time();all_data={};all_lineage={};details=[];comparisons=[]
    for stage in [337,338]:
        rows=[json.loads(s) for s in (R/f'stage{stage}/B/trace-private.jsonl').read_text().splitlines()];frames=np.load(R/f'stage{stage}/B/frames-actions-private.npz')['frames_uint8'];lineage=track(rows);all_lineage[str(stage)]=lineage
        for r in rows:
            comp=components(frames[r['step']-1]);assert [q['metric'] for q in comp]==r['tracker']['direct']
        selected_births={tag:lineage['births'][tag] for tag in ['121:0','123:0','124:0']}
        for tag,birth in selected_births.items():
            step=birth['step'];r=rows[step-1];gt=centers(r['pre_physical']);point=np.array(birth['point'][:2]);dist=np.linalg.norm(gt-point,axis=1);c=components(frames[step-1])[birth['direct_index']]
            projected=pixels(gt);pixel_dist=np.linalg.norm(projected-np.array(c['centroid']),axis=1)
            radii=[o['fixture']['radius'] for o in r['pre_physical']['obstacles']]
            birth.update(component=c,nearest_object=int(dist.argmin()),nearest_GT_distance_m=float(dist.min()),contact_object2_distance_m=float(dist[2]),nearest_projected_center_error_px=float(pixel_dist.min()),fixture_center_compatible_ids=[j for j,d in enumerate(dist) if d<=radii[j]],projected_GT_centers=projected.tolist())
        life=[]
        for r,lr in zip(rows,lineage['records']):
            if not 121<=r['step']<=134:continue
            for tag,point in zip(lr['tags'],r['tracker']['after']):
                if tag not in ['121:0','124:0']:continue
                gt=centers(r['pre_physical']);dist=np.linalg.norm(gt-np.array(point[:2]),axis=1)
                life.append(dict(step=r['step'],tag=tag,point=point,pixel=pixels(np.array(point[:2])).tolist(),nearest_GT_distance_m=float(dist.min()),nearest_object=int(dist.argmin()),optical_reason=lr['optical_reason']))
        for record in read(D/f'diagnostic/{stage}/probes-private.json'):
            v=record['probe']['variants'];base=v['original'];step=record['step'];row=dict(stage=stage,step=step,variants={})
            for mode,value in v.items():
                if mode=='original':continue
                f=np.asarray(value['features']);bf=np.asarray(base['features']);changed=np.flatnonzero(f!=bf).tolist()
                row['variants'][mode]=dict(removed_count=len(base['hazards'])-len(value['hazards']),candidates_changed=value['candidates']!=base['candidates'],connection_evaluation_changed=value['connection_evaluation']!=base['connection_evaluation'],path_changed=value['path']!=base['path'],target_changed=value['target']!=base['target'],steering_changed=value['action'][0]!=base['action'][0],pedals_changed=value['action'][1:]!=base['action'][1:],changed_feature_indices=changed,feature_delta=(f-bf).tolist(),action_delta=(np.asarray(value['action'])-base['action']).tolist(),original_action=base['action'],variant_action=value['action'],original_target=base['target'],variant_target=value['target'],original_candidate_count=len(base['candidates']),variant_candidate_count=len(value['candidates']),original_selected=base['connection_evaluation']['selected_index'],variant_selected=value['connection_evaluation']['selected_index'])
            comparisons.append(row)
        all_data[str(stage)]=dict(births=selected_births,unresolved_lives=life,all_tracker_updates_reconstructed=len(rows),all_detector_outputs_reconstructed=len(rows),lineage_reconstruction_max_error=lineage['maximum_reconstruction_error'])
    # Private image evidence only: original saved grayscale, detected pixels and
    # analytic projected fixture outlines; no new rendering or source rollout.
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Ellipse
    fig,axes=plt.subplots(2,3,figsize=(12,8),layout='constrained')
    for col,step in enumerate([121,123,124]):
        rows=[json.loads(s) for s in (R/'stage337/B/trace-private.jsonl').read_text().splitlines()];frames=np.load(R/'stage337/B/frames-actions-private.npz')['frames_uint8'];frame=frames[step-1];gt=centers(rows[step-1]['pre_physical'])
        for ax in axes[:,col]:
            ax.imshow(frame,cmap='gray',vmin=0,vmax=255,interpolation='nearest')
            for j,(x,y) in enumerate(pixels(gt)):
                if -10<x<94 and -10<y<94:
                    radius=rows[step-1]['pre_physical']['obstacles'][j]['fixture']['radius'];ax.add_patch(Ellipse((x,y),2*radius*1.3608,2*radius*1.701,fill=False,edgecolor='lime',linewidth=1));ax.text(x,y,str(j),color='lime',fontsize=8)
            for j,c in enumerate(components(frame)):
                xy=np.array(c['pixel_xy']);ax.scatter(xy[:,0],xy[:,1],s=18,facecolors='none',edgecolors='magenta');ax.text(*c['centroid'],str(j),color='magenta')
        axes[0,col].set_title(f'Saved input {step}; green: projected fixtures')
        axes[1,col].set_xlim(10,48);axes[1,col].set_ylim(15,-2);axes[1,col].set_title('Top-edge crop; magenta: detector component')
    fig.savefig(D/'birth-evidence-private.png',dpi=160);plt.close(fig);(D/'birth-evidence-private.png').chmod(0o600)
    # Class colors are an ambiguity check, not an RGB reconstruction.
    palette={name:int(cv2.cvtColor(np.array([[color]],np.uint8),cv2.COLOR_RGB2GRAY)[0,0]) for name,color in dict(road=[102,102,102],background_grass=[102,204,102],bright_grass=[102,230,102],obstacle=[255,165,0],white_border=[255,255,255],red_border=[255,0,0]).items()}
    verify(R,True)
    output=dict(stage=339,data=all_data,comparisons=comparisons,palette_gray=palette,projection='Source window1000x800, zoom16.2, flip799-y, state96x96 then84x84 pixel-center mapping: x=41.542+1.3608*body_x,y=62.4475-1.701*body_y. Analytic no-fit mapping; rasterization/filtering centroid uncertainty remains.',
        limits=['Saved grayscale only, no pre-resize RGB or pixel semantic labels. Bright grass and orange obstacle share detector intensity band; exact rendered material unresolved.',
                'Birth121 and124 components touch upper image boundary; real obstacle birth123 also touches it. No edge suppression rule justified.',
                'GT correspondence only diagnoses geometry. No GT passed to routing/actor, no real visibility or occlusion annotation.',
                'Counterfactuals are separate frozen-scene clone calls, never an actual continuation. Paths/controls are diagnostic surrogates.'],
        cost=dict(new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu))
    save(D/'lineage-private.json',all_lineage);save(D/'audit-private.json',output)
    print(json.dumps(dict(reconstructed_inputs=369,palette_gray=palette,comparisons=len(comparisons),cost=output['cost'])),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);run(a.parse_args().private_root)
