"""Read the official speed-bar interior only for longitudinal feedback."""

import numpy as np

from retry.schedule_agent import HazardScheduledAgent


class BarFeedbackAgent(HazardScheduledAgent):
    def __init__(self, speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe,
                 bar_integrals, bar_speeds):
        super().__init__(speed_gain, speed_bias, speed_cap, lateral_fast, lateral_safe)
        self.bar_integrals = np.asarray(bar_integrals, dtype=float)
        self.bar_speeds = np.asarray(bar_speeds, dtype=float)
        assert self.bar_integrals.ndim == self.bar_speeds.ndim == 1
        assert len(self.bar_integrals) == len(self.bar_speeds) >= 2
        assert np.isfinite(self.bar_integrals).all() and np.isfinite(self.bar_speeds).all()
        assert (np.diff(self.bar_integrals) > 0).all()
        self.warm_reference = False
        original = self.controller.action_target

        def feedback(x, forward, pixel_speed):
            action = original(x, forward, pixel_speed)
            curvature = 2 * x / max(forward * forward + x * x, 1e-6)
            target = min(self.controller.speed_cap,
                float(np.sqrt(self.controller.lateral_acceleration / (abs(curvature) + .003))))
            effective = pixel_speed if self.warm_reference else self.current_bar_speed
            changed = action.copy()
            if not self.warm_reference:
                changed[1:] = [np.clip(.08 * (target - effective), 0, .5),
                    np.clip(.04 * (effective - target), 0, .5)]
            assert changed[0] == action[0]
            self.last_features.update(target=[float(x), float(forward)], target_speed=target,
                risk_lateral=self.controller.lateral_acceleration, pixel_speed=pixel_speed,
                feedback_speed=effective, pixel_shadow_action=action.tolist(),
                actual_action=changed.tolist())
            return changed

        self.controller.action_target = feedback

    def read_bar_speed(self, image):
        # The white bar spans screen x=125..150, inside columns 11 and 12
        # after the official 96->84 resize. Reward glyphs lie to its left.
        integral = float(image[74:83, 11:13].sum())
        return float(np.interp(integral, self.bar_integrals, self.bar_speeds))

    def reset(self, observation):
        super().reset(observation)
        self.warm_reference = False

    def act(self, observation):
        self.current_bar_speed = self.read_bar_speed(observation[-1])
        self.last_features = {"bar_speed": self.current_bar_speed}
        return super().act(observation)
