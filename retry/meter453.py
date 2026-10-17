"""453 exclusive budgets with charge-before-call and1792-world source registry."""
import datetime,os,signal,time,copy
from retry.paired442_meter import Meter as Meter442
from retry.pilot420_backend import ResourceStop,TechnicalStop,TerminalVehicleTransition,rnghash
from retry.loss389_analyze import save,sha
from retry.receipt421_io import save_receipt

class Meter453(Meter442):
    def guard(self):
        self.persist();mc,mw=self.modeltime();nc,nw=self.nativetime()
        if mc>=3000 or mw>=4200:raise ResourceStop('453_model_CPU3000_wall4200')
        if nc>=240 or nw>=480:raise ResourceStop('453_actual_CPU240_wall480')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):raise ResourceStop('453_deadline')
    def timers(self):
        if self.active:c,w=self.modeltime();limits=(3000-c,4200-w)
        elif self.actual_start:c,w=self.nativetime();limits=(240-c,480-w)
        else:limits=None
        signal.setitimer(signal.ITIMER_PROF,max(.001,limits[0]) if limits else 0);signal.setitimer(signal.ITIMER_REAL,max(.001,limits[1]) if limits else 0)
    def charge(self,kind,arm):
        assert self.actual_start and self.active is None and arm in ['baseline','candidate'] and kind in ['reset','action']
        self.guard();key='resets' if kind=='reset' else 'actions';ak='arm_resets' if kind=='reset' else 'arm_actions';cap=2 if kind=='reset' else 440;armcap=1 if kind=='reset' else 220
        if self.nb[key]>=cap or self.nb[ak].get(arm,0)>=armcap:raise ResourceStop('453_native_cap_'+arm+'_'+kind)
        self.nb[key]+=1;self.nb[ak][arm]=self.nb[ak].get(arm,0)+1;self.persist()
    def world(self,state,tag):
        # Same433 input proof +428 constructor/restore logic; explicit1792 cap
        # avoids inheriting428's narrower1024 cap. Physics class is unchanged.
        assert self.active is not None
        if self.inputs is None:raise TechnicalStop('missing_preconstructor_input_proof')
        self.guard()
        if self.b['worlds']>=1792:raise ResourceStop('453_world1792')
        self.sequence+=1;number=self.sequence
        proof=dict(sequence=number,tag=tag,input_proof=self.inputs,state=copy.deepcopy(state),global_RNG_digest=rnghash(),restore_gate='NOT_YET_CONSTRUCTED',new_actual_actions=0)
        path=self.d/('world'+str(number)+'-before-constructor-private.json');save_receipt(path,proof)
        self.b['worlds']+=1;self.b['worlds_by_tag'][tag]=self.b['worlds_by_tag'].get(tag,0)+1;self.persist();cpu=time.process_time();wall=time.perf_counter()
        try:m=TerminalVehicleTransition(state)
        finally:self.timing(tag+'_world_setup',cpu,wall)
        self.live.append(m);self.b['confirmed_worlds']+=1;self.b['max_live_worlds']=max(self.b['max_live_worlds'],len(self.live));self.persist()
        if rnghash()!=proof['global_RNG_digest']:raise TechnicalStop('world_constructor_global_RNG_mutation')
        gates=dict(bodies=m.initial_bodies_exact,tiles=m.initial_tiles_exact,progress=m.initial_progress_exact,finish=m.initial_finish_exact)
        if not all(gates.values()):raise TechnicalStop('restore_body_tile_progress_finish')
        self.auth[id(m)]=dict(number=number,input_proof=self.inputs,constructor_proof_sha256=sha(path),restore_gates=gates,first_step=False)
        return m
    def step(self,m,act,tag):
        if self.b['reserved_ticks']+4>98304:raise ResourceStop('453_model_ticks98304')
        return super().step(m,act,tag)
    def checkpoint(self,phase,**facts):
        mc,mw=self.modeltime();nc,nw=self.nativetime();q=dict(stage=453,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),actual_actions=self.nb['actions'],resets=self.nb['resets'],arm_actions=dict(self.nb['arm_actions']),model_ticks=self.b['ticks'],model_reserved_ticks=self.b['reserved_ticks'],model_worlds=self.b['worlds'],model_CPU_s=mc,model_wall_s=mw,actual_CPU_s=nc,actual_wall_s=nw,**facts);save(self.d/'progress-private.json',q);return q
