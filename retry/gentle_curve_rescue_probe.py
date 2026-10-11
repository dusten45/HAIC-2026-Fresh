"""One-use frozen 7/14 preservation pair on an existing student rescue DEV.

Reference damage is part of reproduction, not a zero-damage success threshold.
No adaptive parameters or retries; the existing Stage91 actor is unchanged.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import signal
import time

import numpy as np

from retry import fresh_dev_distribution as native
from retry.gentle_curve_probe import execute


def reproduce(directory, case):
    result = json.loads((directory/case['id']/'result.json').read_text())
    expected = json.loads(Path(case['baseline_result_path']).read_text())
    assert result['status'] == 'COMPLETE' and result['completed']
    assert result['official_lap_ms'] == expected['official_lap_ms'] == case['expected_baseline_lap_ms']
    assert result['damage'] == expected['damage'] == case['expected_baseline_damage']
    assert result['action_sequence_sha256'] == expected['action_sequence_sha256']
    checks = {}
    for suffix, old_path, keys in [
        ('pixels-actions.npz', case['baseline_pixels_actions_path'], ['frames','actions']),
        ('student-masks.npz', case['baseline_masks_path'], ['masks']),
    ]:
        with np.load(directory/(case['id']+'-'+suffix), allow_pickle=False) as new, np.load(old_path, allow_pickle=False) as old:
            for key in keys:
                assert np.array_equal(new[key], old[key]), key
                checks[key+'_exact'] = True
    return {'status':'PASS', **checks, 'official_lap_ms':result['official_lap_ms'],
            'damage':result['damage'], 'damage_is_not_completion_threshold':True,
            'extra_policy_environment_calls':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    path = parser.parse_args().plan.resolve()
    plan = json.loads(path.read_text())
    assert native.sha(path) == (path.parent/'plan.sha256').read_text().split()[0]
    assert [c['coefficient'] for c in plan['cases']] == [7,14]
    assert len({c['condition'] for c in plan['cases']}) == 1
    assert plan['max_actions'] == 4000 and all(v == 2000 for v in plan['stage_budgets'].values())
    for group in ['source_sha256','reference_sha256']:
        for name, expected in plan[group].items():
            assert native.sha(Path(name)) == expected, name
    ready = json.loads((path.parent/'preflight.json').read_text())
    assert ready['status'] == 'PASS' and ready['plan_sha256'] == native.sha(path)
    native.available(plan, path.parent)
    with (path.parent/'execution-claim.json').open('x') as claim:
        json.dump({'claimed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                   'plan_sha256':native.sha(path)}, claim)
    def interrupted(_signum, _frame):
        raise RuntimeError('Supervisor termination requested')
    signal.signal(signal.SIGTERM, interrupted)
    start = time.perf_counter()
    results, stop_reason, qualification = [], None, None
    for case in plan['cases']:
        if stop_reason:
            result = {'id':case['id'],'condition':case['condition'],'coefficient':case['coefficient'],
                      'status':'UNEXECUTED','episode_count':0,'charged_wrapper_actions':0,'reason':stop_reason}
            (path.parent/case['id']).mkdir(mode=0o700)
        else:
            result, technical = execute(case, plan, path)
            result['condition'] = case['condition']
            if technical or result['status'] not in ('COMPLETE','DNF','RESOURCE_CENSORED'):
                stop_reason = 'technical_or_shared_contract_error: '+str(result.get('error'))
            if case['coefficient'] == 7:
                try:
                    qualification = reproduce(path.parent, case)
                except Exception as error:
                    qualification = {'status':'FAIL','error':repr(error),'native_outcome_retained':result['status']}
                    if stop_reason is None:
                        stop_reason = 'baseline_reproduction_failed'
                native.write(path.parent/'baseline-reproduction.json', qualification)
        native.write(path.parent/case['id']/'result.json', result)
        native.write(path.parent/case['id']/'student-result.json', result)
        results.append(result)
        native.write(path.parent/'cohort-results.json', {'results':results,'stop_reason':stop_reason,
                     'baseline_qualification':qualification,'execution_and_recording_wall_s':time.perf_counter()-start})
        print(json.dumps({k:result.get(k) for k in ['coefficient','status','official_lap_ms','damage',
                         'unique_tiles','total_tiles','charged_wrapper_actions','reason','error']}), flush=True)
    return int(stop_reason is not None)


if __name__ == '__main__':
    raise SystemExit(main())
