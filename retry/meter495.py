"""495 exclusive model/native meter with prospective charge-before-call journals."""
import time
WORKER_START = time.perf_counter()
import contextlib
import datetime
import os
from pathlib import Path
import shutil
import signal

if '_BOUND_DEPS' not in globals():
    _BOUND_DEPS=None
if _BOUND_DEPS is not None:
    Meter453=_BOUND_DEPS['meter453'].Meter453
    Meter442=_BOUND_DEPS['paired442_meter'].Meter
    ResourceStop=_BOUND_DEPS['pilot420_backend'].ResourceStop
    TechnicalStop=_BOUND_DEPS['pilot420_backend'].TechnicalStop
    save=_BOUND_DEPS['loss389_analyze'].save
    save_receipt=_BOUND_DEPS['receipt421_io'].save_receipt
    snapshot=_BOUND_DEPS['pilot420_backend'].snapshot
    rnghash=_BOUND_DEPS['pilot420_backend'].rnghash
    CaptureBarrier=_BOUND_DEPS['capture434'].CaptureBarrier
else:
    # Importing this registration module does not load a physics backend.
    Meter453=object;Meter442=object;CaptureBarrier=object


def bind_dependencies(namespace):
    """Return private Meter495 using explicitly isolated dependency modules."""
    required={'meter453','paired442_meter','pilot420_backend','loss389_analyze','receipt421_io','capture434'}
    if not required.issubset(namespace):raise ValueError('missing_meter495_dependencies:'+','.join(sorted(required-set(namespace))))
    env={'_BOUND_DEPS':dict(namespace),'__file__':__file__,'__name__':__name__+'.bound'}
    exec(compile(Path(__file__).read_text(),__file__,'exec'),env)
    return env['Meter495']


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


class Meter495(Meter453):
    HARD_TICKS = 536
    HARD_WORLDS = 113
    SCOPE_TICKS = 536
    SCOPE_WORLDS = 113

    def __init__(self, d, worker_start=None, preparation_CPU_s=0., preparation_wall_s=0.):
        if _BOUND_DEPS is None:raise RuntimeError('495_bind_dependencies_required')
        # Runner passes perf_counter captured before its research imports.
        # CPU is absolute process_time, including those imports.
        self.preparation_CPU_s=preparation_CPU_s;self.preparation_wall_s=preparation_wall_s
        self.integrating_worlds=0;self.peak_integrating=0;self.peak_live=0;self.closed_worlds=0;self.wrapper_slots=0
        self.durable_save=save;self.last_durable=0.
        self.worker_start = WORKER_START if worker_start is None else worker_start
        super().__init__(Path(d))
        self.mc=0.;self.mw=0.;self.raw_counts={};self.geometry_CPU_s=0.;self.geometry_wall_s=0.
        self.native_charge_hook=lambda *args: (_ for _ in ()).throw(TechnicalStop('495_missing_charge_journal'))
        self.phase = 'INITIALIZED'
        scope = self.p['scope']
        if scope.get('ticks') != self.SCOPE_TICKS or scope.get('worlds') != self.SCOPE_WORLDS:
            raise TechnicalStop('495_scope_must_be536ticks113worlds')
        expected=dict(ticks=536,worlds=113,CPU_s=900,wall_s=1200,actual_actions=129,resets=1)
        if any(self.p['caps'].get(k)!=v for k,v in expected.items()):
            raise TechnicalStop('495_hard_contract')
        self.barrier = _StorageBarrier(self.d, self)
        self.allocator_calls=0;self.allocator_CPU_s=0.;self.allocator_wall_s=0.;self.charged_ticks=0

    def check_storage(self):
        minimum = max(512 * 1024 * 1024,
                      int(self.p.get('storage_free_stop_bytes', 0)))
        for path in ('/tmp', '/workspace'):
            if shutil.disk_usage(path).free < minimum:
                raise ResourceStop('495_storage_' + path.replace('/', '_'))

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
        save(self.d / 'budget.json', dict(stage=495,
             model={**self.b, 'regions': self.regions}, actual={**self.nb},
             wholeworker_CPU_s=cpu, whole_execution_wall_s=wall,
             actual_actions=self.nb['actions'], actual_resets=self.nb['resets'], global_ledger_written=bool(self.nb['actions'] or self.nb['resets']),
             phase=getattr(self, 'phase', 'INITIALIZED'), pid=os.getpid(),allocator=dict(calls=getattr(self,'allocator_calls',0),CPU_s=getattr(self,'allocator_CPU_s',0.),wall_s=getattr(self,'allocator_wall_s',0.))))

    def guard(self):
        self.check_storage()
        cpu, wall = self.wholetime()
        if cpu >= 900 or wall >= 1200:
            raise ResourceStop('495_wholeworker_CPU900_wall1200')
        if datetime.datetime.now(datetime.timezone.utc) >= self.deadline():
            raise ResourceStop('495_deadline')
        mc,mw=self.modeltime();nc,nw=self.nativetime()
        if mc>=480 or mw>=600:raise ResourceStop('495_model_exclusive_480_600')
        if nc>=240 or nw>=360:raise ResourceStop('495_native_exclusive_240_360')
        if self.allocator_calls>26:raise ResourceStop('495_allocator26')
        self.persist()

    def timers(self):
        cpu, wall = self.wholetime()
        remaining = (self.deadline() - datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        limits=[(900-cpu,1200-wall),(remaining,remaining)]
        if self.active:
            c,w=self.modeltime();limits.append((480-c,600-w))
        if self.actual_start:
            c,w=self.nativetime();limits.append((240-c,360-w))
        signal.setitimer(signal.ITIMER_PROF,max(.001,min(x[0] for x in limits)))
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(x[1] for x in limits)))

    @contextlib.contextmanager
    def model(self,label):
        if self.actual_start is not None:raise TechnicalStop('495_model_native_region_overlap')
        with super().model(label):yield

    def begin_actual(self):
        if self.active is not None or self.actual_start is not None:raise TechnicalStop('495_native_region_overlap')
        self.actual_start=time.process_time(),time.perf_counter();self.timers()

    def nativetime(self):
        if self.actual_start is None:return self.nb['CPU_s'],self.nb['wall_s']
        return self.nb['CPU_s']+time.process_time()-self.actual_start[0],self.nb['wall_s']+time.perf_counter()-self.actual_start[1]

    def end_actual(self):
        if self.actual_start is not None:
            c,w=self.nativetime();self.nb['CPU_s']=c;self.nb['wall_s']=w;self.actual_start=None
        self.timers();self.persist()

    def charge(self,kind,arm):
        if self.actual_start is None or self.active is not None or arm not in ('D495-A',):raise TechnicalStop('495_native_authority')
        if kind in ('reset_raw','action_raw'):
            self.guard();counter=self.raw_counts.setdefault(arm,dict(reset_raw=0,action_raw=0))
            limit=64 if kind=='reset_raw' else 516
            if counter[kind]>=limit or sum(sum(v.values()) for v in self.raw_counts.values())>=580:raise ResourceStop('495_native_raw_cap')
            self.native_charge_hook(kind,arm,counter[kind]+1)
            counter[kind]+=1;self.persist();return
        if kind not in ('action','reset'):raise TechnicalStop('495_charge_kind')
        self.guard();key='actions' if kind=='action' else 'resets';ak='arm_'+key
        if self.nb[key]>=(129 if kind=='action' else 1) or self.nb[ak].get(arm,0)>=(129 if kind=='action' else 1):raise ResourceStop('495_native_cap')
        number=self.nb[key]+1
        # Dispatch is forbidden until both the append-only charge and updated
        # current-stage ledger have been durably published by the runner hook.
        self.native_charge_hook(kind,arm,number)
        self.nb[key]=number;self.nb[ak][arm]=self.nb[ak].get(arm,0)+1;self.persist()

    @contextlib.contextmanager
    def geometry(self,slot):
        raise TechnicalStop('495_geometry_recomputation_forbidden')
        yield

    @contextlib.contextmanager
    def allocator(self):
        if self.active is not None or self.actual_start is not None:raise TechnicalStop('495_allocator_region_overlap')
        self.guard()
        if self.allocator_calls>=26:raise ResourceStop('495_allocator26')
        self.allocator_calls+=1;self.persist()
        c=time.process_time();w=time.perf_counter()
        try:yield
        finally:
            self.allocator_CPU_s+=time.process_time()-c;self.allocator_wall_s+=time.perf_counter()-w
            self.guard()

    def capture_inputs(self, *args, **kwargs):
        self.guard()
        return super().capture_inputs(*args, **kwargs)

    def world(self, state, tag):
        assert self.active is not None
        self.guard()
        if self.b['worlds'] >= self.HARD_WORLDS:
            raise ResourceStop('495_world_hard113')
        if self.b['worlds'] >= self.SCOPE_WORLDS:
            raise ResourceStop('495_world_scope113')
        if len(self.live)>=2:raise ResourceStop('495_live_worlds2')
        if self.integrating_worlds:raise TechnicalStop('495_concurrent_constructor_or_step')
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
            raise ResourceStop('495_tick_hard536')
        if self.b['ticks'] + 4 > self.SCOPE_TICKS:
            raise ResourceStop('495_tick_scope536')
        if self.wrapper_slots>=134:raise ResourceStop('495_wrapper_slots134')
        if self.integrating_worlds:raise TechnicalStop('495_concurrent_constructor_or_step')
        if m not in self.live:raise TechnicalStop('495_step_nonlive_world')
        auth=self.auth[id(m)]
        if not auth['first_step']:
            save_receipt(self.d/('world'+str(auth['number'])+'-before-first-step-private.json'),dict(**auth,model_root=snapshot(m),global_RNG_digest=rnghash(),first_command=[float(x) for x in act],tag=tag,qualification_passed=self.qualification_passed,actual_execution_allowed=False))
            stream=self.streams.get(id(m))
            if stream is None:raise TechnicalStop('495_FIRST_STEP_MISSING_STREAM')
            paths=[self.d/('world'+str(auth['number'])+'-before-constructor-private.json'),self.d/('world'+str(auth['number'])+'-before-first-step-private.json'),self.d/(stream.label+'-runtime-link-private.json')]
            if sum(p.stat().st_size for p in paths)>1048576:raise ResourceStop('495_WORLD_HEADER1MiB')
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
        if self.integrating_worlds:raise TechnicalStop('495_close_during_integration')
        stream=self.streams.get(id(m));child=None if stream is None else stream.child
        m.close()
        world=m.world
        for body in list(world.bodies):world.DestroyBody(body)
        if list(world.bodies) or list(world.joints):raise TechnicalStop('495_world_teardown_incomplete')
        self.live.remove(m);self.closed_worlds+=1
        self.auth.pop(id(m),None);self.streams.pop(id(m),None)
        if stream is not None:
            stream.world=None;stream.ctrl=None;stream.child=None
        if child is not None:child.m=None
        # Remove every model-owned reference, including initial-contact caches.
        m.__dict__.clear();m.closed495=True
        self.persist()

    def checkpoint(self, phase, **facts):
        self.phase = phase
        self.check_storage()
        cpu, wall = self.wholetime()
        mc, mw = self.modeltime()
        q = dict(stage=495, phase=phase, pid=os.getpid(),
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

# Compatibility alias: callers must obtain the bound class via factory first.
Meter485=Meter495
