"""483 model-only qualification meter; no native authority or global ledger writes."""
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


class Meter483(Meter453):
    HARD_TICKS = 520
    HARD_WORLDS = 110
    SCOPE_TICKS = 520
    SCOPE_WORLDS = 110

    def __init__(self, d, worker_start=None, preparation_CPU_s=0., preparation_wall_s=0.):
        # Runner passes perf_counter captured before its research imports.
        # CPU is absolute process_time, including those imports.
        self.preparation_CPU_s=preparation_CPU_s;self.preparation_wall_s=preparation_wall_s
        self.integrating_worlds=0;self.peak_integrating=0;self.peak_live=0;self.closed_worlds=0;self.wrapper_slots=0
        self.durable_save=save;self.last_durable=0.
        self.worker_start = WORKER_START if worker_start is None else worker_start
        super().__init__(Path(d))
        self.phase = 'INITIALIZED'
        scope = self.p['scope']
        if scope.get('ticks') != self.SCOPE_TICKS or scope.get('worlds') != self.SCOPE_WORLDS:
            raise TechnicalStop('483_scope_must_be520ticks110worlds')
        expected=dict(ticks=520,worlds=110,CPU_s=480,wall_s=600,actual_actions=0,resets=0)
        if any(self.p['caps'].get(k)!=v for k,v in expected.items()):
            raise TechnicalStop('483_hard_contract')
        self.barrier = _StorageBarrier(self.d, self)
        self.allocator_calls=0;self.allocator_CPU_s=0.;self.allocator_wall_s=0.;self.charged_ticks=0

    def check_storage(self):
        minimum = max(512 * 1024 * 1024,
                      int(self.p.get('storage_free_stop_bytes', 0)))
        for path in ('/tmp', '/workspace'):
            if shutil.disk_usage(path).free < minimum:
                raise ResourceStop('483_storage_' + path.replace('/', '_'))

    def wholetime(self):
        return time.process_time()+self.preparation_CPU_s, time.perf_counter()-self.worker_start+self.preparation_wall_s

    def deadline(self):
        return min(datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z', '+00:00')),
                   datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00'))

    def persist(self):
        self.check_storage()
        mc, mw = self.modeltime()
        cpu, wall = self.wholetime()
        self.b.update(CPU_s=mc, execution_wall_s=mw,charged_ticks=getattr(self,'charged_ticks',0),wrapper_slots=self.wrapper_slots,live_worlds=len(self.live),peak_live=self.peak_live,integrating_worlds=self.integrating_worlds,peak_integrating=self.peak_integrating,closed_worlds=self.closed_worlds)
        save(self.d / 'budget.json', dict(stage=483,
             model={**self.b, 'regions': self.regions}, actual={**self.nb},
             wholeworker_CPU_s=cpu, whole_execution_wall_s=wall,
             actual_actions=0, actual_resets=0, global_ledger_written=False,
             phase=getattr(self, 'phase', 'INITIALIZED'), pid=os.getpid(),allocator=dict(calls=getattr(self,'allocator_calls',0),CPU_s=getattr(self,'allocator_CPU_s',0.),wall_s=getattr(self,'allocator_wall_s',0.))))

    def guard(self):
        self.check_storage()
        cpu, wall = self.wholetime()
        if cpu >= 480 or wall >= 600:
            raise ResourceStop('483_wholeworker_CPU480_wall600')
        if datetime.datetime.now(datetime.timezone.utc) >= self.deadline():
            raise ResourceStop('483_deadline')
        if self.nb['actions'] or self.nb['resets'] or self.actual_start is not None:
            raise TechnicalStop('483_native_forbidden')
        if self.allocator_calls>26:raise ResourceStop('483_allocator26')
        self.persist()

    def timers(self):
        cpu, wall = self.wholetime()
        remaining = (self.deadline() - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        signal.setitimer(signal.ITIMER_PROF, max(.001, 480 - cpu))
        signal.setitimer(signal.ITIMER_REAL, max(.001, min(600 - wall, remaining)))

    def begin_actual(self):
        raise TechnicalStop('483_native_forbidden')

    def charge(self, kind, arm):
        raise TechnicalStop('483_native_forbidden')

    def capture_inputs(self, *args, **kwargs):
        self.guard()
        return super().capture_inputs(*args, **kwargs)

    def world(self, state, tag):
        assert self.active is not None
        self.guard()
        if self.b['worlds'] >= self.HARD_WORLDS:
            raise ResourceStop('483_world_hard110')
        if self.b['worlds'] >= self.SCOPE_WORLDS:
            raise ResourceStop('483_world_scope110')
        if len(self.live)>=2:raise ResourceStop('483_live_worlds2')
        if self.integrating_worlds:raise TechnicalStop('483_concurrent_constructor_or_step')
        self.peak_live=max(self.peak_live,len(self.live)+1)
        self.integrating_worlds=1;self.peak_integrating=max(self.peak_integrating,1)
        try:
            model=Meter453.world(self,state,tag)
            self.peak_live=max(self.peak_live,len(self.live))
            return model
        finally:
            self.integrating_worlds=0;self.peak_live=max(self.peak_live,len(self.live));self.persist()

    def step(self, m, act, tag):
        assert self.active is not None
        self.guard()
        if self.charged_ticks + 4 > self.HARD_TICKS:
            raise ResourceStop('483_tick_hard520')
        if self.b['ticks'] + 4 > self.SCOPE_TICKS:
            raise ResourceStop('483_tick_scope520')
        if self.wrapper_slots>=130:raise ResourceStop('483_wrapper_slots130')
        if self.integrating_worlds:raise TechnicalStop('483_concurrent_constructor_or_step')
        if m not in self.live:raise TechnicalStop('483_step_nonlive_world')
        self.charged_ticks+=4;self.wrapper_slots+=1;self.persist()
        self.integrating_worlds=1;self.peak_integrating=max(self.peak_integrating,1)
        try:
            # Preserve433 first-step receipts and428 reserve-before-integrate.
            return Meter442.step(self,m,act,tag)
        finally:
            self.integrating_worlds=0;self.persist()

    def close(self,m):
        # Source.close merely detaches its listener. Explicitly tear down all
        # bodies/joints after the caller's final dump; this never integrates.
        if m not in self.live:return
        if self.integrating_worlds:raise TechnicalStop('483_close_during_integration')
        stream=self.streams.get(id(m));child=None if stream is None else stream.child
        m.close()
        world=m.world
        for body in list(world.bodies):world.DestroyBody(body)
        if list(world.bodies) or list(world.joints):raise TechnicalStop('483_world_teardown_incomplete')
        self.live.remove(m);self.closed_worlds+=1
        self.auth.pop(id(m),None);self.streams.pop(id(m),None)
        if stream is not None:
            stream.world=None;stream.ctrl=None;stream.child=None
        if child is not None:child.m=None
        # Remove every model-owned reference, including initial-contact caches.
        m.__dict__.clear();m.closed483=True
        self.persist()

    def checkpoint(self, phase, **facts):
        self.phase = phase
        self.check_storage()
        cpu, wall = self.wholetime()
        mc, mw = self.modeltime()
        q = dict(stage=483, phase=phase, pid=os.getpid(),
                 at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 actual_actions=0, resets=0, model_ticks=self.b['ticks'],
                 model_reserved_ticks=self.b['reserved_ticks'], model_worlds=self.b['worlds'],
                 model_CPU_s=mc, model_wall_s=mw, wholeworker_CPU_s=cpu,
                 whole_execution_wall_s=wall, global_ledger_written=False, **facts)
        save(self.d / 'progress-private.json', q)
        self.persist()
        if wall-self.last_durable>=30 or phase.startswith('CLOSED'):
            self.durable_save(Path('/workspace/haic-private-retry-20261009/stage483-checkpoint-private.json'),q);self.last_durable=wall
        return q
