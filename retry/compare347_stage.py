"""Register only a new original baseline; existing candidate is not rerun."""
import argparse
import datetime
import time
from pathlib import Path
from retry.path271_run import read,save,sha


def verify(R):
    D=R/'stage347';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    from retry.complete346_stage import verify as previous
    previous(R);G=Path(__file__).resolve().parent.parent;D=R/'stage347';assert not D.exists();D.mkdir(mode=0o700);a=read(R/'stage345/plan.json');b=read(R/'stage346/plan.json');assert read(R/'stage346/final-report-verification.json')['passed'];assert read(R/'stage346/B/result.json')['completed'];cfg=a['configs']['A'];other=b['configs']['B']
    assert a['case']==b['case'] and a['observer_rng_seed']==b['observer_rng_seed']
    assert {k:v for k,v in cfg.items() if k!='constants'}=={k:v for k,v in other.items() if k!='constants'}
    assert cfg['constants']['confidence342-config.json']==dict(enabled=False) and other['constants']['confidence342-config.json']==dict(enabled=True)
    assert {k:v for k,v in cfg['constants'].items() if k!='confidence342-config.json'}=={k:v for k,v in other['constants'].items() if k!='confidence342-config.json'}
    v=read(R/'project-effective-budget-v358.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1283725,513,84000,0)
    inputs=[R/'stage345/plan.json',R/'stage346/plan.json',R/'stage346/final-report-verification.json',R/'stage346/summary-private.json',R/'project-effective-budget-v358.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json',Path(cfg['archive_path']),Path(cfg['worker_path'])]
    for folder in [R/'stage345/A',R/'stage346/B']:
        inputs += [folder/f for f in ['result.json','trace-private.jsonl','frames-actions-private.npz','initial-scene-private.json','initial-RNG-private.json','reset-policy-private.json']]
    inputs += [G/'retry'/f for f in ['compare347_stage.py','compare347_run.py','complete346_run.py','frozen_composite_runtime.py','episode337_run.py','pedal331_run.py','source_vehicle_transition.py','diagnose.py','full_route_reproduction.py']]+[G/'env_wrapper.py',G/'damage.py']+list((G/'core').rglob('*.py'))
    p=dict(stage=347,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=a['case'],observer_rng_seed=a['observer_rng_seed'],configs=dict(A=cfg),sandbox_path=a['sandbox_path'],order=['A'],per_arm_cap=300,total_cap=300,reset_cap=1,
        question='Matched one-condition official completion/lap comparison of a new original296A against already recorded346B; no candidate rerun or baseline change.',
        identity='Original296archive,worker,models,assets andallotherconfig identical to346Bexcept fixedflag enabledFalsevsTrue. Currentenvironment sources match346frozen hashes; same case,RNGseed,wrapper/horizon initialization. Prepare asserts same Python/numpy/OpenCV singleCPU runtime.',
        gates='Reproduce345Aprefix160outputs/fullstates/pixels/physics/accessRNG. Directly match346Breset/initialstates andcommon145commands146inputs before the naturally different146control. Any environment/RNG/code/prefix mismatch invalidates superioritycomparison and stops qualification. No forced146action or storedpost160controls.',
        contract='Only newA actualrun, max300totalincluding160prefix, reset1. Existing346B283actions stays pre-existing charged data, not a newrun. Afterprefix ownobservations/returnedcontrols/normalmemory. GT posthoconly.',
        stop='Officialfinish/retirement first, otherwise300protocolcensor; finishflag first andretroactive center-crossinglap. No baseline tuning, newarm/split/automaticextension.',
        outcomes='Completion first. If bothfinished, compare officiallap ms. Reporttiles/contact/damage/censoring/retirereason jointly, neverdamage-onlyrank. One knownTRAINcase only, no generalization/occlusion safety/championpromotion.',
        budget=dict(research_remaining=513,reserved_native=300,research_after_maximum=213,additional_research=0,final_reserved_actions=84000,final_reserve_used=0),methodology='Parent confirms full documents re-reviewed,pairedsameconditionsand officialobjective. Conditionalcomparability first; preserve researchuncertainty and finalvalidation readiness.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'native-budget.json',dict(actions=0,resets=0,total_cap=300,reset_cap=1,arms=dict(A=0)));save(D/'reservation.json',p['budget']);print('347registered newAonly300total/reset1;346Breused;research513reserve84000',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);build(a.parse_args().private_root)
