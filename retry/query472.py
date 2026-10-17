"""472 fixed P4 native-current H13 pairs; no old-nominal continuation or selector."""
import copy,time
from dataclasses import asdict,replace
from types import SimpleNamespace
import numpy as np
from retry.paired442_query import Query442
from retry.law468 import profile_inputs468,PROJECTED,PROJECTED_SHA
from retry.observer435 import GuardianChild
from retry.parent436 import guardian_proof
from retry.pilot420_backend import capture_context,snapshot,fingerprint,rnghash,TechnicalStop
from retry.planner419 import Parent,GoalLedger
from retry.fixture438 import check_adapter
from retry.ledger439 import require
from retry.receipt421_io import save_receipt

RULE='472_P4_POINT_FF_EVERY_BOUNDARY_SINGLE_GLOBAL126_FULLGAS_NATIVE_FINISH'


def inject_p4_nodes472(ctrl,nodes):
    """Explicit profile injection before current act; no memory/state reset."""
    vector=np.asarray(nodes,float).copy()
    require(vector.ndim==1 and len(vector)==len(ctrl.policy.nodes) and np.isfinite(vector).all() and vector[0]==0 and np.all(vector[1:]>0),'472_P4_NODE_DOMAIN')
    before=copy.deepcopy(ctrl.memory());vector.setflags(write=False);ctrl.policy.nodes=vector
    require(ctrl.memory()==before and not ctrl.policy.nodes.flags.writeable,'472_NODE_INJECTION_MEMORY_CHANGED')
    return fingerprint(vector.tolist())


def mode472(arm,decision,phase,pending):
    require(arm==PROJECTED and type(decision) is int and 1<=decision<=70,'472_FIXED_SCOPE')
    require(phase in ['FIRST_LAP','FINISH_CONFIRM'] and type(pending) is bool,'472_FIXED_PHASE')
    if decision==1:require(phase=='FIRST_LAP' and not pending,'472_FIRST_ROOT_DOMAIN')
    if pending:return 'P4_REGISTERED_PENDING',False
    require(phase=='FIRST_LAP','472_CONFIRM_WITHOUT_PENDING')
    return 'P4_CURRENT',decision==1


def p4_one472(child,nodes,nodes_digest,force_first,tag):
    require(child.ctrl.phase() in ['FIRST_LAP','FINISH_CONFIRM'],'472_SHADOW_PHASE')
    require(not child.ctrl.policy.nodes.flags.writeable and fingerprint(child.ctrl.policy.nodes.tolist())==nodes_digest and np.array_equal(child.ctrl.policy.nodes,nodes),'472_SHADOW_NODES_CHANGED')
    before=copy.deepcopy(child.ctrl.memory());nominal=child.ctrl.act(child.m);command=np.asarray(nominal,np.float32).copy()
    if force_first:
        require(not child.rows and child.ctrl.phase()=='FIRST_LAP','472_PULSE_ONLY_GLOBAL126')
        fullgas=command.copy();fullgas[1:]=[1.,0.]
        require(np.array_equal(command,fullgas),'472_FIRST_NATURAL_FULLGAS_ALIAS');command=fullgas
    after=copy.deepcopy(child.ctrl.memory());n=len(child.rows)
    child.one(tag,first_override=command,prepared_nominal=nominal,prepared_before=before)
    if len(child.rows)==n+1:
        row=child.rows[-1]
        require(row['memory_before']==before and row['memory_after']==after and (child.ctrl.memory()==after or child.status=='FINISHED'),'472_SHADOW_MEMORY_ONCE')
        require(np.array_equal(np.asarray(row['command'],np.float32),command),'472_SHADOW_COMMAND_CHANGED')
    require(not child.ctrl.policy.nodes.flags.writeable and fingerprint(child.ctrl.policy.nodes.tolist())==nodes_digest,'472_SHADOW_NODES_AFTER_STEP')


class Query472(Query442):
    def __init__(self,root,meter,fixed,pace):
        super().__init__(root,meter,fixed,pace);self.d=meter.d
        _,nodes,path=profile_inputs468(root,fixed,pace);self.nodes=nodes.copy();self.nodes.setflags(write=False)
        self.nodes_digest=fingerprint(nodes.tolist());self.profile_path=path
        self.policy_digest=fingerprint(dict(rule=RULE,profile_sha256=PROJECTED_SHA,nodes_digest=self.nodes_digest,sources=meter.p['semantic_sources']))
    def check_policy(self,ctrl):
        require(not self.nodes.flags.writeable and fingerprint(self.nodes.tolist())==self.nodes_digest,'472_FIXED_NODES_CHANGED')
        require(not ctrl.policy.nodes.flags.writeable and np.array_equal(ctrl.policy.nodes,self.nodes),'472_CURRENT_P4_PROFILE_REQUIRED')
        require(self.policy_digest==fingerprint(dict(rule=RULE,profile_sha256=PROJECTED_SHA,nodes_digest=self.nodes_digest,sources=self.meter.p['semantic_sources'])),'472_POLICY_DIGEST_CHANGED')
    def p4_pair(self,parent,ctx,before,label,force_first):
        require(type(ctx.ledger) is GoalLedger and ctx.ledger==self.history.ledger,'472_CURRENT_NATIVE_LEDGER')
        state=snapshot(parent.m);ph,mh,rh=fingerprint(state),fingerprint(parent.ctrl.memory()),rnghash();pair=[]
        for rep in [1,2]:
            childlabel=label+'_P4_'+str(rep)
            save_receipt(self.d/(childlabel+'-own-policy-before-constructor-private.json'),dict(rule=RULE,policy_digest=self.policy_digest,nodes_digest=self.nodes_digest,nodes=self.nodes.tolist(),profile_sha256=PROJECTED_SHA,current_native_clock=ctx.ledger.last_clock_tick,force_global126_first=force_first,actual_DONE_allowed=False))
            self.meter.capture_inputs(state,before,ctx.ledger,childlabel+'_inputs',context=ctx,gate='472_CURRENT_P4_PAIR:'+self.policy_digest)
            # "nominal" binds the exact CURRENT P4 command for the existing
            # pending proof only. No419 Evidence/ranking receipt is produced.
            c=GuardianChild(self.meter,copy.deepcopy(state),copy.deepcopy(before),ctx.ledger,self.fixed,self.pace,childlabel,'nominal','472_policy_required' if rep==1 else '472_policy_repeat',confirmation_phase=parent.ctrl.phase());self.children.append(c)
            inject_p4_nodes472(c.ctrl,self.nodes)
            while c.status=='ACTIVE' and len(c.rows)<13:
                p4_one472(c,self.nodes,self.nodes_digest,force_first and not c.rows,'472_policy_H13')
            c.initial_count=len(c.rows)
            require(bool(c.rows),'472_SHADOW_NO_OBSERVED_FIRST')
            c.end13=c._end_vector();c.initial_ok=len(c.rows)==13 or c.status=='FINISHED';c.initial_safe=not any(r['safety'] for r in c.rows);c.initial_progress=c.ledger.progress_qualified()
            self.validate_child(c)
            require(c.status in ['ACTIVE','FINISHED','UNSAFE','INFEASIBLE'],'472_UNSUPPORTED_SHADOW_STATUS')
            if c.status=='INFEASIBLE':
                if len(c.rows)<13:raise TechnicalStop('472_UNSUPPORTED_EARLY_PROGRESS')
                require(c.error=='predicted_progress_deadline' and c.ledger.deadline_missed,'472_UNREGISTERED_PROGRESS_REJECTION')
            if c.status=='FINISHED':require(c.guardian_certificate and c.guardian_certificate['model_confirmation_qualified'] and not c.guardian_certificate['actual_done_allowed'],'472_UNREGISTERED_MODEL_FINISH')
            c.dump(self.d);self.unchanged(parent,ph,mh,rh);self.check_policy(parent.ctrl);pair.append(c)
        require(pair[0].signature()==pair[1].signature(),'472_P4_H13_REPEAT')
        valid=all(c.initial_ok and c.initial_safe and c.initial_progress and c.status in ['ACTIVE','FINISHED'] for c in pair)
        if self.active_pending is not None and valid:
            for c in pair:save_receipt(self.d/(c.label+'-pending-policy-proof-private.json'),asdict(guardian_proof(self.active_pending,c,True)))
        result=dict(valid=valid,first=copy.deepcopy(pair[0].rows[0]),certificate=pair[0].guardian_certificate,status=pair[0].status,observed_actions=len(pair[0].rows),independent_repeat_exact=True,all_future_actions_use_P4=True)
        for c in pair:self.close_saved(c)
        return result
    def query_policy(self,history,before,nominal,arm,decision):
        self.history=history;history.require_live();self.check_policy(history.ctrl);self.children=[];label=arm+'_decision'+str(decision);started=time.process_time();wall=time.perf_counter();pending=None
        require(history.native.global_step==125+decision,'472_NATIVE_GLOBAL_STEP')
        with self.meter.model(label):
            proxy,full,adapter=check_adapter(history.env,history.obs,history.ctrl,self.d,label)
            parent=SimpleNamespace(m=proxy,ctrl=history.ctrl);self.full_stamp=fingerprint(full);self.ledger_stamp=history.ledger.digest()
            require(type(history.ledger) is GoalLedger and not history.ledger.done,'472_LIVE_NATIVE_GOAL_LEDGER_REQUIRED')
            ctx=capture_context(proxy,history.ctrl,before,nominal,history.ledger,self.fixed,self.policy_digest,{},history.initial.actual_root_digest)
            src,mem,rng=ctx.parent.fork_inputs();src['provenance']='CURRENT_ACTUAL_PARENT472_P4_READONLY';ctx=replace(ctx,parent=Parent.current(src,mem,rng,ctx.parent.raw_clock_tick))
            has_pending=history.env.unwrapped.finish_line_tracker.candidate_crossing_time_s is not None
            mode,force_first=mode472(arm,decision,history.ctrl.phase(),has_pending);self.active_pending=None
            if has_pending:
                pending=history.pending(ctx,before,self.meter.p['semantic_sources']);route=pending.validate(history,ctx)['gate'];self.active_pending=pending.bridge
                save_receipt(self.d/(label+'-actual-pending-private.json'),asdict(pending))
            else:
                ctx.validate();route=ctx.gate();require(route=='QUERY_CURRENT','472_NONPENDING_CURRENT_ROUTE')
            self.active_context=ctx
            self.meter.query_proof=self.meter.capture_inputs(snapshot(proxy),before,ctx.ledger,label+'_query',context=ctx,gate=route)
            ph,mh,rh=fingerprint(snapshot(proxy)),fingerprint(history.ctrl.memory()),rnghash()
            try:
                selected=self.p4_pair(parent,ctx,before,label,force_first)
                require(selected['valid'],'472_FIXED_P4_POLICY_INELIGIBLE_NO_FALLBACK')
            finally:
                for c in self.children:
                    if not c.closed:c.dump(self.d);c.close()
            self.unchanged(parent,ph,mh,rh);self.check_policy(history.ctrl)
            if pending:pending.validate(history,ctx)
            record=dict(arm=arm,relative_decision=decision,mode=mode,fixed_first=decision==1,phase=history.ctrl.phase(),route=route,selected_recipe='P4_POINT_FF_CURRENT',guardian_certificate=selected['certificate'],policy_digest=self.policy_digest,nodes_digest=self.nodes_digest,pair_independent_repeat_exact=True,pair_observed_actions=selected['observed_actions'],all_future_actions_use_P4=True,planner_ranking_receipt=False,actual_done_before_step=history.ledger.done,model_authorizes_actual_DONE=False,parent_memory_RNG_ledger_unchanged=True,canonical_adapter=adapter)
            save_receipt(self.d/(label+'-before-actual-dispatch-private.json'),dict(context=asdict(ctx),query_proof=self.meter.query_proof,selected_first=selected['first'],record=record,actual_dispatch_authorization='EXPLICIT472_SINGLE_P4_NATIVE_TRANSFER_CHARGE_AND_OWN_NATIVE_FACTS_ONLY'))
        record.update(query_CPU_s=time.process_time()-started,query_wall_s=time.perf_counter()-wall);self.meter.queries.append(record)
        return selected['first'],record,pending
