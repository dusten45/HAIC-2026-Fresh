"""Trusted pixel-only process worker for registered memory contrasts."""

import base64
import json
import resource
import sys

resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))

import numpy as np
from retry.memory_agent import FreshDetectionAgent

if sys.argv[1] == "minimal":
    from retry.memory_agent import MinimalMemoryAgent
    cls = MinimalMemoryAgent
else:
    assert sys.argv[1] == "fresh"
    cls = FreshDetectionAgent
agent = cls(*map(float, sys.argv[2:7]))
print(json.dumps({"ready": True, "simulator_imported": any(n.startswith(("core", "env_wrapper")) for n in sys.modules),
    "rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}), flush=True)
for line in sys.stdin:
    request = json.loads(line)
    observation = np.frombuffer(base64.b64decode(request["observation"]), dtype=np.float32).reshape(4, 84, 84).copy()
    if request["op"] == "reset":
        agent.reset(observation)
        response = {"ok": True}
    else:
        response = {"action": np.asarray(agent.act(observation), dtype=np.float32).tolist(),
            "rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}
    print(json.dumps(response), flush=True)
