"""One-use ascending scalar DEV probe; stop larger values on completion loss.

Frozen grayscale student, existing recorder and native simulator are reused.
Condition identities and raw output stay in the private supervisor directory.
"""
import argparse
import datetime as dt
import json
from pathlib import Path
import signal
import time

import numpy as np

from retry import fresh_dev_distribution as native
from retry import road_keep_transfer_probe as recorder
from retry.pixel_sandbox_runtime import SandboxWorker


def baseline_reproduced(directory, case, plan):
    result = json.loads((directory/case['id']/'result.json').read_text())
    expected = json.loads(Path(plan['baseline_result_path']).read_text())
    assert result['status'] == 'COMPLETE'
    assert result['official_lap_ms'] == expected['official_lap_ms'] == 59560
    assert result['damage'] == expected['damage'] == 0
    assert result['action_sequence_sha256'] == expected['action_sequence_sha256']
    checks = {}
    for suffix, old_path, keys in [
        ('pixels-actions.npz', plan['baseline_pixels_actions_path'], ['frames', 'actions']),
        ('student-masks.npz', plan['baseline_masks_path'], ['masks']),
    ]:
        with np.load(directory/(case['id']+'-'+suffix), allow_pickle=False) as new, np.load(old_path, allow_pickle=False) as old:
            for key in keys:
                assert np.array_equal(new[key], old[key]), key
                checks[key+'_exact'] = True
    native.write(directory/'baseline-reproduction.json', {'status':'PASS', **checks,
                 'official_lap_ms':59560, 'damage':0, 'extra_policy_environment_calls':0})


def execute(case, plan, path):
    original_worker, original_assets = recorder.PipeWorker, recorder.copy_assets

    class Worker(SandboxWorker):
        def __init__(self, command, clean, environment):
            super().__init__(command, clean, environment, sandbox=plan['sandbox_binary'])
            assert self.ready['curve_coefficient'] == case['coefficient']
            assert self.ready['curve_source_sha256'] == plan['source_sha256'][plan['curve_source_path']]

    def assets(current_plan, execution):
        execution = original_assets(current_plan, execution)
        clean = execution[0]
        patch = clean/'curve.py'
        patch.write_bytes(Path(plan['curve_source_path']).read_bytes())
        patch.chmod(0o444)
        assert native.sha(patch) == plan['source_sha256'][plan['curve_source_path']]
        config = clean/'curve-config.json'
        config.write_text(json.dumps({'coefficient':case['coefficient']})+'\n')
        config.chmod(0o444)
        return execution

    recorder.PipeWorker, recorder.copy_assets = Worker, assets
    try:
        result, stopped = recorder.recorded_episode(case, plan, path)
    finally:
        recorder.PipeWorker, recorder.copy_assets = original_worker, original_assets
    if result.get('error') == "RuntimeError('Per-case ceiling without native endpoint')":
        result['failure_type'] = 'per_case_action_cap'
        stopped = False
    elif stopped:
        result['status'] = 'TECHNICAL_ERROR' if result.get('raw_step_ticks', 0) < 8000 else result['status']
    result.update(coefficient=case['coefficient'], policy_changed=case['coefficient'] != 7,
                  policy_changed_since_training=case['coefficient'] != 7,
                  policy_changed_during_episode=False, historical_comparison_only=False,
                  historical_full_stream_reproduction=case['coefficient'] == 7)
    native.write(path.parent/case['id']/'result.json', result)
    native.write(path.parent/case['id']/'student-result.json', result)
    return result, stopped


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', required=True, type=Path)
    path = parser.parse_args().plan.resolve()
    plan = json.loads(path.read_text())
    assert native.sha(path) == (path.parent/'plan.sha256').read_text().split()[0]
    assert [c['coefficient'] for c in plan['cases']] == [7, 8, 10, 14]
    assert plan['max_actions'] == 8000 and all(v == 2000 for v in plan['stage_budgets'].values())
    for group in ['source_sha256', 'reference_sha256']:
        for name, expected in plan[group].items():
            assert native.sha(Path(name)) == expected, name
    ready = json.loads((path.parent/'preflight.json').read_text())
    assert ready['status'] == 'PASS' and ready['plan_sha256'] == native.sha(path)
    native.available(plan, path.parent)
    with (path.parent/'execution-claim.json').open('x') as claim:
        json.dump({'claimed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                   'plan_sha256':native.sha(path)}, claim)
    def interrupted(_signal, _frame):
        raise RuntimeError('Supervisor termination requested')
    signal.signal(signal.SIGTERM, interrupted)
    start = time.perf_counter()
    results, stop_reason = [], None
    for case in plan['cases']:
        if stop_reason:
            result = {'id':case['id'], 'coefficient':case['coefficient'], 'status':'UNEXECUTED',
                      'episode_count':0, 'charged_wrapper_actions':0, 'reason':stop_reason}
            (path.parent/case['id']).mkdir(mode=0o700)
            native.write(path.parent/case['id']/'result.json', result)
        else:
            result, technical = execute(case, plan, path)
            if technical:
                stop_reason = 'technical_error: '+str(result.get('error'))
            elif not result.get('completed'):
                stop_reason = 'completion_not_preserved_at_'+str(case['coefficient'])+': '+result['status']
            elif case['coefficient'] == 7:
                try:
                    baseline_reproduced(path.parent, case, plan)
                except Exception as error:
                    stop_reason = 'baseline_reproduction_error: '+repr(error)
                    native.write(path.parent/'baseline-reproduction.json', {'status':'FAIL', 'error':repr(error)})
        results.append(result)
        native.write(path.parent/'cohort-results.json', {'results':results, 'stop_reason':stop_reason,
                     'execution_and_recording_wall_s':time.perf_counter()-start})
        print(json.dumps({k:result.get(k) for k in ['coefficient','status','official_lap_ms','damage',
                         'unique_tiles','total_tiles','charged_wrapper_actions','reason','error']}), flush=True)
    return int(stop_reason is not None and ('technical' in stop_reason or 'reproduction' in stop_reason))


if __name__ == '__main__':
    raise SystemExit(main())
