"""Compare one frozen candidate against cached DEV endpoints, without rerunning baselines.

The private plan supplies up to three fixed cases, arms={'A': candidate}, and
cached_baselines={case_id: {result_path, result_sha256}}. Baseline archive and
configuration hashes identify the reused policy. Only the explicit run entry
point creates workers or environments; preparing this module executes nothing.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
import time

from retry.champion_dev_survey import diagnostic_episode
from retry.completion_first_aggregate import summarize
from retry.frozen_paired_evaluation import (
    native_window, performance_verdict, sha, verify_files, write,
)


def _baseline_records(plan):
    records, initial_pairs = [], {}
    expected = [case['id'] for case in plan['cases']]
    assert set(plan['cached_baselines']) == set(expected)
    for case in plan['cases']:
        reference = plan['cached_baselines'][case['id']]
        assert sha(reference['result_path']) == reference['result_sha256']
        record = json.loads(Path(reference['result_path']).read_text())
        assert record['case'] == case['id'] and 'error' not in record
        assert record['archive_sha256'] == plan['baseline_archive_sha256']
        assert record['configuration_sha256'] == plan['baseline_configuration_sha256']
        # The shared summary validates normal endpoints without treating censor
        # or missing records as driving failures.
        assert summarize([{'case': case['id'], 'baseline': record,
                           'candidate': record}], [case['id']])['cohort_complete']
        initial = record['initial']
        assert initial['road_geometry_sha256'] == case['road_geometry_sha256']
        assert initial['physical_obstacles_sha256'] == case['expected_physical_obstacles_sha256']
        assert all(isinstance(initial[key], str) and len(initial[key]) == 64
                   for key in ('state_sha256', 'observation_sha256'))
        records.append(record)
        initial_pairs[case['id']] = dict(initial)
    return records, initial_pairs


def _capacity(plan, directory, pending):
    native_window(plan)
    assert shutil.disk_usage(directory).free >= plan['minimum_free_disk_bytes']
    remaining = (dt.datetime.fromisoformat(plan['simulation_deadline_utc'])
                 - dt.datetime.now(dt.timezone.utc)).total_seconds()
    assert plan['conservative_episode_wall_s'] > 0
    assert remaining >= pending * plan['conservative_episode_wall_s']


def run(plan_path):
    plan_path = Path(plan_path).resolve()
    directory = plan_path.parent
    plan = json.loads(plan_path.read_text())
    plan_hash = sha(plan_path)
    assert plan_hash == plan_path.with_suffix('.sha256').read_text().split()[0]
    assert plan['experiment_kind'] == 'cached_dev_comparison' and plan['split_kind'] == 'DEV'
    assert plan['no_promotion'] is True and plan['policy_frozen'] is True
    assert plan['automatic_next_candidate'] is False
    cases = plan['cases']
    assert 1 <= len(cases) <= 3 and len({case['id'] for case in cases}) == len(cases)
    assert list(plan['arms']) == ['A'] and plan['arms']['A']['type'] == 'champion'
    assert all(case['arm_order'] == ['A'] for case in cases)
    assert plan['max_steps'] == 2000
    assert plan['max_actions'] == len(cases) * 2000 <= 6000
    roles = [case['id'] + '__A' for case in cases]
    assert plan['stage_budgets'] == {role: 2000 for role in roles}
    assert plan.get('ledger_relative_path', 'budget.json') == 'budget.json'
    assert (dt.datetime.fromisoformat(plan['simulation_deadline_utc'])
            <= dt.datetime.fromisoformat(plan['deadline_utc'])
            <= dt.datetime.fromisoformat(plan['authorization_end_utc']))
    assert plan['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    verify_files(plan['source_sha256'])
    verify_files(plan.get('runtime_sha256', {}))
    config = plan['arms']['A']
    assert sha(config['archive_path']) == config['archive_sha256']
    assert sha(config['worker_path']) == config['worker_sha256']
    assert sha(plan['allocation_path']) == plan['allocation_sha256']
    allocation = json.loads(Path(plan['allocation_path']).read_text())
    assert allocation['B_operating_cap'] == plan['B_operating_cap']
    assert allocation['research_remaining'] >= plan['max_actions']
    assert allocation['final_reserved_actions'] == 84000 and allocation['final_reserve_used'] == 0
    baselines, initial_pairs = _baseline_records(plan)
    _capacity(plan, directory, len(cases))
    assert not (directory / 'budget.json').exists()
    # Exclusive files prevent a repeated invocation. No new qualification or
    # readiness process is introduced; the plan binds the reused evidence.
    write(directory / 'execution-claim.json', {'plan_sha256': plan_hash,
          'started_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
          'one_use': True, 'automatic_retry': False}, exclusive=True)
    write(directory / 'budget.json', {'started_epoch': time.time(),
          'actions': 0, 'stages': {}}, exclusive=True)
    start, cpu_start = time.perf_counter(), time.process_time()
    candidates, launched, failure = [], [], None
    try:
        for case in cases:
            _capacity(plan, directory, len(cases) - len(launched))
            launched.append(case['id'] + '__A')
            try:
                result = diagnostic_episode(plan_path, plan, case, initial_pairs)
            except Exception:
                # Recording can fail after the episode has returned its native
                # endpoint. Retain its costs but keep the comparison incomplete.
                saved = directory / 'runs' / launched[-1] / 'result.json'
                if saved.exists():
                    candidates.append(json.loads(saved.read_text()))
                raise
            candidates.append(result)
            assert 'error' not in result, result.get('error')
            assert result['reaping']['process_reaped'] and result['reaping']['actor_pids_absent']
            write(directory / 'progress.json', {'finished': len(candidates),
                  'native_actions': sum(row['charged_wrapper_actions'] for row in candidates)})
            # A normal DNF or declared cap censor never skips a registered case.
    except Exception as error:
        failure = type(error).__name__ + ': ' + str(error)
    ledger = json.loads((directory / 'budget.json').read_text())
    assert 0 <= ledger['actions'] <= plan['max_actions']
    assert set(ledger['stages']) <= set(roles)
    assert all(0 <= count <= 2000 for count in ledger['stages'].values())
    assert sum(ledger['stages'].values()) == ledger['actions']
    returned = sum(row['charged_wrapper_actions'] for row in candidates)
    if returned != ledger['actions']:
        failure = failure or 'Ledger includes actions without a returned episode record'
    try:
        assert sha(plan_path) == plan_hash
        verify_files(plan['source_sha256'])
        verify_files(plan.get('runtime_sha256', {}))
        assert sha(plan['allocation_path']) == plan['allocation_sha256']
        _baseline_records(plan)
    except Exception as error:
        failure = failure or 'Preservation: ' + type(error).__name__ + ': ' + str(error)
    by_case = {row['case']: row for row in candidates}
    pairs = [{'case': case['id'], 'baseline': baseline,
              'candidate': by_case.get(case['id'])}
             for case, baseline in zip(cases, baselines)]
    summary = summarize(pairs, [case['id'] for case in cases])
    verdict = performance_verdict(summary)
    if failure is not None:
        verdict = 'KEEP_CHAMPION_INCONCLUSIVE_COHORT'
    report = {
        'status': 'PASS' if failure is None and summary['cohort_complete'] else 'INCOMPLETE',
        'failure': failure, 'plan_sha256': plan_hash,
        'baselines': baselines, 'candidates': candidates, 'summary': summary,
        'descriptive_performance_verdict': verdict, 'no_promotion': True,
        'baseline_native_runs': 0, 'candidate_native_runs': len(launched),
        'unexecuted_roles': [role for role in roles if role not in launched],
        'reset_initial_identity_matches': len(candidates) == len(cases) and all(
            row.get('initial') == initial_pairs[row['case']] for row in candidates),
        'cost': {'native_wrapper_actions': ledger['actions'],
                 'returned_episode_record_actions': returned,
                 'raw_step_ticks': sum(row['raw_step_ticks'] for row in candidates),
                 'raw_reset_ticks': sum(row['raw_reset_ticks'] for row in candidates),
                 'wall_including_records_s': time.perf_counter() - start,
                 'evaluator_CPU_including_records_s': time.process_time() - cpu_start,
                 'actor_CPU_s': sum(row['actor_cumulative_CPU_s'] for row in candidates)},
        'calls': {'native_actor_reset': sum(row['actor_reset_calls'] for row in candidates),
                  'native_actor_act': sum(row['actor_act_calls'] for row in candidates),
                  'new_offline_policy_calls': 0, 'new_baseline_native_calls': 0,
                  'extra_native_calls': 0, 'automatic_retries': 0},
        'automatic_next_candidate': False,
        'comparison_scope': 'Cached normal DEV endpoints; exact observed reset hashes, not hidden full-state equivalence. Damage is exposure-dependent diagnostic only.',
    }
    write(directory / 'report.json', report, exclusive=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    result = run(parser.parse_args().plan)
    print(json.dumps({'status': result['status'], 'native_actions': result['cost']['native_wrapper_actions']}))
    raise SystemExit(0 if result['failure'] is None else 1)
