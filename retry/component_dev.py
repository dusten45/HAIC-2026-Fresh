"""Run one frozen standalone component candidate on two existing DEV roads.

Only candidate B runs. The recorder checks each reset against its frozen prior
baseline and saves private DEV records. Normal DNF or action-cap censoring does
not suppress the second road; technical failures stop without an automatic retry.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
import time

from retry.frozen_paired_evaluation import native_window, sha, verify_files, write
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
    assert plan['experiment_kind'] == 'one_component_dev'
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
    for case in plan['cases']:
        # The reused recorder checks these prior initial state fields and the
        # complete observation hash before any candidate driving action.
        path = str(Path(case['reference_started_path']).resolve())
        assert plan['source_sha256'][path] == sha(path)
    assert sha(plan['project_budget_path']) == plan['project_budget_sha256']
    budget = json.loads(Path(plan['project_budget_path']).read_text())
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
    results, launched, initial_pairs = [], [], {}
    termination = None
    try:
        for index, case in enumerate(plan['cases']):
            _capacity(plan, directory, 2 - index)
            launched.append(roles[index])
            result = recorded_episode(plan_path, plan, case, 'B', initial_pairs)
            results.append(result)
            assert result['arm'] == 'B'
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
    complete = len(results) == 2 and termination is None
    report = {
        'status': 'PASS' if complete else 'INCOMPLETE',
        'experiment_kind': 'one_component_dev', 'episodes': results,
        'actions': ledger['actions'], 'returned_episode_record_actions': recorded_actions,
        'launched_roles': launched,
        'unexecuted_roles': [role for role in roles if role not in launched],
        'termination': termination, 'no_promotion': True,
        'performance_promotion': False, 'baseline_native_runs': 0,
        'automatic_retry': False,
    }
    write(directory / 'paired-dev-result.json', report, exclusive=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    result = run(parser.parse_args().plan)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
