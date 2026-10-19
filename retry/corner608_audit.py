"""Read-only frozen-source, durable-cost and outcome audit; no physics imports."""
import collections
import hashlib
import json
from pathlib import Path
import time

CPU = time.process_time()
G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response608-private')


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def digest(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'),
                                   allow_nan=False).encode()).hexdigest()


def main():
    r = read(D / 'as-executed-result-private.json')
    c = read(G / 'retry/corner608_contract.json')
    checks = {}
    checks['frozen_source'] = all(sha(G / p) == h for p, h in c['source_sha256'].items())
    checks['registered_contract'] = read(D / 'REGISTERED-private.json')['contract_sha256'] == sha(G / 'retry/corner608_contract.json')
    checks['closed_result'] = read(D / 'CLOSED-private.json')['result_sha256'] == sha(D / 'as-executed-result-private.json')
    published = read(G / 'retry/corner608_result.json')
    publication = read(D / 'PUBLICATION-private.json')
    checks['aggregate_only_publication'] = publication['public_sha256'] == sha(G / 'retry/corner608_result.json') and publication['original_sha256'] == sha(D / 'as-executed-result-private.json') and all(set(q) <= {'before_raw', 'after_raw', 'fraction', 'time_s', 'hold', 'eligible', 'whole_hold_safe'} for q in published['crossings'].values())
    checks['private_hashes'] = all(sha(D / p) == h for p, h in r['private_sha256'].items())
    checks['pure_stubs'] = read(G / 'retry/corner608_tests.json')['passed']
    checks['original_first_decision_and_grid_exact607'] = all(r.get(k, False) for k in ['first_original607_exact', 'first607_exact', 'first_grid_preflight_model0'])
    counts = collections.Counter()
    certificates = 0
    for p in sorted(D.glob('*-telemetry-private.json')):
        t = read(p)
        for e in t['events']:
            counts['model_attempted'] += e['kind'] == 'BEFORE_MODEL_FORCE'
            counts['model_completed'] += e['kind'] == 'AFTER_MODEL_TICK'
            certificates += e['kind'] == 'TRACKING_TRIAL_START'
        counts.update(w[0] for w in t['wheel_results'])
    checks['primitive_costs'] = all(counts[k] == r['cost'][k] for k in counts)
    checks['force_totals'] = counts['external_force'] + counts['internal_force'] == r['cost']['total_force']
    checks['one_original_per_decision'] = r['original_choose_calls'] == r['cost']['chooser_calls']
    pair_count = 0
    pair_safe = True
    for p in sorted(D.glob('pairs-*-private.json')):
        pairs = read(p)
        pair_count += len(pairs)
        pair_safe &= len(pairs) <= 42 and len({q['action_bits'] for q in pairs}) == len(pairs)
        pair_safe &= [q['index'] for q in pairs] == list(range(len(pairs)))
        for row in ['base', 'shifted']:
            grid = [q['u'] for q in pairs if row in q['rows']]
            pair_safe &= grid == sorted(set(grid), reverse=True) and len(grid) <= 21
        detail = read(D / (p.name.replace('pairs-', 'decision-').replace('-private.json', '-telemetry-private.json')))['detail']
        chosen = next(q for q in pairs if q['action_bits'] == detail['action_bits'])
        pair_safe &= chosen['report']['ok'] and detail['final']['ok']
    checks['fixed_grid_unique_order_and_selected_safe'] = bool(pair_safe)
    checks['fresh_FINAL_per_batch'] = r['fresh_pair_FINAL'] == r['joint_batches'] == len(list(D.glob('pairs-*-private.json')))
    head = '0' * 64
    kinds = collections.Counter()
    for n, line in enumerate((D / 'applied-journal-private.jsonl').read_text().splitlines()):
        e = json.loads(line)
        h = e.pop('sha256')
        assert e['previous'] == head and e['sequence'] == n and digest(e) == h
        head = h
        kinds[e['kind']] += 1
    checks['durable_journal_chain'] = True
    checks['remaining_grid_and_FINAL_reservations'] = kinds['PAIR_REMAINDER_RESERVE'] == pair_count + r['fresh_pair_FINAL']
    candidate = read(D / 'candidate-private.json')
    checks['candidate_raw_count'] = len(candidate['rows']) == r['applied_candidate_raw']
    checks['completed_rows_strict'] = all(not q['pre_failure'] and not q['post_failure'] for q in candidate['rows']) if not r['failure'] else True
    checks['positive_safe_only_replay'] = (r['replay'] is None or (r.get('s400_gain_s', 0) > 0 and r['replay']['exact']))
    checks['caps_and_kernel'] = all(r['cost'][k] <= v for k, v in c['caps'].items()) and r['kernel_hardcap'] == 200000
    checks['no_forbidden_work'] = all(r[k] == 0 for k in ['native', 'worlds', 'resets', 'actions', 'new_seed', 'carry', 'HOLDOUT', 'SEALED', 'FD', 'solver'])
    checks['local_scope_ledger'] = not r['whole_lap_claim'] and not r['native_admission'] and r['research_remaining'] == 22211 and r['reserve_used'] == 0
    elapsed = time.time() - read(D / 'TASK_STARTED-private.json')['start_epoch']
    cpu = time.process_time() - CPU
    checks['whole_task_time_cleanup_reserved'] = elapsed + 120 < 4500 and r['time']['CPU_s'] + cpu + 60 < 3000
    out = dict(study=608, status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILURE',
               checks=checks, certificates=certificates, primitive_counts=dict(counts),
               durable_events=dict(kinds), pairs=pair_count, new_evaluations=0,
               audit_CPU_s=cpu, whole_task_wall_s=elapsed, result_sha256=sha(G / 'retry/corner608_result.json'))
    (G / 'retry/corner608_audit.json').write_text(json.dumps(out, indent=2) + '\n')
    print(json.dumps(out, indent=2))
    assert all(checks.values())


if __name__ == '__main__':
    main()
