"""Fixed H1 native transfer: fresh actual input, two finite safe model copies."""
import copy,time
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.paired442_query import Query442
from retry.pilot420_backend import capture_context,snapshot,fingerprint,rnghash,TechnicalStop
from retry.planner419 import Parent
from retry.observer435 import Child
from retry.fixture438 import check_adapter
from retry.paired417_common import arrival
from retry.ledger439 import require
from retry.receipt421_io import save_receipt


def recipe448(arm,decision):
    require(arm in ['nominal','fullgas'] and type(decision) is int and 1<=decision<=26,'448_FIXED_ARM_OR_DECISION')
    return 'fullgas' if arm=='fullgas' and decision==1 else 'nominal'


def finite_guard448(child,tag,line,exit_progress):
    """Finite physical/progress guard, no finish evidence or policy ranking."""
    hit=dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None,interpolated=False)
    for _ in range(13):
        child.one(tag)
        require(child.status=='ACTIVE' and len(child.rows)>0 and not child.rows[-1]['safety'] and not child.ledger.deadline_missed,'448_MODEL_SAFETY_PROGRESS_OR_UNEXPECTED_TERMINAL')
        hit=arrival(child.rows,line,child.root_ledger.progress_m,exit_progress)
        if hit['reached']:break
    require(hit['reached'] or (len(child.rows)==13 and child.ledger.progress_qualified()),'448_FINITE_PROGRESS_GATE')
    return hit


class Query448(Query442):
    def __init__(self,root,meter,fixed,pace):
        super().__init__(root,meter,fixed,pace);self.d=root/'stage448'
    def query_fixed(self,history,before,nominal,arm,decision,exit_progress):
        self.history=history;history.require_live();label=arm+'_current'+str(decision)
        self.children=[];recipe=recipe448(arm,decision);started=time.process_time();wall=time.perf_counter()
        with self.meter.model(label):
            proxy,full,adapter=check_adapter(history.env,history.obs,history.ctrl,self.d,label)
            from types import SimpleNamespace
            parent=SimpleNamespace(m=proxy,ctrl=history.ctrl)
            self.full_stamp=fingerprint(full);self.ledger_stamp=history.ledger.digest()
            ctx=capture_context(proxy,history.ctrl,before,nominal,history.ledger,self.fixed,self.policy_digest,{},history.initial.actual_root_digest)
            src,mem,rng=ctx.parent.fork_inputs();src['provenance']='CURRENT_ACTUAL_PARENT448_READONLY'
            ctx=replace(ctx,parent=Parent.current(src,mem,rng,ctx.parent.raw_clock_tick));ctx.validate()
            require(history.ctrl.phase()=='FIRST_LAP' and ctx.gate()=='QUERY_CURRENT','448_CURRENT_FIRST_LAP_ONLY')
            require(history.env.unwrapped.finish_line_tracker.candidate_crossing_time_s is None,'448_UNEXPECTED_PENDING_FINISH')
            ph,mh,rh=fingerprint(snapshot(proxy)),fingerprint(history.ctrl.memory()),rnghash()
            state=snapshot(proxy);pair=[]
            try:
                for rep in [1,2]:
                    self.unchanged(parent,ph,mh,rh)
                    child_label=label+'_copy'+str(rep)
                    self.meter.capture_inputs(state,before,ctx.ledger,child_label+'_inputs',context=ctx,gate='448_FRESH_CURRENT_NATIVE_NO_MODEL_AUTHORITY')
                    child=Child(self.meter,copy.deepcopy(state),copy.deepcopy(before),ctx.ledger,self.fixed,self.pace,child_label,recipe=recipe,world_tag=child_label);self.children.append(child)
                    try:
                        hit=finite_guard448(child,'448_current_guard',np.asarray(self.fixed['line']),exit_progress)
                        first=child.rows[0]
                        require(first['memory_before']==before and first['memory_after']==history.ctrl.memory(),'448_FRESH_CURRENT_NOMINAL_MEMORY')
                        require(child.stream.actions[0]['nominal']==np.asarray(nominal,np.float32).tolist(),'448_FRESH_CURRENT_NOMINAL_COMMAND')
                        expected=np.asarray(nominal,np.float32).copy()
                        if recipe=='fullgas':expected[1:]=[1.,0.]
                        require(first['command']==expected.tolist(),'448_FIXED_FIRST_COMMAND')
                        pair.append(dict(signature=child.signature(),first=copy.deepcopy(first),actions=len(child.rows),hit=hit))
                        self.unchanged(parent,ph,mh,rh)
                    finally:
                        child.dump(self.d);child.close()
                require(pair[0]==pair[1],'448_CURRENT_INDEPENDENT_REPEAT')
                self.unchanged(parent,ph,mh,rh);history.require_live()
            finally:
                for child in self.children:
                    if not child.closed:child.dump(self.d);child.close()
            record=dict(arm=arm,decision=decision,recipe=recipe,guard_actions_each=pair[0]['actions'],common_exit_seen_in_guard=pair[0]['hit']['reached'],independent_repeat_exact=True,fresh_current_nominal_memory_exact=True,parent_memory_RNG_ledger_unchanged=True,actual_DONE_allowed=False,actual_execution_authority='EXPLICIT448_NATIVE_CHARGE_CALLBACK_ONLY',canonical_adapter=adapter)
            save_receipt(self.d/(label+'-before-actual-dispatch-private.json'),dict(context=asdict(ctx),selected_first=pair[0]['first'],record=record,scope='FINITE_SAFETY_PROGRESS_GUARD_NO_FINISH_RANKING'))
        record.update(query_CPU_s=time.process_time()-started,query_wall_s=time.perf_counter()-wall);self.meter.queries.append(record)
        return pair[0]['first'],record
