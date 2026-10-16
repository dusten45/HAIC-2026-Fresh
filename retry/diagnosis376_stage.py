"""Register savedT29510-only diagnosis; immutablepolicies, max606act/commit."""
import datetime,time,sys,zipfile
from pathlib import Path
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
 D=R/'stage376';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
 if full:
  for f,h in p['source_hashes'].items():assert sha(f)==h,f
 return p

def build(R):
 D=R/'stage376';assert not D.exists();D.mkdir(mode=0o700);v=read(R/'project-effective-budget-v393.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1311581,36483,84000,0,1432064)
 base=read(R/'stage296/champion-config.json');candidate=read(R/'stage374/config-private.json');assert sha(base['archive_path'])==base['archive_sha256']=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937';assert sha(candidate['archive_path'])==candidate['archive_sha256']=='919832e8ed5d280e65c9b75719c4dcfc494a51198131dc29f71079089a00b04b'
 with zipfile.ZipFile(candidate['archive_path']) as z:decoder=z.read('retry/hud248_features.py')
 asset=D/'observer-hud-private.py';asset.write_bytes(decoder);asset.chmod(0o600);worker=D/'observer-worker-private.py';source=Path(candidate['worker_path']).read_text();needle='from retry.hud248_features import decode';replacement="""import importlib.util
_observer_spec=importlib.util.spec_from_file_location('observer_hud',clean/'observer-hud.py')
_observer_module=importlib.util.module_from_spec(_observer_spec)
_observer_spec.loader.exec_module(_observer_module)
decode=_observer_module.decode""";assert source.count(needle)==1;source=source.replace(needle,replacement);compile(source,str(worker),'exec');worker.write_text(source);worker.chmod(0o600)
 configs={name:dict(cfg,worker_path=str(worker),worker_sha256=sha(worker),assets={'observer-hud.py':dict(path=str(asset),sha256=sha(asset))}) for name,cfg in [('374',candidate),('296',base)]};F=R/'stage375/T29510/B';assert read(F/'result.json')['actual_DNF'] and read(F/'result.json')['native_actions']==303
 job=read(R/'stage295/TRAIN/T29510/g1p4/job.json');baseline=read(R/'stage295/TRAIN/T29510/g1p4/result.json');assert baseline['archive_sha256']==base['archive_sha256'] and baseline['completed'] and baseline['native_actions']==237
 files=[G/f'retry/{n}.py' for n in ['diagnosis376_stage','diagnosis376_replay','diagnosis376_close','frozen_composite_runtime','pixel_sandbox_runtime','qualify_pixel_package','probe338_stage','fallback334_math','fallback334_metrics','confidence341_run']]+[R/'stage296/champion-config.json',R/'stage374/config-private.json',R/'stage375/T29510/native-budget.json',R/'stage375/T29510/reset-qualification.json',R/'stage295/TRAIN/T29510/g1p4/job.json',R/'stage295/TRAIN/T29510/g1p4/result.json',R/'stage295/TRAIN/T29510/g1p4/trace-private.jsonl',R/'current-champion.json',R/'stage296/champion-manifest.json',R/'stage373/candidate365-rejected-locked.json',R/'protected-query-ledger-v1.json',R/'project-effective-budget-v393.json',R/'research-deadline-current.json',worker,asset,Path(candidate['archive_path']),Path(base['archive_path']),Path(candidate['worker_path'])]+[F/n for n in ['result.json','trace-private.jsonl','frames-actions-private.npz','initial-scene-private.json','initial-RNG-private.json','reset-policy-private.json','ready-private.json']]
 sandbox=R/'stage88/pixel-read-sandbox';files.append(sandbox)
 p=dict(stage=376,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],scope='ExistingT29510records295/375only. No newenv/sourcephysics/candidatechange/newsplit/372materials. Fixedpixelactorprobeonlyifneeded,parentauthorized.',configs=configs,sandbox_path=str(sandbox),frames_path=str(F/'frames-actions-private.npz'),actual_trace=str(F/'trace-private.jsonl'),baseline_trace=str(R/'stage295/TRAIN/T29510/g1p4/trace-private.jsonl'),input_count=303,actor_act_cap=606,actor_commit_cap=606,pixel_reset_cap=2,
 order=['374','296'],gates='Reproduceall303actual374controls/features/path/tracker/routing/nominalmemory/originalstateprojectionbefore296counterfactual. Sharedworkeronlyobserverdecoderassetadaptation;policymembers/archivesunchanged. Eacharmowncomputedcontrols/normalmemoryonidenticalstored374inputs. Technical/reproductionerrorstopswithoutretry.',
 analysis='Separateactualold296237features/action/memoryprefixfromfixed374pixels303counterfactual. Firstfallback,transport/retention,opticalmatrix/reason,pre/postmemory,route/target/fullcontrol. PosthocGTposeintervalcheckofHUDyaw/displacementandcoordinateformula;noGTcontrolormodelinput. DonotattributeDNFsolelytofirstdifference;nohistoric296pixels/physicsavailable.',
 stops='Noenvcalls.Capexact606act/commit,2pixelresets;firsterror/deadlineoreachregistered303perarmstops. No extraactor/probe/condition/framecutoffs/parameterfit/newcandidate.',source_hashes={str(f):sha(f) for f in files},protected_hashes={str(f):sha(f) for f in [R/'current-champion.json',R/'stage296/champion-manifest.json',R/'stage373/candidate365-rejected-locked.json',R/'protected-query-ledger-v1.json',R/'project-effective-budget-v393.json']},excluded_directory_stats={str(f):f.stat().st_mtime_ns for f in [R/'stage372',R/'stage297']})
 save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'call-counts.json',dict(actor_act_calls=0,actor_commit_calls=0,pixel_resets=0,new_native_actions=0,new_environment_resets=0));print('376 registeredT29510-only;374reproduce303then296fixedinputs303,max606act/commit,2pixelresets,native0.',flush=True)
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
