"""Frozen global-cap validation: two transfers, then a conditional interaction cell.

The original archive and worker stay immutable. Two numeric literals change in
a private copied archive; the coefficient-7 no-op diagnostic changes one assert.
Cached baseline replay uses pixels only and never constructs an environment.
"""
import argparse
import base64
import datetime as dt
import hashlib
import json
from pathlib import Path
import signal
import sys
import time

import numpy as np

from retry import fresh_dev_distribution as native
from retry.gentle_curve_probe import execute
from retry.pixel_sandbox_runtime import SandboxWorker
from retry.road_keep_student_probe import copy_assets


def cached_reproduce(reference_plan, reference_directory, case_id, directory, coefficient=7):
    """Reset and act on a saved stream: no simulator reset/step or new pixels."""
    start = time.perf_counter()
    reference_directory, directory = Path(reference_directory), Path(directory)
    directory.mkdir(mode=0o700)
    clean, package, worker, runtime = copy_assets(reference_plan, native.clone(reference_plan, directory))
    curve = clean/'curve.py'
    curve.write_bytes(Path(reference_plan['curve_source_path']).read_bytes()); curve.chmod(0o444)
    config = clean/'curve-config.json'; config.write_text(json.dumps({'coefficient':coefficient})+'\n'); config.chmod(0o444)
    with np.load(reference_directory/(case_id+'-pixels-actions.npz'), allow_pickle=False) as saved:
        frames, actions = saved['frames'].copy(), saved['actions'].copy()
    with np.load(reference_directory/(case_id+'-student-masks.npz'), allow_pickle=False) as saved:
        masks = saved['masks'].copy()
    rows = [json.loads(line) for line in (reference_directory/(case_id+'-trace.jsonl')).read_text().splitlines()]
    old = json.loads((reference_directory/case_id/'result.json').read_text())
    assert old['coefficient'] == coefficient and coefficient in (7,14)
    actor = None
    try:
        actor = SandboxWorker([sys.executable, '-I', '-B', str(worker), str(package)], clean, runtime,
                              sandbox=reference_plan['sandbox_binary'])
        assert actor.ready['module_sha256'] == old['worker_ready']['module_sha256']
        assert actor.ready['curve_source_sha256'] == old['worker_ready']['curve_source_sha256']
        assert actor.ready['student_model_sha256'] == reference_plan['student_model_sha256']
        assert actor.ready['numpy_version'] == old['worker_ready']['numpy_version'] == '1.26.0'
        observation = np.repeat(frames[0][None], 4, axis=0).astype(np.float32)/255
        reset, _ = actor.call('reset', observation)
        assert reset['ok']
        assert base64.b64decode(reset['student_mask_base64']) == masks[0].tobytes()
        for index, row in enumerate(rows):
            observation = frames[np.maximum(0, np.arange(index-3,index+1))].astype(np.float32)/255
            response, _ = actor.call('act', observation)
            assert np.array_equal(np.asarray(response['action'], np.float32), actions[index]), index
            assert base64.b64decode(response['student_mask_base64']) == masks[index+1].tobytes(), index
            for key in ('action','route_telemetry','cap_diagnostic','curve_diagnostic','previous_steer_after','original_calls'):
                assert response[key] == row['policy_response'][key], (index,key)
        cpu = response['actor_cumulative_CPU_s']
    finally:
        reap = actor.close() if actor else None
    assert reap and reap['process_reaped']
    return {'status':'PASS', 'actions_exact':len(actions), 'masks_exact':len(masks),
            'semantic_telemetry_exact':True, 'new_environment_resets':0, 'new_environment_actions':0,
            'cached_policy_act_calls':len(actions), 'cached_policy_reset_calls':1,
            'cached_student_inference_calls':len(masks), 'actor_CPU_s':cpu,
            'wall_s':time.perf_counter()-start, 'worker_reaping':reap}



def admitted(plan):
    """Keep the two transfer outcomes; require both qualifications for cell four."""
    bundle = json.loads(Path(plan['bundle_contract_path']).read_text())
    assert native.sha(Path(plan['bundle_contract_path'])) == plan['bundle_contract_sha256']
    assert bundle['max_actions'] == 6000 and bundle['max_actions_each'] == 2000
    assert bundle['candidate_archive_sha256'] == plan['candidate']['archive_sha256']
    budget = json.loads(Path(plan['effective_budget_path']).read_text())
    assert budget['B_operating_cap'] == 650000 and budget['final_reserved_actions'] == 84000
    assert budget['research_remaining'] >= 2000
    prior = []
    for source in plan.get('preceding_comparisons', []):
        previous = json.loads(Path(source).read_text())
        assert previous['all_required_evidence_verified'], 'preceding comparison has a contract/evidence error'
        prior.append(previous)
    if plan['stage'] == 98:
        assert len(prior) == 2 and {p['stage'] for p in prior} == {96,97}
        assert all(p['pair']['both_completed_verified'] for p in prior), 'combination requires both qualified completions'
    return {'status':'PASS','stage':plan['stage'],
            'preceding_comparison_sha256':{p:native.sha(Path(p)) for p in plan.get('preceding_comparisons',[])},
            'research_available':budget['research_remaining'],'historical_baseline_new_episodes':0}


def run(path):
    path = Path(path).resolve(); plan = json.loads(path.read_text())
    assert native.sha(path) == (path.parent/'plan.sha256').read_text().split()[0]
    assert len(plan['cases']) == 1 and plan['cases'][0]['coefficient'] in (7,14)
    assert plan['stage'] in (96,97,98)
    assert plan['cases'][0]['coefficient'] == (14 if plan['stage'] == 98 else 7)
    assert plan['global_cap'] == 40 and plan['max_actions'] == 2000
    assert plan['stage_budgets'] == {plan['cases'][0]['id']:2000}
    assert plan['B_operating_cap'] == 650000 and plan['research_remaining_before'] >= 2000
    for group in ('source_sha256','reference_sha256'):
        for name, expected in plan[group].items():
            assert native.sha(Path(name)) == expected, name
    ready = json.loads((path.parent/'preflight.json').read_text())
    assert ready['status'] == 'PASS' and ready['plan_sha256'] == native.sha(path)
    assert ready['historical_baseline_comparable'] and ready['cached_baseline_reproduction_pass']
    admission = admitted(plan)
    native.write(path.parent/'admission.json', admission)
    native.available(plan, path.parent)
    with (path.parent/'execution-claim.json').open('x') as claim:
        json.dump({'claimed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                   'plan_sha256':native.sha(path)}, claim)
    def interrupted(_signal, _frame):
        raise RuntimeError('Supervisor termination requested')
    signal.signal(signal.SIGTERM, interrupted)
    start = time.perf_counter()
    case = plan['cases'][0]
    result, stopped = execute(case, plan, path)
    result.update(global_cap=40, coefficient=case['coefficient'], policy_changed=True,
                  policy_changed_since_training=True, historical_comparison_only=True,
                  historical_full_stream_reproduction=False, historical_baseline_episode_rerun=False)
    native.write(path.parent/case['id']/'result.json', result)
    native.write(path.parent/case['id']/'student-result.json', result)
    native.write(path.parent/'cohort-results.json', {'results':[result], 'stop_reason':result.get('error') if stopped else None,
                 'execution_and_recording_wall_s':time.perf_counter()-start,
                 'historical_baseline_episode_rerun':False})
    return result, stopped


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--plan', required=True, type=Path)
    result, stopped=run(parser.parse_args().plan)
    print(json.dumps({k:result.get(k) for k in ('status','completed','official_lap_ms','damage','unique_tiles','total_tiles','charged_wrapper_actions','error')}), flush=True)
    return int(stopped)


if __name__ == '__main__':
    raise SystemExit(main())
