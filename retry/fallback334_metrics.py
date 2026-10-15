"""Saved tracker correspondence evaluation; no simulator or policy world.

Nearest identities are heuristic, fixed at previous state/birth, never repaired
using future truth. In-frame missing detection is not called actual occlusion.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import numpy as np


def read(p):return json.loads(Path(p).read_text())
def save(p,v):
    p=Path(p);p.write_text(json.dumps(v,allow_nan=False,indent=2)+'\n');p.chmod(0o600)
def rotation(a):
    c,s=math.cos(a),math.sin(a);return np.array([[c,-s],[s,c]])
def centers(gt):
    h=gt['hull'];r=rotation(-h['angle']);points=[]
    for o in gt['obstacles']:
        absolute=rotation(o['body']['angle'])@np.array(o['fixture']['geometry']['pos'])+o['body']['position'];points.append(r@(absolute-np.array(h['position'])))
    return np.array(points)
def match(p,points):
    distance=np.linalg.norm(points-np.array(p),axis=1);order=np.argsort(distance,kind='stable');return int(order[0]),float(distance[order[0]]),float(distance[order[1]]-distance[order[0]])
def summary(values,roads):
    if not values:return dict(count=0)
    v=np.array(values,float);rr=np.array(roads);unique=set(rr);w=np.array([1/(len(unique)*sum(rr==r)) for r in rr]);order=np.argsort(v,kind='stable');cum=np.cumsum(w[order])
    return dict(count=len(v),roads=len(unique),mean=float(w@v),RMSE=float(np.sqrt(w@(v*v))),p95=float(v[order[min(np.searchsorted(cum,.95),len(v)-1)]]),p99=float(v[order[min(np.searchsorted(cum,.99),len(v)-1)]]),maximum=float(v.max()))


def run(R,package):
    D=R/'stage334';p=read(D/'plan.json');assert not (D/'metrics-private.json').exists();sys.path.insert(0,str(package))
    import retry.connected_agent as routing
    from retry.route_agent import route_target
    from retry.cem294_constants import LOOKAHEAD_SCALE,STEERING_GAIN
    start,cpu=time.perf_counter(),time.process_time();paired=[];sequential=[];frames=[];trajectory=[];seen=set();routing_calls=0;details=[]
    def steer(image,hazards,features):
        nonlocal routing_calls
        path=[list(map(float,z)) for z in routing.connected_route(image,[h[:3] for h in hazards],speed=features[3],previous_steer=features[7])];routing_calls+=1;target=route_target(path,features[3],LOOKAHEAD_SCALE)
        if target is None:return path,float(np.float32(features[7]))
        x,y=target;curvature=2*x/max(x*x+y*y,1e-6);s=.8*float(np.clip(np.arctan(3.24*curvature*STEERING_GAIN),-.4,.4))+.2*features[7];return path,float(np.float32(s))
    for case in p['cases']:
        F=D/case['key'];off=[json.loads(s) for s in (F/'OFF-private.jsonl').read_text().splitlines()];on=[json.loads(s) for s in (F/'ON-private.jsonl').read_text().splitlines()];gt={int(k):v for k,v in read(F/'GT-private.json').items()};obs=np.load(case['pixels'])['observations'];original=[json.loads(s) for s in (Path(case['folder'])/'trace-private.jsonl').read_text().splitlines()];first=next((r['step'] for r in original if r['collision']),None)
        identities={'OFF':[],'ON':[]};cumulative={'OFF':{},'ON':{}};counts=collections.Counter();ages={'OFF':collections.Counter(),'ON':collections.Counter()}
        for i,(a,b) in enumerate(zip(off,on)):
            ta,tb=a['tracker'],b['tracker'];current=centers(gt[i]) if i in gt else None;previous=centers(gt[i-1]) if i-1 in gt else None
            signature=hashlib.sha256((obs[i-1].tobytes() if i else b'')+obs[i].tobytes()+json.dumps(ta['before'],sort_keys=True).encode()).hexdigest();duplicate=case['group']=='N2' and signature in seen
            if case['group']=='N2':seen.add(signature)
            shared=dict(key=case['key'],road=case['road'],group=case['group'],index=i,duplicate=duplicate,optical=ta['affine'] is not None,post=first is not None and i>=first,actual_contact_interval=bool(i and original[i-1]['collision']))
            counts['frames']+=1;counts['optical_OFF']+=ta['affine'] is not None;counts['optical_ON']+=tb['affine'] is not None;counts['fallback_with_points_OFF']+=ta['affine'] is None and bool(ta['before']);counts['fallback_with_points_ON']+=tb['affine'] is None and bool(tb['before']);counts['both_optical']+=ta['affine'] is not None and tb['affine'] is not None;counts['optical_eligibility_difference']+=(ta['optical_reason']=='no_hazards')!=(tb['optical_reason']=='no_hazards');counts['sequential_path_changed']+=a['pixel_path']!=b['pixel_path'];counts['sequential_steering_changed']+=a['action'][0]!=b['action'][0]
            if ta['affine'] is not None and tb['affine'] is not None:assert ta['affine']==tb['affine']
            same=a['paired_ON']==ta['after'];pairpath=a['pixel_path'];pairsteer=a['action'][0]
            if not same:
                original_path,original_steer=steer(obs[i,-1],ta['after'],a['features']);assert original_path==a['pixel_path'] and original_steer==a['action'][0],(case['key'],i,'route readout reproduction')
                pairpath,pairsteer=steer(obs[i,-1],a['paired_ON'],a['features'])
            counts['single_interval_path_changed']+=pairpath!=a['pixel_path'];counts['single_interval_steering_changed']+=pairsteer!=a['action'][0]
            if i and previous is not None and current is not None:
                for j,h in enumerate(ta['before']):
                    identity,error,gap=match(h[:2],previous);ea=float(np.linalg.norm(np.array(a['transported'][j][:2])-current[identity]));eb=float(np.linalg.norm(np.array(a['paired_transported'][j][:2])-current[identity]));paired.append(dict(**shared,identity=identity,age=h[3],previous_association_error=error,nearest_second_margin=gap,OFF_error=ea,ON_error=eb))
            for mode,record in [('OFF',a),('ON',b)]:
                ids=[];birthmeta=[]
                for j,origin in enumerate(record['lineage']):
                    if origin>=0:
                        assert origin<len(identities[mode]);item=identities[mode][origin]
                    else:
                        di=-origin-1;point=record['tracker']['direct'][di]
                        if current is None:item=None
                        else:
                            identity,error,gap=match(point[:2],current);item=dict(identity=identity,birth=i,birth_error=error,margin=gap,uid=(i,di))
                    ids.append(item)
                assert len(ids)==len(record['tracker']['after']);identities[mode]=ids;known=collections.Counter();fresh=set()
                for hazard,item in zip(record['tracker']['after'],ids):
                    ages[mode][str(int(hazard[3]))]+=1
                    if item is None:counts['unknown_identity_points_'+mode]+=1;continue
                    if current is None:continue
                    identity=item['identity'];known[identity]+=1
                    if hazard[3]==0:fresh.add(identity)
                    error=float(np.linalg.norm(np.array(hazard[:2])-current[identity]));uid=item['uid'];cumulative[mode][uid]=cumulative[mode].get(uid,0.)+error*.08
                    sequential.append(dict(**shared,mode=mode,identity=identity,age=hazard[3],error=error,birth_error=item['birth_error'],nearest_second_margin=item['margin'],cumulative_error_m_s=cumulative[mode][uid]))
                if current is not None:
                    # Independent center projection only. Car/road occlusion not inferred.
                    pixels=current*np.array([1.3608,-1.701])+np.array([41.542,62.4475]);eligible=set(np.flatnonzero((pixels[:,0]>=0)&(pixels[:,0]<84)&(pixels[:,1]>=0)&(pixels[:,1]<61)).tolist())
                    frame=dict(**shared,mode=mode,known_identity_points=sum(known.values()),unknown_identity_points=sum(x is None for x in ids),duplicates=sum(max(n-1,0) for n in known.values()),geometric_ROI_obstacles=len(eligible),geometric_ROI_missing_detection=len(eligible-fresh),geometric_ROI_missing_track=len(eligible-set(known)),retained_without_current_detection=len((eligible&set(known))-fresh),actual_occlusion_labels=0)
                    frames.append(frame)
            details.append(dict(**shared,paired_path_changed=pairpath!=a['pixel_path'],paired_steering_changed=pairsteer!=a['action'][0],sequential_path_changed=a['pixel_path']!=b['pixel_path'],sequential_steering_changed=a['action'][0]!=b['action'][0]))
        trajectory.append(dict(key=case['key'],counts=dict(counts),age_distribution={mode:dict(v) for mode,v in ages.items()},actual_GT_frames=len(gt),actual_GT_intervals=sum(i-1 in gt for i in gt if i),unique_N2_intervals=sum(not x['duplicate'] for x in details if x['key']==case['key'] and x['index']>0)))
        print(json.dumps(dict(key=case['key'],frames=counts['frames'],paired_steering_changes=counts['single_interval_steering_changed'],sequential_steering_changes=counts['sequential_steering_changed'])),flush=True)
    masks={'all':lambda r:True,'fallback':lambda r:not r['optical'],'optical':lambda r:r['optical'],'precontact':lambda r:not r['post'],'postcontact':lambda r:r['post'],'actual_contact_interval':lambda r:r['actual_contact_interval'],'fallback_precontact':lambda r:not r['optical'] and not r['post'],'fallback_postcontact':lambda r:not r['optical'] and r['post']}
    aggregate={}
    for group in ['original6','N2']:
        aggregate[group]={}
        for label,predicate in masks.items():
            ps=[r for r in paired if r['group']==group and not r['duplicate'] and predicate(r)];ss=[r for r in sequential if r['group']==group and not r['duplicate'] and predicate(r)];ff=[r for r in frames if r['group']==group and not r['duplicate'] and predicate(r)]
            aggregate[group][label]=dict(single_interval={mode:summary([r[mode+'_error'] for r in ps],[r['road'] for r in ps]) for mode in ['OFF','ON']},single_interval_previous_association=summary([r['previous_association_error'] for r in ps],[r['road'] for r in ps]),single_interval_nearest_second_margin=summary([r['nearest_second_margin'] for r in ps],[r['road'] for r in ps]),
                sequential={mode:dict(error=summary([r['error'] for r in ss if r['mode']==mode],[r['road'] for r in ss if r['mode']==mode]),cumulative_error_m_s=summary([r['cumulative_error_m_s'] for r in ss if r['mode']==mode],[r['road'] for r in ss if r['mode']==mode]),
                    frames=sum(r['mode']==mode for r in ff),duplicates=sum(r['duplicates'] for r in ff if r['mode']==mode),geometric_ROI_obstacle_instances=sum(r['geometric_ROI_obstacles'] for r in ff if r['mode']==mode),geometric_ROI_missing_detection=sum(r['geometric_ROI_missing_detection'] for r in ff if r['mode']==mode),geometric_ROI_missing_track=sum(r['geometric_ROI_missing_track'] for r in ff if r['mode']==mode),retained_without_detection=sum(r['retained_without_current_detection'] for r in ff if r['mode']==mode),unknown_identity_points=sum(r['unknown_identity_points'] for r in ff if r['mode']==mode)) for mode in ['OFF','ON']})
    ages={}
    for group in ['original6','N2']:
        ages[group]={}
        for age in range(9):
            ages[group][str(age)]={mode:summary([r['error'] for r in sequential if r['group']==group and not r['duplicate'] and r['age']==age and r['mode']==mode],[r['road'] for r in sequential if r['group']==group and not r['duplicate'] and r['age']==age and r['mode']==mode]) for mode in ['OFF','ON']}
    modules={name:Path(m.__file__).resolve() for name,m in sys.modules.items() if (name=='retry' or name.startswith('retry.')) and getattr(m,'__file__',None)};assert all(path.is_relative_to(package) for path in modules.values());assert not any(n.split('.')[0] in ['core','env_wrapper','Box2D','gym','gymnasium'] for n in sys.modules)
    save(D/'metrics-private.json',dict(aggregate=aggregate,age_errors=ages,trajectory=trajectory,visibility='No authoritative visibility/occlusion labels; ROI projection only, no actual occlusion preservation claim.',association='Heuristic nearest identity fixed at previous frame or detection birth; unknown birth staysunknown. Distance/margin distributions reported, no fitted gate; duplicates and missing conditional on these identities.',cost=dict(paired_route_function_calls=routing_calls,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,new_native_actions=0,new_learning_fits=0,new_source_physics_ticks=0)))
    save(D/'correspondence-private.json',dict(single_interval=paired,sequential=sequential,frames=frames,routing=details));print('334staticmetricsclosed; no causalphysical orocclusionpromotion',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);p.add_argument('--package',required=True,type=Path);a=p.parse_args();run(a.private_root.resolve(),a.package.resolve())
