"""Run frozen endpoint-only pairs serially and stop on completion loss.

The private plan supplies cases and frozen packages. No trajectories are opened,
no cases are replaced, and missing or censored endpoints never become DNF.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def completion_loss(baseline, candidate):
    def valid(record):
        return (record.get('terminal_observed') is True
                and record.get('censored') is False and 'error' not in record)
    return (valid(baseline) and valid(candidate)
            and baseline.get('completed') is True
            and candidate.get('completed') is False)


def promotion_review_verdict(summary):
    counts = summary['counts']
    if counts['lost_completion']:
        return 'RETIRE_COMPLETION_LOSS_STOP'
    if not summary['cohort_complete']:
        return 'INCONCLUSIVE_INCOMPLETE_OR_INVALID_COHORT'
    if counts['new_completion']:
        return 'KEEP_FOR_PROMOTION_REVIEW_COMPLETION_GAIN'
    if counts['common_completed'] < 2:
        return 'INSUFFICIENT_COMMON_COMPLETIONS'
    if (summary['common_completion_median_lap_delta_ms'] < 0
            and summary['common_completion_mean_lap_ratio'] < 1):
        return 'KEEP_FOR_PROMOTION_REVIEW'
    return 'MIXED_OR_NO_LAP_GAIN'


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def run(plan_path):
    directory = plan_path.parent
    plan = json.loads(plan_path.read_text())
    assert hashlib.sha256(plan_path.read_bytes()).hexdigest() == (directory/'plan.sha256').read_text().split()[0]
    assert list(plan['arms']) == ['baseline', 'candidate']
    start = time.perf_counter()
    launched, batches = [], []
    termination = None
    for case in plan['cases']:
        if (directory/'stop.json').exists():
            termination = 'SHARED_STOP'
            break
        ledger = json.loads((directory/'budget.json').read_text())
        remaining_bound = min((2*len(plan['cases'])-len(launched))*plan['max_steps'],
                              plan['max_actions']-ledger['actions'])
        rates = [plan['prior_serial_actions_per_s']] + [item['actions_per_s'] for item in batches]
        conservative_rate = min(rates)*plan['cost_rate_safety_fraction']
        seconds_left = datetime.datetime.fromisoformat(plan['deadline_utc']).timestamp()-time.time()
        if remaining_bound <= 0 or remaining_bound/conservative_rate+plan['closure_reserve_s'] >= seconds_left:
            termination = 'COST_GATE_CENSORED_UNLAUNCHED'
            write(directory/'stop.json', {'kind': termination, 'remaining_bound': remaining_bound,
                                         'conservative_actions_per_s': conservative_rate,
                                         'seconds_left': seconds_left})
            break
        before = time.perf_counter()
        endpoints = {}
        for arm in ('baseline', 'candidate'):
            role = case['id']+'__'+arm
            launched.append(role)
            queries = json.loads((directory/'query-ledger.json').read_text())
            queries.update(state='EVALUATION_IN_PROGRESS_AGGREGATE_UNOPENED',
                           episodes_launched=len(launched), launched_roles=launched)
            write(directory/'query-ledger.json', queries)
            with (directory/(role+'.stdout')).open('w') as log:
                process = subprocess.Popen([
                    sys.executable, '-m', 'retry.aggregate_only_episode',
                    '--plan', str(plan_path), '--case', case['id'], '--arm', arm],
                    stdout=log, stderr=subprocess.STDOUT,
                    env={**os.environ, 'OMP_NUM_THREADS':'1', 'OPENBLAS_NUM_THREADS':'1',
                         'SDL_VIDEODRIVER':'dummy', 'SDL_AUDIODRIVER':'dummy'})
                exit_code = process.wait()
            result_path = directory/'runs'/role/'result.json'
            if not result_path.exists():
                termination = 'INCONCLUSIVE_MISSING_ENDPOINT'
                break
            result = json.loads(result_path.read_text())
            # Only these gate fields are exposed before the single final look.
            endpoints[arm] = {key: result.get(key) for key in (
                'terminal_observed', 'censored', 'completed', 'charged_wrapper_actions')}
            if exit_code or not endpoints[arm]['terminal_observed'] or endpoints[arm]['censored']:
                termination = 'INCONCLUSIVE_TECHNICAL_OR_RESOURCE'
                break
        elapsed = time.perf_counter()-before
        actions = sum(item['charged_wrapper_actions'] or 0 for item in endpoints.values())
        batch = {'case':case['id'], 'episodes':len(endpoints), 'wall_s':elapsed,
                 'charged_actions':actions, 'actions_per_s':actions/elapsed,
                 'official_endpoints':all(item['terminal_observed'] and not item['censored']
                                          for item in endpoints.values())}
        batches.append(batch)
        if not termination and completion_loss(endpoints['baseline'], endpoints['candidate']):
            termination = 'RETIRE_COMPLETION_LOSS_STOP'
        write(directory/'coordinate-progress.json', {'batches':batches, 'episodes_launched':len(launched),
                                                    'wall_s':time.perf_counter()-start, 'termination':termination})
        print(json.dumps(batch), flush=True)
        if termination:
            if not (directory/'stop.json').exists():
                write(directory/'stop.json', {'kind':termination, 'case':case['id'],
                                             'no_further_launches':True})
            break
    unexecuted = [case['id']+'__'+arm for case in plan['cases'] for arm in ('baseline','candidate')
                  if case['id']+'__'+arm not in launched]
    result = {'batches':batches, 'wall_s':time.perf_counter()-start, 'episodes_launched':len(launched),
              'launched_roles':launched, 'unexecuted':unexecuted, 'termination':termination,
              'simulators_max':1, 'case_order_predeclared':True, 'replacement_or_retry':0,
              'lap_damage_or_trajectory_inspections_before_final_look':0}
    write(directory/'coordinate-result.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True, type=Path)
    run(parser.parse_args().plan.resolve())
