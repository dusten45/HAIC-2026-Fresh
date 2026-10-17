"""A separate guarded policy segment on an unchanged live model parent."""
import copy
from dataclasses import dataclass,asdict
import numpy as np
from retry.observer435 import Child
from retry.pilot420_backend import snapshot,fingerprint,rnghash,model_ledger_view
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
from retry.ledger439 import require,compare_ledgers
from retry.geometry439 import Projection439,Interval
from retry.pilot421_run import compare_frames
from retry.receipt421_io import save_receipt

class Segment451Error(ValueError):pass

def forbidden_nominal451(*args,**kwargs):
    raise Segment451Error('451_GUARDED_SEGMENT_CANNOT_USE_NOMINAL_TAIL_OR_RANKING')

@dataclass(frozen=True)
class Segment451:
    child:object
    world:object
    stream:object
    actual:object
    actual_digest:str
    prefix_actions:int
    prefix_digest:str
    prefix_clock:int
    prefix_native_ticks:int
    def validate(self,c,actual):
        require(c is self.child and c.m is self.world and c.stream is self.stream,'451_SEGMENT_OWNER_WORLD_STREAM')
        require(actual is self.actual and actual.digest()==self.actual_digest,'451_IMMUTABLE_NATIVE_ROOT_OWNER')
        require(type(c.ledger) is ForecastLedger and c.ledger.actual_root_digest==self.actual_digest,'451_PARENT_MODEL_CHANNEL')
        require(fingerprint(c.rows[:self.prefix_actions])==self.prefix_digest,'451_NOMINAL_PREFIX_MUTATED')
        count=len(c.rows)-self.prefix_actions
        require(0<=count<=14 and c.ledger.last_clock_tick==round(c.m.t*50),'451_SEGMENT_CAP_OR_CLOCK')
        ticks=sum(r['predicted']['raw_ticks'] for r in c.rows[self.prefix_actions:])
        require(c.m.native_ticks==self.prefix_native_ticks+ticks and c.ledger.last_clock_tick==self.prefix_clock+ticks,'451_UNRECORDED_PARENT_STEPS')
        c.stream.require_owner(c)
        return self

class Parent451(Child):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.segment451=None;self._selected451=False
    def begin_guarded(self,actual,directory):
        require(self.segment451 is None and self.status=='ACTIVE' and 13<len(self.rows)<=64,'451_GUARD_BEGIN_POINT')
        prefix=self.stream.tail_record()
        save_receipt(directory/(self.label+'-nominal-prefix270-private.json'),dict(tail=asdict(prefix),rows=self.rows,snapshot=snapshot(self.m),memory=self.ctrl.memory(),ledger=asdict(self.ledger),RNG_digest=rnghash(),actual_native_ledger=asdict(actual),scope='SEALED_NOMINAL_FINITE_PREFIX_ONLY_NOT_B_COMPLETION'))
        self.segment451=Segment451(self,self.m,self.stream,actual,actual.digest(),len(self.rows),fingerprint(self.rows),self.ledger.last_clock_tick,self.m.native_ticks)
        self.stream.tail_record=forbidden_nominal451
        self.segment451.validate(self,actual)
        return self.segment451
    def one(self,*args,**kwargs):
        if self.segment451 is not None and not self._selected451:
            raise Segment451Error('451_GUARDED_STEP_REQUIRES_CURRENT_SELECTION')
        return super().one(*args,**kwargs)
    def evidence(self,*args,**kwargs):
        if self.segment451 is not None:return forbidden_nominal451()
        return super().evidence(*args,**kwargs)
    def continue_tail(self,*args,**kwargs):
        if self.segment451 is not None:return forbidden_nominal451()
        return super().continue_tail(*args,**kwargs)
    def guarded_one(self,query,actual,selected,nominal,before,tag):
        self.segment451.validate(self,actual);query.validate(self,actual)
        require(len(self.rows)-self.segment451.prefix_actions<14,'451_B14_CAP')
        old=model_ledger_view(self.ledger);first=selected['first'];expected=np.asarray(nominal,np.float32).copy()
        if selected['recipe']=='neutralbrake':expected=np.asarray([0.,0.,.3],np.float32)
        else:require(selected['recipe']=='nominal','451_NO_OTHER_RECIPE')
        require(first['command']==expected.tolist() and first['actual_root_ledger_digest']==query.context.ledger.digest(),'451_SELECTED_CURRENT_COMMAND_OR_VALUE_VIEW')
        self._selected451=True
        try:self.one(tag,first_override=first['command'],prepared_nominal=nominal,prepared_before=before)
        finally:self._selected451=False
        own=self.rows[-1];check=compare_frames(own,first)
        require(check['passed'] and not check['wheel']['clipped_flag_mismatches'],'451_PARENT_SELECTED_FIRST_FIDELITY')
        require(all(own[k]==first[k] for k in ['command','memory_before','memory_after']),'451_SELECTED_CURRENT_MEMORY')
        require(all(own['raw_hull'][0][k]==first['raw_hull'][0][k] for k in ['origin_position','COM_linear_velocity','angle','yaw','time']),'451_SHADOW_CURRENT_RESTORE_INPUT')
        require(self.status=='ACTIVE' and not own['safety'] and not self.ledger.deadline_missed and not self.ledger.done,'451_SELECTED_PARENT_SAFETY_PROGRESS_TERMINAL')
        geometry=Projection439(self.fixed['line'],sum(self.fixed['free_profile']['ds']),.1)
        pose=lambda h:dict(pos=h['origin_position'],vel=h['COM_linear_velocity'])
        post=lambda r:dict(pos=r['predicted']['position'],vel=r['predicted']['velocity'])
        transition=geometry.transition(pose(own['raw_hull'][0]),post(own),pose(first['raw_hull'][0]),post(first),before['C']['phase'],own['memory_after']['C']['phase'])
        bound=geometry.progress_interval(Interval.point(old.progress_m),transition)
        shadow_old=ForecastLedger.fork(old)
        shadow=shadow_old.advance_prediction(ModelPrediction(first['model_progress'],round(first['predicted']['time']*50),first['predicted']['finished']))
        require(shadow.goal_m==first['model_goal'] and shadow.age_actions==first['model_age'],'451_SHADOW_LEDGER_SELF_CONSISTENCY')
        ledger_proof,_=compare_ledgers(old,model_ledger_view(self.ledger),shadow_old,shadow,self.ledger.progress_m>=old.goal_m,shadow.progress_m>=old.goal_m,bound,Interval.point(old.goal_m))
        self.segment451.validate(self,actual)
        return dict(physical=check,ledger=ledger_proof,model_native_authority=False)
    def dump(self,d):
        super().dump(d)
        if self.segment451 is not None:
            from retry.loss389_analyze import read,save
            path=d/(self.label+'-private.json');value=read(path)
            value.update(policy='NOMINAL_PREFIX_THEN_CONDITIONAL_B_MODEL_ONLY',nominal_prefix_actions=self.segment451.prefix_actions,guarded_actions=len(self.rows)-self.segment451.prefix_actions,nominal_tail_ranking_forbidden=True,actual_DONE_allowed=False)
            save(path,value)
