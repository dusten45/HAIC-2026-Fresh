"""One charged pixel-only direct-routing steering probe, fixed stored controls."""
import argparse
import json
import random
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.pedal331_run import plain,obs_sha,digest,rng,physical
from retry.steering333_stage import verify


def run(R):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    from retry.full_route_reproduction import truth
    D=R/'stage333';p=verify(R);assert read(D/'cache-receipt.json')['passed'];assert not (D/'native-opening.json').exists();save(D/'native-opening.json',dict(epoch=time.time(),runner_sha256=sha(Path(__file__))))
    F=D/'B';F.mkdir(mode=0o700);z=np.load(R/'stage331/A/raw-pixels-actions-private.npz');old=[json.loads(s) for s in (R/'stage331/A/trace-private.jsonl').read_text().splitlines()];boundary64=read(R/'stage331/A/boundary-private.json')
    random.seed(p['observer_rng_seed']);np.random.seed(p['observer_rng_seed']);worker=env=None;frames=[];actions=[];rows=[];steps=rawticks=reset=0;actorcpu=0.;error=None;terminal=complete=False;info={};probe=None;matched=0;gate=False
    start,cpu=time.perf_counter(),time.process_time()
    try:
        worker=prepare(p['config'],F/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});raw=env.unwrapped;reset=round(raw.t*50)
        assert np.array_equal(obs,z['observations'][0]);assert __import__('hashlib').sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256'];policy,_=worker.call('reset',obs);frames.append(obs.copy())
        journal=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
        try:
            for index in range(72):
                verify(R)
                if index==64:
                    actual=dict(observation_sha256=obs_sha(obs),physical=physical(env),policy=policy['state'],RNG=rng(env))
                    for k in ['physical','policy','RNG']:actual[k+'_sha256']=digest(actual[k])
                    save(F/'boundary64-private.json',actual);assert actual==boundary64,'Boundary64 mismatch'
                if index==65:
                    actual=dict(observation_sha256=obs_sha(obs),physical=physical(env),policy=policy['state'],RNG=rng(env))
                    save(F/'prebranch65-private.json',actual)
                    assert actual['observation_sha256']==obs_sha(z['observations'][65]);assert actual['physical']==old[65]['pre_physical'];assert actual['policy']==old[64]['policy'];assert actual['RNG']==boundary64['RNG'],'RNG changed since measured64'
                    gate=True;save(D/'prebranch-gate.json',dict(passed=True,observations_prefix=66,commands_prefix=65,physical_exact=True,policy_exact=True,tracked_RNG_exact=True,reference_RNG_at64_unchanged_at65=True,code_config_bindings_exact=True))
                pre=plain(truth(env));snapshot=physical(env) if index>=64 else None
                r,_=worker.call('act',obs);assert not r['python_audit_denied_events'];command=z['actions'][index].copy()
                if index<=65:
                    assert np.array_equal(obs,z['observations'][index]);assert r['action']==old[index]['calculated330'] and r['features']==old[index]['features'] and r['delta_audit']==old[index]['audit']
                if index==65:
                    assert gate;probe,_=worker.call('direct_probe',obs);assert probe['state_preserved'] and probe['state']==r['state'];assert probe['steering']==read(D/'cache-probe-private.json')['steering'];command[0]=np.float32(probe['steering']);assert command[0]!=z['actions'][index,0]
                c,_=worker.call('commit',command);policy=c;actorcpu=c['actor_cumulative_CPU_s'];assert c['memory']==c['nominal_memory']==r['state']['previous_steer']
                if index<65:assert c['state']==old[index]['policy'] and c['memory']==old[index]['nominal_memory']
                budget=read(D/'native-budget.json');assert budget['actions']<budget['cap'];budget['actions']+=1;save(D/'native-budget.json',budget);steps+=1
                before=raw.t;obs,_,ended,truncated,info=env.step(command);rawticks+=round((raw.t-before)*50);terminal=bool(ended or truncated);complete=raw.finish_time_s is not None;frames.append(obs.copy());actions.append(command.copy())
                row=dict(step=index+1,executed=command.tolist(),original_calculated=r['action'],original_nominal_steering=r['delta_audit']['base'][0],probe_steering=probe['steering'] if index==65 else None,executed_steering=float(command[0]),features=r['features'],pixel_state=r['pixel_state'],audit=r['delta_audit'],nominal_memory=c['memory'],policy=c['state'],pre=pre,post=plain(truth(env)),collision=bool(info['collision']),damage=float(env.damage.damage),damage_increase=float(env.damage.damage)-pre['damage'],terminal=terminal,unique_tiles=int(raw.tile_visited_count),total_tiles=len(raw.track),contact_interval_s=[before,float(raw.t)] if info['collision'] else None)
                if index>=64:row.update(pre_physical=snapshot,post_physical=physical(env))
                if index<65:
                    assert np.array_equal(obs,z['observations'][index+1]);assert row['collision']==old[index]['collision'] and row['damage']==old[index]['damage'] and terminal==old[index]['terminal'];matched+=1
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
    if probe:save(F/'probe-private.json',probe)
    result=dict(arm='B',native_actions=steps,prefix_commands_matched=matched,prebranch_gate_passed=gate,comparison_valid=bool(gate and not error),actual_terminal=terminal,actual_DNF=bool(terminal and not complete),completed=complete,protocol_stop=bool(not error and not terminal and steps==72),technical_error=error,first_contact=next((r['step'] for r in rows if r['collision']),None),damage=rows[-1]['damage'] if rows else None,retire_reason=info.get('retire_reason'),raw_step_ticks=rawticks,raw_reset_ticks=reset,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,wall_s=time.perf_counter()-start,reaping=reaping)
    save(F/'result.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);run(a.parse_args().private_root)
