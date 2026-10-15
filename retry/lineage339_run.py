"""First reproduce all existing inputs; then bounded pure cloned policy probes."""
import argparse
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save
from retry.probe338_stage import stack
from retry.lineage339_stage import verify
from retry.frozen_composite_runtime import prepare


def execute(R,diagnostic=False):
    D=R/'stage339';p=verify(R,True);name='diagnostic' if diagnostic else 'reproduction'
    assert not (D/(name+'-opening.json')).exists()
    if diagnostic:assert read(D/'reproduction-receipt.json')['passed']
    save(D/(name+'-opening.json'),dict(epoch=time.time()))
    start,cpu=time.perf_counter(),time.process_time();total=clones=routes=0;receipts=[]
    for stage in [337,338]:
        F=D/name/str(stage);F.mkdir(parents=True,mode=0o700)
        z=np.load(R/f'stage{stage}/B/frames-actions-private.npz');old=[json.loads(s) for s in (R/f'stage{stage}/B/trace-private.jsonl').read_text().splitlines()]
        limit=132 if diagnostic else len(old);w=prepare(p['config'] if diagnostic else p['base_config'],F/'cpu',p['sandbox_path']);records=[]
        t,cc=time.perf_counter(),time.process_time();last=None
        try:
            reset,_=w.call('reset',stack(z['frames_uint8'],0))
            assert reset['state']==read(R/'stage338/cache/reset-private.json')['state']
            for i in range(limit):
                verify(R);obs=stack(z['frames_uint8'],i);r,_=w.call('act',obs);o=old[i]
                assert not r['python_audit_denied_events']
                assert r['action']==o['returned_action'] and r['features']==o['features'] and r['delta_audit']==o['audit']
                assert r['tracker_record']==o['tracker'] and r['pixel_path']==o['pixel_path']
                if diagnostic and i>=123:
                    probe,_=w.call('lineage_probe',obs)
                    assert probe['state_preserved'] and probe['state']==r['state'] and probe['actual_frozen_package']
                    v=probe['variants']['original'];assert v['delta_audit']==o['audit'] and v['features']==o['features'] and v['action']==o['returned_action']
                    records.append(dict(stage=stage,step=i+1,probe=probe));clones+=4;routes+=4
                c,_=w.call('commit',z['actions'][i]);total+=1;last=c
                assert c['state']==o['policy'] and c['memory']==o['nominal_memory']
                assert c['history'][-1]==o['executed']
            receipts.append(dict(stage=stage,passed=True,cached_actor_calls=limit,actor_CPU_s=last['actor_cumulative_CPU_s'],wall_s=time.perf_counter()-t,runner_CPU_s=time.process_time()-cc))
        finally:
            reaped=w.close();assert reaped['process_reaped'] and reaped['actor_pids_absent']
        if diagnostic:save(F/'probes-private.json',records)
    verify(R,True)
    receipt=dict(passed=True,stages=receipts,cached_actor_calls=total,clone_act_calls=clones,pure_routing_calls=routes,actor_resets=2,new_environment_resets=0,new_native_actions=0,new_source_physics_ticks=0,new_learning_fits=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=sum(x['actor_CPU_s'] for x in receipts))
    save(D/(name+'-receipt.json'),receipt);print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['reproduce','diagnose']);a.add_argument('--private-root',required=True,type=Path);args=a.parse_args();execute(args.private_root,args.command=='diagnose')
