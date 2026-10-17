"""Exclusive model and actual accounting; reserve before every dispatched call."""
import time
WORKER_START=time.perf_counter()
import contextlib,datetime,signal
from retry.pilot436_meter import Meter as ModelMeter
from retry.pilot420_backend import ResourceStop
from retry.loss389_analyze import save
from retry.progress442 import checkpoint
class Meter(ModelMeter):
 def __init__(self,d):
  super().__init__(d);self.mb=self.b;self.active=None;self.mc=time.process_time();self.mw=time.perf_counter()-WORKER_START;self.actual_start=None;self.model_base=None;self.regions=[];self.nb=dict(actions=0,resets=0,arm_actions={},arm_resets={},CPU_s=0.,wall_s=0.);self.queries=[]
 def modeltime(self):return self.mc+(time.process_time()-self.active[0] if self.active else 0),self.mw+(time.perf_counter()-self.active[1] if self.active else 0)
 def nativetime(self):
  if self.actual_start is None:return self.nb['CPU_s'],self.nb['wall_s']
  c,w=self.modeltime();return time.process_time()-self.actual_start[0]-(c-self.model_base[0]),time.perf_counter()-self.actual_start[1]-(w-self.model_base[1])
 def persist(self):
  mc,mw=self.modeltime();nc,nw=self.nativetime();self.b.update(CPU_s=mc,execution_wall_s=mw);save(self.d/'budget.json',dict(model={**self.b,'regions':self.regions},actual={**self.nb,'CPU_s':nc,'wall_s':nw},wholeworker_CPU_s=time.process_time(),whole_execution_wall_s=time.perf_counter()-WORKER_START,exclusive_accounting=True))
 def guard(self):
  self.persist();mc,mw=self.modeltime();nc,nw=self.nativetime()
  if mc>=1800 or mw>=2400:raise ResourceStop('modelCPU1800_wall2400')
  if nc>=240 or nw>=480:raise ResourceStop('actualCPU240_wall480')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):raise ResourceStop('deadline')
 def timers(self):
  if self.active:c,w=self.modeltime();limits=(1800-c,2400-w)
  elif self.actual_start:c,w=self.nativetime();limits=(240-c,480-w)
  else:limits=None
  signal.setitimer(signal.ITIMER_PROF,max(.001,limits[0]) if limits else 0);signal.setitimer(signal.ITIMER_REAL,max(.001,limits[1]) if limits else 0)
 @contextlib.contextmanager
 def model(self,label):
  assert self.active is None;self.guard();self.active=time.process_time(),time.perf_counter();self.timers()
  try:yield
  finally:
   self.mc+=time.process_time()-self.active[0];self.mw+=time.perf_counter()-self.active[1];self.regions.append(dict(label=label,CPU_s=time.process_time()-self.active[0],wall_s=time.perf_counter()-self.active[1]));self.active=None;self.timers();self.persist()
 def begin_actual(self):
  assert self.actual_start is None and self.active is None;self.actual_start=time.process_time(),time.perf_counter();self.model_base=self.modeltime();self.timers();self.persist()
 def end_actual(self):
  if self.actual_start:self.nb['CPU_s'],self.nb['wall_s']=self.nativetime();self.actual_start=None;self.timers();self.persist()
 def charge(self,kind,arm):
  assert self.actual_start and self.active is None;self.guard();key='resets' if kind=='reset' else 'actions';cap=2 if key=='resets' else 416;armcap=1 if key=='resets' else (198 if arm=='C0' else 218);ak='arm_resets' if key=='resets' else 'arm_actions'
  if self.nb[key]>=cap or self.nb[ak].get(arm,0)>=armcap:raise ResourceStop('actual_call_cap_'+arm+'_'+key)
  self.nb[key]+=1;self.nb[ak][arm]=self.nb[ak].get(arm,0)+1;self.persist()
 def checkpoint(self,phase,**facts):
  mc,mw=self.modeltime();nc,nw=self.nativetime();return checkpoint(self.d,phase,actual_actions=self.nb['actions'],actual_resets=self.nb['resets'],actual_arm_actions=dict(self.nb['arm_actions']),model_ticks=self.b['ticks'],model_reserved_ticks=self.b['reserved_ticks'],model_worlds=self.b['worlds'],actual_CPU_s=nc,actual_wall_s=nw,model_CPU_s=mc,model_wall_s=mw,**facts)
 def world(self,state,tag):
  assert self.active is not None;return super().world(state,tag)
 def step(self,m,act,tag):
  assert self.active is not None;return super().step(m,act,tag)
