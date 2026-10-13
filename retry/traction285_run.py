"""Run fixed source traction intervention, stop at paired pilot gate failure."""
import argparse,time,datetime,math
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.traction285_control import control

def run(path,resume=False):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 p=read(path);D=path.parent;assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(Path(q))==h
 assert (D/'recovery-plan.json').exists() if resume else not (D/'opening.json').exists()
 if not resume:save(D/'opening.json',dict(epoch=time.time()))
 phase_start=time.time();results=[];error=None;cpu=time.process_time();pilotpassed=False
 try:
  roads=p['pilot']+p['extension_if_pass']
  for index,road in enumerate(roads):
   if resume and road=='O0':continue
   if index==2:
    pilotpassed=len(results)==2 and all(r['completed'] and r['lap_ms']<r['baseline_lap_ms'] for r in results);save(D/'pilot-gate.json',dict(passed=pilotpassed,conditions='2/2complete,strictpairedtimegainboth',results=results))
    if not pilotpassed:break
   F=D/road;assert not F.exists();F.mkdir(mode=0o700);worker=env=None;rows=[];start=time.perf_counter();ticks=0;simwall=policywall=0.
   try:
    worker=prepare(p['base'],F/'cpu',p['sandbox_path']);case=p['cases'][road];env=make_env();obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;t0=raw.t;reset=round(t0*50);worker.call('reset',obs);limit=4000 if index<2 else 12000;cap=min(2000,limit-read(D/'budget.json')['actions']);assert cap>0
    for step in range(1,cap+1):
     assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();r,ms=worker.call('act',obs);policywall+=ms/1000;base=np.array(r['action'],np.float32);action,audit=control(base,raw.car);assert np.array_equal(action[[0,2]],base[[0,2]]) and 0<=action[1]<=base[1];committed,cms=worker.call('commit',action);policywall+=cms/1000;assert np.float32(committed['memory'])==action[0] and committed['history'][-1]==action.tolist()
     b=read(D/'budget.json');assert b['actions']<limit;b['actions']+=1;save(D/'budget.json',b);before=raw.t;tic=time.perf_counter();obs,_,ended,truncated,info=env.step(action);simwall+=time.perf_counter()-tic;ticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;official_limit=step==2000 and not complete;terminal=bool(ended or truncated or official_limit)
     rows.append(dict(step=step,base=base.tolist(),action=action.tolist(),audit=audit,features=r['features'],memory=committed['state'],damage=env.damage.damage,collision=bool(info['collision']),terminal=terminal))
     with (F/'trace-journal-private.jsonl').open('a') as journal:journal.write(__import__('json').dumps(rows[-1])+'\n')
     (F/'trace-journal-private.jsonl').chmod(0o600)
     if terminal:break
    active=[r for r in rows if r['audit']['applied']];rear=[x for r in active for x in r['audit']['rear']];lap=round((raw.finish_time_s-t0)*1000) if complete else None
    out=dict(road=road,native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=lap,baseline_lap_ms=p['baseline_lap_ms'][road],lap_delta_ms=lap-p['baseline_lap_ms'][road] if complete else None,retire_reason=None if complete else info.get('retire_reason') or ('max_steps' if official_limit else 'budget_cut'),damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),applied_actions=len(active),fallback_actions=len(rows)-len(active),gas_changed_actions=sum(r['audit'].get('gas_changed',False) for r in rows),mean_base_gas=float(np.mean([r['base'][1] for r in rows])),mean_returned_gas=float(np.mean([r['action'][1] for r in rows])),firsttick_baseline_force_above_budget=sum(x['baseline_first_tick_long_force']>x['longitudinal_budget'] for x in rear),firsttick_returned_force_above_budget=sum(x['returned_first_tick_long_force']>x['longitudinal_budget']+1e-4 for x in rear),rear_wheel_samples=len(rear),preserved_steering_brake_and_memory_actions=len(rows),raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,env_step_wall_s=simwall,policy_IPC_wall_s=policywall,actor_CPU_s=committed['actor_cumulative_CPU_s'],GT_not_legal_candidate=True)
   finally:
    if worker:reaped=worker.close()
    if env:env.close()
   out['reaping']=reaped;save(F/'result.json',out);save(F/'trace-private.json',rows);results.append(out);save(D/'results-private.json',results);print(str(out),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(results=results,pilot_passed=pilotpassed,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-phase_start,CPU_s=time.process_time()-cpu))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);a.add_argument('--resume-unexecuted',action='store_true');args=a.parse_args();run(args.plan.resolve(),args.resume_unexecuted)
