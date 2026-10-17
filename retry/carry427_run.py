"""Explicit once-only actual carry of current-state419 first-twelve choices and fixed guardian."""
import datetime,json,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.carry427_model import ActualMeter,ResourceStop
from retry.carry427_actual import actual_pairs
from retry.qualify427 import qualify
G=Path(__file__).resolve().parents[1]

def verify_revised426(root):
 p=read(root/'stage426/static-repair-plan.json');assert sha(root/'stage426/static-repair-plan.json')==(root/'stage426/static-repair-plan.sha256').read_text().strip();result=read(root/'stage426/static-repair-result.json');assert result['passed'] and result['tests']==28 and result['plan_sha256']==sha(root/'stage426/static-repair-plan.json')
 for name in ['guardian426_confirmed.py','static426_recheck.py']:
  f=G/'retry'/name;assert sha(f)==p['sources'][str(f)]
 assert not read(root/'stage426/static-result.json')['passed'] and not(root/'stage426/opening.json').exists()

def prepare(root):
 d=root/'stage427';assert not(d/'plan.json').exists();verify_revised426(root);old=read(root/'stage418/plan.json');v=read(root/'project-effective-budget-v446.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(28621,84000,0)
 files=set([Path(__file__),G/'retry/carry427_analyze.py',G/'retry/carry423_analyze.py',G/'retry/carry427_actual.py',G/'retry/carry427_model.py',G/'retry/static427.py',G/'retry/guardian426_confirmed.py',G/'retry/static426_recheck.py',G/'retry/qualify427.py',G/'retry/pilot421_run.py',G/'retry/preflight421.py',G/'retry/receipt421_io.py',root/'stage421/plan.json',root/'stage421/result.json',root/'stage421/analysis.json',root/'stage421/cost.json',root/'stage421/decisions-private.json',root/'stage421/preflight-result.json',root/'stage418/plan.json',root/'stage418/actual_A/initial-private.json',root/'stage418/actual_A/fork-private.json',root/'stage418/actual_A/trace-private.jsonl',root/'stage418/actual_B/trace-private.jsonl',root/'project-effective-budget-v446.json',root/'research-deadline-current.json'])
 for stage in [418,421,422,423,424,425,426]:
  p=read(root/('stage'+str(stage)+'/plan.json'))
  for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
  files.update(Path(f) for f in p['sources'])
  if stage in [423,424,425,426]:files.update(f for f in (root/('stage'+str(stage))).rglob('*') if f.is_file())
 preserve={str(f):sha(f) for stage in [420,421,422,423,424,425,426] for f in (root/('stage'+str(stage))).rglob('*') if f.is_file()};save(d/'prior-preservation-manifest.json',preserve);files.add(d/'prior-preservation-manifest.json')
 worst_planner=12*3*(13+308)*4*2;worst_guardian_queries=(310-118)-12;worst_ticks=worst_planner+worst_guardian_queries*208+2;worst_worlds=12*6+worst_guardian_queries*4+3;assert(worst_ticks,worst_worlds)==(129890,795)
 p=dict(stage=427,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],case=old['case'],fixed_plan=old['fixed_plan'],exit_original_arc=old['exit_original_arc'],prefix_actions=118,initial_suffix_actions=13,planner_decisions=12,worst_model_ticks=worst_ticks,worst_model_worlds=worst_worlds,static_caps=dict(CPU_s=60,wall_s=120),worst_case_actual_actions=310,per_arm_actual_cap=310,arc_marker_fractions=[.70,.75,.80,.85,.90,.95],selector_sha256=sha(G/'retry/planner419.py'),signed_sha256=sha(G/'retry/signed417_executor.py'),model_caps=dict(ticks=131072,worlds=1000,CPU_s=600,wall_s=900,concurrent_steps=1),actual_caps=dict(wrappers=310,resets=1,CPU_s=90,wall_s=180,exclude_model_regions=True),research_before=28621,reserve=84000,reserve_used=0,new_actor_learning_SEALED_paid=0,
 purpose='New427authorizationafter426closedfirststaticfailure. Verifyexact426revisedcode/assertions/result hashes; unchanged28assertionsreexecutednewplan. Firstnewstatic/modelerrorblocksactual. Preserve425/426failuresandcosts.',
 protocol='Freezeandrunstored425pending/423partial/408-409andnegativecontrols. Onpassonly: freshheldmodelparentplusnominalindependentrepeatatthe425lastsnapshot; eventAT_ROOTmodelcertificatehasnoactualDONEright. Onqualificationpassonly:P12freshresetonce/history118, reproduce425first176commands/fullrows/memory/clipsexactly, everyactualselectedfirstfidelity/currentparent/RNG/ledger, thenofficialfinishorfirsterror. ExistingC0actual15.080from425historicalonly,nofreshC0.',
 fidelity=old['fidelity'],
 boundaries='GuardianChildonlyseparatespending/futuremodelconfirmationfromplanningtimecertificate. SameSourceC/action/phase/corridor/projection/gain/H13/recipes/419selector; planneralwaysusesunchangedChild, guardiancannotemitEvidence/rankingtime. ActualDONEonlydispatchednativecompletedrowpassing409contract. 425source/partialerror/cost/statusimmutable.',
 stop='Firststaticfailure=>nomodel/actual. Firstmodelqualificationfailure=>noactual. Firstactualsafety/progress/fidelity/restore/domain/parentRNG/memory/cost/deadline/bothguardianinvalid=>globalstop,noretry. Actual310/reset1, unchangeddeadline, nootherroot/gain/recipe/windowsearch.',
 promotion='Pofficialnativefinish+all176exactreproduction/currentfirsttransition/parent/ledgergatesqualifytechnicalreproduction. Compare15.080historicalC0explicitly,nofreshpair/generalization/pixel296proof. Noautomaticnextindependentexperiment.',
 accounting='Wholemodel131072ticks/1000world/CPU600/wall900including2tick3worldqualification; worst129890/795. Actual310/reset1 CPU90/wall180excludingmodel. Allreservationsbeforecalls. Required/repeat/initial/tailseparatetags, samechildinitial13+tail, no425costrecharge. Static60/120,preparationseparate.', sources={str(f):sha(f) for f in sorted(files)},protected=old['protected'],original408_preserve=old['original408_preserve'])
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_interval_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],preparation_CPU_s=None,scope=read(d/'preparation-opening.json')['scope'],total_preparation_fully_measured=False));print('427 frozen',sha(d/'plan.json'))

def run(root):
 d=root/'stage427';p=read(d/'plan.json');assert not(d/'opening.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert read(d/'static-result.json')['passed'];verify_revised426(root)
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 for f,h in read(d/'prior-preservation-manifest.json').items():assert sha(f)==h,f
 save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),static_result_sha256=sha(d/'static-result.json')));meter=ActualMeter(d);actual=[];error=None;status='STARTED';cpu=time.process_time();wall=time.perf_counter()
 def timeout(*a):raise ResourceStop('exclusive_actual_or_model_CPU_wall_signal')
 previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
 try:
  fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);qualify(root,meter,fixed,pace);print('427 pending-root independent model qualification passed; actual425 finish remains unobserved',flush=True);prefix=read(root/'stage417/source-prefix-private.json');actual=actual_pairs(root,meter,fixed,pace,None,prefix);status='P12_TECHNICAL_REPLAY_COMPLETED' if len(actual)==1 and all(z['status']=='COMPLETED_SAFE_OFFICIAL' for z in actual) else 'ACTUAL_CARRY_CENSORED_STOP'
 except BaseException as e:status='ACTUAL_CARRY_TECHNICAL_STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc()))
 finally:
  meter.closeall();meter.end_actual();meter.persist();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in previous.items():signal.signal(s,h)
 result=dict(stage=427,status=status,error=error,actual=actual,budget=read(d/'budget.json'),P_actual_finish_qualified=len(actual)==1 and all(z['completed'] for z in actual),pixel_or_generalization_qualified=False,new_actor_learning_SEALED_reserve_paid=0,plan_sha256=sha(d/'plan.json'),execution_CPU_s=time.process_time()-cpu,execution_wall_s=time.perf_counter()-wall,wholeworker_CPU_s=time.process_time());save(d/'result.json',result);print(json.dumps(dict(stage=427,status=status,error=error,budget=result['budget'],arms=[dict(arm=z['arm'],status=z['status'],error=z['error'],suffix=z['suffix_rows']) for z in actual])))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
