"""Experimental current-detection scope for the additional distance cap.

Tracker memory remains available to inherited routing and steering. Missing
current detections can be occlusion; age is not a physical risk label.
"""
import numpy as np

from retry.champion_distance_cap import near_distance_cap


class ChampionFreshDistanceCapMixin:
    """Select age-zero cap inputs while preserving inherited control calls."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inherited = self.controller.action_target
        self.distance_cap_diagnostic = None

        def limited(x, forward, pixel_speed):
            action = inherited(x, forward, pixel_speed)
            curvature = 2 * x / max(forward * forward + x * x, 1e-6)
            original_target = min(self.controller.speed_cap, float(np.sqrt(
                self.controller.lateral_acceleration / (abs(curvature) + .003))))
            cap_inputs = [h for h in self.hazards if h[3] == 0]
            cap, eligible, clearances = near_distance_cap(cap_inputs, pixel_speed)
            effective = min(original_target, cap)
            changed = action.copy()
            if effective < original_target:
                changed[1:] = [np.clip(.08 * (effective - pixel_speed), 0., .5),
                               np.clip(.04 * (pixel_speed - effective), 0., .5)]
            self.distance_cap_diagnostic = {
                "inherited_target": original_target, "effective_target": effective,
                "distance_cap": cap, "eligible_hazards": eligible,
                "radial_clearances": clearances, "cap_active": effective < original_target,
                "original_action": action.tolist(), "cap_input_scope": "age_zero",
                "tracked_hazard_count": len(self.hazards), "cap_input_count": len(cap_inputs)}
            return changed
        self.controller.action_target = limited

    def act(self, observation):
        self.distance_cap_diagnostic = None
        return super().act(observation)
