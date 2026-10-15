"""Register a single candidate episode with 300 total actions including replay."""
import argparse
import datetime
import time
from pathlib import Path
from retry.path271_run import read,save,sha


def verify(R):
    D=R/'stage346';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    from retry.pair345_stage import verify as previous
    previous(R);G=Path(__file__).resolve().parent.parent;D=R/'stage346';assert not D.exists();D.mkdir(mode=0o700);prior=read(R/'stage345/plan.json');assert read(R/'stage345/final-report-verification.json')['passed'];ref=read(R/'stage345/B/result.json');assert ref['native_actions']==160 and ref['protocol_stop'] and not ref['technical_error'];v=read(R/'project-effective-budget-v357.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1283442,796,84000,0)
    cfg=prior['configs']['B'];inputs=[R/'stage345/plan.json',R/'stage345/final-report-verification.json',R/'stage345/summary-private.json',R/'project-effective-budget-v357.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json',Path(cfg['archive_path']),Path(cfg['worker_path'])]
    inputs += [R/'stage345/B'/f for f in ['result.json','trace-private.jsonl','frames-actions-private.npz','initial-scene-private.json','initial-RNG-private.json','reset-policy-private.json']]
    inputs += [G/'retry'/f for f in ['complete346_stage.py','complete346_run.py','pair345_run.py','frozen_composite_runtime.py','episode337_run.py','pedal331_run.py','source_vehicle_transition.py','diagnose.py','full_route_reproduction.py']]+[G/'env_wrapper.py',G/'damage.py']+list((G/'core').rglob('*.py'))
    p=dict(stage=346,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=prior['case'],observer_rng_seed=prior['observer_rng_seed'],configs=dict(B=cfg),sandbox_path=prior['sandbox_path'],order=['B'],per_arm_cap=300,total_cap=300,reset_cap=1,
        question='Absolute official completion feasibility of unchanged296plus342candidate on existingO2; no baseline superiority,safety,generalization orpromotion question.',
        contract='One fresh candidate reset. Reproduce actual345Bprefix160actions/161inputs, fullfreshactor/tracker/normalmemory/capturedphysics/accessRNG and rawtickobservations. Prefix is part of300total, not300additional. Then own observations and all returned controls with normal memory; no storedpost160continuation.',
        gates='Exact345Barchive/worker/rule/models/seed. Prefix/hash/reproduction mismatch is technical failure, not candidateDNF; inspect without newpolicytuning. Stop dependent work and account all usedactions. No extra episode beyond registered300/reset1.',
        stop='Officialfinish orretirement first, otherwise300protocolcensor. Finish flag first; lap from retroactive center crossing minuspostresetstart. No automatic extension, no new split/threshold/arm/fit.',
        measurement='Same read-only rawstep/contactobserver and actualpre/postcapture as345; log contacts/damage diagnostically, officialfinish/lap/tiles/retirereason asresult. Sourcephysicsrollout0, no GT in actor oronline decisions.',
        limits='Single case feasibility only.345providedexposedlocalpair but160censored. Historicalbaseline not reused for a comparative timing/safety claim in346. Existingchampion andprotectedsplits untouched.',
        budget=dict(research_remaining=796,reserved_native=300,research_after_maximum=496,additional_research=0,final_reserved_actions=84000,final_reserve_used=0),methodology='Parent re-reviewed full originals,officialtermination vs partialrun. One hypothesis,exactprefix,finish-awaretermination; no comparative claim from standaloneepisode.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'native-budget.json',dict(actions=0,resets=0,total_cap=300,reset_cap=1,arms=dict(B=0)));save(D/'reservation.json',p['budget']);print('346registered onecandidate300totalincluding160prefix,reset1,research796reserve84000',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);build(a.parse_args().private_root)
