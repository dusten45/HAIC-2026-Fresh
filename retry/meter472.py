"""472 one native P4 candidate, strict whole-worker and all-inclusive model caps."""
import time
WORKER_START=time.perf_counter()
import datetime,os,shutil,signal
from pathlib import Path
from retry.meter453 import Meter453
from retry.paired442_meter import Meter as Meter442
from retry.pilot420_backend import ResourceStop,TechnicalStop
from retry.budget472 import ARM,ChargeLedger472,atomic472
from retry.capture434 import CaptureBarrier

class StorageBarrier472(CaptureBarrier):
    def __init__(self,d,meter):super().__init__(d);self.meter=meter
    def seal(self,*args,**kwargs):self.meter.check_storage();return super().seal(*args,**kwargs)
    def complete(self,*args,**kwargs):self.meter.check_storage();return super().complete(*args,**kwargs)

class Meter472(Meter453):
    HARD_TICKS=9216;HARD_WORLDS=185;SCOPE_TICKS=8738;SCOPE_WORLDS=181
    def __init__(self,d,worker_start=None):
        self.worker_start=WORKER_START if worker_start is None else worker_start
        super().__init__(Path(d));self.phase='INITIALIZED'
        if self.p['scope']!=dict(ticks=8738,worlds=181):raise TechnicalStop('472_scope8738_181')
        expected=dict(ticks=9216,worlds=185,CPU_s=900,wall_s=1200,actual_actions=195,resets=1)
        if any(self.p['caps'].get(k)!=v for k,v in expected.items()):raise TechnicalStop('472_hard_contract')
        self.charge_ledger=ChargeLedger472(self.p,self.d);self.barrier=StorageBarrier472(self.d,self)
    def check_storage(self):
        minimum=max(512*1024**2,int(self.p.get('storage_free_stop_bytes',0)))
        for volume in ('/tmp','/workspace'):
            if shutil.disk_usage(volume).free<minimum:raise ResourceStop('472_storage_'+volume.replace('/','_'))
    def wholetime(self):return time.process_time(),time.perf_counter()-self.worker_start
    def deadline(self):return min(datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')),datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00'))
    def persist(self):
        self.check_storage();mc,mw=self.modeltime();nc,nw=self.nativetime();cpu,wall=self.wholetime();self.b.update(CPU_s=mc,execution_wall_s=mw)
        atomic472(self.d/'budget.json',dict(stage=472,model={**self.b,'regions':self.regions},actual={**self.nb,'CPU_s':nc,'wall_s':nw},wholeworker_CPU_s=cpu,whole_execution_wall_s=wall,exclusive_accounting=True,phase=getattr(self,'phase','INITIALIZED'),pid=os.getpid()))
    def guard(self):
        self.check_storage();cpu,wall=self.wholetime()
        if cpu>=900 or wall>=1200:raise ResourceStop('472_whole_CPU900_wall1200')
        if datetime.datetime.now(datetime.timezone.utc)>=self.deadline():raise ResourceStop('472_deadline')
        self.persist()
    def timers(self):
        cpu,wall=self.wholetime();remaining=(self.deadline()-datetime.datetime.now(datetime.timezone.utc)).total_seconds();c=900-cpu;w=min(1200-wall,remaining)
        signal.setitimer(signal.ITIMER_PROF,max(.001,c));signal.setitimer(signal.ITIMER_REAL,max(.001,w))
    def charge(self,kind,arm):
        if not(self.actual_start and self.active is None and kind in ('reset','action') and arm==ARM):raise TechnicalStop('472_native_scope')
        self.guard();key,ak=('resets','arm_resets') if kind=='reset' else ('actions','arm_actions');cap=1 if kind=='reset' else 195
        if self.nb[key]>=cap or self.nb[ak].get(arm,0)>=cap:raise ResourceStop('472_native_cap_'+kind)
        self.nb[key]+=1;self.nb[ak][arm]=self.nb[ak].get(arm,0)+1
        self.charge_ledger.charge(kind,self.nb);self.persist()
    def capture_inputs(self,*args,**kwargs):self.guard();return super().capture_inputs(*args,**kwargs)
    def world(self,state,tag):
        assert self.active is not None
        self.guard()
        if self.b['worlds']>=self.HARD_WORLDS:raise ResourceStop('472_world_hard185')
        if self.b['worlds']>=self.SCOPE_WORLDS:raise ResourceStop('472_world_scope181')
        return Meter453.world(self,state,tag)
    def step(self,m,act,tag):
        assert self.active is not None
        self.guard()
        if self.b['reserved_ticks']+4>self.HARD_TICKS:raise ResourceStop('472_tick_hard9216')
        if self.b['reserved_ticks']+4>self.SCOPE_TICKS:raise ResourceStop('472_tick_scope8738')
        return Meter442.step(self,m,act,tag)
    def checkpoint(self,phase,**facts):
        self.phase=phase;self.check_storage();mc,mw=self.modeltime();nc,nw=self.nativetime();cpu,wall=self.wholetime()
        q=dict(stage=472,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_actions=self.nb['actions'],resets=self.nb['resets'],arm_actions=dict(self.nb['arm_actions']),model_ticks=self.b['ticks'],model_reserved_ticks=self.b['reserved_ticks'],model_worlds=self.b['worlds'],model_CPU_s=mc,model_wall_s=mw,actual_CPU_s=nc,actual_wall_s=nw,wholeworker_CPU_s=cpu,whole_execution_wall_s=wall,**facts)
        atomic472(self.d/'progress-private.json',q);self.persist();return q
