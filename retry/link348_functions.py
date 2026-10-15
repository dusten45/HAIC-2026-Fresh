"""Isolated routing/target calls only; never construct a policy or environment."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import time


def main():
    a=argparse.ArgumentParser();a.add_argument('--package',type=Path,required=True);a.add_argument('--input',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a=a.parse_args()
    sys.path.insert(0,str(a.package.resolve()))
    import numpy as np
    import retry.connected_agent as routing
    from retry.route_agent import route_target
    from retry.cem294_constants import LOOKAHEAD_SCALE
    p=json.loads(a.input.read_text());images=np.load(p['images'])['images'];records=[];start=time.perf_counter();cpu=time.process_time()
    ledger=a.output.with_suffix('.calls.json');counts=dict(routing=0,target=0)
    def charge(key):
        assert counts[key]<2*len(p['states']);counts[key]+=1
        ledger.write_text(json.dumps(counts)+'\n');ledger.chmod(0o600)
    for i,s in enumerate(p['states']):
        variants={};f=s['features']
        for name,hazards in [('original',s['routing_hazards']),('restored',s['full_hazards'])]:
            charge('routing')
            path=[list(map(float,q)) for q in routing.connected_route(images[i],hazards,speed=f[3],previous_steer=f[7])]
            charge('target');t=route_target(path,f[3],LOOKAHEAD_SCALE);target=None if t is None else list(map(float,t))
            if name=='original':
                assert path==s['pixel_path'],(s['label'],s['step'],'route reproduction')
                assert target==f[1:3],(s['label'],s['step'],'target reproduction',target,f[1:3])
            variants[name]=dict(path=path,target=target)
        records.append(dict(label=s['label'],step=s['step'],variants=variants,path_changed=variants['original']['path']!=variants['restored']['path'],target_changed=variants['original']['target']!=variants['restored']['target']))
    modules={n:Path(m.__file__).resolve() for n,m in sys.modules.items() if n.startswith('retry') and getattr(m,'__file__',None)}
    assert all(q.is_relative_to(a.package.resolve()) for q in modules.values())
    assert not any(n.split('.')[0] in ['Box2D','gym','gymnasium','core','env_wrapper'] for n in sys.modules)
    hashes={str(q.relative_to(a.package.resolve())):hashlib.sha256(q.read_bytes()).hexdigest() for q in modules.values()}
    assert all(p['members_sha256'].get(k)==v for k,v in hashes.items()),'module hash mismatch'
    out=dict(records=records,calls=counts,loaded_module_sha256=hashes,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,numpy_version=np.__version__,new_actor_calls=0,native_actions=0)
    assert not a.output.exists();a.output.write_text(json.dumps(out,allow_nan=False)+'\n');a.output.chmod(0o600)
    print(json.dumps(dict(calls=counts,states=len(records),wall_s=out['wall_s'])),flush=True)


if __name__=='__main__':main()
