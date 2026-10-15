"""Historical source reproduction precedes one candidate on identical pixels."""
import argparse
import hashlib
import json
import time
import traceback
from pathlib import Path
import numpy as np
from retry.path271_run import read,save
from retry.source344_stage import verify
from retry.source344_logic import advance_evidence
from retry.frozen_composite_runtime import prepare


def rows(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def charge(D,kind):
    b=read(D/'call-budget.json');key='actor_calls' if kind=='act' else 'resets';assert b[key]<b['cap' if kind=='act' else 'reset_cap'];b[key]+=1;save(D/'call-budget.json',b)
def digest(v,dtype):return hashlib.sha256(np.asarray(v,dtype=dtype).tobytes()).hexdigest()


def qualify(R):
    D=R/'stage344';p=verify(R);rec=read(D/'baseline/records-private.json');old=rows(R/'stage306/collection/O2/trace-private.jsonl');off=rows(R/'stage334/O2/OFF-private.jsonl');z=np.load(R/'stage306/collection/O2/observations-actions-private.npz');scale=p['source_constants']['LATERAL_SCALE'];history=[]
    assert len(rec)==160 and read(D/'baseline/receipt.json')['technical_error'] is None
    for i,q in enumerate(rec):
        r=q['response'];c=q['commit'];o=old[i];ref=off[i];image=np.rint(z['observations'][i,-1]*255).astype(np.uint8)
        assert r['action']==o['action']==z['actions'][i].tolist() and r['features']==o['features'] and r['delta_audit']==o['delta_audit']
        assert r['nominal']==o['features'][13:16] and r['pixel_path']==ref['pixel_path']
        assert all(r['tracker_record'][k]==ref['tracker'][k] for k in r['tracker_record'])
        expected=dict(previous_steer=o['memory'],lateral_acceleration=(8. if o['features'][8] else 24.)*scale,hazards_sha256=digest(ref['tracker']['after'],np.float64),previous_image_sha256=hashlib.sha256(image.tobytes()).hexdigest(),history_sha256=digest(history,np.float32))
        assert r['state']==expected,(i,'precommitstate')
        history=(history+[o['action']])[-3:];expected['history_sha256']=digest(history,np.float32)
        assert c['state']==expected and c['memory']==c['nominal_memory']==o['memory'] and c['history']==history
    save(D/'baseline-qualified.json',dict(passed=True,inputs=160,original_archive_and_module_hashes_exact=True,original_actions_features_nominal_memory_exact=True,original_five_field_state_contract_reconstructed=True,qualified334OFFtracker_andpath_exact=True,original_full_pickle_or_RNG_snapshot_unavailable=True,additional_actor_calls=0,new_native_actions=0))
    print('344 baseline160 qualified against exact original outputs, storedmemory and five-field state contract',flush=True)


def run(R,mode):
    D=R/'stage344';p=verify(R);F=D/mode;assert mode in ['baseline','candidate'] and not F.exists();F.mkdir(mode=0o700)
    if mode=='candidate':assert read(D/'baseline-qualified.json')['passed']
    save(F/'opening.json',dict(epoch=time.time()));z=np.load(R/'stage306/collection/O2/observations-actions-private.npz');obs=z['observations'][:160];old=rows(R/'stage306/collection/O2/trace-private.jsonl')[:160];off=rows(R/'stage334/O2/OFF-private.jsonl')[:160]
    assert len(obs)==160 and np.array_equal(obs[1:,:3],obs[:-1,1:]) and np.array_equal(z['actions'][:160],np.asarray([q['action'] for q in old],np.float32))
    pre=[]
    for i in range(160):pre=advance_evidence(off[i]['tracker'],pre,i+1,obs[i,-1])['after']
    save(F/'preflight.json',dict(passed=True,source_tracker_algebra160_exact=True,source_observations_and_commands_aligned=True,actor_calls=0))
    w=None;records=[];error=None;last_cpu=None;start,cpu=time.perf_counter(),time.process_time();j=None
    try:
        w=prepare(p['configs'][mode],F/'cpu',p['sandbox_path']);historical=read(R/'stage306/collection/O2/ready-private.json');assert w.ready['policy_module_sha256']==historical['policy_module_sha256'];save(F/'ready-private.json',w.ready)
        charge(D,'reset');reset,_=w.call('reset',obs[0]);save(F/'reset-private.json',reset)
        j=(F/'journal-private.jsonl').open('x');(F/'journal-private.jsonl').chmod(0o600)
        for i in range(160):
            assert time.time()<__import__('datetime').datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp();charge(D,'act');r,_=w.call('act',obs[i]);last_cpu=r['actor_cumulative_CPU_s'];record=dict(index=i,response=r,commit=None);j.write(json.dumps(record,allow_nan=False)+'\n');j.flush();records.append(record)
            assert not r['python_audit_denied_events'];assert r['routing_evidence']['tracker_preserved'] and r['routing_evidence']['full_hazards']==r['tracker_record']['after']
            assert all(r['tracker_record'][k]==off[i]['tracker'][k] for k in r['tracker_record'])
            assert r['features'][11]==len(r['tracker_record']['after'])
            if mode=='baseline':assert not r['routing_evidence']['removed_indices']
            command=np.asarray(r['action'],np.float32);c,_=w.call('commit',command);last_cpu=c['actor_cumulative_CPU_s'];assert c['memory']==c['nominal_memory']==r['state']['previous_steer'] and np.float32(c['memory'])==command[0] and c['history'][-1]==command.tolist();record['commit']=c;j.write(json.dumps(dict(index=i,commit=c),allow_nan=False)+'\n');j.flush()
        verify(R)
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(F/'error-private.json',dict(error=error,traceback=traceback.format_exc(),budget=read(D/'call-budget.json')))
    finally:
        if j:j.close()
        reaping=w.close() if w else None
    save(F/'records-private.json',records);receipt=dict(mode=mode,returned_actor_calls=len(records),committed_calls=sum(q['commit'] is not None for q in records),technical_error=error,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=last_cpu,reaping=reaping,new_native_actions=0,new_environment_resets=0,new_learning_fits=0)
    save(F/'receipt.json',receipt);print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['baseline','qualify','candidate']);a.add_argument('--private-root',required=True,type=Path);args=a.parse_args();qualify(args.private_root) if args.command=='qualify' else run(args.private_root,args.command)
