"""Register remaining13 known cases, frozen357, and explicit24963 grant."""
import datetime
from pathlib import Path
import sys
import time
from retry.path271_run import read,save,sha
from retry.lineage354 import baseline_folder,safe
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
    D=R/'stage363';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip();assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p

def verify_case(R,key,full=False):
    p=verify(R,full);assert key in p['order'];return dict(config=p['config'],case=p['cases'][key],expected_initial_observation_sha256=p['initial_observations'][key],observer_rng_seed=p['observer_rng_seed'],sandbox_path=p['sandbox_path'],episode_cap=2000)

def build(R):
    D=R/'stage363';assert not D.exists();D.mkdir(mode=0o700);prior=read(R/'stage362/summary-private.json');old=read(R/'stage330/plan.json');q=read(R/'stage357/plan.json');cfg=q['configs']['variant'];order=prior['remaining13_budget_proposal']['conditions'];expected=['T2953','T2956','T2959','O0','N0','N1','N3','T2951','T2952','T2955','T2957','T2958','T29510'];assert order==expected and len(set(order))==13
    done={x['condition'] for x in prior['actual357_coverage']['actual_measured']};assert done=={'O2','N2','T29511','T2950','T2954'} and set(order)==set(old['roads'])-done
    assert sha(cfg['archive_path'])==cfg['archive_sha256']=='b03a65de6410b2fa4805eefcd7a5a05ec246fc27843bdc40facc938927e665ad' and sha(cfg['worker_path'])==cfg['worker_sha256'] and read(R/'stage362/final-report-verification.json')['passed']
    v=read(R/'project-effective-budget-v377.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1287405,1037,84000,0,1372442)
    files=[G/f'retry/{name}.py' for name in ['evaluation363_stage','evaluation363_episode','evaluation363_run','evaluation363_close','lineage354','frozen_composite_runtime','source_vehicle_transition','episode337_run','pedal331_run','probe338_stage','package349_run','diagnose','full_route_reproduction','confidence341_run']]+[G/'local_runner.py',G/'env_wrapper.py',G/'damage.py',R/'stage362/summary-private.json',R/'stage362/final-report-verification.json',R/'stage357/plan.json',R/'stage354/summary-private.json',R/'stage330/plan.json',R/'stage349/candidate/reset-private.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',R/'project-effective-budget-v377.json',R/'research-deadline-current.json',Path(cfg['archive_path']),Path(cfg['worker_path']),Path(q['sandbox_path'])]+list((G/'core').rglob('*.py'))
    baselines={};baseline_paths={};table={x['condition']:x for x in read(R/'stage354/summary-private.json')['table']}
    for key in old['roads']:
        f=baseline_folder(R,old,key);br=read(f/'result.json');job=read(f/'job.json');assert job['case']==old['cases'][key] and br['initial_observation_sha256']==old['initial_observations'][key] and br['geometry_sha256']==old['cases'][key]['road_geometry_sha256'] and br['archive_sha256']==cfg296(old)==job['config']['archive_sha256'] and safe(br)==table[key]['baseline296'];baselines[key]=safe(br);baseline_paths[key]=str(f);files += [f/'job.json',f/'result.json']
    for stage in [358,359,360,361,362]:files += [R/f'stage{stage}/plan.json',R/f'stage{stage}/B/result.json',R/f'stage{stage}/summary-private.json']
    p=dict(stage=363,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],order=order,all18_order=old['roads'],cases={k:old['cases'][k] for k in order},initial_observations={k:old['initial_observations'][k] for k in order},config=cfg,sandbox_path=q['sandbox_path'],observer_rng_seed=363,baseline296=baselines,baseline_paths=baseline_paths,existing_actual357=dict(O2=358,N2=359,T29511=360,T2950=361,T2954=362),
        authorization='Explicitparent363add24963to1037=>26000max. Exactlyremaining13oneepisodeeach; alreadymeasuredfive notreexecuted. Actualconsumptiononly, reserve84000untouched. No paidresources/candidatechanges/tuning/retry/control/cache/automaticextension/promotion/protectedsplit.',
        gates='Beforeeachreset frozenhash/deadline/inputidentity. Aftereachofficialterminal/cap, posthocbirthcirclelabels: anyknownsupported direct orbirth-supportedretained routingloss stopsallsubsequentcases. Anytechnical/integrity/source/reset/interfaceerror stopsbatch. OrdinaryDNFrecordedandcontinue;damageisdiagnosticonly. MissingGTreportedseparately, neverconvertedtosupported.',
        stops='Percondition firstofficialfinish/retirement/otherofficialtruncation, otherwise2000protocolcensor/deadline. No2038extension. Totalcap26000. Noautomaticrerunorrecoveryexperiments.',
        contract='Ownpixels/fullreturnedfloat32commands/normalmemory; GTonlyreadonlyidentity/evaluatorcaptureandposthoclabels, neveractorcontrol. Freshresetpercase. Existingknownconditions, notnewDEV/HOLDOUT/SEALEDopening. Sequentialevaluationrequiredbyintercasegate.',
        inference='RepeatedknownTRAIN/knowncaseevaluationafteradaptiveresearch, notindependentgeneralization/unbiasedestimate. 296historicaldifferentpolicy, nofreshpairedcontrol orisolatedrulecausality. Officialcompletionprimary;common-completionlapdeltasseparatefromDNF, damageonlydiagnostic.',budget=dict(research_before=1037,additional_research=24963,research_after_grant=26000,total_native_cap=26000,episode_cap=2000,max_resets=13,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp();save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    save(D/'budget-extension.json',dict(stage=363,additional_research_actions=24963,existing_research=1037,research_after_grant=26000,final_reserve_change=0,authorization=p['authorization']))
    v.update(version=378,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v377.json'),prior_budget_sha256=sha(R/'project-effective-budget-v377.json'),B_increment=24963,B_operating_cap=1397405,research_remaining=26000,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'));assert not (R/'project-effective-budget-v378.json').exists();save(R/'project-effective-budget-v378.json',v)
    save(D/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=26000,reset_cap=13))
    print('363 registered13cases, grant24963 before native; cap26000/percase2000; intercase support/technical gate; reserve84000unchanged.',flush=True)

def cfg296(old):return old['baseline296']['config']['archive_sha256']
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
