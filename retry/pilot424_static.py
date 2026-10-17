"""Stored-only actual-context/ledger/receipt preflight; zero world construction."""
import copy,json,sys,time
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.planner419 import *
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
from retry.paired417_common import policy
from retry.terminal410_model import from_actual_full
from retry.executor397 import canonical_projection
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest
from retry.preflight421 import restore_typed
from retry.carry423_model import require_planner_gate,TechnicalStop
from retry.terminal409_contract import validate
from retry.pilot424_run import Pilot

def run(root):
 d=root/'stage424';p=read(d/'plan.json');assert not(d/'static-result.json').exists();cpu=time.process_time();wall=time.perf_counter();checks=[]
 for f,h in p['sources'].items():assert sha(f)==h,f
 fork=read(root/'stage418/actual_A/fork-private.json');row=json.loads((root/'stage418/actual_A/trace-private.jsonl').read_text().splitlines()[118]);fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);state=from_actual_full(fork);h=state['physical']['hull'];q=canonical_projection(np.asarray(fixed['line']),h['position'],h['velocity'],'FIRST_LAP');r,_=policy(fixed,pace)._reference(q);ledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-(row['step']-1)),round(row['pre']['time']*50));old=ledger.digest();parent=Parent.current(dict(terminal_model=state,provenance='CURRENT_ACTUAL_PARENT'),fork['controller']['before'],fork['RNG'],ledger.last_clock_tick);ctx=Current(parent,ledger,'static',tuple(fork['controller']['nominal']),'FIRST_LAP',r,q['sigma'],float(np.asarray(h['velocity'])@np.asarray([-np.sin(h['angle']),np.cos(h['angle'])])),sum(fixed['free_profile']['ds'])-ledger.progress_m)
 assert ctx.gate()=='QUERY_CURRENT';checks.append('saved_actual_current_context_gate')
 forecast=ForecastLedger.fork(ledger);pred=forecast.advance_prediction(ModelPrediction(ledger.progress_m+.01,ledger.last_clock_tick+4));assert ledger.digest()==old and pred.actual_root_digest==old;checks.append('forecast_never_advances_actual')
 committed=ledger.advance_actual(ActualObservation(ledger.progress_m+.01,ledger.last_clock_tick+4));assert ledger.digest()==old and committed.last_clock_tick==ledger.last_clock_tick+4;checks.append('actual_commit_requires_actual_observation')
 try:ledger.advance_actual(ModelPrediction(ledger.progress_m+.01,ledger.last_clock_tick+4))
 except ContractError:checks.append('model_observation_rejected_by_actual')
 else:raise AssertionError('model_actual_channel_mixed')
 for n in range(1,4):
  payload=load_receipt(root/('stage421/P_decision'+str(n)+'-evidence-private.json'));c,e=restore_typed(copy.deepcopy(payload));assert asdict(choose(c,e))==dict(payload['decision'],gain_rawticks=None if payload['decision']['gain_rawticks'] is None else tuple(payload['decision']['gain_rawticks']));checks.append('saved421_typed_selector_'+str(n))
 payload=dict(context=asdict(ctx),ledger=asdict(ledger),scope='STATIC_ACTUAL_CONTEXT_ONLY');path=d/'static-context-private.json';digest=save_receipt(path,payload);assert receipt_digest(load_receipt(path))==digest and ctx.parent.stamp()==parent.stamp();checks.append('full_actual_context_receipt_roundtrip')
 assert query_schedule(ctx,Budget(131072,256)).mode=='STATE_QUERY_LONG_C_WITNESSES';checks.append('frozen_full_query_budget')
 confirmation=replace(ctx,phase='FINISH_CONFIRM');assert confirmation.gate()=='EXISTING_PHASE_ONLY_NOT_A_NEW_FALLBACK';require_planner_gate(confirmation,False);checks.append('existing_confirmation_guardian_not_firstlap_planner')
 try:require_planner_gate(confirmation,True)
 except TechnicalStop:checks.append('planner_rejects_confirmation_phase')
 else:raise AssertionError('planner_outside_firstlap')
 last=json.loads((root/'stage411/policy_C/trace-private.jsonl').read_text().splitlines()[-1]);assert last['raw_ticks']==3 and last['completed'] and validate(last)['passed'];checks.append('stored_official_partial_finish_contract')
 bad=copy.deepcopy(last);bad['finish_time_s']=bad['post']['time']+1;assert not validate(bad)['passed'];checks.append('future_finish_metadata_rejected')
 after=read(root/'stage411/policy_C/final-private.json');done=policy(fixed,pace);done.mark_done(after['wrapper']['finish_tracker'],last['post']['time']);assert done.phase=='DONE';checks.append('stored_official_finish_to_DONE')
 schedule=query_schedule(ctx,Budget(131072,256));assert 12*(schedule.essential_ticks_cap+schedule.qualification_extra_ticks_cap)+2048+4096<131072;checks.append('twelve_query_worst_tick_reservation_with_gate_margin')
 state2=copy.deepcopy(state);state2['physical']['hull']['position'][0]+=1e-10;other=Parent.current(dict(terminal_model=state2,provenance='CURRENT_ACTUAL_PARENT'),fork['controller']['before'],fork['RNG'],ledger.last_clock_tick);assert other.stamp()!=parent.stamp();checks.append('nearby_state_has_distinct_exact_root_stamp')
 result=dict(passed=True,checks=checks,tests=len(checks),model_worlds=0,model_ticks=0,actual_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,plan_sha256=sha(d/'plan.json'));save(d/'static-result.json',result);print(json.dumps(result))
if __name__=='__main__':run(Path(sys.argv[1]))
