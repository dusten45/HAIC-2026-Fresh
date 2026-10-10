"""Audit a frozen connector predicate against saved policy-input paths.

This is saved-array arithmetic: no simulator, Agent, replay or candidate run.
Physical obstacle geometry is deliberately absent from the predicate inputs.
"""
import argparse
import ast
import datetime
import hashlib
import json
from pathlib import Path
import time

import numpy as np


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    plan_path = args.plan.resolve()
    folder = plan_path.parent
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == (folder / 'plan.sha256').read_text().split()[0]
    assert sha(Path(__file__)) == (folder / 'audit-code.sha256').read_text().split()[0]
    for name, expected in plan['source_sha256'].items():
        assert sha(Path(name)) == expected, name
    started_wall, started_cpu = time.perf_counter(), time.process_time()
    now = datetime.datetime.now(datetime.timezone.utc)
    assert now < datetime.datetime.fromisoformat(plan['premise_deadline_utc'])

    source = Path(plan['existing_connector_source'])
    tree = ast.parse(source.read_text(), filename=str(source))
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == plan['existing_function']]
    assert len(functions) == 1
    # Extract only the original pure predicate, without importing its policy.
    namespace = {'np': np}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(source), 'exec'), namespace)
    predicate = namespace[plan['existing_function']]
    onset = int(plan['problem_onset_action'])
    rows = [json.loads(line) for line in Path(plan['saved_trace']).read_text().splitlines()]
    rejected, audit = [], []
    for index, row in enumerate(rows, 1):
        assert row['step'] == index
        telemetry = row['route_telemetry']
        path = np.asarray(telemetry['selected_path'], dtype=float)
        hazards = telemetry['route_obstacle_inputs']
        assert path.ndim == 2 and path.shape[1] == 2 and len(path) >= 2
        assert np.isfinite(path).all() and np.array_equal(path[0], [0, 0])
        assert float(path[1] @ path[1]) > 0
        assert not telemetry['actual_fallback_called']
        accepted = bool(predicate(path[1], hazards))
        if not accepted:
            rejected.append(index)
        audit.append({'action': index, 'pre_time_s': row['before_time'],
                      'connector_endpoint': path[1].tolist(),
                      'policy_hazard_count': len(hazards), 'accepted': accepted})
    prior = [index for index in rejected if index < onset]
    if not rejected:
        verdict = 'STOP_NO_CONNECTOR_REJECTION'
    elif not prior:
        verdict = 'STOP_POST_PROBLEM_ONSET_ONLY'
    else:
        verdict = 'PRE_ONSET_PREDICATE_GATE_PASS_ACTION_GATE_STILL_REQUIRED'
    report = {'verdict': verdict, 'records': len(rows), 'problem_onset_action': onset,
              'first_rejected_action': rejected[0] if rejected else None,
              'rejected_actions': len(rejected), 'pre_onset_rejected_actions': len(prior),
              'at_onset_rejected': onset in rejected, 'candidate_creation_allowed': bool(prior),
              'actual_action_effect_test': 'NOT_REACHED' if not prior else 'REQUIRED_BEFORE_DRIVE',
              'new_environment_actions': 0, 'new_policy_act_calls': 0, 'learning': 0,
              'same_original_predicate_used': True, 'privileged_obstacles_used_as_policy_input': False,
              'predicate_source_sha256': sha(source), 'plan_sha256': sha(plan_path),
              'audit_code_sha256': sha(Path(__file__)),
              'saved_trace_sha256': sha(Path(plan['saved_trace'])),
              'wall_s': time.perf_counter() - started_wall,
              'cpu_s': time.process_time() - started_cpu,
              'premise_gate_finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
    assert datetime.datetime.now(datetime.timezone.utc) < datetime.datetime.fromisoformat(plan['premise_deadline_utc'])
    (folder / 'predicate-rows.json').write_text(json.dumps(audit, indent=2) + '\n')
    (folder / 'premise-report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
