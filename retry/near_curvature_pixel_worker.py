"""Pixel-only actor with read-only same-input curvature-term diagnostics.

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

agent = Agent()
assert (agent.lateral_fast, agent.lateral_safe) == (7.0, 5.0)
observed = {}
original_control = agent.controller.action_target
restores_near = 'curvature_offset' in original_control.__code__.co_varnames


def control(x, forward, speed, **kwargs):
    assert not observed, 'More than one target control call in an act'
    near = agent.controller.lateral_acceleration == agent.lateral_safe
    offset = kwargs.get('curvature_offset', 0.0)
    assert set(kwargs) <= {'curvature_offset'}
    if restores_near:
        assert offset == (0.003 if near else 0.0)
    else:
        assert not kwargs
    action = original_control(x, forward, speed, **kwargs)
    curvature = 2 * x / max(forward * forward + x * x, 1e-6)
    lateral, cap = agent.controller.lateral_acceleration, agent.controller.speed_cap
    nominal = min(cap, float(np.sqrt(lateral / max(abs(curvature), 1e-6))))
    restored = min(cap, float(np.sqrt(lateral / (abs(curvature) + 0.003)))) if near else nominal
    def shadow(target):
        return np.array([action[0], float(np.clip(0.08 * (target - speed), 0, 0.5)),
                         float(np.clip(0.04 * (speed - target), 0, 0.5))], dtype=np.float32)
    a, b = shadow(nominal), shadow(restored)
    assert np.array_equal(action, b if restores_near else a)
    assert restored <= nominal and b[1] <= a[1] and b[2] >= a[2]
    observed.update(near=bool(near), target_calls=1,
                    variant='near_restore' if restores_near else 'nominal',
                    actual_offset=float(offset), curvature=float(curvature),
                    speed_estimate=float(speed), target_x=float(x), target_forward=float(forward),
                    nominal_target=nominal, restored_target=restored,
                    target_reduction=nominal-restored,
                    nominal_action=a.tolist(), restored_action=b.tolist(),
                    would_change_action=not np.array_equal(a, b),
                    gas_reduction=float(a[1])-float(b[1]),
                    brake_increase=float(b[2])-float(a[2]))
    return action


agent.controller.action_target = control
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
        observed.clear()
        action = np.asarray(agent.act(obs),dtype=np.float32)
        duration = (time.perf_counter()-before)*1000
        assert action.shape == (3,) and np.isfinite(action).all()
        assert np.all(action >= [-1,0,0]) and np.all(action <= [1,1,1])
        if not observed:
            observed.update(near=bool(agent.controller.lateral_acceleration == agent.lateral_safe),
                            target_calls=0, variant='near_restore' if restores_near else 'nominal',
                            actual_offset=0.0, nominal_target=None, restored_target=None,
                            target_reduction=0.0, nominal_action=action.tolist(),
                            restored_action=action.tolist(), would_change_action=False,
                            gas_reduction=0.0, brake_increase=0.0)
        response = {'action':action.tolist(),'act_compute_ms':duration,
                    'near_curvature_probe':dict(observed),
                    'observer_extra_policy_calls':0,
                    'memory':{'previous_steer':agent.controller.previous_steer,
                              'lateral_acceleration':agent.controller.lateral_acceleration,
                              'hazards_sha256':hashlib.sha256(np.asarray(agent.hazards,dtype=np.float64).tobytes()).hexdigest(),
                              'previous_image_sha256':hashlib.sha256(agent.previous_image.tobytes()).hexdigest()}}
    response.update(rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                    actor_cumulative_CPU_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                    python_audit_denied_events=list(denied))
    print(json.dumps(response),flush=True)
