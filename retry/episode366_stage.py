"""One frozen365 T29510 actual episode, historical363/357 comparison only."""
import datetime,time
from pathlib import Path
import sys
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
 D=R/'stage366';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
 if full:
  for f,h in p['source_hashes'].items():assert sha(f)==h,f
 return p

def legacy_support(value):
 if isinstance(value,list):return [legacy_support(x) for x in value]
 if isinstance(value,dict):return {k:legacy_support(v) for k,v in value.items() if k!='positive_history'}
 return value

def build(R):
 D=R/'stage366';assert not D.exists();D.mkdir(mode=0o700);q=read(R/'stage365/plan.json');hist=read(R/'stage363/plan.json');cfg=q['configs']['variant'];base=hist['config'];case=hist['cases']['T29510'];assert read(R/'stage365/run-result.json')['passed'] and read(R/'stage365/final-report-verification.json')['cached_candidate_gate']
 assert sha(cfg['archive_path'])==cfg['archive_sha256']=='65df88a5b2391675e49c3f39259adab0f8a791da5ab58ea620cbe130b0a9ce34' and sha(base['archive_path'])==base['archive_sha256']=='b03a65de6410b2fa4805eefcd7a5a05ec246fc27843bdc40facc938927e665ad'
 assert cfg['worker_path']==base['worker_path'] and cfg['worker_sha256']==base['worker_sha256']==sha(cfg['worker_path']) and cfg['assets']==base['assets'] and cfg['constants']==base['constants']
 assert set(cfg['members_sha256'])==set(base['members_sha256']) and {n for n,h in cfg['members_sha256'].items() if h!=base['members_sha256'][n]}=={'retry/support342_logic.py','retry/nominal238_base.py'}
 for f,h in hist['source_hashes'].items():assert sha(f)==h,f
 assert case==read(R/'stage330/plan.json')['cases']['T29510'];v=read(R/'project-effective-budget-v381.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1291215,22190,84000,0)
 files=[G/f'retry/{n}.py' for n in ['episode366_stage','episode366_run','frozen_composite_runtime','source_vehicle_transition','episode337_run','pedal331_run','probe338_stage','package349_run','diagnose','full_route_reproduction','history365_logic','lineage339_audit','confidence341_run']]+[G/'env_wrapper.py',G/'damage.py',R/'stage365/plan.json',R/'stage365/summary-private.json',R/'stage365/final-report-verification.json',R/'stage363/plan.json',R/'stage363/summary-private.json',R/'project-effective-budget-v381.json',R/'research-deadline-current.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',Path(cfg['archive_path']),Path(base['archive_path']),Path(cfg['worker_path']),Path(q['sandbox_path'])]+[R/'stage363/T29510/B'/n for n in ['result.json','trace-private.jsonl','frames-actions-private.npz','initial-scene-private.json','initial-RNG-private.json','reset-policy-private.json','ready-private.json']]+list((G/'core').rglob('*.py'))
 p=dict(stage=366,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=cfg,case=case,expected_initial_observation_sha256=hist['initial_observations']['T29510'],observer_rng_seed=hist['observer_rng_seed'],sandbox_path=q['sandbox_path'],episode_cap=2000,total_native_cap=2000,actor_act_cap=2000,reset_cap=1,
 authorization='Explicitparent366onefrozen365T29510actualepisode, reserve2000withinexisting22190research, actualcostonly. No grant,candidatechange,retry,newcontrol,cache,auxiliaryphysics,learning,protectedopeningorpromotion. Reserve84000unchanged.',
 comparison='Historical363T29510/357252actions/lap20120only. Samecase/init/RNG/environment/runtime/models andsamepassiveworker. Twochangedpolicymembersonepositive-historyconcept. Diagnosticpositive_historyfielddifference recordedseparately; striponlythisnewfieldtoqualifyoriginalsupportrecord. Comparealloriginalsemanticoutputs/path/control/normalmemory/physics/accessRNG/rawcontactswherecommon; noforcedhistory.',
 contract='Ownpixels, executereturnedfullcontrolsunchangedwithnormalmemory. GTonlyreadonlyinitialidentity/evaluatorcaptureandposthocdiagnosis, neverpolicycontrol. Freshactual365episode distinctfrom365cachequalification.',
 gates='Posthocactual58->59unique2mdeduppositivehistory,60-63supportpreservation,andallknownsupported direct/birth-supportedretained losses. Auditpositive-transferambiguityandmissingGT, notclaimresolutionofprior62ambiguousedgesor12/16missingGTcontexts. Anytechnical/source/reset/interfacefailure stops; noautomaticretry.',
 stops='Firstofficialfinish/retirement/otherofficialtruncation, else2000protocolcensor/deadline. No2038extension. Singleknownconditionnotgeneralization orautomaticpromotion.',budget=dict(research_before=22190,episode_reservation=2000,additional_research=0,new_environment_resets=1,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
 save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'reservation.json',p['budget']);save(D/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=2000,episode_cap=2000,actor_act_cap=2000,reset_cap=1));print('366registered onefrozen365T29510actualrun cap2000 from22190; history363only, reserve84000unchanged.',flush=True)
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
