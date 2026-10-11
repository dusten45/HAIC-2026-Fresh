"""Build a frozen observed-hazard bypass-side candidate without importing a policy.

Only tracker ID metadata, the connected route search, and its schedule call are
patched. Archive construction and observer projection execute no environments,
policies, models, renderers, or qualification runs.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import zipfile


BASE_ARCHIVE_SHA256 = 'b8c40bcff8ad9eea60e21755950b77235c22a0d7df89eb74f08148bbb0c9890c'
CHANGED_MEMBERS = {'retry/temporal_agent.py', 'retry/connected_agent.py', 'retry/schedule_agent.py'}


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _replace(source, old, new):
    assert source.count(old) == 1, 'Source patch must match once'
    return source.replace(old, new)


def _temporal(source):
    source = _replace(source, '        self.hazards = []\n',
                      '        self.hazards = []\n        self.hazard_ids = []\n        self.next_hazard_id = 0\n')
    source = _replace(source, '        predicted = []\n        for x, y, radius, age in self.hazards:\n',
                      '        predicted, predicted_ids = [], []\n'
                      '        for index, (x, y, radius, age) in enumerate(self.hazards):\n')
    source = _replace(source, '                predicted.append((float(x), float(y), radius, age + 1))\n',
                      '                predicted.append((float(x), float(y), radius, age + 1))\n'
                      '                predicted_ids.append(self.hazard_ids[index])\n')
    source = _replace(source,
        '            predicted = [p for p in predicted if np.hypot(p[0] - x, p[1] - y) > 2]\n',
        '''            distances = [np.hypot(p[0] - x, p[1] - y) for p in predicted]
            keep = [distance > 2 for distance in distances]
            removed = [index for index, retained in enumerate(keep) if not retained]
            if removed:
                nearest = min(removed, key=lambda index: (distances[index], index))
                hazard_id = predicted_ids[nearest]
            else:
                hazard_id = self.next_hazard_id
                self.next_hazard_id += 1
            predicted = [p for p, retained in zip(predicted, keep) if retained]
            predicted_ids = [value for value, retained in zip(predicted_ids, keep) if retained]
''')
    source = _replace(source, '            predicted.append((x, y, radius, 0))\n',
                      '            predicted.append((x, y, radius, 0))\n            predicted_ids.append(hazard_id)\n')
    return _replace(source, '        self.previous_image, self.hazards = current, predicted\n',
                    '        self.previous_image, self.hazards = current, predicted\n'
                    '        self.hazard_ids = predicted_ids\n')


ROUTE_EXTENSION = '''def _bypass_crossing(path, forward):
    for first, second in zip(path, path[1:]):
        if (first[1] - forward) * (second[1] - forward) <= 0 and first[1] != second[1]:
            fraction = (forward - first[1]) / (second[1] - first[1])
            return float(first[0] + fraction * (second[0] - first[0]))
    return None


def connected_route(image, obstacles_override=None, bypass_state=None, hazard_ids=None, near_limit=None):
    obstacles = road_and_obstacles(image)[1] if obstacles_override is None else obstacles_override
    allowed, distance, start, _, goal, _ = routing_problem(image, obstacles)
    if bypass_state is None:
        return [] if start is None or goal is None else _connected_search(allowed, distance, start, goal)
    active_id, side = bypass_state.get("id"), bypass_state.get("side")
    ids = [] if hazard_ids is None else hazard_ids
    assert hazard_ids is None or len(ids) == len(obstacles)
    probe = {"id": active_id, "side": side, "status": "UNHELD", "reason": None,
             "obstacle_xyr": None, "crossing_x": None, "fence_row": None,
             "restricted_searches": 0, "base_searches": 0}
    released = False
    if active_id is not None:
        index = next((index for index, value in enumerate(ids) if value == active_id), None)
        if index is None:
            reason = "TRACK_LOST"
        else:
            ox, oy, radius = obstacles[index]
            probe["obstacle_xyr"] = [float(ox), float(oy), float(radius)]
            if oy <= 0:
                reason = "PASSED"
            else:
                assert side in (-1, 1)
                restricted = allowed.copy()
                row = int(np.clip(round(63 - 1.701 * oy), 24, 56))
                restricted[row] &= side * ((np.arange(restricted.shape[1]) - 42) / 1.3608 - ox) > 0
                probe["fence_row"] = row
                starts = np.flatnonzero(restricted[56])
                held_path = []
                if len(starts) and goal is not None:
                    start_x = int(starts[np.argmin(abs(starts - 42))])
                    if abs(start_x - 42) <= 12:
                        probe["restricted_searches"] = 1
                        held_path = _connected_search(restricted, distance, (56, start_x), goal)
                crossing = _bypass_crossing(held_path, oy)
                probe["crossing_x"] = crossing
                if held_path and crossing is not None and side * (crossing - ox) > 0:
                    probe.update(status="HELD", reason="SIDE_CONNECTED")
                    bypass_state["probe"] = probe
                    return held_path
                reason = "DISCONNECTED"
        released = True
        bypass_state["id"], bypass_state["side"] = None, None
        probe.update(status="RELEASED", reason=reason)
    base_path = []
    if start is not None and goal is not None:
        probe["base_searches"] = 1
        base_path = _connected_search(allowed, distance, start, goal)
    if not released and active_id is None and near_limit is not None and len(ids) == len(obstacles):
        eligible = []
        for index, (ox, oy, radius) in enumerate(obstacles):
            separation = np.hypot(ox, oy)
            if oy > 0 and separation <= near_limit + 2.6 + radius:
                crossing = _bypass_crossing(base_path, oy)
                if crossing is not None:
                    eligible.append((separation, index, crossing))
        if eligible:
            _, index, crossing = min(eligible, key=lambda item: (item[0], item[1]))
            ox, oy, radius = obstacles[index]
            chosen_side = 1 if crossing > ox else -1 if crossing < ox else None
            if chosen_side is not None:
                bypass_state["id"], bypass_state["side"] = ids[index], chosen_side
                probe.update(id=ids[index], side=chosen_side, status="ACQUIRED",
                             reason="BASELINE_CROSSING", obstacle_xyr=[float(ox), float(oy), float(radius)],
                             crossing_x=crossing)
    bypass_state["probe"] = probe
    return base_path
'''


def _connected(source):
    tree = ast.parse(source)
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'connected_route')
    lines = source.splitlines(keepends=True)
    first = next(node for node in function.body if isinstance(node, ast.Assign)
                 and any(isinstance(target, ast.Tuple) and any(isinstance(name, ast.Name) and name.id == 'costs'
                         for name in target.elts) for target in node.targets))
    body = ''.join(lines[first.lineno - 1:function.end_lineno])
    helper = 'def _connected_search(allowed, distance, start, goal):\n' + body
    old = ''.join(lines[function.lineno - 1:function.end_lineno])
    modified = _replace(source, old, helper + '\n\n' + ROUTE_EXTENSION.rstrip())
    copied = next(node for node in ast.parse(modified).body
                  if isinstance(node, ast.FunctionDef) and node.name == '_connected_search')
    original_body = function.body[function.body.index(first):]
    assert ast.dump(ast.Module(body=original_body, type_ignores=[])) == ast.dump(ast.Module(body=copied.body, type_ignores=[]))
    return modified


def _schedule(source):
    source = _replace(source, '    def act(self, observation):\n',
        '    def reset(self, observation):\n        super().reset(observation)\n'
        '        self.bypass_state = {"id": None, "side": None, "probe": {}}\n\n'
        '    def act(self, observation):\n')
    return _replace(source, '        target = route_target(connected_route(image, obstacles), speed)\n',
        '        target = route_target(connected_route(image, obstacles, bypass_state=self.bypass_state,\n'
        '            hazard_ids=self.hazard_ids, near_limit=lookahead), speed)\n')


def build(source_archive, output_archive, expected_sha256=BASE_ARCHIVE_SHA256):
    source_archive, output_archive = Path(source_archive), Path(output_archive)
    source_bytes = source_archive.read_bytes()
    assert _sha(source_bytes) == expected_sha256
    patches = {'retry/temporal_agent.py': _temporal,
               'retry/connected_agent.py': _connected, 'retry/schedule_agent.py': _schedule}
    with zipfile.ZipFile(source_archive) as original:
        members = original.namelist()
        assert len(members) == len(set(members)) and CHANGED_MEMBERS <= set(members)
        before = {name: original.read(name) for name in members}
        after = dict(before)
        for name, patch in patches.items():
            after[name] = patch(before[name].decode()).encode()
            ast.parse(after[name], filename=name)
        assert {name for name in members if before[name] != after[name]} == CHANGED_MEMBERS
        with zipfile.ZipFile(output_archive, 'x') as output:
            for info in original.infolist():
                output.writestr(info, after[info.filename])
    output_archive.chmod(0o600)
    assert source_archive.read_bytes() == source_bytes
    return {'status': 'BUILT_NOT_EXECUTED', 'source_archive_sha256': expected_sha256,
            'archive_sha256': _sha(output_archive.read_bytes()),
            'members_sha256': {name: _sha(data) for name, data in after.items()},
            'changed_members': sorted(CHANGED_MEMBERS),
            'unchanged_members': sorted(set(members) - CHANGED_MEMBERS),
            'Dijkstra_body_AST_identical': True,
            'tracker_numeric_rule_unchanged_source_only_assertion': True,
            'native_policy_model_renderer_qualification_calls': 0}


def probe_worker(source_worker, destination):
    source_worker, destination = Path(source_worker), Path(destination)
    original = source_worker.read_text()
    marker = '    response.update(rss_mib='
    projection = '    response["bypass_side_probe"] = dict(getattr(agent, "bypass_state", {}).get("probe", {}))\n'
    changed = _replace(original, marker, projection + marker)
    ast.parse(changed, filename=str(destination))
    with destination.open('x') as stream:
        stream.write(changed)
    destination.chmod(0o600)
    assert source_worker.read_text() == original
    return {'source_worker_sha256': _sha(original.encode()),
            'worker_sha256': _sha(changed.encode()), 'output_projection_only': True,
            'new_policy_model_native_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--observer-source', type=Path)
    parser.add_argument('--observer-output', type=Path)
    parser.add_argument('--receipt', required=True, type=Path)
    args = parser.parse_args()
    assert (args.observer_source is None) == (args.observer_output is None)
    report = build(args.source, args.output)
    if args.observer_source is not None:
        report['observer'] = probe_worker(args.observer_source, args.observer_output)
    report['builder_sha256'] = _sha(Path(__file__).read_bytes())
    with args.receipt.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')
    args.receipt.chmod(0o600)
    print(json.dumps({'status': report['status'], 'archive_sha256': report['archive_sha256'],
                      'changed_members': report['changed_members'],
                      'native_policy_model_calls': 0}))
