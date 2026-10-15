"""Register one frozen357N2actualrun under existing1361native, history350only."""
import datetime
from pathlib import Path
import sys
import time
from retry.path271_run import read,save,sha

G=Path(__file__).resolve().parent.parent


def verify(R,full=False):
    D=R/'stage359';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    D=R/'stage359';assert not D.exists();D.mkdir(mode=0o700);q=read(R/'stage357/plan.json');hist=read(R/'stage350/plan.json');cfg=q['configs']['variant'];base=hist['config'];assert read(R/'stage357/final-report-verification.json')['passed'] and read(R/'stage358/final-report-verification.json')['passed']
    assert sha(cfg['archive_path'])==cfg['archive_sha256']=='b03a65de6410b2fa4805eefcd7a5a05ec246fc27843bdc40facc938927e665ad' and sha(cfg['worker_path'])==cfg['worker_sha256'];assert base['archive_sha256']=='ef1965a5b09ec9324498643842badbcd972c48fb7c141770d7cce88fe6496208'
    assert set(cfg['members_sha256'])==set(base['members_sha256']) and {n for n,h in cfg['members_sha256'].items() if h!=base['members_sha256'][n]}=={'retry/nominal238_base.py'} and cfg['assets']==base['assets'] and cfg['constants']==base['constants']
    for f,h in hist['source_hashes'].items():assert sha(f)==h,f
    p330=read(R/'stage330/plan.json');assert hist['case']==p330['cases']['N2'];v=read(R/'project-effective-budget-v372.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1286150,1361,84000,0)
    files=[G/'retry/episode359_stage.py',G/'retry/episode359_run.py',G/'retry/frozen_composite_runtime.py',G/'retry/source_vehicle_transition.py',G/'retry/episode337_run.py',G/'retry/pedal331_run.py',G/'retry/probe338_stage.py',G/'retry/package349_run.py',G/'retry/diagnose.py',G/'retry/full_route_reproduction.py',G/'env_wrapper.py',G/'damage.py',R/'stage357/plan.json',R/'stage357/summary-private.json',R/'stage357/final-report-verification.json',R/'stage358/summary-private.json',R/'stage350/plan.json',R/'stage350/summary-private.json',R/'stage350/final-report-verification.json',R/'stage330/plan.json',R/'project-effective-budget-v372.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',Path(cfg['archive_path']),Path(base['archive_path']),Path(cfg['worker_path']),Path(base['worker_path']),Path(q['sandbox_path'])]+[R/'stage350/B'/n for n in ['result.json','trace-private.jsonl','frames-actions-private.npz','initial-scene-private.json','initial-RNG-private.json','reset-policy-private.json','ready-private.json']]+[R/'stage337/B'/n for n in ['result.json','trace-private.jsonl','frames-actions-private.npz']]+list((G/'core').rglob('*.py'))
    p=dict(stage=359,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=cfg,case=hist['case'],expected_initial_observation_sha256=p330['initial_observations']['N2'],observer_rng_seed=hist['observer_rng_seed'],sandbox_path=q['sandbox_path'],episode_cap=1361,total_native_cap=1361,actor_act_cap=1361,reset_cap=1,
        authorization='Explicitparent359: onefreshfrozen357N2episode withinexisting1361native, no grant. Officialterminalor1361researchbudget/deadline first. No newcontrol/cache/auxiliarynative/retry/extraarm/tuning/protectedsplit/promotion. Reserve84000preserved.',
        identity='Match350N2case/init/evaluatorRNGseed, not precedingO2seed. Frozen357onlyage0routingguard differsfrom350349policymembers; models/controller/fallback/constantsunchanged. Sameenvironment/runtimeversions.357passiveobserver differsfrom349measurementassertiononly, samequalification as357/358.',
        history_gate='350B349292actions/lap23320isreusedhistoricalcomparison, notnewcontrol. Verifyfreshresetpixels/fullphysics/accessRNG/originalpolicyprojection. Compare eachnaturallycommonprestate/ownoutputs/tracker/support/physical/RNG/rawticks; distinguishfirstmembershipdifferencefromfirstpath/target/fullcontroldifference. Mixedhistoricalfullphysicsfirst72andcompactthereafter preserved. Aftersemanticbranch ownobservations/fullcontrols/normalmemory, no forcedhistory.',
        retained_question='Record121:0retainedexclusionat127-129anditsage. Preserveold350routingeffect versusno-filter337historicalcontext, withoutnewbaseline. Post127coupledtrajectorydifferences notindependentsteering/pedalcausality. Fullnewactualcompletionneeded beyond357cached233.',
        cache_context='357N2_337andN2_340storedinputs camefromactual334nofilter337andknown121routingintervention340. Theircachedoutputs are not anewphysicalepisode.350actual349completion remainsseparatehistory.',
        stops='Officialfinish/retirement/otherofficialtruncation first, otherwise1361budgetprotocolcensor/deadline. Source/reset/interface/leak/technicalmismatch stops, no automatic2000/2038extension. Budgetcensor isnotcompletion oractualDNF.',
        metrics='Officialretroactivecenterlap minuspostresetstart; progress/contact/damage/retirementjointly. GTreadonlyevaluatorcaptureandposthocbirthsupportlabels only, neveractorinput/actionselection. Knownfixture-supported directandbirth-supportedretained lossesseparate.',
        inference='SingleknownN2regressioncheckversusqualifiedhistory, notfreshpairedcontrol/generalization/promotion. Originalstateprojection excludesfullpickle; hidden solver/OpenCV RNG/warmstart/islandstate notdirectlycaptured.',budget=dict(research_before=1361,episode_cap=1361,new_environment_resets=1,new_cached_actor_calls=0,additional_research=0,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp();save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'reservation.json',p['budget']);save(D/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=1361,episode_cap=1361,actor_act_cap=1361,reset_cap=1));print('359registered onefrozen357N2run max1361/reset1;350historyonly, same350init/RNG; reserve84000unchanged.',flush=True)


if __name__=='__main__':build(Path(sys.argv[1]).resolve())
