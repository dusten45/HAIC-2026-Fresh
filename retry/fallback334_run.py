"""OFF qualification then fixed-pixel sequentialON; no environment import."""
import argparse
import datetime
import gzip
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.fallback334_math import advance,validate


def verify(R):
    D=R/'stage334';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    return p


def load_case(case):
    F=Path(case['folder']);trace=[json.loads(s) for s in (F/'trace-private.jsonl').read_text().splitlines()];z=np.load(case['pixels']);obs=z['observations'][:len(trace)];actions=z['actions'][:len(trace)];n=len(trace)
    assert len(obs)==n and np.array_equal(obs[1:,:3],obs[:-1,1:]);assert [r['step'] for r in trace]==list(range(1,n+1))
    gt={};provenance=[]
    if case['snapshots']:
        with gzip.open(case['snapshots'],'rt') as f:
            for row in map(json.loads,f):
                index=row['step']-1;s=row['snapshot'];assert row['features']==trace[index]['features'];gt[index]=dict(hull=s['hull'],obstacles=s['obstacles'],time=s['actual_time'])
    else:
        static=next(r['pre_physical']['obstacles'] for r in trace if 'pre_physical' in r)
        for i,row in enumerate(trace):
            if case['original_fields']=='333':
                t=row['pre'];gt[i]=dict(hull=dict(position=t['position'],angle=t['angle']),obstacles=static,time=t['time'])
            elif 'pre_physical' in row:
                s=row['pre_physical'];gt[i]=dict(hull=s['hull'],obstacles=s['obstacles'],time=s['actual_time'])
    for i in range(1,n):
        if i in gt and i-1 in gt:assert abs(gt[i]['time']-gt[i-1]['time']-.08)<1e-9
    assert not any(row['terminal'] for row in trace[:-1])
    return obs,actions,trace,gt


def run(R):
    from retry.frozen_composite_runtime import prepare
    D=R/'stage334';p=verify(R);assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));save(D/'algebra-validation.json',validate());configs=read(D/'configs-private.json');overall=time.perf_counter();receipts=[]
    inventory=[]
    for case in p['cases']:
        obs,actions,trace,gt=load_case(case);F=D/case['key'];F.mkdir(mode=0o700);save(F/'GT-private.json',gt)
        inventory.append(dict(key=case['key'],road=case['road'],group=case['group'],input_observations=len(obs),actual_GT_input_boundaries=len(gt),GT_interval_count=sum(i-1 in gt and i in gt for i in range(1,len(obs))),actual_visibility_labels=0,reset_frame_excluded_from_intervals=1,terminal_after_frame_not_replayed=True,source=case['GT']))
        off=[]
        for enabled in [False,True]:
            label='ON' if enabled else 'OFF';w=prepare(configs[case['kind']][label],F/label/'cpu',p['sandbox_path']);records=[];start,cpu=time.perf_counter(),time.process_time();actorcpu=0.
            try:
                w.call('reset',obs[0]);j=(F/(label+'-private.jsonl')).open('x');(F/(label+'-private.jsonl')).chmod(0o600)
                try:
                    for i in range(len(obs)):
                        assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
                        r,_=w.call('act',obs[i]);assert not r['python_audit_denied_events'];t=r['tracker_record'];rebuilt,lineage,transported=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],enabled)
                        assert np.allclose(np.array(rebuilt).reshape(-1,4),np.array(t['after']).reshape(-1,4),rtol=0,atol=1e-12),(case['key'],label,i,'trackerrebuild')
                        if not enabled:
                            expected_action=trace[i]['action'] if case['original_fields']=='collection' else trace[i]['original_calculated'] if case['original_fields']=='333' else trace[i]['calculated330']
                            assert r['action']==expected_action and r['features']==trace[i]['features'],(case['key'],i,'OFF action/features')
                        else:
                            assert t['direct']==off[i]['tracker']['direct']
                            if t['affine'] is not None and off[i]['tracker']['affine'] is not None:assert t['affine']==off[i]['tracker']['affine'],(case['key'],i,'acceptedaffinechanged')
                        c,_=w.call('commit',actions[i]);actorcpu=c['actor_cumulative_CPU_s'];assert c['memory']==r['state']['previous_steer']
                        if not enabled:
                            memory=trace[i]['memory'] if case['original_fields']=='collection' else trace[i]['nominal_memory'];assert c['memory']==memory,(case['key'],i,'OFF memory')
                            if case['original_fields']!='collection':assert c['state']==trace[i]['policy'],(case['key'],i,'OFF policy')
                        record=dict(index=i,features=r['features'],action=r['action'],pixel_path=r['pixel_path'],tracker=t,lineage=lineage,transported=transported,nominal_memory=c['memory'],collision_after=trace[i]['collision'],damage_after=trace[i]['damage'])
                        if not enabled:
                            paired,paired_lineage,paired_transport=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],True)
                            record.update(paired_ON=paired,paired_lineage=paired_lineage,paired_transported=paired_transport)
                            if t['affine'] is not None:assert paired==rebuilt
                        j.write(json.dumps(record,allow_nan=False)+'\n');j.flush();records.append(record)
                finally:j.close()
            finally:reaping=w.close()
            receipt=dict(key=case['key'],mode=label,stored_actor_calls=len(records),runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,wall_s=time.perf_counter()-start,reaping=reaping,new_native_actions=0)
            save(F/(label+'-receipt.json'),receipt);receipts.append(receipt)
            if not enabled:assert len(records)==len(obs);off=records
            print(json.dumps({k:receipt[k] for k in ['key','mode','stored_actor_calls','wall_s']}),flush=True)
    save(D/'inventory-private.json',inventory);save(D/'actor-cost.json',dict(receipts=receipts,stored_actor_calls=sum(r['stored_actor_calls'] for r in receipts),wall_s=time.perf_counter()-overall,new_native_actions=0,new_learning_fits=0,new_source_physics_ticks=0))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);run(p.parse_args().private_root)
