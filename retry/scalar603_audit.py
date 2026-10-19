"""Read-only evidence audit; no compiler, evaluator or chooser execution."""
import time
CPU = time.process_time()
WALL = time.perf_counter()
import hashlib
import json
import re
import struct
from pathlib import Path

G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response603-private')


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    c = read(G / 'retry/scalar603_contract.json')
    r = read(G / 'retry/scalar603_result.json')
    tests = read(G / 'retry/scalar603_tests.json')
    saved = read(D / 'saved774-private.json')
    closed = read(D / 'CLOSED-private.json')
    call = read(D / 'CALL-private.json')
    compiler = read(D / 'compiler-private.json')
    assembly = (D / 'assembly-private.txt').read_text()
    binary = Path(c['command'][-1])
    checks = dict(
        one_source_candidate=all(sha(G / p) == h for p, h in c['source_sha256'].items()),
        compiler_runtime_pinned=all(sha(Path(p)) == h for p, h in c['compiler_runtime_sha256'].items()),
        python_headers_pinned=all(sha(Path(p)) == h for p, h in c['python_header_sha256'].items()),
        parent602_contract_pinned=sha(G / 'retry/segments602_contract.json') == c['source602_contract_sha256'],
        same_saved_input=sha(Path('/workspace/haic-response599-private/proposed-timing-input-private.json')) == c['input_sha256'],
        same774baseline=sha(Path('/workspace/haic-response602-private/saved774-comparison-private.json')) == c['baseline_saved_sha256'],
        registered_contract=read(D / 'REGISTERED-private.json')['contract_sha256'] == call['contract_sha256'] == sha(G / 'retry/scalar603_contract.json'),
        one_compilation=r['compilation_attempts'] == closed['compilation_attempts'] == 1 and compiler['command'] == c['command'] and compiler['returncode'] == 0,
        strict_options=all(q in c['command'] for q in ['-fno-fast-math', '-fno-associative-math', '-ffp-contract=off', '-fexcess-precision=standard', '-frounding-math', '-fno-tree-vectorize', '-fno-tree-slp-vectorize', '-mfpmath=sse', '-msse2']),
        binary_pin=sha(binary) == r['binary_sha256'] == call['binary_sha256'],
        assembly_pin=sha(D / 'assembly-private.txt') == r['assembly_audit']['disassembly_sha256'],
        no_FMA_instructions=not re.search(r'\b(?:vfmadd\w*|vfmsub\w*|vfnmadd\w*|vfnmsub\w*|fmadd\w*)\b', assembly),
        no_packed_FP_arithmetic=not re.search(r'\b(?:v?(?:add|sub|mul|div|sqrt|max|min)pd|v?(?:add|sub|mul|div|sqrt|max|min)ps)\b', assembly),
        scalar_binary64_nearest=r['compiled_environment']['FLT_EVAL_METHOD'] == 0 and r['compiled_environment']['DBL_MANT_DIG'] == 53 and r['compiled_environment']['rounding_mode'] == r['compiled_environment']['FE_TONEAREST'],
        all_pure_checks=tests['passed'] and tests['unchanged601memo_tests']['passed'],
        same39_synthetic_cases_charged=tests['synthetic_comparisons'] == 39 and tests['charged_geometry'] == 78,
        saved774_bit_exact=len(saved) == 774 and all(q['exact'] and struct.pack('>d', q['actual']) == struct.pack('>d', q['expected']) for q in saved),
        no_old_baseline_evaluations=r['saved_comparison']['new_baseline_queries'] == 0,
        exactly_one_choose=r['chooser_calls'] == closed['chooser_calls'] == call['chooser_calls'] == 1,
        closed_result_pin=closed['result_sha256'] == sha(G / 'retry/scalar603_result.json'),
        tests_before_choose=call['tests_sha256'] == sha(G / 'retry/scalar603_tests.json'),
        private_evidence_pinned=all(sha(D / p) == h for p, h in r['private_sha256'].items()),
        all_parity=all(r['parity'].values()),
        all4538raw_bytes=sha(D / 'diagnostics-private.json') == c['baseline_raw_sha256'],
        all7176wheel_bytes=sha(D / 'wheel-private.json') == c['baseline_wheel_sha256'],
        model906_888=r['cost']['model_attempted'] == 906 and r['cost']['model_completed'] == 888,
        force7176=r['cost']['external_force'] == 3624 and r['cost']['internal_force'] == 3552 and r['cost']['total_force'] == 7176,
        geometry_charged=r['pre_choose_geometry'] == 78 + 774 and r['cost']['geometry'] == 78 + 774 + 2641,
        memo_and_pair_order_work_unchanged=r['memo']['hits'] == 145 and r['memo']['misses'] == 774 and r['prepared_road']['polygon_segment_pairs'] == 196667,
        all_work_caps=all(r['cost'][k] <= cap for k, cap in c['caps'].items()),
        zero_forbidden_work=all(r[k] == 0 for k in ['native', 'worlds', 'resets', 'actions', 'solver', 'FD', 'new_seed', 'HOLDOUT', 'SEALED']),
        ledger_unchanged=r['research_remaining'] == 22211 and r['reserve'] == 84000 and r['reserve_used'] == 0,
        scoped_adoption_only=r['optimization_adopted'] and not r['pixel_act_promotion'] and not r['lap_gain_claim'],
        core_below5_single_sample=r['stages']['normal_core']['wall_s'] < 5,
        compiler_child_CPU_accounted=r['child_CPU_s'] > 0 and r['stages']['one_compilation_and_load']['CPU_s'] > 0)
    audit_cpu = time.process_time() - CPU
    audit_wall = time.perf_counter() - WALL
    total = dict(CPU_s=closed['time']['CPU_s'] + audit_cpu, wall_s=closed['time']['wall_s'] + audit_wall)
    checks['total_caps_with5s_summary_reserve'] = total['CPU_s'] + 5 < 300 and total['wall_s'] + 5 < 420
    before = r['single_sample_comparison']['baseline602']['wall_s']
    after = r['stages']['normal_core']['wall_s']
    output = dict(study=603, status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILURE', checks=checks,
                  audit_CPU_s=audit_cpu, audit_wall_s=audit_wall, total_through_audit=total,
                  summary_write_reserve_CPU_s=5, summary_write_reserve_wall_s=5,
                  single_sample_wall_reduction_s=before - after,
                  single_sample_wall_reduction_fraction=1 - after / before,
                  result_sha256=sha(G / 'retry/scalar603_result.json'), chooser=0, geometry=0, force=0, compiler=0, native=0)
    (G / 'retry/scalar603_audit.json').write_text(json.dumps(output, indent=2) + '\n')
    print(json.dumps(output, indent=2))
    assert all(checks.values())


if __name__ == '__main__':
    main()
