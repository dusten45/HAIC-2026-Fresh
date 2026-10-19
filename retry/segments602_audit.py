"""Read-only602 audit: no evaluator or policy imports."""
import time
CPU = time.process_time()
WALL = time.perf_counter()
import hashlib
import json
import struct
from pathlib import Path

G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response602-private')


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    c = read(G / 'retry/segments602_contract.json')
    r = read(G / 'retry/segments602_result.json')
    tests = read(G / 'retry/segments602_tests.json')
    closed = read(D / 'CLOSED-private.json')
    saved = read(D / 'saved774-comparison-private.json')
    checks = dict(
        one_implementation_frozen=all(sha(G / p) == h for p, h in c['implementation_sha256'].items()),
        registered_contract=read(D / 'REGISTERED-private.json')['contract_sha256'] == sha(G / 'retry/segments602_contract.json'),
        one_call=read(D / 'CALL-private.json')['chooser_calls'] == r['chooser_calls'] == closed['chooser_calls'] == 1,
        call_same_contract=read(D / 'CALL-private.json')['contract_sha256'] == sha(G / 'retry/segments602_contract.json'),
        tests_before_call=read(D / 'CALL-private.json')['tests_sha256'] == sha(G / 'retry/segments602_tests.json'),
        source601_pinned=sha(G / 'retry/profile601_optimized_result.json') == c['source601_sha256'],
        same_input=sha(Path('/workspace/haic-response599-private/proposed-timing-input-private.json')) == c['input_sha256'],
        private_outputs_pinned=all(sha(D / p) == h for p, h in r['private_sha256'].items()),
        closed_result_pinned=closed['result_sha256'] == sha(G / 'retry/segments602_result.json'),
        pure_checks=tests['passed'] and tests['unchanged601memo_tests']['passed'],
        synthetic_charges=tests['charged_geometry'] == 2 * tests['synthetic_comparisons'] == 78,
        saved774_exact=len(saved) == 774 and all(q['exact'] and struct.pack('>d', q['expected']) == struct.pack('>d', q['actual']) for q in saved),
        baseline_values_reused=r['saved_comparison']['baseline_reused'] == 774 and r['saved_comparison']['new_baseline_queries'] == 0,
        new_evaluator_charges=r['pre_choose_geometry'] == 78 + 774 and r['cost']['geometry'] == 78 + 774 + 2641,
        all_parity=all(r['parity'].values()),
        all_raw_diagnostics_byte_exact=sha(D / 'diagnostics-private.json') == c['baseline_raw_sha256'],
        all_wheel_returns_byte_exact=sha(D / 'wheel-private.json') == c['baseline_wheel_sha256'],
        model906_888=r['cost']['model_attempted'] == 906 and r['cost']['model_completed'] == 888,
        force7176=r['cost']['external_force'] == 3624 and r['cost']['internal_force'] == 3552 and r['cost']['total_force'] == 7176,
        logical_geometry_fully_charged=r['cost']['geometry_source_footprint'] == 919 and r['planner_cost']['geometry_checks'] == 919,
        saved_and_normal_pair_work_equal=r['saved_comparison']['polygon_segment_pairs'] == r['prepared_road']['polygon_segment_pairs'] == 196667,
        memo_unchanged=r['memo']['hits'] == 145 and r['memo']['misses'] == r['prepared_road']['margin_calls'] == 774,
        work_caps=all(r['cost'][k] <= cap for k, cap in c['caps'].items()),
        zero_forbidden_work=all(r[k] == 0 for k in ['native', 'worlds', 'resets', 'actions', 'solver', 'FD', 'new_seed', 'HOLDOUT', 'SEALED']),
        ledger_unchanged=r['research_remaining'] == 22211 and r['reserve'] == 84000 and r['reserve_used'] == 0,
        scoped_exact_adoption=r['optimization_adopted'] and r['status'] == 'EXACT_PREPARED_SEGMENTS_VALIDATED' and not r['pixel_act_promotion'] and not r['lap_gain_claim'],
        still_above5=r['stages']['normal_core']['wall_s'] >= 5)
    audit_cpu = time.process_time() - CPU
    audit_wall = time.perf_counter() - WALL
    total = dict(CPU_s=closed['time']['CPU_s'] + audit_cpu, wall_s=closed['time']['wall_s'] + audit_wall)
    checks['time_caps_with5s_summary_reserve'] = total['CPU_s'] + 5 < 240 and total['wall_s'] + 5 < 300
    old = r['single_sample_comparison']['baseline601']['wall_s']
    now = r['stages']['normal_core']['wall_s']
    output = dict(study=602, status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILURE', checks=checks,
                  audit_CPU_s=audit_cpu, audit_wall_s=audit_wall, total_through_audit=total,
                  summary_reserve_CPU_s=5, summary_reserve_wall_s=5,
                  normal_single_sample_wall_reduction_s=old - now,
                  normal_single_sample_wall_reduction_fraction=1 - now / old,
                  result_sha256=sha(G / 'retry/segments602_result.json'), chooser=0, geometry=0, force=0, native=0)
    (G / 'retry/segments602_audit.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))
    assert all(checks.values())


if __name__ == '__main__':
    main()
