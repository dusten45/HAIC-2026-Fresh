"""Execute every returned ON action on actual observations, one72-cap episode."""
import argparse
import json
import random
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.pedal331_run import plain,obs_sha,digest,rng,physical
from retry.closed335_stage import verify


def run(R):
    from retry.frozen_composite_runtime import prepare
    from retry.diagnose import make_env
    from retry.full_route_reproduction import truth
    D=R/'stage335';p=verify(R);assert read(D/'cache-receipt.json')['passed'];assert not (D/'native-opening.json').exists();save(D/'native-opening.json',dict(epoch=time.time(),runner_sha256=sha(Path(__file__))))
    F=D/'B';F.mkdir(mode=0o700);z=np.load(R/'stage331/A/raw-pixels-actions-private.npz');a=[json.loads(s) for s in (R/'stage331/A/trace-private.jsonl').read_text().splitlines()];sharedtruth=[json.loads(s) for s in (R/'stage333/B/trace-private.jsonl').read_text().splitlines()];ref_rng=read(R/'stage331/A/boundary-private.json')['RNG'];oncache=read(D/'cache/ON-records-private.json');offcache=read(D/'cache/OFF-records-private.json')
    random.seed(p['observer_rng_seed']);np.random.seed(p['observer_rng_seed']);w=env=None;frames=[];actions=[];rows=[];steps=rawticks=reset_ticks=0;actorcpu=0.;error=None;terminal=complete=False;info={};common=True;common_actions=0;first=dict(command=None,input=None,actor_state=None,nominal_memory=None);qualification=[];start,cpu=time.perf_counter(),time.process_time()
    try:
        w=prepare(p['configs']['ON'],F/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});raw=env.unwrapped;reset_ticks=round(raw.t*50)
        assert np.array_equal(obs,z['observations'][0]);assert __import__('hashlib').sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==p['case']['road_geometry_sha256'];policy,_=w.call('reset',obs);assert policy['state']==read(D/'cache/ON-reset-private.json')['state'];frames.append(obs.copy())
        journal=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
        try:
            for i in range(72):
                verify(R);same_input=np.array_equal(obs,z['observations'][i])
                if not same_input and first['input'] is None:first['input']=i+1
                pre=plain(truth(env));snapshot=physical(env)
                if common:
                    assert same_input,'Unexpectedpixelsunderidenticalexecutedprefix'
                    expected=read(D/'cache/ON-reset-private.json')['state'] if i==0 else oncache[i-1]['commit']['state'];assert policy['state']==expected,'ONstatevsqualifiedsameinputcache'
                    if i<=65:assert pre==sharedtruth[i]['pre'],'Measured333sharedprefixbasicstate'
                    if i>=64:assert snapshot==a[i]['pre_physical'],'ActualAcapturedphysicalprefix'
                    assert rng(env)==ref_rng,'AccessibleRNGnotmatchingreferenceconstantpostresetstate'
                    qualification.append(dict(boundary=i,pixels=True,ON_cached_state=True,measured_physical_available=True,accessible_RNG=True))
                r,_=w.call('act',obs);assert not r['python_audit_denied_events'];command=np.asarray(r['action'],np.float32)
                assert command.shape==(3,) and np.isfinite(command).all() and np.all(command>=np.array([-.4,0,0],np.float32)) and np.all(command<=np.array([.4,1,1],np.float32))
                assert r['delta_audit']['action']==command.tolist()
                if common:
                    expected=oncache[i]['response'];assert r['action']==expected['action'] and r['features']==expected['features'] and r['state']==expected['state'] and r['tracker_record']==expected['tracker_record'],'QualifiedONsameinputreproduction'
                if first['actor_state'] is None and r['state']!=offcache[i]['response']['state']:first['actor_state']=i+1
                if first['nominal_memory'] is None and r['state']['previous_steer']!=a[i]['nominal_memory']:first['nominal_memory']=i+1
                differs=not np.array_equal(command,z['actions'][i])
                if differs and first['command'] is None:first['command']=i+1;save(F/'first-divergence-private.json',dict(step=i+1,pre=pre,physical=snapshot,policy_before=policy['state'],accessible_RNG=rng(env),observation_sha256=obs_sha(obs),ON_returned=r))
                c,_=w.call('commit',command);policy=c;actorcpu=c['actor_cumulative_CPU_s'];assert c['memory']==c['nominal_memory']==r['state']['previous_steer'] and c['history'][-1]==command.tolist() and np.float32(c['memory'])==command[0]
                if common and not differs:assert c['state']==oncache[i]['commit']['state']
                common=common and not differs
                if common:common_actions+=1
                b=read(D/'native-budget.json');assert b['actions']<b['cap'];b['actions']+=1;save(D/'native-budget.json',b);steps+=1
                before=raw.t;obs,_,ended,truncated,info=env.step(command);rawticks+=round((raw.t-before)*50);assert abs(raw.t-before-.08)<1e-9 or ended or truncated;terminal=bool(ended or truncated);complete=raw.finish_time_s is not None;frames.append(obs.copy());actions.append(command.copy())
                row=dict(step=i+1,executed=command.tolist(),returned_action=r['action'],features=r['features'],pixel_state=r['pixel_state'],audit=r['delta_audit'],tracker=r['tracker_record'],pixel_path=r['pixel_path'],nominal_memory=c['memory'],policy=c['state'],pre=pre,post=plain(truth(env)),pre_physical=snapshot,post_physical=physical(env),collision=bool(info['collision']),damage=float(env.damage.damage),damage_increase=float(env.damage.damage)-pre['damage'],terminal=terminal,unique_tiles=int(raw.tile_visited_count),total_tiles=len(raw.track),contact_interval_s=[before,float(raw.t)] if info['collision'] else None,same_reference_input=same_input,same_reference_action=not differs)
                if common:
                    assert np.array_equal(obs,z['observations'][i+1]);assert row['collision']==a[i]['collision'] and row['damage']==a[i]['damage'] and terminal==a[i]['terminal']
                journal.write(json.dumps(plain(row),allow_nan=False)+'\n');journal.flush();rows.append(row)
                if terminal:break
        finally:journal.close()
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(F/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
    finally:
        reaping=w.close() if w else None
        if env:env.close()
    if frames:
        dest=F/'raw-pixels-actions-private.npz';np.savez_compressed(dest,observations=np.array(frames,np.float32),actions=np.array(actions,np.float32));dest.chmod(0o600)
    save(F/'common-prefix-qualification-private.json',qualification)
    result=dict(native_actions=steps,comparison_valid=not error,technical_error=error,actual_terminal=terminal,actual_DNF=bool(terminal and not complete),completed=complete,protocol_stop=bool(not error and not terminal and steps==72),first_contact=next((r['step'] for r in rows if r['collision']),None),damage=rows[-1]['damage'] if rows else None,retire_reason=info.get('retire_reason'),actual_common_prefix_commands=common_actions,first_differences=first,returned_commands_all_executed=True,raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actorcpu,wall_s=time.perf_counter()-start,reaping=reaping)
    save(F/'result.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);run(a.parse_args().private_root)
