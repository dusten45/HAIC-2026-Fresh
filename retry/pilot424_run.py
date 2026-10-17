"""Twelve-decision model-only scope extension of unchanged419 planning law."""
import copy,datetime,json,math,os,signal,sys,time,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import *
from retry.pilot424_meter import Meter
from retry.pilot421_run import compare_frames
from retry.pilot420_json import json_ready
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest
from retry.terminal410_model import from_actual_full
from retry.qualify424 import qualify
G=Path(__file__).resolve().parents[1]

def prepare(root):
 d=root/'stage424';assert not(d/'plan.json').exists();prior=read(root/'stage423/plan.json');v=read(root/'project-effective-budget-v443.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(28986,84000,0);assert read(root/'stage423/analysis.json')['actual_paired_carry_qualified']
 for f,h in {**prior['sources'],**prior['protected'],**prior['original408_preserve']}.items():assert sha(f)==h,f
 files=set(Path(f) for f in prior['sources']);files.update([Path(__file__),G/'retry/pilot424_meter.py',G/'retry/qualify424.py',G/'retry/pilot424_static.py',G/'retry/pilot421_run.py',G/'retry/calibrate422_analyze.py',G/'retry/carry423_model.py',G/'retry/preflight421.py',G/'retry/planner419_model_ledger.py',root/'stage423/plan.json',root/'stage423/result.json',root/'stage423/analysis.json',root/'stage423/cost.json',root/'project-effective-budget-v443.json',root/'research-deadline-current.json'])
 for arm in ['C0','P']:files.update(root/('stage423/actual_'+arm+'/'+name) for name in ['initial-private.json','fork-private.json','trace-private.jsonl','final-private.json'])
 files.update(root/('stage423/actual_P/actual_P_'+str(step)+'-receipt-private.json') for step in [119,120,121])
 preserve={str(f):sha(f) for stage in [420,421,422,423] for f in (root/('stage'+str(stage))).rglob('*') if f.is_file()};save(d/'prior-preservation-manifest.json',preserve);files.add(d/'prior-preservation-manifest.json')
 p=dict(stage=424,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],fixed_plan=prior['fixed_plan'],decision_count=12,root='Same423actualC0fork/Cpre119history118; knownrootisresearchscope, notdeploymenttrigger',caps=dict(ticks=131072,worlds=256,CPU_s=600,wall_s=900,max_parallel=1),new_actual_reset_actor_learning_SEALED_reserve_paid_cap=0,research_before=28986,reserve=84000,reserve_used=0,
 qualification='Beforepilot: replayactual423C0/Psavedcommandsfromactualforkthroughfirst13andcontinuationofficialfinish, eachindependenttwice. Allbody/wheel/rawhull/phase/finishmetadata/clipflagsand3.24m/13deadlinegates. Replayisphysicalcalibrationwithsavedcommands, notnewpolicyperformance; recomputednominaldelta reported, noactualfutureinselector. FreshrestorethreeactualPquerystates, selectedfirsttransitioneachtwice. Heldrootparent/memory/RNG/immutableactualledgeraftereveryfork/replaystep, thenheldfirstnominalvsindependent. Firstfailureglobalstop.',
 pilot='Afterqualificationreturns, freshC0thenPmodelparentsfromsameimmutableactualroot. Each12currentdecisionupdatesunlessfinish/stop. C0existingnominal13duplicates/neutralonlyifinvalid. P419allthreeinitial13andindependentrepeatthenSAMEchildCnominaltailtoofficialfinish/unsafe/censor<=additional308. Frozen419choose; noforeigntail/terminalweights/timeimputation. OnlyselectedfirstcommandtorealMODELparent, neverbranchmemory. After12sameparentCnominalcontinuationtoofficialfinish/stop<=additional308.',
 boundaries='ControlH13,3recipes/gain/projection/signedC/finishwitness/selector unchanged. ImmutableactualGoalLedgernevercommitted; ForecastLedgerfornewmodelpredictionsandcurrentvalueviewforreceipt. New424statesandwiderclippingnotactualqualified. Noactual/actor/learning/SEALED/reserve/paid. Noautomaticactualfollowup.',
 cache='No cache lookup or reuse: every424world/queryfresh, cachehits0. Noapproximate/nearby-stateoractualfuturecachedselection. Exactstate+memory+RNG+clock/ledger/policydigestsretainedineveryreceipt;12isexperimentaldecisioncountonly.',
 stop='Firsttechnical/fidelity/domain/numeric/restore/repeat/phase/liveparent/RNG/ledgererror/cost/deadlineglobalstop. Baselineguardianbothinadmissibleglobalstop. Failed/censoredtailsexcludedwithouttimeestimate. Frozen419cannotrepresentinitialunsafe<13: stopwithoutpadding/repair/retry. Nochangesafterfirstfailure.',
 promotion='Bothfinishedmodelparents+allgatesandstrictpositiveofficialfinishbracketgainqualifyonlyproposalforseparatelyauthorizedactualtransitioncalibration. Noactualautostart, noindependentgeneralization/11secondproof/pixel296promotion. Everydecisionwitnessandrootprojectedbracketreportedwithoutaddingoverlappinggains; post12actualMODELtailcancellationreported.',
 accounting='Chargeallworldsandrawtickreservationsbeforecalls, retainpartial/unconfirmed. Qualificationreplayfirst13/continuation/currentrestore/parent, C0required/repeat, plannerinitial13/tailrequired/repeat,parentadvance/finaltailseparatetags. Initial13andtailSAMEchild,no reintegration; cachedoldcost0recharged. WholeworkerCPUincludesimports/control/hash/IO/cleanup; preparationseparatepartialscope.',sources={str(f):sha(f) for f in sorted(files)},protected=prior['protected'],original408_preserve=prior['original408_preserve'])
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_interval_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,total_preparation_fully_measured=False,scope=read(d/'preparation-opening.json')['scope']));print('424 frozen',sha(d/'plan.json'))

class Pilot:
 def __init__(self,root,meter,fixed,pace,state,memory,actual_ledger,rng):
  self.root=root;self.d=root/'stage424';self.meter=meter;self.fixed=fixed;self.pace=pace;self.state=state;self.memory=memory;self.actual_ledger=actual_ledger;self.actual_digest=actual_ledger.digest();self.archive_rng=rng;self.children=[];self.decisions=[];self.results=[];self.policy_digest=fingerprint(dict(signed=sha(G/'retry/signed417_executor.py'),rules=sha(G/'retry/planner419.py'),fixed=sha(Path(meter.p['fixed_plan'])),pace=pace.tolist()))
 def new(self,state,memory,ledger,label,recipe='nominal',tag='required'):
  c=Child(self.meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,self.fixed,self.pace,label,recipe,tag);self.children.append(c);return c
 def assert_actual(self):
  if self.actual_ledger.digest()!=self.actual_digest:raise TechnicalStop('immutable_actual_ledger_changed')
 def unchanged(self,parent,ph,mh,rh):
  self.assert_actual()
  if fingerprint(snapshot(parent.m))!=ph or fingerprint(parent.ctrl.memory())!=mh or rnghash()!=rh:raise TechnicalStop('live_model_parent_memory_RNG_changed')
 def close_saved(self,child):child.dump(self.d);child.close()
 def short_pair(self,parent,ctx,before,label,recipe):
  state=snapshot(parent.m);ph=fingerprint(state);mh=fingerprint(parent.ctrl.memory());rh=rnghash();pair=[]
  for rep in range(2):
   c=self.new(state,before,ctx.ledger,label+'_'+recipe+'_'+str(rep+1),recipe,'C0_guard_required' if rep==0 else 'C0_guard_repeat');c.initial13('C0_guard_required' if rep==0 else 'C0_guard_repeat');c.dump(self.d);self.unchanged(parent,ph,mh,rh);pair.append(c)
  if pair[0].signature()!=pair[1].signature():raise TechnicalStop('C0_guardian_repeat')
  first=pair[0].rows[0];valid=pair[0].initial_safe and pair[0].initial_progress and pair[0].initial_ok and pair[0].status in ['ACTIVE','FINISHED'];result=dict(valid=valid,first=copy.deepcopy(first),recipe=recipe)
  for c in pair:self.close_saved(c)
  return result
 def guardian(self,parent,ctx,before,label):
  a=self.short_pair(parent,ctx,before,label,'nominal')
  if a['valid']:return a
  b=self.short_pair(parent,ctx,before,label,'neutralbrake')
  if not b['valid']:raise PilotStop('baseline_guardian_both_infeasible')
  return b
 def planning_query(self,parent,ctx,before,label):
  schedule=query_schedule(ctx,Budget(131072-self.meter.b['reserved_ticks'],256-self.meter.b['worlds']))
  if schedule.mode!='STATE_QUERY_LONG_C_WITNESSES':raise ResourceStop('full_frozen_planner_query_budget_not_available')
  state=snapshot(parent.m);ph=fingerprint(state);mh=fingerprint(parent.ctrl.memory());rh=rnghash();pairs={};eval_order=[r for r in ['nominal','neutralbrake','fullgas'] if r in schedule.recipes]
  for recipe in eval_order:
   pair=[]
   for rep in range(2):
    tag='planner_required_initial13' if rep==0 else 'planner_repeat_initial13';c=self.new(state,before,ctx.ledger,label+'_'+recipe+'_'+str(rep+1),recipe,'planner_required' if rep==0 else 'planner_independent_repeat');c.initial13(tag);c.dump(self.d);self.unchanged(parent,ph,mh,rh);pair.append(c)
   if pair[0].signature()!=pair[1].signature():raise TechnicalStop('planner_initial13_repeat')
   if not pair[0].initial_ok:raise TechnicalStop('partial_initial_ineligible_419_receipt_stop_without_padding')
   pairs[recipe]=pair
   if recipe=='neutralbrake' and not(pairs['nominal'][0].initial_safe and pairs['nominal'][0].initial_progress) and not(pair[0].initial_safe and pair[0].initial_progress):raise PilotStop('planner_baseline_guardian_both_infeasible')
  for recipe,pair in pairs.items():
   for rep,c in enumerate(pair):
    if c.initial_safe and c.initial_progress:c.continue_tail('planner_required_tail' if rep==0 else 'planner_repeat_tail')
    c.dump(self.d);self.unchanged(parent,ph,mh,rh)
   if pair[0].signature()!=pair[1].signature():raise TechnicalStop('planner_full_C_tail_repeat')
  receipts={r:cs[0].evidence(ctx) for r,cs in pairs.items()};decision=choose(ctx,receipts)
  payload=dict(query=asdict(schedule),context=asdict(ctx),evidence={r:asdict(e) for r,e in receipts.items()},decision=asdict(decision),scope='New424statesandwiderclippingMODEL_ONLY. Saved423actualqualificationisolatedbeforepilot, noactualfuturetraceinputs/cache.')
  receipt_path=self.d/(label+'-evidence-private.json');digest=save_receipt(receipt_path,payload)
  if receipt_digest(load_receipt(receipt_path))!=digest:raise TechnicalStop('runtime_receipt_roundtrip_digest')
  self.unchanged(parent,ph,mh,rh)
  save(self.d/(label+'-receipt-digest.json'),dict(digest=digest,readback_verified=True,parent_unchanged=True))
  if decision.recipe is None or decision.status not in ['MODEL_TIME_CHOICE','GUARDIAN_REFERENCE_ONLY']:raise PilotStop('planner_no_qualified_first_action:'+decision.status)
  selected=pairs[decision.recipe][0];first=copy.deepcopy(selected.rows[0]);summary=dict(decision=asdict(decision),recipes={r:dict(status=c[0].status,initial_actions=c[0].initial_count,tail_actions=c[0].tail_count,finish_ticks=None if c[0].finish_ticks is None else asdict(c[0].finish_ticks),actual_physics_qualified=False) for r,c in pairs.items()})
  for pair in pairs.values():
   for c in pair:self.close_saved(c)
  return dict(recipe=decision.recipe,first=first,summary=summary)
 def policy(self,name):
  parent=self.new(self.state,self.memory,self.actual_ledger,'parent_'+name,tag='pilot_parent');self.assert_actual();count=0
  for index in range(12):
   if parent.status!='ACTIVE':break
   before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m);ctx=capture_context(parent.m,parent.ctrl,before,nominal,parent.ledger,self.fixed,self.policy_digest,self.archive_rng,self.actual_digest)
   if ctx.gate()!='QUERY_CURRENT':raise TechnicalStop('current_context:'+ctx.gate())
   label=name+'_decision'+str(index+1)
   selected=self.guardian(parent,ctx,before,label) if name=='C0' else self.planning_query(parent,ctx,before,label)
   parent.one('parent_'+name+'_advance',first_override=selected['first']['command'],prepared_nominal=nominal,prepared_before=before);check=compare_frames(parent.rows[-1],selected['first']);self.assert_actual()
   if not check['passed']:raise TechnicalStop('new_model_parent_vs_selected_first')
   if parent.status in ['UNSAFE','INFEASIBLE','CENSORED']:raise PilotStop('parent_first_action_'+parent.status)
   record=dict(policy=name,relative_decision=index+1,selected_recipe=selected['recipe'],parent_model_clock=parent.ledger.last_clock_tick,parent_model_progress=parent.ledger.progress_m,selected_first_check=check,choice=selected.get('summary'),actual_ledger_unchanged=True,new_state_actual_physics_qualified=False);self.decisions.append(record);save(self.d/'decisions-private.json',self.decisions);count+=1;print(json.dumps(dict(stage=424,policy=name,decision=count,recipe=selected['recipe'],model_ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])),flush=True)
  parent.initial_count=len(parent.rows);parent.end13=parent._end_vector();parent.initial_safe=not any(r['safety'] for r in parent.rows);parent.initial_progress=parent.ledger.progress_qualified();parent.initial_ok=True
  if parent.status=='ACTIVE':parent.continue_tail('parent_'+name+'_final_C_tail')
  rr=dict(policy=name,status=parent.status,error=parent.error,decisions=count,total_model_actions=len(parent.rows),continuation_actions=parent.tail_count,finish_ticks=None if parent.finish_ticks is None else asdict(parent.finish_ticks),remaining_time_bracket_s=None if parent.finish_ticks is None else parent.finish_ticks.seconds(),official_finish=parent.status=='FINISHED',max_post_path_error_m=max(r['path_error_m'] for r in parent.rows),damage=parent.m.damage.damage,predicted_progress_goal_ok=parent.ledger.progress_qualified(),long_tail_actual_physics_qualified=False,actual_ledger_unchanged=True);self.results.append(rr);save(self.d/'policy-results.json',self.results);self.close_saved(parent)
  if rr['status']!='FINISHED':raise PilotStop(name+'_continuation_'+rr['status'])
 def closeall(self):
  for c in self.children:
   if not c.closed:
    try:c.dump(self.d)
    finally:c.close()
  self.meter.closeall()

def run(root):
 d=root/'stage424';p=read(d/'plan.json');assert not(d/'opening.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert read(d/'static-result.json')['passed']
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 for f,h in read(d/'prior-preservation-manifest.json').items():assert sha(f)==h,f
 save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),static_result_sha256=sha(d/'static-result.json')));meter=Meter(d);pilot=None;stage='root';status='STARTED';error=None
 def timeout(*a):raise ResourceStop('CPU600_wall900_signal')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.01,599-time.process_time()));signal.setitimer(signal.ITIMER_REAL,899)
 try:
  fork=read(root/'stage423/actual_C0/fork-private.json');state=from_actual_full(fork);memory=fork['controller']['before'];clock=round(state['physical']['actual_time']*50);actualrow=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);actual=GoalLedger(actualrow['progress_before'],actualrow['goal_before'],H-(actualrow['deadline_before']-(actualrow['step']-1)),clock);fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);stage='actual423_qualification';qualify(root,meter,fixed,pace,state,memory,actual);print('424 saved423 actual-fidelity qualification passed',flush=True)
  pilot=Pilot(root,meter,fixed,pace,state,memory,actual,fork['RNG'])
  for name in ['C0','P']:stage='model_policy_'+name;pilot.policy(name);print('424 '+name+' model parent continuation finished',flush=True)
  status='MODEL_TWELVE_DECISION_PILOT_COMPLETED'
 except BaseException as e:status='MODEL_PILOT_STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc()))
 finally:
  if pilot:pilot.closeall()
  else:meter.closeall()
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  meter.persist()
 results=[] if pilot is None else pilot.results;gain=None
 if len(results)==2 and all(z['official_finish'] for z in results):a=results[0]['finish_ticks'];b=results[1]['finish_ticks'];gain=[(a['lo']-b['hi'])/50,(a['hi']-b['lo'])/50]
 q=dict(stage=424,status=status,last_stage=stage,error=error,policies=results,decision_count=0 if pilot is None else len(pilot.decisions),model_remaining_finish_gain_bracket_s=gain,strict_model_gain=bool(gain and gain[0]>0),actual_gate_opened=False,new_actual_reset_actor_learning_SEALED_reserve_paid=0,actual_root_ledger_unchanged=True if pilot is None else pilot.actual_ledger.digest()==pilot.actual_digest,new424_states_actual_physics_qualified=False,cache_hits=0,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'));save(d/'result.json',q);print(json.dumps({k:v for k,v in q.items() if k!='policies'}))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
