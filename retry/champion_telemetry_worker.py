"""Isolated pixel actor; optional read-only hooks preserve original call results.

Usage: python champion_telemetry_worker.py PACKAGE [--plain]
Simulator truth, case identities and evaluator metadata are never inputs.
"""
import base64
import hashlib
import json
from pathlib import Path
import resource
import sys

resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024,) * 2)
resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
root = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(root))
import numpy as np
from agent import Agent

agent = Agent()
modules = {n: str(Path(m.__file__).resolve()) for n, m in sys.modules.items()
           if (n == "agent" or n == "retry" or n.startswith("retry."))
           and getattr(m, "__file__", None)}
assert all(Path(f).is_relative_to(root) for f in modules.values())
assert not any(n.startswith(("core", "env_wrapper")) for n in sys.modules)
observed = {}
if "--plain" not in sys.argv[2:]:
    original_tracker = agent.tracked_obstacles
    def tracker(image, speed):
        obstacles = original_tracker(image, speed)
        lookahead = float(np.clip(4 + 0.35 * speed, 6, 14))
        observed.update(speed_estimate=float(speed), tracked_obstacle_count=len(obstacles),
                        tracked_max_age=max((p[3] for p in agent.hazards), default=0),
                        hazard_near=bool(not getattr(agent, "warming_fixed_reference", False) and any(
                            y > 0 and np.hypot(x, y) <= lookahead + 2.6 + radius
                            for x, y, radius in obstacles)))
        return obstacles
    agent.tracked_obstacles = tracker
    connected = sys.modules["retry.connected_agent"]
    original_ridge = connected.ridge_path
    def ridge(image):
        path = original_ridge(image)
        observed["centerline_points"] = len(path)
        return path
    connected.ridge_path = ridge
    schedule = sys.modules["retry.schedule_agent"]
    original_route = schedule.connected_route
    def route(image, obstacles):
        path = original_route(image, obstacles)
        observed["path_points"] = len(path)
        return path
    schedule.connected_route = route
    original_target = schedule.route_target
    def target(path, speed):
        point = original_target(path, speed)
        observed["route_target_missing"] = point is None
        return point
    schedule.route_target = target
    original_control = agent.controller.action_target
    def control(x, forward, speed):
        action = original_control(x, forward, speed)
        curvature = 2 * x / max(forward * forward + x * x, 1e-6)
        target_speed = min(agent.controller.speed_cap, float(np.sqrt(
            agent.controller.lateral_acceleration / (abs(curvature) + .003))))
        observed.update(target_x=float(x), target_forward=float(forward),
                        curvature=float(curvature), target_speed=float(target_speed))
        return action
    agent.controller.action_target = control

print(json.dumps({"ready": True, "simulator_imported": False,
                  "policy_modules": modules, "plain": "--plain" in sys.argv[2:]}), flush=True)
for line in sys.stdin:
    request = json.loads(line)
    assert set(request) == {"op", "observation"}
    obs = np.frombuffer(base64.b64decode(request["observation"]), dtype=np.float32).reshape(4, 84, 84).copy()
    if request["op"] == "reset":
        agent.reset(obs)
        result = {"ok": True}
    else:
        assert request["op"] == "act"
        observed.clear()
        action = np.asarray(agent.act(obs), dtype=np.float32)
        result = {"action": action.tolist(), "policy": dict(observed), "memory": {
            "previous_steer": agent.controller.previous_steer,
            "lateral_acceleration": agent.controller.lateral_acceleration,
            "hazards_sha256": hashlib.sha256(np.asarray(agent.hazards, dtype=np.float64).tobytes()).hexdigest(),
            "previous_image_sha256": hashlib.sha256(agent.previous_image.tobytes()).hexdigest()},
            "rss_mib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            "actor_cumulative_CPU_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime + resource.getrusage(resource.RUSAGE_SELF).ru_stime}
    print(json.dumps(result), flush=True)
