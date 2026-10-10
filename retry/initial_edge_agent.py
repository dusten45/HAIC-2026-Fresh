"""Check the synthetic origin edge; preserve the legacy route on unsupported starts.

The existing planning mask excludes the vehicle origin. Rejection therefore
means missing planning support, not a privileged assertion that the car is off
the road. No road pixels, clearance thresholds or controller rules are changed.
"""

import numpy as np

from retry.connected_agent import connected_route, routing_problem
from retry.route_agent import route_target
from retry.schedule_agent import HazardScheduledAgent


def edge_cells(start, end):
    """All raster cells touched by a centre-to-centre segment, including corners.

    At a diagonal grid corner both orthogonal neighbours are included, matching
    the legacy route's prohibition on cutting a blocked diagonal corner.
    """
    y, x = start
    end_y, end_x = end
    nx, ny = abs(end_x - x), abs(end_y - y)
    sx = 1 if end_x > x else -1
    sy = 1 if end_y > y else -1
    ix = iy = 0
    cells = [(y, x)]
    while ix < nx or iy < ny:
        decision = (1 + 2 * ix) * ny - (1 + 2 * iy) * nx
        if decision == 0:
            cells.extend([(y, x + sx), (y + sy, x)])
            x, y = x + sx, y + sy
            ix, iy = ix + 1, iy + 1
        elif decision < 0:
            x += sx
            ix += 1
        else:
            y += sy
            iy += 1
        cells.append((y, x))
    return cells


def check_initial_edge(allowed, first_grid_point):
    """Apply the unchanged mask and corner constraints to the complete first edge."""
    point = np.asarray(first_grid_point, dtype=np.float64)
    if point.shape != (2,) or not np.isfinite(point).all():
        return {"accepted": False, "reason": "nonfinite_initial_endpoint"}
    start = (63, 42)
    end = (int(round(63 - point[1] * 1.701)),
           int(round(42 + point[0] * 1.3608)))
    cells = edge_cells(start, end)
    for index, (row, column) in enumerate(cells):
        if not (0 <= row < allowed.shape[0] and 0 <= column < allowed.shape[1]):
            reason = "initial_edge_outside_image"
        elif not allowed[row, column]:
            reason = ("origin_outside_planning_support" if index == 0
                      else "initial_edge_outside_constraints")
        else:
            continue
        return {"accepted": False, "reason": reason,
                "first_rejected_cell": [row, column],
                "edge_cells": len(cells), "checked_cells": index + 1}
    return {"accepted": True, "reason": "initial_edge_checked",
            "edge_cells": len(cells), "checked_cells": len(cells)}


def initial_edge_route(image, obstacles):
    """Return a checked route or the exact original route as the required fallback."""
    original = connected_route(image, obstacles)
    if not original:
        return original, {"accepted": False, "reason": "legacy_no_route",
                          "fallback": True}
    allowed, _, _, _, _, _ = routing_problem(image, obstacles)
    diagnostic = check_initial_edge(allowed, original[1])
    diagnostic["fallback"] = not diagnostic["accepted"]
    # A rejection must not invoke route-none braking or reset tracking/steering.
    # The legacy path is also the checked path when its initial edge passes.
    return original, diagnostic


class InitialEdgeCheckedAgent(HazardScheduledAgent):
    def reset(self, observation):
        super().reset(observation)
        self.route_diagnostic = None

    def act(self, observation):
        image = observation[-1]
        speed = max(0.0, self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        obstacles = self.tracked_obstacles(image, speed)
        lookahead = float(np.clip(4 + 0.35 * speed, 6, 14))
        near = not getattr(self, "warming_fixed_reference", False) and any(
            y > 0 and np.hypot(x, y) <= lookahead + 2.6 + radius for x, y, radius in obstacles)
        self.controller.lateral_acceleration = self.lateral_safe if near else self.lateral_fast
        path, self.route_diagnostic = initial_edge_route(image, obstacles)
        target = route_target(path, speed)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
