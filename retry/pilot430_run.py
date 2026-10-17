"""430 fresh model-only pilot, authenticated early physical ineligibility."""
import copy,datetime,json,os,signal,sys,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.pilot428_run import Pilot as Pilot428
from retry.pilot420_backend import *
from retry.pilot430_meter import Meter
from retry.qualify430 import qualify
from retry.guardian426_confirmed import GuardianChild
from retry.early429 import choose,GateProofs,bind_before_query_proof,to_wire,from_wire,encoded,PHYSICAL_REASONS,ProtocolStop
from retry.audit429 import audit_pair
from retry.proposal429 import bounds
from retry.loss389_analyze import read,save,sha
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest
from retry.pilot420_json import json_ready
from retry.pilot421_run import compare_frames
from retry.terminal410_model import from_actual_full
G=Path(__file__).resolve().parents[1]

def scope(name,planner_used,phase):
 if name not in ['C0','P']:raise TechnicalStop('unknown_policy')
 return (80 if name=='C0' else 100),name=='P' and phase=='FIRST_LAP' and planner_used<64

def prepare(root):
 d=root/'stage430';assert not(d/'plan.json').exists();old=read(root/'stage429/recheck-plan.json');prior=read(root/'stage428/plan.json');v=read(root/'project-effective-budget-v449.json')
 assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(28444,84000,0)
 for f,h in {**old['sources'],**old['protected'],**old['original408_preserve']}.items():assert sha(f)==h,f
 for f,h in read(root/'stage429/prior-preservation-manifest.json').items():assert sha(f)==h,f
 b=bounds();assert(b['total_tick_cap_required'],b['total_world_cap_required'])==(519038,882)
 deadline=read(root/'research-deadline-current.json')['deadline_utc'];assert deadline=='2026-10-20T10:01:55Z'
 files=set(Path(f) for f in old['sources']);files.update(G/'retry'/n for n in ['pilot430_run.py','pilot430_meter.py','qualify430.py','static430.py','test_pilot430.py','pilot430_analyze.py']);files.update([root/'project-effective-budget-v449.json',root/'stage429/cost.json',root/'stage429/publication.json'])
 preserve={str(f):sha(f) for n in range(420,430) for f in (root/('stage'+str(n))).rglob('*') if f.is_file()};save(d/'prior-preservation-manifest.json',preserve);files.add(d/'prior-preservation-manifest.json')
 p=dict(stage=430,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,authorization='User16Oct3dayextension/autonomouscontinue; explicit430modelonly. 429expiryinterpretationwaswrong; preservehistoricalreportwithcorrection.',fixed_plan=prior['fixed_plan'],caps=dict(ticks=524288,worlds=1024,CPU_s=1800,wall_s=2400,max_parallel=1),worst_model_ticks=519038,worst_model_worlds=882,bounds=b,new_actual_reset_actor_learning_SEALED_reserve_paid_cap=0,research_before=28444,
 scope='Freshsame423pre119root; C0guardian<=80; PeligibleFIRST_LAPplanner<=64 then guardianonly, Ptotal<=100 includingFINISH_CONFIRM. H13+samechildtail308 unchanged; allrecipes/gain/bracket/guardian/DONEunchanged. Noaftercaptail. Unfinishedparentsarecensorednotestimated. No428UNBOUNDreceiptinput/reconstruction.',
 preintegration='Privatequerycontext+fullglobalRNG+state/memory/ledger+gatebeforechildconstructor; eachworldinput+restoregate+firststepsnapshotbeforeintegration; finish/cost/repeat/parent/RNGproofsbeforechooser. Noassertionofactualfidelityinnewstates. Numericalfidelitygateonlyqualifiesisolatedsaved423/427calibration.',
 qualification='Saved423C0/427Pfullreplaytwice+12restored427statesfirsttransitiontwice1132ticks29worlds. Saved425pendingrootnominaltwice2ticks3worlds. Allbeforepilot. Noactualenvironment.',
 stop='Firststatic/technical/domain/numeric/fidelity/restore/repeat/parentRNG/phase/cost/deadline/guardianunavailable=>globalstop,noinrunrepair/retry. Authenticatedearlyphysicalunsafe1..12isineligiblewithobservedfinitecost/state,noH13padding/time/ranking. Reverse/unknownphysicalflagsremainglobalstop. Requiredrepeatcostretained. ModelonlyfinishnotactualDONE.',
 cache='Noquerycache; allfreshchildren; exactroot/ledger/policybinding. Neverload428UNBOUNDdataintopilot.',sources={str(f):sha(f) for f in sorted(files)},protected=old['protected'],original408_preserve=old['original408_preserve'])
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_interval_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],CPU_s=None,total_preparation_fully_measured=False));print(json.dumps(dict(stage=430,plan_sha256=sha(d/'plan.json'),worst_ticks=519038,worst_worlds=882)))

class Pilot(Pilot428):
 def __init__(self,*args):
  super().__init__(*args);self.d=self.root/'stage430';self.planner_count=0;self.active_context=None
 def new(self,state,memory,ledger,label,recipe='nominal',tag='required'):
  self.meter.capture_inputs(state,memory,ledger,label+'_inputs',context=self.active_context,gate='QUALIFIED_MODEL_ONLY')
  return super().new(state,memory,ledger,label,recipe,tag)
 def validate_child(self,c):
  encoded(dict(rows=c.rows,physical=snapshot(c.m),memory=c.ctrl.memory(),ledger=asdict(c.ledger)))
  if c.status=='TECHNICAL_STOP' or any(set(r['safety'])-PHYSICAL_REASONS for r in c.rows) or (c.status=='UNSAFE' and set((c.error or '').split(','))-PHYSICAL_REASONS):raise ProtocolStop('technical_domain_or_nonphysical_failure')
  if not c.rows:raise ProtocolStop('no_observed_first_action')
 def short_pair(self,parent,ctx,before,label,recipe):
  self.meter.capture_inputs(snapshot(parent.m),before,ctx.ledger,label+'_'+recipe+'_guardian_inputs',context=ctx,gate='CURRENT_GUARDIAN_QUERY')
  result=super().short_pair(parent,ctx,before,label,recipe)
  for c in self.children:
   if c.label.startswith(label+'_'+recipe+'_'):self.validate_saved_child(c)
  return result
 def validate_saved_child(self,c):
  # Children have been closed by the unchanged guardian routine.
  raw=read(self.d/(c.label+'-private.json'));encoded(raw)
  if any(set(r['safety'])-PHYSICAL_REASONS for r in raw['rows']) or (raw['status']=='UNSAFE' and set((raw['error'] or '').split(','))-PHYSICAL_REASONS):raise ProtocolStop('guardian_domain_or_nonphysical_failure')
 def planning_query(self,parent,ctx,before,label):
  schedule=query_schedule(ctx,Budget(524288-self.meter.b['reserved_ticks'],1024-self.meter.b['worlds']))
  if schedule.mode!='STATE_QUERY_LONG_C_WITNESSES':raise ResourceStop('full_frozen_planner_query_budget_not_available')
  state=snapshot(parent.m);ph=fingerprint(state);mh=fingerprint(parent.ctrl.memory());rh=rnghash();pairs={};early={};timings={}
  for recipe in [r for r in ['nominal','neutralbrake','fullgas'] if r in schedule.recipes]:
   pair=[];tm=[]
   for rep in range(2):
    c0=time.process_time();w0=time.perf_counter();tag='planner_required_initial13' if rep==0 else 'planner_repeat_initial13'
    c=self.new(state,before,ctx.ledger,label+'_'+recipe+'_'+str(rep+1),recipe,'planner_required' if rep==0 else 'planner_independent_repeat');c.initial13(tag);c.dump(self.d);self.unchanged(parent,ph,mh,rh);self.validate_child(c);pair.append(c);tm.append(dict(CPU_s=time.process_time()-c0,wall_s=time.perf_counter()-w0))
   if pair[0].signature()!=pair[1].signature():raise TechnicalStop('planner_initial13_repeat')
   pairs[recipe]=pair;timings[recipe]=tm
   if not pair[0].initial_ok:
    paths=[self.d/(c.label+'-private.json') for c in pair];raw=[read(x) for x in paths];rootstate,rootmem,_=ctx.parent.fork_inputs()
    e=audit_pair(raw[0],raw[1],np.asarray(self.fixed['line']),rootstate,rootmem,ctx.parent.raw_clock_tick,[sha(x) for x in paths])
    proofs=GateProofs(True,True,True,True,self.meter.qualification_passed,True,True)
    e=replace(e,cost=replace(e.cost,required_CPU_s=tm[0]['CPU_s'],repeat_CPU_s=tm[1]['CPU_s'],required_wall_s=tm[0]['wall_s'],repeat_wall_s=tm[1]['wall_s']))
    early[recipe]=bind_before_query_proof(e,ctx,proofs);early[recipe].authenticate(ctx)
    wire=to_wire(early[recipe]);path=self.d/(label+'_'+recipe+'-early-private.json');save_receipt(path,wire)
    if from_wire(load_receipt(path))!=early[recipe]:raise TechnicalStop('early_wire_roundtrip')
   if recipe=='neutralbrake' and not(pairs['nominal'][0].initial_ok and pairs['nominal'][0].initial_safe and pairs['nominal'][0].initial_progress) and not(pair[0].initial_ok and pair[0].initial_safe and pair[0].initial_progress):raise PilotStop('planner_baseline_guardian_both_infeasible')
  for recipe,pair in pairs.items():
   if recipe in early:continue
   for rep,c in enumerate(pair):
    if c.initial_safe and c.initial_progress:c.continue_tail('planner_required_tail' if rep==0 else 'planner_repeat_tail')
    c.dump(self.d);self.unchanged(parent,ph,mh,rh);self.validate_child(c)
   if pair[0].signature()!=pair[1].signature():raise TechnicalStop('planner_full_C_tail_repeat')
  receipts={r:early[r] if r in early else cs[0].evidence(ctx) for r,cs in pairs.items()};decision=choose(ctx,receipts)
  payload=dict(query=asdict(schedule),context=asdict(ctx),evidence={r:asdict(e) for r,e in receipts.items() if r not in early},early_evidence={r:to_wire(e) for r,e in early.items()},decision=asdict(decision),preintegration=self.meter.query_proof,scope='430MODEL_ONLY_NEW_AUTHENTICATED_CONTEXT; no428UNBOUNDreuse')
  path=self.d/(label+'-evidence-private.json');dg=save_receipt(path,payload)
  if receipt_digest(load_receipt(path))!=dg:raise TechnicalStop('runtime_receipt_roundtrip')
  self.unchanged(parent,ph,mh,rh);save(self.d/(label+'-receipt-digest.json'),dict(digest=dg,readback_verified=True,parent_unchanged=True,RNG_unchanged=True))
  if decision.recipe is None or decision.status not in ['MODEL_TIME_CHOICE','GUARDIAN_REFERENCE_ONLY']:raise PilotStop('planner_no_qualified_first_action:'+decision.status)
  selected=pairs[decision.recipe][0];summary=dict(decision=asdict(decision),recipes={r:dict(status='EARLY_PHYSICAL_INELIGIBLE' if r in early else cs[0].status,initial_actions=cs[0].initial_count,tail_actions=cs[0].tail_count,finish_ticks=None if cs[0].finish_ticks is None else asdict(cs[0].finish_ticks),authenticated=True,actual_physics_qualified=False) for r,cs in pairs.items()})
  first=copy.deepcopy(selected.rows[0])
  for pair in pairs.values():
   for c in pair:self.close_saved(c)
  return dict(recipe=decision.recipe,first=first,summary=summary)
 def policy(self,name):
  self.active_context=None;parent=self.new(self.state,self.memory,self.actual_ledger,'parent_'+name,tag='pilot_parent');self.assert_actual();count=0;planner_used=0;limit,_=scope(name,0,'FIRST_LAP')
  for index in range(limit):
   if parent.status!='ACTIVE':break
   qc=time.process_time();qw=time.perf_counter();before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m);ctx=capture_context(parent.m,parent.ctrl,before,nominal,parent.ledger,self.fixed,self.policy_digest,self.archive_rng,self.actual_digest);phase=parent.ctrl.phase();ctx.validate()
   if phase=='FIRST_LAP' and ctx.gate()!='QUERY_CURRENT':raise TechnicalStop('current_context:'+ctx.gate())
   if phase not in ['FIRST_LAP','FINISH_CONFIRM']:raise TechnicalStop('unsupported_current_phase')
   label=name+'_decision'+str(index+1);self.active_context=ctx
   self.meter.query_proof=self.meter.capture_inputs(snapshot(parent.m),before,ctx.ledger,label+'_query',context=ctx,gate=ctx.gate())
   qph=fingerprint(snapshot(parent.m));qmh=fingerprint(parent.ctrl.memory());qrh=rnghash()
   _,planned=scope(name,planner_used,phase)
   selected=self.planning_query(parent,ctx,before,label) if planned else self.guardian(parent,ctx,before,label)
   if planned:planner_used+=1
   query_CPU=time.process_time()-qc;query_wall=time.perf_counter()-qw
   self.unchanged(parent,qph,qmh,qrh)
   save_receipt(self.d/(label+'-before-parent-step-private.json'),dict(context=asdict(ctx),query_proof=self.meter.query_proof,selected_recipe=selected['recipe'],first_command=selected['first']['command'],parent_unchanged=True,RNG_unchanged=True,actual_ledger_unchanged=True,actual_execution_allowed=False))
   parent.one('parent_'+name+'_advance',first_override=selected['first']['command'],prepared_nominal=nominal,prepared_before=before);check=compare_frames(parent.rows[-1],selected['first']);self.assert_actual();self.validate_child(parent)
   if not check['passed'] or check['wheel']['clipped_flag_mismatches']!=0:raise TechnicalStop('new_model_parent_vs_selected_first')
   if parent.status in ['UNSAFE','INFEASIBLE','CENSORED']:raise PilotStop('parent_first_action_'+parent.status)
   record=dict(policy=name,relative_decision=index+1,phase=phase,planner_used=planned,query_CPU_s=query_CPU,query_wall_s=query_wall,guardian_certificate=selected.get('certificate'),model_parent_not_actual=True,actual_execution_allowed=False,selected_recipe=selected['recipe'],parent_model_clock=parent.ledger.last_clock_tick,parent_model_progress=parent.ledger.progress_m,selected_first_check=check,choice=selected.get('summary'),actual_ledger_unchanged=True,new_state_actual_physics_qualified=False);self.decisions.append(record);save(self.d/'decisions-private.json',self.decisions);count+=1;print(json.dumps(dict(stage=430,policy=name,decision=count,planner_used=planned,recipe=selected['recipe'],model_ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])),flush=True)
  if parent.status=='ACTIVE':parent.status='SCOPE_CENSORED';parent.error='Noofficialfinishwithinparentactioncap; noaftercaptailorfinishimputation'
  rr=dict(policy=name,status=parent.status,error=parent.error,decisions=count,planner_decisions=planner_used,guardian_decisions=count-planner_used,total_model_actions=len(parent.rows),finish_ticks=None if parent.finish_ticks is None else asdict(parent.finish_ticks),official_finish=parent.status=='FINISHED',scope_censored=parent.status=='SCOPE_CENSORED',observed_model_time_s=sum(r['predicted']['raw_ticks'] for r in parent.rows)/50,actual_ledger_unchanged=True);self.results.append(rr);save(self.d/'policy-results.json',self.results);self.close_saved(parent)
  if rr['status'] not in ['FINISHED','SCOPE_CENSORED']:raise PilotStop(name+'_parent_'+rr['status'])

def qualify_pending(root,meter,fixed,pace):
 d=root/'stage430';full=read(root/'stage425/actual_P/final-private.json');last=json.loads((root/'stage425/actual_P/trace-private.jsonl').read_text().splitlines()[-1]);memory=last['nominal_memory_after'];ledger=GoalLedger(**read(root/'stage425/actual_P/result.json')['actual_ledger']);state=from_actual_full(full);failed=read(root/'stage425/actual_P/actual_P_177_nominal_1-private.json')['rows'][0];rh=rnghash();children=[];signatures=[];records=[]
 meter.capture_inputs(state,memory,ledger,'pending_held_inputs',gate='SAVED_PENDING_QUALIFICATION');held=GuardianChild(meter,state,memory,ledger,fixed,pace,'held_pending_root',world_tag='qualification_pending_parent');ph=fingerprint(snapshot(held.m));nominal=held.ctrl.act(held.m);mh=fingerprint(held.ctrl.memory())
 try:
  for rep in range(2):
   label='pending_nominal_'+str(rep+1);meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='SAVED_PENDING_QUALIFICATION');c=GuardianChild(meter,state,memory,ledger,fixed,pace,label,world_tag='qualification_pending_required' if rep==0 else 'qualification_pending_repeat',confirmation_phase=held.ctrl.phase());children.append(c);c.initial13('qualification_pending_required' if rep==0 else 'qualification_pending_repeat');c.dump(d);z=compare_frames(c.rows[0],failed)
   if not z['passed'] or z['wheel']['clipped_flag_mismatches'] or c.status!='FINISHED' or len(c.rows)!=1 or c.guardian_certificate['kind']!='AT_ROOT_CONFIRMED_IN_MODEL' or c.guardian_certificate['actual_done_allowed'] or c.first_command!=tuple(nominal):raise TechnicalStop('pending_guardian_model_qualification')
   if fingerprint(snapshot(held.m))!=ph or fingerprint(held.ctrl.memory())!=mh or rnghash()!=rh:raise TechnicalStop('pending_parent_RNG_memory_changed')
   signatures.append(c.signature());records.append(dict(check=z,certificate=c.guardian_certificate));c.close()
  if signatures[0]!=signatures[1]:raise TechnicalStop('pending_guardian_independent_repeat')
  if full['wrapper']['finish_time_s'] is not None:raise TechnicalStop('saved425_actual_finish_relabelled')
  save(d/'pending-qualification.json',dict(passed=True,records=records,model_ticks=2,model_worlds=3,actual_DONE_allowed=False));return True
 finally:
  for c in children:
   if not c.closed:
    try:c.dump(d)
    finally:c.close()
  held.dump(d);held.close()

def run(root):
 d=root/'stage430';p=read(d/'plan.json');assert not(d/'opening.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert read(d/'static-result.json')['passed']
 for group in [p['sources'],p['protected'],p['original408_preserve'],read(d/'prior-preservation-manifest.json')]:
  for f,h in group.items():assert sha(f)==h,f
 save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),static_result_sha256=sha(d/'static-result.json')));meter=Meter(d);pilot=None;stage='root';status='STARTED';error=None
 def timeout(*a):raise ResourceStop('CPU1800_wall2400_signal')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.01,1799-time.process_time()));signal.setitimer(signal.ITIMER_REAL,2399)
 try:
  fork=read(root/'stage423/actual_C0/fork-private.json');state=from_actual_full(fork);memory=fork['controller']['before'];clock=round(state['physical']['actual_time']*50);row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);actual=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-(row['step']-1)),clock);fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268'])
  stage='saved423_427_qualification';qualify(root,meter,fixed,pace,state,memory,actual);stage='pending_guardian_qualification';qualify_pending(root,meter,fixed,pace)
  if (meter.b['ticks'],meter.b['worlds'])!=(1134,32):raise TechnicalStop('qualification_cost_not_frozen_bound')
  meter.qualification_passed=True;print('430 physical calibration and restore gates passed: 1134 ticks / 32 worlds',flush=True);pilot=Pilot(root,meter,fixed,pace,state,memory,actual,fork['RNG'])
  for name in ['C0','P']:stage='model_policy_'+name;pilot.policy(name)
  status='MODEL_SCOPE_COMPLETED'
 except BaseException as e:status='MODEL_PILOT_STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc()))
 finally:
  if pilot:pilot.closeall()
  else:meter.closeall()
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  meter.persist()
 results=[] if pilot is None else pilot.results;gain=None
 if len(results)==2 and all(z['official_finish'] for z in results):a=results[0]['finish_ticks'];b=results[1]['finish_ticks'];gain=[(a['lo']-b['hi'])/50,(a['hi']-b['lo'])/50]
 q=dict(stage=430,status=status,last_stage=stage,error=error,policies=results,decision_count=0 if pilot is None else len(pilot.decisions),model_remaining_finish_gain_bracket_s=gain,strict_model_gain=bool(gain and gain[0]>0),actual_gate_opened=False,new_actual_reset_actor_learning_SEALED_reserve_paid=0,actual_root_ledger_unchanged=True if pilot is None else pilot.actual_ledger.digest()==pilot.actual_digest,new_states_actual_physics_qualified=False,cache_hits=0,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'));save(d/'result.json',q);print(json.dumps(dict(stage=430,status=status,error=error,decision_count=q['decision_count'],gain=gain,ticks=meter.b['ticks'],worlds=meter.b['worlds'])))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
