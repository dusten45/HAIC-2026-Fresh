"""Reuse436 selector and child code against a live read-only actual parent."""
import copy,time
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from retry.pilot436_run import Pilot as Pilot436,scope
from retry.pilot420_backend import capture_context,fingerprint,rnghash,snapshot,TechnicalStop
from retry.planner419 import Parent
from retry.actual437_boundary import live_proxy
from retry.fork394_run import complete_state
from retry.terminal410_model import from_actual_full
from retry.fixture438 import check_adapter
from retry.receipt421_io import save_receipt
from retry.loss389_analyze import sha,save
G=Path(__file__).resolve().parents[1]
class Query442(Pilot436):
 def __init__(self,root,meter,fixed,pace):
  self.root=root;self.d=root/'stage442';self.meter=meter;self.fixed=fixed;self.pace=pace;self.children=[];self.active_context=None;self.active_pending=None;self.policy_digest=fingerprint(dict(signed=sha(G/'retry/signed417_executor.py'),rules=sha(G/'retry/planner419.py'),fixed=sha(Path(meter.p['fixed_plan'])),pace=pace.tolist()))
 def unchanged(self,parent,ph,mh,rh):
  if fingerprint(snapshot(parent.m))!=ph or fingerprint(parent.ctrl.memory())!=mh or rnghash()!=rh or fingerprint(complete_state(self.history.env,self.history.obs,self.history.ctrl.memory()))!=self.full_stamp or self.history.ledger.digest()!=self.ledger_stamp:raise TechnicalStop('live_actual_parent_memory_RNG_ledger_changed')
 def query(self,history,before,nominal,arm,decision,planner_used):
  self.history=history;history.require_live();env=history.env;ctrl=history.ctrl;label=arm+'_decision'+str(decision);parent=SimpleNamespace(m=live_proxy(env),ctrl=ctrl);self.active_pending=None;cpu=time.process_time();wall=time.perf_counter()
  with self.meter.model(label):
   proxy,full,adapter_proof=check_adapter(env,history.obs,ctrl,self.d,label)
   parent.m=proxy
   self.full_stamp=fingerprint(full);self.ledger_stamp=history.ledger.digest();ctx=capture_context(parent.m,ctrl,before,nominal,history.ledger,self.fixed,self.policy_digest,{},history.initial.actual_root_digest);src,mem,rng=ctx.parent.fork_inputs();src['provenance']='CURRENT_ACTUAL_PARENT442_READONLY';from dataclasses import replace;ctx=replace(ctx,parent=Parent.current(src,mem,rng,ctx.parent.raw_clock_tick));pending=None
   if env.unwrapped.finish_line_tracker.candidate_crossing_time_s is not None:
    pending=history.pending(ctx,before,self.meter.p['semantic_sources']);route=pending.validate(history,ctx)['gate'];self.active_pending=pending.bridge;save_receipt(self.d/(label+'-actual-pending-private.json'),asdict(pending))
   else:
    ctx.validate();route=ctx.gate()
    if ctrl.phase()=='FIRST_LAP' and route!='QUERY_CURRENT':raise TechnicalStop('actual_current_context:'+route)
    if ctrl.phase() not in ['FIRST_LAP','FINISH_CONFIRM']:raise TechnicalStop('actual_current_phase')
   self.active_context=ctx;self.meter.query_proof=self.meter.capture_inputs(snapshot(parent.m),before,ctx.ledger,label+'_query',context=ctx,gate=route);ph=fingerprint(snapshot(parent.m));mh=fingerprint(ctrl.memory());rh=rnghash();_,planned=scope(arm,planner_used,ctrl.phase());planned=planned and pending is None
   try:selected=self.planning_query(parent,ctx,before,label) if planned else self.guardian(parent,ctx,before,label)
   finally:
    for c in self.children:
     if not c.closed:c.dump(self.d);c.close()
   self.unchanged(parent,ph,mh,rh)
   if pending:pending.validate(history,ctx)
   record=dict(arm=arm,relative_decision=decision,phase=ctrl.phase(),route=route,planner_used=planned,selected_recipe=selected['recipe'],model_decision=selected.get('summary'),guardian_certificate=selected.get('certificate'),parent_memory_RNG_ledger_unchanged=True,actual_done_before_step=history.ledger.done,model_authorizes_actual_DONE=False,new_state_prior_actual_qualified=False,canonical_adapter=adapter_proof)
   save_receipt(self.d/(label+'-before-actual-dispatch-private.json'),dict(context=asdict(ctx),query_proof=self.meter.query_proof,selected_first=selected['first'],record=record,actual_dispatch_authorization='Explicit442once_only_actual_pair; model_receipt_itself_has_no_authority'))
  record.update(query_CPU_s=time.process_time()-cpu,query_wall_s=time.perf_counter()-wall);self.meter.queries.append(record)
  return selected['first'],record,pending
