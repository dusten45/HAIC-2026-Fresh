"""Change only the safe-route goal's reachability; preserve the reference policy."""

import heapq

import cv2
import numpy as np

from retry.clearance_agent import road_and_obstacles
from retry.ridge_agent import ridge_path
from retry.route_agent import route_target
from retry.temporal_agent import TemporalRouteAgent


def routing_problem(image, obstacles):
    road = ((image > 0.32) & (image < 0.47)).astype(np.uint8)
    road[61:] = 0
    road = cv2.morphologyEx(road, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    distance = cv2.distanceTransform(road, cv2.DIST_L2, 5)
    allowed = distance >= 1.5
    allowed[:24] = False
    allowed[57:] = False
    allowed[:, :3] = False
    allowed[:, 81:] = False
    yy, xx = np.indices(image.shape)
    for x, y, radius in obstacles:
        clearance = 2.6 + radius
        allowed &= ((xx - 42) / 1.3608 - x) ** 2 + ((63 - yy) / 1.701 - y) ** 2 > clearance ** 2
    starts, centerline = np.flatnonzero(allowed[56]), ridge_path(image)
    if not len(starts) or not centerline:
        return allowed, distance, None, None, None, None
    start_x = int(starts[np.argmin(abs(starts - 42))])
    if abs(start_x - 42) > 12:
        return allowed, distance, None, None, None, None
    start = 56, start_x
    # Four-connectivity has exactly the reachability of eight moves that cannot
    # cross a blocked diagonal corner. Eight-connected labels alone overstate it.
    _, labels = cv2.connectedComponents(allowed.astype(np.uint8), connectivity=4)
    reachable = labels == labels[start]
    legacy_goal = connected_goal = None
    for center_x, forward in reversed(centerline):
        row = int(round(63 - forward * 1.701))
        for mask, name in [(allowed, "legacy"), (reachable, "connected")]:
            if (legacy_goal if name == "legacy" else connected_goal) is not None:
                continue
            goals = np.flatnonzero(mask[row])
            if len(goals):
                goal_x = int(goals[np.argmin(abs(goals - (42 + center_x * 1.3608)))])
                if name == "legacy":
                    legacy_goal = row, goal_x
                else:
                    connected_goal = row, goal_x
        if legacy_goal is not None and connected_goal is not None:
            break
    return allowed, distance, start, legacy_goal, connected_goal, labels


def connected_route(image, obstacles_override=None):
    obstacles = road_and_obstacles(image)[1] if obstacles_override is None else obstacles_override
    allowed, distance, start, _, goal, _ = routing_problem(image, obstacles)
    if start is None or goal is None:
        return []
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
            return [(0.0, 0.0)] + [((x - 42) / 1.3608, (63 - y) / 1.701) for y, x in reversed(result)]
        y, x = current
        for dy, dx, length in moves:
            ny, nx = y + dy, x + dx
            if not 24 <= ny <= 56 or not 3 <= nx < 81 or not allowed[ny, nx]:
                continue
            if dy and dx and (not allowed[y, nx] or not allowed[ny, x]):
                continue
            following = ny, nx
            next_cost = cost + length * (1 + 2 / max(float(distance[ny, nx]), 1.5))
            if next_cost < costs.get(following, float("inf")):
                costs[following], previous[following] = next_cost, current
                heapq.heappush(queue, (next_cost, following))
    return []


class ConnectedTemporalAgent(TemporalRouteAgent):
    def act(self, observation):
        image = observation[-1]
        speed = max(0.0, self.speed_gain * float(image[74:83, 9:14].sum()) + self.speed_bias)
        obstacles = self.tracked_obstacles(image, speed)
        target = route_target(connected_route(image, obstacles), speed)
        if target is None:
            return self.controller.action(None, speed)
        return self.controller.action_target(float(target[0]), float(target[1]), speed)
