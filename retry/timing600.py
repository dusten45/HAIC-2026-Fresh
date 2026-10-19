"""One recorded chooser call; deferred diagnostic IO, unchanged 598 numeric meters.

No native world, replay, warm-up choose or second invocation is permitted.
"""
import time
BOOT_CPU = time.process_time()
BOOT_WALL = time.perf_counter()
import datetime
import hashlib
import json
import math
import os
import signal
import struct
import subprocess
import sys
import traceback
from collections import Counter
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dsp'
import numpy as np
import retry.cold598_support as old
from retry.cold598_support import Support
from retry.clip561_core import plain, atomic_write
from retry.durable568 import digest
from retry.plan513_model import load_root

G = Path(__file__).resolve().parents[1]
D = Path('/workspace/haic-response600-private')
INPUT = Path('/workspace/haic-response599-private/proposed-timing-input-private.json')
INPUT_SHA = 'a0905322d069bad0b515620aae64856c8c8394d789722db27917486819e0e23e'
CAPS = dict(model_attempted=1536, model_completed=1536, external_force=6144,
            internal_force=6144, total_force=12288, geometry=5000)
DEADLINE = datetime.datetime(2026, 10, 20, 10, 1, 55, tzinfo=datetime.timezone.utc)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def exact_key(value):
    """JSON-domain structural identity, including float type and signed zero.

    No JSON encoding or SHA work. Roots use finite binary64 numbers and string
    dictionary keys. Tuple/list equivalence matches the original plain()/JSON.
    """
    if isinstance(value, dict):
        return ('dict', tuple((k, exact_key(v)) for k, v in sorted(value.items())))
    if isinstance(value, (tuple, list)):
        return ('array', tuple(exact_key(v) for v in value))
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError('NONFINITE_JSON')
        return ('float', struct.pack('>d', value))
    if value is None or isinstance(value, (str, bool, int)):
        return (type(value).__name__, value)
    raise TypeError('UNSUPPORTED_DEFERRED_IDENTITY')


class DeferredDigest:
    def __init__(self, value):
        self.value = value
        self.key = exact_key(value)

    def __eq__(self, other):
        return isinstance(other, DeferredDigest) and self.key == other.key

    def __ne__(self, other):
        return not self == other


def materialize(value):
    if isinstance(value, DeferredDigest):
        return digest(value.value)
    if isinstance(value, dict):
        return {k: materialize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [materialize(v) for v in value]
    return plain(value)


class MemoryJournal:
    """append's return is unused by all the inherited chooser meters."""
    def __init__(self):
        self.rows = []

    def append(self, kind, **data):
        self.rows.append(dict(kind=kind, **data))


class Meter(Support):
    # Reuse the original force/tick/body/Trial/report/geometry meter methods.
    # Only diagnostic digest representation, journal sink and tighter budgets
    # differ; no numeric policy/dynamics/gate function is edited or copied.
    hash = staticmethod(DeferredDigest)

    def __init__(self, static):
        self.static = static
        self.source_index = old.bounds(static['roads'])
        self.source_edges = old.boundary_index(static['boundary'])
        self.counts = Counter()
        self.model = [0]
        self.planner = dict(force_evaluations=0, forecast_calls=0,
                            forecast_ticks=0, geometry_checks=0)
        self.originals = {}
        self.label = 'candidate'
        self.model_mode = 'actual_feedback'
        self.active_trial = None
        self.trial_summaries = []
        self.pending = self.diag = None
        self.last_model_before = self.last_model_after = None
        self.journal = MemoryJournal()
        self.core = None
        self.core_spent = dict(CPU_s=0., wall_s=0.)

    def guard(self, *args):
        if time.process_time() - BOOT_CPU + 5 >= 90:
            raise old.CostStop('TOTAL_CPU90')
        if time.perf_counter() - BOOT_WALL + 5 >= 120:
            raise old.CostStop('TOTAL_WALL120')
        if datetime.datetime.now(datetime.timezone.utc) >= DEADLINE:
            raise old.CostStop('DEADLINE')
        if self.core is None:
            t = elapsed()
            if t['CPU_s'] - self.core_spent['CPU_s'] >= 60:
                raise old.CostStop('PREPARATION_AUDIT_CPU60')
            if t['wall_s'] - self.core_spent['wall_s'] >= 75:
                raise old.CostStop('PREPARATION_AUDIT_WALL75')
        if self.core is not None:
            if time.process_time() - self.core[0] >= 30:
                raise old.CostStop('CORE_CPU30')
            if time.perf_counter() - self.core[1] >= 45:
                raise old.CostStop('CORE_WALL45')

    def capacity(self, req):
        self.guard()
        for k, n in req.items():
            if k in CAPS and self.counts[k] + n > CAPS[k]:
                raise old.CostStop('600_' + k)

    def add(self, k, n=1):
        if k in CAPS and self.counts[k] + n > CAPS[k]:
            raise old.CostStop('600_ADD_' + k)
        self.counts[k] += n


def pure_checks(root, static):
    """Synthetic stand-ins only: zero chooser, integrator and force evaluators."""
    checks = []
    values = [None, True, 1, 1., 0., -0., [1, 2.], (1, 2.),
              {'a': [1., -0.], 'b': False}, Support.short(root),
              Support.short(replace(root, floor=root.floor + .01))]
    for a in values:
        for b in values:
            assert (DeferredDigest(a) == DeferredDigest(b)) == (digest(a) == digest(b))
    checks.append('deferred_identity_matches_eager_JSON_digest_including_signed_zero')
    records = []
    forces = [dict(ratio=.8, clipped=False, wheel=i) for i in range(4)]
    after = replace(root, center=(root.center[0] + .001, root.center[1]))
    def fake_tick(r, gas, brake, index, counter):
        counter[0] += 1
        return after
    for eager in (True, False):
        m = Meter(static)
        if eager:
            m.hash = digest
        m.original_margin = lambda *a: 1.
        with patch.object(old.d, 'force_rows', lambda *a: forces), \
             patch.object(old.d, 'source_tick', fake_tick):
            action = np.array([0., .1, 0.], np.float32)
            assert m.model_force(root, action) is forces
            assert m.model_tick(root, float(action[1]), 0., m.source_index, m.model) is after
            assert m.source_geometry(after) == 1.
        records.append((materialize(m.journal.rows), dict(m.counts)))
    assert records[0] == records[1]
    checks.append('original_force_tick_body_geometry_numeric_and_diagnostic_payloads_equal_with_synthetic_functions')
    m = Meter(static)
    invalid = [dict(ratio=float('nan'), clipped=False)] * 4
    with patch.object(old.d, 'force_rows', lambda *a: invalid):
        try:
            m.model_force(root, np.array([0., 0., 0.], np.float32))
        except old.IdentityStop:
            pass
        else:
            raise AssertionError('INVALID_FORCE_NOT_REJECTED')
    checks.append('original_nonfinite_force_identity_guard_retained')
    m = Meter(static)
    with patch.object(old.d, 'force_rows', lambda *a: forces), \
         patch.object(old.d, 'source_tick', fake_tick), patch.object(old, 'body', lambda *a: 100.):
        m.model_force(root, np.zeros(3, np.float32))
        try:
            m.model_tick(root, 0., 0., m.source_index, m.model)
        except old.DomainStop:
            pass
        else:
            raise AssertionError('BODY100_NOT_REJECTED')
    checks.append('original_body_domain_guard_retained')
    m = Meter(static)
    try:
        m.capacity(dict(model_attempted=1537))
    except old.CostStop:
        pass
    else:
        raise AssertionError('CAP_NOT_REJECTED')
    checks.append('tighter_cap_pre_dispatch_guard')
    for name in ('model_force', 'model_tick', 'source_geometry', 'project',
                 'certifier_factory', 'install_meters', 'kernel', 'short'):
        assert getattr(Meter, name) is getattr(Support, name)
    checks.append('numeric_meter_methods_inherited_unchanged')
    return dict(passed=True, checks=checks, chooser=0, integrator=0, force_evaluator=0,
                geometry_evaluator=0, native=0)


def elapsed():
    return dict(CPU_s=time.process_time() - BOOT_CPU + 5,
                wall_s=time.perf_counter() - BOOT_WALL + 5)


def main():
    D.mkdir(mode=0o700, exist_ok=False)  # Exclusive marker, never retry.
    result = dict(study=600, status='PREPARATION', chooser_calls=0, native=0,
                  worlds=0, resets=0, actions=0, solver=0, FD=0, new_seed=0,
                  HOLDOUT=0, SEALED=0, research_remaining=22211, reserve=84000,
                  reserve_used=0, general_promotion=False, pixel_act_promotion=False)
    meter = None
    started = None
    def interrupt(*args):
        raise old.CostStop('600_TIMER')
    signal.signal(signal.SIGPROF, interrupt)
    signal.signal(signal.SIGALRM, interrupt)
    signal.setitimer(signal.ITIMER_PROF, max(.01, 88 - elapsed()['CPU_s']))
    signal.setitimer(signal.ITIMER_REAL, max(.01, 118 - elapsed()['wall_s']))
    try:
        assert sha(INPUT) == INPUT_SHA
        packet = json.loads(INPUT.read_text())
        c598 = json.loads((G / 'retry/cold598_contract.json').read_text())
        for name, h in c598['implementation_sha256'].items():
            assert sha(G / name) == h, ('598_CODE_PIN', name)
        # Check only already-imported runtime dependencies; no new environment.
        for module in tuple(sys.modules.values()):
            filename = getattr(module, '__file__', None)
            if filename and str(Path(filename).resolve()) in c598['dependency_sha256']:
                p = str(Path(filename).resolve())
                assert sha(p) == c598['dependency_sha256'][p], ('RUNTIME_PIN', p)
        for p, h in [(old.INPUTS['static'], packet['roads_static_sha256']),
                     (old.INPUTS['candidate_paths'], packet['paths_sha256'])]:
            assert sha(p) == h
        assert packet['hold'] == 148
        static = json.loads(old.INPUTS['static'].read_text())
        paths = json.loads(old.INPUTS['candidate_paths'].read_text())
        root = load_root(dict(packet['root'], roads=static['root']['roads']))
        tests = pure_checks(root, static)
        atomic_write(G / 'retry/timing600_tests.json', tests)
        meter = Meter(static)
        geometry = old.tracking.geometry_context(static, 5000)
        import retry.plan512_control as kernel
        assert kernel.MAX_MODEL_TICKS == 200000
        assert subprocess.check_output(['git', 'rev-parse', 'main'], cwd=G, text=True).strip() == 'dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
        assert not subprocess.check_output(['git', 'diff', '--name-only', 'main', '--', 'Participants'], cwd=G, text=True).strip()
        # A world/reset/step cannot be constructed/dispatched from this run.
        def forbidden(*a, **kw):
            raise AssertionError('NATIVE_WORLD_RESET_ACTION_FORBIDDEN')
        old.CarRacing.__init__ = old.CarRacing.reset = old.CarRacing.step = forbidden
        old.Car.__init__ = old.Car.step = forbidden
        meter.install_meters()
        contract = dict(study=600, status='FROZEN_BEFORE_SINGLE_CHOOSE',
                        registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                        deadline_utc=DEADLINE.isoformat(), input_sha256=INPUT_SHA,
                        implementation_sha256=sha(Path(__file__)),
                        original_contract_sha256=sha(G / 'retry/cold598_contract.json'),
                        tests_sha256=sha(G / 'retry/timing600_tests.json'),
                        caps=CAPS, kernel_hardcap=200000, chooser_calls=1,
                        time_caps=dict(core_CPU_s=30, core_wall_s=45,
                                       preparation_audit_CPU_s=60, preparation_audit_wall_s=75,
                                       total_CPU_s=90, total_wall_s=120),
                        boundary='Start clocks immediately before ONE original tracking.choose; end clocks in finally immediately after return/exception. Includes nominal/backup/trials/freshFINAL/report/action plus unchanged inherited598 numeric/body/cost/passiveTrial meters, finite structural root identity and in-memory diagnostics. No import/restore/context setup/JSON/SHA/fsync/4raw preview/native/pixel/thread/marshalling inside core.',
                        diagnostic_change='Inherited598 short/asdict retained. Original diagnostic SHA replaced inside core by typed finite structural keys including signedzero; SHA and JSON/fsync deferred until afterward. Pure synthetic eager/deferred payload and identity checks before call. This is an explicit offline diagnostic IO protocol change, not original durable-before-every-primitive protocol.',
                        parity='Exact float32 action bytes, entire certificate report/trials/FINAL via JSON-domain digest; attempts906/completed888, forces3624/3552 and geometry2641. Mismatch=>timing interpretation withheld, no retry.',
                        decision='Only if parity valid: core wall>=5 means this implementation/input component exceeded5s; otherwise report one sample only. Neither implies fullact/pixel/allinput eligibility or universal impossibility. No lap improvement claim.',
                        stop='First cap/domain/identity/IO/error stops. No rerun/warmup/other input or follow-up experiment.',
                        parent_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=G, text=True).strip(),
                        runtime=dict(python=sys.version, numpy=np.__version__, platform=old.platform.platform()),
                        privacy='Raw roots/commands/reports and deferred journal private outside Git. Technical code/hash/aggregates only.',
                        research_remaining=22211, reserve=84000, reserve_used=0)
        atomic_write(G / 'retry/timing600_contract.json', contract)
        atomic_write(D / 'REGISTERED-private.json', dict(contract_sha256=sha(G / 'retry/timing600_contract.json'), input=packet, chooser_calls=0))
        meter.guard()
        assert elapsed()['CPU_s'] < 50 and elapsed()['wall_s'] < 65  # full core+audit reserve
        result['preparation_before_call'] = elapsed()
        atomic_write(D / 'CALL_STARTED-private.json', dict(contract_sha256=sha(G / 'retry/timing600_contract.json'), chooser_calls=1))
        result['chooser_calls'] = 1
        signal.setitimer(signal.ITIMER_PROF, min(30., 88 - elapsed()['CPU_s']))
        signal.setitimer(signal.ITIMER_REAL, min(45., 118 - elapsed()['wall_s']))
        meter.core = started = (time.process_time(), time.perf_counter())
        try:
            action, report = old.tracking.choose(root, paths['candidate'], paths['backup'],
                                                packet['progress'], meter.model, meter.planner,
                                                180000, history=tuple(packet['actual_running_history']),
                                                geometry=geometry)
        finally:
            result['core'] = dict(CPU_s=time.process_time() - started[0],
                                  wall_s=time.perf_counter() - started[1])
            meter.core = None
            meter.core_spent = result['core']
            signal.setitimer(signal.ITIMER_PROF, max(.01, min(88 - elapsed()['CPU_s'], 58 - (elapsed()['CPU_s'] - result['core']['CPU_s']))))
            signal.setitimer(signal.ITIMER_REAL, max(.01, min(118 - elapsed()['wall_s'], 73 - (elapsed()['wall_s'] - result['core']['wall_s']))))
        output_start = (time.process_time(), time.perf_counter())
        atomic_write(D / 'output-private.json', dict(action_bits=None if action is None else action.tobytes().hex(), report=report))
        parity = dict(action_bytes=action is not None and action.dtype == np.float32 and action.tobytes().hex() == packet['expected_action_bits'],
                      full_certificate=digest(report) == digest(packet['expected_certificate']),
                      attempted=meter.counts['model_attempted'] == 906,
                      completed=meter.counts['model_completed'] == 888,
                      external_force=meter.counts['external_force'] == 3624,
                      internal_force=meter.counts['internal_force'] == 3552,
                      geometry=meter.counts['geometry'] == 2641,
                      tick_counter=meter.model[0] == 888,
                      passive_reports=all(x['exact'] for x in meter.trial_summaries),
                      fresh_FINAL=report.get('final_recertified') and any(x['mode'] == 'FINAL' and x['ok'] for x in report.get('reports', [])))
        result['parity'] = parity
        result['status'] = ('PARITY_VALID_COMPONENT_EXCEEDS5S' if result['core']['wall_s'] >= 5 else 'PARITY_VALID_SINGLE_COMPONENT_SAMPLE_BELOW5S') if all(parity.values()) else 'PARITY_MISMATCH_TIMING_WITHHELD'
        atomic_write(D / 'deferred-diagnostics-private.json', materialize(meter.journal.rows))
        result['output_materialization_JSON_fsync_and_parity'] = dict(CPU_s=time.process_time() - output_start[0], wall_s=time.perf_counter() - output_start[1])
        assert sha(INPUT) == INPUT_SHA and sha(Path(__file__)) == contract['implementation_sha256']
        meter.guard()
    except BaseException as exc:
        result['status'] = 'COST_CENSORED_TIMING_WITHHELD' if isinstance(exc, old.CostStop) else 'TECHNICAL_FAILURE_TIMING_WITHHELD'
        result['error'] = type(exc).__name__ + ':' + str(exc)
        atomic_write(D / 'error-private.json', dict(error=result['error'], traceback=traceback.format_exc()))
    finally:
        if meter is not None:
            meter.restore()
            result['cost'] = dict(meter.counts)
            result['planner_cost'] = meter.planner
            result['diagnostic_events'] = len(meter.journal.rows)
        result['total_pre_result'] = elapsed()
        core = result.get('core', dict(CPU_s=0., wall_s=0.))
        result['preparation_audit_pre_result'] = {k: result['total_pre_result'][k] - core[k] for k in core}
        result['scope'] = 'One privileged saved-state chooser component only; not full Agent.act, pixel, all inputs, native simulation or lap improvement.'
        result['private_sha256'] = {p.name: sha(p) for p in D.glob('*.json')}
        atomic_write(G / 'retry/timing600_result.json', result)
        # Final result serialization is measured separately and bounded by timer.
        atomic_write(D / 'CLOSED-private.json', dict(final_total=elapsed(), chooser_calls=result['chooser_calls'], result_sha256=sha(G / 'retry/timing600_result.json')))
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.setitimer(signal.ITIMER_REAL, 0)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
