"""485 exclusive model/native meter with prospective charge-before-call journals."""
import time
WORKER_START = time.perf_counter()
import contextlib
import datetime
import os
from pathlib import Path
import shutil
import signal

from retry.meter453 import Meter453
from retry.paired442_meter import Meter as Meter442
from retry.pilot420_backend import ResourceStop, TechnicalStop
from retry.loss389_analyze import save
from retry.receipt421_io import save_receipt
from retry.pilot420_backend import snapshot,rnghash
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


class Meter485(Meter453):
    HARD_TICKS = 1064
    HARD_WORLDS = 226
    SCOPE_TICKS = 1064
    SCOPE_WORLDS = 226

    def __init__(self, d, worker_start=None, preparation_CPU_s=0., preparation_wall_s=0.):
        # Runner passes perf_counter captured before its research imports.
        # CPU is absolute process_time, including those imports.
        self.preparation_CPU_s=preparation_CPU_s;self.preparation_wall_s=preparation_wall_s
        self.integrating_worlds=0;self.peak_integrating=0;self.peak_live=0;self.closed_worlds=0;self.wrapper_slots=0
        self.durable_save=save;self.last_durable=0.
        self.worker_start = WORKER_START if worker_start is None else worker_start
        super().__init__(Path(d))
        self.mc=0.;self.mw=0.;self.raw_counts={};self.geometry_CPU_s=0.;self.geometry_wall_s=0.
        self.native_charge_hook=lambda *args: (_ for _ in ()).throw(TechnicalStop('485_missing_charge_journal'))
        self.phase = 'INITIALIZED'
        scope = self.p['scope']
        if scope.get('ticks') != self.SCOPE_TICKS or scope.get('worlds') != self.SCOPE_WORLDS:
            raise TechnicalStop('485_scope_must_be1064ticks226worlds')
        expected=dict(ticks=1064,worlds=226,CPU_s=2400,wall_s=3000,actual_actions=256,resets=2)
        if any(self.p['caps'].get(k)!=v for k,v in expected.items()):
            raise TechnicalStop('485_hard_contract')
        self.barrier = _StorageBarrier(self.d, self)
        self.allocator_calls=0;self.allocator_CPU_s=0.;self.allocator_wall_s=0.;self.charged_ticks=0

    def check_storage(self):
        minimum = max(512 * 1024 * 1024,
                      int(self.p.get('storage_free_stop_bytes', 0)))
        for path in ('/tmp', '/workspace'):
            if shutil.disk_usage(path).free < minimum:
                raise ResourceStop('485_storage_' + path.replace('/', '_'))

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
        save(self.d / 'budget.json', dict(stage=485,
             model={**self.b, 'regions': self.regions}, actual={**self.nb},
             wholeworker_CPU_s=cpu, whole_execution_wall_s=wall,
             actual_actions=self.nb['actions'], actual_resets=self.nb['resets'], global_ledger_written=bool(self.nb['actions'] or self.nb['resets']),
             phase=getattr(self, 'phase', 'INITIALIZED'), pid=os.getpid(),allocator=dict(calls=getattr(self,'allocator_calls',0),CPU_s=getattr(self,'allocator_CPU_s',0.),wall_s=getattr(self,'allocator_wall_s',0.))))

    def guard(self):
        self.check_storage()
        cpu, wall = self.wholetime()
        if cpu >= 2400 or wall >= 3000:
            raise ResourceStop('485_wholeworker_CPU2400_wall3000')
        if datetime.datetime.now(datetime.timezone.utc) >= self.deadline():
            raise ResourceStop('485_deadline')
        mc,mw=self.modeltime();nc,nw=self.nativetime()
        if mc>=1700 or mw>=2100:raise ResourceStop('485_model_exclusive_1700_2100')
        if nc>=360 or nw>=550:raise ResourceStop('485_native_exclusive_360_550')
        if self.allocator_calls>52:raise ResourceStop('485_allocator52')
        self.persist()

    def timers(self):
        cpu, wall = self.wholetime()
        remaining = (self.deadline() - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        limits=[(2400-cpu,3000-wall),(remaining,remaining)]
        if self.active:
            c,w=self.modeltime();limits.append((1700-c,2100-w))
        if self.actual_start:
            c,w=self.nativetime();limits.append((360-c,550-w))
        signal.setitimer(signal.ITIMER_PROF,max(.001,min(x[0] for x in limits)))
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(x[1] for x in limits)))

    @contextlib.contextmanager
    def model(self,label):
        if self.actual_start is not None:raise TechnicalStop('485_model_native_region_overlap')
        with super().model(label):yield

    def begin_actual(self):
        if self.active is not None or self.actual_start is not None:raise TechnicalStop('485_native_region_overlap')
        self.actual_start=time.process_time(),time.perf_counter();self.timers()

    def nativetime(self):
        if self.actual_start is None:return self.nb['CPU_s'],self.nb['wall_s']
        return self.nb['CPU_s']+time.process_time()-self.actual_start[0],self.nb['wall_s']+time.perf_counter()-self.actual_start[1]

    def end_actual(self):
        if self.actual_start is not None:
            c,w=self.nativetime();self.nb['CPU_s']=c;self.nb['wall_s']=w;self.actual_start=None
        self.timers();self.persist()

    def charge(self,kind,arm):
        if self.actual_start is None or self.active is not None or arm not in ('D485-A','D485-B'):raise TechnicalStop('485_native_authority')
        if kind in ('reset_raw','action_raw'):
            self.guard();counter=self.raw_counts.setdefault(arm,dict(reset_raw=0,action_raw=0))
            limit=64 if kind=='reset_raw' else 512
            if counter[kind]>=limit:raise ResourceStop('485_native_raw_cap')
            self.native_charge_hook(kind,arm,counter[kind]+1)
            counter[kind]+=1;self.persist();return
        if kind not in ('action','reset'):raise TechnicalStop('485_charge_kind')
        self.guard();key='actions' if kind=='action' else 'resets';ak='arm_'+key
        if self.nb[key]>=(256 if kind=='action' else 2) or self.nb[ak].get(arm,0)>=(128 if kind=='action' else 1):raise ResourceStop('485_native_cap')
        number=self.nb[key]+1
        # Dispatch is forbidden until both the append-only charge and updated
        # current-stage ledger have been durably published by the runner hook.
        self.native_charge_hook(kind,arm,number)
        self.nb[key]=number;self.nb[ak][arm]=self.nb[ak].get(arm,0)+1;self.persist()

    @contextlib.contextmanager
    def geometry(self,slot):
        if self.active is not None:raise TechnicalStop('485_geometry_model_overlap')
        running=self.actual_start is not None
        if running:self.end_actual()
        self.guard();c=time.process_time();w=time.perf_counter()
        signal.setitimer(signal.ITIMER_PROF,max(.001,min(60,120-self.geometry_CPU_s,2400-self.wholetime()[0])))
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(90,180-self.geometry_wall_s,3000-self.wholetime()[1],(self.deadline()-datetime.datetime.now(datetime.timezone.utc)).total_seconds())))
        try:yield
        finally:
            self.timers()
            dc=time.process_time()-c;dw=time.perf_counter()-w
            self.geometry_CPU_s+=dc;self.geometry_wall_s+=dw
            if dc>60 or dw>90 or self.geometry_CPU_s>120 or self.geometry_wall_s>180:raise ResourceStop('485_geometry_60_90_each_120_180_total')
            if running:self.begin_actual()
            self.guard()

    def capture_inputs(self, *args, **kwargs):
        self.guard()
        return super().capture_inputs(*args, **kwargs)

    def world(self, state, tag):
        assert self.active is not None
        self.guard()
        if self.b['worlds'] >= self.HARD_WORLDS:
            raise ResourceStop('485_world_hard226')
        if self.b['worlds'] >= self.SCOPE_WORLDS:
            raise ResourceStop('485_world_scope226')
        if len(self.live)>=2:raise ResourceStop('485_live_worlds2')
        if self.integrating_worlds:raise TechnicalStop('485_concurrent_constructor_or_step')
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
            raise ResourceStop('485_tick_hard1064')
        if self.b['ticks'] + 4 > self.SCOPE_TICKS:
            raise ResourceStop('485_tick_scope1064')
        if self.wrapper_slots>=266:raise ResourceStop('485_wrapper_slots266')
        if self.integrating_worlds:raise TechnicalStop('485_concurrent_constructor_or_step')
        if m not in self.live:raise TechnicalStop('485_step_nonlive_world')
        auth=self.auth[id(m)]
        if not auth['first_step']:
            save_receipt(self.d/('world'+str(auth['number'])+'-before-first-step-private.json'),dict(**auth,model_root=snapshot(m),global_RNG_digest=rnghash(),first_command=[float(x) for x in act],tag=tag,qualification_passed=self.qualification_passed,actual_execution_allowed=False))
            stream=self.streams.get(id(m))
            if stream is None:raise TechnicalStop('485_FIRST_STEP_MISSING_STREAM')
            paths=[self.d/('world'+str(auth['number'])+'-before-constructor-private.json'),self.d/('world'+str(auth['number'])+'-before-first-step-private.json'),self.d/(stream.label+'-runtime-link-private.json')]
            if sum(p.stat().st_size for p in paths)>829464:raise ResourceStop('485_WORLD_HEADER829464')
            auth['first_step']=True
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
        if self.integrating_worlds:raise TechnicalStop('485_close_during_integration')
        stream=self.streams.get(id(m));child=None if stream is None else stream.child
        m.close()
        world=m.world
        for body in list(world.bodies):world.DestroyBody(body)
        if list(world.bodies) or list(world.joints):raise TechnicalStop('485_world_teardown_incomplete')
        self.live.remove(m);self.closed_worlds+=1
        self.auth.pop(id(m),None);self.streams.pop(id(m),None)
        if stream is not None:
            stream.world=None;stream.ctrl=None;stream.child=None
        if child is not None:child.m=None
        # Remove every model-owned reference, including initial-contact caches.
        m.__dict__.clear();m.closed485=True
        self.persist()

    def checkpoint(self, phase, **facts):
        self.phase = phase
        self.check_storage()
        cpu, wall = self.wholetime()
        mc, mw = self.modeltime()
        q = dict(stage=485, phase=phase, pid=os.getpid(),
                 at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 actual_actions=self.nb['actions'], resets=self.nb['resets'], model_ticks=self.b['ticks'],
                 model_reserved_ticks=self.b['reserved_ticks'], model_worlds=self.b['worlds'],
                 model_CPU_s=mc, model_wall_s=mw, wholeworker_CPU_s=cpu,
                 whole_execution_wall_s=wall, global_ledger_written=bool(self.nb['actions'] or self.nb['resets']), **facts)
        save(self.d / 'progress-private.json', q)
        self.persist()
        if wall-self.last_durable>=30 or phase.startswith('CLOSED'):
            self.durable_checkpoint(q);self.last_durable=wall
        return q
