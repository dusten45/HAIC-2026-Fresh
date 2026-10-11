"""One frozen scalar intervention using only existing pixel-policy quantities.

The original action_target runs once. Its full-precision smoothed steering and
age-zero distance cap are retained; only pedals can change inside the gate.
The original distance_cap_diagnostic remains the unmodified coefficient-7
calculation at the current input. curve_diagnostic reports the applied target.
"""
import math
import numpy as np


def gate(curvature, steer, near):
    return not near and .015 <= abs(curvature) <= .05 and abs(steer) <= .18


def install(agent, coefficient):
    coefficient = float(coefficient)
    if coefficient not in (7., 8., 10., 14.):
        raise ValueError("coefficient is outside the preregistered set")
    inherited = agent.controller.action_target
    agent.curve_diagnostic = None

    def limited(x, forward, speed):
        original = inherited(x, forward, speed)
        curvature = 2*x / max(forward*forward+x*x, 1e-6)
        steer = float(agent.controller.previous_steer)
        # Frozen schedule sets exactly 5 for near and 7 for not-near. Verify
        # independently from the same tracked pixel geometry used by schedule.
        lookahead = float(np.clip(4+.35*speed, 6, 14))
        near = any(y > 0 and np.hypot(xh, y) <= lookahead+2.6+radius
                   for xh, y, radius, _age in agent.hazards)
        assert not getattr(agent, "warming_fixed_reference", False)
        assert agent.controller.lateral_acceleration == (5. if near else 7.)
        assert agent.controller.speed_cap == 28.
        active = gate(curvature, steer, near)
        base = float(agent.distance_cap_diagnostic["effective_target"])
        distance = float(agent.distance_cap_diagnostic["distance_cap"])
        target = min(28., math.sqrt(coefficient/(abs(curvature)+.003)), distance) if active and coefficient != 7. else base
        changed = original
        if target > base:
            changed = original.copy()
            changed[1:] = [np.clip(.08*(target-speed), 0., .5),
                           np.clip(.04*(speed-target), 0., .5)]
        agent.curve_diagnostic = {
            "coefficient": coefficient, "gate": active, "near": near,
            "curvature": curvature, "existing_smoothed_steer": steer,
            "baseline_final_target": base, "applied_final_target": target,
            "target_delta": target-base, "baseline_action": original.tolist(),
            "throttle_delta": float(changed[1])-float(original[1]),
            "brake_delta": float(changed[2])-float(original[2]),
            "steering_unchanged": float(changed[0]) == float(original[0]),
            "original_controller_calls": 1,
        }
        return changed

    agent.controller.action_target = limited
