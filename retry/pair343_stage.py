"""Register two fresh O2 arms, not the historical collection policy."""
import argparse
import datetime
import time
from pathlib import Path
from retry.path271_run import read,save,sha


def verify(R):
    D=R/'stage343';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    from retry.support342_stage import verify as previous
    previous(R);G=Path(__file__).resolve().parent.parent;D=R/'stage343';assert not D.exists();D.mkdir(mode=0o700)
    assert read(R/'stage342/final-report-verification.json')['passed'];prior=read(R/'stage342/plan.json');job=read(R/'stage306/collection/O2/job.json');budget=read(R/'project-effective-budget-v354.json');assert (budget['research_remaining'],budget['final_reserved_actions'],budget['final_reserve_used'])==(1436,84000,0)
    inputs=[R/'stage342/plan.json',R/'stage342/run-result.json',R/'stage342/final-report-verification.json',R/'stage342/summary-private.json',R/'stage306/collection/O2/job.json',R/'stage306/collection/O2/track-private.json',R/'project-effective-budget-v354.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip']
    for cfg in prior['configs'].values():inputs += [Path(cfg['worker_path']),Path(cfg['archive_path'])]
    inputs += [G/'retry'/f for f in ['pair343_stage.py','pair343_run.py','support342_logic.py','frozen_composite_runtime.py','episode337_run.py','pedal331_run.py','source_vehicle_transition.py','diagnose.py','full_route_reproduction.py']]+[G/'env_wrapper.py',G/'damage.py']+list((G/'core').rglob('*.py'))
    p=dict(stage=343,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=job['case'],observer_rng_seed=343,configs=dict(A=prior['configs']['baseline'],B=prior['configs']['candidate']),sandbox_path=prior['sandbox_path'],order=['A','B'],per_arm_cap=160,total_cap=320,reset_cap=2,
        hypothesis='Exactly the cached pixel low-road-support rule does not create earlier harmful contact/blockage on an existing different TRAIN road with a near-car unresolved birth. Cheap local falsification, not completion/general safety.',
        contract='Two fresh actualO2resets, current334ON/H1A and exact342candidateB. No historical actualO2replacement for A. Never force146or old-imageprefix. Before first naturally different full float32command verify independent reset/road/pixels/commands/actor/tracker/captured physics/accessRNG. Each arm own observations, full returned controls and normal own memory thereafter.',
        unchanged='Detector/tracker/source association/dedup/age/expiry, near/count/min-distance definitions, models/controller/lookahead. Only exact342observation-flag routing exclusion, no new thresholds or arms. GT posthoc evaluator only, no onlineGTstopping or actionselection.',
        stop='Each arm official termination or160cap; prefix/integrity/deadline failure stops dependent qualification. No natural control exposure is unexposed, no automatic horizon extension. Finishflag first; survival withoutfinish protocolcensor. Technical errors distinct from method failure; recover only within remaining320native and2resets, otherwise exact shortfall.',
        measurement='Full initial capture, pre/post compact physical states and accessibleRNG, actor state/tracker/flags/actions, raw-tick contact fixture pairs/time/hit flags from read-only observer around each original raw.step. No extra world advancement. Wall/CPU, reset, raw-step/render, capture, observer, serialization/artifact costs recorded.',
        outcomes='Joint fixture contact timing, touching persistence, tile progress,speed,damage,retirement/finish. New early contact/blockage or fixture-supported withheld birth is local counterexample, never damage-only officialscore. Exposure and actual material/occlusion uncertainty separate.',
        budget=dict(research_remaining=1436,reserved_native=320,research_after_maximum=1116,additional_research=0,final_reserved_actions=84000,final_reserve_used=0),methodology='Parent confirms full originals re-reviewed before343; single hypothesis,small falsification,P3/P8. Exact342cache passed, no native promotion by cache alone.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'native-budget.json',dict(actions=0,resets=0,total_cap=320,reset_cap=2,arms=dict(A=0,B=0)));save(D/'reservation.json',p['budget']);print('343registered twofreshO2arms160each/320total/reset2; reserve84000untouched',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);build(a.parse_args().private_root)
