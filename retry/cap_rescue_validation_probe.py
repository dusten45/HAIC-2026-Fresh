"""One frozen cap40 rescue-DEV candidate, using a qualified historical baseline.

Admission and accounting only. The existing pixel actor and native executor
are unchanged; a separate saved-trace diagnosis cannot change this policy.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import signal
import time

from retry import fresh_dev_distribution as native
from retry.gentle_curve_probe import execute


def admit(plan, budget, reuse, frozen):
    assert plan['stage'] == 100 and len(plan['cases']) == 1
    assert plan['cases'][0]['coefficient'] == 7 and plan['global_cap'] == 40
    assert plan['max_actions'] == 2000 and plan['native_horizon_raw_ticks'] == 8200
    assert plan['stage_budgets'] == {plan['cases'][0]['id']: 2000}
    assert plan['candidate']['archive_sha256'] == frozen['private_artifact_hashes']['candidate40.zip']
    assert budget['B_operating_cap'] == plan['B_operating_cap'] == 650000
    assert budget['final_reserved_actions'] == plan['final_reserved_actions'] == 84000
    assert budget['actual_cumulative_wrapper_actions'] == plan['prior_cumulative']
    assert budget['research_remaining'] == plan['research_remaining_before'] >= 2000
    assert sum(budget[k] for k in ('actual_cumulative_wrapper_actions', 'research_remaining', 'final_reserved_actions')) == 650000
    assert reuse['status'] == 'PASS' and reuse['cached_baseline_reproduction_pass']
    assert reuse['baseline_lap_ms'] == plan['historical_baseline']['official_lap_ms']
    # The qualified reference has nonzero damage; this is not a zero-damage gate.
    assert reuse['baseline_damage'] == plan['historical_baseline']['damage']
    assert reuse['baseline_new_native_episodes'] == 0
    assert plan['independent_of_stage99_results'] is True
    return {'status': 'PASS', 'research_available': budget['research_remaining'],
            'reserve': 84000, 'baseline_new_native_episodes': 0,
            'damage_is_not_completion_threshold': True,
            'stage99_does_not_select_or_modify_candidate': True}


def run(path):
    path = Path(path).resolve(); plan = json.loads(path.read_text())
    assert native.sha(path) == (path.parent/'plan.sha256').read_text().split()[0]
    for group in ('source_sha256', 'reference_sha256'):
        for filename, expected in plan[group].items():
            assert native.sha(Path(filename)) == expected, filename
    ready = json.loads((path.parent/'preflight.json').read_text())
    assert ready['status'] == 'PASS' and ready['plan_sha256'] == native.sha(path)
    assert ready['historical_baseline_comparable'] and ready['cached_baseline_reproduction_pass']
    admission = admit(plan, json.loads(Path(plan['effective_budget_path']).read_text()),
                      json.loads((path.parent/'historical-reuse.json').read_text()),
                      json.loads(Path(plan['frozen_cap40_receipt_path']).read_text()))
    native.write(path.parent/'admission.json', admission)
    native.available(plan, path.parent)
    with (path.parent/'execution-claim.json').open('x') as claim:
        json.dump({'claimed_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                   'plan_sha256': native.sha(path)}, claim)

    def interrupted(_signal, _frame):
        raise RuntimeError('Supervisor termination requested')
    signal.signal(signal.SIGTERM, interrupted)
    start = time.perf_counter(); case = plan['cases'][0]
    result, stopped = execute(case, plan, path)
    result.update(global_cap=40, coefficient=7, policy_changed=True,
                  policy_changed_since_training=True, historical_comparison_only=True,
                  historical_full_stream_reproduction=False,
                  historical_baseline_episode_rerun=False,
                  independent_of_stage99_results=True)
    native.write(path.parent/case['id']/'result.json', result)
    native.write(path.parent/case['id']/'student-result.json', result)
    native.write(path.parent/'cohort-results.json', {
        'results': [result], 'stop_reason': result.get('error') if stopped else None,
        'execution_and_recording_wall_s': time.perf_counter()-start,
        'historical_baseline_episode_rerun': False})
    return result, stopped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    result, stopped = run(parser.parse_args().plan)
    print(json.dumps({k: result.get(k) for k in ('status', 'completed', 'official_lap_ms',
          'damage', 'unique_tiles', 'total_tiles', 'charged_wrapper_actions', 'error')}), flush=True)
    return int(stopped)


if __name__ == '__main__':
    raise SystemExit(main())
