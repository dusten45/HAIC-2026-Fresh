"""Fixed legal preview prototype; minimally durable terminal receipt and scalars."""
import argparse,time,datetime,json
from pathlib import Path
import numpy as np
from retry.path271_run import read,sha,save as rawsave
from retry.progress288_control import control
from retry.source_vehicle_transition import capture

def plain(x):
 if isinstance(x,np.generic):return x.item()
 if isinstance(x,np.ndarray):return x.tolist()
 if isinstance(x,dict):return {k:plain(v) for k,v in x.items()}
 if isinstance(x,(list,tuple)):return [plain(v) for v in x]
 return x
def save(path,x):rawsave(path,plain(x))
def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 p=read(path);D=path.parent;assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(Path(q))==h
 assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));results=[];error=None;cpu=time.process_time();gate=False;counters=dict(world_build_attempts=0,clone_initializations=0,physics_ticks=0,clone_build_wall_s=0.,integration_wall_s=0.)
 try:
  for index,road in enumerate(p['pilot']):
   if index==2:
    gate=all(r['completed'] and r['lap_ms']<r['baseline_lap_ms'] for r in results);save(D/'pilot-gate.json',dict(passed=gate))
    if not gate:break
   F=D/road;assert not F.exists();F.mkdir(mode=0o700);worker=env=None;rows=[];ticks=0;start=time.perf_counter();plannerwall=simwall=policywall=0.
   try:
    worker=prepare(p['base'],F/'cpu',p['sandbox_path']);case=p['cases'][road];env=make_env();obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;t0=raw.t;reset=round(t0*50);worker.call('reset',obs);limit=4000 if index<2 else 12000;cap=min(2000,limit-read(D/'budget.json')['actions']);assert cap>0
    journal=(F/'trace-journal-private.jsonl').open('x');(F/'trace-journal-private.jsonl').chmod(0o600)
    try:
     for step in range(1,cap+1):
      assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();response,ms=worker.call('act',obs);policywall+=ms/1000;base=np.array(response['action'],np.float32);tic=time.perf_counter();snapshot=capture(env);before_pose=(tuple(raw.car.hull.position),float(raw.car.hull.angle),float(raw.t));corridor=np.unpackbits(np.frombuffer(__import__('base64').b64decode(response['corridor_bits']),dtype=np.uint8))[:84*84].reshape(84,84).astype(bool);action,audit=control(base,response['features'],response['pixel_path'],snapshot,counters,corridor);assert before_pose==(tuple(raw.car.hull.position),float(raw.car.hull.angle),float(raw.t));save(D/'model-budget.json',counters);plannerwall+=time.perf_counter()-tic;assert np.array_equal(base[1:],action[1:]);committed,cms=worker.call('commit',action);policywall+=cms/1000;assert np.float32(committed['memory'])==action[0] and committed['history'][-1]==action.tolist()
      b=read(D/'budget.json');assert b['actions']<limit;b['actions']+=1;save(D/'budget.json',b);before=raw.t;tic=time.perf_counter();obs,_,ended,truncated,info=env.step(action);simwall+=time.perf_counter()-tic;ticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;official_limit=step==2000 and not complete;terminal=bool(ended or truncated or official_limit)
      row=dict(step=step,base=base.tolist(),action=action.tolist(),features=response['features'],pixel_path=response['pixel_path'],audit=audit,memory=committed['state'],damage=env.damage.damage,collision=bool(info['collision']),terminal=terminal);journal.write(json.dumps(plain(row),allow_nan=False)+'\n');journal.flush();rows.append(row)
      if terminal:break
    finally:journal.close()
    lap=round((raw.finish_time_s-t0)*1000) if complete else None
    minimal=dict(road=road,native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=lap,baseline_lap_ms=p['baseline_lap_ms'][road],lap_delta_ms=lap-p['baseline_lap_ms'][road] if complete else None,retire_reason=None if complete else info.get('retire_reason') or ('max_steps' if official_limit else 'budget_cut'),damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),raw_step_ticks=ticks,raw_reset_ticks=reset)
    save(F/'terminal-receipt.json',minimal)
    audits=[r['audit'] for r in rows];out=dict(minimal,planner_applied_actions=sum(a['applied'] for a in audits),optimizer_accepted_actions=sum(a.get('accepted',False) for a in audits),steering_changed_actions=sum(a.get('steering_changed',False) for a in audits),fallback_actions=sum(not a['applied'] for a in audits),corridor_initial_feasible_actions=sum(a.get('initial_corridor_feasible',False) for a in audits),corridor_final_feasible_actions=sum(a.get('final_corridor_feasible',False) for a in audits),no_feasible_fallback_actions=sum(a.get('no_feasible_candidate',False) for a in audits),tracking_tie_break_actions=sum(a.get('tracking_tie_break_used',False) for a in audits),source_clone_queries=sum(a['source_clone_queries'] for a in audits),source_model_physics_ticks=sum(a['source_model_physics_ticks'] for a in audits),source_zero_time_initializations=sum(a['source_zero_time_initializations'] for a in audits),current_call_pedals_exact_actions=len(rows),memory_verified_actions=len(rows),wall_s=time.perf_counter()-start,planner_wall_s=plannerwall,env_step_wall_s=simwall,policy_IPC_wall_s=policywall,actor_CPU_s=committed['actor_cumulative_CPU_s'],legal_input_only=False,privileged_GT_model_state=True,official_package_qualification=False)
   finally:
    if worker:reaping=worker.close()
    if env:env.close()
   out['reaping']=reaping;save(F/'result.json',out);results.append(out);save(D/'results-private.json',results);print(str(out),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'model-budget.json',counters)
 save(D/'outcome-private.json',dict(results=results,technical_error=error,gate_passed=gate,budget=read(D/'budget.json'),source_counters=counters,wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
