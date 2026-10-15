"""Register one frozen357 T2950 episode within existing1725 research."""
import datetime
from pathlib import Path
import sys
import time
from retry.path271_run import read,save,sha
G=Path(__file__).resolve().parent.parent

def verify(R,full=False):
    D=R/'stage361';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p

def build(R):
    D=R/'stage361';assert not D.exists();D.mkdir(mode=0o700)
    q=read(R/'stage357/plan.json');cfg=q['configs']['variant'];old=read(R/'stage330/plan.json');case=old['cases']['T2950'];job=read(R/'stage295/TRAIN/T2950/g1p4/job.json');br=read(R/'stage295/TRAIN/T2950/g1p4/result.json');cr=read(R/'stage330/evaluation/T2950/result.json')
    assert job['case']==case and br['initial_observation_sha256']==old['initial_observations']['T2950'] and br['geometry_sha256']==case['road_geometry_sha256']
    assert br['archive_sha256']==old['baseline296']['config']['archive_sha256'] and cr['archive_sha256']==read(R/'stage330/artifacts-private.json')['ON']['archive_sha256']
    table=next(x for x in read(R/'stage354/summary-private.json')['table'] if x['condition']=='T2950')
    from retry.lineage354 import safe
    assert table['baseline296']==safe(br) and table['H1_330']==safe(cr) and read(R/'stage354/final-report-verification.json')['passed']
    assert br['actual_DNF'] and br['native_actions']==315 and br['visited']==208 and br['total_tiles']==338 and cr['completed'] and cr['native_actions']==361 and cr['lap_ms']==28860
    assert sha(cfg['archive_path'])==cfg['archive_sha256']=='b03a65de6410b2fa4805eefcd7a5a05ec246fc27843bdc40facc938927e665ad' and sha(cfg['worker_path'])==cfg['worker_sha256'] and read(R/'stage360/final-report-verification.json')['passed']
    v=read(R/'project-effective-budget-v375.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1286717,1725,84000,0,1372442)
    files=[G/'retry/episode361_stage.py',G/'retry/episode361_run.py',G/'retry/lineage354.py',G/'retry/frozen_composite_runtime.py',G/'retry/source_vehicle_transition.py',G/'retry/episode337_run.py',G/'retry/pedal331_run.py',G/'retry/probe338_stage.py',G/'retry/package349_run.py',G/'retry/diagnose.py',G/'retry/full_route_reproduction.py',G/'local_runner.py',G/'env_wrapper.py',G/'damage.py',R/'stage357/plan.json',R/'stage357/final-report-verification.json',R/'stage360/final-report-verification.json',R/'stage354/summary-private.json',R/'stage354/final-report-verification.json',R/'stage330/plan.json',R/'stage330/artifacts-private.json',R/'stage330/evaluation/T2950/result.json',R/'stage295/TRAIN/T2950/g1p4/job.json',R/'stage295/TRAIN/T2950/g1p4/result.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',R/'stage349/candidate/reset-private.json',R/'project-effective-budget-v375.json',R/'research-deadline-current.json',Path(cfg['archive_path']),Path(cfg['worker_path']),Path(q['sandbox_path'])]+list((G/'core').rglob('*.py'))
    p=dict(stage=361,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=cfg,case=case,expected_initial_observation_sha256=old['initial_observations']['T2950'],observer_rng_seed=361,sandbox_path=q['sandbox_path'],episode_cap=1725,total_native_cap=1725,actor_act_cap=1725,reset_cap=1,
        authorization='Explicitparent361: existing1725research cap1725, noadditionalgrant, one frozen357T2950actualepisode. No candidatechange, retry, newcontrol/cache/auxiliarynative, tuning, automaticextension orpromotion. Reserve84000unchanged.',
        historical=dict(baseline296=table['baseline296'],H1_330=table['H1_330'],same_case_verified=True,reused_not_new=True),
        contract='Ownofficialpixels, executeallreturnedfullcontrols withnormalownmemory. GTreadonlyidentity/evaluatorcaptureandposthocdiagnosticsonly; noGTtoactor. Freshreset hashes geometry/physicalobstacles/initialpixels and originalresetprojection. FixednewobserverRNG361;historical330didnotrecordamatchingobserverseed. No forcedhistoricalpolicy/physics/RNGprefix.',
        stops='Officialfinish/retirement/otherofficialtruncation first; else1725protocolcensor orregistereddeadline/technicalfailure. No2038extension. Posthocgate: anyknownsupported director birth-supportedretained withheld failsgate regardlessfinish; nofollowupcandidateexpansion/promotion.',
        inference='SingleknownTRAINcondition;296and330differentpolicies, historicalcomparisononly.357includes334fallbackand342filterplusage0guard, cannotisolatecauses. N2/O2successdoesnotimplythiscaseorgeneralization. No newDEV/HOLDOUT/SEALEDopening.',
        budget=dict(research_before=1725,additional_research=0,episode_cap=1725,new_environment_resets=1,new_cached_actor_calls=0,new_native_auxiliary=0,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    save(D/'reservation.json',p['budget'])
    save(D/'native-budget.json',dict(actions=0,resets=0,actor_act_calls=0,actor_commit_calls=0,actor_resets=0,total_cap=1725,episode_cap=1725,reset_cap=1,actor_act_cap=1725))
    print('361 existing1725 registered before reset/actions; one frozen357T2950 run cap1725; reserve84000unchanged.',flush=True)
if __name__=='__main__':build(Path(sys.argv[1]).resolve())
