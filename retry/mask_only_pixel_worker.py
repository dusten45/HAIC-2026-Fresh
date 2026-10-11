"""Road-mask-only observer around the unchanged formal champion archive.

The sole request payload is official float32(4,84,84); learned model and feature
code are fixed read-only assets. No environment, GT, seed, step, or cache input.
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

import runpy
boundary = runpy.run_path(str(root.parent/'boundary.py'))
student_api = runpy.run_path(str(root.parent/'student.py'))
mask_config = json.loads((root.parent/'mask-config.json').read_text())
assert set(mask_config) == {'source'} and mask_config['source'] in ('student','original')
mask_source = mask_config['source']
student = student_api['KeepStudent'](root.parent/'student.xml') if mask_source == 'student' else None
student_source_sha256 = hashlib.sha256((root.parent/'student.py').read_bytes()).hexdigest()
boundary_source_sha256 = hashlib.sha256((root.parent/'boundary.py').read_bytes()).hexdigest()
student_model_sha256 = hashlib.sha256((root.parent/'student.xml').read_bytes()).hexdigest()
connected_boundary = sys.modules['retry.connected_agent']
set_road_mask, _, _, mask_boundary_receipt = boundary['install_mask_boundary'](connected_boundary)
agent = Agent()
control_parameters = {'speed_cap':float(agent.controller.speed_cap),
                      'lateral_fast':float(agent.lateral_fast), 'lateral_safe':float(agent.lateral_safe),
                      'speed_gain':float(agent.speed_gain), 'speed_bias':float(agent.speed_bias)}
assert control_parameters == {'speed_cap':28.0, 'lateral_fast':7.0, 'lateral_safe':5.0,
                              'speed_gain':11.4142485314592, 'speed_bias':-6.545558315185489}
assert not hasattr(agent, 'distance_cap_diagnostic') and not hasattr(agent, 'curve_diagnostic')
modules = {name:str(Path(module.__file__).resolve()) for name,module in sys.modules.items()
           if (name == 'agent' or name == 'retry' or name.startswith('retry.'))
           and getattr(module,'__file__',None)}
assert all(Path(path).is_relative_to(root) for path in modules.values())
assert not any('distance_cap' in name or 'curve' in name for name in modules)
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
    observed['controller_before'] = controller_state()
    observed.update(controller_target=[float(x),float(forward)], previous_steer_before=float(agent.controller.previous_steer))
    action = original_control(x,forward,speed)
    observed['controller_output'] = action.tolist()
    observed['controller_after'] = controller_state()
    return action
agent.controller.action_target = control

original_fallback = agent.controller.action
def fallback(far_x,speed):
    count('fallback_action')
    observed['controller_before'] = controller_state()
    action = original_fallback(far_x,speed)
    observed.update(actual_fallback_called=True, fallback_far_x=far_x,
                    fallback_path=[], fallback_mode='NO_ROUTE_HOLD_PREVIOUS_STEER_BRAKE' if far_x is None else 'SINGLE_FAR_TARGET',
                    fallback_action=action.tolist(), controller_output=action.tolist(),
                    controller_after=controller_state(), previous_steer_before=observed['controller_before']['previous_steer'])
    return action
agent.controller.action = fallback

def controller_state():
    return {'previous_steer':float(agent.controller.previous_steer),
            'speed_cap':float(agent.controller.speed_cap),
            'lateral_acceleration':float(agent.controller.lateral_acceleration)}

print(json.dumps({'ready':True,'simulator_imported':False,'policy_modules':modules,
                  'module_sha256':{n:hashlib.sha256(Path(p).read_bytes()).hexdigest() for n,p in modules.items()},
                  'package_init_ms':(time.perf_counter()-started)*1000,'rss_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                  'numpy_version':np.__version__,'address_space_limit_bytes':1_024_000_000,
                  'observer_additional_policy_calls':0,'privileged_diagnostic':False,'intervention':'road_mask_only','mask_source':mask_source,
                  'control_parameters':control_parameters,'distance_cap_applied':False,'curve_applied':False,
                  'student_source_sha256':student_source_sha256,'boundary_source_sha256':boundary_source_sha256,
                  'observer_additional_model_calls':0,'student_model_sha256':student_model_sha256,'input_contract':'float32(4,84,84) grayscale only','mask_boundary':mask_boundary_receipt,'CPU_affinity':sorted(os.sched_getaffinity(0)),
                  'local_frame':'car hull local metres, x right/y forward; route origin(0,0); pixel u=42+1.3608*x,v=63-1.701*y',
                  'routing_obstacle_radial_margin_m':2.6}),flush=True)
for line in sys.stdin:
    request = json.loads(line)
    assert set(request) == {'op','observation'}
    assert request['op'] in ('reset','act')
    obs = np.frombuffer(base64.b64decode(request['observation'],validate=True),dtype=np.float32).reshape(4,84,84).copy()
    assert np.isfinite(obs).all() and obs.min() >= 0 and obs.max() <= 1
    if mask_source == 'student':
        road, student_receipt = student.mask(obs)
    else:
        road = ((obs[-1] > .32) & (obs[-1] < .47)).astype(np.uint8)
        digest = hashlib.sha256(road.tobytes()).hexdigest()
        student_receipt = {'original_P_cells':int(road.sum()), 'kept_cells':int(road.sum()),
            'deleted_cells':0, 'added_cells':0, 'original_P_sha256':digest,
            'student_mask_sha256':digest, 'inference_ms':0.0, 'feature_mean_on_P':None,
            'input_shape':[4,84,84], 'input_dtype':'float32', 'input_kind':'official_grayscale_only'}
    student_receipt.update(mask_source=mask_source, intervention='road_mask_only',
                           mask_evaluations=1, model_mask_calls=int(mask_source == 'student'))
    set_road_mask(road)
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
                    'cap_diagnostic':None,'curve_diagnostic':None,
                    'distance_cap_applied':False,'curve_applied':False,
                    'previous_steer_after':float(agent.controller.previous_steer)}
    response.update(intervention='road_mask_only', mask_source=mask_source,
                    distance_cap_applied=False, curve_applied=False, control_parameters=control_parameters)
    response['student_receipt'] = student_receipt
    response['student_mask_base64'] = base64.b64encode(road.tobytes()).decode('ascii')
    response.update(rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                    actor_cumulative_CPU_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime)
    print(json.dumps(response),flush=True)
