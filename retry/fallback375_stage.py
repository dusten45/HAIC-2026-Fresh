"""Freeze remaining17knownTRAIN, immutable374, cap34000/percase2000."""
import datetime,time,sys,zipfile,hashlib
from pathlib import Path
from retry.path271_run import read,save,sha
from retry.lineage354 import baseline_folder,safe
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
 D=R/'stage375';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
 if full:
  for f,h in p['source_hashes'].items():assert sha(f)==h,f
 return p

def verify_case(R,key,full=False):
 p=verify(R,full);assert key in p['order'];return dict(config=p['config'],case=p['cases'][key],expected_initial_observation_sha256=p['initial_observations'][key],observer_rng_seed=375,sandbox_path=p['sandbox_path'],episode_cap=2000,runtime_versions=p['runtime_versions'])

def build(R):
 D=R/'stage375';assert not D.exists();D.mkdir(mode=0o700);v=read(R/'project-effective-budget-v392.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1306782,41282,84000,0,1432064)
 q=read(R/'stage374/plan.json');cfg=q['config'];assert sha(cfg['archive_path'])==cfg['archive_sha256']=='919832e8ed5d280e65c9b75719c4dcfc494a51198131dc29f71079089a00b04b' and sha(cfg['worker_path'])==cfg['worker_sha256'];assert read(R/'stage374/final-report-verification.json')['actual_run_valid'] and read(R/'stage374/summary-private.json')['judgment']['local_rescue_feasibility_pass']
 base=q['base_config']
 with zipfile.ZipFile(cfg['archive_path']) as z:
  assert set(z.namelist())==set(cfg['members_sha256']) and all(hashlib.sha256(z.read(n)).hexdigest()==h for n,h in cfg['members_sha256'].items());assert not any('h1_' in n or 'support342' in n for n in z.namelist())
 assert set(cfg['members_sha256'])-set(base['members_sha256'])=={'retry/hud248_features.py'} and {n for n,h in base['members_sha256'].items() if cfg['members_sha256'].get(n)!=h}=={'retry/temporal_agent.py'}
 old=read(R/'stage330/plan.json');order=[k for k in old['roads'] if k!='T2950'];assert order==['T2953','T2956','T2959','O0','O2','N0','N1','N2','N3','T2951','T2952','T2954','T2955','T2957','T2958','T29510','T29511']
 files=[G/f'retry/{n}.py' for n in ['fallback375_stage','fallback375_episode','fallback375_run','fallback375_close','lineage354','frozen_composite_runtime','pixel_sandbox_runtime','qualify_pixel_package','source_vehicle_transition','episode337_run','pedal331_run','probe338_stage','package349_run','diagnose','full_route_reproduction','fallback334_math','confidence341_run','pair343_close']]+[G/'README.md',G/'env_wrapper.py',G/'local_runner.py',G/'damage.py',R/'stage374/plan.json',R/'stage374/config-private.json',R/'stage374/B/result.json',R/'stage374/summary-private.json',R/'stage374/support-gate.json',R/'stage374/final-report-verification.json',R/'stage374/commit-receipt.json',R/'stage330/plan.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',R/'current-champion.json',R/'stage373/candidate365-rejected-locked.json',R/'protected-query-ledger-v1.json',R/'HOLDOUT.opened',R/'project-effective-budget-v392.json',R/'research-deadline-current.json',Path(cfg['archive_path']),Path(cfg['worker_path']),Path(q['sandbox_path'])]+list((G/'core').rglob('*.py'));baselines={}
 for k in old['roads']:
  F=baseline_folder(R,old,k);r=read(F/'result.json');j=read(F/'job.json');assert j['case']==old['cases'][k] and r['archive_sha256']==j['config']['archive_sha256']==base['archive_sha256'] and r['initial_observation_sha256']==old['initial_observations'][k] and r['geometry_sha256']==old['cases'][k]['road_geometry_sha256'] and not r['technical_error'] and not r['censored'];baselines[k]=safe(r);files += [F/'job.json',F/'result.json']
 assert all(baselines[k]['completed'] for k in order) and sum(x['completed'] for x in baselines.values())==17
 p=dict(stage=375,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=cfg,base_config=base,package_difference=q['package_difference'],order=order,all18_order=old['roads'],cases={k:old['cases'][k] for k in order},initial_observations={k:old['initial_observations'][k] for k in order},baseline296=baselines,runtime_versions=q['runtime_versions'],sandbox_path=q['sandbox_path'],
 authorization='Explicitparent375:17remainingknownTRAINonly,existing41282research,batchcap34000/percase2000;reuse374T2950withoutreexecution. Actualcostonly,no grant/reserveuse. Frozen374,noothercandidate/tuning/retry/372materials/newsplit/promotion.',
 contract='Ownpixels/fullreturnedfloat32controls/normalmemory. Onlyoriginal374fixedfallback+decoderdiffersfrom296,H1/birthrouting/historyabsent. GTreadonlyposthocdiagnostics,neveractorcontrol. Resetidentityagainstexistingmetadata/image. No historicalforcedactions/pixels/state/RNG;fixedobserver375notclaimedoldRNGmatch.',
 gates='Aftereachcasebeforenextreset,alltrackedhazardsmustreachrouting;knownsupported directorbirth-supportedretainedloss/legality/technical/source/reset/integrityerrorstopsremaining. OrdinaryDNFcontinues. No retry/resampling/substitution;unmeasurednotDNF.',
 stops='Officialfinish/retire/otherofficialtruncationfirst,else2000protocolcensor/currentdeadline/technicalstop. Batch34000. Nointernal2038orbudget/capextension. No stopbecauseperformanceappearsclear.',
 judgment='Reportall18knownTRAINcombining17newwith374T2950. Explicitlytestpreservationof17historical296finishes;completioncountfirst,common-completionlapmean/median/sum/each,DNFnotfakelap. AknownTRAINcriterionpassrequiresall18definitiveandallsupportgates,completioncountgreaterthan17orequal17withstrictnegativecommonmean. Separatelyreportevenoneexistingfinishlost;noautomaticpromotion/newDEV/SEALED. Damageonlydiagnostic.',
 budget=dict(research_before=41282,total_native_cap=34000,per_episode_cap=2000,max_resets=17,additional_research=0,final_reserved_actions=84000,final_reserve_used=0),protected_marker_hashes=q['protected_marker_hashes'],excluded_directory_stats={str(f):f.stat().st_mtime_ns for f in [R/'stage372',R/'stage297']},source_hashes={str(f):sha(f) for f in files})
 save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'reservation.json',p['budget']);save(D/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=34000,reset_cap=17));print('375 registered17remainingTRAIN,immutable374,total34000/percase2000,from41282,noT2950repeat.',flush=True)
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
