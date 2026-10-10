"""One archived-policy cap sensitivity against verified saved DEV baselines.

Reuses the pixel worker, native environment and charged episode evaluator.
Only one literal in an isolated archive changes; the baseline is never edited.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import statistics
import time
import zipfile

from retry import fresh_dev_distribution as cohort
from retry.full_route_reproduction import truth


def build_candidate(baseline, directory):
    directory.mkdir(mode=0o700)
    archive = Path(baseline['archive_path'])
    assert cohort.sha(archive) == baseline['archive_sha256']
    module = 'retry/champion_distance_cap.py'
    old, new = b'np.sqrt(10. * d)', b'np.sqrt(11. * d)'
    data = {}
    with zipfile.ZipFile(archive) as zipped:
        assert set(zipped.namelist()) == set(baseline['members_sha256'])
        for name, wanted in baseline['members_sha256'].items():
            data[name] = zipped.read(name)
            assert hashlib.sha256(data[name]).hexdigest() == wanted
    assert data[module].count(old) == 1 and new not in data[module]
    original = data[module]; data[module] = original.replace(old, new)
    assert data[module].replace(new, old) == original
    target = directory/'candidate.zip'
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as zipped:
        for name in sorted(data):
            entry = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            entry.compress_type = zipfile.ZIP_DEFLATED
            zipped.writestr(entry, data[name])
    target.chmod(0o600)
    candidate = {'archive_path':str(target), 'archive_sha256':cohort.sha(target),
                 'members_sha256':{n:hashlib.sha256(v).hexdigest() for n,v in data.items()},
                 'baseline_archive_sha256':baseline['archive_sha256'],
                 'changed_member':module, 'unchanged_members':len(data)-1,
                 'single_change':'radicand 10*d to11*d; equivalent heuristic coefficient5 to5.5'}
    cohort.write(directory/'candidate.json', candidate)
    return candidate


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args(); path = args.plan.resolve(); directory = path.parent
    plan = json.loads(path.read_text()); started = time.perf_counter()
    assert cohort.sha(path) == (directory/'plan.sha256').read_text().split()[0]
    for name, wanted in plan['source_sha256'].items(): assert cohort.sha(Path(name)) == wanted, name
    assert len(plan['cases']) == 4 and plan['max_actions'] == 8000
    execution = cohort.clone(plan, directory)
    official_factory = cohort.make_env; results = []; stop_reason = None
    for case in plan['cases']:
        receipt = {}
        if stop_reason is None:
            try: cohort.available(plan, directory)
            except Exception as error: stop_reason = repr(error)
        if stop_reason is not None:
            result = {'id':case['id'], 'reference_id':case['reference_id'], 'status':'UNEXECUTED',
                      'reason':stop_reason, 'episode_count':0, 'retries':0, 'charged_wrapper_actions':0,
                      'official_lap_ms':None, 'official_progress':None, 'failure_type':None}
        else:
            def guarded_factory():
                env = official_factory(); original_reset = env.reset
                def guarded_reset(*args, **kwargs):
                    obs, info = original_reset(*args, **kwargs)
                    receipt['actual_reset_raw_ticks'] = round(env.unwrapped.t*50)
                    assert hashlib.sha256(obs.tobytes()).hexdigest() == case['baseline_initial_observation_sha256']
                    actual = truth(env); expected = case['baseline_initial_truth']
                    assert {k:actual[k] for k in expected} == expected
                    receipt.update(initial_full_pixel_stack_equal=True, recorded_initial_truth_equal=True)
                    return obs, info
                env.reset = guarded_reset
                return env
            cohort.make_env = guarded_factory
            try: result, technical_stop = cohort.episode(case, plan, path, execution)
            finally: cohort.make_env = official_factory
            result.update(reference_id=case['reference_id'], baseline_identity_receipt=receipt)
            if receipt.get('actual_reset_raw_ticks'):
                result['raw_reset_ticks'] = receipt['actual_reset_raw_ticks']
            baseline = case['baseline_result']
            if result['status'] == 'COMPLETE':
                result.update(baseline_official_lap_ms=baseline['official_lap_ms'],
                              lap_delta_ms=result['official_lap_ms']-baseline['official_lap_ms'],
                              baseline_damage=baseline['damage'], damage_delta=result['damage']-baseline['damage'])
            elif result['status'] == 'DNF':
                stop_reason = 'RETIRE_FIRST_COMPLETION_LOSS'
                result.update(baseline_official_lap_ms=baseline['official_lap_ms'], baseline_damage=baseline['damage'],
                              lap_delta_ms=None, damage_delta=result['damage']-baseline['damage'])
            if technical_stop: stop_reason = 'INCONCLUSIVE_TECHNICAL_OR_RESOURCE_BOUNDARY'
            cohort.write(directory/case['id']/'result.json', result)
        results.append(result)
        report = {'results':results, 'stop_reason':stop_reason,
                  'status_counts':{s:sum(r['status']==s for r in results) for s in ('COMPLETE','DNF','RESOURCE_CENSORED','UNEXECUTED')},
                  'plan_sha256':cohort.sha(path), 'wall_s':time.perf_counter()-started,
                  'candidate_archive_sha256':plan['candidate']['archive_sha256'],
                  'new_baseline_runs':0, 'retries_or_second_coefficients':0, 'promotion_or_protected_runs':0}
        cohort.write(directory/'sensitivity-report.json', report)
        print(json.dumps({k:result.get(k) for k in ('id','status','official_lap_ms','lap_delta_ms','damage','damage_delta','charged_wrapper_actions','error')}), flush=True)
    complete = all(r['status'] == 'COMPLETE' for r in results)
    deltas = [r['lap_delta_ms'] for r in results] if complete else []
    mean = statistics.mean(deltas) if deltas else None
    median = statistics.median(deltas) if deltas else None
    verdict = ('KEEP_DEV_SINGLE_SENSITIVITY' if mean < 0 and median < 0 else 'RETIRE_NO_MEAN_AND_MEDIAN_LAP_GAIN') if complete else (stop_reason or 'INCONCLUSIVE')
    report.update(verdict=verdict, all_four_completions_preserved=complete,
                  mean_lap_delta_ms=mean, median_lap_delta_ms=median,
                  charged_wrapper_actions=json.loads((directory/'budget.json').read_text())['actions'],
                  original_v2_preserved=True, default_or_champion_changed=False,
                  further_coefficients_or_experiments=False)
    cohort.write(directory/'sensitivity-report.json', report)
    return int(verdict.startswith('INCONCLUSIVE'))


if __name__ == '__main__': raise SystemExit(main())
