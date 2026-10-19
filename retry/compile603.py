"""Single installed-GCC candidate, no installation, one allowed chooser."""
import time
import resource
BOOT_CPU = time.process_time()
BOOT_WALL = time.perf_counter()
import datetime
import importlib.util
import json
import math
import os
import re
import signal
import subprocess
import sys
import sysconfig
import traceback
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import retry.verify602 as prior
import retry.segments602 as geometry
from retry.clip561_core import atomic_write

base = prior.base
G = base.G
D = Path('/workspace/haic-response603-private')
CAPS = dict(model_attempted=1536, model_completed=1536, external_force=6144,
            internal_force=6144, total_force=12288, geometry=15000)
FLAGS = ['-O2', '-std=c11', '-fPIC', '-shared', '-fno-fast-math',
         '-fno-unsafe-math-optimizations', '-fno-associative-math', '-ffp-contract=off',
         '-fexcess-precision=standard', '-frounding-math', '-ftrapping-math',
         '-fno-tree-vectorize', '-fno-tree-slp-vectorize', '-fno-lto',
         '-mfpmath=sse', '-msse2', '-fno-builtin']


def child_cpu():
    q = resource.getrusage(resource.RUSAGE_CHILDREN)
    return q.ru_utime + q.ru_stime


def cpu():
    return time.process_time() + child_cpu()


IMPORT_CPU = cpu() - BOOT_CPU
IMPORT_WALL = time.perf_counter() - BOOT_WALL


def elapsed():
    return dict(CPU_s=cpu() - BOOT_CPU + 5, wall_s=time.perf_counter() - BOOT_WALL + 5)


class Meter(prior.Meter):
    def guard(self, *args):
        t = elapsed()
        if t['CPU_s'] >= 295 or t['wall_s'] >= 415:
            raise base.old.CostStop('603_TOTAL_RESERVE5')
        if datetime.datetime.now(datetime.timezone.utc) >= base.DEADLINE:
            raise base.old.CostStop('DEADLINE')


def main():
    D.mkdir(mode=0o700, exist_ok=False)
    result = dict(study=603, status='PREPARATION', chooser_calls=0, compilation_attempts=0,
                  native=0, worlds=0, resets=0, actions=0, solver=0, FD=0,
                  new_seed=0, HOLDOUT=0, SEALED=0, research_remaining=22211,
                  reserve=84000, reserve_used=0, optimization_adopted=False,
                  pixel_act_promotion=False, lap_gain_claim=False,
                  stages=dict(imports=dict(CPU_s=IMPORT_CPU, wall_s=IMPORT_WALL)),
                  conservative_preparation_charge_s=5)
    meter = cache = road = None
    @contextmanager
    def stage(name):
        start = (cpu(), time.perf_counter())
        try:
            yield
        finally:
            result['stages'][name] = dict(CPU_s=cpu() - start[0], wall_s=time.perf_counter() - start[1])
    def interrupt(*args):
        raise base.old.CostStop('603_TIMER')
    signal.signal(signal.SIGPROF, interrupt)
    signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_PROF, max(.01, 295 - elapsed()['CPU_s']))
    signal.setitimer(signal.ITIMER_REAL, max(.01, 415 - elapsed()['wall_s']))
    try:
        with stage('input_restore_runtime_and_tool_pins'):
            cc = Path('/usr/bin/gcc').resolve()
            include = Path(sysconfig.get_path('include'))
            assert cc.exists() and (include / 'Python.h').exists()
            version = subprocess.check_output([str(cc), '--version'], text=True).splitlines()[0]
            assert '14.2.0' in version
            cc1 = Path(subprocess.check_output([str(cc), '-print-prog-name=cc1'], text=True).strip()).resolve()
            runtime_paths = [cc, cc1, Path('/usr/bin/as').resolve(), Path('/usr/bin/ld').resolve(),
                             Path('/usr/bin/objdump').resolve(), Path(sys.executable).resolve(),
                             Path('/usr/lib/x86_64-linux-gnu/libm.so.6').resolve(),
                             Path('/usr/lib/x86_64-linux-gnu/libc.so.6').resolve()]
            runtime_pins = {str(p): base.sha(p) for p in runtime_paths}
            header_pins = {str(p): base.sha(p) for p in include.rglob('*.h')}
            c602 = json.loads((G / 'retry/segments602_contract.json').read_text())
            for p, h in c602['implementation_sha256'].items():
                assert base.sha(G / p) == h
            c598 = json.loads((G / 'retry/cold598_contract.json').read_text())
            for p, h in c598['implementation_sha256'].items():
                assert base.sha(G / p) == h
            assert base.sha(base.INPUT) == base.INPUT_SHA
            packet = json.loads(base.INPUT.read_text())
            assert base.sha(base.old.INPUTS['static']) == packet['roads_static_sha256']
            assert base.sha(base.old.INPUTS['candidate_paths']) == packet['paths_sha256']
            static = json.loads(base.old.INPUTS['static'].read_text())
            paths = json.loads(base.old.INPUTS['candidate_paths'].read_text())
            old602 = json.loads((G / 'retry/segments602_result.json').read_text())
            assert base.sha(prior.D / 'saved774-comparison-private.json') == old602['private_sha256']['saved774-comparison-private.json']
            saved = json.loads((prior.D / 'saved774-comparison-private.json').read_text())
            assert len(saved) == 774 and all(q['exact'] for q in saved)
            root = base.load_root(dict(packet['root'], roads=static['root']['roads']))
            cases = [(base.load_root(dict(q['root'], roads=static['root']['roads'])), q['expected']) for q in saved]
            meter = Meter(static, {})
            geometry_context = base.old.tracking.geometry_context(static, 5000)
            assert subprocess.check_output(['git', 'rev-parse', 'main'], cwd=G, text=True).strip() == 'dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
            assert not subprocess.check_output(['git', 'diff', '--name-only', 'main', '--', 'Participants'], cwd=G, text=True).strip()
            import retry.plan512_control as kernel
            assert kernel.MAX_MODEL_TICKS == 200000
            def forbidden(*a, **kw):
                raise AssertionError('603_NATIVE_FORBIDDEN')
            base.old.CarRacing.__init__ = base.old.CarRacing.reset = base.old.CarRacing.step = forbidden
            base.old.Car.__init__ = base.old.Car.step = forbidden
        binary = D / ('_scalar603' + sysconfig.get_config_var('EXT_SUFFIX'))
        command = [str(cc), *FLAGS, '-I' + str(include), str(G / 'retry/scalar603.c'), '-lm', '-o', str(binary)]
        contract = dict(study=603, status='ONE_CANDIDATE_FROZEN_BEFORE_COMPILATION',
            registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), deadline_utc=base.DEADLINE.isoformat(),
            compiler_version=version, command=command, compiler_runtime_sha256=runtime_pins, python_header_sha256=header_pins,
            source_sha256={p: base.sha(G / p) for p in ['retry/scalar603.c', 'retry/compile603.py']},
            python=sys.version, input_sha256=base.INPUT_SHA,
            source602_contract_sha256=base.sha(G / 'retry/segments602_contract.json'),
            baseline_saved_sha256=base.sha(prior.D / 'saved774-comparison-private.json'),
            baseline_raw_sha256=old602['private_sha256']['diagnostics-private.json'],
            baseline_wheel_sha256=old602['private_sha256']['wheel-private.json'],
            caps=CAPS, time_caps=dict(CPU_s=300, wall_s=420, final_reserve_s=5, compiler_timeout_wall_s=60),
            compilation_attempts=1, chooser_calls=1, kernel_hardcap=200000, choose_max_ticks=180000,
            candidate='Only602query/distance loops become C scalar binary64.602Road/segment preparation/directed order/inside/signedmin/lowerpruning and601exactmemo remain unchanged. Use ordered compare-update min/max, no fmin/fmax, no new pruning. Each point hypot calls original CPython math.hypot with two binary64 Python floats; no replacement libm algorithm.',
            numeric_guards='binary64 sizeof8/mantissa53/exponent1024/FLT_EVAL_METHOD0 compile asserts; no fastmath/association/FMA/vectorization; SSE scalar; roundingmode FE_TONEAREST; originalmath.hypot object identity checked; reject FMA instructions in disassembly. Original division-d!=0 and typed float operands; preservefirstequal/NaN behavior and SATpositivezero.',
            gate='Run SAME60239syntheticcases by replacing only query/distance, charge78geometry. Then774savedfullmargins bitexact, no baseline reevaluation. First mismatch=>stop withnochanges/nochoose. Only thenONE normalchoose with exact all600~602 reports/raw/wheel/model906/888 parity. Compilation/context/IO separately measured; totalCPU includes subprocess children.',
            research_remaining=22211, reserve=84000, reserve_used=0,
            privacy='Csource/options/runtimehashes/aggregates public; binary/disassembly/compilerlog/rawinput/results private outsideGit.',
            parent_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=G, text=True).strip())
        atomic_write(G / 'retry/scalar603_contract.json', contract)
        atomic_write(D / 'REGISTERED-private.json', dict(contract_sha256=base.sha(G / 'retry/scalar603_contract.json'), chooser_calls=0))
        with stage('one_compilation_and_load'):
            result['compilation_attempts'] = 1
            proc = subprocess.run(command, capture_output=True, text=True, timeout=60)
            atomic_write(D / 'compiler-private.json', dict(command=command, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr))
            if proc.returncode:
                raise RuntimeError('COMPILER_FAILED_NO_RETRY')
            os.chmod(binary, 0o600)
            spec = importlib.util.spec_from_file_location('_scalar603', binary)
            extension = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(extension)
            env = extension.environment()
            assert env.pop('original_math_hypot') is math.hypot
            assert env['FLT_EVAL_METHOD'] == 0 and env['DBL_MANT_DIG'] == 53
            assert env['rounding_mode'] == env['FE_TONEAREST']
            result['compiled_environment'] = env
            result['binary_sha256'] = base.sha(binary)
        with stage('assembly_and_runtime_audit'):
            assembly = subprocess.check_output(['/usr/bin/objdump', '-d', str(binary)], text=True)
            (D / 'assembly-private.txt').write_text(assembly)
            fma = re.findall(r'\b(?:vfmadd\w*|vfmsub\w*|vfnmadd\w*|vfnmsub\w*|fmadd\w*)\b', assembly)
            assert not fma
            result['assembly_audit'] = dict(FMA_instructions=0, disassembly_sha256=base.sha(D / 'assembly-private.txt'))
            assert all(base.sha(Path(p)) == h for p, h in runtime_pins.items())
        def charge(n=1):
            meter.capacity(dict(geometry=n)); meter.add('geometry', n)
        with stage('same602_synthetic_compiled_checks'):
            before = meter.counts['geometry']
            with patch.object(geometry, 'query', extension.query), patch.object(geometry, 'distance', extension.distance):
                tests = geometry.pure_checks(charge)
            memo_tests, _ = prior.reuse.pure_checks()
            tests['unchanged601memo_tests'] = memo_tests
            tests['charged_geometry'] = meter.counts['geometry'] - before
            atomic_write(G / 'retry/scalar603_tests.json', tests)
        with stage('saved_context_preparation'):
            road_saved = geometry.Road(static['roads'], meter.source_index, static['boundary'], meter.source_edges)
            obstacles = prior.reuse.freeze(static['obstacles'])
        with stage('saved774_compiled_evaluations'):
            comparison = []
            with patch.object(geometry, 'distance', extension.distance), patch.object(geometry.full, 'road_margin', road_saved):
                for r, expected in cases:
                    charge()
                    actual = geometry.full.margin(r, *road_saved.args, obstacles)
                    exact = geometry.same(expected, actual)
                    comparison.append(dict(expected=expected, actual=actual, exact=exact))
                    if not exact:
                        atomic_write(D / 'first-mismatch-private.json', dict(root=base.Support.short(r), expected=expected, actual=actual))
                        raise AssertionError('603_SAVED_MARGIN_NOT_BIT_EXACT_NO_RETRY')
            result['saved_comparison'] = dict(inputs=774, exact=all(q['exact'] for q in comparison), new_compiled_queries=774, new_baseline_queries=0)
        with stage('saved_comparison_JSON_fsync'):
            atomic_write(D / 'saved774-private.json', comparison)
        result['pre_choose_geometry'] = meter.counts['geometry']
        with stage('normal_context_preparation'):
            meter.install_meters()
            cache = prior.reuse.install()
            road = geometry.Road(*cache.args[:4], already_frozen=True)
        atomic_write(D / 'CALL-private.json', dict(chooser_calls=1, contract_sha256=base.sha(G / 'retry/scalar603_contract.json'), tests_sha256=base.sha(G / 'retry/scalar603_tests.json'), binary_sha256=base.sha(binary), saved_exact=True))
        result['chooser_calls'] = 1
        try:
            with patch.object(geometry, 'distance', extension.distance), patch.object(geometry.full, 'road_margin', road):
                with stage('normal_core'):
                    action, report = base.old.tracking.choose(root, paths['candidate'], paths['backup'], packet['progress'],
                        meter.model, meter.planner, 180000, history=tuple(packet['actual_running_history']), geometry=geometry_context)
        finally:
            result['memo'] = cache.statistics()
            result['prepared_road'] = dict(margin_calls=road.margin_calls, polygon_segment_pairs=road.segment_pairs)
            cache.restore(); cache = None
        with stage('result_materialization_JSON_fsync'):
            output = dict(action_bits=None if action is None else action.tobytes().hex(), report=report)
            atomic_write(D / 'output-private.json', output)
            atomic_write(D / 'diagnostics-private.json', prior.previous.materialize(meter.journal.rows))
            atomic_write(D / 'wheel-private.json', prior.previous.materialize(meter.raw_kernels))
        with stage('exact_parity_audit'):
            parity = dict(action_bytes=output['action_bits'] == packet['expected_action_bits'],
                full_report=base.digest(report) == base.digest(packet['expected_certificate']),
                all_raw_diagnostics=base.sha(D / 'diagnostics-private.json') == contract['baseline_raw_sha256'],
                all_wheel_results=base.sha(D / 'wheel-private.json') == contract['baseline_wheel_sha256'],
                model_attempted=meter.counts['model_attempted'] == 906, model_completed=meter.counts['model_completed'] == 888,
                external_force=meter.counts['external_force'] == 3624, internal_force=meter.counts['internal_force'] == 3552,
                normal_geometry=meter.counts['geometry'] - result['pre_choose_geometry'] == 2641,
                memo_unchanged=result['memo']['hits'] == 145 and result['memo']['misses'] == 774,
                passive_reports=all(q['exact'] for q in meter.trial_summaries),
                saved774=result['saved_comparison']['exact'], binary_pin=base.sha(binary) == result['binary_sha256'],
                source_pins=all(base.sha(G / p) == h for p, h in contract['source_sha256'].items()))
            result['parity'] = parity
            result['optimization_adopted'] = all(parity.values())
            result['status'] = 'EXACT_SCALAR_COMPILED_VALIDATED' if result['optimization_adopted'] else 'PARITY_FAILED_NOT_ADOPTED'
            result['single_sample_comparison'] = dict(baseline602=old602['stages']['normal_core'], compiled603=result['stages']['normal_core'])
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
        result['child_CPU_s'] = child_cpu()
        result['time'] = elapsed()
        result['private_sha256'] = {p.name: base.sha(p) for p in D.glob('*.json')}
        atomic_write(G / 'retry/scalar603_result.json', result)
        atomic_write(D / 'CLOSED-private.json', dict(time=elapsed(), chooser_calls=result['chooser_calls'], compilation_attempts=result['compilation_attempts'], result_sha256=base.sha(G / 'retry/scalar603_result.json')))
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
