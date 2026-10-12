"""Submission Agent: unchanged normal24 nominal policy plus frozen231 pedals.

Only image-derived nominal-call features enter the head. Corrected pedals are
returned after nominal state updates; they are never fed into nominal memory.
The builder installs this file as the ZIP root agent.py.
"""
import numpy as np
from retry.schedule_agent import HazardScheduledAgent, connected_route, route_target, decode_feedback_speed
from retry.submission232_model import HEAD_MEAN, HEAD_STD, HEAD_WEIGHTS


class Agent(HazardScheduledAgent):
    def __init__(self):
        super().__init__(11.4142485314592, -6.545558315185489, 45.0, 24.0, 8.0)

    def correct_pedals(self, features, nominal):
        standardized = (np.asarray(features, np.float64) - HEAD_MEAN) / HEAD_STD
        row = np.concatenate((standardized, [1.]))
        residual = np.clip(row @ HEAD_WEIGHTS, -0.5, 0.5)
        corrected = np.asarray(nominal, np.float32).copy()
        corrected[1:] = np.clip(corrected[1:].astype(np.float64) + residual, 0., 1.).astype(np.float32)
        return corrected

    def act(self, observation):
        image = observation[-1]
        previous_steer = float(self.controller.previous_steer)
        speed = max(0.0, self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        obstacles = self.tracked_obstacles(image, speed)
        lookahead = float(np.clip(4 + 0.35 * speed, 6, 14))
        near = not getattr(self, 'warming_fixed_reference', False) and any(
            y > 0 and np.hypot(x, y) <= lookahead + 2.6 + radius for x, y, radius in obstacles)
        self.controller.lateral_acceleration = self.lateral_safe if near else self.lateral_fast
        path = connected_route(image, obstacles, speed=speed, previous_steer=self.controller.previous_steer)
        points = np.asarray(path, np.float64).reshape(-1, 2)
        length = sum(float(np.linalg.norm(b-a)) for a, b in zip(points[:-1], points[1:]))
        target = route_target(path, speed)
        if target is None:
            nominal = np.asarray(self.controller.action(None, speed), np.float32)
            x = forward = curvature = target_speed = 0.0
            feedback = speed
        else:
            x, forward = float(target[0]), float(target[1])
            feedback = float(decode_feedback_speed(image, speed))
            curvature = 2 * x / max(forward * forward + x * x, 1e-6)
            target_speed = min(float(self.controller.speed_cap), float(np.sqrt(
                float(self.controller.lateral_acceleration) / max(abs(curvature), 1e-6))))
            nominal = np.asarray(self.controller.action_target(x, forward, speed, pedal_speed=feedback), np.float32)
        features = [float(target is None), float(x or 0), float(forward or 0),
            float(speed or 0), float(feedback or 0), float(curvature or 0), float(target_speed or 0),
            previous_steer, float(self.controller.lateral_acceleration == self.lateral_safe),
            float(length or 0), float(len(path)), float(len(obstacles)),
            min((float(np.hypot(ox, oy)) for ox, oy, _ in obstacles), default=100.),
            *map(float, nominal)]
        return self.correct_pedals(features, nominal)
