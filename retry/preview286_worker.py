"""Pixel-only PPO275 base observer with executed-action commit and pure cutoff peek.

Python audit hooks constrain Python file access; this is not an OS sandbox,
a container, a fresh machine, or proof of official runner parity.
"""
import copy
import base64
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import time

started = time.perf_counter()
root = Path(sys.argv[1]).resolve()
clean = root.parent
allowed = (clean, Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve())
denied = []
# README says 1,024 MB; conservatively enforce decimal bytes locally.
# This remains address-space enforcement, not official RSS/cgroup parity.
memory_limit_bytes = 1_024_000_000
resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes,)*2)
resource.setrlimit(resource.RLIMIT_CPU, (120,120))
resource.setrlimit(resource.RLIMIT_NOFILE, (64,64))
if hasattr(os, 'sched_getaffinity'):
    os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})


def audit(event, args):
    forbidden = event in {'os.system', 'subprocess.Popen', 'socket.__new__'}
    if event == 'import':
        forbidden |= str(args[0]).split('.')[0] in {'core','env_wrapper','gym','gymnasium','Box2D'}
    if event == 'open':
        name, mode, flags = args
        if isinstance(name, (str, bytes, os.PathLike)):
            path = Path(os.fsdecode(name)).resolve()
            forbidden |= not any(path.is_relative_to(prefix) for prefix in allowed)
            forbidden |= bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND))
        elif isinstance(name, int):
            forbidden |= name not in (0,1,2)
    if forbidden:
        denied.append(event)
        raise PermissionError('Clean pixel probe blocked '+event)


sys.addaudithook(audit)
sys.path.insert(0,str(root))
import numpy as np
from agent import Agent

agent = Agent()
observed_features={}
original_correct=agent.correct_pedals
def observe_features(features,nominal):
    observed_features['nominal']=list(map(float,nominal));observed_features['features']=list(features);return original_correct(features,nominal)
agent.correct_pedals=observe_features
modules = {name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items()
           if (name == 'agent' or name == 'retry' or name.startswith('retry.'))
           and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(root) for path in modules.values())
assert not any(name.split('.')[0] in {'core','env_wrapper','gym','gymnasium','Box2D'} for name in sys.modules)
print(json.dumps({'ready':True,'simulator_imported':False,'policy_modules':modules,
                  'policy_module_sha256':{name:hashlib.sha256(Path(path).read_bytes()).hexdigest() for name,path in modules.items()},
                  'package_init_ms':(time.perf_counter()-started)*1000,
                  'rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  'CPU_affinity':sorted(os.sched_getaffinity(0)) if hasattr(os,'sched_getaffinity') else None,
                  'numpy_version':np.__version__, 'opencv_version':getattr(sys.modules.get('cv2'),'__version__',None),
                  'python_version':sys.version.split()[0], 'python_audit_denied_events':denied,
                  'address_space_limit_bytes':memory_limit_bytes,
                  'isolation_scope':'clean cwd + extracted package origins + isolated Python + sanitized env + separate CPU process + Python audit hooks; same host/runtime, not OS filesystem or network isolation'}),flush=True)
nominal_module=sys.modules['retry.nominal238_base']
original_route=nominal_module.connected_route
observed_route={}
def route_observer(*args,**kwargs):
    path=original_route(*args,**kwargs)
    observed_route['path']=[list(map(float,p)) for p in path]
    return path
nominal_module.connected_route=route_observer
history=[]
pending=False
last_base=None
def state():
    return dict(previous_steer=float(agent.controller.previous_steer),lateral_acceleration=float(agent.controller.lateral_acceleration),
        hazards_sha256=hashlib.sha256(np.asarray(agent.hazards,dtype=np.float64).tobytes()).hexdigest(),
        previous_image_sha256=hashlib.sha256(agent.previous_image.tobytes()).hexdigest() if agent.previous_image is not None else None,
        history_sha256=hashlib.sha256(np.asarray(history,dtype=np.float32).tobytes()).hexdigest())
def history_vector():
    padded=np.zeros((3,3),np.float64);mask=np.zeros(3,np.float64)
    if history:padded[-len(history):]=history;mask[-len(history):]=1
    return np.r_[(padded/np.array([.4,1.,1.])).ravel(),mask].tolist()
for line in sys.stdin:
    request = json.loads(line)
    assert set(request) == {'op','observation'}
    op=request['op']
    payload=np.frombuffer(base64.b64decode(request['observation']),dtype=np.float32)
    before=time.perf_counter()
    if op=='commit':
        assert pending and payload.shape==(3,) and np.isfinite(payload).all()
        assert np.all(payload>=np.array([-.4,0,0],np.float32)) and np.all(payload<=np.array([.4,1,1],np.float32))
        nominal=float(agent.controller.previous_steer)
        # Exactzero preserves240 float64 nominal memory; actual command agrees
        # in float32. All changed steering commands own the returned command.
        if payload[0]!=last_base[0]:agent.controller.previous_steer=float(payload[0])
        assert np.float32(agent.controller.previous_steer)==payload[0]
        history.append(payload.tolist());history=history[-3:];pending=False
        response=dict(ok=True,nominal_memory=nominal,memory=float(agent.controller.previous_steer),history=history,state=state(),commit_ms=(time.perf_counter()-before)*1000)
    else:
        obs=payload.reshape(4,84,84).copy();assert np.isfinite(obs).all() and obs.min()>=0 and obs.max()<=1
        if op=='reset':
            agent.reset(obs);history=[];pending=False;last_base=None
            response=dict(ok=True,state=state(),history=history,reset_compute_ms=(time.perf_counter()-before)*1000)
        else:
            assert op in ['act','peek'] and not pending
            if op=='peek':
                before_state=state();clone=copy.deepcopy(agent)
                base=np.asarray(clone.act(obs),np.float32)
                assert state()==before_state
            else:
                base=np.asarray(agent.act(obs),np.float32);last_base=base.copy();pending=True
            f=list(observed_features['features'])
            response=dict(action=base.tolist(),features=f,history_features=history_vector(),history=history,
                state=state(),pixel_path=observed_route.get('path',[]),nominal=observed_features['nominal'],peek_state_preserved=op=='peek',act_compute_ms=(time.perf_counter()-before)*1000)
    response.update(rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
        actor_cumulative_CPU_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
        python_audit_denied_events=list(denied))
    print(json.dumps(response),flush=True)
