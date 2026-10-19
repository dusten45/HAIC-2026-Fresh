"""602: one prepared-segment candidate, saved-value tests, one timed choose."""
import time
BOOT_CPU = time.process_time()
BOOT_WALL = time.perf_counter()
import datetime
import json
import signal
import subprocess
import traceback
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import retry.profile601 as previous
import retry.reuse601 as reuse
import retry.segments602 as candidate
from retry.clip561_core import atomic_write

base = previous.base
G = base.G
D = Path('/workspace/haic-response602-private')
CAPS = dict(model_attempted=1536, model_completed=1536, external_force=6144,
            internal_force=6144, total_force=12288, geometry=15000)
IMPORT_CPU = time.process_time() - BOOT_CPU
IMPORT_WALL = time.perf_counter() - BOOT_WALL


def elapsed():
    return dict(CPU_s=time.process_time() - BOOT_CPU + 5,
                wall_s=time.perf_counter() - BOOT_WALL + 5)


class Meter(previous.Meter):
    def guard(self, *args):
        t = elapsed()
        if t['CPU_s'] >= 235 or t['wall_s'] >= 295:
            raise base.old.CostStop('602_TOTAL_RESERVE5')
        if datetime.datetime.now(datetime.timezone.utc) >= base.DEADLINE:
            raise base.old.CostStop('DEADLINE')

    def capacity(self, req):
        self.guard()
        for k, n in req.items():
            if k in CAPS and self.counts[k] + n > CAPS[k]:
                raise base.old.CostStop('602_' + k)


def restore_cases(rows, packet, static):
    """Saved baseline only: 773 distinct post-root geometries + initial root.

    Zero-tick trial reports contain exactly the initial check's margin, before
    any tick, so no additional baseline evaluator call is necessary.
    """
    initial = [q['original']['min_footprint_margin_m'] for q in rows
               if q['kind'] == 'TRACKING_TRIAL_END' and q['original']['model_ticks'] == 0]
    assert initial and all(candidate.same(v, initial[0]) for v in initial)
    root = base.load_root(dict(packet['root'], roads=static['root']['roads']))
    cases = {reuse.geometry_key(root): (root, initial[0], 'ZERO_TICK_INITIAL_REPORT')}
    last = None
    for q in rows:
        if q['kind'] == 'AFTER_MODEL_TICK':
            last = q
        elif q['kind'] == 'SOURCE_GEOMETRY_DIAGNOSTIC':
            assert last is not None and last['root_sha256'] == q['root_sha256']
            r = base.load_root(dict(last['root'], roads=static['root']['roads']))
            key = reuse.geometry_key(r)
            if key in cases:
                assert candidate.same(cases[key][1], q['footprint'])
            else:
                cases[key] = (r, q['footprint'], 'SAVED_POST_TICK_FOOTPRINT')
    assert len(cases) == 774
    return root, list(cases.values())


def main():
    D.mkdir(mode=0o700, exist_ok=False)
    result = dict(study=602, chooser_calls=0, status='PREPARATION',
                  native=0, worlds=0, resets=0, actions=0, solver=0, FD=0,
                  new_seed=0, HOLDOUT=0, SEALED=0, research_remaining=22211,
                  reserve=84000, reserve_used=0, optimization_adopted=False,
                  lap_gain_claim=False, pixel_act_promotion=False,
                  stages=dict(imports=dict(CPU_s=IMPORT_CPU, wall_s=IMPORT_WALL)),
                  conservative_preparation_charge_s=5)
    meter = cache = road = None
    @contextmanager
    def stage(name):
        t = (time.process_time(), time.perf_counter())
        try:
            yield
        finally:
            result['stages'][name] = dict(CPU_s=time.process_time() - t[0], wall_s=time.perf_counter() - t[1])
    def interrupt(*args):
        raise base.old.CostStop('602_TOTAL_TIMER')
    signal.signal(signal.SIGPROF, interrupt)
    signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_PROF, max(.01, 235 - elapsed()['CPU_s']))
    signal.setitimer(signal.ITIMER_REAL, max(.01, 295 - elapsed()['wall_s']))
    try:
        with stage('input_restore_saved_cases_and_pins'):
            assert base.sha(base.INPUT) == base.INPUT_SHA
            packet = json.loads(base.INPUT.read_text())
            c598 = json.loads((G / 'retry/cold598_contract.json').read_text())
            c601 = json.loads((G / 'retry/profile601_optimized_contract.json').read_text())
            assert base.sha(G / 'retry/reuse601.py') == c601['candidate_sha256']
            for p, h in c598['implementation_sha256'].items():
                assert base.sha(G / p) == h
            assert base.sha(base.old.INPUTS['static']) == packet['roads_static_sha256']
            assert base.sha(base.old.INPUTS['candidate_paths']) == packet['paths_sha256']
            static = json.loads(base.old.INPUTS['static'].read_text())
            paths = json.loads(base.old.INPUTS['candidate_paths'].read_text())
            old_result = json.loads((G / 'retry/profile601_optimized_result.json').read_text())
            for name in ['optimized-diagnostics-private.json', 'optimized-raw-kernels-private.json']:
                assert base.sha(previous.D / name) == old_result['private_sha256'][name]
            old_rows = json.loads((previous.D / 'optimized-diagnostics-private.json').read_text())
            root, cases = restore_cases(old_rows, packet, static)
            meter = Meter(static, {})
            geometry = base.old.tracking.geometry_context(static, 5000)
            assert subprocess.check_output(['git', 'rev-parse', 'main'], cwd=G, text=True).strip() == 'dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
            assert not subprocess.check_output(['git', 'diff', '--name-only', 'main', '--', 'Participants'], cwd=G, text=True).strip()
            import retry.plan512_control as kernel
            assert kernel.MAX_MODEL_TICKS == 200000
            def forbidden(*a, **kw):
                raise AssertionError('602_NATIVE_FORBIDDEN')
            base.old.CarRacing.__init__ = base.old.CarRacing.reset = base.old.CarRacing.step = forbidden
            base.old.Car.__init__ = base.old.Car.step = forbidden
        contract = dict(study=602, status='ONE_IMPLEMENTATION_FROZEN_BEFORE_ALL_EVALUATORS',
            registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), deadline_utc=base.DEADLINE.isoformat(),
            implementation_sha256={p: base.sha(G / p) for p in ['retry/verify602.py', 'retry/segments602.py']},
            input_sha256=base.INPUT_SHA, source601_sha256=base.sha(G / 'retry/profile601_optimized_result.json'),
            baseline_raw_sha256=base.sha(previous.D / 'optimized-diagnostics-private.json'),
            baseline_wheel_sha256=base.sha(previous.D / 'optimized-raw-kernels-private.json'),
            caps=CAPS, time_caps=dict(CPU_s=240, wall_s=300, final_audit_reserve_s=5), chooser_calls=1,
            kernel_hardcap=200000, choose_max_ticks=180000,
            candidate='Prepare directed segment dx/dy/d with original arithmetic once per immutable road edge and once per current vehicle polygon edge. Reuse these operands and edge sequences in original SAT/point-segment/min order. No new prune, approximation or point query omission. Keep601exactmarginmemo unchanged.',
            semantics='Same original SAT positive0 for no separation; exact original ordered point-distance min otherwise. Preserve both directions, d==0 branch, t=max(0,min(1,dot/d)), hypot subtraction order. Road covered=all(any(inclusiveAABB and inside(mincross>=0 or maxcross<=0))). Signed distance positive inside, negative outside including -0. Ordered min begins+inf and keeps first equal value. Original lower>=distance skip and segment order unchanged; no new segment exclusions.',
            saved_comparison='774distinctgeometryinputs;773fromsavedpostfootprints,initial1fromninezero-tickreports. No new old-baseline query. Every new candidate fullmargin and both synthetic evaluators charged to geometry before dispatch; nested point-segment is included in its geometry pack as601.',
            parity='Exact binary64margin774; same600/601actionbytes/fullreports/trials/FINAL/all4538rawdiagnostics/all7176wheelreturns/model906/888 and logicalgeometry2641. Mismatch=>reject and stop without implementation change or choose retry.',
            boundary='ONE normal choose only after pure+saved gates. Start/end core immediately around original537choose with601meter/fullwheelcapture and unchanged601memo. All numeric/body/cost gates retained. Imports/input restoration/context preparation/tests/saved comparisons/JSON/fsync/audit separately measured outside core.',
            stop='First mismatch/domain/integrity/IO/cost/deadline failure ends study. No extra candidate or retry. No native/world/reset/action/solver/FD/newseed/HOLDOUT/SEALED.',
            research_remaining=22211, reserve=84000, reserve_used=0,
            parent_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=G, text=True).strip())
        atomic_write(G / 'retry/segments602_contract.json', contract)
        atomic_write(D / 'REGISTERED-private.json', dict(contract_sha256=base.sha(G / 'retry/segments602_contract.json'), chooser_calls=0))
        def charge(n=1):
            meter.capacity(dict(geometry=n)); meter.add('geometry', n)
        with stage('pure_synthetic_tests'):
            before = meter.counts['geometry']
            tests = candidate.pure_checks(charge)
            memo_tests, _ = reuse.pure_checks()
            tests['unchanged601memo_tests'] = memo_tests
            tests['charged_geometry'] = meter.counts['geometry'] - before
            atomic_write(G / 'retry/segments602_tests.json', tests)
        # Prepare one immutable context for saved comparisons. No old evaluator.
        with stage('saved_comparison_context_preparation'):
            context = candidate.Road(static['roads'], meter.source_index, static['boundary'], meter.source_edges)
            obstacles = reuse.freeze(static['obstacles'])
        with stage('saved774_candidate_evaluations'):
            observed = []
            with patch.object(candidate.full, 'road_margin', context):
                for r, expected, source in cases:
                    charge()
                    actual = candidate.full.margin(r, context.args[0], context.args[1], context.args[2], context.args[3], obstacles)
                    observed.append(dict(root=base.Support.short(r), expected=expected, actual=actual, source=source, exact=candidate.same(expected, actual)))
                    if not observed[-1]['exact']:
                        atomic_write(D / 'first-saved-mismatch-private.json', observed[-1])
                        raise AssertionError('SAVED_MARGIN_NOT_BIT_EXACT')
            result['saved_comparison'] = dict(distinct_inputs=774, exact=all(q['exact'] for q in observed),
                baseline_reused=774, new_baseline_queries=0, new_candidate_queries=774,
                initial_baseline='CONSISTENT_ZERO_TICK_REPORTS', prepared_road_calls=context.margin_calls,
                polygon_segment_pairs=context.segment_pairs)
        with stage('saved_comparison_JSON_fsync'):
            atomic_write(D / 'saved774-comparison-private.json', observed)
        result['pre_choose_geometry'] = meter.counts['geometry']
        with stage('normal_context_preparation'):
            meter.install_meters()
            cache = reuse.install()
            road = candidate.Road(*cache.args[:4], already_frozen=True)
            original_road = candidate.full.road_margin
            candidate.full.road_margin = road
        atomic_write(D / 'CALL-private.json', dict(chooser_calls=1, contract_sha256=base.sha(G / 'retry/segments602_contract.json'), tests_sha256=base.sha(G / 'retry/segments602_tests.json'), saved_exact=True))
        result['chooser_calls'] = 1
        try:
            with stage('normal_core'):
                action, report = base.old.tracking.choose(root, paths['candidate'], paths['backup'], packet['progress'],
                    meter.model, meter.planner, 180000, history=tuple(packet['actual_running_history']), geometry=geometry)
        finally:
            candidate.full.road_margin = original_road
            result['memo'] = cache.statistics()
            result['prepared_road'] = dict(margin_calls=road.margin_calls, polygon_segment_pairs=road.segment_pairs,
                                           immutable_prepared_boundary_segments=len(road.prepared))
            cache.restore(); cache = None
        with stage('result_materialization_JSON_fsync'):
            output = dict(action_bits=action.tobytes().hex() if action is not None else None, report=report)
            rows = previous.materialize(meter.journal.rows)
            raw = previous.materialize(meter.raw_kernels)
            atomic_write(D / 'output-private.json', output)
            atomic_write(D / 'diagnostics-private.json', rows)
            atomic_write(D / 'wheel-private.json', raw)
        with stage('exact_parity_audit'):
            parity = dict(action_bytes=output['action_bits'] == packet['expected_action_bits'],
                whole_report=base.digest(report) == base.digest(packet['expected_certificate']),
                all600_601_raw=base.sha(D / 'diagnostics-private.json') == contract['baseline_raw_sha256'],
                all601_wheels=base.sha(D / 'wheel-private.json') == contract['baseline_wheel_sha256'],
                model_attempted=meter.counts['model_attempted'] == 906,
                model_completed=meter.counts['model_completed'] == 888,
                external_force=meter.counts['external_force'] == 3624,
                internal_force=meter.counts['internal_force'] == 3552,
                normal_geometry=meter.counts['geometry'] - result['pre_choose_geometry'] == 2641,
                memo_unchanged=result['memo']['hits'] == 145 and result['memo']['misses'] == 774,
                passive_trial_reports=all(q['exact'] for q in meter.trial_summaries),
                all_saved_margins=result['saved_comparison']['exact'],
                code_pins=all(base.sha(G / p) == h for p, h in contract['implementation_sha256'].items()))
            result['parity'] = parity
            result['optimization_adopted'] = all(parity.values())
            result['status'] = 'EXACT_PREPARED_SEGMENTS_VALIDATED' if result['optimization_adopted'] else 'PARITY_FAILED_OPTIMIZATION_REJECTED'
            result['single_sample_comparison'] = dict(baseline601=old_result['core'], normal602=result['stages']['normal_core'], scope='One normal sample each; no repeated paired estimate and no end-to-end Agent.act claim.')
            meter.guard()
    except BaseException as exc:
        result['status'] = 'FAILED_NO_RETRY'
        result['optimization_adopted'] = False
        result['error'] = type(exc).__name__ + ':' + str(exc)
        atomic_write(D / 'error-private.json', dict(error=result['error'], traceback=traceback.format_exc()))
    finally:
        if cache:
            cache.restore()
        if meter:
            meter.restore()
            result['cost'] = dict(meter.counts)
            result['planner_cost'] = meter.planner
        result['time'] = elapsed()
        result['private_sha256'] = {p.name: base.sha(p) for p in D.glob('*.json')}
        atomic_write(G / 'retry/segments602_result.json', result)
        atomic_write(D / 'CLOSED-private.json', dict(time=elapsed(), chooser_calls=result['chooser_calls'], result_sha256=base.sha(G / 'retry/segments602_result.json')))
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
