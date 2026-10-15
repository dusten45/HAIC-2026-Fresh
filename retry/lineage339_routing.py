"""Strict routing-input-only clone diagnostic; tracker-derived features stay fixed."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.probe338_stage import stack
from retry.lineage339_stage import verify
from retry.frozen_composite_runtime import prepare


def build(R):
    D=R/'stage339';p=verify(R,True);assert read(D/'selection-repair-receipt.json')['passed'];assert not (D/'routing-only-plan.json').exists()
    source=Path(p['config']['worker_path']).read_text()
    replacements={
        'saved_evaluation=copy.deepcopy(routing.LAST_CONNECTION_EVALUATION)':'saved_evaluation=copy.deepcopy(routing.LAST_CONNECTION_EVALUATION)\n        saved_route_binding=nominal_module.connected_route',
        'clone.hazards=copy.deepcopy(selected)':'clone.hazards=copy.deepcopy(hazards)',
        'clone.tracked_obstacles=lambda image,speed:[p[:3] for p in selected]':'''clone.tracked_obstacles=lambda image,speed:[p[:3] for p in hazards]
                def routing_only(image,obstacles_override=None,speed=0.,previous_steer=0.):
                    path=original_route(image,[p[:3] for p in selected],speed=speed,previous_steer=previous_steer)
                    observed_route['path']=[list(map(float,p)) for p in path]
                    return path
                nominal_module.connected_route=routing_only''',
        'routing.route_candidates=original_candidates':'routing.route_candidates=original_candidates\n            nominal_module.connected_route=saved_route_binding',
        "f=list(clone.selector_features)":"f=list(clone.selector_features)\n                assert [f[j] for j in [3,4,7,8,11,12]]==[saved_features['features'][j] for j in [3,4,7,8,11,12]]"
    }
    for before,after in replacements.items():assert source.count(before)==1;source=source.replace(before,after)
    worker=D/'routing-only-worker-private.py';worker.write_text(source);worker.chmod(0o600)
    save(D/'routing-only-plan.json',dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        purpose='Requested strict routing-input boundary. Earlier full-hazard clone comparator also changed tracker count/nearest features and is reported separately, not mislabeled routing-only.',
        boundary='Original frozen tracked hazards feed unchanged near scheduling and count/nearest features. Only connected_route receives selected hazards; frozen target/controller/pedal head/selector recompute from changed path. No live actor state update.',
        gates='All original full outputs exact, clone original exact, only one UID removed in each drop variant, original real-current component retained. Fixed speed/feedback/prior memory/near/hazard count/min-distance features exact.',
        config=dict(p['config'],worker_path=str(worker),worker_sha256=sha(worker)),script_sha256=sha(Path(__file__)),
        saved_pixel_steps=[124,132],cases=[337,338],planned_cached_actor_calls=264,planned_clone_act_calls=72,new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0))


def run(R):
    D=R/'stage339';p=verify(R,True);rp=read(D/'routing-only-plan.json');assert sha(Path(__file__))==rp['script_sha256'];assert not (D/'routing-only-opening.json').exists()
    save(D/'routing-only-opening.json',dict(epoch=time.time()));start,cpu=time.perf_counter(),time.process_time();receipts=[]
    for stage in rp['cases']:
        F=D/f'routing-only/{stage}';F.mkdir(parents=True,mode=0o700);z=np.load(R/f'stage{stage}/B/frames-actions-private.npz');old=[json.loads(s) for s in (R/f'stage{stage}/B/trace-private.jsonl').read_text().splitlines()];w=prepare(rp['config'],F/'cpu',p['sandbox_path']);records=[]
        try:
            w.call('reset',stack(z['frames_uint8'],0))
            for i in range(132):
                verify(R);obs=stack(z['frames_uint8'],i);r,_=w.call('act',obs);o=old[i]
                assert r['action']==o['returned_action'] and r['features']==o['features'] and r['delta_audit']==o['audit'] and r['tracker_record']==o['tracker'] and r['pixel_path']==o['pixel_path']
                if i>=123:
                    probe,_=w.call('lineage_probe',obs);assert probe['state_preserved'] and probe['state']==r['state'];variants=probe['variants'];base=variants['original']
                    for mode in ['drop_birth121','drop_birth124']:
                        birth=int(mode.split('birth')[1]);v=variants[mode];selected=v['hazards'];present=any(i+1-int(h[3])==birth for h in base['hazards'])
                        assert len(base['hazards'])-len(selected)==int(present)
                        if i==123:assert o['tracker']['direct'][1]+[0] in selected
                        assert [v['features'][j] for j in [3,4,7,8,11,12]]==[base['features'][j] for j in [3,4,7,8,11,12]]
                    records.append(dict(stage=stage,step=i+1,probe=probe))
                c,_=w.call('commit',z['actions'][i]);assert c['state']==o['policy'] and c['memory']==o['nominal_memory']
            save(F/'probes-private.json',records);receipts.append(dict(stage=stage,cached_actor_calls=132,clone_act_calls=36,actor_CPU_s=c['actor_cumulative_CPU_s']))
        finally:assert w.close()['process_reaped']
    verify(R,True)
    receipt=dict(passed=True,strict_routing_input_only=True,stages=receipts,cached_actor_calls=264,clone_act_calls=72,pure_routing_calls=72,actor_resets=2,new_environment_resets=0,new_native_actions=0,new_source_physics_ticks=0,new_learning_fits=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=sum(x['actor_CPU_s'] for x in receipts))
    save(D/'routing-only-receipt.json',receipt);print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['build','run']);a.add_argument('--private-root',required=True,type=Path);args=a.parse_args();globals()[args.command](args.private_root)
