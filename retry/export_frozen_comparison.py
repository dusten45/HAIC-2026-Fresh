"""Export an allowlisted aggregate without private case identities or artifacts."""
import argparse
import json
import math
from pathlib import Path


def public_report(aggregate, cost, decision):
    """Select public scalars explicitly; never copy arbitrary input dictionaries."""
    common = aggregate['common_completion_metrics']
    native = cost['native']
    replay = cost['qualification']
    assert aggregate['performance_verdict'] in {
        'KEEP_CHAMPION_INCONCLUSIVE_COHORT', 'KEEP_CHAMPION_COMPLETION_LOSS',
        'COMPARISON_PASS_COMPLETION_GAIN', 'COMPARISON_PASS_PAIRED_LAP_GAIN',
        'KEEP_CHAMPION_INSUFFICIENT_COMMON_COMPLETIONS',
        'KEEP_CHAMPION_MIXED_OR_NO_LAP_GAIN'}
    assert replay['status'] in {'PASS', 'FAIL'}
    assert decision['status'] in {
        'ADOPTED', 'RETAINED_INCONCLUSIVE', 'RETAINED_COMPLETION_LOSS',
        'RETAINED_NO_GAIN'}
    report = {
        'schema': 1,
        'comparison': {
            'baseline': 'Original hazard-scheduled pixel policy, global cap40',
            'candidate': 'Same policy with the additive curvature denominator term removed',
            'policy_changes_after_DEV': 0,
        },
        'cohort': {
            'fresh_registered_geometries': aggregate['expected_count'],
            'episodes_recorded': aggregate['episodes_recorded'],
            'complete': aggregate['cohort_complete'],
            'baseline_completions': aggregate['baseline_completed_count'],
            'candidate_completions': aggregate['candidate_completed_count'],
            'unexecuted_pairs': len(aggregate['unexecuted']),
            'inconclusive_pairs': len(aggregate['inconclusive']),
            'censored_pairs': len(aggregate['censored_cases']),
            **{key: aggregate['counts'][key] for key in (
                'new_completion', 'lost_completion', 'common_dnf', 'common_completed')},
        },
        'performance_verdict': aggregate['performance_verdict'],
        'common_completed_laps': {
            'median_paired_delta_ms': aggregate['common_completion_median_lap_delta_ms'],
            'mean_paired_ratio': aggregate['common_completion_mean_lap_ratio'],
            'candidate_faster': sum(row['lap_delta_ms'] < 0 for row in common),
            'tied': sum(row['lap_delta_ms'] == 0 for row in common),
            'candidate_slower': sum(row['lap_delta_ms'] > 0 for row in common),
        },
        'separate_damage_warning': {
            'baseline_sum': aggregate['total_damage_diagnostic']['sums']['baseline'],
            'candidate_sum': aggregate['total_damage_diagnostic']['sums']['candidate'],
            'common_completion_pairs_with_increase': sum(row['damage_delta'] > 0 for row in common),
            'maximum_common_completion_increase': max(
                [0.0] + [row['damage_delta'] for row in common]),
            'exposure_caveat': 'Episode durations and completion exposure can differ.',
        },
        'observed_latency_ms': {
            'baseline_max_episode_p95': cost['actor_latency_by_arm']['A']['max_episode_p95_ms'],
            'candidate_max_episode_p95': cost['actor_latency_by_arm']['B']['max_episode_p95_ms'],
            'baseline_max_act': cost['actor_latency_by_arm']['A']['max_act_ms'],
            'candidate_max_act': cost['actor_latency_by_arm']['B']['max_act_ms'],
        },
        'native_cost': {key: native[key] for key in (
            'episodes', 'wrapper_actions', 'raw_step_ticks', 'raw_reset_ticks',
            'actor_act_calls', 'actor_reset_calls', 'wall_s', 'actor_CPU_s',
            'evaluator_CPU_s', 'max_act_ms', 'max_RSS_bytes',
            'automatic_retries', 'all_actors_reaped')},
        'same_host_qualification': {key: replay[key] for key in (
            'status', 'cold_starts', 'reset_calls', 'act_calls',
            'session_wall_sum_s', 'parallel_sessions', 'actor_CPU_s',
            'max_cold_ms', 'max_reset_ms', 'max_act_ms', 'max_RSS_bytes',
            'new_native_calls')},
        'decision': {key: decision[key] for key in (
            'status', 'current_champion_updated', 'previous_champions_preserved')},
        'limits': [
            'Four fresh registered geometries, one run per policy; a descriptive adoption gate.',
            'No zero failure probability, broad reliability or general safety claim.',
            'Same-host process reproduction does not establish fresh-machine or server parity.',
            'Damage and observed latency are separate warnings, not ranking replacements.',
            'No prior protected details, sealed data, private identities or document excerpts are published.',
        ],
    }
    # Every input-derived leaf must be a finite scalar of its declared kind.
    # Strings and arbitrary nested dictionaries cannot enter numeric fields.
    string_fields = {'same_host_qualification.status', 'decision.status'}
    bool_fields = {'cohort.complete', 'native_cost.all_actors_reaped',
                   'same_host_qualification.parallel_sessions',
                   'decision.current_champion_updated',
                   'decision.previous_champions_preserved'}
    nullable_fields = {'common_completed_laps.median_paired_delta_ms',
                       'common_completed_laps.mean_paired_ratio'}
    for group in ('cohort', 'common_completed_laps', 'separate_damage_warning', 'observed_latency_ms',
                  'native_cost', 'same_host_qualification', 'decision'):
        for key, value in report[group].items():
            field = group + '.' + key
            if field in string_fields or field == 'separate_damage_warning.exposure_caveat':
                continue
            if field in bool_fields:
                assert type(value) is bool, field
            elif value is None and field in nullable_fields:
                continue
            else:
                assert type(value) in (int, float) and math.isfinite(value), field
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('aggregate', 'cost', 'decision', 'output'):
        parser.add_argument('--' + name, required=True, type=Path)
    args = parser.parse_args()
    values = [json.loads(path.read_text()) for path in
              (args.aggregate, args.cost, args.decision)]
    report = public_report(*values)
    with args.output.open('x') as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
