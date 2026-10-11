"""One frozen global-cap candidate on two previously registered DEV roads.

Reuse the verified first-road original endpoint. On the second road run the
original and candidate once each. No result-dependent tuning or normal-DNF stop.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import shutil
import time

from retry.frozen_paired_evaluation import native_window, sha, verify_files, write
from retry.mask_only_dev import recorded_episode
from retry.paired_audit_gate import claim_once


def run(plan_path):
    plan_path = Path(plan_path).resolve()
    plan = json.loads(plan_path.read_text())
    assert sha(plan_path) == plan_path.with_suffix('.sha256').read_text().split()[0]
    assert plan['split_kind'] == 'DEV' and plan['max_actions'] == 6000 and plan['max_steps'] == 2000
    assert len(plan['cases']) == 2 and list(plan['arms']) == ['A', 'B']
    assert [c['arm_order'] for c in plan['cases']] == [['B'], ['A', 'B']]
    assert all(c['type'] == 'champion' and not c.get('assets') and not c.get('constants')
               for c in plan['arms'].values())
    roles = [c['id'] + '__' + a for c in plan['cases'] for a in c['arm_order']]
    assert plan['stage_budgets'] == {role: 2000 for role in roles}
    verify_files(plan['source_sha256'])
    verify_files(plan['runtime_sha256'])
    assert plan['source_sha256'][str(Path(__file__).resolve())] == sha(__file__)
    assert sha(plan['project_budget_path']) == plan['project_budget_sha256']
    budget = json.loads(Path(plan['project_budget_path']).read_text())
    assert budget['research_remaining'] >= plan['max_actions'] and budget['final_reserve_used'] == 0
    assert budget['final_reserved_actions'] == plan['reserved_actions']
    assert shutil.disk_usage(plan_path.parent).free >= plan['minimum_free_disk_bytes']
    claim_once(plan_path)
    write(plan_path.parent / 'budget.json', {'started_epoch': time.time(), 'actions': 0, 'stages': {}}, exclusive=True)
    results, initial_pairs = [], {}
    for case in plan['cases']:
        for arm in case['arm_order']:
            native_window(plan)
            remaining = (dt.datetime.fromisoformat(plan['simulation_deadline_utc'])
                         - dt.datetime.now(dt.timezone.utc)).total_seconds()
            assert remaining >= (len(roles) - len(results)) * plan['conservative_episode_wall_s']
            assert shutil.disk_usage(plan_path.parent).free >= plan['minimum_free_disk_bytes']
            result = recorded_episode(plan_path, plan, case, arm, initial_pairs)
            results.append(result)
            write(plan_path.parent / 'progress.json', {'finished': len(results),
                                                      'actions': sum(r['charged_wrapper_actions'] for r in results)})
            print(json.dumps({'stage': case['stage'], 'arm': arm, 'finished': len(results),
                              'charged_actions': result['charged_wrapper_actions'],
                              'technical_error': result.get('error')}), flush=True)
            if 'error' in result:
                break
        if 'error' in results[-1]:
            break
    report = {'status': 'PASS' if len(results) == 3 and not any('error' in r for r in results) else 'INCOMPLETE',
              'episodes': results, 'actions': sum(r['charged_wrapper_actions'] for r in results),
              'performance_promotion': False, 'baseline_native_runs': sum(r['arm'] == 'A' for r in results),
              'automatic_retry': False}
    write(plan_path.parent / 'paired-dev-result.json', report, exclusive=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    result = run(parser.parse_args().plan)
    raise SystemExit(0 if result['status'] == 'PASS' else 1)
