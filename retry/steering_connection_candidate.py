"""Add one nominal steering-transition term to a fixed pixel route family."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile

BASE_SHA256 = '945f9d04caf5a85efbfd33a7b56f6b8dc0bef688b202a7281659d516ff0c9cc2'
ROUTER = 'retry/connected_agent.py'
SCHEDULE = 'retry/schedule_agent.py'

ROUTE_CODE = '''def _shortest_route(allowed, distance, start, goal):
    if start is None or goal is None:
        return [], float("inf")
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
            path = [(0.0, 0.0)] + [((x - 42) / 1.3608, (63 - y) / 1.701) for y, x in reversed(result)]
            return path, cost
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
    return [], float("inf")


def route_candidates(image, obstacles):
    allowed, distance, start, _, goal, _ = routing_problem(image, obstacles)
    path, cost = _shortest_route(allowed, distance, start, goal)
    if not path:
        return []
    candidates = [{"path": path, "base_cost_m": cost, "side": "original"}]
    crossings = [(float(y), float(x), int(round(63 - y * 1.701)))
                 for x, y, radius in obstacles
                 if y > 0 and goal[0] < int(round(63 - y * 1.701)) < start[0]]
    if not crossings:
        return candidates
    _, x, row = min(crossings)
    boundary = 42 + 1.3608 * x
    for side in ["left", "right"]:
        constrained = allowed.copy()
        columns = np.arange(allowed.shape[1])
        constrained[row] &= columns < boundary if side == "left" else columns > boundary
        alternative, alternate_cost = _shortest_route(constrained, distance, start, goal)
        if alternative and not any(alternative == c["path"] for c in candidates):
            assert alternate_cost >= cost - 1e-9
            candidates.append({"path": alternative, "base_cost_m": alternate_cost, "side": side})
    return candidates


def choose_route(candidates, speed, previous_steer, connection_weight=1.0):
    if not candidates:
        return [], {"candidate_count": 0, "selected_index": None}
    scores, details = [], []
    for i, candidate in enumerate(candidates):
        target = route_target(candidate["path"], speed)
        x, forward = map(float, target)
        curvature = 2 * x / max(forward * forward + x * x, 1e-6)
        raw = float(np.clip(np.arctan(3.24 * curvature), -0.4, 0.4))
        next_steer = 0.8 * raw + 0.2 * previous_steer
        connection = max(0.0, speed) * abs(next_steer - previous_steer) / 3.0
        base_gap = max(0.0, candidate["base_cost_m"] - candidates[0]["base_cost_m"])
        if base_gap < 1e-9:
            base_gap = 0.0
        scores.append((base_gap + connection_weight * connection, i))
        details.append({"base_gap_m": base_gap, "connection_m": connection,
                        "next_steer": next_steer, "side": candidate["side"]})
    selected = min(scores)[1]
    return candidates[selected]["path"], {"candidate_count": len(candidates),
        "selected_index": selected, "previous_command_proxy": previous_steer,
        "speed_estimate_m_s": speed, "connection_weight": connection_weight,
        "candidate_scores": details}


def connected_route(image, obstacles_override=None, speed=0.0, previous_steer=0.0):
    global LAST_CONNECTION_EVALUATION
    obstacles = road_and_obstacles(image)[1] if obstacles_override is None else obstacles_override
    candidates = route_candidates(image, obstacles)
    path, LAST_CONNECTION_EVALUATION = choose_route(candidates, speed, previous_steer)
    return path
'''


def build(source, destination):
    source, destination = Path(source), Path(destination)
    digest = lambda data: hashlib.sha256(data).hexdigest()
    assert digest(source.read_bytes()) == BASE_SHA256
    with zipfile.ZipFile(source) as original:
        names = original.namelist()
        before = {n: original.read(n) for n in names}
        router = before[ROUTER].decode()
        node = next(n for n in ast.parse(router).body if isinstance(n, ast.FunctionDef) and n.name == 'connected_route')
        lines = router.splitlines(keepends=True)
        router = ''.join(lines[:node.lineno - 1]) + ROUTE_CODE + ''.join(lines[node.end_lineno:])
        schedule = before[SCHEDULE].decode()
        old = 'target = route_target(connected_route(image, obstacles), speed)'
        new = 'target = route_target(connected_route(image, obstacles, speed=speed, previous_steer=self.controller.previous_steer), speed)'
        assert schedule.count(old) == 1
        schedule = schedule.replace(old, new)
        after = {**before, ROUTER: router.encode(), SCHEDULE: schedule.encode()}
        for name in [ROUTER, SCHEDULE]:
            ast.parse(after[name], filename=name)
        with zipfile.ZipFile(destination, 'x') as output:
            for info in original.infolist():
                output.writestr(info, after[info.filename])
    destination.chmod(0o600)
    with zipfile.ZipFile(destination) as output:
        assert output.namelist() == names
        assert [n for n in names if output.read(n) != before[n]] == [ROUTER, SCHEDULE]
    return {'status': 'BUILT_NOT_EXECUTED', 'base_sha256': BASE_SHA256,
            'archive_sha256': digest(destination.read_bytes()),
            'changed_members': [ROUTER, SCHEDULE],
            'unchanged_members': [n for n in names if n not in [ROUTER, SCHEDULE]],
            'members_sha256': {n: digest(b) for n, b in after.items()},
            'single_change': 'One soft nominal steering-transition length in fixed route selection; schedule only passes existing state.',
            'GT_or_identity_data_in_candidate': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    receipt = build(args.source, args.output)
    with args.receipt.open('x') as f:
        json.dump(receipt, f, indent=2); f.write('\n')
    args.receipt.chmod(0o600)
    print(json.dumps({'status': receipt['status'], 'archive_sha256': receipt['archive_sha256']}))
