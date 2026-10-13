"""Finalcategorical checkpoint16 only:6TRAIN+2screen candidate,2screenbaseline."""
import argparse,time,datetime,hashlib,json
from pathlib import Path
import numpy as np
from retry.path271_run import read,sha
from retry.preview286_run import save,plain

def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 D=path.parent;p=read(path);train=read(D/'training-plan.json');assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(Path(q))==h
 assert read(D/'state.json')['last_committed_batch']==16 and not (D/'evaluation-opening.json').exists();save(D/'evaluation-opening.json',dict(epoch=time.time(),checkpoint=16));save(D/'screen-opening.json',dict(final_checkpoint=16,opened_after_training=True,training_or_selection_use=False,registration_sha256=train['screen_registration_sha256']));seal=read(D/'screen-seal.json');seal['opened_for_policy_evaluation']=True;save(D/'screen-seal.json',seal);results=[];error=None;cpu=time.process_time();initials={}
 try:
  for item in p['order']:
   road,arm=item['road'],item['arm'];remaining=min(22884-read(D/'budget.json')['actions'],6500-read(D/'budget.json')['evaluation']);assert remaining>=650;F=D/'evaluation'/(road+'_'+arm);F.mkdir(parents=True,mode=0o700);worker=env=None;rows=[];ticks=0;start=time.perf_counter()
   try:
    worker=prepare(p[arm],F/'cpu',p['sandbox_path']);env=make_env();case=p['cases'][road];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});raw=env.unwrapped;t0=raw.t;reset=round(t0*50);obs_sha=hashlib.sha256(obs.tobytes()).hexdigest();assert hashlib.sha256(np.asarray(raw.track,dtype='<f8').tobytes()).hexdigest()==case['road_geometry_sha256']
    if road in p['initial_observations']:assert obs_sha==p['initial_observations'][road]
    if road in initials:assert initials[road]==obs_sha
    else:initials[road]=obs_sha
    worker.call('reset',obs);journal=(F/'trace-journal-private.jsonl').open('x');journalname=journal.name;Path(journalname).chmod(0o600)
    try:
     for step in range(1,651):
      assert time.time()<datetime.datetime.fromisoformat(train['deadline_utc']).timestamp();r,ms=worker.call('act',obs);action=np.array(r['action'],np.float32);assert not r['python_audit_denied_events']
      if arm=='candidate':assert np.float32(r['nominal_state']['previous_steer'])==action[0] and r['executed_history'][-1]==action.tolist()
      b=read(D/'budget.json');assert b['actions']<22884 and b['evaluation']<6500;b['actions']+=1;b['evaluation']+=1;save(D/'budget.json',b);before=raw.t;obs,_,ended,truncated,info=env.step(action);ticks+=round((raw.t-before)*50);complete=raw.finish_time_s is not None;terminal=bool(ended or truncated)
      row=dict(step=step,action=action.tolist(),macro=r['macro_audit'],features=r['features'],memory=r['nominal_state'],damage=env.damage.damage,collision=bool(info['collision']),compute_ms=r['act_compute_ms'],IPC_ms=ms);journal.write(json.dumps(plain(row),allow_nan=False)+'\n');journal.flush();rows.append(row)
      if terminal:break
    finally:journal.close()
    minimal=dict(road=road,arm=arm,cohort=p['cohorts'][road],native_actions=step,completed=complete,actual_DNF=terminal and not complete,censored=not terminal,lap_ms=round((raw.finish_time_s-t0)*1000) if complete else None,damage=env.damage.damage,visited=raw.tile_visited_count,total_tiles=len(raw.track),retire_reason=None if complete else info.get('retire_reason') or 'budget_cut',raw_step_ticks=ticks,raw_reset_ticks=reset);save(F/'terminal-receipt.json',minimal)
    macros=[r['macro'] for r in rows if r['macro'] is not None];out=dict(minimal,wall_s=time.perf_counter()-start,actor_CPU_s=r['actor_cumulative_CPU_s'],macro_decisions=sum(m['decision'] for m in macros),native_macro_counts={str(c):sum(m['category']==c for m in macros) for c in range(5)},decision_macro_counts={str(c):sum(m['category']==c and m['decision'] for m in macros) for c in range(5)},Agent_ms=dict(median=float(np.median([r['compute_ms'] for r in rows])),p95=float(np.percentile([r['compute_ms'] for r in rows],95)),max=float(max(r['compute_ms'] for r in rows))),pixel_only=True,GT_inputs=False,archive_sha256=p[arm]['archive_sha256'])
   finally:
    if worker:reaped=worker.close()
    if env:env.close()
   out['reaping']=reaped;save(F/'result.json',out);results.append(out);save(D/'evaluation-results-private.json',results);print(str({k:out[k] for k in ['road','arm','completed','actual_DNF','censored','lap_ms','native_actions']}),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'evaluation-outcome-private.json',dict(results=results,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'evaluation-opening.json')['epoch'],CPU_s=time.process_time()-cpu))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
