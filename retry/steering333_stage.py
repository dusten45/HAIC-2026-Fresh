"""Bind existing exactA evidence, one immutable probe, and minimal +1 budget."""
import argparse
import datetime
import json
import time
from pathlib import Path

import numpy as np
from retry.path271_run import read,save,sha

PROBE = '''    if op=='direct_probe':
        assert pending
        obs=payload.reshape(4,84,84).copy();before_state=state()
        import retry.connected_agent as routing
        from retry.clearance_agent import road_and_obstacles
        from retry.route_agent import route_target
        from retry.cem294_constants import LOOKAHEAD_SCALE,STEERING_GAIN
        prior_evaluation=copy.deepcopy(routing.LAST_CONNECTION_EVALUATION)
        features=observed_features['features'];direct=road_and_obstacles(obs[-1])[1]
        path=[list(map(float,p)) for p in routing.connected_route(obs[-1],direct,speed=features[3],previous_steer=features[7])]
        target=route_target(path,features[3],LOOKAHEAD_SCALE)
        assert target is not None
        x,y=map(float,target);curvature=2*x/max(x*x+y*y,1e-6)
        steering=float(np.float32(.8*float(np.clip(np.arctan(3.24*curvature*STEERING_GAIN),-.4,.4))+.2*features[7]))
        routing.LAST_CONNECTION_EVALUATION=prior_evaluation
        assert state()==before_state
        response=dict(steering=steering,direct_obstacles=[list(map(float,p)) for p in direct],path=path,target=[x,y],curvature=curvature,state_preserved=True,state=state())
    elif op=='commit':
'''


def verify(R):
    D=R/'stage333';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    return p


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage333';assert not D.exists();D.mkdir(mode=0o700)
    a=np.load(R/'stage331/A/raw-pixels-actions-private.npz');old=np.load(R/'stage330/evaluation/N2/raw-pixels-actions-private.npz')
    assert np.array_equal(a['observations'],old['observations']) and np.array_equal(a['actions'],old['actions']) and len(a['actions'])==72
    ar=read(R/'stage331/A/result.json');assert ar['reference330_exact'] and ar['reference_steps_matched']==72 and not ar['technical_error'] and ar['actual_terminal'] and ar['retire_reason']=='crash'
    assert read(R/'stage331/independent-verification.json')['passed']
    t1=[json.loads(s) for s in (R/'stage331/A/trace-private.jsonl').read_text().splitlines()];t0=[json.loads(s) for s in (R/'stage330/evaluation/N2/trace-private.jsonl').read_text().splitlines()]
    for x,y in zip(t1,t0):
        assert x['executed']==y['action'] and x['features']==y['features'] and x['audit']==y['audit'] and x['nominal_memory']==y['memory']
        for key in ['collision','damage','terminal']:assert x[key]==y[key]
    p331=read(R/'stage331/plan.json');original=Path(p331['config']['worker_path']);assert sha(original)==p331['config']['worker_sha256']
    source=original.read_text();assert source.count("    if op=='commit':\n")==1;source=source.replace("    if op=='commit':\n",PROBE)
    worker=D/'observer-worker-private.py';worker.write_text(source);worker.chmod(0o600);cfg=dict(p331['config'],worker_path=str(worker),worker_sha256=sha(worker))
    # Initializing observer RNG follows the already executed reference protocol.
    # Its value is stored only in this private plan, never in public results.
    import ast
    seeds=[]
    for node in ast.walk(ast.parse(original.read_text())):
        if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='seed' and len(node.args)==1 and isinstance(node.args[0],ast.Constant):seeds.append(node.args[0].value)
    assert len(set(seeds))==1
    inputs=[R/'stage331/plan.json',R/'stage331/independent-verification.json',R/'stage331/A/result.json',R/'stage331/A/boundary-private.json',R/'stage331/A/trace-private.jsonl',R/'stage331/A/raw-pixels-actions-private.npz',R/'stage330/evaluation/N2/trace-private.jsonl',R/'stage330/evaluation/N2/raw-pixels-actions-private.npz',R/'stage332/routing-counterfactual-private.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',R/'project-effective-budget-v339.json',R/'research-deadline-current.json',original,worker,Path(cfg['archive_path']),G/'env_wrapper.py',G/'damage.py',G/'retry/source_vehicle_transition.py',G/'retry/full_route_reproduction.py',G/'retry/pedal331_run.py',G/'retry/frozen_composite_runtime.py',G/'retry/diagnose.py',Path(p331['sandbox_path'])]+list((G/'core').rglob('*.py'))+[G/'retry'/f for f in ['steering333_stage.py','steering333_run.py']]
    p=dict(stage=333,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=p331['case'],config=cfg,sandbox_path=p331['sandbox_path'],observer_rng_seed=seeds[0],
        method='Explicit parent4.7-4.9/4.13,P2/P3/P8; full original reread reported04:59:40-05:00:11UTC; originals not copied or uploaded.',
        design='One newB. Stored331A commands1-65. Only action66 executed steering replaced by existing routing/controller output using current direct detections. Action66 pedals and all commands67-72 stored331A. Actual-observation original nominal memory updates retained; original calculated steer, probe steer and executed steer separate.',
        A_qualification='Existing331A exact to330: full72commands/73pixelstacks/features/audit/nominalmemory/collision/damage/terminal, independent verification passed. No newA needed.',
        qualification='Stop first input/action/feature/audit/memory/policy/collision/damage mismatch throughout65-prefix. Match captured physical/RNG/policy/observation at64 to331A; at65 match actual snapshot preaction66, whole policy after65, raw observation65. Environment/global RNG must equal reference64 at65; source step has no RNG calls after reset. Opaque OpenCV RNG only seed/callstream matching; hidden solver state not directly measured. No forced state repair/reseed/retry.',
        probe='After original act66, calculate direct-only route from same actual input image/speed/prior nominal steer and existing constants. Pure probe restores module routing evaluation and asserts serialized policy/RNG state unchanged. Compare cached result to332 counterfactual. No GT enters participant.',
        stop='Officialterminal immediately or action72protocolstop or authorizationdeadline. No postterminal actions/observations. No protected split, fit, source rollout, threshold change, sweep or promotion.',
        interpretation='Compare firstcontact/contactfixtures/persistence/damage/crash/pose/speed/uniqueprogress over common actual interval. Increased damage is not automatic veto. Same/worse refutes this one-command sufficiency only. Surviving72 is no completion/general-policy improvement.',
        cap=72,additional_research=1,final_reserved_actions=84000,source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    save(D/'A-reference-qualification.json',dict(passed=True,old330_and331A_actions_pixels_exact=True,full_A_exact_replay=True,commands=72,pixel_stacks=73,new_A_native_actions=0))
    prior=R/'project-effective-budget-v339.json';v=read(prior);assert v['research_remaining']==71 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    extension=dict(stage=333,additional_research_actions=1,reason='Observe already measured crash boundary72 in one newB; existingA exact evidence qualifies. User explicitly authorizes measured minimal+1.',new_native_cap=72,research_before=71,research_after_registration=72,final_reserve_change=0)
    save(D/'budget-extension.json',extension);v.update(version=340,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=1,B_operating_cap=v['B_operating_cap']+1,research_remaining=72,extension_path=str(D/'budget-extension.json'),extension_sha256=sha(D/'budget-extension.json'))
    assert not (R/'project-effective-budget-v340.json').exists();save(R/'project-effective-budget-v340.json',v);save(D/'native-budget.json',dict(cap=72,actions=0));print('333existingAexact; oneBcap72; minimal+1registered; reserve84000untouched',flush=True)


def cache(R):
    from retry.frozen_composite_runtime import prepare
    D=R/'stage333';p=verify(R);assert not (D/'cache-opening.json').exists();save(D/'cache-opening.json',dict(epoch=time.time()));z=np.load(R/'stage331/A/raw-pixels-actions-private.npz');old=[json.loads(s) for s in (R/'stage331/A/trace-private.jsonl').read_text().splitlines()];expected=next(x for x in read(R/'stage332/routing-counterfactual-private.json')['records'] if x['arm']=='A' and x['boundary']==65)['variants']['direct_only']['steering'];w=prepare(p['config'],D/'cache/cpu',p['sandbox_path']);start,cpu=time.perf_counter(),time.process_time();receipt={}
    try:
        w.call('reset',z['observations'][0])
        for i in range(66):
            r,_=w.call('act',z['observations'][i]);assert r['action']==old[i]['calculated330'] and r['features']==old[i]['features'] and r['delta_audit']==old[i]['audit']
            if i==65:
                probe,_=w.call('direct_probe',z['observations'][i]);assert probe['state']==r['state'] and probe['state_preserved'] and probe['steering']==expected
            c,_=w.call('commit',z['actions'][i]);assert c['memory']==old[i]['nominal_memory'] and c['state']==old[i]['policy']
        receipt=dict(passed=True,cached_actor_calls=66,pure_probe_calls=1,policy_state_exact=True,probe_policy_state_preserved=True,probe_equals332=True,native_actions=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=c['actor_cumulative_CPU_s'])
    finally:receipt['reaping']=w.close()
    save(D/'cache-receipt.json',receipt);save(D/'cache-probe-private.json',probe);print('333cachepassed66; probe332exact; noactorstatechange; native0',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','cache']);p.add_argument('--private-root',required=True,type=Path);a=p.parse_args();globals()[a.command](a.private_root)
