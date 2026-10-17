"""442 durable native authority binding then once-only actual C0/P pair."""
from retry.paired442_meter import Meter
import datetime,json,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.proposal429 import bounds
from retry.qualify442 import qualify,qualify_pending
from retry.qualify_parent442 import qualify as qualify_parent
from retry.paired442_actual import actual_pairs
from retry.pilot420_backend import GoalLedger,H,ResourceStop
from retry.terminal410_model import from_actual_full
G=Path(__file__).resolve().parents[1]

def verify436(root):
 d=root/'stage436';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'result.json')['plan_sha256'];assert read(d/'static-result.json')['passed'] and read(d/'static-result.json')['tests']==118;assert read(d/'result.json')['status']=='MODEL_SCOPE_COMPLETED';assert read(d/'qualification.json')['passed'] and read(d/'parent-pending-qualification.json')['passed']
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 return p

def verify437(root):
 p=verify436(root);old=read(root/'stage437/plan.json');r=read(root/'stage437/result.json');assert r['status']=='ACTUAL_PAIR_CENSORED_STOP' and r['budget']['actual']['actions']==118 and r['budget']['actual']['resets']==1;assert read(root/'stage437/static-result.json')['passed']
 for f,h in {**old['sources'],**old['protected'],**old['original408_preserve']}.items():assert sha(f)==h,f
 return old

def verify439(root):
 verify437(root);old=read(root/'stage438/plan.json');p=read(root/'stage439/plan.json');r=read(root/'stage439/result.json');assert r['passed'] and r['tests']==171 and r['plan_sha256']==sha(root/'stage439/plan.json');assert read(root/'stage438/result.json')['status']=='ACTUAL_PAIR_CENSORED_STOP'
 for group in [old['sources'],p['sources'],p['protected'],p['original408_preserve']]:
  for f,h in group.items():assert sha(f)==h,f
 return old,p

def prepare(root):
 d=root/'stage442';assert not(d/'plan.json').exists();old,contract=verify439(root);v=read(root/'project-effective-budget-v461.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27878,84000,0);b=bounds(qualification_ticks=1242,qualification_worlds=35);wt=b['total_tick_cap_required']-b['parent_tick_cap'];ww=b['total_world_cap_required']-2;assert(wt,ww)==(518426,883)
 preserve={str(f):sha(f) for n in range(420,442) for f in (root/('stage'+str(n))).rglob('*') if f.is_file()};save(d/'prior-preservation-manifest.json',preserve);files=set(Path(f) for f in old['sources']);files.update(Path(f) for f in contract['sources']);files.update((G/'retry').glob('*442*.py'));files.update((G/'retry').glob('*440*.py'));files.update([G/'env_wrapper.py',G/'damage.py',root/'project-effective-budget-v461.json',root/'stage439/cost.json',root/'stage439/publication.json',d/'prior-preservation-manifest.json',root/'stage423/actual_C0/initial-private.json',root/'stage423/actual_C0/fork-private.json',root/'stage423/actual_C0/trace-private.jsonl',root/'stage417/source-prefix-private.json']);files.update((G/'core').rglob('*.py'));semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'});deadline=read(root/'research-deadline-current.json')['deadline_utc'];assert deadline=='2026-10-20T10:01:55Z'
 assert v['authorization_end_utc']==deadline=='2026-10-20T10:01:55Z'
 p=dict(stage=442,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,authorization='Explicit442known-conditionactualC0/Ppaironce: fresh118prefixeach, actualcurrentstatefreshmodelqueries, transitionfidelityandfullactualcompletioncontrastonly. No436futurecommandsinselection/noactualretry/pixelpromotion/generalization/learning/HOLDOUT/SEALED/newseed/reserve/paidresource.',case=read(root/'stage418/plan.json')['case'],fixed_plan=old['fixed_plan'],semantic_sources=semantic,model_caps=dict(ticks=524288,worlds=1024,CPU_s=1800,wall_s=2400,max_parallel=1),actual_caps=dict(actions=416,resets=2,C0_actions=198,P_actions=218,CPU_s=240,wall_s=480,exclusive_of_model=True),prefix_actions_each=118,C0_suffix_cap=80,P_suffix_cap=100,P_FIRST_LAP_planner_cap=64,worst_model_ticks=wt,worst_model_worlds=ww,worst_actual_raw_ticks_including_reset=1766,arithmetic=dict(planner64_all3recipes_H13tail308_repeat=b['planner_required_and_repeat_tick_cap'],guardian116queries_two_recipes_repeat=b['guardian_required_and_repeat_tick_cap'],qualification_max_ticks=1242,qualification_worlds=35,actual_parent_model_ticks=0,actual_parent_model_worlds=0,total=wt,worlds=ww),research_before=27878,research_after_worst=27462,reserve=84000,reserve_used=0,
 unchanged='436selector,recipes,gain,H13,tail308,strictbracket,steering,path/safety/progresscriteriaandsourcephysicsunchanged. C0guardianonly; PeligibleFIRST_LAP<=64; registeredpending/FINISH_CONFIRM/capguardianonly. Noaftercaptail.',
 qualification='Verify436frozenstatic118andqualifiedstoredactualreceiptsfirst; rerunfreshobserver423C0/427Pactualreplays2each+12restores2eachand425pending2, then436saved435pendinggate2guardian+ownparentstep. Max1242ticks35worlds; beforeactualreset.',
 canonical_contract='Existingplainonlyafterstrictsupport/finite/keyinspection. Arraydimensionsretainedincludingemptytrailingdimensions. Exacttypedvaluesincludingbool/int/float/signedzero; no numericrounding/tolerance. Mismatchwritesbothrawpickles+normalizedtrees+exactfielddiffprivatebeforestop. Stored437actualfixturewalksrealadapterandcapturewithoutsolver/envconstruction. Original437livelvalueabsentsootherdifferencesnotexcluded; original437failure/costretained.',actual_pending='Read-onlyactualproxy+prospectivePostTrackerTap/nativehistory. ActualAuthority437separatesactualobservationsfrommodelauthority. Routingbridgehasnoplannerranking/actualexecution/DONEright. Liveactualidentity/dispatchcounter/currentfullstate/memory/RNG/ledger/registeredsourceeventrequired. Actualledgercommitrequiresownsuccessfulunconsumedenv.stepdispatchticket+liveofficialtracker; modelcertificatecannotcommit. Staticnegativesmustpassorstopbeforeactual.',
 fidelity=read(root/'stage418/plan.json')['fidelity'],native_binding='NativeAuthority439withchargecallbackandownsuccessfulunconsumedticket. Fullnativebefore/afterstate/RNG/memory/wrapper/clock/finish+rawposttrackerrecordsbeforenativefactandforecastverification. Nativefactscommitwithoutforecasts; failedverificationretainsfactsandlatchesnochange/dispatch. Prefixownnativeledger+exact423prefix/source417fidelity; suffixfreshmodelcurrentqueriesonly. Readonlyobservedroutingvaluesneveractualauthority.',additional_exact_checks='439geometry/IEEEintervalprogress/goalcomparison, exactnumericgoalhitandclock/age/deadline/DONE, currentcopypose/memory/nominalprephysics. Unsupportedbranch/ambiguity/unwrapcutstop; existingbody/wheel/rawhull/phase/clippingsafetyunchanged. Actualqualificationonlyobservedverifiedstates.',
 stop='Firststatic/modelqualification/actualtechnical,domain,numeric,restore,repeat,parentstate/RNG/memory/ledger,fidelity,safety,progress,cost,deadlinefailure=>globalstop,retainallcosts,noactualretry. Insufficientactualpendingconnectionevidence=>stopbeforereset. Unfinishedarmtime/gainnull. Firstmodelerrorstopnorepairaftermodelstart. Premodelobviousimport/serialization/runnerwiringrepaironlywithoriginalattemptpreservedandnostrategy/threshold/capchange.',
 promotion='Bothfreshactualarmsofficialfinish+allchecksrequiredfornewknown-rootactualcontrast. Noindependentseed/generalization/pixelpromotion. Historical436modelgainand425/427actualresultsstayseparate.',sources={str(f):sha(f) for f in sorted(files)},protected=old['protected'],original408_preserve=old['original408_preserve'])
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_interval_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],CPU_s=None,total_preparation_fully_measured=False));print(json.dumps(dict(stage=442,plan_sha256=sha(d/'plan.json'),worst_model_ticks=wt,worst_model_worlds=ww,actual_actions_cap=416,resets_cap=2)))

def run(root):
 d=root/'stage442';p=read(d/'plan.json');assert not(d/'opening.json').exists();assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256'];assert read(d/'static-result.json')['passed'];verify439(root)
 for group in [p['sources'],p['protected'],p['original408_preserve'],read(d/'prior-preservation-manifest.json')]:
  for f,h in group.items():assert sha(f)==h,f
 save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),static_result_sha256=sha(d/'static-result.json')));meter=Meter(d);actual=[];stage='qualification';status='STARTED';error=None
 meter.checkpoint('MODEL_QUALIFICATION_STARTED',actual_dispatch_allowed=False)
 def timeout(*args):raise ResourceStop('exclusive_model_or_actual_time_signal')
 old={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
 try:
  fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);fork=read(root/'stage423/actual_C0/fork-private.json');state=from_actual_full(fork);memory=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);ledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(state['physical']['actual_time']*50))
  with meter.model('qualification_all_before_actual'):
   qualify(root,meter,fixed,pace,state,memory,ledger);qualify_pending(root,meter,fixed,pace)
   if (meter.b['ticks'],meter.b['worlds'])!=(1134,32):raise ResourceStop('base_qualification_frozen_cost')
   meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
   if meter.b['ticks']>1242 or meter.b['worlds']!=35:raise ResourceStop('pending_qualification_cost')
  meter.checkpoint('PRE_MODEL_GATES_PASSED',qualification_passed=True)
  print('442 all stored actual fidelity/restore and pending gates passed; opening once-only actual pair.',flush=True);stage='actual_pair';actual=actual_pairs(root,meter,fixed,pace);status='FRESH_ACTUAL_PAIR_COMPLETED' if len(actual)==2 and all(a['completed'] for a in actual) else 'ACTUAL_PAIR_CENSORED_STOP'
 except BaseException as e:status='TECHNICAL_STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc()))
 finally:
  meter.end_actual()
  with meter.model('final_model_cleanup'):meter.closeall()
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in old.items():signal.signal(s,h)
  meter.persist()
 meter.checkpoint('WORKER_COMPLETE' if status=='FRESH_ACTUAL_PAIR_COMPLETED' else 'WORKER_STOP',status=status,error=error)
 q=dict(stage=442,status=status,error=error,actual=actual,budget=read(d/'budget.json'),pixel_or_generalization_qualified=False,new_actor_learning_HOLDOUT_SEALED_seed_reserve_paid=0,plan_sha256=sha(d/'plan.json'));save(d/'result.json',q);print(json.dumps(dict(stage=442,status=status,error=error,actual_actions=meter.nb['actions'],resets=meter.nb['resets'],ticks=meter.b['ticks'],worlds=meter.b['worlds'])))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
