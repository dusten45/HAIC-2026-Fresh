"""Connect an unknown origin to the fixed first supported forward corridor.

Road support outside the original grid is unknown, never filled as free space.
Only the initial connection/start selection changes. Tracked-obstacle clearance,
grid goal priority, costs/corners, memory and the existing controller stay fixed.
"""

import heapq

import numpy as np

from retry.connected_agent import connected_route, routing_problem
from retry.ridge_agent import ridge_path
from retry.route_agent import route_target
from retry.schedule_agent import HazardScheduledAgent


def connector_clear(point, obstacles):
    """Reject any observed/tracked inflated obstacle touching the entire link."""
    point = np.asarray(point, dtype=np.float64)
    squared = float(np.dot(point, point))
    for x, y, radius in obstacles:
        obstacle = np.array([x, y], dtype=np.float64)
        fraction = float(np.clip(np.dot(point, obstacle) / squared, 0, 1))
        if np.linalg.norm(obstacle - fraction * point) <= 2.6 + radius:
            return False
    return True


def unknown_origin_route(image, obstacles):
    original = connected_route(image, obstacles)
    diagnostic = {"road_support_before_corridor": "unknown",
                  "corridor_row": 56, "fallback": False, "changed": False}
    if not original:
        diagnostic.update(reason="legacy_no_route", fallback=True)
        return original, diagnostic
    if connector_clear(original[1], obstacles):
        diagnostic.update(reason="legacy_connector_clear")
        return original, diagnostic

    allowed, distance, _, _, _, labels = routing_problem(image, obstacles)
    starts = [int(x) for x in np.flatnonzero(allowed[56])
              if abs(int(x) - 42) <= 12
              and connector_clear(((int(x) - 42) / 1.3608, 7 / 1.701), obstacles)]
    if not starts:
        diagnostic.update(reason="no_obstacle_clear_forward_connection", fallback=True)
        return original, diagnostic
    # Preserve the original nearest-centre order and increasing-column tie break.
    start = (56, min(starts, key=lambda x: abs(x - 42)))
    reachable = labels == labels[start]
    goal = None
    for center_x, forward in reversed(ridge_path(image)):
        row = int(round(63 - forward * 1.701))
        goals = np.flatnonzero(reachable[row])
        if len(goals):
            goal = (row, int(goals[np.argmin(abs(goals - (42 + center_x * 1.3608)))]))
            break
    if goal is None:
        diagnostic.update(reason="no_connected_forward_goal", fallback=True)
        return original, diagnostic

    costs, previous, queue = {start: 0.0}, {}, [(0.0, start)]
    moves = [(dy, dx, float(np.hypot(dx / 1.3608, dy / 1.701)))
             for dy in [-1, 0, 1] for dx in [-1, 0, 1] if dy or dx]
    while queue:
        cost, current = heapq.heappop(queue)
        if cost != costs[current]:
            continue
        if current == goal:
            result = [current]
            while result[-1] != start:
                result.append(previous[result[-1]])
            path = [(0.0, 0.0)] + [((x - 42) / 1.3608, (63 - y) / 1.701)
                                   for y, x in reversed(result)]
            diagnostic.update(reason="changed_forward_connection", changed=True,
                              start=list(start), goal=list(goal))
            return path, diagnostic
        y, x = current
        for dy, dx, length in moves:
            ny, nx = y + dy, x + dx
            if not 24 <= ny <= 56 or not 3 <= nx < 81 or not allowed[ny, nx]:
                continue
            if dy and dx and (not allowed[y, nx] or not allowed[ny, x]):
                continue
            following = (ny, nx)
            next_cost = cost + length * (1 + 2 / max(float(distance[ny, nx]), 1.5))
            if next_cost < costs.get(following, float("inf")):
                costs[following], previous[following] = next_cost, current
                heapq.heappush(queue, (next_cost, following))
    diagnostic.update(reason="grid_search_failed", fallback=True)
    return original, diagnostic


class UnknownOriginAgent(HazardScheduledAgent):
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
        path, self.route_diagnostic = unknown_origin_route(image, obstacles)
        target = route_target(path, speed)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
