"""Isolated frozen routing function comparison on saved pixels, no Agent call.

GT never enters routing. Compare retained+direct hazards with direct detections
only, holding pixels/speed/previous steering and all routing constants fixed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    p=argparse.ArgumentParser();p.add_argument('--package',required=True,type=Path);p.add_argument('--stage332',required=True,type=Path);args=p.parse_args()
    package=args.package.resolve();D=args.stage332.resolve();sys.path.insert(0,str(package))
    import numpy as np
    import retry.connected_agent as routing
    from retry.route_agent import route_target
    from retry.cem294_constants import LOOKAHEAD_SCALE,STEERING_GAIN
    start,cpu=time.perf_counter(),time.process_time();records=[];function_calls=0
    for label in ['A','B']:
        replay=json.loads((D/label/'saved-pixel-replay-private.json').read_text());frames=np.load(D.parent/'stage331'/label/'raw-pixels-actions-private.npz')['observations']
        for index in range(64,68):
            r=replay[index]['response'];f=r['features'];variants={}
            for mode,obstacles in [('retained',[h[:3] for h in r['state']['hazards']]),('direct_only',r['direct_obstacles'])]:
                path=[list(map(float,p)) for p in routing.connected_route(frames[index,-1],obstacles,speed=f[3],previous_steer=f[7])];function_calls+=1
                target=route_target(path,f[3],LOOKAHEAD_SCALE)
                if mode=='retained':assert path==r['pixel_path'],(label,index,'retained route mismatch')
                if target is None:steer=None;curvature=None
                else:
                    x,y=map(float,target);curvature=2*x/max(x*x+y*y,1e-6);steer=float(np.float32(.8*float(np.clip(np.arctan(3.24*curvature*STEERING_GAIN),-.4,.4))+.2*f[7]))
                if mode=='retained':assert steer==r['calculated330'][0] if 'calculated330' in r else steer==r['action'][0]
                variants[mode]=dict(path=path,target=None if target is None else list(map(float,target)),steering=steer,curvature=curvature,connection_evaluation=routing.LAST_CONNECTION_EVALUATION)
            records.append(dict(arm=label,boundary=index,path_changed=variants['retained']['path']!=variants['direct_only']['path'],variants=variants))
    modules={name:Path(m.__file__) for name,m in sys.modules.items() if (name=='retry' or name.startswith('retry.')) and getattr(m,'__file__',None)}
    assert all(path.resolve().is_relative_to(package) for path in modules.values());assert not any(name.split('.')[0] in ['Box2D','gym','gymnasium','core'] for name in sys.modules)
    out=dict(records=records,routing_function_calls=function_calls,new_agent_act_calls=0,native_actions=0,new_fits=0,source_physics_rollout_ticks=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,
        loaded_module_sha256={str(path.relative_to(package)):hashlib.sha256(path.read_bytes()).hexdigest() for path in modules.values()})
    dest=D/'routing-counterfactual-private.json';assert not dest.exists();dest.write_text(json.dumps(out,allow_nan=False)+'\n');dest.chmod(0o600)
    print(json.dumps(dict(routing_function_calls=function_calls,changed_paths=sum(r['path_changed'] for r in records),new_agent_act_calls=0,native_actions=0,CPU_s=out['CPU_s'])),flush=True)


if __name__=='__main__':main()
