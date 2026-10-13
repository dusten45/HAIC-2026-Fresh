"""One preregistered gas-only residual removal, two saved-command prefix controls.

Pixels/16 legal features enter the unchanged controller. Simulator truth is private
observation only. Prefix replay costs are charged; no episode is rerun on failure.
"""
import argparse,json,hashlib,time,datetime
from pathlib import Path
import numpy as np

def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 from retry.full_route_reproduction import truth
 from retry.ppo244_math import apply
 p=json.loads(path.read_text());D=path.parent
 def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
 def save(q,x):
  tmp=q.with_name(q.name+'.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');tmp.chmod(0o600);tmp.replace(q)
 assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 assert not (D/'opening.json').exists(),'One-use experiment; never restart native replay'
 save(D/'opening.json',dict(start_epoch=time.time()));save(D/'budget.json',dict(actions=0,phases={}))
 actor=np.load(p['actor']);stored=np.load(p['residual_buffer']);bd=json.loads(Path(p['baseline_diagnostic']).read_text());baseline=np.asarray([r['after'] for r in bd['audit']],np.float32)
 records=[];error=None;cpu=time.process_time()
 try:
  for arm in ['saved_residual','saved_baseline','gas_restored']:
   folder=D/arm;folder.mkdir(mode=0o700);env=worker=None;rows=[];pixels=[];features=[];actions=[];start=time.perf_counter();raw=0;maxms=0.;matches=0
   try:
    worker=prepare(p['base'],folder/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});initial=hashlib.sha256(obs.tobytes()).hexdigest();assert initial==p['initial_observation_sha256'];reset_ticks=round(env.unwrapped.t*50);worker.call('reset',obs)
    for i in range(p['prefix_steps']):
     assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp()
     response,ms=worker.call('act',obs);maxms=max(maxms,ms);f=np.asarray(response['legal_feature_audit']['features'],float);base=np.asarray(response['action'],np.float32);z=((f-actor['mean'])/actor['std'])@actor['weights']+actor['bias'];computed=apply(base,z)
     if arm=='saved_residual':
      assert np.array_equal(f,stored['features'][i]),'Saved legal feature mismatch'
      assert np.array_equal(base,stored['base'][i]) and np.array_equal(computed,stored['executed'][i]),'Saved command mismatch'
      action=stored['executed'][i].copy();matches+=1
     elif arm=='saved_baseline':
      assert np.array_equal(base,baseline[i]),'Baseline command mismatch'
      action=baseline[i].copy();matches+=1
     else:
      action=computed.copy();action[1]=base[1];assert action[0]==base[0] and action[2]==computed[2]
     pixels.append(obs.copy());features.append(f.copy());actions.append(action.copy());before=truth(env);b=json.loads((D/'budget.json').read_text());assert b['actions']<p['native_cap'];b['actions']+=1;b['phases'][arm]=b['phases'].get(arm,0)+1;save(D/'budget.json',b)
     oldt=env.unwrapped.t;obs,_,ended,truncated,info=env.step(action);raw+=round((env.unwrapped.t-oldt)*50);t=truth(env)
     if arm=='saved_residual':
      sr=p['residual_trajectory'][i];assert t['unique_tiles']==sr['visited'] and abs(t['speed_m_s']-sr['speed_m_s'])<1e-10 and t['damage']==sr['damage'],'Residual physics mismatch'
     if arm=='saved_baseline':
      sr=bd['actual_steps'][i];assert t['unique_tiles']==sr['visited'] and abs(t['speed_m_s']-sr['speed_m_s'])<1e-10 and t['damage']==sr['damage'],'Baseline physics mismatch'
     # Longitudinal hull direction observes physical reversal, never affects action.
     angle=t['angle'];forward=np.asarray([-np.sin(angle),np.cos(angle)]);longitudinal=float(np.dot(t['velocity'],forward));rows.append(dict(action=i+1,features=f.tolist(),base=base.tolist(),executed=action.tolist(),latent=z.tolist(),truth=t,longitudinal_m_s=longitudinal,collision=bool(info.get('collision',False)),terminated=bool(ended or truncated)))
     if ended or truncated:break
   finally:
    if worker:reaping=worker.close()
    if env:env.close()
   arrays=folder/'private-pixels-features-actions.npz';np.savez_compressed(arrays,observations=np.asarray(pixels),features=np.asarray(features),actions=np.asarray(actions));arrays.chmod(0o600);save(folder/'trace-private.json',rows)
   result=dict(arm=arm,native_actions=len(rows),raw_step_ticks=raw,reset_ticks=reset_ticks,replay_matches=matches,wall_s=time.perf_counter()-start,max_base_IPC_ms=maxms,base_actor_CPU_s=response['actor_cumulative_CPU_s'],initial_observation_sha256=initial,reaping=reaping,last=rows[-1],completed=env.unwrapped.finish_time_s is not None,retire_reason=info.get('retire_reason'),censored=not(ended or truncated),prefix_steps=p['prefix_steps'])
   save(folder/'result.json',result);records.append(result);save(D/'records-private.json',records);print(json.dumps({k:result[k] for k in ['arm','native_actions','replay_matches','completed','retire_reason','censored']}),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(records=records,technical_error=error,budget=json.loads((D/'budget.json').read_text()),wall_s=time.time()-json.loads((D/'opening.json').read_text())['start_epoch'],evaluator_CPU_s=time.process_time()-cpu))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
