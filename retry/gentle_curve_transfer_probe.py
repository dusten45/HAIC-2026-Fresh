"""Fixed 7/14 paired preservation checks on ordered known DEV geometries.

Native performance failure does not stop other conditions. Shared contract or
technical failure stops execution; baseline reproduction qualifies its own pair.
The unchanged Stage91 actor/patch and existing native recorder are reused.
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
    assert result['damage'] == expected['damage'] == 0
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
    return {'status':'PASS', 'condition':case['condition'], **checks,
            'official_lap_ms':result['official_lap_ms'], 'damage':result['damage'],
            'extra_policy_environment_calls':0}


def performance_failure_stops_other_conditions(result):
    """Explicitly keep native DNF and local action censorship out of global stop."""
    return result['status'] not in ('COMPLETE', 'DNF', 'RESOURCE_CENSORED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    path = parser.parse_args().plan.resolve()
    plan = json.loads(path.read_text())
    assert native.sha(path) == (path.parent/'plan.sha256').read_text().split()[0]
    assert [(c['condition'],c['coefficient']) for c in plan['cases']] == [('high',7),('high',14),('low',7),('low',14)]
    assert plan['max_actions'] == 8000 and all(v == 2000 for v in plan['stage_budgets'].values())
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
    results, stop_reason, pair_qualification = [], None, {}
    for case in plan['cases']:
        if stop_reason:
            reason = stop_reason
        elif case['coefficient'] == 14 and pair_qualification.get(case['condition'],{}).get('status') != 'PASS':
            reason = 'baseline_reproduction_failed_for_'+case['condition']
        else:
            reason = None
        if reason:
            result = {'id':case['id'],'condition':case['condition'],'coefficient':case['coefficient'],
                      'status':'UNEXECUTED','episode_count':0,'charged_wrapper_actions':0,'reason':reason}
            (path.parent/case['id']).mkdir(mode=0o700)
            native.write(path.parent/case['id']/'result.json', result)
        else:
            result, technical = execute(case, plan, path)
            result['condition'] = case['condition']
            if technical or performance_failure_stops_other_conditions(result):
                stop_reason = 'technical_or_shared_contract_error: '+str(result.get('error'))
            if case['coefficient'] == 7:
                try:
                    pair_qualification[case['condition']] = reproduce(path.parent, case)
                except Exception as error:
                    pair_qualification[case['condition']] = {'status':'FAIL','error':repr(error),
                        'native_outcome_retained':result['status'],'condition':case['condition']}
                native.write(path.parent/('baseline-'+case['condition']+'-reproduction.json'), pair_qualification[case['condition']])
            native.write(path.parent/case['id']/'result.json', result)
            native.write(path.parent/case['id']/'student-result.json', result)
        results.append(result)
        native.write(path.parent/'cohort-results.json', {'results':results,'stop_reason':stop_reason,
                     'pair_qualification':pair_qualification,'execution_and_recording_wall_s':time.perf_counter()-start})
        print(json.dumps({k:result.get(k) for k in ['condition','coefficient','status','official_lap_ms','damage',
                         'unique_tiles','total_tiles','charged_wrapper_actions','reason','error']}), flush=True)
    return int(stop_reason is not None or any(v['status'] != 'PASS' for v in pair_qualification.values()))


if __name__ == '__main__':
    raise SystemExit(main())
