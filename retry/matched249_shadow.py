"""Matched-steering 12-action privileged shadows, exact240 two-road materialization.

No training or actual pulse driving. Existing source/contact restore and196
accuracy limits reused. Frontier times have four-tick/80ms resolution.
"""
import argparse,json,time,datetime,hashlib
from pathlib import Path
import numpy as np


def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 from retry.full_route_reproduction import truth
 from retry.source_vehicle_transition import capture
 from retry.receding_horizon_oracle import predict_actions,contiguous_visited_tiles
 p=json.loads(path.read_text());D=path.parent
 def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
 def read(q):return json.loads(q.read_text())
 def save(q,x):
  tmp=q.with_name(q.name+'.tmp');tmp.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');tmp.chmod(0o600);tmp.replace(q)
 assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 if not (D/'opening.json').exists():save(D/'opening.json',dict(start_epoch=time.time()))
 material=[];reports=[];error=None;cpu=time.process_time()
 try:
  for label in ['O0','N0']:
   folder=D/label;case=p['cases'][label];ref=p['references'][label]
   if folder.exists():
    assert (folder/'materialized.json').exists(),'Unfinishednative materialization: never rerun'
    m=read(folder/'materialized.json')
   else:
    folder.mkdir(mode=0o700);commands=np.asarray(ref['actions'],np.float32);worker=env=None;rows=[];nominal=[];snaps={};rawticks=0;start=time.perf_counter();simwall=[]
    try:
     worker=prepare(p['base'],folder/'cpu',p['sandbox_path']);env=make_env();obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});reset_ticks=round(env.unwrapped.t*50);start_t=env.unwrapped.t;assert hashlib.sha256(obs.tobytes()).hexdigest()==ref['initial_observation_sha256'];worker.call('reset',obs)
     for i,saved in enumerate(commands):
      assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();step=i+1
      response,ms=worker.call('act',obs);actual=np.asarray(response['action'],np.float32);assert np.array_equal(actual,saved) and ms<=5000;nominal.append(response['legal_feature_audit']['nominal_action'])
      if step in p['anchors'][label]:snaps[str(step)]=capture(env)
      b=read(D/'budget.json');assert b['actual_actions']<6504;b['actual_actions']+=1;save(D/'budget.json',b);old_t=env.unwrapped.t;tic=time.perf_counter();obs,_,ended,truncated,info=env.step(saved);simwall.append(time.perf_counter()-tic);ticks=round((env.unwrapped.t-old_t)*50);rawticks+=ticks;t=truth(env);visited={int(tile.idx) for tile in env.unwrapped.road if tile.road_visited};t.update(action=step,contiguous=contiguous_visited_tiles(visited,len(env.unwrapped.track)),visited_ids=sorted(visited),wheel_road_contacts=sum(bool(w.tiles) for w in env.unwrapped.car.wheels),collision=bool(info['collision']),terminal=bool(ended or truncated),raw_ticks=ticks)
      old=ref['rows'][i];assert t['unique_tiles']==old['visited'] and t['damage']==old['damage'] and abs(t['speed_m_s']-old['speed_m_s'])<1e-10
      rows.append(t)
      if ended or truncated:assert step==len(commands);break
     assert env.unwrapped.finish_time_s is not None and round((env.unwrapped.finish_time_s-start_t)*1000)==ref['lap_ms']
     m=dict(label=label,native_actions=len(rows),lap_ms=ref['lap_ms'],raw_step_ticks=rawticks,raw_reset_ticks=reset_ticks,snapshots=snaps,rows=rows,commands=commands.tolist(),nominal=nominal,env_step_wall_s=simwall,wall_s=time.perf_counter()-start,base_actor_CPU_s=response['actor_cumulative_CPU_s'])
    finally:
     if worker:reaping=worker.close()
     if env:env.close()
    m['reaping']=reaping;save(folder/'materialized.json',m)
   material.append(m)
   for anchor in p['anchors'][label]:
    q=folder/('shadow'+str(anchor)+'.json')
    if q.exists():reports.append(read(q));continue
    snapshot=m['snapshots'][str(anchor)];sequence=np.asarray(m['commands'][anchor-1:anchor+11],np.float32);nom=np.asarray(m['nominal'][anchor-1:anchor+2],np.float32);actual=m['rows'][anchor-1:anchor+11];assert len(sequence)==len(actual)==12
    def forecast(actions):
     b=read(D/'budget.json');b['model_queries']+=1;save(D/'budget.json',b);prediction=predict_actions(snapshot,actions,True);b=read(D/'budget.json');b['model_ticks']+=prediction['model_physics_ticks'];save(D/'budget.json',b);return prediction
    base=forecast(sequence);before=contiguous_visited_tiles({r['idx'] for r in snapshot['roads'] if r['visited']},snapshot['road_count']);target=actual[-1]['contiguous']
    visited={r['idx'] for r in snapshot['roads'] if r['visited']}
    def contiguous(row):return contiguous_visited_tiles(visited|set(row['newly_visited_tile_ids']),snapshot['road_count'])
    mismatch={k:0 for k in ['contiguous','unique_tiles','contact','road_wheels','counter','terminal']};limits=p['match_limits'];errors=dict(position_error_m=0.,speed_error_m_s=0.,angle_error_rad=0.,damage_error=0.)
    for a,b in zip(actual,base['rows']):
     for name,left,right in [('contiguous',a['contiguous'],contiguous(b)),('unique_tiles',a['unique_tiles'],b['unique_tiles']),('contact',a['collision'],b['collision']),('road_wheels',a['wheel_road_contacts'],b['wheel_road_contacts']),('counter',a['off_track_counter'],b['off_track_counter']),('terminal',a['terminal'],b['terminal'])]:mismatch[name]+=int(left!=right)
     for name,v in [('position_error_m',np.linalg.norm(np.asarray(a['position'])-b['position'])),('speed_error_m_s',abs(a['speed_m_s']-b['speed_m_s'])),('angle_error_rad',abs(a['angle']-b['angle'])),('damage_error',abs(a['damage']-b['damage']))]:errors[name]=max(errors[name],float(v))
    valid=len(base['rows'])==12 and all(base['initialization'].values()) and not any(mismatch.values()) and all(errors[k]<=v for k,v in limits.items())
    report=dict(road=label,anchor=anchor,baseline_valid=valid,verification=dict(mismatch=mismatch,max_errors=errors,initialization=base['initialization']),initial_frontier=before,target=target,candidates={},baseline_model_wall_s=base['wall_s'],model_wall_s=base['wall_s'],saved_actual_suffix_env_step_wall_s=sum(m['env_step_wall_s'][anchor-1:anchor+11]))
    def score(prediction):
     terminal=any(r['terminal'] for r in prediction['rows']);passage=next((i+1 for i,r in enumerate(prediction['rows']) if contiguous(r)>=target),None)
     return dict(first_passage_actions=passage if not terminal else None,terminal=terminal,damage=prediction['rows'][-1]['damage'],contact_actions=[i+1 for i,r in enumerate(prediction['rows']) if r['collision']],frontier=contiguous(prediction['rows'][-1]),model_physics_ticks=prediction['model_physics_ticks'])
    report['candidates']['baseline']=score(base)
    if not valid:report.update(status='incomparable_model_baseline',selected=None)
    elif target<=before:report.update(status='incomparable_no_new_frontier',selected=None)
    else:
     seen={sequence.tobytes():'baseline'};scoremap={'baseline':report['candidates']['baseline']}
     for name,channel,bound in [('gas_upper',1,1),('brake_lower',2,-1),('brake_upper',2,1)]:
      changed=sequence.copy();pedals=np.clip(nom[:,channel].astype(float)+.5*bound,0,1);changed[:3,channel]=np.clip(pedals*p['scales'][channel-1],0,1).astype(np.float32);assert np.array_equal(changed[:,0],sequence[:,0]) and np.array_equal(changed[3:],sequence[3:]) and np.array_equal(changed[:,3-channel],sequence[:,3-channel])
      if changed.tobytes() in seen:result=dict(scoremap[seen[changed.tobytes()]],reused=seen[changed.tobytes()]);report['candidates'][name]=result
      else:
       pred=forecast(changed);result=score(pred);report['model_wall_s']+=pred['wall_s'];report['candidates'][name]=result;seen[changed.tobytes()]=name;scoremap[name]=result
     basepass=report['candidates']['baseline']['first_passage_actions'];assert basepass is not None
     selected='baseline';best=basepass
     for name in ['gas_upper','brake_lower','brake_upper']:
      value=report['candidates'][name]['first_passage_actions']
      if value is not None and value<best:selected=name;best=value
     report.update(status='improved' if best<basepass else 'tie_baseline',selected=selected,saved_first_passage_physics_s=(basepass-best)*4/50,actual_baseline_first_passage_actions=next(i+1 for i,row in enumerate(actual) if row['contiguous']>=target),worse_candidates=sum(r['first_passage_actions'] is None or r['first_passage_actions']>basepass for name,r in report['candidates'].items() if name!='baseline'),tied_candidates=sum(r['first_passage_actions']==basepass for name,r in report['candidates'].items() if name!='baseline'))
    save(q,dict(report=report,baseline_prediction=base));reports.append(dict(report=report,baseline_prediction=base));print(json.dumps({k:report.get(k) for k in ['road','anchor','status','selected','saved_first_passage_physics_s']}),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'outcome-private.json',dict(stage=249,materialized_labels=[m['label'] for m in material],reports=reports,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['start_epoch'],CPU_s=time.process_time()-cpu))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
