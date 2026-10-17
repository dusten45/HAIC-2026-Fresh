"""Frozen419 three-decision model-only C0/planner pilot from real418 fork."""
import copy,datetime,json,math,os,signal,sys,time,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import *
from retry.pilot420_json import json_ready
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest
from retry.terminal410_model import from_actual_full
from retry.paired417_common import shapecheck
G=Path(__file__).resolve().parents[1]

def compare_frames(a,b):
 qa,qb=a['predicted'],b['predicted'];e=dict(position_m=math.dist(qa['position'],qb['position']),speed_m_s=abs(qa['speed_m_s']-qb['speed_m_s']),yaw_rad_s=abs(qa['angular_velocity']-qb['angular_velocity']),time_s=abs(qa['time']-qb['time']));discrete=all(qa[k]==qb[k] for k in ['collision','damage','wheel_road_contacts','raw_ticks','finished','terminated','truncated']);w=wheel_compare(a['tires'],b['tires']);h=hull_compare(a['raw_hull'],b['raw_hull']);phase=a['memory_after']['C']['phase']==b['memory_after']['C']['phase'];return dict(passed=e['position_m']<=.1 and e['speed_m_s']<=.5 and e['yaw_rad_s']<=.05 and e['time_s']<1e-8 and discrete and w['passed'] and h['passed'] and phase,body_errors=e,discrete_exact=discrete,wheel=w,hull=h,phase_exact=phase)

def prepare(root):
 d=root/'stage421';assert not(d/'plan.json').exists();preflight=read(d/'preflight-result.json');assert preflight['status']=='STATIC_FULL_RECEIPT_PREFLIGHT_PASSED' and preflight['tests']==12
 for f,h in read(d/'original420-manifest.json').items():assert sha(f)==h
 v=read(root/'project-effective-budget-v440.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(29618,84000,0);base=read(root/'stage419/plan.json');p418=read(root/'stage418/plan.json');assert read(root/'stage419/result.json')['tests_run']==32 and read(root/'stage419/ledger-result.json')['tests_run']==4
 files=[Path(__file__),G/'retry/pilot420_backend.py',G/'retry/pilot420_json.py',G/'retry/receipt421_io.py',G/'retry/preflight421.py',root/'stage421/preflight-plan.json',root/'stage421/preflight-result.json',root/'stage421/original420-manifest.json',root/'stage420/plan.json',root/'stage420/result.json',root/'stage420/cost.json',root/'stage420/executed-pilot420_run.py',G/'retry/planner419.py',G/'retry/planner419_model_ledger.py',G/'retry/planner419_design.md',G/'retry/signed417_executor.py',G/'retry/paired417_common.py',G/'retry/headroom413_run.py',G/'retry/terminal410_run.py',G/'retry/terminal410_model.py',G/'retry/source_vehicle_transition.py',G/'retry/terminal409_contract.py',G/'retry/executor397.py',G/'retry/scalar392_audit.py',G/'retry/cross404_common.py',G/'retry/pace269_run.py',root/'stage418/plan.json',root/'stage418/analysis.json',root/'stage418/actual_A/fork-private.json',root/'stage418/actual_A/trace-private.jsonl',root/'stage418/actual_B/trace-private.jsonl',Path(p418['fixed_plan']),root/'stage404/profiles-private.json',root/'stage419/result.json',root/'stage419/ledger-result.json',root/'project-effective-budget-v440.json',root/'research-deadline-current.json']+list((G/'core').rglob('*.py'))
 p=dict(stage=421,preflight_required_before_models=True,preflight_tests=12,prior420_preservation_manifest_sha256=sha(d/'original420-manifest.json'),separate_cost_from420=True,recovery='Identical419selector/C/root/recipe/gain/horizon/projection/ledger; onlyatomiclosslessreceiptIO/readbackverification fixed. No420partialgainrelabelledas421policygain.',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],fixed_plan=p418['fixed_plan'],root='Existing418Aactualfork,currentCpre119physics+beforecurrentnominalmemory+RNG; noactualenv. Knownrootlabelnotdeploymenttrigger.',caps=dict(ticks=32768,worlds=64,CPU_s=150,wall_s=240,max_parallel=1),new_actual_reset_actor_learning_SEALED_reserve_paid_cap=0,qualification='Currentnominalfloat32exact418; restorebody/tiles/progress/finish exact. FreshA13/B13actualbody/wheel/rawhull+phasevs418thenindependentrepeats. Continuousheldparentone vsfreshAfirst. Liveparentsnapshot/memory/RNG unchangedaftereachfork. Firsttechnicalfailureglobalstop.',model_pilot='C0 thenP parents freshindependentroot. Threecurrentdecisionstateupdates each unlessofficialfinish/stop. C0signednominal13duplicates; onlyifinvalidneutral13duplicates, bothinvalidstop. P frozen419all3distinctinitial13+duplicates thencontinueSAME6children nominalCtoofficialfinish/unsafe/progress/cap308; <=13checkpoint; no nestedguardianincertificate. Use419choose unchanged; onlyfirstselectedcommand toparent, neverbranchmemory. After3, sameparentCnominaltailuptoadditional308 tofinish/stop.',progress='ImmutableactualrootGoalLedger retained; allintegratedstates use ForecastLedger/ModelPrediction. Currentreceiptauthentication getsread-onlyGoalLedgervalueview ofpredictedparent, notactualcommit. Persist3.24goal/13deadline acrosssteps andcheckpoints; officialfinishcountsgoal.',time='Officialfinish_time_smustexactlymatchstoredrawclockeventtimestamp; [eventtick-1,eventtick] relativecurrentroot, notlastwrapper/endgeometry/referenceclock. Noepsilon rounding finish event. Unknown/censored/unsafe timeNone.',technical='Anybranchprojection/numeric/phase/restore/repeat/fidelity/parentRNGerrorpreservepartialrecordandglobalstop, noepsilon/repair/retry. Aninitialunsafe/infeasiblepartial<13cannotbeexpressedbyfrozen419receipt; preserveitandstopprotocolratherthanpadcounts. Unsafeorunfinishedtail>=initial13ineligiblewithnoestimatedtime. Baselineguardianbothinvalidglobalstop. Costcapglobalstop.',qualification_scope='OnlyfirstrootA/B13vsactual418isactualfidelity. Allsubsequentstates,neutrals/tails,modelparentfirststepcomparisonsaremodel-only, nolonghorizonactualqualification.',accounting='Chargeeachmodelworldbeforeconstructorandraw4beforewrapper-model-step, retainpartial/unconfirmed. Per-tag requiredinitial/requiredtail/independentrepeat/qualification/parent/tailticks andCPU. First13andtail sameworld, no re-integration orduplicatebilling. Worldholds sequentialsimulationonly. Actualcountersall0, modelnotchargednative.',sources={str(f):sha(f) for f in files},protected=base['protected'],original408_preserve=base['original408_preserve'])
 for f,h in {**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_interval_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,total_preparation_fully_measured=False,scope=read(d/'preparation-opening.json')['scope']));print('421 frozen',sha(d/'plan.json'))

class Pilot:
 def __init__(self,root,meter,fixed,pace,state,memory,actual_ledger,rng):
  self.root=root;self.d=root/'stage421';self.meter=meter;self.fixed=fixed;self.pace=pace;self.state=state;self.memory=memory;self.actual_ledger=actual_ledger;self.actual_digest=actual_ledger.digest();self.archive_rng=rng;self.children=[];self.decisions=[];self.results=[];self.policy_digest=fingerprint(dict(signed=sha(G/'retry/signed417_executor.py'),rules=sha(G/'retry/planner419.py'),fixed=sha(Path(meter.p['fixed_plan'])),pace=pace.tolist()))
 def new(self,state,memory,ledger,label,recipe='nominal',tag='required'):
  c=Child(self.meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,self.fixed,self.pace,label,recipe,tag);self.children.append(c);return c
 def assert_actual(self):
  if self.actual_ledger.digest()!=self.actual_digest:raise TechnicalStop('immutable_actual_ledger_changed')
 def unchanged(self,parent,ph,mh,rh):
  self.assert_actual()
  if fingerprint(snapshot(parent.m))!=ph or fingerprint(parent.ctrl.memory())!=mh or rnghash()!=rh:raise TechnicalStop('live_model_parent_memory_RNG_changed')
 def close_saved(self,child):child.dump(self.d);child.close()
 def qualify(self):
  parent=self.new(self.state,self.memory,self.actual_ledger,'qual_parent',tag='qualification_parent');nominal=parent.ctrl.act(parent.m);a_ref=[json.loads(x) for x in (self.root/'stage418/actual_A/trace-private.jsonl').read_text().splitlines()][118:];b_ref=[json.loads(x) for x in (self.root/'stage418/actual_B/trace-private.jsonl').read_text().splitlines()][118:]
  if nominal.tolist()!=a_ref[0]['nominal']:raise TechnicalStop('current_nominal_not_exact_actual418')
  ph=fingerprint(snapshot(parent.m));mh=fingerprint(parent.ctrl.memory());rh=rnghash();held={};records={}
  for recipe,refs in [('nominal',a_ref),('fullgas',b_ref)]:
   pair=[]
   for rep in range(2):
    tag='qualification_required' if rep==0 else 'qualification_repeat';c=self.new(self.state,self.memory,self.actual_ledger,'qual_'+recipe+'_'+str(rep+1),recipe,tag);c.initial13(tag);c.dump(self.d);self.unchanged(parent,ph,mh,rh);checks=[shapecheck(f,r) for f,r in zip(c.rows,refs)]
    if c.status!='ACTIVE' or len(checks)!=13 or not all(z['passed'] for z in checks):raise TechnicalStop('actual418_body_wheel_rawhull13:'+recipe)
    if any(f['memory_before']['C']['phase']!=r['memory_before']['C']['phase'] for f,r in zip(c.rows,refs)):raise TechnicalStop('actual418_Cphase_mismatch')
    records[recipe+'_'+str(rep+1)]=checks;pair.append(c)
   if pair[0].signature()!=pair[1].signature():raise TechnicalStop('qualification_repeat:'+recipe)
   held[recipe]=pair[0];self.close_saved(pair[1])
  parent.one('qualification_parent_step',prepared_nominal=nominal,prepared_before=self.memory);z=compare_frames(parent.rows[0],held['nominal'].rows[0])
  if not z['passed']:raise TechnicalStop('qualification_continuous_parent_first_step')
  save(self.d/'qualification.json',dict(passed=True,current_nominal_exact=True,actual13_checks=records,parent_first_step=z,actual_root_ledger_unchanged=True,global_RNG_unchanged=True,scope='Onlyactual418A/B13rootcalibration, notnewstates/longtail.'))
  for c in [parent,*held.values()]:self.close_saved(c)
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
  schedule=query_schedule(ctx,Budget(32768-self.meter.b['reserved_ticks'],64-self.meter.b['worlds']))
  if schedule.mode!='STATE_QUERY_LONG_C_WITNESSES':raise ResourceStop('full_frozen_planner_query_budget_not_available')
  state=snapshot(parent.m);ph=fingerprint(state);mh=fingerprint(parent.ctrl.memory());rh=rnghash();pairs={};eval_order=[r for r in ['nominal','neutralbrake','fullgas'] if r in schedule.recipes]
  for recipe in eval_order:
   pair=[]
   for rep in range(2):
    tag='planner_required_initial13' if rep==0 else 'planner_repeat_initial13';c=self.new(state,before,ctx.ledger,label+'_'+recipe+'_'+str(rep+1),recipe,'planner_required' if rep==0 else 'planner_independent_repeat');c.initial13(tag);c.dump(self.d);self.unchanged(parent,ph,mh,rh);pair.append(c)
   if pair[0].signature()!=pair[1].signature():raise TechnicalStop('planner_initial13_repeat')
   if not pair[0].initial_ok:raise TechnicalStop('partial_initial_ineligible_419_receipt_stop_without_padding')
   pairs[recipe]=pair
   if recipe=='neutralbrake' and not pairs['nominal'][0].initial_safe and not pair[0].initial_safe:raise PilotStop('planner_baseline_guardian_both_infeasible')
  for recipe,pair in pairs.items():
   for rep,c in enumerate(pair):
    if c.initial_safe and c.initial_progress:c.continue_tail('planner_required_tail' if rep==0 else 'planner_repeat_tail')
    c.dump(self.d);self.unchanged(parent,ph,mh,rh)
   if pair[0].signature()!=pair[1].signature():raise TechnicalStop('planner_full_C_tail_repeat')
  receipts={r:cs[0].evidence(ctx) for r,cs in pairs.items()};decision=choose(ctx,receipts)
  payload=dict(query=asdict(schedule),context=asdict(ctx),evidence={r:asdict(e) for r,e in receipts.items()},decision=asdict(decision),scope='AllnewstatesandlongtailsMODEL_ONLY, onlyinitialroot13A/Bwasactualcalibrated.')
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
  for index in range(3):
   if parent.status!='ACTIVE':break
   before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m);ctx=capture_context(parent.m,parent.ctrl,before,nominal,parent.ledger,self.fixed,self.policy_digest,self.archive_rng,self.actual_digest)
   if ctx.gate()!='QUERY_CURRENT':raise TechnicalStop('current_context:'+ctx.gate())
   label=name+'_decision'+str(index+1)
   selected=self.guardian(parent,ctx,before,label) if name=='C0' else self.planning_query(parent,ctx,before,label)
   parent.one('parent_'+name+'_advance',first_override=selected['first']['command'],prepared_nominal=nominal,prepared_before=before);check=compare_frames(parent.rows[-1],selected['first']);self.assert_actual()
   if not check['passed']:raise TechnicalStop('new_model_parent_vs_selected_first')
   if parent.status in ['UNSAFE','INFEASIBLE','CENSORED']:raise PilotStop('parent_first_action_'+parent.status)
   record=dict(policy=name,relative_decision=index+1,selected_recipe=selected['recipe'],parent_model_clock=parent.ledger.last_clock_tick,parent_model_progress=parent.ledger.progress_m,selected_first_check=check,choice=selected.get('summary'),actual_ledger_unchanged=True,new_state_actual_physics_qualified=False);self.decisions.append(record);save(self.d/'decisions-private.json',self.decisions);count+=1
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
 d=root/'stage421';p=read(d/'plan.json');assert not(d/'opening.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));meter=Meter(d);pilot=None;stage='root';status='STARTED';error=None
 def timeout(*a):raise ResourceStop('CPU150_wall240_signal')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.01,149-time.process_time()));signal.setitimer(signal.ITIMER_REAL,239)
 try:
  fork=read(root/'stage418/actual_A/fork-private.json');state=from_actual_full(fork);memory=fork['controller']['before'];clock=round(state['physical']['actual_time']*50);actualrow=json.loads((root/'stage418/actual_A/trace-private.jsonl').read_text().splitlines()[118]);actual=GoalLedger(actualrow['progress_before'],actualrow['goal_before'],H-(actualrow['deadline_before']-(actualrow['step']-1)),clock);fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);pilot=Pilot(root,meter,fixed,pace,state,memory,actual,fork['RNG']);stage='qualification';pilot.qualify();print('421actual13qualification passed',flush=True)
  for name in ['C0','P']:stage='policy_'+name;pilot.policy(name);print('421 '+name+' parent model continuation finished',flush=True)
  status='MODEL_CLOSEDLOOP_PILOT_COMPLETED'
 except BaseException as e:status='MODEL_PILOT_STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc()))
 finally:
  if pilot:pilot.closeall()
  else:meter.closeall()
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  meter.persist()
 results=[] if pilot is None else pilot.results;gain=None
 if len(results)==2 and all(z['official_finish'] for z in results):A=results[0]['finish_ticks'];B=results[1]['finish_ticks'];gain=[(A['lo']-B['hi'])/50,(A['hi']-B['lo'])/50]
 q=dict(stage=421,status=status,last_stage=stage,error=error,policies=results,decision_count=0 if pilot is None else len(pilot.decisions),model_remaining_finish_gain_bracket_s=gain,model_strict_gain=bool(gain and gain[0]>0),actual_gate_opened=False,new_actual_reset_actor_learning_SEALED_reserve_paid=0,prior420_partial_result_not_relabelled=True,actual_root_ledger_unchanged=True if pilot is None else pilot.actual_ledger.digest()==pilot.actual_digest,long_tail_actual_physics_qualified=False,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'));save(d/'result.json',q);print(json.dumps(q))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
