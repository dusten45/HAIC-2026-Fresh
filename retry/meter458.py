"""458 exclusive model/native caps; unchanged453 constructor and433 step proofs."""
import datetime,os,signal,time
from retry.meter453 import Meter453
from retry.paired442_meter import Meter as Meter442
from retry.pilot420_backend import ResourceStop
from retry.loss389_analyze import save

class Meter458(Meter453):
    def guard(self):
        self.persist();mc,mw=self.modeltime();nc,nw=self.nativetime()
        if mc>=6000 or mw>=9000:raise ResourceStop('458_model_CPU6000_wall9000')
        if nc>=240 or nw>=480:raise ResourceStop('458_actual_exclusive_CPU240_wall480')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):raise ResourceStop('458_deadline')
    def timers(self):
        if self.active:c,w=self.modeltime();limits=(6000-c,9000-w)
        elif self.actual_start:c,w=self.nativetime();limits=(240-c,480-w)
        else:limits=None
        remaining=(datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00'))-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        signal.setitimer(signal.ITIMER_PROF,max(.001,limits[0]) if limits else 0)
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(limits[1],remaining)) if limits else 0)
    def step(self,m,act,tag):
        if self.b['reserved_ticks']+4>212992:raise ResourceStop('458_model_tick212992')
        return Meter442.step(self,m,act,tag)
    def charge(self,kind,arm):
        assert self.actual_start and self.active is None and arm in ['C0','P'] and kind in ['reset','action']
        self.guard();key='resets' if kind=='reset' else 'actions';ak='arm_resets' if kind=='reset' else 'arm_actions';cap=2 if kind=='reset' else 440;armcap=1 if kind=='reset' else 220
        if self.nb[key]>=cap or self.nb[ak].get(arm,0)>=armcap:raise ResourceStop('458_native_cap_'+arm+'_'+kind)
        self.nb[key]+=1;self.nb[ak][arm]=self.nb[ak].get(arm,0)+1;self.persist()
    def checkpoint(self,phase,**facts):
        mc,mw=self.modeltime();nc,nw=self.nativetime();q=dict(stage=458,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_actions=self.nb['actions'],resets=self.nb['resets'],arm_actions=dict(self.nb['arm_actions']),model_ticks=self.b['ticks'],model_reserved_ticks=self.b['reserved_ticks'],model_worlds=self.b['worlds'],model_CPU_s=mc,model_wall_s=mw,actual_CPU_s=nc,actual_wall_s=nw,**facts);save(self.d/'progress-private.json',q);return q
