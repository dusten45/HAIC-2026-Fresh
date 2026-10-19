"""Read-only aggregate audit; no model, chooser, integrator or native imports."""
import time
CPU = time.process_time()
WALL = time.perf_counter()
import collections
import hashlib
import json
from pathlib import Path

G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response600-private')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def main():
    r = read(G / 'retry/timing600_result.json')
    c = read(G / 'retry/timing600_contract.json')
    closed = read(D / 'CLOSED-private.json')
    output = read(D / 'output-private.json')
    registered = read(D / 'REGISTERED-private.json')
    rows = read(D / 'deferred-diagnostics-private.json')
    counts = collections.Counter(q['kind'] for q in rows)
    checks = {}
    checks['input_pinned'] = sha(Path('/workspace/haic-response599-private/proposed-timing-input-private.json')) == c['input_sha256']
    checks['implementation_frozen'] = sha(G / 'retry/timing600.py') == c['implementation_sha256']
    checks['original_contract_pinned'] = sha(G / 'retry/cold598_contract.json') == c['original_contract_sha256']
    checks['pure_tests_before_freeze'] = sha(G / 'retry/timing600_tests.json') == c['tests_sha256'] and read(G / 'retry/timing600_tests.json')['passed']
    checks['registration_and_start_same_contract'] = registered['contract_sha256'] == read(D / 'CALL_STARTED-private.json')['contract_sha256'] == sha(G / 'retry/timing600_contract.json')
    checks['closed_result_pinned'] = closed['result_sha256'] == sha(G / 'retry/timing600_result.json')
    checks['all_private_outputs_pinned'] = all(sha(D / p) == h for p, h in r['private_sha256'].items())
    checks['single_call_closed'] = r['chooser_calls'] == closed['chooser_calls'] == 1
    checks['independent_action_parity'] = output['action_bits'] == registered['input']['expected_action_bits']
    checks['independent_full_report_parity'] = digest(output['report']) == digest(registered['input']['expected_certificate'])
    checks['all_reported_parity_pass'] = all(r['parity'].values())
    checks['primitive_counts'] = counts == dict(BEFORE_MODEL_FORCE=906, MODEL_FORCE_VERDICT=906, BEFORE_MODEL_TICK=888, AFTER_MODEL_TICK=888, SOURCE_GEOMETRY_DIAGNOSTIC=888, TRACKING_TRIAL_START=31, TRACKING_TRIAL_END=31)
    checks['fresh_trial_reports_exact'] = all(q['exact'] for q in rows if q['kind'] == 'TRACKING_TRIAL_END')
    checks['all_body_checks_valid'] = all(q['body'] < 100 for q in rows if q['kind'] == 'AFTER_MODEL_TICK')
    checks['all_work_caps'] = all(r['cost'][k] <= cap for k, cap in c['caps'].items())
    checks['force_accounting'] = r['cost']['external_force'] == 4 * 906 and r['cost']['internal_force'] == 4 * 888 and r['cost']['total_force'] == 7176
    checks['geometry_accounting'] = sum(v for k, v in r['cost'].items() if k.startswith('geometry_')) == r['cost']['geometry'] == 2641
    checks['zero_forbidden_work'] = all(r[k] == 0 for k in ['native', 'worlds', 'resets', 'actions', 'solver', 'FD', 'new_seed', 'HOLDOUT', 'SEALED'])
    checks['ledger_unchanged'] = r['research_remaining'] == 22211 and r['reserve'] == 84000 and r['reserve_used'] == 0
    checks['core_limits_and_scoped_conclusion'] = r['core']['CPU_s'] < 30 and 5 <= r['core']['wall_s'] < 45 and r['status'] == 'PARITY_VALID_COMPONENT_EXCEEDS5S' and not r['pixel_act_promotion']
    audit_cpu = time.process_time() - CPU
    audit_wall = time.perf_counter() - WALL
    total = {k: closed['final_total'][k] + v for k, v in [('CPU_s', audit_cpu), ('wall_s', audit_wall)]}
    prep = {k: total[k] - r['core'][k] for k in total}
    checks['total_and_preparation_audit_caps'] = total['CPU_s'] < 90 and total['wall_s'] < 120 and prep['CPU_s'] < 60 and prep['wall_s'] < 75
    result = dict(study=600, status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILURE', checks=checks,
                  diagnostic_event_counts=dict(counts), audit_CPU_s=audit_cpu, audit_wall_s=audit_wall,
                  total_through_audit_before_summary=total, preparation_audit=prep,
                  final_summary_write_reserve_CPU_s=1, final_summary_write_reserve_wall_s=1,
                  result_sha256=sha(G / 'retry/timing600_result.json'), closed_sha256=sha(D / 'CLOSED-private.json'),
                  chooser=0, model=0, native=0)
    (G / 'retry/timing600_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    assert all(checks.values())


if __name__ == '__main__':
    main()
