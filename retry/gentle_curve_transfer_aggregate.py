"""Saved-only paired DEV transfer results and actual cap-transition segments."""
import argparse
import json
from pathlib import Path
import time

import numpy as np

from retry.gentle_curve_aggregate import analyze as verify_frozen_actions
from retry.gentle_curve_limit_segments import summarize


def analyze(directory):
    directory = Path(directory)
    plan = json.loads((directory/'plan.json').read_text())
    cohort = json.loads((directory/'cohort-results.json').read_text())
    # The unchanged Stage91 verifier checks per-action formulas and resets its
    # reference stream at each coefficient-7 episode. Its single-condition lap
    # field is replaced below by the correct paired condition before saving.
    report = verify_frozen_actions(directory)
    report['stage'] = 92
    baselines = {}
    for case, result in zip(plan['cases'], report['results']):
        result['condition'] = case['condition']
        if case['coefficient'] == 7:
            baselines[case['condition']] = result
        reference = baselines.get(case['condition'])
        result['lap_delta_ms_vs_fresh_baseline'] = (
            result['official_lap_ms']-reference['official_lap_ms']
            if reference and reference.get('completed') and result.get('completed') else None)
        if result['status'] == 'UNEXECUTED':
            continue
        rows = [json.loads(line) for line in (directory/(case['id']+'-trace.jsonl')).read_text().splitlines()]
        finish = rows[-1]['info']['finish_time_s'] if result['completed'] else rows[-1]['truth_after']['time']
        dt = np.maximum(0., np.minimum([r['truth_after']['time'] for r in rows], finish)
                        - np.asarray([r['truth_before']['time'] for r in rows]))
        limits = summarize(rows, dt)
        assert abs(sum(limits['interval_dwell_s'].values())-dt.sum()) < 1e-8
        for segment in limits['segments']:
            first, last = rows[segment['start_step']-1], rows[segment['end_step']-1]
            segment['start_progress_tiles'] = first['truth_before']['unique_tiles']
            segment['end_progress_tiles'] = last['truth_after']['unique_tiles']
            segment['total_tiles'] = result['total_tiles']
            segment['lap_time_start_s'] = segment['start_time_s']-rows[0]['truth_before']['time']
            segment['lap_time_end_s'] = segment['end_time_s']-rows[0]['truth_before']['time']
        result['actual_limit_segments'] = limits
        result['gate_to_other_limit_transitions'] = [
            {'from':a,'to':b} for a,b in zip(limits['segments'][:-1],limits['segments'][1:])
            if a['curvature_subtype'] == 'gate14' and b['curvature_subtype'] != 'gate14']
    pairs = []
    for condition in plan['ordered_conditions']:
        baseline, candidate = [r for r in report['results'] if r['condition'] == condition]
        both = bool(baseline.get('completed') and candidate.get('completed'))
        qualified = cohort['pair_qualification'].get(condition,{}).get('status') == 'PASS'
        pairs.append({'condition':condition,'baseline_reproduced':qualified,
            'baseline_status':baseline['status'],'candidate_status':candidate['status'],
            'both_completed':both,'completion_preserved':both,
            'completion_lost':baseline.get('completed') is True and candidate['status'] == 'DNF',
            'candidate_resource_censored':candidate['status'] == 'RESOURCE_CENSORED',
            'common_completed_lap_delta_ms':candidate['lap_delta_ms_vs_fresh_baseline'] if both else None,
            'baseline_damage':baseline.get('damage'),'candidate_damage':candidate.get('damage'),
            'damage_is_separate_warning':True})
    report['pairs'] = pairs
    report['interpretation'] = 'Two known DEV geometries, one episode per arm; no global safety/speed or champion claim.'
    report['no_minimum_lap_improvement_threshold'] = True
    report['HOLDOUT_details_or_SEALED_opened'] = False
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, type=Path)
    args = parser.parse_args()
    start = time.perf_counter()
    report = analyze(args.directory)
    report['analysis_wall_s'] = time.perf_counter()-start
    (args.directory/'comparison.json').write_text(json.dumps(report, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'actions':report['new_wrapper_actions'],'native_wall_s':report['native_and_recording_wall_s'],
                     'pairs':report['pairs']}))


if __name__ == '__main__':
    main()
