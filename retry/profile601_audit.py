"""Read saved evidence only; zero scientific evaluator imports or calls."""
import time
CPU = time.process_time()
WALL = time.perf_counter()
import hashlib
import json
import pstats
from pathlib import Path

G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response601-private')


def read(p):
    return json.loads(p.read_text())


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    c = read(G / 'retry/profile601_contract.json')
    opt = read(G / 'retry/profile601_optimized_contract.json')
    results = {phase: read(G / f'retry/profile601_{phase}_result.json') for phase in ['profile', 'optimized']}
    checks = {}
    checks['runner_frozen'] = sha(G / 'retry/profile601.py') == c['runner_sha256']
    checks['one_candidate_frozen'] = sha(G / 'retry/reuse601.py') == opt['candidate_sha256']
    checks['profile_precedes_candidate_freeze'] = sha(G / 'retry/profile601_profile_result.json') == opt['profile_result_sha256']
    checks['candidate_freeze_links_main_contract'] = sha(G / 'retry/profile601_contract.json') == opt['main_contract_sha256']
    checks['all_pure_checks_pass'] = all(read(G / f'retry/profile601_{phase}_tests.json')['passed'] for phase in results)
    checks['tests_pinned'] = sha(G / 'retry/profile601_profile_tests.json') == c['pure_tests_sha256'] and sha(G / 'retry/profile601_optimized_tests.json') == opt['tests_sha256']
    checks['same_input_pinned'] = sha(Path('/workspace/haic-response599-private/proposed-timing-input-private.json')) == c['input_sha256']
    checks['source600_pinned'] = sha(G / 'retry/timing600_contract.json') == c['baseline600_contract_sha256'] and sha(Path('/workspace/haic-response600-private/deferred-diagnostics-private.json')) == c['baseline600_raw_sha256']
    times = dict(CPU_s=0., wall_s=0.)
    costs = {k: 0 for k in c['caps']}
    for phase, r in results.items():
        closed = read(D / f'{phase}-CLOSED-private.json')
        checks[phase + '_closed_result_pinned'] = closed['result_sha256'] == sha(G / f'retry/profile601_{phase}_result.json')
        checks[phase + '_one_call'] = r['chooser_calls'] == closed['chooser_calls'] == read(D / f'{phase}-CALL-private.json')['chooser_calls'] == 1
        checks[phase + '_private_evidence_pinned'] = all(sha(D / p) == h for p, h in r['private_sha256'].items())
        checks[phase + '_all_parity'] = all(r['parity'].values())
        checks[phase + '_no_forbidden_work'] = all(r[k] == 0 for k in ['native', 'worlds', 'resets', 'actions', 'solver', 'FD', 'new_seed', 'HOLDOUT', 'SEALED'])
        checks[phase + '_ledger_and_promotion'] = r['research_remaining'] == 22211 and r['reserve'] == 84000 and r['reserve_used'] == 0 and not r['pixel_act_promotion'] and not r['lap_gain_claim']
        checks[phase + '_registered_before_call'] = read(D / f'{phase}-REGISTERED-private.json')['contract_sha256'] == sha(G / 'retry/profile601_contract.json')
        for k in times:
            times[k] += closed['time'][k]
        for k in costs:
            costs[k] += r['cost'][k]
    checks['byte_identical600_all_raw_diagnostics'] = sha(D / 'profile-diagnostics-private.json') == sha(D / 'optimized-diagnostics-private.json') == c['baseline600_raw_sha256']
    checks['byte_identical_full_raw_force_outputs'] = sha(D / 'profile-raw-kernels-private.json') == sha(D / 'optimized-raw-kernels-private.json')
    checks['two_closed_chooser_calls_only'] = len(list(D.glob('*-CALL-private.json'))) == 2
    checks['aggregate_work_caps'] = all(costs[k] <= c['caps'][k] for k in costs)
    checks['logical_geometry_fully_charged'] = results['optimized']['cost']['geometry'] == 2641 and results['optimized']['planner_cost']['geometry_checks'] == 919
    cache = results['optimized']['cache_work']
    checks['memo_accounting'] = cache['hits'] == 145 and cache['misses'] == cache['entries'] == 774 and cache['logical_queries'] == 919
    checks['valid_optimization_scoped_above5s'] = results['optimized']['optimization_adopted'] and results['optimized']['core']['wall_s'] >= 5
    stats = pstats.Stats(str(D / 'profile-private.pstats'))
    detail = []
    for (filename, line, name), (cc, nc, own, cum, callers) in stats.stats.items():
        if (Path(filename).name == 'structure537_control.py' and name == 'result') or (Path(filename).name == 'dataclasses.py' and name == 'asdict') or (Path(filename).name == 'brake502_response.py' and name == 'wheel_response'):
            detail.append(dict(file=Path(filename).name, name=name, calls=nc, self_s=own, cumulative_s=cum))
    audit_cpu = time.process_time() - CPU
    audit_wall = time.perf_counter() - WALL
    times['CPU_s'] += audit_cpu
    times['wall_s'] += audit_wall
    checks['total_time_caps_with5s_summary_reserve'] = times['CPU_s'] + 5 < 240 and times['wall_s'] + 5 < 300
    baseline = read(G / 'retry/timing600_result.json')['core']
    normal = results['optimized']['core']
    result = dict(study=601, status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILURE',
                  checks=checks, chooser_calls=2, aggregate_cost=costs,
                  time_through_read_only_audit=times, audit_CPU_s=audit_cpu, audit_wall_s=audit_wall,
                  summary_write_reserve_CPU_s=5, summary_write_reserve_wall_s=5,
                  profiled_function_details=detail,
                  profiled_unallocated_self_time_gap_s=results['profile']['core']['wall_s'] - results['profile']['profile']['categories_sum_s'],
                  comparison=dict(normal_wall_reduction_s=baseline['wall_s'] - normal['wall_s'],
                                  normal_wall_reduction_fraction=1 - normal['wall_s'] / baseline['wall_s'],
                                  reused_margin_fraction=cache['hits'] / cache['logical_queries'],
                                  scope='One600normal vs one601normal saved-input sample.601also retains raw kernel returns and has aggregate guard bookkeeping; no repeated paired latency estimate. Profiled21.46s is excluded from speedup comparison.'),
                  scientific_evaluations_in_audit=0)
    (G / 'retry/profile601_audit.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    assert all(checks.values())


if __name__ == '__main__':
    main()
