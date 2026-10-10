"""One fixed longitudinal cap on an inherited champion; no estimator changes.

This reuses the earlier radial-distance heuristic in a different feedback
context. Center clearance is not a stopping-distance or safety guarantee.
"""
import numpy as np


def near_distance_cap(obstacles, pixel_speed):
    lookahead = float(np.clip(4 + .35 * pixel_speed, 6, 14))
    eligible = [list(h[:3]) for h in obstacles
                if h[1] > 0 and np.hypot(h[0], h[1]) <= lookahead + 2.6 + h[2]]
    clearances = [max(0., float(np.hypot(x, y)) - radius - 2.6)
                  for x, y, radius in eligible]
    cap = min([28.] + [max(4., float(np.sqrt(10. * d))) for d in clearances])
    return cap, eligible, clearances


class ChampionDistanceCapMixin:
    """Preserve inherited act/tracker/routing/steering and change pedals only."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        inherited = self.controller.action_target
        self.distance_cap_diagnostic = None

        def limited(x, forward, pixel_speed):
            action = inherited(x, forward, pixel_speed)
            curvature = 2 * x / max(forward * forward + x * x, 1e-6)
            original_target = min(self.controller.speed_cap, float(np.sqrt(
                self.controller.lateral_acceleration / (abs(curvature) + .003))))
            cap, eligible, clearances = near_distance_cap(self.hazards, pixel_speed)
            effective = min(original_target, cap)
            changed = action.copy()
            if effective < original_target:
                changed[1:] = [np.clip(.08 * (effective - pixel_speed), 0., .5),
                               np.clip(.04 * (pixel_speed - effective), 0., .5)]
            self.distance_cap_diagnostic = {
                "inherited_target": original_target, "effective_target": effective,
                "distance_cap": cap, "eligible_hazards": eligible,
                "radial_clearances": clearances, "cap_active": effective < original_target,
                "original_action": action.tolist()}
            return changed
        self.controller.action_target = limited

    def act(self, observation):
        self.distance_cap_diagnostic = None
        return super().act(observation)
