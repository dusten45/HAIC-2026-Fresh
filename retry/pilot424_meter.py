"""Model-only424 caps; unchanged420 Child/physics implementation."""
import datetime,time
from retry.pilot420_backend import ResourceStop,TechnicalStop,TerminalVehicleTransition
from retry.loss389_analyze import read,save
class Meter:
 def __init__(self,d):
  self.d=d;self.p=read(d/'plan.json');self.wall=time.perf_counter();self.b=dict(ticks=0,reserved_ticks=0,worlds=0,confirmed_worlds=0,ticks_by_tag={},worlds_by_tag={},CPU_by_tag={},wall_by_tag={},max_live_worlds=0);self.live=[]
 def persist(self):self.b.update(CPU_s=time.process_time(),execution_wall_s=time.perf_counter()-self.wall);save(self.d/'budget.json',self.b)
 def guard(self):
  self.persist()
  if time.process_time()>=600 or time.perf_counter()-self.wall>=900:raise ResourceStop('CPU600_wall900')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):raise ResourceStop('deadline')
 def timing(self,tag,c,w):
  self.b['CPU_by_tag'][tag]=self.b['CPU_by_tag'].get(tag,0)+time.process_time()-c;self.b['wall_by_tag'][tag]=self.b['wall_by_tag'].get(tag,0)+time.perf_counter()-w
 def world(self,state,tag):
  self.guard()
  if self.b['worlds']>=256:raise ResourceStop('world256')
  self.b['worlds']+=1;self.b['worlds_by_tag'][tag]=self.b['worlds_by_tag'].get(tag,0)+1;self.persist();c=time.process_time();w=time.perf_counter()
  try:m=TerminalVehicleTransition(state)
  finally:self.timing(tag+'_world_setup',c,w)
  self.live.append(m);self.b['confirmed_worlds']+=1;self.b['max_live_worlds']=max(self.b['max_live_worlds'],len(self.live));self.persist()
  if not(m.initial_bodies_exact and m.initial_tiles_exact and m.initial_progress_exact and m.initial_finish_exact):raise TechnicalStop('restore_body_tile_progress_finish')
  return m
 def step(self,m,act,tag):
  self.guard()
  if self.b['reserved_ticks']+4>131072:raise ResourceStop('tick131072')
  self.b['reserved_ticks']+=4;self.persist();before=m.native_ticks;c=time.process_time();w=time.perf_counter();success=False
  try:q=m.step(act);success=True;return q
  finally:
   count=m.native_ticks-before;self.b['ticks']+=count;self.b['ticks_by_tag'][tag]=self.b['ticks_by_tag'].get(tag,0)+count
   if success:self.b['reserved_ticks']-=4-count
   self.timing(tag,c,w);self.persist()
 def close(self,m):
  if m in self.live:self.live.remove(m);m.close()
 def closeall(self):
  for m in list(self.live):self.close(m)
  self.persist()
