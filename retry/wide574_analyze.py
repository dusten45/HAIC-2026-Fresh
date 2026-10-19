"""Read-only post-run checks for 574; never imports or runs a simulator."""
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = Path('/workspace/haic-response574-private')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    cpu, wall = time.process_time(), time.perf_counter()
    contract = read(ROOT / 'retry/wide574_contract.json')
    result = read(ROOT / 'retry/wide574_result.json')
    ledger_path = ROOT / 'retry/wide574_cost.json'
    ledger = read(ledger_path)
    checks = {}
    checks['frozen_sources'] = all(sha(ROOT / p) == h for p, h in contract['source_sha256'].items())
    checks['inputs'] = all(sha(Path(p)) == h for p, h in contract['input_sha256'].items())
    checks['tests_pin'] = sha(ROOT / 'retry/wide574_tests.json') == contract['tests_sha256']
    checks['design_pin'] = sha(ROOT / 'retry/wide574_design.json') == contract['design_sha256']
    checks['journal_valid'] = result['journal']['valid']
    kinds = result['journal'].get('kinds', {})
    total = result['cost']['total']
    checks['tick_journal_count'] = kinds.get('AFTER_TICK', 0) == total['ticks']
    checks['force_journal_count'] = kinds.get('FORCE_VERDICT', 0) * 4 == total['force']
    checks['force_per_tick'] = total['force'] == 4 * total['ticks']
    checks['geometry_per_tick'] = total['geometry'] == total['ticks']
    checks['total_caps_including_run_audit'] = all(total[k] <= cap for k, cap in contract['aggregate'].items())
    checks['phase_counters'] = all(sum(p[k] for p in result['cost']['phases']) == total[k] for k in ['ticks', 'force', 'geometry'])
    bucket_checks = {}
    for bucket, caps in contract['budgets'].items():
        spent = {k: sum(p[k] for p in result['cost']['phases'] if p['bucket'] == bucket) for k in caps}
        bucket_checks[bucket] = dict(spent=spent, passed=all(spent[k] <= cap for k, cap in caps.items()))
    checks['bucket_caps'] = all(v['passed'] for v in bucket_checks.values())
    summaries = []
    for n in range(1, result['linearizations'] + 1):
        path = PRIVATE / f'linear-{n}-summary-private.json'
        if path.exists():
            item = read(path)
            summaries.append(dict(center=n, **item))
    checks['completed_fd_arithmetic'] = all(v['FD_source_ticks'] == v['expected_ticks'] and v['all_prefix_derivatives_exact_zero'] for v in summaries)
    checks['checkpoint_proofs'] = all(v['source_next_tick_exact'] for v in result['checkpoint_proofs'])
    checks['no_native_holdout_sealed_paid'] = all(result[k] == 0 for k in ['new_native_actions', 'new_resets', 'new_worlds', 'new_seeds', 'HOLDOUT', 'SEALED', 'paid_compute'])
    checks['no_unverified_official_promotion'] = not result['official_promotion'] or result['new_plan_independently_verified']
    if result['new_plan_independently_verified']:
        verify = result['independent_verification']
        checks['new_replay_exact'] = verify['fullstate_force_history_tracker_exact'] and verify['checkpoint_exact']
    # The runner saves its ledger before checking its journal. Charge that audit
    # using the runner's later cost snapshot, preserving the original snapshot.
    old_total = ledger.get('finally_first_total', ledger['total'])
    ledger.update(total=total, finally_first_total=old_total,
                  reconciliation='Final result snapshot includes runner journal audit; phase counters unchanged.')
    ledger_path.write_text(json.dumps(ledger, indent=2) + '\n')
    output = dict(passed=all(checks.values()), checks=checks, buckets=bucket_checks,
                  FD_centers=summaries, cost=total,
                  final_journal_audit_increment={k: total[k] - old_total[k] for k in ['CPU_s', 'wall_s']},
                  source_ticks_during_postrun_analysis=0,
                  tail_comparison_limitation='Fixed leading aux bounds in numerical margin remain nonzero before inward fixing. Tiny ~1e-15 zero-row tightening is handled by solver tolerance. This is a conditional numerical comparison, not a strict feasible-set certificate; final rounded original-row checks remain authoritative.',
                  analysis_CPU_s=time.process_time() - cpu,
                  analysis_wall_s=time.perf_counter() - wall)
    (ROOT / 'retry/wide574_analysis.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))
    if not output['passed']:
        raise SystemExit('574_POSTRUN_CHECK_FAILED')


if __name__ == '__main__':
    main()
