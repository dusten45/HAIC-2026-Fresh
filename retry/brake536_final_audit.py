"""Read saved 536 records only; never import a controller or simulator."""
import hashlib
import json
import signal
import time
from pathlib import Path

G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response536-private')


def run():
    cpu, wall = time.process_time(), time.perf_counter()
    def cap(*args):
        raise RuntimeError('STATIC_AUDIT_CAP')
    signal.signal(signal.SIGPROF, cap)
    signal.signal(signal.SIGALRM, cap)
    signal.setitimer(signal.ITIMER_PROF, 30)
    signal.setitimer(signal.ITIMER_REAL, 60)
    read = lambda p: json.loads(Path(p).read_text())
    sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
    c = read(G / 'retry/brake536_contract.json')
    assert all(sha(G / p) == h for p, h in c['source_sha256'].items())
    assert all(sha(p) == h for p, h in c['private_inputs_sha256'].items())
    phases = [read(G / f'retry/brake536_{p}_result.json') for p in ('pilot', 'cold', 'carry')]
    assert all(r['passed'] for r in phases)
    n = read(G / 'retry/brake536_native_result.json')
    charges = sorted(D.glob('charge-*.json'))
    assert len(charges) == n['counts']['actions']
    for i, p in enumerate(charges, 1):
        q = read(p)
        assert q['attempted_actual_actions'] == i
        assert q['research_remaining'] == c['research_start'] - i
        assert q['reserve_used'] == 0
    assert n['research_remaining'] == 23893 - len(charges)
    assert n['reserve'] == 84000 and n['reserve_used'] == 0
    assert n['counts']['worlds'] == n['counts']['closed'] <= 2
    assert n['counts']['resets'] <= 2 and len(charges) <= 1000
    assert n['counts']['raw_attempts'] <= 4102
    exit_counts = read(D / 'native-exit-counters-private.json')
    assert exit_counts['counts'] == n['counts']
    assert exit_counts['model_ticks'] == n['native_model_integrator_ticks']
    assert exit_counts['explicit_force_evaluations'] == n['native_explicit_force_evaluations']
    raw = sorted(D.glob('raw-*.json'))
    assert len(raw) == n['counts']['raw_completed']
    raw_errors = sorted({e for p in raw for e in read(p)['errors']})
    final_certificates = 0
    for p in D.glob('action-candidate-*.json'):
        q = read(p)
        if q['record']['index'] <= 24:
            continue
        detail = q['governor_detail']
        assert detail['final_recertified']
        cert = next(x for x in detail['reports'] if x['mode'] == 'FINAL')
        assert cert['ok'] and cert['peak'] <= 1.0590000000000002
        assert cert['min_footprint_margin_m'] >= .5
        final_certificates += 1
    ticks = sum(r['model_integrator_ticks'] for r in phases)
    force = sum(r['explicit_force_evaluations'] for r in phases)
    geo = sum(r['planner_cost']['geometry_checks'] for r in phases)
    assert n['all_model_integrator_ticks'] == ticks + n['native_model_integrator_ticks'] <= 260000
    assert n['all_model_wheel_force_evaluations'] == force + n['native_explicit_force_evaluations'] <= 1300000
    assert n['all_geometry_checks'] == geo + n['native_geometry_checks'] <= 280000
    files = list(D.iterdir())
    out = dict(status='SAVED_RECORD_AUDIT_PASS', source_and_private_pins=True,
               native_counts=n['counts'], raw_guard_errors=raw_errors,
               candidate_fresh_certificates=final_certificates,
               research_remaining=n['research_remaining'], reserve=84000, reserve_used=0,
               private_files=len(files), private_bytes=sum(p.stat().st_size for p in files),
               new_simulation_actions=0, new_model_ticks=0,
               CPU_s=time.process_time()-cpu, wall_s=time.perf_counter()-wall)
    assert out['private_files'] <= 8192 and out['private_bytes'] <= 268435456
    signal.setitimer(signal.ITIMER_PROF, 0)
    signal.setitimer(signal.ITIMER_REAL, 0)
    with (G / 'retry/brake536_final_audit.json').open('x') as f:
        json.dump(out, f, indent=2)
        f.write('\n')
    print(json.dumps(out))


if __name__ == '__main__':
    run()
