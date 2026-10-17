"""Frozen whole native policy modes with442 current/pending guardian binding."""
import copy,time
from dataclasses import asdict,replace
from types import SimpleNamespace
from retry.paired442_query import Query442
from retry.pilot420_backend import capture_context,snapshot,fingerprint,rnghash
from retry.planner419 import Parent,GoalLedger
from retry.fixture438 import check_adapter
from retry.ledger439 import require
from retry.receipt421_io import save_receipt


def mode453(arm,decision,B_started,phase,pending):
    require(arm in ['baseline','candidate'] and type(decision) is int and 1<=decision<=198,'453_FIXED_ARM_DECISION')
    require(phase in ['FIRST_LAP','FINISH_CONFIRM'],'453_FIXED_POLICY_PHASE')
    if pending:
        require(B_started,'453_PENDING_BEFORE270');return 'REGISTERED_PENDING_B','nominal'
    require(phase=='FIRST_LAP','453_CONFIRM_WITHOUT_REGISTERED_PENDING')
    if arm=='candidate' and decision==1:
        require(not B_started,'453_PULSE_ONLY_AT_ORIGINAL_ROOT');return 'FIXED_FIRST_PULSE','fullgas'
    return ('CONDITIONAL_B','nominal') if B_started else ('FIXED_NOMINAL_TO270','nominal')


class Query453(Query442):
    def __init__(self,root,meter,fixed,pace):
        super().__init__(root,meter,fixed,pace);self.d=meter.d;self.alternatives=[]
        self.policy_digest=fingerprint(dict(rule='453_FIRST_PULSE_CANDIDATE_NOMINAL270_THEN_B_REGISTERED_NATIVE_FINISH',sources=meter.p['semantic_sources']))
    def short_pair(self,parent,ctx,before,label,recipe):
        require(type(ctx.ledger) is GoalLedger and ctx.ledger==self.history.ledger,'453_CURRENT_NATIVE_LEDGER_VALUE')
        start=len(self.children);result=super().short_pair(parent,ctx,before,label,recipe)
        for child in self.children[start:]:
            require(child.status in ['ACTIVE','FINISHED','UNSAFE','INFEASIBLE'],'453_UNREGISTERED_ALTERNATIVE_TERMINAL')
            if child.status=='INFEASIBLE':require(child.error=='predicted_progress_deadline' and child.ledger.deadline_missed,'453_UNREGISTERED_PROGRESS_REJECTION')
            if child.status=='FINISHED':require(child.guardian_certificate and child.guardian_certificate['model_confirmation_qualified'] and not child.guardian_certificate['actual_done_allowed'],'453_FINISHED_SHADOW_NOT_REGISTERED_MODEL_CONFIRMATION')
        self.alternatives.append(dict(recipe=recipe,valid=result['valid'],certificate=result['certificate']))
        return result
    def query_policy(self,history,before,nominal,arm,decision,B_started):
        self.history=history;history.require_live();self.children=[];self.alternatives=[];label=arm+'_decision'+str(decision);started=time.process_time();wall=time.perf_counter();pending=None
        with self.meter.model(label):
            proxy,full,adapter=check_adapter(history.env,history.obs,history.ctrl,self.d,label)
            parent=SimpleNamespace(m=proxy,ctrl=history.ctrl);self.full_stamp=fingerprint(full);self.ledger_stamp=history.ledger.digest()
            require(type(history.ledger) is GoalLedger and not history.ledger.done,'453_LIVE_NATIVE_GOAL_LEDGER_REQUIRED')
            ctx=capture_context(proxy,history.ctrl,before,nominal,history.ledger,self.fixed,self.policy_digest,{},history.initial.actual_root_digest)
            src,mem,rng=ctx.parent.fork_inputs();src['provenance']='CURRENT_ACTUAL_PARENT453_READONLY';ctx=replace(ctx,parent=Parent.current(src,mem,rng,ctx.parent.raw_clock_tick))
            has_pending=history.env.unwrapped.finish_line_tracker.candidate_crossing_time_s is not None
            mode,forced_recipe=mode453(arm,decision,B_started,history.ctrl.phase(),has_pending);self.active_pending=None
            if has_pending:
                pending=history.pending(ctx,before,self.meter.p['semantic_sources']);route=pending.validate(history,ctx)['gate'];self.active_pending=pending.bridge
                save_receipt(self.d/(label+'-actual-pending-private.json'),asdict(pending))
            else:
                ctx.validate();route=ctx.gate();require(route=='QUERY_CURRENT','453_NONPENDING_CURRENT_ROUTE')
            self.active_context=ctx
            self.meter.query_proof=self.meter.capture_inputs(snapshot(proxy),before,ctx.ledger,label+'_query',context=ctx,gate=route)
            ph,mh,rh=fingerprint(snapshot(proxy)),fingerprint(history.ctrl.memory()),rnghash()
            try:
                if mode.startswith('FIXED_'):
                    selected=self.short_pair(parent,ctx,before,label,forced_recipe)
                    require(selected['valid'],'453_FIXED_POLICY_COMMAND_INELIGIBLE_NO_FALLBACK')
                else:selected=self.guardian(parent,ctx,before,label)
            finally:
                for c in self.children:
                    if not c.closed:c.dump(self.d);c.close()
            self.unchanged(parent,ph,mh,rh)
            if pending:pending.validate(history,ctx)
            record=dict(arm=arm,relative_decision=decision,mode=mode,B_started=B_started,phase=history.ctrl.phase(),route=route,selected_recipe=selected['recipe'],alternatives=copy.deepcopy(self.alternatives),guardian_certificate=selected['certificate'],actual_done_before_step=history.ledger.done,model_authorizes_actual_DONE=False,parent_memory_RNG_ledger_unchanged=True,canonical_adapter=adapter)
            save_receipt(self.d/(label+'-before-actual-dispatch-private.json'),dict(context=asdict(ctx),query_proof=self.meter.query_proof,selected_first=selected['first'],record=record,actual_dispatch_authorization='EXPLICIT453_FIXED_KNOWN_DEV_PAIR_NATIVE_CHARGE_AND_OWN_FACTS_ONLY'))
        record.update(query_CPU_s=time.process_time()-started,query_wall_s=time.perf_counter()-wall);self.meter.queries.append(record)
        return selected['first'],record,pending
