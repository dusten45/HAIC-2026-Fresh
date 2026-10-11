"""Build and evaluate one near-gated HUD pedal change on existing DEV.

Reuse frozen baseline/candidate endpoints and the existing native runner.
Private plans retain seed and record identity; no protected split is opened.
"""
import argparse
import ast
import datetime as dt
import hashlib
import json
from pathlib import Path
import time
import zipfile

from retry.frozen_paired_evaluation import episode, native_window, sha, verify_files, write


def build(source, destination):
    """Change only pedal_speed when the existing `near` predicate is true."""
    old = 'pedal_speed=decode_feedback_speed(image, speed)'
    new = 'pedal_speed=(speed if near else decode_feedback_speed(image, speed))'
    with zipfile.ZipFile(source) as archive:
        names = archive.namelist()
        assert len(names) == len(set(names))
        members = {name: archive.read(name) for name in names}
        text = members['retry/schedule_agent.py'].decode()
        assert text.count(old) == 1
        changed = text.replace(old, new)
        ast.parse(changed)
        with Path(destination).open('xb') as stream:
            with zipfile.ZipFile(stream, 'w') as output:
                for name in names:
                    data = changed.encode() if name == 'retry/schedule_agent.py' else members[name]
                    output.writestr(archive.getinfo(name), data)
    with zipfile.ZipFile(destination) as output:
        assert output.namelist() == names
        assert [name for name in names if output.read(name) != members[name]] == ['retry/schedule_agent.py']
        return {name: hashlib.sha256(output.read(name)).hexdigest() for name in names}


def run(plan_path):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == plan_path.with_suffix('.sha256').read_text().strip()
    assert plan['experiment_kind'] == 'near_gated_hud_existing_dev'
    assert plan['max_actions'] == 4000 and plan['max_steps'] == 2000
    assert len(plan['cases']) == 2 and list(plan['arms']) == ['C']
    assert plan['no_promotion'] and plan['protected_HOLDOUT_details_or_SEALED'] is False
    assert plan['research_balance_before'] >= 4000 and plan['reserved_actions'] == 84000
    verify_files(plan['source_sha256'])
    cached, initial_pairs = {}, {}
    for case in plan['cases']:
        cached[case['id']] = {}
        for arm, reference in plan['cached_results'][case['id']].items():
            assert sha(reference['path']) == reference['sha256']
            row = json.loads(Path(reference['path']).read_text())
            assert row['case'] == case['id'] and row['arm'] == arm and 'error' not in row
            assert row['archive_sha256'] == plan['cached_archive_sha256'][arm]
            assert row['terminal_observed'] and row['completed']
            cached[case['id']][arm] = row
        assert cached[case['id']]['A']['initial'] == cached[case['id']]['B']['initial']
        initial_pairs[case['id']] = cached[case['id']]['A']['initial']
    native_window(plan)
    directory = plan_path.parent
    write(directory / 'execution-claim.json', {'plan_sha256': sha(plan_path),
          'started_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
          'one_use': True, 'automatic_retry': False}, exclusive=True)
    write(directory / 'budget.json', {'started_epoch': time.time(), 'actions': 0, 'stages': {}}, exclusive=True)
    start, cpu = time.perf_counter(), time.process_time()
    results, comparisons, failure = [], [], None
    for case in plan['cases']:
        result = episode(plan_path, plan, case, 'C', initial_pairs)
        results.append(result)
        print(json.dumps({'episodes_finished': len(results),
                          'native_actions': result['charged_wrapper_actions'],
                          'technical_error': 'error' in result}), flush=True)
        if 'error' in result:
            failure = result['error']
            break
        a, b = cached[case['id']]['A'], cached[case['id']]['B']
        comparisons.append({'case': case['id'], 'A': a, 'B': b, 'C': result,
            'C_minus_A_lap_ms': result['lap_ms'] - a['lap_ms'] if result['completed'] else None,
            'C_minus_B_lap_ms': result['lap_ms'] - b['lap_ms'] if result['completed'] else None})
    ledger = json.loads((directory / 'budget.json').read_text())
    report = {'status': 'PASS' if failure is None and len(results) == 2 else 'FAIL',
              'failure': failure, 'plan_sha256': sha(plan_path), 'pairs': comparisons,
              'native_actions': ledger['actions'],
              'raw_step_ticks': sum(r['raw_step_ticks'] for r in results),
              'raw_reset_ticks': sum(r['raw_reset_ticks'] for r in results),
              'wall_s': time.perf_counter() - start, 'evaluator_CPU_s': time.process_time() - cpu,
              'actor_CPU_s': sum(r['actor_cumulative_CPU_s'] for r in results),
              'all_actors_reaped': all(r.get('reaping', {}).get('actor_pids_absent') for r in results),
              'new_offline_replay_calls': 0, 'new_seeds': 0,
              'automatic_retry': False, 'no_promotion': True}
    write(directory / 'comparison-result.json', report, exclusive=True)
    print(json.dumps({k: v for k, v in report.items() if k != 'pairs'}), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.plan)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
