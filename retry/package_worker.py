"""External worker loads an extracted ZIP entrypoint, not checkout policy modules."""

import base64
import json
from pathlib import Path
import resource
import sys

resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
package_root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(package_root))

import numpy as np
from agent import Agent


agent = Agent()
policy_modules = {name: str(Path(module.__file__).resolve()) for name, module in sys.modules.items()
                  if (name == "agent" or name == "retry" or name.startswith("retry.")) and getattr(module, "__file__", None)}
assert all(Path(path).is_relative_to(package_root) for path in policy_modules.values())
print(json.dumps({"ready": True, "policy_modules": policy_modules,
    "simulator_imported": any(n.startswith(("core", "env_wrapper")) for n in sys.modules),
    "rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}), flush=True)
for line in sys.stdin:
    request = json.loads(line)
    if request["op"] == "exit":
        break
    observation = np.frombuffer(base64.b64decode(request["observation"]),
                                dtype=np.float32).reshape(4, 84, 84).copy()
    if request["op"] == "reset":
        agent.reset(observation)
        response = {"ok": True}
    else:
        response = {"action": np.asarray(agent.act(observation), dtype=np.float32).tolist(),
                    "rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}
    print(json.dumps(response), flush=True)
