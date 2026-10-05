"""Matched full-episode results and clean-prefix plan errors from saved artifacts."""

import argparse
import json
from pathlib import Path

import numpy as np


def hud_errors(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    estimates, truths = [], []
    for record in manifest['episodes']:
        with np.load(directory / record['path'], allow_pickle=False) as saved:
            frames = saved['frames'][:-1].astype(np.float32) / 255.
        raw = (frames[:, 77:83, 10:13].sum(axis=(1, 2)) - .27) / .085
        limited = np.clip(raw, 0, 80)
        average = .5 * (limited + np.r_[limited[:1], limited[:-1]])
        estimates.append(np.column_stack((average, limited, np.clip(raw, 0, 100))))
        trace = directory / f"track{record['track_id']}_seed{record['geometry_seed']}.jsonl"
        with trace.open() as file:
            truths.extend(json.loads(line)['pre']['speed'] for line in file)
    prediction, truth = np.concatenate(estimates), np.asarray(truths)
    result: dict = dict(episodes=len(manifest['episodes']), geometry_count=manifest['geometry_count'],
                  pre_observations=len(truth), coefficient_fit=False, driving_experiment=False,
                  true_speed_max=float(truth.max()))
    for scope, mask in (('all', np.ones(len(truth), bool)), ('true_speed_above80', truth > 80)):
        result[scope] = {}
        for column, name in enumerate(('average2_clip80', 'newest_clip80', 'newest_clip100')):
            error = prediction[mask, column] - truth[mask]
            result[scope][name] = dict(count=len(error), mae=float(abs(error).mean()),
                p95=float(np.percentile(abs(error), 95)), bias=float(error.mean()))
    return result


def analyze(directory):
    directory = Path(directory)
    manifest = json.loads((directory / 'manifest.json').read_text())
    records = []
    for record in manifest['episodes']:
        item = dict(record)
        trace = directory / f"track{record['track_id']}_seed{record['geometry_seed']}.jsonl"
        last = None
        fallback_first = None
        with trace.open() as file:
            for line in file:
                row = json.loads(line)
                last = row
                if fallback_first is None and row.get('tracker', {}).get('fallback_mode', 'none') != 'none':
                    fallback_first = row['step']
        item['first_fallback_step'] = fallback_first
        boundary = bool(last and max(abs(v) for v in last['post']['position']) > 2000. / 6.)
        item['world_boundary_exit'] = boundary
        item['failure_class'] = ('finished' if record['finished'] else 'execution_error' if record['error']
            else 'collision_retirement' if record['reason'] == 'crash'
            else 'stalled' if record['first_sustained_stop_step'] is not None
            else 'off_track_boundary' if boundary
            else 'off_track_no_progress' if record['off_track_retirement']
            else record['reason'])
        if manifest['mode'] == 'student':
            with np.load(directory / record['path'], allow_pickle=False) as archive:
                valid, predicted, target = archive['valid'], archive['predictions'], archive['plans']
                end = record['first_collision_step']
                end = record['steps'] if end is None else end + 1
                for name, start in (('clean_prefix', 0), ('pre_contact_window', max(0, end - 15))):
                    mask = valid[start:end]
                    delta = (predicted[start:end] - target[start:end])[mask]
                    item[name] = dict(actions=end - start, valid_points=int(mask.sum()),
                        position_mae=float(np.linalg.norm(delta[:, :2], axis=1).mean()) if len(delta) else None,
                        speed_mae=float(np.abs(delta[:, 2]).mean()) if len(delta) else None)
        records.append(item)
    finishes = [r for r in records if r['finished'] and r['complete']]
    failure_types = sorted({r['failure_class'] for r in records})
    return dict(directory=str(directory), mode=manifest['mode'], conditions=manifest['conditions'],
        episode_count=len(records), road_count=len({(r['track_id'], r['geometry_seed']) for r in records}),
        geometry_count=len({r['geometry_seed'] for r in records}),
        requested_episode_count=manifest['requested_episode_count'], batch_complete=manifest['batch_complete'],
        finish_count=len(finishes), successful_road_count=len(finishes),
        mean_finished_lap_s=float(np.mean([r['lap_time_s'] for r in finishes])) if finishes else None,
        collision_episodes=sum(r['collisions'] > 0 for r in records),
        collision_actions=sum(r['collisions'] for r in records),
        off_track_episodes=sum(r['world_boundary_exit'] or r['off_track_retirement'] for r in records),
        stalled_episodes=sum(r['first_sustained_stop_step'] is not None for r in records),
        failure_counts={name: sum(r['failure_class'] == name for r in records) for name in failure_types},
        records=records)


def compare(reference, candidate) -> dict:
    if reference['conditions'] != candidate['conditions']:
        raise ValueError('Comparison conditions differ')
    original = {(r['track_id'], r['geometry_seed']): r for r in reference['records']}
    pairs, reset_mismatches = [], []
    for item in candidate['records']:
        key = item['track_id'], item['geometry_seed']
        if key not in original:
            continue
        base = original[key]
        if item['reset_sha256'] != base['reset_sha256']:
            reset_mismatches.append(key)
        if item['finished'] and base['finished']:
            pairs.append(dict(track_id=key[0], geometry_seed=key[1],
                reference_s=base['lap_time_s'], candidate_s=item['lap_time_s'],
                delta_s=item['lap_time_s'] - base['lap_time_s']))
    return dict(reference=reference['directory'], candidate=candidate['directory'],
        reset_mismatches=reset_mismatches, jointly_finished_road_count=len(pairs),
        candidate_faster_on_joint_finishes=sum(r['delta_s'] < 0 for r in pairs),
        mean_paired_delta_s=float(np.mean([r['delta_s'] for r in pairs])) if pairs else None,
        pairs=pairs, note='Conditional paired lap times; finish counts take precedence.')


def paired_finish_timing(reference, candidate, target_track=4, goal_seconds=10.5) -> dict:
    """Only matched completed laps enter speed comparisons; never pool finish sets."""
    comparison = compare(reference, candidate)
    if comparison['reset_mismatches']:
        raise ValueError('Initial states differ on shared road settings')
    pairs = comparison['pairs']
    result: dict = dict(comparison, common_road_count=len(pairs),
        common_geometry_count=len({row['geometry_seed'] for row in pairs}),
        paired_reference_mean_s=float(np.mean([row['reference_s'] for row in pairs])) if pairs else None,
        paired_candidate_mean_s=float(np.mean([row['candidate_s'] for row in pairs])) if pairs else None,
        target_track=target_track, goal_seconds=goal_seconds,
        goal_interpretation='Explicit low-10 timing reference, not a feasibility bound',
        official_reported_track4_seed_known=False)
    base = {(row['track_id'], row['geometry_seed']): row for row in reference['records']}
    target_rows = []
    for row in candidate['records']:
        if row['track_id'] != target_track:
            continue
        key = row['track_id'], row['geometry_seed']
        other = base.get(key)
        finished = bool(row['finished'] and row.get('complete', True))
        base_finished = bool(other and other['finished'] and other.get('complete', True))
        lap = float(row['lap_time_s']) if finished else None
        previous = float(other['lap_time_s']) if other is not None and base_finished else None
        target_rows.append(dict(track_id=key[0], geometry_seed=key[1],
            reference_finished=base_finished, candidate_finished=finished,
            reference_s=previous, candidate_s=lap,
            paired_delta_s=lap - previous if lap is not None and previous is not None else None,
            gap_to_goal_s=lap - goal_seconds if lap is not None else None,
            required_lap_reduction_percent=100 * (lap - goal_seconds) / lap if lap is not None else None,
            gap_to_10_seconds=lap - 10. if lap is not None else None))
    result['target_roads'] = sorted(target_rows, key=lambda row: row['geometry_seed'])
    result['note'] = 'Matched shared finishes only; conditional timing, not overall superiority or learned-student performance.'
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', nargs='+', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--hud-replay', type=Path)
    parser.add_argument('--paired-only', action='store_true', help='Read two manifests only; no traces or model execution')
    parser.add_argument('--target-track', type=int, default=4)
    parser.add_argument('--lap-goal', type=float, default=10.5)
    args = parser.parse_args(argv)
    if args.output.exists():
        parser.error('Preserve previous reports; choose a fresh output file')
    if args.paired_only:
        if len(args.runs) != 2 or not np.isfinite(args.lap_goal) or args.lap_goal <= 0:
            parser.error('Paired timing needs two runs and a positive finite goal')
        inputs = []
        for path in args.runs:
            manifest = json.loads((path / 'manifest.json').read_text())
            if not manifest['batch_complete'] or any(not row['complete'] for row in manifest['episodes']):
                raise ValueError('Only completed comparison batches are supported')
            inputs.append(dict(directory=str(path), conditions=manifest['conditions'], records=manifest['episodes']))
        result = paired_finish_timing(*inputs, target_track=args.target_track, goal_seconds=args.lap_goal)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
        print(json.dumps(result), flush=True)
        return result
    reports = [analyze(path) for path in args.runs]
    result: dict = dict(runs=reports, comparisons=[compare(reports[0], row) for row in reports[1:]],
                  protected_roads_used=False, new_experiments_run=False)
    if args.hud_replay:
        result['hud_diagnostic'] = hud_errors(args.hud_replay)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps([dict(mode=r['mode'], finishes=r['finish_count'], episodes=r['episode_count'],
        geometries=r['geometry_count'], finished_mean_s=r['mean_finished_lap_s'],
        failures=r['failure_counts']) for r in reports]), flush=True)
    if args.hud_replay:
        print(json.dumps(result['hud_diagnostic']), flush=True)
    return result


if __name__ == '__main__':
    main()
