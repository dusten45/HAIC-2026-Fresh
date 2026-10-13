"""Minimal action97..103 trace of saved local GT policies; no new policy fitting."""
import argparse,json,hashlib,time,datetime,textwrap
from pathlib import Path
import numpy as np
from retry.diagnose import make_env
from retry.visible260_plan import observed_geometry,local_plan as plan260
from retry.visible261_plan import local_plan as plan261

def control_trace(plan,pos,speed,rawenv,laststeer,model):
    # Execute the unchanged archived controller body; return its intermediate values.
    src=Path(__file__).with_name('visible261_run.py').read_text();block=src.split('                    if plan is None:',1)[1].split('                    actms.append',1)[0];body=textwrap.dedent('                    if plan is None:'+block)
    scope=dict(plan=plan,pos=pos,speed=speed,rawenv=rawenv,laststeer=laststeer,model=model,np=np);exec(body,scope)
    keys=['action','laststeer','err','desired','idx','u','sarc','arc','look','goal','target','delta','x','feed','acc']
    return {k:scope[k] for k in keys if k in scope}

def run(D):
 R=D.parent;p=json.loads((D/'diagnostic-plan.json').read_text())
 def sha(q):return hashlib.sha256(q.read_bytes()).hexdigest()
 def save(q,x):q.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');q.chmod(0o600)
 for q,h in p['hashes'].items():assert sha(Path(q))==h
 assert not (D/'diagnostic-opening.json').exists(),'Started prefix: no replay'
 save(D/'diagnostic-opening.json',dict(epoch=time.time()));receipts=[];error=None
 try:
  for stage in [260,261]:
   old=json.loads((R/('stage'+str(stage))/'N0/trajectory-private.json').read_text());env=make_env();memory={};plan=None;created=None;laststeer=0.;records=[];ticks=0;calls=0;start=time.perf_counter();ms=[]
   try:
    case=p['case'];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observation'];resetticks=round(env.unwrapped.t*50)
    for step in range(1,104):
     assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();raw=env.unwrapped;pos=np.asarray(raw.car.hull.position);velocity=np.asarray(raw.car.hull.linearVelocity);speed=float(np.linalg.norm(velocity));new=None
     assert abs(speed-old[step-1]['speed_m_s'])<.01
     if (step-1)%3==0:
      tic=time.perf_counter();data=observed_geometry(raw);new=plan260(data,p['model']) if stage==260 else plan261(data,p['model'],memory);ms.append((time.perf_counter()-tic)*1000);calls+=new['objective_calls'] if new else 0
      if new is not None and new['geometrically_feasible']:plan=new;created=step
     trace=control_trace(plan,pos,speed,raw,laststeer,p['model']);laststeer=trace['laststeer'];assert np.array_equal(trace['action'],np.asarray(old[step-1]['action'],np.float32))
     if step>=97:
      idx=trace['idx'];u=trace['u'][idx];forward=np.asarray(raw.car.hull.GetWorldVector((0,1)));direction=velocity/max(speed,1e-9);delta=trace['delta'];segment=plan['line'][idx+1]-plan['line'][idx];tangent=segment/np.linalg.norm(segment);k=plan['curvature'][idx];v=plan['speed'];r=dict(stage=stage,step=step,pose=pos.tolist(),hull_forward=forward.tolist(),velocity=velocity.tolist(),speed=speed,velocity_hull_dot=float(direction@forward),target_body_forward=float(delta@forward),target_velocity_forward=float(delta@direction),plan_tangent_body_dot=float(tangent@forward),plan_tangent_velocity_dot=float(tangent@direction),plan_created=created,plan_age=step-created,replanned=(step-1)%3==0,new_available=new is not None,new_feasible=new['geometrically_feasible'] if new else None,plan_start=plan['line'][0].tolist(),plan_end=plan['line'][-1].tolist(),plan_length=plan['visible_length_m'],nearest_idx=int(idx),fraction=float(u),arc=float(trace['arc']),goal_arc=float(trace['goal']),tail_extension=bool(trace['goal']>trace['sarc'][-1]),target=trace['target'].tolist(),path_error=trace['err'],segment_s0=float(trace['sarc'][idx]),segment_s1=float(trace['sarc'][idx+1]),v0=float(v[idx]),v1=float(v[idx+1]),curvature=float(k),curvature_cap=float(min(100,np.sqrt(p['model']['lateral_accel']/max(abs(k),1e-6)))),desired=trace['desired'],feedforward=trace['feed'],feedback=1.5*(trace['desired']-speed),command_acc=trace['acc'],action=trace['action'].tolist());records.append(r)
      if step in [97,100]:save(D/(f'stage{stage}-plan{step}-private.json'),dict(line=plan['line'].tolist(),speed=plan['speed'].tolist(),curvature=plan['curvature'].tolist(),ds=plan['ds'].tolist(),new_geometry=[s.tolist() for s in data['segments']],new_obstacles=data['obstacles'].tolist()))
     b=json.loads((D/'budget.json').read_text());assert b['actions']<2917;b['actions']+=1;save(D/'budget.json',b);before=raw.t;_,_,end,trunc,info=env.step(trace['action']);ticks+=round((raw.t-before)*50);assert raw.tile_visited_count==old[step-1]['visited'];assert abs(env.damage.damage-old[step-1]['damage'])<1e-6;assert not end and not trunc
   finally:env.close()
   save(D/(f'stage{stage}-trace-private.json'),records);receipt=dict(stage=stage,prefix_actions=103,raw_step_ticks=ticks,raw_reset_ticks=resetticks,wall_s=time.perf_counter()-start,objective_calls=calls,planning_ms_sum=sum(ms),matched_actions_bitexact=True,matched_physics=True,selected_trace_rows=len(records));receipts.append(receipt);save(D/'diagnostic-receipts.json',receipts);print(json.dumps(receipt),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'diagnostic-outcome.json',dict(receipts=receipts,technical_error=error,budget=json.loads((D/'budget.json').read_text()),wall_s=time.time()-json.loads((D/'diagnostic-opening.json').read_text())['epoch']))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--stage-dir',type=Path,required=True);run(a.parse_args().stage_dir.resolve())
