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

agent = Agent()
modules = {name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items()
           if (name == 'agent' or name == 'retry' or name.startswith('retry.'))
           and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(root) for path in modules.values())
assert not any(name.split('.')[0] in {'core','env_wrapper','gym','gymnasium','Box2D'} for name in sys.modules)
observed = {}
counts = {}


def count(name):
    counts[name] = counts.get(name,0)+1


temporal = sys.modules['retry.temporal_agent']
original_detection = temporal.road_and_obstacles
def detection(image):
    count('detection')
    result = original_detection(image)
    path,obstacles = result
    observed['current_detections'] = [list(item) for item in obstacles]
    return result
temporal.road_and_obstacles = detection

original_tracker = agent.tracked_obstacles
def tracker(image,speed):
    count('tracker')
    observed['memory_hazards_before_tracker'] = [list(item) for item in agent.hazards]
    obstacles = original_tracker(image,speed)
    observed.update(speed_estimate=float(speed), route_obstacle_inputs=[list(item) for item in obstacles],
                    memory_hazards_after_tracker=[list(item) for item in agent.hazards])
    return obstacles
agent.tracked_obstacles = tracker

connected = sys.modules['retry.connected_agent']
original_ridge = connected.ridge_path
def ridge(image):
    count('ridge')
    path = original_ridge(image)
    observed['centerline'] = [list(item) for item in path]
    return path
connected.ridge_path = ridge

schedule = sys.modules['retry.schedule_agent']
original_route = schedule.connected_route
def route(image,obstacles):
    count('route')
    path = original_route(image,obstacles)
    observed['selected_path'] = [list(item) for item in path]
    return path
schedule.connected_route = route

original_target = schedule.route_target
def target(path,speed):
    count('target')
    point = original_target(path,speed)
    observed['selected_target'] = None if point is None else np.asarray(point).tolist()
    return point
schedule.route_target = target

original_control = agent.controller.action_target
def control(x,forward,speed):
    count('action_target')
    observed.update(controller_target=[float(x),float(forward)], previous_steer_before=float(agent.controller.previous_steer))
    action = original_control(x,forward,speed)
    observed['controller_output'] = action.tolist()
    return action
agent.controller.action_target = control

original_fallback = agent.controller.action
def fallback(far_x,speed):
    count('fallback_action')
    action = original_fallback(far_x,speed)
    observed.update(actual_fallback_called=True, fallback_far_x=far_x,
                    fallback_path=[], fallback_mode='NO_ROUTE_HOLD_PREVIOUS_STEER_BRAKE' if far_x is None else 'SINGLE_FAR_TARGET',
                    fallback_action=action.tolist())
    return action
agent.controller.action = fallback

print(json.dumps({'ready':True,'simulator_imported':False,'policy_modules':modules,
                  'module_sha256':{n:hashlib.sha256(Path(p).read_bytes()).hexdigest() for n,p in modules.items()},
                  'package_init_ms':(time.perf_counter()-started)*1000,'rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  'numpy_version':np.__version__,'address_space_limit_bytes':1_024_000_000,
                  'observer_additional_policy_calls':0,'CPU_affinity':sorted(os.sched_getaffinity(0)),
                  'local_frame':'car hull local metres, x right/y forward; route origin(0,0); pixel u=42+1.3608*x,v=63-1.701*y',
                  'routing_obstacle_radial_margin_m':2.6}),flush=True)
for line in sys.stdin:
    request = json.loads(line)
    assert set(request) == {'op','observation'}
    obs = np.frombuffer(base64.b64decode(request['observation']),dtype=np.float32).reshape(4,84,84).copy()
    assert np.isfinite(obs).all() and obs.min() >= 0 and obs.max() <= 1
    observed.clear(); counts.clear()
    before = time.perf_counter()
    if request['op'] == 'reset':
        agent.reset(obs)
        response = {'ok':True,'reset_compute_ms':(time.perf_counter()-before)*1000}
    else:
        assert request['op'] == 'act'
        action = np.asarray(agent.act(obs),dtype=np.float32)
        assert action.shape == (3,) and np.isfinite(action).all()
        assert np.all(action >= [-1,0,0]) and np.all(action <= [1,1,1])
        assert all(counts.get(name) == 1 for name in ('detection','tracker','ridge','route','target'))
        assert counts.get('action_target',0)+counts.get('fallback_action',0) == 1
        observed.setdefault('actual_fallback_called',False)
        observed.setdefault('fallback_path',None)
        response = {'action':action.tolist(),'act_compute_ms':(time.perf_counter()-before)*1000,
                    'route_telemetry':dict(observed),'original_calls':dict(counts),
                    'cap_diagnostic':getattr(agent,'distance_cap_diagnostic',None),
                    'previous_steer_after':float(agent.controller.previous_steer)}
    response.update(rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                    actor_cumulative_CPU_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
    print(json.dumps(response),flush=True)
