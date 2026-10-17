"""448 explicit caps on the existing exclusive native/model charge boundary."""
import datetime,os,signal,time
from retry.paired442_meter import Meter as Meter442
from retry.pilot420_backend import ResourceStop
from retry.loss389_analyze import save

class Meter448(Meter442):
    def guard(self):
        self.persist();mc,mw=self.modeltime();nc,nw=self.nativetime()
        if mc>=180 or mw>=300:raise ResourceStop('448_model_CPU180_wall300')
        if nc>=90 or nw>=180:raise ResourceStop('448_actual_CPU90_wall180')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):raise ResourceStop('448_deadline')
    def timers(self):
        if self.active:
            c,w=self.modeltime();limits=(180-c,300-w)
        elif self.actual_start:
            c,w=self.nativetime();limits=(90-c,180-w)
        else:limits=None
        signal.setitimer(signal.ITIMER_PROF,max(.001,limits[0]) if limits else 0)
        signal.setitimer(signal.ITIMER_REAL,max(.001,limits[1]) if limits else 0)
    def charge(self,kind,arm):
        assert kind in ['reset','action'] and arm in ['nominal','fullgas']
        assert self.actual_start and self.active is None
        self.guard();key='resets' if kind=='reset' else 'actions';ak='arm_resets' if kind=='reset' else 'arm_actions'
        cap=2 if kind=='reset' else 96;armcap=1 if kind=='reset' else 48
        if self.nb[key]>=cap or self.nb[ak].get(arm,0)>=armcap:raise ResourceStop('448_actual_call_cap_'+arm+'_'+kind)
        self.nb[key]+=1;self.nb[ak][arm]=self.nb[ak].get(arm,0)+1;self.persist()
    def world(self,state,tag):
        if self.b['worlds']>=128:raise ResourceStop('448_world128')
        return super().world(state,tag)
    def step(self,m,act,tag):
        if self.b['reserved_ticks']+4>6144:raise ResourceStop('448_model_tick6144')
        return super().step(m,act,tag)
    def checkpoint(self,phase,**facts):
        mc,mw=self.modeltime();nc,nw=self.nativetime()
        q=dict(stage=448,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_actions=self.nb['actions'],resets=self.nb['resets'],arm_actions=dict(self.nb['arm_actions']),model_ticks=self.b['ticks'],model_reserved_ticks=self.b['reserved_ticks'],worlds=self.b['worlds'],actual_CPU_s=nc,actual_wall_s=nw,model_CPU_s=mc,model_wall_s=mw,**facts)
        save(self.d/'progress-private.json',q);return q
