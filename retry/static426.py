"""Frozen positive/negative temporal controls, entirely without integrations."""
import copy,json,signal,sys,time
from dataclasses import replace
from pathlib import Path
from retry.guardian426 import *
from retry.loss389_analyze import read,sha,save
from retry.preflight421 import restore_typed
from retry.receipt421_io import load_receipt
from retry.planner419 import choose,ContractError

class StaticBudgetStop(BaseException):pass
def run(root):
 d=root/'stage426';p=read(d/'plan.json');assert not(d/'static-result.json').exists();cpu=time.process_time();wall=time.perf_counter();checks=[];error=None
 def timeout(*a):raise StaticBudgetStop('staticCPU60_wall120')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.001,59-time.process_time()));signal.setitimer(signal.ITIMER_REAL,119)
 def mark(name,condition):
  if not condition:raise AssertionError(name)
  checks.append(name)
 def deny(name,call):
  try:call()
  except Exception:checks.append(name);return
  raise AssertionError(name)
 try:
  for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
  final=read(root/'stage425/actual_P/final-private.json');rootstate=dict(physical=copy.deepcopy(final['physical']),finish_tracker=copy.deepcopy(final['wrapper']['finish_tracker']));failed=read(root/'stage425/actual_P/actual_P_177_nominal_1-private.json');frame=failed['rows'][0];pred=frame['predicted'];tracker=failed['final_state']['finish_tracker'];t=rootstate['physical']['actual_time'];cert=guardian_finish(rootstate,'FINISH_CONFIRM',pred,tracker,{t:0,pred['time']:1});mark('425_AT_ROOT_model_only',cert['kind']=='AT_ROOT_CONFIRMED_IN_MODEL' and not cert['actual_done_allowed'] and not cert['planner_ranking_eligible'])
  past=copy.deepcopy(rootstate);past['physical']['actual_time']=t+.02;later=copy.deepcopy(pred);later['time']=t+.04;mark('registered_BEFORE_ROOT_pending_confirmation',guardian_finish(past,'FINISH_CONFIRM',later,tracker,{})['kind']=='BEFORE_ROOT_CONFIRMED_IN_MODEL')
  def mutate_root(key,value):
   x=copy.deepcopy(rootstate);x['finish_tracker'][key]=value;return x
  future=copy.deepcopy(pred);future['finish_time_s']=pred['time']+.02;deny('future_timestamp_rejected',lambda:guardian_finish(rootstate,'FINISH_CONFIRM',future,tracker,{}))
  deny('mismatched_pending_phase_rejected',lambda:guardian_finish(rootstate,'FIRST_LAP',pred,tracker,{}))
  deny('STOP_phase_rejected',lambda:guardian_finish(rootstate,'STOP',pred,tracker,{}))
  deny('crossing_without_qualification_rejected',lambda:guardian_finish(mutate_root('qualified_time_s',None),'FINISH_CONFIRM',pred,tracker,{}))
  deny('crossing_without_from_back_rejected',lambda:guardian_finish(mutate_root('crossing_from_back',False),'FINISH_CONFIRM',pred,tracker,{}))
  deny('arbitrary_past_event_rejected',lambda:guardian_finish(mutate_root('candidate_crossing_time_s',t-.02),'FINISH_CONFIRM',pred,tracker,{}))
  deny('current_official_finish_forbids_new_query',lambda:guardian_finish(mutate_root('finish_time_s',t),'FINISH_CONFIRM',pred,tracker,{}))
  bad=copy.deepcopy(rootstate);bad['physical']['hull']['position']=[1e6,1e6];deny('confirmation_corridor_rejected',lambda:guardian_finish(bad,'FINISH_CONFIRM',pred,tracker,{}))
  wrong=copy.deepcopy(tracker);wrong['candidate_crossing_time_s']=t-.02;deny('model_confirmation_mismatch_rejected',lambda:guardian_finish(rootstate,'FINISH_CONFIRM',pred,wrong,{}))
  stale=copy.deepcopy(rootstate);stale['finish_tracker']['candidate_crossing_time_s']=0.;stale_pred=copy.deepcopy(pred);stale_pred['finish_time_s']=0.;stale_tracker=copy.deepcopy(tracker);stale_tracker.update(candidate_crossing_time_s=0.,finish_time_s=0.);deny('arbitrary_prequalification_past_event_rejected',lambda:guardian_finish(stale,'FINISH_CONFIRM',stale_pred,stale_tracker,{}))
  mark('model_certificate_not_native_DONE',not actual_done_eligible(cert,False))
  rows=[json.loads(s) for s in (root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()];last=rows[-1];mark('423_normal_partial_native_DONE',last['raw_ticks']==3 and actual_done_eligible(last,True));mark('unissued_actual_action_cannot_DONE',not actual_done_eligible(last,False));mark('425_candidate_not_actual_DONE',not actual_done_eligible(json.loads((root/'stage425/actual_P/trace-private.jsonl').read_text().splitlines()[-1]),True))
  model=read(root/'stage423/actual_C0/actual_C0_189_nominal_1-private.json');q=model['rows'][0]['predicted'];normal=copy.deepcopy(rootstate);normal['physical']['actual_time']=last['pre']['time'];normal['finish_tracker']=copy.deepcopy(model['final_state']['finish_tracker']);normal['finish_tracker'].update(finish_time_s=None,candidate_crossing_time_s=None);clocks={h['time']:h['raw_tick']-1 for h in model['rows'][0]['raw_hull']};clocks[q['time']]=q['raw_ticks'];mark('423_AFTER_ROOT_guardian_without_ranking',guardian_finish(normal,'FIRST_LAP',q,model['final_state']['finish_tracker'],clocks)['kind']=='AFTER_ROOT_CONFIRMED_IN_MODEL')
  deny('unregistered_future_event_rejected',lambda:guardian_finish(normal,'FIRST_LAP',q,model['final_state']['finish_tracker'],{}))
  old408=[json.loads(s) for s in (root/'stage408/trace-private.jsonl').read_text().splitlines()];mark('408_409_partial_contract_preserved',all(validate(r)['passed'] for r in old408) and read(root/'stage408/result.json')['status']=='QUALIFICATION_OR_TECHNICAL_STOP');mark('409_original_failure_not_waived',read(root/'stage409/result.json')['original408_completed_safe_preserved'] is False)
  bad=copy.deepcopy(last);bad['finish_time_s']=bad['post']['time']+1;mark('native_future_finish_rejected',not actual_done_eligible(bad,True));bad=copy.deepcopy(last);bad['raw_tire_samples'].pop();mark('native_missing_sample_rejected',not actual_done_eligible(bad,True));bad=copy.deepcopy(last);bad['completed']=False;bad['finish_time_s']=None;bad['ended']=False;bad['truncated']=False;mark('short_nonterminal_rejected',not validate(bad)['passed'])
  deny('planner_negative_bracket_unchanged',lambda:TickBracket(-1,0));payload=load_receipt(root/'stage425/actual_P/actual_P_119-receipt-private.json');ctx,ev=restore_typed(copy.deepcopy(payload));name=next(iter(ev));deny('planner_zero_event_ranking_rejected',lambda:replace(ev[name],finish_ticks=TickBracket(0,0)).authenticate(ctx));mark('planner_selection_unchanged',choose(ctx,ev).recipe==payload['decision']['recipe'])
  deny('guardian_certificate_cannot_be_evidence',lambda:GuardianChild.__new__(GuardianChild).evidence(ctx));mark('worst_cost_bound',p['worst_model_ticks']==129890 and p['worst_model_worlds']==795)
 except BaseException as e:error=type(e).__name__+': '+str(e)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
 result=dict(passed=error is None,error=error,checks=checks,tests=len(checks),new_actual_actions=0,new_model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,plan_sha256=sha(d/'plan.json'));save(d/'static-result.json',result);print(json.dumps(result))
if __name__=='__main__':run(Path(sys.argv[1]))
