"""Same-execution pixel/features/actualterminal reward capture, no new policy."""
import argparse,time,datetime,json,hashlib
from pathlib import Path
import numpy as np
from retry.path271_run import read,sha
from retry.preview286_run import save,plain
from retry.ppo244_math import reward

def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 p=read(path);D=path.parent;assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(Path(q))==h
 assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));results=[];error=None;cpu=time.process_time()
 try:
  for job in p['jobs']:
   road,behavior,cap=job['road'],job['behavior'],job['cap'];F=D/(road+'_'+behavior);assert not F.exists();F.mkdir(mode=0o700);worker=env=None;pixels=[];features=[];rewards=[];rows=[];history=[];ticks=0;prevp=prevt=0.;start=time.perf_counter()
   try:
    assert 6000-read(D/'budget.json')['actions']>=cap;worker=prepare(p['configs'][behavior],F/'cpu',p['sandbox_path']);env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;t0=raw.t;reset=round(t0*50);assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road];worker.call('reset',obs);journal=(F/'trace-journal-private.jsonl').open('x');Path(journal.name).chmod(0o600)
    try:
     for step in range(1,cap+1):
      assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();image=np.rint(obs*255).astype(np.uint8);assert np.array_equal((image.astype(np.float64)/255).astype(np.float32),obs);r,_=worker.call('act',obs);action=np.array(r['action'],np.float32);padded=np.zeros((3,3));mask=np.zeros(3)
      if history:padded[-len(history):]=history;mask[-len(history):]=1
      x=np.r_[r['features'],(padded/np.array([.4,1,1])).ravel(),mask];assert x.shape==(28,) and np.isfinite(x).all();pixels.append(image);features.append(x)
      b=read(D/'budget.json');assert b['actions']<6000;b['actions']+=1;save(D/'budget.json',b);before=raw.t;obs,_,ended,truncated,info=env.step(action);ticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;terminal=bool(ended or truncated);t=raw.finish_time_s-t0 if complete else raw.t-t0;progress=raw.tile_visited_count/len(raw.track);rt=reward(progress,prevp,t,prevt,'completed' if complete else 'DNF' if terminal else None);prevp,prevt=progress,t;rewards.append(rt);history=(history+[action.tolist()])[-3:]
      row=dict(step=step,action=action.tolist(),reward=rt,completed=complete,terminal=terminal,damage=env.damage.damage,progress=progress,time_s=t);journal.write(json.dumps(plain(row),allow_nan=False)+'\n');journal.flush();rows.append(row)
      if terminal:break
    finally:journal.close()
    out=dict(road=road,behavior=behavior,native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=round((raw.finish_time_s-t0)*1000) if complete else None,retire_reason=None if complete else info.get('retire_reason') or 'budget_cut',damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,actor_CPU_s=r['actor_cumulative_CPU_s'],pixel_frame_rows=len(pixels),stored_sameexecution=True)
    if terminal:assert abs(sum(rewards)-(2-t/160 if complete else progress-1))<1e-9
    save(F/'terminal-receipt.json',out);data=F/'observations-private.npz';np.savez_compressed(data,pixels=np.array(pixels,np.uint8),features=np.array(features,np.float64),rewards=np.array(rewards,np.float64),completed=np.array(complete),actual_terminal=np.array(terminal));data.chmod(0o600)
   finally:
    if worker:reaped=worker.close()
    if env:env.close()
   out['reaping']=reaped;save(F/'result.json',out);results.append(out);save(D/'results-private.json',results);print(str({k:out[k] for k in ['road','behavior','completed','actual_DNF','censored','native_actions']}),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'collection-outcome-private.json',dict(results=results,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['epoch'],CPU_s=time.process_time()-cpu))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
