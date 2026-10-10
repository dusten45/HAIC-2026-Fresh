"""Isolated pixel policy worker without trajectory or diagnostic exports."""
import base64
import json
from pathlib import Path
import resource
import sys

resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
package = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(package))
import numpy as np
from agent import Agent

agent = Agent()
modules = {name: str(Path(module.__file__).resolve())
           for name, module in sys.modules.items()
           if (name == 'agent' or name == 'retry' or name.startswith('retry.'))
           and getattr(module, '__file__', None)}
assert all(Path(path).is_relative_to(package) for path in modules.values())
assert not any(name.startswith(('core', 'env_wrapper')) for name in sys.modules)
print(json.dumps({'ready': True, 'simulator_imported': False,
                  'policy_modules': modules, 'diagnostic_exports': False}), flush=True)
for line in sys.stdin:
    request = json.loads(line)
    assert set(request) == {'op', 'observation'}
    observation = np.frombuffer(base64.b64decode(request['observation']),
                                dtype=np.float32).reshape(4, 84, 84).copy()
    if request['op'] == 'reset':
        agent.reset(observation)
        response = {'ok': True}
    else:
        assert request['op'] == 'act'
        action = np.asarray(agent.act(observation), dtype=np.float32)
        response = {'action': action.tolist(),
                    'rss_mib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
                    'actor_cumulative_CPU_s': (resource.getrusage(resource.RUSAGE_SELF).ru_utime
                                              + resource.getrusage(resource.RUSAGE_SELF).ru_stime)}
    print(json.dumps(response), flush=True)
