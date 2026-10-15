"""First dtype-real routing change in fixed124-132 window; one command at128."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

PROBE='''    if op=='direct_probe':
        assert pending
        obs=payload.reshape(4,84,84).copy();before_state=state()
        import retry.connected_agent as routing
        from retry.clearance_agent import road_and_obstacles
        from retry.cem294_constants import LOOKAHEAD_SCALE
        prior_evaluation=copy.deepcopy(routing.LAST_CONNECTION_EVALUATION)
        features=observed_features['features'];direct=road_and_obstacles(obs[-1])[1]
        variants={}
        for mode,hazards in [('original',agent.hazards),('direct',direct)]:
            path=[list(map(float,p)) for p in routing.connected_route(obs[-1],[p[:3] for p in hazards],speed=features[3],previous_steer=features[7])]
            target=nominal_module.route_target(path,features[3],LOOKAHEAD_SCALE)
            assert target is not None
            controller=copy.deepcopy(agent.controller)
            controller.previous_steer=float(features[7])
            calculated=np.asarray(controller.action_target(float(target[0]),float(target[1]),float(features[3]),pedal_speed=float(features[4])),np.float32)
            variants[mode]=dict(path=path,target=list(map(float,target)),steering=float(calculated[0]),dtype=str(calculated.dtype))
        assert variants['original']['path']==observed_route['path'] and np.float32(variants['original']['steering'])==last_base[0]
        routing.LAST_CONNECTION_EVALUATION=prior_evaluation
        assert state()==before_state
        response=dict(variants=variants,direct=direct,state_preserved=True,state=state(),tracker_unchanged=True,actual_frozen_controller=True)
    elif op=='commit':
'''


def verify(R,full=False):
    D=R/'stage338';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    return p


def stack(frames,index):return frames[np.maximum(np.arange(index-3,index+1),0)].astype(np.float32)/255


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage338';assert not D.exists();D.mkdir(mode=0o700)
    prior=read(R/'stage337/plan.json');assert sha(R/'stage337/plan.json')==(R/'stage337/plan.sha256').read_text().strip()
    for f,h in prior['source_hashes'].items():assert sha(f)==h,f
    result=read(R/'stage337/B/result.json');assert result['comparison_valid'] and result['native_actions']==233 and result['actual_DNF'] and result['retire_reason']=='off_track';assert read(R/'stage337/saved-evidence-verification.json')['passed']
    base=prior['config'];original=Path(base['worker_path']);assert sha(original)==base['worker_sha256'];source=original.read_text();assert source.count("    if op=='commit':\n")==1;source=source.replace("    if op=='commit':\n",PROBE);worker=D/'observer-worker-private.py';worker.write_text(source);worker.chmod(0o600);cfg=dict(base,worker_path=str(worker),worker_sha256=sha(worker))
    inputs=[R/'stage337/plan.json',R/'stage337/B/result.json',R/'stage337/B/trace-private.jsonl',R/'stage337/B/frames-actions-private.npz',R/'stage337/B/initial-scene-private.json',R/'stage337/saved-evidence-verification.json',R/'stage337/failure-diagnosis-private.json',R/'stage335/B/first-divergence-private.json',R/'stage334/summary-private.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',R/'project-effective-budget-v348.json',R/'research-deadline-current.json',original,worker,Path(cfg['archive_path']),G/'retry/probe338_stage.py',G/'retry/probe338_run.py',G/'retry/episode337_run.py',G/'retry/diagnose.py',G/'retry/frozen_composite_runtime.py',G/'retry/pedal331_run.py',G/'retry/source_vehicle_transition.py',G/'retry/full_route_reproduction.py',G/'env_wrapper.py',G/'damage.py']+list((G/'core').rglob('*.py'))
    p=dict(stage=338,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],case=prior['case'],observer_rng_seed=prior['observer_rng_seed'],config=cfg,base_config=base,sandbox_path=prior['sandbox_path'],
        hypothesis='Single earliest dtype-real steering difference at128 in fixed124-132diagnostic window usingcurrentdirectdetections canresolve newobstacle2blockage.',
        design='Existingactual337A reused, no newA. Bactualprefix1-127 exact. At128samefrozenrouting/route_target/controller class, samepixels/speed/previousnominalsteer, directdetections onlyin pureprobe. Execute probe steer, preserve actualoriginal128gas/brake andnominalmemory. No tracker deletion.129+alloriginalcandidate outputs on own observations, no savedcontinuation.',
        gate='Original128routing/controller float32steer reproduced first; cached124-127directequalsoriginal and128actualfloat32differs. Do not picklarger129difference. Sameinitialconditions/physics/accessRNG/actor/tracker/memory/pixels beforeprobe. Probe statehash equal, module routing evaluation restored.',
        cap=233,research_available=1805,additional_research=0,final_reserved_actions=84000,
        interpretation='Local sufficiency only: lessblockage/progress supports thisparticularsteer intervention; samefailure refutes onlythissufficiency.233survival isprotocolcensor notcompletion. Do notinfer allretainedpoints harmless orspeed/lookahead cause; .549rad near/far difference canbenormalcurvedpath.',
        stop='Officialterminal,qualificationmismatch,233cap orauthorizationdeadline. No fit,threshold,sweep,lookahead/pedalchange/newroad/protectedsplit/promotion. Technicalrecoverywithinbudgetrecordsallcost; exactshortfall reported ifmore needed.',
        methodology='Parentfulloriginal/appliedplanreread11:46:07-11:46:44UTC; onehypothesispaired/info/objective/implementation/causeisolation principles; originaltexts notcopied.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);print('338registeredfixed128probe; frozencontrollerclone; no newA/budgetincrease',flush=True)


def cache(R):
    from retry.frozen_composite_runtime import prepare
    from retry.episode337_run import json_default
    D=R/'stage338';p=verify(R,True);assert not (D/'cache-opening.json').exists();save(D/'cache-opening.json',dict(epoch=time.time()));z=np.load(R/'stage337/B/frames-actions-private.npz');old=[json.loads(s) for s in (R/'stage337/B/trace-private.jsonl').read_text().splitlines()];w=prepare(p['config'],D/'cache/cpu',p['sandbox_path']);start,cpu=time.perf_counter(),time.process_time();records=[];probes=[];receipt={}
    try:
        reset,_=w.call('reset',stack(z['frames_uint8'],0));save(D/'cache/reset-private.json',reset)
        for i in range(128):
            obs=stack(z['frames_uint8'],i);r,_=w.call('act',obs);assert r['action']==old[i]['returned_action'] and r['features']==old[i]['features'] and r['tracker_record']==old[i]['tracker'] and r['pixel_path']==old[i]['pixel_path'] and r['delta_audit']==old[i]['audit']
            if i>=123:
                probe,_=w.call('direct_probe',obs);assert probe['state_preserved'] and probe['state']==r['state'] and probe['actual_frozen_controller'];assert probe['variants']['original']['steering']==r['action'][0];json.dumps(probe,default=json_default,allow_nan=False);probes.append(dict(step=i+1,probe=probe,dtype_diff=bool(np.float32(probe['variants']['original']['steering'])!=np.float32(probe['variants']['direct']['steering']))))
            c,_=w.call('commit',z['actions'][i]);assert c['state']==old[i]['policy'] and c['memory']==old[i]['nominal_memory'];records.append(dict(response=r,commit=c))
        assert [x['step'] for x in probes if x['dtype_diff']]==[128]
        receipt=dict(passed=True,cached_actor_calls=128,frozen_package_routing_controller_calls=10,first_fixed_window_actual_dtype_difference=128,original_output_all_reproduced=True,float32_difference_real=True,probe_no_state_mutation=True,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=c['actor_cumulative_CPU_s'],new_native_actions=0)
    finally:receipt['reaping']=w.close()
    save(D/'cache/records-private.json',records);save(D/'cache/probes-private.json',probes);save(D/'cache-receipt.json',receipt)
    prior=R/'project-effective-budget-v348.json';v=read(prior);assert v['research_remaining']==1805 and v['actual_cumulative_wrapper_actions']==1282433 and v['final_reserved_actions']==84000 and v['final_reserve_used']==0
    reservation=dict(stage=338,cap=233,from_existing_research=1805,additional_research=0,research_after_maximum=1572,final_reserve_change=0)
    save(D/'reservation.json',reservation);v.update(version=349,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,stage338_reserved_cap=233,reservation_path=str(D/'reservation.json'),reservation_sha256=sha(D/'reservation.json'));assert not (R/'project-effective-budget-v349.json').exists();save(R/'project-effective-budget-v349.json',v);save(D/'native-budget.json',dict(cap=233,actions=0))
    print('338cache128exact; firstfloat32change128; cap233from1805registered',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['build','cache']);p.add_argument('--private-root',required=True,type=Path);a=p.parse_args();globals()[a.command](a.private_root)
