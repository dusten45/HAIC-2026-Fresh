"""Two independent N2 replays: frozen steering, stored versus same-call296 pedals.

Ground truth and source capture are evaluator-only measurements. No source world
is reconstructed or advanced. Policy memory retains the calculated nominal steer.
"""
import argparse
import datetime
import hashlib
import json
import pickle
import random
import time
from pathlib import Path

import numpy as np
from retry.path271_run import read, save, sha


def plain(v):
    if isinstance(v,dict):return {str(k):plain(x) for k,x in v.items()}
    if isinstance(v,(list,tuple)):return [plain(x) for x in v]
    if isinstance(v,np.ndarray):return v.tolist()
    if isinstance(v,np.generic):return v.item()
    return v


def digest(v):return hashlib.sha256(json.dumps(plain(v),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def obs_sha(o):return hashlib.sha256(o.tobytes()).hexdigest()


def verify(R):
    D=R/'stage331';p=read(D/'plan.json')
    assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    return p


def rng(env):
    return dict(environment=plain(env.unwrapped.np_random.bit_generator.state),
        python_sha256=hashlib.sha256(pickle.dumps(random.getstate(),protocol=5)).hexdigest(),
        numpy_sha256=hashlib.sha256(pickle.dumps(np.random.get_state(),protocol=5)).hexdigest())


def physical(env):
    from retry.source_vehicle_transition import capture
    return plain(capture(env))


def arm(R,label):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    from retry.full_route_reproduction import truth
    D=R/'stage331';p=verify(R);F=D/label;assert label in ['A','B'] and not F.exists();F.mkdir(mode=0o700)
    if label=='B':assert read(D/'A/result.json')['reference330_exact']
    reference=R/'stage330/evaluation/N2';z=np.load(reference/'raw-pixels-actions-private.npz');stored=z['actions'];old=[json.loads(s) for s in (reference/'trace-private.jsonl').read_text().splitlines()]
    random.seed(331);np.random.seed(331)
    worker=env=None;frames=[];actions=[];rows=[];steps=rawticks=0;actorcpu=0.;reset=0;error=None;boundary=None;terminal=False;complete=False;info={}
    start,cpu=time.perf_counter(),time.process_time();matched=0
    try:
        worker=prepare(p['config'],F/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});raw=env.unwrapped;reset=round(raw.t*50)
        assert obs_sha(obs)==obs_sha(z['observations'][0]);assert hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256']
        policy,_=worker.call('reset',obs);frames.append(obs.copy())
        journal=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
        try:
            for index in range(72):
                verify(R)
                if index==64:
                    boundary=dict(observation_sha256=obs_sha(obs),physical=physical(env),policy=policy['state'],RNG=rng(env))
                    boundary['physical_sha256']=digest(boundary['physical']);boundary['policy_sha256']=digest(boundary['policy']);boundary['RNG_sha256']=digest(boundary['RNG'])
                    save(F/'boundary-private.json',boundary)
                    if label=='B':assert boundary==read(D/'A/boundary-private.json'),'Independent prebranch boundary mismatch'
                pre=truth(env) if index>=64 else None
                prephysical=physical(env) if index>=64 else None
                r,_=worker.call('act',obs);assert not r['python_audit_denied_events'];calculated=np.array(r['action'],np.float32)
                full296=np.array(r['delta_audit']['base'],np.float32)
                command=stored[index].copy()
                if label=='B' and index>=64:command[1:]=full296[1:]
                reference_expected=label=='A' or index<64
                if reference_expected:
                    assert np.array_equal(obs,z['observations'][index]),('prepixels',index)
                    assert np.array_equal(calculated,stored[index]),('calculated330',index)
                    assert r['features']==old[index]['features'] and r['delta_audit']==old[index]['audit'],('features/audit',index)
                c,_=worker.call('commit',command);policy=c;actorcpu=c['actor_cumulative_CPU_s']
                assert c['memory']==c['nominal_memory']==r['state']['previous_steer']
                assert c['history'][-1]==command.tolist()
                if reference_expected:assert c['memory']==old[index]['memory']
                b=read(D/'native-budget.json');assert b['actions']<b['cap'];b['actions']+=1;save(D/'native-budget.json',b)
                before=raw.t;obs,_,ended,truncated,info=env.step(command);steps+=1;rawticks+=round((raw.t-before)*50);terminal=bool(ended or truncated);complete=raw.finish_time_s is not None
                frames.append(obs.copy());actions.append(command.copy())
                row=dict(step=index+1,executed=command.tolist(),calculated330=calculated.tolist(),calculated296=full296.tolist(),nominal_raw=r['nominal'],
                    calculated_steering=float(full296[0]),executed_steering=float(command[0]),nominal_memory=c['memory'],features=r['features'],pixel_state=r['pixel_state'],audit=r['delta_audit'],
                    collision=bool(info['collision']),damage=float(env.damage.damage),terminal=terminal,policy=c['state'])
                if index>=64:
                    row.update(pre=plain(pre),post=plain(truth(env)),pre_physical=prephysical,post_physical=physical(env),
                        damage_increase=float(env.damage.damage)-pre['damage'],first_contact_interval_s=[before,float(raw.t)] if info['collision'] else None,
                        progress=int(raw.tile_visited_count)/len(raw.track),raw_pre_index=index,raw_post_index=index+1)
                if reference_expected:
                    assert np.array_equal(obs,z['observations'][index+1]),('postpixels',index)
                    assert row['collision']==old[index]['collision'] and row['damage']==old[index]['damage'] and terminal==old[index]['terminal'],('outcome',index)
                    matched+=1
                journal.write(json.dumps(plain(row),allow_nan=False)+'\n');journal.flush();rows.append(row)
                if terminal:break
        finally:journal.close()
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
    finally:
        reaping=worker.close() if worker else None
        if env:env.close()
    if frames:
        dest=F/'raw-pixels-actions-private.npz';np.savez_compressed(dest,observations=np.array(frames,np.float32),actions=np.array(actions,np.float32));dest.chmod(0o600)
    result=dict(arm=label,native_actions=steps,reference330_exact=bool(label=='A' and not error and matched==len(stored)),reference_steps_matched=matched,
        boundary_available=boundary is not None,actual_terminal=terminal,actual_DNF=bool(terminal and not complete),completed=complete,protocol_stop=bool(not error and not terminal and steps==72),
        technical_error=error,damage=rows[-1]['damage'] if rows else None,first_contact=next((r['step'] for r in rows if r['collision']),None),
        retire_reason=info.get('retire_reason'),raw_step_ticks=rawticks,raw_reset_ticks=reset,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,wall_s=time.perf_counter()-start,reaping=reaping)
    save(F/'result.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);a.add_argument('--arm',choices=['A','B'],required=True);args=a.parse_args();arm(args.private_root,args.arm)
