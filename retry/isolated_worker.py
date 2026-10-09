"""Research participant subprocess. Never include this harness in a submission."""

import base64
import json
import resource
import sys
import time

resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
resource.setrlimit(resource.RLIMIT_CPU, (30, 30))

import numpy as np

from retry.pixel_agent import PixelAgent


def emit(value):
    print(json.dumps(value), flush=True)


if sys.argv[1] in ["geometry", "clearance", "arc"]:
    if sys.argv[1] == "geometry":
        from retry.geometry_agent import GeometryAgent as Policy
    elif sys.argv[1] == "clearance":
        from retry.clearance_agent import ClearanceAgent as Policy
    else:
        from retry.arc_agent import ArcAgent as Policy
    agent = Policy(float(sys.argv[3]), float(sys.argv[4]))
else:
    agent = PixelAgent(adaptive=sys.argv[1] == "adaptive")
fault = sys.argv[2] if len(sys.argv) > 2 else "none"
emit({"ready": True, "rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
      "simulator_imported": any(n.startswith(("core", "env_wrapper")) for n in sys.modules)})
for line in sys.stdin:
    request = json.loads(line)
    if request["op"] == "exit":
        break
    observation = np.frombuffer(base64.b64decode(request["observation"]),
                                dtype=np.float32).reshape(4, 84, 84).copy()
    if request["op"] == "reset":
        agent.reset(observation)
        emit({"ok": True})
        continue
    if fault == "timeout":
        time.sleep(30)
    elif fault == "memory":
        try:
            allocation = bytearray(1024 * 1024 * 1024)
            emit({"allocation_blocked": False})
        except MemoryError:
            emit({"allocation_blocked": True})
        break
    elif fault == "crash":
        sys.exit(7)
    action = [0.0, float("nan"), 0.0] if fault == "invalid" else agent.act(observation).tolist()
    emit({"action": action, "rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024})
