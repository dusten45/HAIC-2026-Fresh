"""At most one profiled and one normal chooser, exact same saved hold148.

The optimization module is selected only after the single profile has finished.
"""
import time
BOOT_CPU = time.process_time()
BOOT_WALL = time.perf_counter()
import argparse
import cProfile
import datetime
import importlib
import json
import pstats
import signal
import subprocess
import traceback
from collections import Counter
from dataclasses import asdict, is_dataclass
from pathlib import Path
import retry.timing600 as base
from retry.clip561_core import atomic_write

G = base.G
D = Path('/workspace/haic-response601-private')
CAPS = dict(model_attempted=3072, model_completed=3072, external_force=12288,
            internal_force=12288, total_force=24576, geometry=10000)


def elapsed():
    return dict(CPU_s=time.process_time() - BOOT_CPU + 5,
                wall_s=time.perf_counter() - BOOT_WALL + 5)


def materialize(value):
    if is_dataclass(value):
        return materialize(asdict(value))
    if isinstance(value, base.DeferredDigest):
        return base.digest(value.value)
    if isinstance(value, dict):
        return {k: materialize(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [materialize(v) for v in value]
    return base.plain(value)


class Meter(base.Meter):
    def __init__(self, static, previous):
        super().__init__(static)
        self.previous = previous
        self.raw_kernels = []

    def guard(self, *args):
        t = elapsed()
        if t['CPU_s'] + self.previous.get('time', {}).get('CPU_s', 0) >= 235:
            raise base.old.CostStop('601_TOTAL_CPU_RESERVE5')
        if t['wall_s'] + self.previous.get('time', {}).get('wall_s', 0) >= 295:
            raise base.old.CostStop('601_TOTAL_WALL_RESERVE5')
        if datetime.datetime.now(datetime.timezone.utc) >= base.DEADLINE:
            raise base.old.CostStop('DEADLINE')

    def capacity(self, req):
        self.guard()
        for k, n in req.items():
            if k in CAPS and self.counts[k] + self.previous.get('cost', {}).get(k, 0) + n > CAPS[k]:
                raise base.old.CostStop('601_' + k)
            if k in base.CAPS and self.counts[k] + n > base.CAPS[k]:
                raise base.old.CostStop('601_PER_CALL_' + k)

    def add(self, k, n=1):
        self.capacity({k: n})
        self.counts[k] += n

    def kernel(self, key, fn, *args, **kwargs):
        result = super().kernel(key, fn, *args, **kwargs)
        # Frozen dataclass/tuple/dict results are never changed by callers;
        # materialization happens after the timed boundary in both arms.
        self.raw_kernels.append((key, result))
        return result


def category(filename, name):
    leaf = Path(filename).name
    if leaf in ('dataclasses.py', 'copy.py'):
        return 'state_copy_and_dataclass_allocation'
    if leaf in ('plan513_model.py', 'brake506_geometry.py', 'corner515_model.py',
                'brake508_corridor.py', 'brake510_common.py') or (leaf == 'lap518_control.py' and name in ('raw_projection', 'project', 'point_at', 'reference')):
        return 'geometry_and_path_queries'
    if leaf in ('brake502_response.py', 'brake504_planar.py', 'plan512_control.py',
                'closure524_control.py', 'speed516_control.py', 'late568_model.py', 'lap518_finish.py'):
        return 'physics_and_body'
    if leaf in ('timing600.py', 'profile601.py', 'cold598_support.py', 'feedback596_trace.py'):
        return 'instrumentation_identity_and_budget'
    if leaf in ('structure537_control.py', 'preview527_control.py', 'lap518_control.py', 'envelope500.py'):
        return 'policy_reports_and_admission'
    return 'other_including_builtins'


def profile_summary(profiler):
    stats = pstats.Stats(profiler)
    groups = Counter()
    functions = []
    for (filename, line, name), (cc, nc, own, cumulative, callers) in stats.stats.items():
        groups[category(filename, name)] += own
        functions.append(dict(file=Path(filename).name, line=line, name=name,
                              primitive_calls=cc, total_calls=nc,
                              self_s=own, cumulative_s=cumulative))
    return dict(exclusive_self_seconds_by_category=dict(groups),
                categories_sum_s=sum(groups.values()),
                top_self=sorted(functions, key=lambda q: -q['self_s'])[:20],
                top_cumulative=sorted(functions, key=lambda q: -q['cumulative_s'])[:20],
                scope='Single cProfile instrumented call. Times include profiler overhead and are not normal latency. Categories use function self time; builtins remain other, cumulative rows overlap.')


def run(phase):
    if phase == 'profile':
        D.mkdir(mode=0o700, exist_ok=False)
        previous = {}
    else:
        previous = json.loads((G / 'retry/profile601_profile_result.json').read_text())
        assert previous['status'] == 'EXACT_PROFILE_COMPLETED'
    # An existing start marker permanently prevents retry of either phase.
    atomic_write(D / f'{phase}-STARTED-private.json', dict(phase=phase, requested_chooser_calls=1))
    result = dict(study=601, phase=phase, chooser_calls=0, status='PREPARATION',
                  native=0, worlds=0, resets=0, actions=0, solver=0, FD=0,
                  new_seed=0, HOLDOUT=0, SEALED=0, research_remaining=22211,
                  reserve=84000, reserve_used=0, lap_gain_claim=False,
                  pixel_act_promotion=False, optimization_adopted=False)
    meter = None
    def interrupt(*args):
        raise base.old.CostStop('601_TOTAL_TIMER')
    signal.signal(signal.SIGPROF, interrupt)
    signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_PROF, max(.01, 235 - previous.get('time', {}).get('CPU_s', 0) - elapsed()['CPU_s']))
    signal.setitimer(signal.ITIMER_REAL, max(.01, 295 - previous.get('time', {}).get('wall_s', 0) - elapsed()['wall_s']))
    try:
        assert base.sha(base.INPUT) == base.INPUT_SHA
        packet = json.loads(base.INPUT.read_text())
        c598 = json.loads((G / 'retry/cold598_contract.json').read_text())
        c600 = json.loads((G / 'retry/timing600_contract.json').read_text())
        assert base.sha(G / 'retry/timing600.py') == c600['implementation_sha256']
        for p, h in c598['implementation_sha256'].items():
            assert base.sha(G / p) == h
        for p, h in [(base.old.INPUTS['static'], packet['roads_static_sha256']),
                     (base.old.INPUTS['candidate_paths'], packet['paths_sha256'])]:
            assert base.sha(p) == h
        static = json.loads(base.old.INPUTS['static'].read_text())
        paths = json.loads(base.old.INPUTS['candidate_paths'].read_text())
        root = base.load_root(dict(packet['root'], roads=static['root']['roads']))
        meter = Meter(static, previous)
        geometry = base.old.tracking.geometry_context(static, 5000)
        old_rows = json.loads((base.D / 'deferred-diagnostics-private.json').read_text())
        assert base.sha(base.D / 'deferred-diagnostics-private.json') == json.loads((G / 'retry/timing600_result.json').read_text())['private_sha256']['deferred-diagnostics-private.json']
        assert subprocess.check_output(['git', 'rev-parse', 'main'], cwd=G, text=True).strip() == 'dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
        assert not subprocess.check_output(['git', 'diff', '--name-only', 'main', '--', 'Participants'], cwd=G, text=True).strip()
        import retry.plan512_control as kernel
        assert kernel.MAX_MODEL_TICKS == 200000
        def forbidden(*args, **kwargs):
            raise AssertionError('NATIVE_FORBIDDEN')
        base.old.CarRacing.__init__ = base.old.CarRacing.reset = base.old.CarRacing.step = forbidden
        base.old.Car.__init__ = base.old.Car.step = forbidden
        contract_path = G / 'retry/profile601_contract.json'
        if phase == 'profile':
            tests = base.pure_checks(root, static)
            atomic_write(G / 'retry/profile601_profile_tests.json', tests)
            contract = dict(study=601, status='FROZEN_BEFORE_PROFILE', caps=CAPS,
                            time_caps=dict(total_CPU_s=240, total_wall_s=300, final_audit_reserve_s=5),
                            input_sha256=base.INPUT_SHA, runner_sha256=base.sha(Path(__file__)),
                            baseline600_contract_sha256=base.sha(G / 'retry/timing600_contract.json'),
                            baseline600_raw_sha256=base.sha(base.D / 'deferred-diagnostics-private.json'),
                            pure_tests_sha256=base.sha(G / 'retry/profile601_profile_tests.json'),
                            registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            deadline_utc=base.DEADLINE.isoformat(), chooser_calls_max=2,
                            selection_rule='After ONE profiled original chooser, select ONE largest repeated cost identified from source and exclusive/cumulative profile. One semantic-preserving reuse/deduplication implementation only. Pure immutable/no-history-leak tests before ONE normal optimized chooser. No tuning/retry/extra candidate or extra choose.',
                            boundary='Same600 core: original537choose with all original numeric/body/budget/Trial gates, deferred diagnostics. Both601calls additionally retain all external/internal wheel_response results in memory for exact comparison; no extra force evaluation. Profiler on only first call. Import/restore/JSON/fsync/audit outside core.',
                            parity='Same600 actionbytes/fullreport/trials/FINAL/model906/888/geometry2641 and all4538 materialized raw diagnostic events exact. Optimized additionally all7176 full wheel_response return tuples exact vs profiled original. Any mismatch=>reject optimization and stop.',
                            immutable_rule='No mutable cache entries, no trial/history leakage; fresh per-call cache context; all logical gates/query costs still charged even if a pure subcalculation is reused.',
                            kernel_hardcap=200000, choose_max_ticks=180000,
                            native_world_reset_actions_solver_FD_seed_HOLDOUT_SEALED=0,
                            research_remaining=22211, reserve=84000, reserve_used=0,
                            parent_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=G, text=True).strip())
            atomic_write(contract_path, contract)
        else:
            contract = json.loads(contract_path.read_text())
            assert base.sha(Path(__file__)) == contract['runner_sha256']
            candidate = importlib.import_module('retry.reuse601')
            tests, tests_geometry = candidate.pure_checks()
            # Synthetic geometry tests are explicitly charged to the aggregate.
            meter.counts['geometry'] += tests_geometry
            result['pure_geometry_queries'] = tests_geometry
            atomic_write(G / 'retry/profile601_optimized_tests.json', tests)
            frozen = dict(study=601, status='ONE_CANDIDATE_FROZEN_BEFORE_NORMAL_CHOOSE',
                          main_contract_sha256=base.sha(contract_path),
                          profile_result_sha256=base.sha(G / 'retry/profile601_profile_result.json'),
                          candidate_sha256=base.sha(G / 'retry/reuse601.py'),
                          tests_sha256=base.sha(G / 'retry/profile601_optimized_tests.json'),
                          chosen_cost=candidate.DESIGN,
                          registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
            atomic_write(G / 'retry/profile601_optimized_contract.json', frozen)
        atomic_write(D / f'{phase}-REGISTERED-private.json', dict(contract_sha256=base.sha(contract_path), input_sha256=base.INPUT_SHA, chooser_calls=0))
        meter.install_meters()
        cache = candidate.install() if phase == 'optimized' else None
        profiler = cProfile.Profile() if phase == 'profile' else None
        meter.guard()
        atomic_write(D / f'{phase}-CALL-private.json', dict(chooser_calls=1, input_sha256=base.INPUT_SHA))
        result['chooser_calls'] = 1
        start = (time.process_time(), time.perf_counter())
        if profiler:
            profiler.enable()
        try:
            action, report = base.old.tracking.choose(root, paths['candidate'], paths['backup'],
                packet['progress'], meter.model, meter.planner, 180000,
                history=tuple(packet['actual_running_history']), geometry=geometry)
        finally:
            if profiler:
                profiler.disable()
            result['core'] = dict(CPU_s=time.process_time() - start[0], wall_s=time.perf_counter() - start[1])
            if cache:
                result['cache_work'] = cache.statistics()
                cache.restore()
        output = dict(action_bits=None if action is None else action.tobytes().hex(), report=report)
        rows = materialize(meter.journal.rows)
        raw = materialize(meter.raw_kernels)
        atomic_write(D / f'{phase}-output-private.json', output)
        atomic_write(D / f'{phase}-diagnostics-private.json', rows)
        atomic_write(D / f'{phase}-raw-kernels-private.json', raw)
        pure_geom = result.get('pure_geometry_queries', 0)
        parity = dict(action_bytes=output['action_bits'] == packet['expected_action_bits'],
                      full_report=base.digest(report) == base.digest(packet['expected_certificate']),
                      all600_raw_events=base.digest(rows) == base.digest(old_rows),
                      model_attempts=meter.counts['model_attempted'] == 906,
                      model_completed=meter.counts['model_completed'] == 888,
                      force_external=meter.counts['external_force'] == 3624,
                      force_internal=meter.counts['internal_force'] == 3552,
                      geometry=meter.counts['geometry'] - pure_geom == 2641,
                      kernel_return_count=len(raw) == 7176,
                      passive_trial_reports=all(x['exact'] for x in meter.trial_summaries))
        if phase == 'optimized':
            parity['all_profiled_full_raw_forces'] = base.digest(raw) == base.digest(json.loads((D / 'profile-raw-kernels-private.json').read_text()))
        result['parity'] = parity
        if profiler:
            result['profile'] = profile_summary(profiler)
            profiler.dump_stats(str(D / 'profile-private.pstats'))
        result['status'] = ('EXACT_PROFILE_COMPLETED' if phase == 'profile' else 'EXACT_OPTIMIZATION_VALIDATED') if all(parity.values()) else 'PARITY_FAILED_OPTIMIZATION_REJECTED'
        result['optimization_adopted'] = phase == 'optimized' and all(parity.values())
        if phase == 'optimized' and result['optimization_adopted']:
            baseline = json.loads((G / 'retry/timing600_result.json').read_text())['core']
            result['single_sample_vs600'] = {k: dict(baseline=baseline[k], optimized=result['core'][k], speedup=baseline[k] / result['core'][k]) for k in baseline}
        assert base.sha(base.INPUT) == base.INPUT_SHA
        meter.guard()
    except BaseException as exc:
        result['status'] = 'FAILED_NO_RETRY'
        result['optimization_adopted'] = False
        result['error'] = type(exc).__name__ + ':' + str(exc)
        atomic_write(D / f'{phase}-error-private.json', dict(error=result['error'], traceback=traceback.format_exc()))
    finally:
        if meter:
            meter.restore()
            result['cost'] = dict(meter.counts)
            result['planner_cost'] = meter.planner
        result['time'] = elapsed()
        result['aggregate_cost'] = {k: result.get('cost', {}).get(k, 0) + previous.get('cost', {}).get(k, 0) for k in CAPS}
        result['aggregate_time'] = {k: result['time'][k] + previous.get('time', {}).get(k, 0) for k in result['time']}
        result['private_sha256'] = {p.name: base.sha(p) for p in D.glob(f'{phase}-*.json')}
        atomic_write(G / f'retry/profile601_{phase}_result.json', result)
        atomic_write(D / f'{phase}-CLOSED-private.json', dict(time=elapsed(), result_sha256=base.sha(G / f'retry/profile601_{phase}_result.json'), chooser_calls=result['chooser_calls']))
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', required=True, choices=['profile', 'optimized'])
    run(parser.parse_args().phase)
