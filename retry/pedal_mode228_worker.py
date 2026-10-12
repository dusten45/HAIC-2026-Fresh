"""Frozen mode/strength pedal student; pixel-only, nominal steering/memory preserved.

Python audit hooks constrain Python file access; this is not an OS sandbox,
a container, a fresh machine, or proof of official runner parity.
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

with np.load(clean / 'mode-head.npz', allow_pickle=False) as model:
    assert set(model.files) == {'mean','std','classifier','gas','brake'}
    head_mean=model['mean'].copy();head_std=model['std'].copy()
    mode_weights=model['classifier'].copy();gas_weights=model['gas'].copy();brake_weights=model['brake'].copy()
assert head_mean.shape==head_std.shape==(16,) and mode_weights.shape==(17,3)
assert gas_weights.shape==brake_weights.shape==(17,)
assert all(np.isfinite(v).all() for v in [head_mean,head_std,mode_weights,gas_weights,brake_weights])
assert (head_std>=1e-6).all()
agent = Agent()
assert (agent.lateral_fast, agent.lateral_safe) == (24.0, 8.0)
observed = {}
route_observed = {}
contact_observed = {}
call_counts = {}
schedule = sys.modules['retry.schedule_agent']
connected = sys.modules['retry.connected_agent']
temporal = sys.modules['retry.temporal_agent']
original_control = agent.controller.action_target
original_fallback = agent.controller.action
original_tracker = agent.tracked_obstacles
original_route = schedule.connected_route
original_target = schedule.route_target
original_ridge = connected.ridge_path
original_detection = temporal.road_and_obstacles
original_decoder = getattr(schedule, 'decode_feedback_speed', None)


def count(name):
    call_counts[name] = call_counts.get(name, 0) + 1


def argument(args, kwargs, name, index, default=None):
    return args[index] if len(args) > index else kwargs.get(name, default)


def controller_state():
    return {name: float(getattr(agent.controller, name)) for name in
            ('previous_steer', 'lateral_acceleration', 'speed_cap')}


def control(*args, **kwargs):
    count('controller')
    before = controller_state()
    action = original_control(*args, **kwargs)
    x = float(argument(args, kwargs, 'x', 0))
    forward = float(argument(args, kwargs, 'forward', 1))
    speed = float(argument(args, kwargs, 'speed', 2))
    supplied = argument(args, kwargs, 'pedal_speed', 3)
    feedback = speed if supplied is None else float(supplied)
    curvature = 2 * x / max(forward * forward + x * x, 1e-6)
    target_speed = min(before['speed_cap'], float(np.sqrt(
        before['lateral_acceleration'] / max(abs(curvature), 1e-6))))
    expected_pedals = np.asarray([float(np.clip(0.08 * (target_speed-feedback), 0, 0.5)),
                                 float(np.clip(0.04 * (feedback-target_speed), 0, 0.5))], np.float32)
    assert np.array_equal(np.asarray(action)[1:], expected_pedals)
    observed.update(near=bool(before['lateral_acceleration'] == agent.lateral_safe),
        target_calls=1, variant='hud_feedback' if original_decoder else 'nominal',
        actual_offset=0.0, curvature=float(curvature), speed_estimate=speed,
        target_x=x, target_forward=forward, nominal_target=target_speed)
    contact_observed.update(old_HUD_speed_m_s=speed,
        supplied_pedal_speed_m_s=None if supplied is None else float(supplied),
        actual_feedback_speed_m_s=feedback, curvature=float(curvature),
        target_speed_m_s=target_speed, target_speed_source='Source-identical arithmetic from actual controller arguments and pre-call constants; not a frame-local snapshot',
        controller_before=before, controller_after=controller_state(),
        controller_return_action=np.asarray(action).tolist(),
        gas=float(action[1]), brake=float(action[2]))
    return action


def fallback(*args, **kwargs):
    count('fallback_controller')
    before = controller_state()
    action = original_fallback(*args, **kwargs)
    speed = float(argument(args, kwargs, 'speed', 1))
    contact_observed.update(old_HUD_speed_m_s=speed, supplied_pedal_speed_m_s=None,
        actual_feedback_speed_m_s=speed, curvature=None, target_speed_m_s=None,
        target_speed_source='No target: original fallback controller',
        controller_before=before, controller_after=controller_state(),
        controller_return_action=np.asarray(action).tolist(),
        gas=float(action[1]), brake=float(action[2]))
    return action


def detection(*args, **kwargs):
    count('detection')
    output = original_detection(*args, **kwargs)
    contact_observed['detected_path_xy'] = np.asarray(output[0], np.float64).reshape(-1, 2).tolist()
    contact_observed['detected_obstacles_xyr'] = np.asarray(output[1], np.float64).reshape(-1, 3).tolist()
    return output


def tracker(*args, **kwargs):
    count('tracker')
    contact_observed['tracker_hazards_before'] = np.asarray(agent.hazards, np.float64).reshape(-1, 4).tolist()
    obstacles = original_tracker(*args, **kwargs)
    speed = float(argument(args, kwargs, 'speed', 1))
    contact_observed['old_HUD_speed_m_s'] = speed
    route_observed['obstacle_count'] = len(obstacles)
    route_observed['tracked_obstacles_body'] = np.asarray(obstacles, np.float64).reshape(-1, 3).tolist()
    route_observed['tracker_hazards_after'] = np.asarray(agent.hazards, np.float64).reshape(-1, 4).tolist()
    contact_observed['tracker_hazards_after'] = route_observed['tracker_hazards_after']
    return obstacles


def route(*args, **kwargs):
    count('route')
    path = original_route(*args, **kwargs)
    points = np.asarray(path, np.float64).reshape(-1, 2)
    length = sum(float(np.linalg.norm(b-a)) for a,b in zip(points[:-1], points[1:]))
    route_observed.update(path_point_count=len(path), route_empty=not bool(len(path)),
        selected_path_body=points.tolist(), route_total_polyline_length_m=length,
        path_last_forward_m=float(points[-1,1]) if len(path) else None,
        path_last_range_m=float(np.linalg.norm(points[-1])) if len(path) else None,
        path_max_forward_m=float(points[:,1].max()) if len(path) else None)
    return path


def ridge(*args, **kwargs):
    count('ridge')
    centerline = original_ridge(*args, **kwargs)
    route_observed['ridge_centerline_body'] = np.asarray(centerline, np.float64).reshape(-1, 2).tolist()
    return centerline


def target(*args, **kwargs):
    count('target')
    point = original_target(*args, **kwargs)
    path = argument(args, kwargs, 'path', 0)
    speed = float(argument(args, kwargs, 'speed', 1))
    desired = float(np.clip(4 + 0.35 * speed, 6, 14))
    route_observed.update(desired_lookahead_m=desired,
        returned_target=None if point is None else np.asarray(point).tolist(),
        target_endpoint_truncated=bool(point is not None and
            route_observed['route_total_polyline_length_m'] < desired),
        target_at_endpoint=bool(point is not None and np.array_equal(point, np.asarray(path[-1]))))
    return point


def decoder(*args, **kwargs):
    count('decoder')
    value = original_decoder(*args, **kwargs)
    image = argument(args, kwargs, 'image', 0)
    signature = np.rint(image[74:83, 11:13] * 255).astype(np.uint8).tobytes()
    matched = signature in sys.modules['retry.hud_feedback'].TEMPLATES
    contact_observed.update(decoder_called=True, fixed_decoder_speed_m_s=float(value),
        decoder_exact_match=bool(matched), decoder_fallback_used=not matched,
        decoder_core_signature_hex=signature.hex())
    return value


agent.controller.action_target = control
agent.controller.action = fallback
agent.tracked_obstacles = tracker
schedule.connected_route = route
schedule.route_target = target
connected.ridge_path = ridge
temporal.road_and_obstacles = detection
if original_decoder is not None:
    schedule.decode_feedback_speed = decoder

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
                  'observer_extra_policy_calls':0,'observer_extra_vision_calls':0,'observer_model_calls':0,
                  'decoder_present':original_decoder is not None,
                  'observer_scope':'Actual call inputs/returns and explicit before/after attributes only; no arbitrary snapshots or extra perception',
                  'speed_constraint_scope':'Visibility has no explicit speed-cap term; path extent and returned target may affect control indirectly',
                  'isolation_scope':'clean cwd + extracted package origins + isolated Python + sanitized env + separate CPU process + Python audit hooks; same host/runtime, not OS filesystem or network isolation'}),flush=True)
for line in sys.stdin:
    request = json.loads(line)
    assert set(request) == {'op','observation'}
    obs = np.frombuffer(base64.b64decode(request['observation']),dtype=np.float32).reshape(4,84,84).copy()
    assert np.isfinite(obs).all() and obs.min() >= 0 and obs.max() <= 1
    before = time.perf_counter()
    if request['op'] == 'reset':
        agent.reset(obs)
        response = {'ok':True, 'reset_compute_ms':(time.perf_counter()-before)*1000}
    else:
        assert request['op'] == 'act'
        observed.clear(); route_observed.clear(); contact_observed.clear(); call_counts.clear()
        latest = np.rint(obs[-1] * 255).astype(np.uint8)
        contact_observed.update(decoder_called=False, fixed_decoder_speed_m_s=None,
            decoder_exact_match=None, decoder_fallback_used=None,
            heading_estimate=None, heading_estimate_status='Not present as an explicit policy state in the frozen archives; no estimate invented',
            latest_image_uint8_sha256=hashlib.sha256(latest.tobytes()).hexdigest(),
            latest_image_source='Official latest grayscale plane, diagnostic only',
            old_HUD_ROI_sum=float(obs[-1,74:83,9:14].sum()),
            core_signature_hex=latest[74:83,11:13].tobytes().hex())
        shadow_before = controller_state()
        action = np.asarray(agent.act(obs),dtype=np.float32)
        duration = (time.perf_counter()-before)*1000
        assert action.shape == (3,) and np.isfinite(action).all()
        assert np.all(action >= [-1,0,0]) and np.all(action <= [1,1,1])
        if not observed:
            observed.update(near=bool(agent.controller.lateral_acceleration == agent.lateral_safe),
                            target_calls=0, variant='hud_feedback' if original_decoder else 'nominal',
                            actual_offset=0.0, curvature=None,
                            speed_estimate=contact_observed['old_HUD_speed_m_s'],
                            target_x=None, target_forward=None, nominal_target=None)
        assert all(call_counts.get(name) == 1 for name in ('detection','tracker','route','target','ridge'))
        assert call_counts.get('controller', 0) + call_counts.get('fallback_controller', 0) == 1
        assert call_counts.get('decoder', 0) == int(original_decoder is not None and observed['target_calls'] == 1)
        route_observed.update(near=observed['near'], actual_calls=dict(call_counts),
                              visibility_explicit_speed_cap=False)
        contact_observed.update(near=observed['near'], actual_calls=dict(call_counts),
            coordinate_scope='Original image-derived x/forward returns; no new world-coordinate transform',
            returned_action=action.tolist())
        response = {'action':action.tolist(),'act_compute_ms':duration,
                    'connection_selection':getattr(connected, 'LAST_CONNECTION_EVALUATION', None),
                    'speed_constraint_probe':dict(route_observed),
                    'contact_probe':dict(contact_observed),
                    'near_curvature_probe':dict(observed),
                    'observer_extra_policy_calls':0,
                    'memory':{'previous_steer':agent.controller.previous_steer,
                              'lateral_acceleration':agent.controller.lateral_acceleration,
                              'hazards_sha256':hashlib.sha256(np.asarray(agent.hazards,dtype=np.float64).tobytes()).hexdigest(),
                              'previous_image_sha256':hashlib.sha256(agent.previous_image.tobytes()).hexdigest()}}
    if request['op'] == 'act':
        p = contact_observed
        r = route_observed
        target_x = observed.get('target_x')
        obstacles = r.get('tracked_obstacles_body', [])
        features = [float(target_x is None), float(target_x or 0),
            float(observed.get('target_forward') or 0),
            float(p.get('old_HUD_speed_m_s') or 0),
            float(p.get('actual_feedback_speed_m_s') or 0),
            float(p.get('curvature') or 0), float(p.get('target_speed_m_s') or 0),
            shadow_before['previous_steer'], float(observed['near']),
            float(r.get('route_total_polyline_length_m') or 0),
            float(r.get('path_point_count') or 0), float(len(obstacles)),
            min((float(np.hypot(x,y)) for x,y,_ in obstacles), default=100.),
            *map(float, action)]
        assert len(features) == 16 and np.isfinite(features).all()
        response['shadow_features'] = features
        response['shadow_controller_before'] = shadow_before
        response['shadow_state_after'] = dict(controller=controller_state(),
            hazards=np.asarray(agent.hazards, np.float64).reshape(-1,4).tolist(),
            previous_image_sha256=hashlib.sha256(agent.previous_image.tobytes()).hexdigest())
    if request['op'] == 'act':
        head_started=time.perf_counter()
        nominal=np.asarray(response['action'],np.float32);memory_after_nominal=controller_state()
        row=np.concatenate(((np.asarray(features,np.float64)-head_mean)/head_std,[1.]))
        logits=row@mode_weights;mode=int(np.argmax(logits));corrected=nominal.copy();corrected[1:]=0
        strength=0.
        if mode==0:strength=float(np.clip(row@gas_weights,0,1));corrected[1]=strength
        elif mode==1:strength=float(np.clip(row@brake_weights,0,1));corrected[2]=strength
        assert corrected[0]==nominal[0] and not (corrected[1]>0 and corrected[2]>0)
        response.update(nominal_action=nominal.tolist(),action=corrected.tolist(),pedal_mode=mode,
            mode_logits=logits.tolist(),mode_strength=strength,
            head_inference_ms=(time.perf_counter()-head_started)*1000,
            student_total_compute_ms=(time.perf_counter()-before)*1000)
        assert controller_state()==memory_after_nominal
        response['nominal_memory_preserved']=True
    response.update(rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                    actor_cumulative_CPU_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                    python_audit_denied_events=list(denied))
    print(json.dumps(response),flush=True)
