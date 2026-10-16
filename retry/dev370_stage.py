"""Freeze reusedDEV12 candidate365, grant7158, max24000/percase2000."""
import datetime,time
from pathlib import Path
import sys
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
 D=R/'stage370';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
 if full:
  for f,h in p['source_hashes'].items():assert sha(f)==h,f
 return p

def verify_case(R,key,full=False):
 p=verify(R,full);assert key in p['order'];return dict(config=p['config'],case=p['cases'][key],expected_initial_observation_sha256=p['initial_observations'][key],observer_rng_seed=p['observer_rng_seed'],runtime_versions=p['runtime_versions'],sandbox_path=p['sandbox_path'],episode_cap=2000)

def build(R):
 D=R/'stage370';assert not D.exists();D.mkdir(mode=0o700);binding=read(R/'stage369/DEV296-exact-contract-private.json');q=read(R/'stage365/plan.json');cfg=q['configs']['variant'];contract=read(R/'stage369/summary-private.json');order=[b['public_label'] for b in binding['exact_bindings']];assert order==['S296'+str(i) for i in range(12)] and binding['frozen_candidate_configuration']==cfg and read(R/'stage369/final-report-verification.json')['passed']
 assert sha(cfg['archive_path'])==cfg['archive_sha256']=='65df88a5b2391675e49c3f39259adab0f8a791da5ab58ea620cbe130b0a9ce34' and sha(cfg['worker_path'])==cfg['worker_sha256'];v=read(R/'project-effective-budget-v385.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1296563,16842,84000,0,1397405)
 files=[G/f'retry/{n}.py' for n in ['dev370_stage','dev370_episode','dev370_run','dev370_close','frozen_composite_runtime','source_vehicle_transition','episode337_run','pedal331_run','probe338_stage','package349_run','diagnose','full_route_reproduction','confidence341_run','history365_logic','lineage339_audit']]+[G/'README.md',G/'local_runner.py',G/'env_wrapper.py',G/'damage.py',R/'stage369/plan.json',R/'stage369/summary-private.json',R/'stage369/DEV296-exact-contract-private.json',R/'stage365/plan.json',R/'stage296/plan.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',R/'current-champion.json',R/'stage297/fresh-DEV-private.json',R/'stage297/screen-seal.json',R/'HOLDOUT.opened',R/'protected-query-ledger-v1.json',R/'stage367/B/reset-policy-private.json',R/'project-effective-budget-v385.json',R/'research-deadline-current.json',Path(cfg['archive_path']),Path(cfg['worker_path']),Path(q['sandbox_path'])]+list((G/'core').rglob('*.py'))
 for b in binding['exact_bindings']:
  F=Path(b['baseline_result_path']).parent;assert sha(F/'result.json')==b['baseline_result_sha256'];files += [F/n for n in ['job.json','result.json','trace-private.jsonl','ready-private.json']]
 markers={str(f):sha(f) for f in [R/'stage297/fresh-DEV-private.json',R/'stage297/screen-seal.json',R/'HOLDOUT.opened',R/'protected-query-ledger-v1.json',R/'current-champion.json']}
 p=dict(stage=370,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=cfg,sandbox_path=q['sandbox_path'],order=order,cases={b['public_label']:b['exact_case'] for b in binding['exact_bindings']},initial_observations={b['public_label']:b['initial_observation_sha256'] for b in binding['exact_bindings']},baseline296={b['public_label']:b['baseline_result'] for b in binding['exact_bindings']},baseline_paths={b['public_label']:b['baseline_result_path'] for b in binding['exact_bindings']},observer_rng_seed=370,runtime_versions=contract['comparability']['python_numpy_opencv_versions'],protected_marker_hashes=markers,
 authorization='Explicitparent370executesalreadyused296DEVS2960-S29611withfrozen365. Grant7158beforefirstresetadds16842=>24000max. Actualcostonly,reserve84000unchanged. No297fresh12/HOLDOUT/SEALEDopening,candidatechange,tuning,retry,alternatecandidateorautomaticpromotion.',
 comparison='Historical29610/12only;nofreshcontrol. Exactcase/initialimage/geometry/registeredobstaclehashandmatchingruntimeversions. Old296doesnotrecordperstepstate/RNG/fullpixels,soobserver370fixednewnotclaimedmatchedlatentprefix.',
 contract='Ownpixels,allreturnedfloat32controls,normalmemory. GTonlyreadonlyinitialidentity/evaluatorcaptureandposthocbirthcircle/positive-transferdiagnosis,neveractorinput. Fixedcaseorder,noreplacement/resampling.',
 gates='Aftereachofficialterminal/cap,before nextreset,anyknownsupported direct orbirth-supportedretainedroutingloss or technical/integrityerror stopsbatch. Confirmedcrossfixturelowpositive-transfercounterexamplealsofails369qualification. OrdinaryDNFrecordedandcontinue. Unresolved/missingGTnotnegativegroundtruth;prior62and12/16unknownnotclaimedresolved.',
 stops='Officialfinish/retirement/otherofficialtruncationfirst;else2000protocolcensor/currentdeadline/technicalstop. Total24000. No2038/internalcapextension,retryorsubstitutedcase.',
 judgment=contract['proposed_frozen_evaluation']['judgment'],decision_gate='Evaluate369criteriononlyafterall12definitiveuncensoredofficialresultsandallknownsupportgatespass.11-12completion=countimprovement;10requirestrictnegativecommonmeannew-oldlap;0-9inferior. No automaticchampionchange.',budget=dict(research_before=16842,additional_research=7158,research_after_grant=24000,total_native_cap=24000,per_case_cap=2000,max_resets=12,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
 save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget-extension.json',dict(stage=370,additional_research_actions=7158,research_before=16842,research_after_grant=24000,final_reserve_change=0,authorization=p['authorization']))
 v.update(version=386,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v385.json'),prior_budget_sha256=sha(R/'project-effective-budget-v385.json'),B_increment=7158,B_operating_cap=1404563,research_remaining=24000,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'));assert not (R/'project-effective-budget-v386.json').exists();save(R/'project-effective-budget-v386.json',v)
 save(D/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=24000,reset_cap=12));print('370 registered usedDEV12, grant7158 beforecalls, cap24000/percase2000; protectedsets/reserveunchanged.',flush=True)
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
