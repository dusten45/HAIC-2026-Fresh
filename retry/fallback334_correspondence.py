"""Posthoc correspondence audit using actual fixture membership at birth.

This is a diagnostic subset, not a fitted association gate or policy change.
Unresolved detections are retained as unknown; future truth never repairs IDs.
"""
import argparse
import hashlib
import json
import math
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save


def rot(a):
    c,s=math.cos(a),math.sin(a);return np.array([[c,-s],[s,c]])
def body(gt):
    h=gt['hull'];return np.array([rot(-h['angle'])@(rot(o['body']['angle'])@np.array(o['fixture']['geometry']['pos'])+o['body']['position']-h['position']) for o in gt['obstacles']])
def stats(values,roads):
    if not values:return dict(count=0)
    v=np.array(values,float);rr=np.array(roads);w=np.array([1/(len(set(rr))*sum(rr==r)) for r in rr]);order=np.argsort(v,kind='stable');cum=np.cumsum(w[order]);return dict(count=len(v),roads=len(set(rr)),mean=float(w@v),RMSE=float(np.sqrt(w@(v*v))),p95=float(v[order[min(np.searchsorted(cum,.95),len(v)-1)]]),p99=float(v[order[min(np.searchsorted(cum,.99),len(v)-1)]]),maximum=float(v.max()))


def run(R):
    D=R/'stage334';assert not (D/'fixture-birth-audit-private.json').exists();p=read(D/'plan.json');start,cpu=time.perf_counter(),time.process_time();source=read(D/'correspondence-private.json');meta={(x['key'],x['index']):x for x in source['routing']};paired=[];sequence=[];frames=[];coverage=[];births=[]
    for case in p['cases']:
        F=D/case['key'];records={mode:[json.loads(s) for s in (F/(mode+'-private.jsonl')).read_text().splitlines()] for mode in ['OFF','ON']};gt={int(k):v for k,v in read(F/'GT-private.json').items()};ids={'OFF':[],'ON':[]};integral={'OFF':{},'ON':{}}
        for i in range(len(records['OFF'])):
            m=meta[(case['key'],i)];current=body(gt[i]) if i in gt else None;r=records['OFF'][i]
            if i and i-1 in gt and current is not None:
                for j,item in enumerate(ids['OFF']):
                    coverage.append(dict(**m,resolved=item is not None))
                    if item is not None:
                        target=current[item['id']];paired.append(dict(**m,age=r['tracker']['before'][j][3],OFF=float(np.linalg.norm(np.array(r['transported'][j][:2])-target)),ON=float(np.linalg.norm(np.array(r['paired_transported'][j][:2])-target))))
            for mode in ['OFF','ON']:
                r=records[mode][i];after=[]
                for origin in r['lineage']:
                    if origin>=0:item=ids[mode][origin]
                    elif current is None:item=None
                    else:
                        point=r['tracker']['direct'][-origin-1][:2];dist=np.linalg.norm(current-point,axis=1);radii=np.array([o['fixture']['radius'] for o in gt[i]['obstacles']]);inside=np.flatnonzero(dist<=radii)
                        item=dict(id=int(inside[0]),uid=(i,-origin-1)) if len(inside)==1 else None
                        births.append(dict(**m,mode=mode,unique_fixture_compatible=len(inside)==1,no_fixture_compatible=len(inside)==0,multiple_fixture_compatible=len(inside)>1,nearest_distance=float(dist.min())))
                    after.append(item)
                ids[mode]=after
                if current is None:continue
                counts={};fresh=set()
                for point,item in zip(r['tracker']['after'],after):
                    if item is None:continue
                    identity=item['id'];counts[identity]=counts.get(identity,0)+1
                    if point[3]==0:fresh.add(identity)
                    error=float(np.linalg.norm(np.array(point[:2])-current[identity]));uid=item['uid'];integral[mode][uid]=integral[mode].get(uid,0.)+error*.08
                    sequence.append(dict(**m,mode=mode,age=point[3],error=error,cumulative=integral[mode][uid]))
                pixels=current*np.array([1.3608,-1.701])+np.array([41.542,62.4475]);eligible=set(np.flatnonzero((pixels[:,0]>=0)&(pixels[:,0]<84)&(pixels[:,1]>=0)&(pixels[:,1]<61)).tolist());unknown=sum(v is None for v in after);missing=len(eligible-set(counts))
                frames.append(dict(**m,mode=mode,duplicates=sum(max(v-1,0) for v in counts.values()),unknown_points=unknown,geometric_ROI_instances=len(eligible),no_known_track_upper_bound=missing,no_track_lower_bound=max(0,missing-unknown),no_direct_fixture_supported=len(eligible-fresh),retained_without_direct=len((eligible&set(counts))-fresh)))
    output={};perroad={}
    for group in ['original6','N2']:
        output[group]={}
        for label,select in [('all',lambda r:True),('fallback',lambda r:not r['optical']),('optical',lambda r:r['optical']),('fallback_fresh',lambda r:not r['optical'] and r['age']==0),('fallback_aged',lambda r:not r['optical'] and r['age']>0),('fallback_precontact',lambda r:not r['optical'] and not r['post']),('fallback_postcontact',lambda r:not r['optical'] and r['post'])]:
            pp=[r for r in paired if r['group']==group and not r['duplicate'] and select(r)];ss=[r for r in sequence if r['group']==group and not r['duplicate'] and select(r)];ff=[r for r in frames if r['group']==group and not r['duplicate'] and (label=='all' or label=='fallback' and not r['optical'] or label=='optical' and r['optical'])]
            output[group][label]=dict(paired={mode:stats([r[mode] for r in pp],[r['road'] for r in pp]) for mode in ['OFF','ON']},sequential={mode:stats([r['error'] for r in ss if r['mode']==mode],[r['road'] for r in ss if r['mode']==mode]) for mode in ['OFF','ON']},frame_totals={mode:{key:sum(r[key] for r in ff if r['mode']==mode) for key in ['duplicates','unknown_points','geometric_ROI_instances','no_known_track_upper_bound','no_track_lower_bound','no_direct_fixture_supported','retained_without_direct']} for mode in ['OFF','ON']})
        c=[r for r in coverage if r['group']==group and not r['duplicate']];bb=[r for r in births if r['group']==group and not r['duplicate'] and r['mode']=='OFF'];output[group]['coverage']=dict(candidate_previous_points=len(c),fixture_birth_supported_previous_points=sum(r['resolved'] for r in c),birth_detections_with_GT=len(bb),unique_fixture_compatible_births=sum(r['unique_fixture_compatible'] for r in bb),no_fixture_compatible_births=sum(r['no_fixture_compatible'] for r in bb),multiple_fixture_compatible_births=sum(r['multiple_fixture_compatible'] for r in bb))
    for road in sorted(set(c['road'] for c in p['cases'])):
        rr=[r for r in paired if r['road']==road and not r['duplicate'] and not r['optical']];perroad[road]={mode:stats([r[mode] for r in rr],[r['road'] for r in rr]) for mode in ['OFF','ON']}
    age_metrics={group:{str(age):{mode:stats([r['error'] for r in sequence if r['group']==group and not r['duplicate'] and r['age']==age and r['mode']==mode],[r['road'] for r in sequence if r['group']==group and not r['duplicate'] and r['age']==age and r['mode']==mode]) for mode in ['OFF','ON']} for age in range(9)} for group in ['original6','N2']}
    integral_metrics={group:{mode:stats([r['cumulative'] for r in sequence if r['group']==group and not r['duplicate'] and r['mode']==mode],[r['road'] for r in sequence if r['group']==group and not r['duplicate'] and r['mode']==mode]) for mode in ['OFF','ON']} for group in ['original6','N2']}
    save(D/'fixture-birth-audit-private.json',dict(posthoc=True,criterion='Detection center lies within exactly one actual captured circular fixture at birth, using its physical radius, not a fitted distance/confidence threshold. Then fixed identity propagates through existing source lineage; otherwise unresolved forever.',not_visibility_or_oracle=True,aggregate=output,perroad_paired_fallback=perroad,age_errors=age_metrics,cumulative_error_m_s=integral_metrics,cost=dict(wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,new_native_actions=0,new_actor_calls=0,new_learning_fits=0,new_source_physics_ticks=0)))
    save(D/'fixture-birth-points-private.json',dict(paired=paired,sequence=sequence,frames=frames,births=births));print(json.dumps(dict(coverage={g:output[g]['coverage'] for g in output},fallback={g:output[g]['fallback']['paired'] for g in output})),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);run(p.parse_args().private_root)
