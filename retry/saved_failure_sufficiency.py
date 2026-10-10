"""Audit saved route telemetry before any failure timeline or alignment.

Counts and a single controller target do not identify a selected route.
This module reads records only: no pixels, policy calls, geometry generation,
simulator imports, alignment, causal ordering or controller changes.
"""
import argparse
from collections import Counter
import datetime
import hashlib
import json
import math
from pathlib import Path


def coordinate_sequence(value):
    if not isinstance(value, list) or len(value) < 2:
        return False
    return all(isinstance(point, (list, tuple)) and len(point) == 2
               and all(isinstance(v, (int, float)) and math.isfinite(v) for v in point)
               for point in value)


def coverage(rows):
    path_types = Counter(type(row.get('policy', {}).get('path_points')).__name__ for row in rows)
    route_rows = sum(coordinate_sequence(row.get('policy', {}).get('path_points')) for row in rows)
    pose_rows = sum(all(key in row.get('truth_before', {}) for key in ('position', 'angle', 'time'))
                    and coordinate_sequence([row['truth_before']['position']]*2) for row in rows)
    return {'rows':len(rows), 'path_points_value_types':dict(path_types),
            'selected_route_coordinate_rows':route_rows, 'vehicle_pose_rows':pose_rows,
            'single_controller_target_rows':sum(all(k in row.get('policy', {})
                                                     for k in ('target_x','target_forward')) for row in rows),
            'tracked_hazard_array_rows':sum(isinstance(row.get('tracked_obstacles'),list) for row in rows),
            'hazard_digest_rows':sum('hazards_sha256' in row.get('memory', {}) for row in rows),
            'coordinate_frame_and_route_input_review_required_even_if_coordinates_exist':True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan',required=True,type=Path)
    args = parser.parse_args()
    directory = args.plan.resolve().parent
    plan = json.loads(args.plan.read_text())
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    assert sha(args.plan) == (directory/'plan.sha256').read_text().split()[0]
    now = datetime.datetime.now(datetime.timezone.utc)
    assert datetime.datetime.fromisoformat(plan['start_utc']) <= now < datetime.datetime.fromisoformat(plan['deadline_utc'])
    for path,wanted in plan['input_source_sha256'].items():
        assert sha(Path(path)) == wanted,path
    summaries = []
    starts = []
    for source in plan['sources']:
        root = Path(source['directory'])
        rows = [json.loads(line) for line in (root/'trace.jsonl').read_text().splitlines()]
        assert len(rows) == json.loads((root/'result.json').read_text())['steps']
        started = json.loads((root/'started.json').read_text())
        starts.append(started)
        summaries.append({'label':source['label'],**coverage(rows)})
    same_geometry = len({item['geometry_sha256'] for item in starts}) == 1
    same_obstacles = len({item['obstacles_sha256'] for item in starts}) == 1
    same_initial_obs = len({item['initial_observation_sha256'] for item in starts}) == 1
    same_initial_pose = all(item['initial'] == starts[0]['initial'] for item in starts)
    missing = any(item['selected_route_coordinate_rows'] != item['rows'] for item in summaries)
    verdict = ('STOP_MISSING_SELECTED_PATH_GEOMETRY' if missing
               else 'REQUIRES_REFERENCE_FRAME_AND_OBSTACLE_INPUT_REVIEW')
    report = {'verdict':verdict,'coverage':summaries,
              'same_registered_road_geometry':same_geometry,'same_physical_obstacle_digest':same_obstacles,
              'same_initial_observation_digest':same_initial_obs,'same_initial_pose':same_initial_pose,
              'selected_path_vs_tracking_failure_identifiable':False,
              'critical_missing':['Actual selected route polyline with coordinate reference and decision-time binding',
                                  'Original record obstacle coordinates actually available to the route decision; a digest/count is insufficient'],
              'single_target_or_path_length_is_not_a_polyline':True,
              'geometry_clearance_and_dynamic_tracking_are_separate_questions':True,
              'timeline_alignment_and_event_order_performed':False,'stationary_vs_repeated_motion_inferred':False,
              'policy_replay_or_geometry_reconstruction_performed':False,'causal_hypothesis_asserted':False,
              'new_environment_actions':0,'policy_calls':0,'learning':0,'policy_changes':0,
              'HOLDOUT_or_SEALED_opened':False,'plan_sha256':sha(args.plan)}
    target = directory/'sufficiency-report.json'
    assert not target.exists()
    target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'verdict':verdict,'sources':len(summaries),'rows':sum(x['rows'] for x in summaries),
                      'selected_route_coordinate_rows':sum(x['selected_route_coordinate_rows'] for x in summaries),
                      'timeline_or_policy_calls':0,'new_environment_actions':0}))


if __name__ == '__main__':
    main()
