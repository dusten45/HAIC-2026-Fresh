"""Pixel-only package probe in a clean directory on the existing host.

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
resource.setrlimit(resource.RLIMIT_AS, (1024*1024*1024,)*2)
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
        action = np.asarray(agent.act(obs),dtype=np.float32)
        duration = (time.perf_counter()-before)*1000
        assert action.shape == (3,) and np.isfinite(action).all()
        assert np.all(action >= [-1,0,0]) and np.all(action <= [1,1,1])
        response = {'action':action.tolist(),'act_compute_ms':duration}
    response.update(rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
                    actor_cumulative_CPU_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                    python_audit_denied_events=list(denied))
    print(json.dumps(response),flush=True)
