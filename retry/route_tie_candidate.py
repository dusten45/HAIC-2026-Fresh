"""Build one score-bounded continuity candidate from the frozen near8 champion."""
import ast
import hashlib
from pathlib import Path
import zipfile

BASE_SHA256 = 'b004fd5409914be5c2685569567f6b1d4d141bf67b3c311a8ee3b778bca9195e'
CHANGED = {'retry/connected_agent.py', 'retry/schedule_agent.py',
           'retry/temporal_agent.py'}
HELPER = 'retry/route_tie_continuity.py'


def replace_once(source, old, new):
    assert source.count(old) == 1, old
    return source.replace(old, new)


def build(source, destination):
    source, destination = Path(source), Path(destination)
    digest = lambda data: hashlib.sha256(data).hexdigest()
    assert digest(source.read_bytes()) == BASE_SHA256
    with zipfile.ZipFile(source) as archive:
        before = {n: archive.read(n) for n in archive.namelist()}
        after = dict(before)
        temporal = before['retry/temporal_agent.py'].decode()
        temporal = replace_once(temporal, '        predicted = []\n',
            '        self.route_motion_transform = transform\n'
            '        self.route_motion_fallback_displacement = None\n'
            '        predicted = []\n')
        temporal = replace_once(temporal,
            '                y -= decode_feedback_speed(image, speed) * 0.08\n',
            '                displacement = decode_feedback_speed(image, speed) * 0.08\n'
            '                self.route_motion_fallback_displacement = displacement\n'
            '                y -= displacement\n')
        router = before['retry/connected_agent.py'].decode()
        router += '\nfrom retry.route_tie_continuity import choose_tied_route\n'
        router = replace_once(router, '    _, x, row = min(crossings)\n',
            '    focus_y, x, row = min(crossings)\n')
        router = replace_once(router, '    return candidates\n\n\ndef choose_route',
            '    for candidate in candidates:\n'
            '        candidate["continuity_obstacle_xy"] = (x, focus_y)\n'
            '    return candidates\n\n\ndef choose_route')
        router = replace_once(router,
            'def choose_route(candidates, speed, previous_steer, connection_weight=1.0):',
            'def choose_route(candidates, speed, previous_steer, connection_weight=1.0, previous_path=()):')
        router = replace_once(router, '    selected = min(scores)[1]\n',
            '    selected, tie = choose_tied_route(candidates, scores, previous_path)\n')
        router = replace_once(router, '        "candidate_scores": details}',
            '        "candidate_scores": details, "tie_continuity": tie}')
        router = replace_once(router,
            'def connected_route(image, obstacles_override=None, speed=0.0, previous_steer=0.0):',
            'def connected_route(image, obstacles_override=None, speed=0.0, previous_steer=0.0, previous_path=()):')
        router = replace_once(router,
            '    path, LAST_CONNECTION_EVALUATION = choose_route(candidates, speed, previous_steer)',
            '    path, LAST_CONNECTION_EVALUATION = choose_route(candidates, speed, previous_steer, previous_path=previous_path)')
        schedule = before['retry/schedule_agent.py'].decode()
        schedule = replace_once(schedule, 'from retry.connected_agent import connected_route\n',
            'from retry.connected_agent import connected_route\n'
            'from retry.route_tie_continuity import transport_path\n')
        schedule = replace_once(schedule, '    def act(self, observation):\n',
            '    def reset(self, observation):\n'
            '        super().reset(observation)\n'
            '        self.previous_selected_path = []\n\n'
            '    def act(self, observation):\n')
        schedule = replace_once(schedule,
            '        target = route_target(connected_route(image, obstacles, speed=speed, previous_steer=self.controller.previous_steer), speed)\n',
            '        previous_path = transport_path(self.previous_selected_path,\n'
            '            self.route_motion_transform, self.route_motion_fallback_displacement)\n'
            '        path = connected_route(image, obstacles, speed=speed,\n'
            '            previous_steer=self.controller.previous_steer, previous_path=previous_path)\n'
            '        self.previous_selected_path = path\n'
            '        target = route_target(path, speed)\n')
        after.update({'retry/temporal_agent.py': temporal.encode(),
                      'retry/connected_agent.py': router.encode(),
                      'retry/schedule_agent.py': schedule.encode(),
                      HELPER: Path(__file__).with_name('route_tie_continuity.py').read_bytes()})
        assert {n for n in before if before[n] != after[n]} == CHANGED
        for name in CHANGED | {HELPER}:
            ast.parse(after[name], filename=name)
        with zipfile.ZipFile(destination, 'x') as output:
            for info in archive.infolist():
                output.writestr(info, after[info.filename])
            output.writestr(HELPER, after[HELPER])
    destination.chmod(0o600)
    return dict(source_archive_sha256=BASE_SHA256,
                archive_sha256=digest(destination.read_bytes()),
                members_sha256={n: digest(b) for n, b in after.items()},
                changed_members=sorted(CHANGED), added_member=HELPER,
                unchanged_members=sorted(set(before) - CHANGED),
                tracker_motion_reused_without_new_calls=True,
                current_candidates_and_costs_unchanged=True,
                GT_or_action_correction=False)
