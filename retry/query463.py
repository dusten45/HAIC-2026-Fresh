"""Frozen whole native policy modes with442 current/pending guardian binding."""
import copy,time
import numpy as np
from retry.compare462 import secant_command
from dataclasses import asdict,replace
from types import SimpleNamespace
from retry.query453 import Query453
from retry.pilot420_backend import capture_context,snapshot,fingerprint,rnghash
from retry.planner419 import Parent,GoalLedger
from retry.fixture438 import check_adapter
from retry.ledger439 import require
from retry.receipt421_io import save_receipt


def mode463(arm,decision,phase,pending):
    require(arm in ['Original','SecantOnce'] and type(decision) is int and 1<=decision<=70,'463_FIXED_ARM_DECISION')
    require(phase in ['FIRST_LAP','FINISH_CONFIRM'] and type(pending) is bool,'463_FIXED_POLICY_PHASE')
    if decision==1:
        require(phase=='FIRST_LAP' and not pending,'463_FIXED_FIRST_DOMAIN')
        return 'FIXED_FIRST','nominal' if arm=='Original' else 'fullgas'
    if pending:return 'REGISTERED_PENDING_GUARDIAN','nominal'
    require(phase=='FIRST_LAP','463_CONFIRM_WITHOUT_REGISTERED_PENDING')
    return 'GUARDIAN','nominal'


class Query463(Query453):
    def __init__(self,root,meter,fixed,pace):
        super().__init__(root,meter,fixed,pace);self.d=meter.d;self.alternatives=[]
        self.policy_digest=fingerprint(dict(rule='463_PRE126_FIXED_ORIGINAL_NOMINAL_SECANT_FULLGAS_ALIAS_ONCE_THEN_SAME_GUARDIAN70',sources=meter.p['semantic_sources']))
    def query_policy(self,history,before,nominal,arm,decision):
        self.history=history;history.require_live();self.children=[];self.alternatives=[];label=arm+'_decision'+str(decision);started=time.process_time();wall=time.perf_counter();pending=None
        with self.meter.model(label):
            proxy,full,adapter=check_adapter(history.env,history.obs,history.ctrl,self.d,label)
            parent=SimpleNamespace(m=proxy,ctrl=history.ctrl);self.full_stamp=fingerprint(full);self.ledger_stamp=history.ledger.digest()
            require(type(history.ledger) is GoalLedger and not history.ledger.done,'463_LIVE_NATIVE_GOAL_LEDGER_REQUIRED')
            ctx=capture_context(proxy,history.ctrl,before,nominal,history.ledger,self.fixed,self.policy_digest,{},history.initial.actual_root_digest)
            src,mem,rng=ctx.parent.fork_inputs();src['provenance']='CURRENT_ACTUAL_PARENT463_READONLY';ctx=replace(ctx,parent=Parent.current(src,mem,rng,ctx.parent.raw_clock_tick))
            has_pending=history.env.unwrapped.finish_line_tracker.candidate_crossing_time_s is not None
            mode,forced_recipe=mode463(arm,decision,history.ctrl.phase(),has_pending);self.active_pending=None
            if has_pending:
                pending=history.pending(ctx,before,self.meter.p['semantic_sources']);route=pending.validate(history,ctx)['gate'];self.active_pending=pending.bridge
                save_receipt(self.d/(label+'-actual-pending-private.json'),asdict(pending))
            else:
                ctx.validate();route=ctx.gate();require(route=='QUERY_CURRENT','463_NONPENDING_CURRENT_ROUTE')
            self.active_context=ctx
            self.meter.query_proof=self.meter.capture_inputs(snapshot(proxy),before,ctx.ledger,label+'_query',context=ctx,gate=route)
            ph,mh,rh=fingerprint(snapshot(proxy)),fingerprint(history.ctrl.memory()),rnghash()
            try:
                if mode.startswith('FIXED_'):
                    expected_secant=secant_command(self.fixed,self.pace,list(proxy.car.hull.position),list(proxy.car.hull.linearVelocity),ctx.nominal) if arm=='SecantOnce' else None
                    selected=self.short_pair(parent,ctx,before,label,forced_recipe)
                    if expected_secant is not None:require(np.array_equal(np.asarray(selected['first']['command'],np.float32),expected_secant),'463_SECANT_SELECTED_FULL_VECTOR_EXACT')
                    require(selected['valid'],'463_FIXED_POLICY_COMMAND_INELIGIBLE_NO_FALLBACK')
                else:selected=self.guardian(parent,ctx,before,label)
            finally:
                for c in self.children:
                    if not c.closed:c.dump(self.d);c.close()
            self.unchanged(parent,ph,mh,rh)
            if pending:pending.validate(history,ctx)
            record=dict(arm=arm,relative_decision=decision,mode=mode,fixed_first=decision==1,phase=history.ctrl.phase(),route=route,selected_recipe=selected['recipe'],alternatives=copy.deepcopy(self.alternatives),guardian_certificate=selected['certificate'],actual_done_before_step=history.ledger.done,model_authorizes_actual_DONE=False,parent_memory_RNG_ledger_unchanged=True,canonical_adapter=adapter)
            save_receipt(self.d/(label+'-before-actual-dispatch-private.json'),dict(context=asdict(ctx),query_proof=self.meter.query_proof,selected_first=selected['first'],record=record,actual_dispatch_authorization='EXPLICIT463_FIXED125_PREFIX_ONE_SECANT_NATIVE_PAIR_CHARGE_AND_OWN_FACTS_ONLY'))
        record.update(query_CPU_s=time.process_time()-started,query_wall_s=time.perf_counter()-wall);self.meter.queries.append(record)
        return selected['first'],record,pending
