"""Replay saved local planner controls for minimal pre-failure connection evidence."""
import json,time,hashlib,datetime
from pathlib import Path
import numpy as np
from retry.diagnose import make_env
from retry.visible260_plan import observed_geometry,local_plan,local_center

def run(D):
 R=D.parent;p=json.loads((D/'source-plan.json').read_text())
 def save(q,x):q.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');q.chmod(0o600)
 assert not (D/'diagnostic-opening.json').exists(),'Do not replay an already started prefix'
 save(D/'diagnostic-opening.json',dict(epoch=time.time()))
 receipts=[];records=[];error=None
 try:
  for road,limit in [('O0',184),('N0',308)]:
   rows=json.loads((R/'stage260'/road/'trajectory-private.json').read_text());case=p['cases'][road];env=make_env();start=time.perf_counter();plan=None;created=None;rawticks=0;maxgap=0.;points=[]
   chosen={49,52,55,58,61,64,79,82,85,133,136,139,178,181,184} if road=='O0' else set(range(268,308,3))
   try:
    obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observations'][road]
    reset_ticks=round(env.unwrapped.t*50)
    for step in range(1,limit+1):
     assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();raw=env.unwrapped
     if (step-1)%3==0:
      data=observed_geometry(raw);new=local_plan(data,p['model'])
      if new is not None and new['geometrically_feasible']:plan=new;created=step
      if step in chosen:
       center=local_center(data);pos=data['pose'];forward=data['forward'];r=dict(road=road,step=step,pose=pos.tolist(),forward=forward.tolist(),speed=data['speed'],segments=[s.tolist() for s in data['segments']],obstacles=data['obstacles'].tolist(),radii=data['radii'].tolist(),center=center.tolist() if center is not None else None,new_feasible=new['geometrically_feasible'] if new else None,new_violation=new['geometry_violation'] if new else None,new_calls=new['objective_calls'] if new else 0,retained_created=created,plan_age=step-created if created else None,previous_action=rows[step-2]['action'],action=rows[step-1]['action'],action_delta=(np.asarray(rows[step-1]['action'])-rows[step-2]['action']).tolist(),target_speed=rows[step-1]['target_speed_m_s'])
       if plan:
        line=plan['line'];v=np.diff(line,axis=0);u=np.clip(np.sum((pos-line[:-1])*v,axis=1)/np.maximum(np.sum(v*v,axis=1),1e-9),0,1);proj=line[:-1]+u[:,None]*v;j=int(np.argmin(np.linalg.norm(proj-pos,axis=1)));r.update(plan_start=line[0].tolist(),plan_end=line[-1].tolist(),plan_nodes=len(line),plan_length=plan['visible_length_m'],plan_speed=plan['speed'].tolist(),plan_ds=plan['ds'].tolist(),nearest_segment=j,nearest_fraction=float(u[j]),plan_distance=float(np.linalg.norm(proj[j]-pos)),start_forward_distance=float((line[0]-pos)@forward),end_forward_distance=float((line[-1]-pos)@forward),tail_curvature=plan['assumed_tail_curvature'],endpoint_passed=float((pos-line[-1])@v[-1]/max(np.linalg.norm(v[-1]),1e-9)))
       points.append(r)
     before=raw.t;b=json.loads((D/'budget.json').read_text());assert b['actions']<3865;b['actions']+=1;save(D/'budget.json',b);obs,_,end,trunc,info=env.step(np.asarray(rows[step-1]['action'],np.float32));rawticks+=round((raw.t-before)*50)
     if step<limit:
      ref=rows[step];gap=abs(float(np.linalg.norm(raw.car.hull.linearVelocity))-ref['speed_m_s']);maxgap=max(maxgap,gap);assert gap<.01
     assert raw.tile_visited_count==rows[step-1]['visited'];assert abs(env.damage.damage-rows[step-1]['damage'])<1e-6;assert not end and not trunc
   finally:env.close()
   rec=dict(road=road,prefix_native=limit,raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,wall_s=time.perf_counter()-start,max_speed_replay_gap=maxgap,sampled_records=len(points),physics_match=True);save(D/(road+'-diagnostic-private.json'),points);receipts.append(rec);records.extend(points);save(D/'diagnostic-receipts.json',receipts);print(json.dumps(rec),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'diagnostic-outcome.json',dict(receipts=receipts,technical_error=error,budget=json.loads((D/'budget.json').read_text()),wall_s=time.time()-json.loads((D/'diagnostic-opening.json').read_text())['epoch']))

if __name__=='__main__':
 import argparse
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--stage-dir',type=Path,required=True);run(a.parse_args().stage_dir.resolve())
