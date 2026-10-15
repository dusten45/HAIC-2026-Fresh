"""One actual357O2episode, historical353Bcomparison and research1644cap."""
import datetime
from pathlib import Path
import sys
import time
from retry.path271_run import read,save,sha

G=Path(__file__).resolve().parent.parent


def verify(R,full=False):
    D=R/'stage358';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    D=R/'stage358';assert not D.exists();D.mkdir(mode=0o700);q=read(R/'stage357/plan.json');hist=read(R/'stage353/plan.json');cfg=q['configs']['variant'];base=hist['configs']['B'];assert read(R/'stage357/final-report-verification.json')['passed'] and read(R/'stage357/summary-private.json')['passed_cached_gate']
    assert sha(cfg['archive_path'])==cfg['archive_sha256']=='b03a65de6410b2fa4805eefcd7a5a05ec246fc27843bdc40facc938927e665ad' and sha(cfg['worker_path'])==cfg['worker_sha256'];assert base['archive_sha256']=='ef1965a5b09ec9324498643842badbcd972c48fb7c141770d7cce88fe6496208'
    assert set(cfg['members_sha256'])==set(base['members_sha256']) and {n for n,h in cfg['members_sha256'].items() if h!=base['members_sha256'][n]}=={'retry/nominal238_base.py'}
    assert cfg['assets']==base['assets'] and cfg['constants']==base['constants']
    for f,h in hist['source_hashes'].items():assert sha(f)==h,f
    source=read(R/'stage306/collection/O2/job.json');assert source['case']==hist['case'] and source['config']['archive_sha256']==sha(R/'stage296/submission296.zip')
    v=read(R/'project-effective-budget-v371.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1285867,1644,84000,0)
    files=[G/'retry/episode358_stage.py',G/'retry/episode358_run.py',G/'retry/frozen_composite_runtime.py',G/'retry/source_vehicle_transition.py',G/'retry/episode337_run.py',G/'retry/pedal331_run.py',G/'retry/probe338_stage.py',G/'retry/package349_run.py',G/'retry/diagnose.py',G/'retry/full_route_reproduction.py',G/'env_wrapper.py',G/'damage.py',R/'stage357/plan.json',R/'stage357/summary-private.json',R/'stage357/final-report-verification.json',R/'stage357/passive-worker-private.py',R/'stage353/plan.json',R/'stage353/summary-private.json',R/'stage353/final-report-verification.json',R/'stage306/collection/O2/job.json',R/'project-effective-budget-v371.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',Path(cfg['archive_path']),Path(base['archive_path']),Path(cfg['worker_path']),Path(base['worker_path']),Path(q['sandbox_path'])]+[R/'stage353/B'/name for name in ['result.json','trace-private.jsonl','frames-actions-private.npz','initial-scene-private.json','initial-RNG-private.json','reset-policy-private.json','ready-private.json']]+list((G/'core').rglob('*.py'))
    p=dict(stage=358,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=cfg,case=hist['case'],expected_initial_observation_sha256=source['initial_observation_sha256'],observer_rng_seed=hist['observer_rng_seed'],sandbox_path=q['sandbox_path'],episode_cap=1644,total_native_cap=1644,actor_act_cap=1644,reset_cap=1,
        authorization='Explicitparent358: exactlyonefreshfrozen357O2candidateepisodewithinexisting1644research, no grant. Officialterminalor1644budget/deadline first. No newbaseline, cache, auxiliarynative, extraarm, retry, tuning, othercandidate/split/promotion. Reserve84000untouched.',
        cache_context='357O2cacheframes camefrom296source306collection/O2, notcurrent334/349actualrollout. Replaypolicywas334ON/H1+349or357.146-153cachedactiondifference cannotbeassumedtobe353actualregression. Samecasebutdifferentimagegeneratingpolicy.',
        identity='Frozen357changesonlynominalroutingage0guardrelative353B349; otherpolicymembers/models/fallback/constantsidentical. All353registeredsourcehashesunchanged. Samecase/init/evaluatorRNG/environment/runtimeversions. Workerhashdiffersbecause357passiveactualsubsetrecorderreplaced349low-implies-excludedmeasurementassertion; itdoesnotselect andold349behaviorwasqualifiedby357baselinereplays.',
        history_gate='Historical353B349isareusedcomparison, notanewcontrol. Verifyfreshresetfullphysics/pixels/evaluatorRNG/originalpolicystateprojection andruntimeversions. At eachnaturallycommonprestate compareowninputstack/physics/RNG/policyprojection/supportmetadata. Recordfirstroutingmembershipdifference separatelyfromfirstpath/target/feature/action/audit/memorydifference. Afterfirstsemanticbranch keepownobservations/fullreturnedcontrols/normalmemory, noforcedhistoricalcommands.',
        metrics='Officialcompletionfirst andretroactivecenterlap minuspostresetstart. Reportuniqueprogress/contact/damage/retirereason, knownsupportdirect/birth-supportedretainedlossesposthoc.1644unfinishedisresearchbudgetprotocolcensor, nevercompletion; noautomatic2000or2038extension.',
        inference='Oneknownconditionregressioncheckversushistorical353B. Measurementadapterdifferenceexplicit; no freshpairedcontrolorindependentgeneralization/championclaim. GTread-onlyevaluationandposthoclabels, notpolicyinput oractionselection.',
        budget=dict(research_before=1644,episode_cap=1644,total_native_cap=1644,new_environment_resets=1,new_cached_actor_calls=0,additional_research=0,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp();save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'reservation.json',p['budget']);save(D/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=1644,episode_cap=1644,actor_act_cap=1644,reset_cap=1))
    print('358registered onefrozen357O2run max1644/reset1; historical353Bonly; cacheimages296; reserve84000unchanged.',flush=True)


if __name__=='__main__':build(Path(sys.argv[1]).resolve())
