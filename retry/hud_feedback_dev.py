"""Run a frozen HUD pedal-feedback candidate against two saved DEV baselines.

Only candidate B runs. The recorder checks each reset against its frozen prior
baseline and saves private DEV records. Normal DNF or action-cap censoring does
not suppress the second road; technical failures stop without an automatic retry.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import time

from retry.completion_first_aggregate import summarize
from retry.frozen_paired_evaluation import native_window, performance_verdict, sha, verify_files, write
from retry.mask_only_dev import recorded_episode
from retry.paired_audit_gate import claim_once, verify_readiness


def _capacity(plan, directory, remaining_episodes):
    native_window(plan)
    remaining = (dt.datetime.fromisoformat(plan['simulation_deadline_utc'])
                 - dt.datetime.now(dt.timezone.utc)).total_seconds()
    assert plan['conservative_episode_wall_s'] > 0
    assert remaining >= remaining_episodes * plan['conservative_episode_wall_s']
    assert shutil.disk_usage(directory).free >= plan['minimum_free_disk_bytes']


def run(plan_path):
    plan_path = Path(plan_path).resolve()
    directory = plan_path.parent
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == plan_path.with_suffix('.sha256').read_text().split()[0]
    assert plan['experiment_kind'] == 'hud_feedback_dev'
    assert plan['no_promotion'] is True and plan['split_kind'] == 'DEV'
    assert plan['max_actions'] == 4000 and plan['max_steps'] == 2000
    assert len(plan['cases']) == 2 and list(plan['arms']) == ['B']
    assert len({case['id'] for case in plan['cases']}) == 2
    assert all(case['arm_order'] == ['B'] for case in plan['cases'])
    config = plan['arms']['B']
    assert config['type'] == 'champion'
    assert not config.get('assets') and not config.get('constants')
    roles = [case['id'] + '__B' for case in plan['cases']]
    assert plan['stage_budgets'] == {role: 2000 for role in roles}
    assert plan['ledger_relative_path'] == 'budget.json'
    verify_files(plan['source_sha256'])
    verify_files(plan['runtime_sha256'])
    assert plan['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    champion_path = str(Path(plan['champion_manifest_path']).resolve())
    assert plan['source_sha256'][champion_path] == sha(champion_path)
    assert plan['deadline_utc'] == plan['simulation_deadline_utc'] == plan['authorization_end_utc']
    authorized_seconds = (dt.datetime.fromisoformat(plan['authorization_end_utc'])
                          - dt.datetime.now(dt.timezone.utc)).total_seconds()
    assert plan['max_experiment_wall_s'] >= authorized_seconds > 0
    prior_path = str(Path(plan['prior_plan_path']).resolve())
    assert plan['prior_plan_sha256'] == plan['source_sha256'][prior_path] == sha(prior_path)
    prior = json.loads(Path(prior_path).read_text())
    assert prior['experiment_kind'] == 'near_curvature_dev' and prior['split_kind'] == 'DEV'
    assert plan['baseline_archive_sha256'] == prior['arms']['A']['archive_sha256']
    assert plan['baseline_archive_sha256'] == '6d162d961041333eeddfbb8fc749a5cbeb3e562c96b93144c2aa2816e3b7ea22'
    assert len(prior['cases']) == 2
    baselines, initial_pairs = {}, {}
    identity_fields = ('id', 'seed', 'track_id', 'road_geometry_sha256',
                       'expected_physical_obstacles_sha256')
    for case, old_case in zip(plan['cases'], prior['cases']):
        assert all(case[key] == old_case[key] for key in identity_fields), 'Changed baseline condition/order'
        baseline_path = Path(case['baseline_result_path']).resolve()
        assert baseline_path == Path(prior_path).parent / 'runs' / (case['id'] + '__A') / 'result.json'
        assert plan['source_sha256'][str(baseline_path)] == sha(baseline_path)
        baseline = json.loads(baseline_path.read_text())
        assert baseline['arm'] == 'A' and baseline['case'] == case['id'] and 'error' not in baseline
        assert baseline['archive_sha256'] == plan['baseline_archive_sha256']
        assert baseline['configuration_sha256'] == hashlib.sha256(
            json.dumps(prior['arms']['A'], sort_keys=True).encode()).hexdigest()
        assert baseline['terminal_observed'] and not baseline['censored']
        assert baseline['initial']['road_geometry_sha256'] == case['road_geometry_sha256']
        assert baseline['initial']['physical_obstacles_sha256'] == case['expected_physical_obstacles_sha256']
        assert Path(case['reference_started_path']).resolve() == baseline_path.parent / 'dev-started.json'
        baselines[case['id']] = baseline
        initial_pairs[case['id']] = baseline['initial']
        # The reused recorder checks these prior initial state fields and the
        # complete observation hash before any candidate driving action.
        path = str(Path(case['reference_started_path']).resolve())
        assert plan['source_sha256'][path] == sha(path)
    assert sha(plan['allocation_path']) == plan['allocation_sha256']
    budget = json.loads(Path(plan['allocation_path']).read_text())
    assert budget['B_operating_cap'] == plan['B_operating_cap']
    assert budget['research_remaining'] >= 4000 and budget['final_reserve_used'] == 0
    assert budget['final_reserved_actions'] == plan['reserved_actions'] == 84000
    assert sha(plan['qualification_path']) == plan['qualification_sha256']
    assert json.loads(Path(plan['qualification_path']).read_text())['status'] == 'PASS'
    verify_readiness(plan_path)
    _capacity(plan, directory, 2)
    # Do not consume the one-use claim if an earlier ledger already exists.
    assert not (directory / 'budget.json').exists()
    claim_once(plan_path)
    write(directory / 'budget.json',
          {'started_epoch': time.time(), 'actions': 0, 'stages': {}}, exclusive=True)
    results, launched = [], []
    run_started, run_CPU_started = time.perf_counter(), time.process_time()
    termination = None
    try:
        for index, case in enumerate(plan['cases']):
            _capacity(plan, directory, 2 - index)
            launched.append(roles[index])
            result = recorded_episode(plan_path, plan, case, 'B', initial_pairs)
            results.append(result)
            assert result['arm'] == 'B'
            if 'error' not in result:
                assert result['reaping']['process_reaped'] and result['reaping']['actor_pids_absent']
            write(directory / 'progress.json', {
                'finished': len(results),
                'actions': sum(row['charged_wrapper_actions'] for row in results)})
            print(json.dumps({'finished': len(results), 'planned': 2,
                              'charged_actions': result['charged_wrapper_actions'],
                              'technical_error': 'error' in result}), flush=True)
            if 'error' in result:
                termination = 'Technical failure; remaining condition not executed'
                break
            # A normal DNF or 2000-action censor is an observation, not a stop.
    except Exception as error:
        termination = type(error).__name__ + ': ' + str(error)
    ledger = json.loads((directory / 'budget.json').read_text())
    assert 0 <= ledger['actions'] <= 4000
    assert set(ledger['stages']) <= set(roles)
    assert all(0 <= used <= 2000 for used in ledger['stages'].values())
    assert sum(ledger['stages'].values()) == ledger['actions']
    recorded_actions = sum(row['charged_wrapper_actions'] for row in results)
    if recorded_actions != ledger['actions']:
        termination = termination or 'Ledger includes actions without a returned episode record'
    try:
        verify_files(plan['source_sha256'])
        verify_files(plan['runtime_sha256'])
        assert sha(plan['allocation_path']) == plan['allocation_sha256']
    except Exception as error:
        termination = termination or 'Preservation: ' + type(error).__name__ + ': ' + str(error)
    by_case = {row['case']: row for row in results}
    pairs = [{'case': case['id'], 'baseline': baselines[case['id']],
              'candidate': by_case.get(case['id'])} for case in plan['cases']]
    summary = summarize(pairs, [case['id'] for case in plan['cases']])
    verdict = performance_verdict(summary) if termination is None else 'KEEP_CHAMPION_INCONCLUSIVE_COHORT'
    complete = len(results) == 2 and termination is None
    report = {
        'status': 'PASS' if complete else 'INCOMPLETE',
        'experiment_kind': 'hud_feedback_dev', 'episodes': results,
        'actions': ledger['actions'], 'returned_episode_record_actions': recorded_actions,
        'launched_roles': launched,
        'unexecuted_roles': [role for role in roles if role not in launched],
        'termination': termination, 'no_promotion': True,
        'performance_promotion': False, 'baseline_native_runs': 0,
        'automatic_retry': False, 'descriptive_only': True, 'summary': summary,
        'descriptive_performance_verdict': verdict,
        'wall_including_records_s': time.perf_counter() - run_started,
        'evaluator_CPU_including_records_s': time.process_time() - run_CPU_started,
        'comparison_scope': 'Two reused DEV baselines; descriptive completion, common lap and separate damage only',
    }
    write(directory / 'paired-dev-result.json', report, exclusive=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    result = run(parser.parse_args().plan)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
