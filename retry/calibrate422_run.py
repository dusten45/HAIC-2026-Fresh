"""Explicit bounded actual calibration of current-state419 choices, not a lap test."""
import datetime,json,os,signal,sys,time,traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.calibrate422_model import ActualMeter,ResourceStop
from retry.calibrate422_actual import actual_pairs
G=Path(__file__).resolve().parents[1]

def prepare(root):
 d=root/'stage422';assert not(d/'plan.json').exists();old=read(root/'stage418/plan.json');v=read(root/'project-effective-budget-v441.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(29618,84000,0)
 files=set([Path(__file__),G/'retry/calibrate422_actual.py',G/'retry/calibrate422_model.py',G/'retry/calibrate422_static.py',G/'retry/pilot421_run.py',G/'retry/preflight421.py',G/'retry/receipt421_io.py',root/'stage421/plan.json',root/'stage421/result.json',root/'stage421/analysis.json',root/'stage421/cost.json',root/'stage421/decisions-private.json',root/'stage421/preflight-result.json',root/'stage418/plan.json',root/'stage418/actual_A/initial-private.json',root/'stage418/actual_A/fork-private.json',root/'stage418/actual_A/trace-private.jsonl',root/'stage418/actual_B/trace-private.jsonl',root/'project-effective-budget-v441.json',root/'research-deadline-current.json'])
 for stage in [418,421]:
  p=read(root/('stage'+str(stage)+'/plan.json'))
  for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
  files.update(Path(f) for f in p['sources'])
 preserve={str(f):sha(f) for stage in [420,421] for f in (root/('stage'+str(stage))).rglob('*') if f.is_file()};save(d/'prior-preservation-manifest.json',preserve);files.add(d/'prior-preservation-manifest.json')
 p=dict(stage=422,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],case=old['case'],fixed_plan=old['fixed_plan'],exit_original_arc=old['exit_original_arc'],prefix_actions=118,suffix_actions=13,selector_sha256=sha(G/'retry/planner419.py'),signed_sha256=sha(G/'retry/signed417_executor.py'),model_caps=dict(ticks=32768,worlds=128,CPU_s=150,wall_s=240,concurrent_steps=1),actual_caps=dict(wrappers=400,resets=2,CPU_s=90,wall_s=180,exclude_model_regions=True),research_before=29618,reserve=84000,reserve_used=0,new_actor_learning_SEALED_paid=0,
 purpose='Actualtransition/clippingcalibrationofnewcontinuousselectioncombination; model421gain.62-.66andq1.407remainnotactualevidence.',
 protocol='C0thenPonceeachactualreset/history118+13suffixonly. Initialfullstate/RNG/pixelsandforkbefore/aftermemoryexact418andbetweenarms; allprefixbody/wheel/rawhullgates. C0existingnominal13duplicateguardianwithneutral13duplicatesonlyifnominalinvalid. Pfirst3currentACTUALstatesquery419allthreeinitial13duplicatesthenSAMEchildnominalCtailofficialfinish/stop<=308, frozenstrictbracketselector; remaining10C0guardian. Neverreplay421recipes; differencesreadAFTERqueryonly. Nevercommitbranchmemory.',
 fidelity=old['fidelity'],
 boundaries='ActualGoalLedgercommitsonlyactualpostobservation; ForecastLedgerseparate. Allqueryfullactualparent/memory/globalRNG/ledgerunchanged. Eachactualselectedfirstbody/wheel/rawhull/phase/finishmetadata+rawtickcontract. Inadditionreportandrequirezeroexactclipflagmismatch(selectedandmatching). Activepriorinitial13witnesscheckeduntilcommanddelta>1e-6thenmarkpolicydivergencebeforechangedtransitionandstopthatwitnesscomparison; newselectedfirstalwayschecked. Guardianoverrideandactualpolicyoutcomeexplicitlyseparate. Nochangedoldfidelitythreshold.',
 stop='Firstsafety/fidelity/restore/domain/numeric/parent/RNG/cost/deadlineerrorglobalstop; guardianbothinvalidstop; preservepartialcharges; nootherarm/retry/newwindow/gain/horizon/recipe/actualfull-lap. Unsafeinitialpartialcannotpad419receipt. Neverimputeuncrossedexit/finish.',
 promotion='Onlyactual13transition/clippingqualifiedifboth13safe/goal+fidelity+allgates. Noactualwholefinishgain/pixel/generalizationqualification. Noautomaticnextstage.',
 accounting='Everymodelworldandraw4reservationchargedbeforecall; actualreset/actionbeforecall. Required/repeat/initial/tailseparatetags; queryregionsincludecontext/hash/IO/cleanup. ModelCPUincludesimportsconservatively; actualexcludesmodelregions. Parentactualchargednative, noartificialmodelparent. Preflightstatic0world. Cachedoldsource0newcharge. Preparationseparatepartialscope.',sources={str(f):sha(f) for f in sorted(files)},protected=old['protected'],original408_preserve=old['original408_preserve'])
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_interval_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],preparation_CPU_s=None,scope=read(d/'preparation-opening.json')['scope'],total_preparation_fully_measured=False));print('422 frozen',sha(d/'plan.json'))

def run(root):
 d=root/'stage422';p=read(d/'plan.json');assert not(d/'opening.json').exists() and sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert read(d/'static-result.json')['passed']
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 for f,h in read(d/'prior-preservation-manifest.json').items():assert sha(f)==h,f
 save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),static_result_sha256=sha(d/'static-result.json')));meter=ActualMeter(d);actual=[];error=None;status='STARTED';cpu=time.process_time();wall=time.perf_counter()
 def timeout(*a):raise ResourceStop('exclusive_actual_or_model_CPU_wall_signal')
 previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
 try:
  fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);prefix=read(root/'stage417/source-prefix-private.json');actual=actual_pairs(root,meter,fixed,pace,None,prefix);status='ACTUAL13_CALIBRATION_PAIRED_COMPLETED' if len(actual)==2 and all(z['status']=='COMPLETED_SAFE_13' for z in actual) else 'ACTUAL13_CALIBRATION_CENSORED_STOP'
 except BaseException as e:status='ACTUAL13_CALIBRATION_TECHNICAL_STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc()))
 finally:
  meter.closeall();meter.end_actual();meter.persist();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in previous.items():signal.signal(s,h)
 result=dict(stage=422,status=status,error=error,actual=actual,budget=read(d/'budget.json'),long_actual_finish_gain_qualified=False,pixel_or_generalization_qualified=False,new_actor_learning_SEALED_reserve_paid=0,plan_sha256=sha(d/'plan.json'),execution_CPU_s=time.process_time()-cpu,execution_wall_s=time.perf_counter()-wall,wholeworker_CPU_s=time.process_time());save(d/'result.json',result);print(json.dumps(dict(stage=422,status=status,error=error,budget=result['budget'],arms=[dict(arm=z['arm'],status=z['status'],error=z['error'],suffix=z['suffix_rows']) for z in actual])))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
