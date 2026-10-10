"""Current-pixel-only transport; branch activation belongs to the trusted harness."""

import base64
import hashlib
import json
from pathlib import Path
import resource
import sys

resource.setrlimit(resource.RLIMIT_AS, (1024 ** 3,) * 2)
resource.setrlimit(resource.RLIMIT_NOFILE, (64,) * 2)
resource.setrlimit(resource.RLIMIT_CPU, (30,) * 2)
package = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(package))

import numpy as np
from agent import Agent
from retry.distance_target_agent import DistanceTargetMixin


class Policy(DistanceTargetMixin, Agent):
    pass


actor = Policy(mode=sys.argv[2])
prefix_kind = sys.argv[3]
modules = {n: str(Path(m.__file__).resolve()) for n, m in sys.modules.items()
           if (n == "agent" or n == "retry" or n.startswith("retry."))
           and getattr(m, "__file__", None)}
assert all(Path(v).is_relative_to(package) for v in modules.values())
assert not any(n.startswith(("core", "env_wrapper")) for n in sys.modules)


def snapshot():
    image = actor.previous_image
    return {"previous_steer": actor.controller.previous_steer,
            "hazards": actor.hazards,
            "previous_image_sha256": None if image is None else hashlib.sha256(image.tobytes()).hexdigest()}


print(json.dumps({"ready": True, "simulator_imported": False,
                  "policy_modules": modules}), flush=True)
for line in sys.stdin:
    request = json.loads(line)
    assert set(request) == {"op", "observation"}
    observation = np.frombuffer(base64.b64decode(request["observation"]),
                                dtype=np.float32).reshape(4, 84, 84).copy()
    if request["op"] == "reset":
        actor.reset(observation)
        actor.intervention_enabled = False
        actor.warm_reference = prefix_kind == "champion"
        response = {"ok": True}
    elif request["op"] == "activate":
        actor.intervention_enabled = True
        actor.warm_reference = False
        response = {"ok": True, "policy_state": snapshot()}
    else:
        assert request["op"] == "act"
        before = snapshot()
        action = np.asarray(actor.act(observation), dtype=np.float32)
        response = {"action": action.tolist(), "features": actor.last_features,
                    "policy_state_before": before, "policy_state_after": snapshot(),
                    "rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}
    print(json.dumps(response), flush=True)
