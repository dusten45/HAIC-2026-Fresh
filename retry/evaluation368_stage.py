"""Register16 frozen365 known-condition runs under existing21646 total actions."""
import datetime,time
from pathlib import Path
import sys
from retry.path271_run import read,save,sha
from retry.lineage354 import baseline_folder,safe
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
 D=R/'stage368';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
 if full:
  for f,h in p['source_hashes'].items():assert sha(f)==h,f
 return p

def verify_case(R,key,full=False):
 p=verify(R,full);assert key in p['order'];cap=read(R/'stage368'/key/'native-budget.json')['total_cap'];return dict(config=p['config'],case=p['cases'][key],expected_initial_observation_sha256=p['initial_observations'][key],observer_rng_seed=p['observer_rng_seeds'][key],sandbox_path=p['sandbox_path'],episode_cap=cap,historical_folder=p['historical357_paths'][key])

def build(R):
 D=R/'stage368';assert not D.exists();D.mkdir(mode=0o700);q=read(R/'stage365/plan.json');cfg=q['configs']['variant'];old=read(R/'stage330/plan.json');p363=read(R/'stage363/plan.json');prior=read(R/'stage363/summary-private.json');order=[k for k in old['roads'] if k not in ['T29510','N2']];assert order==['T2950','T2953','T2956','T2959','O0','O2','N0','N1','N3','T2951','T2952','T2954','T2955','T2957','T2958','T29511']
 assert sha(cfg['archive_path'])==cfg['archive_sha256']=='65df88a5b2391675e49c3f39259adab0f8a791da5ab58ea620cbe130b0a9ce34' and sha(cfg['worker_path'])==cfg['worker_sha256'] and read(R/'stage367/final-report-verification.json')['passed']
 v=read(R/'project-effective-budget-v383.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1291759,21646,84000,0,1397405)
 files=[G/f'retry/{n}.py' for n in ['evaluation368_stage','evaluation368_episode','evaluation368_run','evaluation368_close','lineage354','frozen_composite_runtime','source_vehicle_transition','episode337_run','pedal331_run','probe338_stage','package349_run','diagnose','full_route_reproduction','confidence341_run','history365_logic','lineage339_audit','episode367_stage']]+[G/'local_runner.py',G/'env_wrapper.py',G/'damage.py',R/'stage365/plan.json',R/'stage365/summary-private.json',R/'stage363/plan.json',R/'stage363/summary-private.json',R/'stage330/plan.json',R/'stage349/candidate/reset-private.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',R/'project-effective-budget-v383.json',R/'research-deadline-current.json',Path(cfg['archive_path']),Path(cfg['worker_path']),Path(q['sandbox_path'])]+list((G/'core').rglob('*.py'))
 baselines={};hist357={};paths={};seeds={};table={x['condition']:x for x in prior['table']}
 for key in old['roads']:
  f=baseline_folder(R,old,key);br=read(f/'result.json');job=read(f/'job.json');assert job['case']==old['cases'][key] and br['initial_observation_sha256']==old['initial_observations'][key] and br['geometry_sha256']==old['cases'][key]['road_geometry_sha256'] and br['archive_sha256']==job['config']['archive_sha256']==old['baseline296']['config']['archive_sha256'];baselines[key]=safe(br);files += [f/'job.json',f/'result.json']
  stage=p363['existing_actual357'].get(key,363);folder=R/f'stage{stage}'/key if stage==363 else R/f'stage{stage}';pp=read(R/f'stage{stage}/plan.json');cc=pp['cases'][key] if stage==363 else pp['case'];assert cc==old['cases'][key] and pp['config']['archive_sha256']=='b03a65de6410b2fa4805eefcd7a5a05ec246fc27843bdc40facc938927e665ad' and pp['config']['worker_sha256']==cfg['worker_sha256'];rr=read(folder/'B/result.json');hist357[key]=safe(rr);assert {k:table[key]['frozen357'][k] for k in safe(rr)}==safe(rr);paths[key]=str(folder);seeds[key]=pp['observer_rng_seed'];files += [R/f'stage{stage}/plan.json',folder/'B/result.json']
  if key in order:files += [folder/'B'/n for n in ['trace-private.jsonl','frames-actions-private.npz','initial-scene-private.json','initial-RNG-private.json','reset-policy-private.json','ready-private.json']]
 for stage,key in [(366,'T29510'),(367,'N2')]:
  pp=read(R/f'stage{stage}/plan.json');assert pp['config']['archive_sha256']==cfg['archive_sha256'] and pp['case']==old['cases'][key];files += [R/f'stage{stage}/plan.json',R/f'stage{stage}/B/result.json',R/f'stage{stage}/summary-private.json']
 p=dict(stage=368,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],order=order,all18_order=old['roads'],cases={k:old['cases'][k] for k in order},initial_observations={k:old['initial_observations'][k] for k in order},config=cfg,sandbox_path=q['sandbox_path'],observer_rng_seeds=seeds,baseline296=baselines,historical357=hist357,historical357_paths=paths,existing_actual365=dict(T29510=366,N2=367),
 authorization='Explicitparent368: existing21646totalnativecap,16remainingcasesoneepisodeeach,max2000percase. No newgrant, reserve84000unchanged. T29510/N2notreexecuted; no candidatechange,tuning,retry,newcontrol/cache,paidresource,protectedopeningorpromotion.',
 gates='Freshresetidentityandhistorical357initphysics/accessRNG/runtime/originalresetprojection; samecaseobserverRNGseed. Postepisode before nextreset: knownsupported directorbirth-supportedretainedloss or technical/integrityerror stopsbatch. Positive-transferambiguityandmissingGTreported, notclaimedresolved. OrdinaryDNFrecordedandcontinue;damage diagnostic.',
 stops='Officialfinish/retirement/otherofficialtruncationfirst,elsepercasecap=min(2000,remainingglobal21646),deadline/technicalstop. Whenremainingzero,stopandlistunmeasuredwithoutgrant. No2038orinternalextension. Historicalfull-outputcomparisonisdiagnostic,noforcedhistory.',
 contract='Ownpixels/fullreturnedfloat32commands/normalmemory. GTonlyreadonlyinitialidentity/evaluatorcaptureandposthocdiagnosis,neverruntimefeature. Sequentialintercasegate; existingknownconditionsonly, nonewDEV/HOLDOUT/SEALED.',
 inference='RepeatedknownTRAIN/knowncaseafteradaptiveresearch; historical357and296comparisonsnotnewpairedcontrolsorunbiasedgeneralization.18tablecombines16newand2prior365episodes. Completionprimary,common-completionlapdeltasconditional,DAMAGEdiagnosticonly.',budget=dict(research_before=21646,additional_research=0,total_native_cap=21646,episode_max=2000,max_resets=16,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
 save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'reservation.json',p['budget']);save(D/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=21646,reset_cap=16));print('368registered16cases frozen365, totalexisting21646/percase<=2000; no grant/reserveuse; prior2notrepeated.',flush=True)
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
