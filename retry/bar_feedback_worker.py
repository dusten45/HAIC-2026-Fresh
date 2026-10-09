"""Trusted transport for a current-pixel bar-feedback prototype."""

import base64
import json
from pathlib import Path
import resource
import sys

resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))

import numpy as np
from retry.bar_feedback_agent import BarFeedbackAgent

table = json.loads(Path(sys.argv[6]).read_text())
agent = BarFeedbackAgent(*map(float, sys.argv[1:6]), table["integrals"], table["speeds"])
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
