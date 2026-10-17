"""Twelve-decision model-only scope extension of unchanged419 planning law."""
import copy,datetime,json,math,os,signal,sys,time,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import *
from retry.pilot428_meter import Meter
from retry.pilot421_run import compare_frames
from retry.pilot420_json import json_ready
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest
from retry.terminal410_model import from_actual_full
from retry.qualify428 import qualify
from retry.guardian426_confirmed import GuardianChild
G=Path(__file__).resolve().parents[1]

def prepare(root):
 d=root/'stage428';assert not(d/'plan.json').exists();prior=read(root/'stage427/plan.json');v=read(root/'project-effective-budget-v447.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(28444,84000,0)
 for f,h in {**prior['sources'],**prior['protected'],**prior['original408_preserve']}.items():assert sha(f)==h,f
 files=set(Path(f) for f in prior['sources']);files.update([Path(__file__),G/'retry/pilot428_meter.py',G/'retry/qualify428.py',G/'retry/static428.py',G/'retry/pilot428_analyze.py',G/'retry/planner419_model_ledger.py',G/'retry/calibrate422_analyze.py',G/'retry/guardian426_confirmed.py',root/'project-effective-budget-v447.json',root/'research-deadline-current.json'])
 for folder in ['stage427','stage423']:
  files.update(f for f in (root/folder).rglob('*') if f.is_file())
 preserve={str(f):sha(f) for stage in range(420,428) for f in (root/('stage'+str(stage))).rglob('*') if f.is_file()};save(d/'prior-preservation-manifest.json',preserve);files.add(d/'prior-preservation-manifest.json')
 worst=64*3*(13+308)*4*2+64*2*13*4*2+128*4+1132;worlds=64*6+64*4+2+29;assert(worst,worlds)==(508012,671)
 p=dict(stage=428,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],fixed_plan=prior['fixed_plan'],decision_count=64,caps=dict(ticks=524288,worlds=1024,CPU_s=1800,wall_s=2400,max_parallel=1),worst_model_ticks=worst,worst_model_worlds=worlds,new_actual_reset_actor_learning_SEALED_reserve_paid_cap=0,research_before=28444,reserve=84000,reserve_used=0,
 qualification='Isolatedsaved423C0and427Pfullactualcommandreplayeach2independent, first13+continuationbody/wheel/rawhull/phase/clip/finish. Restore12actual427Pquerycurrentstatesfirstselectedtransitions2each. Heldrootparent/memory/globalRNG/actualledgerunchangedandheldfirststepvsindependent. Modelonlyqualificationcost1132ticks29worlds; actualfuturecommandreplayforphysicalgatesonly, notselectorinputs.',
 pilot='FreshC0thenPfromsame423root. BOTHparentsmax64decisions. C0guardianatcurrentstate; PFIRST_LAPeligible419all3distinctrecipesinitial13+SAMEchildCnominaltail<=additional308, required+independentrepeat; strictbracketchooseunchanged. FINISH_CONFIRMonlyverifiedguardiancertificate426,no419futureranking. OnlyselectedfirstcommandtoMODELparent; nochildmemorycommit. Everynewcurrentstatequeried. Noafter64tail: ifnotfinishedSCOPE_CENSORED, noestimatedfinish. C0scopecensorisnottechnicalerrorandPmayrun; anytechnical/guardianbothinvalid/costglobalstop.',
 comparison='FreshC0/Pofficialfinishgainonlyifbothfinishwithin64. C0knownhistorical71actionsisnotexemptedfrom64, soifcensoredfreshgainNone. Qualificationreplayorhistorical423/427finishmustnotreplacefreshbaselineoutcome. CommonobservedarcbracketsandPofficialfinishcanbereportedseparately.',
 stop='Firsttechnical/domain/numeric/fidelity/restore/repeat/phase/parentRNG/memory/actualledgererror,bothbaselineguardianinadmissible,cost/deadline=>globalstop. Failed/censoredcandidatetailstimeNone; noinitialpartialpadding. Noactual/learning/SEALED/reserve/paid/newseed/path/steering/pedalsize/gain/recipe/H13/projectionchange.',
 cache='Nocachelookup/reuse,allworldsfresh;cachehits0. ExactParentstate/memory/RNG/clock+ledger/policyhashineveryreceipt; noapproximateoractualfuturecachedselection.',
 measurement='WholeprocessCPUincludesimports/sourcechecks/control/hash/snapshot/IO/cleanup; executionwallfrommeterstart, hardSIGPROF1800/wall2400. PerdecisionwholequeryCPU/wallandtagconstructor/steptime, required/repeat/initial/tail/parent/qualificationticks/worlds. Preparationseparatepartialscope. Newstates/widerforceareasnotactualqualified, modelparentnotactualenv. Noautomaticactualfollowup/generalization/11secondclaim.',sources={str(f):sha(f) for f in sorted(files)},protected=prior['protected'],original408_preserve=prior['original408_preserve'])
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_interval_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],CPU_s=None,total_preparation_fully_measured=False,scope=read(d/'preparation-opening.json')['scope']));print('428 frozen',sha(d/'plan.json'))

class Pilot:
 def __init__(self,root,meter,fixed,pace,state,memory,actual_ledger,rng):
  self.root=root;self.d=root/'stage428';self.meter=meter;self.fixed=fixed;self.pace=pace;self.state=state;self.memory=memory;self.actual_ledger=actual_ledger;self.actual_digest=actual_ledger.digest();self.archive_rng=rng;self.children=[];self.decisions=[];self.results=[];self.policy_digest=fingerprint(dict(signed=sha(G/'retry/signed417_executor.py'),rules=sha(G/'retry/planner419.py'),fixed=sha(Path(meter.p['fixed_plan'])),pace=pace.tolist()))
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
   c=GuardianChild(self.meter,copy.deepcopy(state),copy.deepcopy(before),ctx.ledger,self.fixed,self.pace,label+'_'+recipe+'_'+str(rep+1),recipe,'guardian_required' if rep==0 else 'guardian_repeat',confirmation_phase=parent.ctrl.phase());self.children.append(c);c.initial13('guardian_required' if rep==0 else 'guardian_repeat');c.dump(self.d);self.unchanged(parent,ph,mh,rh);pair.append(c)
  if pair[0].signature()!=pair[1].signature():raise TechnicalStop('C0_guardian_repeat')
  first=pair[0].rows[0];valid=pair[0].initial_safe and pair[0].initial_progress and pair[0].initial_ok and pair[0].status in ['ACTIVE','FINISHED'];result=dict(valid=valid,first=copy.deepcopy(first),recipe=recipe,certificate=pair[0].guardian_certificate)
  for c in pair:self.close_saved(c)
  return result
 def guardian(self,parent,ctx,before,label):
  a=self.short_pair(parent,ctx,before,label,'nominal')
  if a['valid']:return a
  b=self.short_pair(parent,ctx,before,label,'neutralbrake')
  if not b['valid']:raise PilotStop('baseline_guardian_both_infeasible')
  return b
 def planning_query(self,parent,ctx,before,label):
  schedule=query_schedule(ctx,Budget(524288-self.meter.b['reserved_ticks'],1024-self.meter.b['worlds']))
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
  payload=dict(query=asdict(schedule),context=asdict(ctx),evidence={r:asdict(e) for r,e in receipts.items()},decision=asdict(decision),scope='New428statesandwiderclippingMODEL_ONLY. Saved423actualqualificationisolatedbeforepilot, noactualfuturetraceinputs/cache.')
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
  for index in range(64):
   if parent.status!='ACTIVE':break
   query_c=time.process_time();query_w=time.perf_counter();before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m);ctx=capture_context(parent.m,parent.ctrl,before,nominal,parent.ledger,self.fixed,self.policy_digest,self.archive_rng,self.actual_digest)
   phase=parent.ctrl.phase()
   if phase=='FIRST_LAP':
    if ctx.gate()!='QUERY_CURRENT':raise TechnicalStop('current_context:'+ctx.gate())
   elif phase!='FINISH_CONFIRM':raise TechnicalStop('unsupported_current_phase:'+phase)
   label=name+'_decision'+str(index+1)
   planned=name=='P' and phase=='FIRST_LAP'
   selected=self.planning_query(parent,ctx,before,label) if planned else self.guardian(parent,ctx,before,label)
   query_CPU=time.process_time()-query_c;query_wall=time.perf_counter()-query_w
   parent.one('parent_'+name+'_advance',first_override=selected['first']['command'],prepared_nominal=nominal,prepared_before=before);check=compare_frames(parent.rows[-1],selected['first']);self.assert_actual()
   if not check['passed']:raise TechnicalStop('new_model_parent_vs_selected_first')
   if parent.status in ['UNSAFE','INFEASIBLE','CENSORED']:raise PilotStop('parent_first_action_'+parent.status)
   record=dict(policy=name,relative_decision=index+1,phase=phase,planner_used=planned,query_CPU_s=query_CPU,query_wall_s=query_wall,guardian_certificate=selected.get('certificate'),model_parent_not_actual=True,actual_execution_allowed=False,selected_recipe=selected['recipe'],parent_model_clock=parent.ledger.last_clock_tick,parent_model_progress=parent.ledger.progress_m,selected_first_check=check,choice=selected.get('summary'),actual_ledger_unchanged=True,new_state_actual_physics_qualified=False);self.decisions.append(record);save(self.d/'decisions-private.json',self.decisions);count+=1;print(json.dumps(dict(stage=428,policy=name,decision=count,recipe=selected['recipe'],model_ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])),flush=True)
  if parent.status=='ACTIVE':parent.status='SCOPE_CENSORED_DECISION64';parent.error='Noofficialfinishwithin64parentdecisions; notail/timeimputation'
  rr=dict(policy=name,status=parent.status,error=parent.error,decisions=count,planner_decisions=sum(x['planner_used'] for x in self.decisions if x['policy']==name),guardian_decisions=sum(not x['planner_used'] for x in self.decisions if x['policy']==name),total_model_actions=len(parent.rows),continuation_actions=0,finish_ticks=None if parent.finish_ticks is None else asdict(parent.finish_ticks),remaining_time_bracket_s=None if parent.finish_ticks is None else parent.finish_ticks.seconds(),official_finish=parent.status=='FINISHED',scope_censored=parent.status=='SCOPE_CENSORED_DECISION64',observed_model_time_s=sum(r['predicted']['raw_ticks'] for r in parent.rows)/50,max_post_path_error_m=max(r['path_error_m'] for r in parent.rows),damage=parent.m.damage.damage,predicted_progress_goal_ok=parent.ledger.progress_qualified(),long_tail_actual_physics_qualified=False,actual_ledger_unchanged=True);self.results.append(rr);save(self.d/'policy-results.json',self.results);self.close_saved(parent)
  if rr['status'] not in ['FINISHED','SCOPE_CENSORED_DECISION64']:raise PilotStop(name+'_parent_'+rr['status'])

 def closeall(self):
  for c in self.children:
   if not c.closed:
    try:c.dump(self.d)
    finally:c.close()
  self.meter.closeall()

def run(root):
 d=root/'stage428';p=read(d/'plan.json');assert not(d/'opening.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert read(d/'static-result.json')['passed']
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 for f,h in read(d/'prior-preservation-manifest.json').items():assert sha(f)==h,f
 save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),static_result_sha256=sha(d/'static-result.json')));meter=Meter(d);pilot=None;stage='root';status='STARTED';error=None
 def timeout(*a):raise ResourceStop('CPU1800_wall2400_signal')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.01,1799-time.process_time()));signal.setitimer(signal.ITIMER_REAL,2399)
 try:
  fork=read(root/'stage423/actual_C0/fork-private.json');state=from_actual_full(fork);memory=fork['controller']['before'];clock=round(state['physical']['actual_time']*50);actualrow=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);actual=GoalLedger(actualrow['progress_before'],actualrow['goal_before'],H-(actualrow['deadline_before']-(actualrow['step']-1)),clock);fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);stage='actual423_qualification';qualify(root,meter,fixed,pace,state,memory,actual);print('428 saved423 actual-fidelity qualification passed',flush=True)
  pilot=Pilot(root,meter,fixed,pace,state,memory,actual,fork['RNG'])
  for name in ['C0','P']:stage='model_policy_'+name;pilot.policy(name);print('428 '+name+' model parent continuation finished',flush=True)
  status='MODEL_SCOPE64_COMPLETED'
 except BaseException as e:status='MODEL_PILOT_STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc()))
 finally:
  if pilot:pilot.closeall()
  else:meter.closeall()
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  meter.persist()
 results=[] if pilot is None else pilot.results;gain=None
 if len(results)==2 and all(z['official_finish'] for z in results):a=results[0]['finish_ticks'];b=results[1]['finish_ticks'];gain=[(a['lo']-b['hi'])/50,(a['hi']-b['lo'])/50]
 q=dict(stage=428,status=status,last_stage=stage,error=error,policies=results,decision_count=0 if pilot is None else len(pilot.decisions),model_remaining_finish_gain_bracket_s=gain,strict_model_gain=bool(gain and gain[0]>0),actual_gate_opened=False,new_actual_reset_actor_learning_SEALED_reserve_paid=0,actual_root_ledger_unchanged=True if pilot is None else pilot.actual_ledger.digest()==pilot.actual_digest,new428_states_actual_physics_qualified=False,cache_hits=0,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'));save(d/'result.json',q);print(json.dumps({k:v for k,v in q.items() if k!='policies'}))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
