"""Bounded breadth diagnostics for the unchanged normal24/near8/cap45 agent.

All privileged quantities are evaluator labels. The original pixel observer,
one-call policy execution, target/P checks and native accounting are reused.
No full frame, policy or trajectory stream is retained.
"""
from collections import deque
import math

import numpy as np

from retry.compact_dev_diagnostic import ScalarStats

CATEGORIES = ('normal_curvature24', 'near_additional8', 'global_cap45', 'missing_target')


def limit_category(row):
    if row['target_m_s'] is None:
        return 'missing_target'
    normal = min(45.0, math.sqrt(24.0 / max(abs(row['curvature']), 1e-6)))
    if row['near'] and row['target_m_s'] < normal - 1e-9:
        return 'near_additional8'
    return 'normal_curvature24' if normal < 45.0 - 1e-9 else 'global_cap45'


def path_projection(path, point):
    p = np.asarray(path, dtype=float).reshape(-1, 2)
    if len(p) < 2:
        return None
    delta = np.diff(p, axis=0)
    norm2 = (delta * delta).sum(1)
    fractions = np.clip(((np.asarray(point) - p[:-1]) * delta).sum(1) /
                        np.maximum(norm2, 1e-12), 0, 1)
    distances = np.linalg.norm(p[:-1] + fractions[:, None] * delta - point, axis=1)
    distances[norm2 < 1e-12] = np.inf
    index = int(np.argmin(distances))
    if not np.isfinite(distances[index]):
        return None
    return float(distances[index]), delta[index] / math.sqrt(norm2[index]), index


class BreadthStats(ScalarStats):
    def __init__(self, state):
        super().__init__()
        self.state = state
        fields = ('rows', 'dwell_s', 'GT_bound_or_braking_s', 'feedback_bound_or_braking_s',
                  'braking_s', 'gas_s', 'GT_below_target_minus1_s', 'target_weighted_sum',
                  'GT_speed_weighted_sum', 'abs_GT_minus_target_weighted_sum',
                  'abs_feedback_minus_GT_weighted_sum')
        self.limits = {name: dict.fromkeys(fields, 0.0) for name in CATEGORIES}
        self.quality = dict.fromkeys(('target_truncated_s', 'missing_route_s', 'offroad_s',
            'large_heading_error_s', 'large_path_error_s', 'near_path_margin_gt2_bound_s',
            'joint_residual_sum', 'joint_residual_max', 'matched_center_error_sum',
            'matched_center_error_max', 'matched_obstacles', 'distant_or_ambiguous_obstacles'), 0.0)
        self.history = deque(maxlen=50)
        self.streaks = dict(no_progress=0, heading=0, offroad=0)
        self.max_no_progress = 0
        self.earliest = None

    def add(self, row):
        row.update(self.state['extra'])
        name = limit_category(row)
        bucket, duration = self.limits[name], row['dwell_s']
        bucket['rows'] += 1
        bucket['dwell_s'] += duration
        target = row['target_m_s']
        bound = False
        if target is not None:
            speed, feedback = row['speed_before_m_s'], row['feedback_m_s']
            brake = row['brake'] > 1e-6
            bound = speed >= target - 1 or brake
            for key, value in dict(GT_bound_or_braking_s=bound,
                feedback_bound_or_braking_s=feedback >= target - 1 or brake,
                braking_s=brake, gas_s=row['gas'] > 1e-6, GT_below_target_minus1_s=speed < target - 1,
                target_weighted_sum=target, GT_speed_weighted_sum=speed,
                abs_GT_minus_target_weighted_sum=abs(speed-target),
                abs_feedback_minus_GT_weighted_sum=abs(feedback-speed)).items():
                bucket[key] += duration * value
        q = self.quality
        for key, value in dict(target_truncated_s=row['target_truncated'],
            missing_route_s=not row['selected_path_body'], offroad_s=row['road_wheels_after'] < 4,
            large_heading_error_s=row['heading_error_abs_rad'] is not None and row['heading_error_abs_rad'] > .2,
            large_path_error_s=row['path_error_m'] is not None and row['path_error_m'] > .5,
            near_path_margin_gt2_bound_s=name == 'near_additional8' and bound and
                row['tracked_grid_margin_m'] is not None and row['tracked_grid_margin_m'] > 2).items():
            q[key] += duration * value
        joint = max(row['front_joint_residual_after_rad'])
        q['joint_residual_sum'] += joint
        q['joint_residual_max'] = max(q['joint_residual_max'], joint)
        q['matched_center_error_sum'] += sum(row['compatible_center_errors_m'])
        q['matched_obstacles'] += len(row['compatible_center_errors_m'])
        q['matched_center_error_max'] = max([q['matched_center_error_max'], *row['compatible_center_errors_m']])
        q['distant_or_ambiguous_obstacles'] += row['distant_or_ambiguous_obstacles']
        active = row['before_official_finish']
        checks = dict(no_progress=row['new_tiles'] == 0,
                      heading=row['heading_error_abs_rad'] is not None and row['heading_error_abs_rad'] > .2,
                      offroad=row['road_wheels_after'] < 4)
        for key, condition in checks.items():
            self.streaks[key] = self.streaks[key] + 1 if active and condition else 0
        self.max_no_progress = max(self.max_no_progress, self.streaks['no_progress'])
        events = []
        if active and (row['collision'] or row['damage_after'] > row['damage_before']):
            events.append(('contact', row['step']))
        for key, threshold in [('no_progress', 25), ('heading', 10), ('offroad', 10)]:
            if self.streaks[key] == threshold:
                events.append((key, row['step'] - threshold + 1))
        for kind, onset in events:
            if self.earliest is None or onset < self.earliest['onset_step']:
                self.earliest = dict(kind=kind, onset_step=onset, trigger_step=row['step'],
                    pre_rows=[x for x in self.history if onset-20 <= x['step'] < onset],
                    onset_row=next((x for x in self.history if x['step'] == onset), row),
                    trigger_row=row, label_not_causal_proof=True)
        self.history.append(row)
        super().add(row)

    def summary(self, completed):
        result = super().summary(completed)
        result.pop('near5_rows', None)
        assert abs(sum(b['dwell_s'] for b in self.limits.values()) - self.elapsed) < 1e-8
        result.update(limit_exposure=self.limits, route_and_tracking=self.quality,
            max_no_progress_actions=self.max_no_progress, earliest_anomaly=self.earliest,
            first_contact_step=self.first_damage['step'] if self.first_damage else None,
            exposure_is_recoverable_time=False,
            diagnostic_scope='Observed native intervals including terminal callbacks. Speed, pose, physical obstacles and road contacts are evaluator-only labels.',
            matching_scope='Current nearest physical correspondence with error<=2m and next-match distance gap>2m. Distant/ambiguous cases counted separately; not track-lineage or perception-correctness proof.',
            path_scope='Post-action hull origin against fixed pre-action path. Projection onto origin connector is labeled. Grid circle margin does not prove swept-body safety.')
        return result


def breadth_episode(plan_path, plan, case, initial_pairs):
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry.compact_dev_diagnostic import compact_episode
    from retry.full_route_reproduction import truth

    original_factory, original_prepare = diagnose.make_env, runtime.prepare
    state = {}

    def factory(*args, **kwargs):
        env = original_factory(*args, **kwargs)
        old_step = env.step

        def step(action):
            before = truth(env)
            response = state['response']
            route = response['speed_constraint_probe']
            path = route['selected_path_body']
            physical = [[*map(float, env.unwrapped.car.hull.GetLocalPoint(tuple(o.position))),
                         float(o.fixtures[0].shape.radius)] for o in env.unwrapped.obstacles]
            errors, unmatched = [], 0
            for obstacle in route['tracked_obstacles_body']:
                distances = sorted(float(np.linalg.norm(np.asarray(obstacle[:2])-o[:2])) for o in physical)
                if len(distances) >= 2 and distances[0] <= 2 and distances[1]-distances[0] > 2:
                    errors.append(distances[0])
                else:
                    unmatched += 1
            margins = []
            for x, y, radius in route['tracked_obstacles_body']:
                projection = path_projection(path[1:], [x, y])
                if projection is not None:
                    margins.append(projection[0] - 2.6 - radius)
            active = env.unwrapped.finish_time_s is None
            saved = np.asarray(action, np.float32).copy()
            assert saved.tobytes() == np.asarray(response['action'], np.float32).tobytes()
            out = old_step(action)
            assert np.array_equal(saved, action)
            after = truth(env)
            dx, dy = np.asarray(after['position']) - before['position']
            c, s = math.cos(before['angle']), math.sin(before['angle'])
            projection = path_projection(path, [c*dx+s*dy, -s*dx+c*dy])
            heading = None
            if projection is not None:
                delta = after['angle']-before['angle']
                forward = np.array([-math.sin(delta), math.cos(delta)])
                tangent = projection[1]
                heading = abs(math.atan2(tangent[0]*forward[1]-tangent[1]*forward[0], float(np.dot(tangent, forward))))
            state['extra'] = dict(new_tiles=after['unique_tiles']-before['unique_tiles'],
                before_official_finish=active, target_truncated=route['target_endpoint_truncated'],
                road_wheels_after=sum(bool(w.tiles) for w in env.unwrapped.car.wheels),
                path_error_m=projection[0] if projection else None, heading_error_abs_rad=heading,
                projection_on_origin_connector=projection[2] == 0 if projection else None,
                tracked_grid_margin_m=min(margins) if margins else None,
                compatible_center_errors_m=errors, distant_or_ambiguous_obstacles=unmatched,
                selected_path_body=path, tracked_obstacles_body=route['tracked_obstacles_body'],
                detected_obstacles_body=response['contact_probe']['detected_obstacles_xyr'],
                tracked_hazards_after=route['tracker_hazards_after'],
                physical_obstacles_body=physical, source_route_selection=response['connection_selection'])
            return out

        env.step = step
        return env

    def prepare(*args, **kwargs):
        worker = original_prepare(*args, **kwargs)
        old_call = worker.call

        def call(operation, observation):
            response, elapsed = old_call(operation, observation)
            if operation == 'act':
                state['response'] = response
            return response, elapsed

        worker.call = call
        return worker

    diagnose.make_env, runtime.prepare = factory, prepare
    try:
        return compact_episode(plan_path, plan, case, initial_pairs, [],
                               stats_factory=lambda: BreadthStats(state))
    finally:
        diagnose.make_env, runtime.prepare = original_factory, original_prepare
