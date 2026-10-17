"""477 model-only qualification meter; no native authority or global ledger writes."""
import time
WORKER_START = time.perf_counter()
import datetime
import os
from pathlib import Path
import shutil
import signal

from retry.meter453 import Meter453
from retry.paired442_meter import Meter as Meter442
from retry.pilot420_backend import ResourceStop, TechnicalStop
from retry.loss389_analyze import save
from retry.capture434 import CaptureBarrier


class _StorageBarrier(CaptureBarrier):
    def __init__(self, directory, meter):
        super().__init__(directory)
        self.meter = meter

    def seal(self, *args, **kwargs):
        self.meter.check_storage()
        return super().seal(*args, **kwargs)

    def complete(self, *args, **kwargs):
        self.meter.check_storage()
        return super().complete(*args, **kwargs)


class Meter477(Meter453):
    HARD_TICKS = 4096
    HARD_WORLDS = 49
    SCOPE_TICKS = 3674
    SCOPE_WORLDS = 49

    def __init__(self, d, worker_start=None):
        # Runner passes perf_counter captured before its research imports.
        # CPU is absolute process_time, including those imports.
        self.worker_start = WORKER_START if worker_start is None else worker_start
        super().__init__(Path(d))
        self.phase = 'INITIALIZED'
        scope = self.p['scope']
        if scope.get('ticks') != self.SCOPE_TICKS or scope.get('worlds') != self.SCOPE_WORLDS:
            raise TechnicalStop('477_scope_must_be3674ticks49worlds')
        expected=dict(ticks=4096,worlds=49,CPU_s=600,wall_s=900,actual_actions=0,resets=0)
        if any(self.p['caps'].get(k)!=v for k,v in expected.items()):
            raise TechnicalStop('477_hard_contract')
        self.barrier = _StorageBarrier(self.d, self)
        self.allocator_calls=0;self.allocator_CPU_s=0.;self.allocator_wall_s=0.

    def check_storage(self):
        minimum = max(512 * 1024 * 1024,
                      int(self.p.get('storage_free_stop_bytes', 0)))
        for path in ('/tmp', '/workspace'):
            if shutil.disk_usage(path).free < minimum:
                raise ResourceStop('477_storage_' + path.replace('/', '_'))

    def wholetime(self):
        return time.process_time(), time.perf_counter() - self.worker_start

    def deadline(self):
        return min(datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z', '+00:00')),
                   datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00'))

    def persist(self):
        self.check_storage()
        mc, mw = self.modeltime()
        cpu, wall = self.wholetime()
        self.b.update(CPU_s=mc, execution_wall_s=mw)
        save(self.d / 'budget.json', dict(stage=477,
             model={**self.b, 'regions': self.regions}, actual={**self.nb},
             wholeworker_CPU_s=cpu, whole_execution_wall_s=wall,
             actual_actions=0, actual_resets=0, global_ledger_written=False,
             phase=getattr(self, 'phase', 'INITIALIZED'), pid=os.getpid(),allocator=dict(calls=getattr(self,'allocator_calls',0),CPU_s=getattr(self,'allocator_CPU_s',0.),wall_s=getattr(self,'allocator_wall_s',0.))))

    def guard(self):
        self.check_storage()
        cpu, wall = self.wholetime()
        if cpu >= 600 or wall >= 900:
            raise ResourceStop('477_wholeworker_CPU600_wall900')
        if datetime.datetime.now(datetime.timezone.utc) >= self.deadline():
            raise ResourceStop('477_deadline')
        if self.nb['actions'] or self.nb['resets'] or self.actual_start is not None:
            raise TechnicalStop('477_native_forbidden')
        self.persist()

    def timers(self):
        cpu, wall = self.wholetime()
        remaining = (self.deadline() - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        signal.setitimer(signal.ITIMER_PROF, max(.001, 600 - cpu))
        signal.setitimer(signal.ITIMER_REAL, max(.001, min(900 - wall, remaining)))

    def begin_actual(self):
        raise TechnicalStop('477_native_forbidden')

    def charge(self, kind, arm):
        raise TechnicalStop('477_native_forbidden')

    def capture_inputs(self, *args, **kwargs):
        self.guard()
        return super().capture_inputs(*args, **kwargs)

    def world(self, state, tag):
        assert self.active is not None
        self.guard()
        if self.b['worlds'] >= self.HARD_WORLDS:
            raise ResourceStop('477_world_hard49')
        if self.b['worlds'] >= self.SCOPE_WORLDS:
            raise ResourceStop('477_world_scope49')
        return Meter453.world(self, state, tag)

    def step(self, m, act, tag):
        assert self.active is not None
        self.guard()
        if self.b['reserved_ticks'] + 4 > self.HARD_TICKS:
            raise ResourceStop('477_tick_hard4096')
        if self.b['ticks'] + 4 > self.SCOPE_TICKS:
            raise ResourceStop('477_tick_scope3674')
        # Retain493 first-step receipts and428 reserve-before-integrate accounting.
        return Meter442.step(self, m, act, tag)

    def checkpoint(self, phase, **facts):
        self.phase = phase
        self.check_storage()
        cpu, wall = self.wholetime()
        mc, mw = self.modeltime()
        q = dict(stage=477, phase=phase, pid=os.getpid(),
                 at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 actual_actions=0, resets=0, model_ticks=self.b['ticks'],
                 model_reserved_ticks=self.b['reserved_ticks'], model_worlds=self.b['worlds'],
                 model_CPU_s=mc, model_wall_s=mw, wholeworker_CPU_s=cpu,
                 whole_execution_wall_s=wall, global_ledger_written=False, **facts)
        save(self.d / 'progress-private.json', q)
        self.persist()
        return q
