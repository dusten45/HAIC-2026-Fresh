"""Register an exposed-source-context fresh O2 pair, no historical A substitution."""
import argparse
import datetime
import time
from pathlib import Path
from retry.path271_run import read,save,sha


def verify(R):
    D=R/'stage345';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    from retry.source344_stage import verify as previous
    previous(R);G=Path(__file__).resolve().parent.parent;D=R/'stage345';assert not D.exists();D.mkdir(mode=0o700);prior=read(R/'stage344/plan.json');assert read(R/'stage344/final-report-verification.json')['passed'];assert read(R/'stage344/baseline-qualified.json')['passed']
    old_worker=Path(prior['configs']['baseline']['worker_path']);assert prior['configs']['baseline']['worker_sha256']==prior['configs']['candidate']['worker_sha256']==sha(old_worker);source=old_worker.read_text();assert source.count('import copy\n')==1;source=source.replace('import copy\n','import copy\nimport pickle\n')
    marker='return dict(previous_steer=float(agent.controller.previous_steer),lateral_acceleration=float(agent.controller.lateral_acceleration),';assert source.count(marker)==1
    source=source.replace(marker,marker+"\n        agent_pickle_sha256=hashlib.sha256(pickle.dumps(agent,protocol=5)).hexdigest(),controller_attributes=dict(agent.controller.__dict__),hazards=[list(map(float,p)) for p in agent.hazards],")
    marker="    response['routing_evidence']=routing_evidence";assert source.count(marker)==1;source=source.replace(marker,marker+"\n    response['final_action_audit']=copy.deepcopy(getattr(agent,'last_audit',None))")
    worker=D/'observer-worker-private.py';worker.write_text(source);worker.chmod(0o600);configs={arm:dict(prior['configs'][mode],worker_path=str(worker),worker_sha256=sha(worker)) for arm,mode in [('A','baseline'),('B','candidate')]}
    v=read(R/'project-effective-budget-v356.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1283122,1116,84000,0)
    inputs=[old_worker,worker,Path(prior['original_config']['archive_path']),R/'stage344/plan.json',R/'stage344/baseline-qualified.json',R/'stage344/final-report-verification.json',R/'stage344/summary-private.json',R/'stage306/collection/O2/job.json',R/'project-effective-budget-v356.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json']
    inputs += [G/'retry'/f for f in ['pair345_stage.py','pair345_run.py','source344_logic.py','support342_logic.py','frozen_composite_runtime.py','episode337_run.py','pedal331_run.py','source_vehicle_transition.py','diagnose.py','full_route_reproduction.py']]+[G/'env_wrapper.py',G/'damage.py']+list((G/'core').rglob('*.py'))
    p=dict(stage=345,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=read(R/'stage306/collection/O2/job.json')['case'],observer_rng_seed=345,configs=configs,sandbox_path=prior['sandbox_path'],order=['A','B'],per_arm_cap=160,total_cap=320,reset_cap=2,
        hypothesis='Exactly the fixed342birth-road-neighbor routing rule can be locally falsified for harmful actual near-car effects under the original296policy that reached the344exposure.',
        contract='Two fresh independent actualO2arms, exact296A vs exact344single-ruleB. No historical A substitution, no current334ON/H1. Never force146. Match reset/road/commands/pixels/fullfreshactorstate/tracker/capturedphysics/accessRNG before the first naturally different fullcontrol. Then each own observations/fullreturnedcontrols/normal memory. Observer extends state hashes only; policy/rule unchanged.',
        unchanged='Original296detector/tracker/fallback/association/dedup/age/expiry, near/count/min-distance definitions, head/models/controller/lookahead. Only frozen zero-road-neighbor source-lineage footprint withholding in B. GT posthoc only, not onlineaction orstop.',
        stop='Officialtermination or160cap each; qualification/integrity/deadline stop distinct from method harm. No natural action exposure means inconclusive, noautomaticextension. Technical recovery only remaining320native/reset2; otherwise exactshortfall.',
        outcomes='First fixture/time/touching duration,uniqueprogress,speed,damage,officialretirement/finish jointly. Newearlycontact/blockage or captured supportedwithholding islocalcounterexample; damagealone notofficialscore.160survival nofinish protocolcensor.',
        measurement='Same read-only raw-step contact observer as343, no extra advancement; initialfull andpre/postcompactphysics/accessRNG, flags, actions, wholefreshactorpickle/controller state. Logwall/CPU/rawtick/reset/capture/journal/artifact overhead.',
        budget=dict(research_remaining=1116,reserved_native=320,research_after_maximum=796,additional_research=0,final_reserved_actions=84000,final_reserve_used=0),methodology='Parent confirms both originals re-reviewed; onechange,pairedsameconditions,censoring.344source-policy cache qualified,343differentpolicy unexposed retained. No champion promotion.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'native-budget.json',dict(actions=0,resets=0,total_cap=320,reset_cap=2,arms=dict(A=0,B=0)));save(D/'reservation.json',p['budget']);print('345registered exact296freshA/B160each, total320reset2; research1116 reserve84000',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);build(a.parse_args().private_root)
