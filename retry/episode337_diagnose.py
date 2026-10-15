"""Posthoc analysis of the measured new failure; no new native telemetry/run."""
import argparse
import hashlib
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


def run(R,package):
    D=R/'stage337';assert not (D/'failure-diagnosis-private.json').exists();sys.path.insert(0,str(package))
    import retry.connected_agent as routing
    from retry.route_agent import route_target
    from retry.cem294_constants import LOOKAHEAD_SCALE,STEERING_GAIN
    start,cpu=time.perf_counter(),time.process_time();rows=[json.loads(s) for s in (D/'B/trace-private.jsonl').read_text().splitlines()];frames=np.load(D/'B/frames-actions-private.npz')['frames_uint8'];records=[];calls=0
    contact=next(r for r in rows if r['collision']);object_id=contact['post_physical']['touching_obstacle_contacts'][0][0]
    for step in range(124,133):
        r=rows[step-1];s=r['pre_physical'];h=s['hull'];centers=np.array([rotation(-h['angle'])@(rotation(o['body']['angle'])@np.array(o['fixture']['geometry']['pos'])+o['body']['position']-h['position']) for o in s['obstacles']]);direct=r['tracker']['direct'];current_errors=[float(np.linalg.norm(np.array(p[:2])-centers[object_id])) for p in direct];aged=[]
        for p in r['tracker']['after']:
            if p[3]>0:
                distance=np.linalg.norm(centers-np.array(p[:2]),axis=1);aged.append(dict(age=p[3],nearest_object=int(distance.argmin()),nearest_any_GT_error_m=float(distance.min())))
        variants={};f=r['features']
        for mode,hazards in [('original_retained',r['tracker']['after']),('direct_only',direct)]:
            path=[list(map(float,p)) for p in routing.connected_route(frames[step-1].astype(np.float32)/255,[p[:3] for p in hazards],speed=f[3],previous_steer=f[7])];calls+=1;target=route_target(path,f[3],LOOKAHEAD_SCALE)
            if mode=='original_retained':assert path==r['pixel_path']
            if target is None:steer=float(np.float32(f[7]));heading=None
            else:
                x,y=map(float,target);curvature=2*x/max(x*x+y*y,1e-6);steer=float(np.float32(.8*float(np.clip(np.arctan(3.24*curvature*STEERING_GAIN),-.4,.4))+.2*f[7]));heading=math.atan2(x,y)
            if mode=='original_retained':assert steer==r['executed'][0]
            variants[mode]=dict(path=path,steering=steer,target_heading_rad=heading)
        first=r['pixel_path'][1] if len(r['pixel_path'])>1 else None
        records.append(dict(step=step,direct_count=len(direct),closest_direct_to_contact_object_error_m=min(current_errors) if current_errors else None,aged=aged,optical_accepted=r['tracker']['affine'] is not None,pre_speed_m_s=r['pre']['speed_m_s'],target_speed=f[6],initial_path_heading_rad=None if first is None else math.atan2(first[0],first[1]),target_heading_rad=variants['original_retained']['target_heading_rad'],path_changed=variants['original_retained']['path']!=variants['direct_only']['path'],steering_changed=variants['original_retained']['steering']!=variants['direct_only']['steering'],variants=variants))
    touching=[r['step'] for r in rows if any(p[0]==object_id and p[2]==0 for p in r['post_physical']['touching_obstacle_contacts'])];start_negative=next(r['step'] for r in rows if r['post']['off_track_counter']>0);last_growth=max(r['step'] for r in rows if r['pre']['unique_tiles']!=r['post']['unique_tiles']);last=rows[-1]
    modules={n:Path(m.__file__).resolve() for n,m in sys.modules.items() if (n=='retry' or n.startswith('retry.')) and getattr(m,'__file__',None)};assert all(p.is_relative_to(package) for p in modules.values());assert not any(n.split('.')[0] in ['core','Box2D','gym','gymnasium'] for n in sys.modules)
    out=dict(first_contact_action=contact['step'],contact_object=object_id,hull_touching_endpoint_first=touching[0],hull_touching_endpoint_last=touching[-1],hull_touching_endpoint_count=len(touching),consecutive_hull_touching=touching==list(range(touching[0],touching[-1]+1)),first_negative_counter_action=start_negative,terminal_negative_counter=last['post']['off_track_counter'],last_unique_tile_growth_action=last_growth,missing_target_inputs=sum(bool(r['features'][0]) for r in rows),current_detection_error_range_m=[min(x['closest_direct_to_contact_object_error_m'] for x in records),max(x['closest_direct_to_contact_object_error_m'] for x in records)],diagnostic_frames=records,direct_only_steering_changed_steps=[r['step'] for r in records if r['steering_changed']],
        interpretation='Off_track is101consecutive negative-reward actions after progress stopped, not proof of geometric road departure. Collisionevent only132 butactualhull-obstaclecontact persists132-233. Currentrealobstacle detection is accurate in sampled approach; extra retained points andpath/goal/approach speed remain distinct hypotheses. Staticroutingcounterfactual is no physical outcome.',cost=dict(routing_function_calls=calls,new_actor_calls=0,new_native_actions=0,new_learning_fits=0,new_source_physics_ticks=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu),loaded_module_sha256={str(p.relative_to(package)):hashlib.sha256(p.read_bytes()).hexdigest() for p in modules.values()})
    save(D/'failure-diagnosis-private.json',out);print(json.dumps({k:out[k] for k in ['hull_touching_endpoint_count','first_negative_counter_action','terminal_negative_counter','last_unique_tile_growth_action','missing_target_inputs','current_detection_error_range_m','direct_only_steering_changed_steps']}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);p.add_argument('--package',required=True,type=Path);a=p.parse_args();run(a.private_root.resolve(),a.package.resolve())
