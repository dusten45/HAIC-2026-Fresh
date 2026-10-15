"""Register1468research grant and exactly one unchanged349T2954episode."""
import datetime
from pathlib import Path
import sys
import time
from retry.path271_run import read,save,sha

G=Path(__file__).resolve().parent.parent


def verify(R,full=False):
    D=R/'stage355';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    D=R/'stage355';assert not D.exists();D.mkdir(mode=0o700);b=read(R/'stage354/T2954-ready-binding-private.json');q=read(R/'stage349/plan.json');c=read(R/'stage354/T2954-contract-private.json');assert read(R/'stage354/final-report-verification.json')['passed']
    cfg=b['config'];assert cfg==q['configs']['candidate']==c['config'];assert sha(cfg['archive_path'])==cfg['archive_sha256']=='ef1965a5b09ec9324498643842badbcd972c48fb7c141770d7cce88fe6496208';assert sha(cfg['worker_path'])==cfg['worker_sha256']
    assert b['case']==c['case']==read(R/'stage330/plan.json')['cases']['T2954'];assert b['normal_native_cap']==2000 and b['additional_research_needed']==1468
    for f,h in b['code_source_hashes'].items():assert sha(f)==h,f
    v=read(R/'project-effective-budget-v367.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'],v['B_operating_cap'])==(1285511,532,84000,0,1370043)
    files=[G/'retry/episode355_stage.py',G/'retry/episode355_run.py',G/'retry/frozen_composite_runtime.py',G/'retry/source_vehicle_transition.py',G/'retry/episode337_run.py',G/'retry/pedal331_run.py',G/'retry/probe338_stage.py',G/'retry/package349_run.py',G/'retry/diagnose.py',G/'retry/full_route_reproduction.py',G/'local_runner.py',G/'env_wrapper.py',G/'damage.py',R/'stage354/plan.json',R/'stage354/summary-private.json',R/'stage354/final-report-verification.json',R/'stage354/T2954-ready-binding-private.json',R/'stage354/T2954-contract-private.json',R/'stage349/plan.json',R/'stage349/final-report-verification.json',R/'stage349/candidate/reset-private.json',R/'stage330/plan.json',R/'stage330/evaluation/T2954/result.json',R/'stage295/TRAIN/T2954/g1p4/result.json',R/'stage296/submission296.zip',R/'stage296/champion-manifest.json',R/'project-effective-budget-v367.json',R/'research-deadline-current.json',Path(cfg['archive_path']),Path(cfg['worker_path']),Path(q['sandbox_path'])]+list((G/'core').rglob('*.py'))
    p=dict(stage=355,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=b['case'],config=cfg,expected_initial_observation_sha256=b['expected_initial_observation_sha256'],observer_rng_seed=b['observer_rng_seed'],sandbox_path=q['sandbox_path'],episode_cap=2000,total_native_cap=2000,reset_cap=1,actor_act_cap=2000,
        authorization='Explicitparent355allocates1468additionalresearch to532=>2000foronefreshT2954candidateepisode. Fixed349archive+worker+342rule unchanged. No freshbaseline/cache/auxiliarynative/retry/extraarm/tuning/split/promotion. Finalreserve84000unchanged.',
        question='Officialcompletion feasibility on previouslyunmeasured current349T2954. Distinctuncertainty after knownN2/O0/O2, not another repeat of thoseconditions.',
        gates='354source/artifact/condition contract reused. Freshreset verifiesgeometry/physicalobstacles/initialpixelhash, exactloaded349code/runtime, inputonlyactor, legalfinitecommands and emptymetadata/originalresetstateprojection. Capturefreshstate/tracker/physical/accessRNG/rawcontacts. No qualifiedhistoricalcurrent349T2954prefix exists; do notforce296/330storedcontrols/pixels/memory.',
        contract='Allownofficialpixelobservations, everyreturnedfullcontrol executedunchanged, normalownnominalmemory. GT onlyevaluatoridentityandposthocdiagnostics, neverpolicycontrol/selection. Independentfreshreset and newcostonly.',
        stops='Officialfinish/retirement/otherofficialtruncation first, otherwise2000protocolcap/deadline. Source/reset/interface/leak/technicalerrorstops, no automaticretry/expansion or2038extension.2000withoutfinish isprotocolcensor, notcompletion.',
        metrics='Officialfinishfirst, retroactivecenterlap minuspostresetstart; qualification anddeclaration separate. Uniqueprogress/contact/damage/retirement jointly;357of357tiles isnotofficialfinish. Historical296finish344/lap27440and330DNF612arecontextonly andnotcharged/relabelled.',
        inference='SingleknownTRAINfeasibility.349versus330also changes334fallback, so noisolated342causality ornewpairedlapclaim. No championpromotion/generalization/occlusionclaim.',
        budget=dict(research_before=532,additional_research=1468,research_after_grant=2000,episode_cap=2000,total_native_cap=2000,new_environment_resets=1,new_cached_actor_calls=0,new_native_auxiliary=0,final_reserved_actions=84000,final_reserve_used=0),source_hashes={str(f):sha(f) for f in files})
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    grant=dict(stage=355,additional_research_actions=1468,existing_research=532,research_after_grant=2000,total_native_cap=2000,final_reserve_change=0,authorization=p['authorization']);save(D/'budget-extension.json',grant)
    v.update(version=368,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(R/'project-effective-budget-v367.json'),prior_budget_sha256=sha(R/'project-effective-budget-v367.json'),B_increment=1468,B_operating_cap=1371511,research_remaining=2000,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'));assert not (R/'project-effective-budget-v368.json').exists();save(R/'project-effective-budget-v368.json',v)
    save(D/'native-budget.json',dict(actions=0,resets=0,actor_act_calls=0,actor_resets=0,total_cap=2000,episode_cap=2000,reset_cap=1,actor_act_cap=2000));print('355 grant1468registered before native; research2000; oneT2954episode cap2000/reset1; reserve84000unchanged.',flush=True)


if __name__=='__main__':build(Path(sys.argv[1]).resolve())
