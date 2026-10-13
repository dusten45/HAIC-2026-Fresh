"""Same official executor with separate screen/extension/DEV cost counters."""
import argparse,datetime,json,time,fcntl
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def charge(D,phase,cap):
 with (D/'budget.lock').open('a') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX);b=read(D/'budget.json');assert b[phase]<cap;b[phase]+=1;b['actions']+=1;save(D/'budget.json',b);fcntl.flock(lock,fcntl.LOCK_UN)

def run(jobpath):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 job=read(jobpath);D=Path(job['private_stage']);F=jobpath.parent;p=read(D/'plan.json');assert not (F/'opening.json').exists();save(F/'opening.json',dict(epoch=time.time()));worker=env=None;start=time.perf_counter();cpu=time.process_time();steps=0;rawticks=0;error=None;result=None;complete=terminal=False;actorcpu=0;reaping=None;timings=[];infos={};reset=0
 try:
  assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
  worker=prepare(job['config'],F/'cpu',p['sandbox_path']);save(F/'ready-private.json',worker.ready);env=make_env();case=job['case'];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;t0=raw.t;reset=round(t0*50);initial=sha_bytes(obs.tobytes());geometry=sha_bytes(np.asarray(raw.track,dtype='<f8').tobytes());assert geometry==case['road_geometry_sha256'];assert not job.get('initial_observation_sha256') or initial==job['initial_observation_sha256'];worker.call('reset',obs)
  j=(F/'trace-private.jsonl').open('x');(F/'trace-private.jsonl').chmod(0o600)
  try:
   for step in range(1,job['native_cap']+1):
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();response,ms=worker.call('act',obs);a=np.array(response['action'],np.float32);assert ms<=5000 and not response['python_audit_denied_events'];f=response['features'];g=response['guard_audit'];expected=np.array(g['before'],np.float32);active=bool(f[8]==1 and f[14]==0 and f[0]==1);assert g['active']==active and g['memory_preserved'];expected[1]=0 if active else expected[1];assert np.array_equal(a,expected);nom=np.array(response['nominal'],np.float32);assert np.array_equal(np.array(f[13:16],np.float32),nom);assert np.float32(response['state']['previous_steer'])==a[0]
    if not f[0]:
     curv=2*f[1]/max(f[2]*f[2]+f[1]*f[1],1e-6);assert np.isclose(curv,f[5],rtol=1e-12,atol=1e-12);goal=min(job['ceiling'],float(np.sqrt(response['state']['lateral_acceleration']/max(abs(curv),1e-6))));assert np.isclose(goal,f[6],rtol=1e-12,atol=1e-12);expected=.8*float(np.clip(np.arctan(3.24*curv*job['steering_gain']),-.4,.4))+.2*f[7];assert np.float32(expected)==a[0]
    committed,cms=worker.call('commit',a);assert np.float32(committed['memory'])==a[0] and committed['history'][-1]==a.tolist();actorcpu=committed['actor_cumulative_CPU_s'];charge(D,job['phase'],p['phase_caps'][job['phase']]);steps=step;before=raw.t;obs,_,ended,truncated,infos=env.step(a);rawticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;terminal=bool(ended or truncated or step==2000);timings.append(ms+cms);j.write(json.dumps(dict(step=step,action=a.tolist(),features=f,guard_audit=g,memory=committed['memory'],damage=float(env.damage.damage),collision=bool(infos['collision']),terminal=terminal),allow_nan=False)+'\n');j.flush()
    if terminal:break
  finally:j.close()
  result=dict(road=job['road'],completed=complete,actual_DNF=terminal and not complete,censored=not terminal,technical_error=None,native_actions=steps,lap_ms=round((raw.finish_time_s-t0)*1000) if complete else None,damage=float(env.damage.damage),visited=raw.tile_visited_count,total_tiles=len(raw.track),retire_reason=None if complete else infos.get('retire_reason') or ('max_steps' if terminal else 'budget_cut'),initial_observation_sha256=initial,geometry_sha256=geometry,raw_step_ticks=rawticks,raw_reset_ticks=reset,actor_CPU_s=actorcpu,runner_CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,policy_IPC_max_ms=max(timings) if timings else None,legal_input_only=True,source_model_physics_ticks=0,memory_feature_checks=steps,archive_sha256=job['config']['archive_sha256']);save(F/'terminal-receipt.json',result)
 except BaseException as e:
  error=type(e).__name__+': '+str(e);save(F/'error-traceback-private.json',dict(traceback=__import__('traceback').format_exc()));result=dict(road=job['road'],completed=False,actual_DNF=False,censored=False,technical_error=error,native_actions=steps,lap_ms=None,raw_step_ticks=rawticks,raw_reset_ticks=reset,actor_CPU_s=actorcpu,runner_CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,observed_terminal=terminal,observed_completed=complete,legal_input_only=True,source_model_physics_ticks=0)
 finally:
  if worker:reaping=worker.close()
  if env:env.close()
 result['reaping']=reaping;save(F/'result.json',result);print(json.dumps({k:result.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','native_actions','lap_ms']}),flush=True)
def sha_bytes(b):return __import__('hashlib').sha256(b).hexdigest()
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--job',type=Path,required=True);run(a.parse_args().job.resolve())
