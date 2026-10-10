"""One longitudinal target intervention on an inherited pixel-only ROI policy.

Distance is tracked hazard center distance, not distance along the planned route.
The planning deceleration and creep floor are hypotheses, not safety guarantees.
"""

import numpy as np


class DistanceTargetMixin:
    def __init__(self, mode="distance", **kwargs):
        assert mode in ("roi", "distance", "slow")
        super().__init__(**kwargs)
        self.target_mode = mode
        self.intervention_enabled = True
        inherited = self.controller.action_target

        def limited(x, forward, pixel_speed):
            action = inherited(x, forward, pixel_speed)
            features = self.last_features
            original_target = float(features["target_speed"])
            lookahead = float(np.clip(4 + .35 * pixel_speed, 6, 14))
            eligible = [list(h[:3]) for h in self.hazards
                        if h[1] > 0 and np.hypot(h[0], h[1]) <= lookahead + 2.6 + h[2]]
            clearances = [max(0., float(np.hypot(h[0], h[1])) - h[2] - 2.6)
                          for h in eligible]
            distance_cap = min([28.] + [max(4., float(np.sqrt(10. * d)))
                                       for d in clearances])
            cap = 28.
            if self.intervention_enabled:
                if self.target_mode == "distance":
                    cap = distance_cap
                elif self.target_mode == "slow":
                    cap = 4.
            effective_target = min(original_target, cap)
            changed = action.copy()
            if effective_target < original_target:
                speed = float(features["feedback_speed"])
                changed[1:] = [np.clip(.08 * (effective_target - speed), 0., .5),
                              np.clip(.04 * (speed - effective_target), 0., .5)]
            assert changed[0] == action[0]
            features.update(inherited_target=original_target,
                            effective_target=effective_target,
                            eligible_hazards=eligible, radial_clearances=clearances,
                            distance_cap=distance_cap,
                            cap_active=effective_target < original_target,
                            roi_shadow_action=action.tolist(), actual_action=changed.tolist())
            return changed

        self.controller.action_target = limited
