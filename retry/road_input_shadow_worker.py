"""Read-only full-route observer outside an unchanged pixel-policy package.

Hooks call the original detector/tracker/route/target/controller exactly once,
returning the original results. Only reset/act and pixels enter this process.
"""
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
allowed = (root.parent, Path(sys.prefix).resolve(), Path(sys.base_prefix).resolve())
resource.setrlimit(resource.RLIMIT_AS,(1_024_000_000,)*2)
resource.setrlimit(resource.RLIMIT_CPU,(120,)*2)
resource.setrlimit(resource.RLIMIT_NOFILE,(64,)*2)
os.sched_setaffinity(0,{min(os.sched_getaffinity(0))})


def audit(event,args):
    forbidden = event in {'os.system','subprocess.Popen','socket.__new__'}
    if event == 'import':
        forbidden |= str(args[0]).split('.')[0] in {'core','env_wrapper','gym','gymnasium','Box2D'}
    if event == 'open':
        name,mode,flags = args
        if isinstance(name,(str,bytes,os.PathLike)):
            path = Path(os.fsdecode(name)).resolve()
            forbidden |= not any(path.is_relative_to(prefix) for prefix in allowed)
            forbidden |= bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND))
        elif isinstance(name,int):
            forbidden |= name not in (0,1,2)
    if forbidden:
        raise PermissionError('Pixel observer blocked '+event)


sys.addaudithook(audit)
sys.path.insert(0,str(root))
import numpy as np
from agent import Agent

import copy
import pickle
import runpy

boundary=runpy.run_path(str(root.parent/'boundary.py'))
connected=sys.modules['retry.connected_agent'];schedule=sys.modules['retry.schedule_agent']
set_mask,restore,activate,boundary_receipt=boundary['install_mask_boundary'](connected)
restore();actual=Agent();shadow=Agent();active={}


def state(obj):
    result={}
    for k,v in sorted(vars(obj).items()):
        if callable(v):continue
        result[k]=('object',state(v)) if hasattr(v,'__dict__') else ('data',copy.deepcopy(v))
    return result


def put(obj,data):
    for k,(kind,v) in data.items():
        if kind=='object':put(getattr(obj,k),v)
        else:setattr(obj,k,copy.deepcopy(v))


def digest(data):return hashlib.sha256(pickle.dumps(data,protocol=4)).hexdigest()
def encoded(a):
    a=np.ascontiguousarray(a)
    return {'dtype':str(a.dtype),'shape':list(a.shape),'base64':base64.b64encode(a.tobytes()).decode('ascii')}


original_tracker=actual.tracked_obstacles
def actual_tracker(image,speed):
    active['tracker_calls']+=1
    result=original_tracker(image,speed)
    active.update(speed=float(speed),obstacles=copy.deepcopy(result),hazards=copy.deepcopy(actual.hazards),previous_image=actual.previous_image.copy())
    return result
actual.tracked_obstacles=actual_tracker

def shared_tracker(image,speed):
    assert float(speed)==active['speed']
    assert np.array_equal(np.rint(image*255).astype(np.uint8),active['previous_image'])
    shadow.hazards=copy.deepcopy(active['hazards']);shadow.previous_image=active['previous_image'].copy()
    return copy.deepcopy(active['obstacles'])
shadow.tracked_obstacles=shared_tracker


def evaluate(agent,observation,mask,capture):
    restore()
    if mask is not None:set_mask(mask);activate()
    old_problem=connected.routing_problem;old_ridge=connected.ridge_path
    old_route=schedule.connected_route;old_target=schedule.route_target;telemetry={};arrays={};calls={}
    def tick(k):calls[k]=calls.get(k,0)+1
    def ridge(image):
        tick('ridge');r=old_ridge(image);telemetry['centerline']=[list(p) for p in r];return r
    def problem(image,obstacles):
        tick('routing_problem');r=old_problem(image,obstacles)
        allowed,distance,start,legacy,goal,labels=r
        telemetry.update(start=start,legacy_goal=legacy,connected_goal=goal)
        arrays.update(closed_road=(distance>0).astype(np.uint8),distance=distance,allowed=allowed.astype(np.uint8),labels=np.zeros((84,84),np.int32) if labels is None else labels)
        return r
    def route(image,obstacles):
        tick('route');r=old_route(image,obstacles);telemetry['path']=[list(p) for p in r];return r
    def target(path,speed):
        tick('target');r=old_target(path,speed);telemetry['target']=None if r is None else np.asarray(r).tolist();return r
    connected.ridge_path=ridge;connected.routing_problem=problem;schedule.connected_route=route;schedule.route_target=target
    try:action=np.asarray(agent.act(observation),dtype=np.float32)
    finally:
        connected.routing_problem=old_problem;connected.ridge_path=old_ridge;schedule.connected_route=old_route;schedule.route_target=old_target;restore()
    assert all(calls.get(k)==1 for k in ['ridge','routing_problem','route','target'])
    raw=((observation[-1]>.32)&(observation[-1]<.47)).astype(np.uint8) if mask is None else mask.copy()
    cropped=raw.copy();cropped[61:]=0
    arrays.update(raw_road=raw,cropped_road=cropped)
    telemetry.update(action=action.tolist(),speed=active['speed'],hazards=copy.deepcopy(agent.hazards),previous_steer_after=float(agent.controller.previous_steer),lateral_acceleration=float(agent.controller.lateral_acceleration),cap=copy.deepcopy(agent.distance_cap_diagnostic),calls=calls)
    if capture:telemetry['arrays']={k:encoded(v) for k,v in arrays.items()}
    return action,telemetry,arrays


modules={n:str(Path(m.__file__).resolve()) for n,m in sys.modules.items() if (n=='agent' or n=='retry' or n.startswith('retry.')) and getattr(m,'__file__',None)}
assert all(Path(p).is_relative_to(root) for p in modules.values())
print(json.dumps({'ready':True,'simulator_imported':False,'policy_modules':modules,'module_sha256':{n:hashlib.sha256(Path(p).read_bytes()).hexdigest() for n,p in modules.items()},'boundary':boundary_receipt,'shared_actual_tracker_only':True,'closure_functions_preserved_per_instance':True,'shadow_tracker_RNG_calls':0}),flush=True)
for line in sys.stdin:
    request=json.loads(line);assert set(request)=={'op','observation'}
    packed=np.frombuffer(base64.b64decode(request['observation']),dtype=np.float32).reshape(5,84,84).copy();obs=packed[:4];mask=packed[4].astype(np.uint8)
    assert np.array_equal(mask,packed[4]) and np.isfinite(obs).all() and obs.min()>=0 and obs.max()<=1
    before=time.perf_counter()
    if request['op']=='reset':
        restore();actual.reset(obs);shadow.reset(obs);response={'ok':True}
    else:
        assert request['op'] in ('act','capture','noop');capture=request['op']!='act';active.clear();active['tracker_calls']=0
        pre=state(actual);pre_sha=digest(pre)
        pixel_action,pixel,pa=evaluate(actual,obs,None,capture)
        post=state(actual);post_sha=digest(post)
        put(shadow,pre);assert digest(state(shadow))==pre_sha
        visible=mask if request['op']!='noop' else pa['raw_road']
        shadow_action,gt,ga=evaluate(shadow,obs,visible,capture)
        assert digest(state(actual))==post_sha and active['tracker_calls']==1
        if request['op']=='noop':
            assert pixel_action.tobytes()==shadow_action.tobytes() and digest(state(shadow))==post_sha
            assert pixel['path']==gt['path'] and pixel['target']==gt['target']
            assert all(np.array_equal(pa[k],ga[k]) for k in pa)
        false=pa['raw_road'].astype(bool)&~ga['raw_road'].astype(bool);missing=ga['raw_road'].astype(bool)&~pa['raw_road'].astype(bool)
        response={'action':pixel_action.tolist(),'pixel':pixel,'visible_GT_shadow':gt,'actual_pre_memory_sha256':pre_sha,'shadow_pre_memory_sha256':pre_sha,'actual_post_memory_sha256':post_sha,'actual_post_unchanged_by_shadow':True,'shared_tracker_calls':1,'false_road_cells':int(false.sum()),'missing_road_cells':int(missing.sum()),'action_delta':(shadow_action-pixel_action).tolist(),'closed_road_difference_cells':int(np.count_nonzero(pa['closed_road']!=ga['closed_road'])),'allowed_difference_cells':int(np.count_nonzero(pa['allowed']!=ga['allowed']))}
        if capture:response['pre_memory_pickle_base64']=base64.b64encode(pickle.dumps(pre,protocol=4)).decode('ascii')
    response.update(act_compute_ms=(time.perf_counter()-before)*1000,rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,actor_cumulative_CPU_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
    print(json.dumps(response),flush=True)
