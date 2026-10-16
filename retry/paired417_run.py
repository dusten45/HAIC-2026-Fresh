"""Once-only pre119 C nominal/full-gas test, conditional actual pairs behind all source gates."""
import ast,copy,datetime,json,math,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.paired417_common import *
from retry.fork394_run import complete_state
from retry.terminal410_model import from_actual_full
from retry.signed417_executor import CoherentExecutor as Signed
from retry.executor397 import CoherentExecutor as Old
from retry.cross404_common import G

def normal_gate(root,fixed,pace):
 rows=[json.loads(t) for t in (root/'stage411/policy_C/trace-private.jsonl').read_text().splitlines()];checks=[]
 for row in rows:
  if row['nominal_memory_after']['C']['phase']!='FIRST_LAP':continue
  memory=row['memory_before']['C'];a=policy(fixed,pace);b=Old(fixed);b.nodes=np.asarray(fixed['free_profile']['speed'])*pace
  for c in [a,b]:
   for k,v in memory.items():setattr(c,k,v)
  state=row['pre'];finish=dict(finish_time_s=None,candidate_crossing_time_s=None);x,_=a.act(state,np.asarray(row['nominal'],np.float32),finish);y,_=b.act(state,np.asarray(row['nominal'],np.float32),finish);passed=x.tolist()==y.tolist()==row['nominal'];checks.append(dict(step=row['step'],passed=passed))
 if len(checks)!=188 or not all(z['passed'] for z in checks):raise ModelFailure('signed188normal_commands_changed')
 return dict(passed=True,rows=len(checks),checks=checks)

def prepare(root):
 d=root/'stage417';assert not(d/'plan.json').exists();base=read(root/'stage416/plan.json');v=read(root/'project-effective-budget-v436.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(29880,84000,0);p411=read(root/'stage411/plan.json');fixed=read(Path(p411['fixed_plan']));line=np.asarray(fixed['line']);old=[json.loads(t) for t in (root/'stage411/policy_C/trace-private.jsonl').read_text().splitlines()];anchor=canonical_projection(line,old[118]['pre']['pos'],old[118]['pre']['vel'],'FIRST_LAP')['arc'];original=(G/'retry/executor397.py').read_text();replacement="if sigma<-.1:raise ExecutorDomainError('Meaningful_negative_progress_domain')";assert (G/'retry/signed417_executor.py').read_text()==original.replace("if sigma<0:raise ExecutorDomainError('Negative_progress_domain')",replacement)
 files=[Path(__file__),G/'retry/paired417_common.py',G/'retry/paired417_actual.py',G/'retry/signed417_executor.py',G/'retry/executor397.py',G/'retry/closed411_run.py',G/'retry/terminal410_run.py',G/'retry/terminal410_model.py',G/'retry/headroom413_run.py',G/'retry/source_vehicle_transition.py',G/'retry/terminal409_contract.py',G/'retry/fork394_run.py',G/'retry/loss389_replay.py',G/'retry/cross404_common.py',G/'retry/pace269_run.py',G/'env_wrapper.py',G/'damage.py',G/'retry/domain416_next_design.md',root/'stage411/plan.json',root/'stage411/policy_C/initial-private.json',root/'stage411/policy_C/trace-private.jsonl',root/'stage413/actual_A/trace-private.jsonl',Path(p411['fixed_plan']),root/'stage404/profiles-private.json',root/'project-effective-budget-v436.json',root/'research-deadline-current.json']+list((G/'core').rglob('*.py'))
 p=dict(stage=417,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],case=p411['case'],fixed_plan=p411['fixed_plan'],anchor_step=119,prefix_actions=118,H=13,exit_original_arc=anchor+30,exit_distance_m=30,goal_distance_m=3.24,deadline_actions=13,model_caps=dict(ticks=8192,worlds=160,CPU_s=45,wall_s=90),actual_caps=dict(wrappers=400,resets=2,CPU_s=90,wall_s=180),max_parallel=1,new_actor_learning_SEALED_reserve_paid=0,signed_copy='Exact397copy, onlystrictsigma<0 domain guard becomesexistingmeaningfulsigma<-.1; bodyforward<-.1safety retained. No sigma clip/epsilon/COMorigin/projection/phase/target/finish changes; normal411188commands exactbeforeworlds.',source_order='188normalfirst; continuoussourceprefix118storedCactualcommands, body/wheel vsactual andrawhullfirstpre vsactual; nominalA1sealedthenactualnominal13body/wheel/rawfirstpre, A2; B1,B2; Apost; parentcontinuous13 vsAfullrawhulls/body/wheel. Allinput/RNG/parentimmutable, restoreexact. Firstmodel/source/fidelity/domain/vertex/safetyfailurestop, nootherwindow/repair.',raw_hull_reference_scope='411actualhasrawtiresandboundarypre/postbutnotintermediaterawhulls. Sourcefullrawhullgate continuousparent vsrestoredbranches +existingactualCOMmetadata; actualrawfirstpre matchesboundary. Do notclaimhistoricalactualmidtickhullreference. Ifactualopens, collectallrawhullsandcompareprefix+firstchanged+matchingrecipe13torealrawphase.',time_gate='Onlybothvalidandexitreached, raw20mstickintegerbrackets Bupper<=Alower-4rawticks. Timecountsnotfloat-epstuned. Originalreferencearcforallprogress/guard/exit; nofailedtimeimputation.',actual='AthenBfreshresetonce;initialfullsame411, replayhistory118 withownnominalCmemory andstoredselectedprefixcommands including91neutralpulse. Prefixactual/sourcefullrawhull andbody/wheelfidelity, exactactual411sensor/nominal/memory. FullforkA/B/RNGsame. Suffix13 only, signedCownfeedback, same411guardian nominal13twice thenfixedneutralbrake13twiceonlyifinvalid; primaryinvalidbothstop. B119only: nominalguardianplusindependentfullgasfirsttwicevalidationrequired, executeonefrozenfullgas actiononlyifvalid. No repeatedtime-selection. Guardianquerycannotmutatelivefullstate/RNG/controller. Everyselectedfirstprediction actualbody/wheel/rawhull; originalA/Brecipefidelity onlyuntilfirstsemanticguardianoverride, divergedcommandslogged. Firstsafety/progress/fidelity/infeasible/costfailureglobalstop.',accounting='Allsourceandactualguardian modelticks/worlds/CPU/wall inone modelaccount; actualCPU/wall exclusive ofmodelregions. Wrapperreset/stepchargedonlynative; modelstepchargedonlyticks, zero-timecontactsetupseparate. Nativeactualuseonlydeductresearch; noreserve.',fidelity=read(root/'stage413/plan.json')['fidelity'],sources={str(f):sha(f) for f in files},protected=base['protected'],original408_preserve=base['original408_preserve'])
 for f,h in {**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,CPU_fully_measured=False));print('417 frozen',sha(d/'plan.json'))

def run(root):
 from retry.paired417_actual import actual_pairs
 d=root/'stage417';p=read(d/'plan.json');assert not(d/'opening.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 cpu=time.process_time();wall=time.perf_counter();save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));meter=Meter(d);fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);line=np.asarray(fixed['line']);old=[json.loads(t) for t in (root/'stage411/policy_C/trace-private.jsonl').read_text().splitlines()];parent=None;source={};source_arrival={};actual=[];eligible=False;stage='normal188';status='RUNNING';error=None;prefix=[];source_checks=[];telemetry={}
 def timeout(*a):raise Stop('phase_CPU_or_wall_signal')
 handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
 try:
  with meter.model('qualification'):
   save(d/'normal188-qualification.json',normal_gate(root,fixed,pace));stage='prefix';initial=from_actual_full(read(root/'stage411/policy_C/initial-private.json'));parent=meter.world(initial);tr=Trace(lambda:parent.t);memory=old[0]['memory_before'];ctrl=SourceC(fixed,pace,memory)
   expected_meta=json.loads((root/'stage413/actual_A/trace-private.jsonl').read_text().splitlines()[0])['raw_hull'][0]
   for i,r in enumerate(old[:118]):
    nominal=ctrl.act(parent)
    if np.max(abs(nominal-np.asarray(r['nominal'],np.float32)))>1e-6:raise ModelFailure('sourceprefix_nominal_command:'+str(i+1))
    f=modelrow(meter,parent,tr,np.asarray(r['command'],np.float32),i+1,line,ctrl.phase());z=shapecheck(f,r)
    if not z['passed'] or f['safety']:raise ModelFailure('sourceprefix_bodywheelrawpre:'+str(i+1))
    if any(h[k]!=expected_meta[k] for h in f['raw_hull'] for k in ['COM_local','mass','inertia']):raise ModelFailure('sourceCOMmetadata')
    prefix.append(f);source_checks.append(z)
   save(d/'source-prefix-private.json',prefix);save(d/'prefix-qualification.json',dict(passed=True,rows=118,checks=source_checks,full_actual_midhull_reference=False));telemetry['prefix']=tr.overhead();memory=copy.deepcopy(old[118]['memory_before']);state=snapshot(parent);ph=fingerprint(snapshot(parent));mh=fingerprint(memory);rh=rnghash();progress=old[118]['progress_before'];goal=old[118]['goal_before'];deadline=old[118]['deadline_before'];start_arc=canonical_projection(line,list(parent.car.hull.position),list(parent.car.hull.linearVelocity),'FIRST_LAP')['arc'];save(d/'source-entry-private.json',dict(state=state,memory=memory,progress=progress,goal=goal,deadline=deadline,start_arc=start_arc))
   def branch(name,recipe):
    f=forecast(meter,state,memory,fixed,pace,118,progress,goal,deadline,recipe)
    if fingerprint(snapshot(parent))!=ph or fingerprint(memory)!=mh or rnghash()!=rh:raise ModelFailure('sourceparent_memory_RNG_mutation')
    save(d/(name+'-private.json'),f);telemetry[name]=f['overhead'];return f
   stage='nominal';A=branch('A1','nominal');checks=[shapecheck(f,r) for f,r in zip(A['rows'],old[118:131])]
   if len(checks)!=13 or not all(z['passed'] for z in checks) or not A['valid']:raise ModelFailure('source_nominal13_fidelity_or_safety')
   save(d/'nominal-qualification.json',dict(passed=True,rows=13,checks=checks));A2=branch('A2','nominal')
   if sig(A)!=sig(A2):raise ModelFailure('A_independence')
   stage='B';B=branch('B1','fullgas');B2=branch('B2','fullgas')
   if sig(B)!=sig(B2):raise ModelFailure('B_independence')
   source=dict(A=A,B=B);source_arrival={k:arrival(f['rows'],line,start_arc,p['exit_original_arc']) if f['valid'] else dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None) for k,f in source.items()};save(d/'source-arrival.json',source_arrival)
   stage='postreference';Apost=branch('Apost','nominal')
   if sig(A)!=sig(Apost):raise ModelFailure('post_reference_changed')
   stage='continuous_rawhull';ctrl=SourceC(fixed,pace,copy.deepcopy(memory));checksparent=[]
   for i,ref in enumerate(A['rows']):
    f=modelrow(meter,parent,tr,ctrl.act(parent),i+1,line,ctrl.phase());body=row_fidelity(f,old[118+i]);h=hull_compare(f['raw_hull'],ref['raw_hull']);w=wheel_compare(f['tires'],ref['tires']);z=dict(passed=body['passed'] and h['passed'] and w['passed'],bodywheel_vs_actual=body,hull_vs_fresh=h,wheel_vs_fresh=w);checksparent.append(z)
    if not z['passed']:raise ModelFailure('continuous_parent_rawhull:'+str(i+1))
   save(d/'parent-qualification.json',dict(passed=True,checks=checksparent));telemetry['continuous_parent']=tr.overhead()
   eligible=all(f['valid'] and source_arrival[k]['reached'] for k,f in source.items()) and source_arrival['B']['rawtick_bracket'][1]<=source_arrival['A']['rawtick_bracket'][0]-4
   status='SOURCE_PASSED_ACTUAL_ALLOWED' if eligible else 'SOURCE_NO_QUALIFIED_TIME_GAIN'
   save(d/'source-result.json',dict(status=status,actual_gate=eligible,branches={k:dict(valid=f['valid'],safety=f['safety'],domain=f['domain'],goal_reached=f['goal_reached'],actions=len(f['rows'])) for k,f in source.items()},arrival=source_arrival,budget=copy.deepcopy(meter.mb)))
   parent.close();parent=None
  if eligible:
   stage='actual';actual=actual_pairs(root,meter,fixed,pace,source,prefix);status='ACTUAL_PAIRED_COMPLETED' if len(actual)==2 and all(z['status']=='COMPLETED_SAFE_13' for z in actual) else 'ACTUAL_CENSORED_STOP'
 except BaseException as e:error=type(e).__name__+': '+str(e);status='SOURCE_OR_TECHNICAL_STOP' if not meter.nb['actions'] else 'ACTUAL_CENSORED_STOP';save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc()))
 finally:
  if parent:parent.close()
  meter.end_actual();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in handlers.items():signal.signal(s,h)
  meter.persist()
 result=dict(stage=417,status=status,last_stage=stage,error=error,source_gate=eligible,source_arrival=source_arrival,source_branches={k:dict(valid=f['valid'],safety=f['safety'],domain=f['domain'],actions=len(f['rows'])) for k,f in source.items()},actual=actual,budget=read(d/'budget.json'),new_actor_learning_SEALED_reserve_paid=0,wholeworker_CPU_s=time.process_time(),execution_CPU_s=time.process_time()-cpu,execution_wall_s=time.perf_counter()-wall,telemetry=telemetry,plan_sha256=sha(d/'plan.json'));save(d/'result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='telemetry'}))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
