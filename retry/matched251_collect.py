"""One on-policy240 materialization and matched249teacher per six training roads."""
import argparse,json,time,hashlib,datetime
from pathlib import Path
import numpy as np


def run(path):
 from retry.frozen_composite_runtime import prepare
 from retry.diagnose import make_env
 from retry.full_route_reproduction import truth
 from retry.source_vehicle_transition import capture
 from retry.receding_horizon_oracle import predict_actions,contiguous_visited_tiles
 from retry.matched251_targets import residual_delta
 p=json.loads(path.read_text());D=path.parent;norm=np.load(p['original_model']);mean,std,W=norm['mean'],norm['std'],norm['weights']
 def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
 def read(q):return json.loads(q.read_text())
 def save(q,x):
  t=q.with_name(q.name+'.tmp');t.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');t.chmod(0o600);t.replace(q)
 assert sha(path)==path.with_suffix('.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h
 if not (D/'opening.json').exists():save(D/'opening.json',dict(start_epoch=time.time()))
 error=None;receipts=[];cpu=time.process_time()
 try:
  for label in p['road_order']:
   folder=D/'training'/label;ref=p['references'][label];commands=np.asarray(ref['actions'],np.float32)
   if folder.exists():assert (folder/'materialized.json').exists(),'Unfinished native collection: never replay'
   else:
    folder.mkdir(parents=True,mode=0o700);worker=env=None;obsrows=[];features=[];nominal=[];actual=[];snaps={};raw=0;start=time.perf_counter()
    try:
     worker=prepare(p['base'],folder/'cpu',p['sandbox_path']);env=make_env();case=p['roads'][label];obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});assert hashlib.sha256(obs.tobytes()).hexdigest()==ref['initial_observation_sha256'];start_t=env.unwrapped.t;reset_ticks=round(start_t*50);worker.call('reset',obs)
     for i,command in enumerate(commands):
      assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();step=i+1;response,ms=worker.call('act',obs);assert ms<=5000 and np.array_equal(np.asarray(response['action'],np.float32),command);obsrows.append(obs.copy());features.append(response['legal_feature_audit']['features']);nominal.append(response['legal_feature_audit']['nominal_action'])
      if i%3==0 and len(commands)-i>=12:snaps[str(step)]=capture(env)
      b=read(D/'budget.json');assert b['actions']<7000;b['actions']+=1;b['phases']['collection']=b['phases'].get('collection',0)+1;save(D/'budget.json',b);old_t=env.unwrapped.t;obs,_,ended,truncated,info=env.step(command);raw+=round((env.unwrapped.t-old_t)*50);t=truth(env);visited={int(tile.idx) for tile in env.unwrapped.road if tile.road_visited};t.update(contiguous=contiguous_visited_tiles(visited,len(env.unwrapped.track)),visited_ids=sorted(visited),wheel_road_contacts=sum(bool(w.tiles) for w in env.unwrapped.car.wheels),collision=bool(info['collision']),terminal=bool(ended or truncated))
      reference=ref['rows'][i];assert t['unique_tiles']==reference['visited'] and t['damage']==reference['damage'] and abs(t['speed_m_s']-reference['speed_m_s'])<1e-10;actual.append(t)
      if ended or truncated:assert step==len(commands);break
     assert env.unwrapped.finish_time_s is not None and round((env.unwrapped.finish_time_s-start_t)*1000)==ref['lap_ms'];obsrows.append(obs.copy())
     m=dict(label=label,native_actions=len(commands),raw_step_ticks=raw,raw_reset_ticks=reset_ticks,snapshots=snaps,actual=actual,wall_s=time.perf_counter()-start,base_actor_CPU_s=response['actor_cumulative_CPU_s'])
    finally:
     if worker:reaping=worker.close()
     if env:env.close()
    cache=folder/'cache-private.npz';np.savez_compressed(cache,observations=np.asarray(obsrows),features=np.asarray(features),nominal=np.asarray(nominal,np.float32),commands=commands);cache.chmod(0o600);m['reaping']=reaping;save(folder/'materialized.json',m)
   m=read(folder/'materialized.json');c=np.load(folder/'cache-private.npz');labels=[];indices=[];queries=[]
   for i in range(0,len(commands),3):
    q=folder/('query'+str(i+1)+'.json')
    if q.exists():r=read(q)
    else:
     selected='baseline';status='tail_baseline';predictions={};snapshot=m['snapshots'].get(str(i+1));target=commands[i,1:].copy();delta=np.zeros(2);modelwall=0.
     if snapshot is not None:
      sequence=commands[i:i+12];visited={x['idx'] for x in snapshot['roads'] if x['visited']};count=snapshot['road_count'];before=contiguous_visited_tiles(visited,count);actual=m['actual'][i:i+12];goal=actual[-1]['contiguous']
      def frontier(row):return contiguous_visited_tiles(visited|set(row['newly_visited_tile_ids']),count)
      def forecast(a):
       b=read(D/'budget.json');b['model_queries']+=1;save(D/'budget.json',b);pred=predict_actions(snapshot,a,True);b=read(D/'budget.json');b['model_ticks']+=pred['model_physics_ticks'];save(D/'budget.json',b);return pred
      base=forecast(sequence);modelwall+=base['wall_s'];valid=len(base['rows'])==12 and all(base['initialization'].values());errors={k:0. for k in p['match_limits']};mismatch=0
      for a,b in zip(actual,base['rows']):
       mismatch+=sum(a[k]!=b[k] for k in ['unique_tiles','collision','wheel_road_contacts','off_track_counter','terminal'])+int(a['contiguous']!=frontier(b))
       for k,v in [('position_error_m',np.linalg.norm(np.asarray(a['position'])-b['position'])),('speed_error_m_s',abs(a['speed_m_s']-b['speed_m_s'])),('angle_error_rad',abs(a['angle']-b['angle'])),('damage_error',abs(a['damage']-b['damage']))]:errors[k]=max(errors[k],float(v))
      valid=valid and mismatch==0 and all(errors[k]<=v for k,v in p['match_limits'].items());status='incomparable_baseline' if not valid else 'no_frontier_baseline' if goal<=before else 'baseline_tie'
      def passage(pred):return None if any(row['terminal'] for row in pred['rows']) else next((j+1 for j,row in enumerate(pred['rows']) if frontier(row)>=goal),None)
      if valid and goal>before:
       best=passage(base);assert best is not None;seen={sequence.tobytes():best}
       for name,ch,bound in [('gas_upper',1,1),('brake_lower',2,-1),('brake_upper',2,1)]:
        changed=sequence.copy();changed[:3,ch]=np.clip(np.clip(c['nominal'][i:i+3,ch].astype(float)+.5*bound,0,1)*p['scales'][ch-1],0,1).astype(np.float32)
        if changed.tobytes() in seen:value=seen[changed.tobytes()]
        else:pred=forecast(changed);modelwall+=pred['wall_s'];value=passage(pred);seen[changed.tobytes()]=value
        predictions[name]=value
        if value is not None and value<best:selected=name;best=value;target=changed[0,1:].copy();status='intervention_selected'
     feature=c['features'][i];raw_residual=np.r_[(feature-mean)/std,1.]@W
     if selected!='baseline':delta=residual_delta(c['nominal'][i,1:],raw_residual,target,p['scales'])
     r=dict(action=i+1,status=status,selected=selected,delta=delta.tolist(),target_final_pedals=target.tolist(),model_wall_s=modelwall,first_passages=predictions);save(q,r)
    labels.append(r['delta']);indices.append(i);queries.append(r)
   targetfile=folder/'targets-private.npz'
   if not targetfile.exists():np.savez(targetfile,features=c['features'][indices],delta=np.asarray(labels));targetfile.chmod(0o600)
   receipt=dict(road=label,rows=len(labels),statuses={k:sum(x['status']==k for x in queries) for k in set(x['status'] for x in queries)},selections={k:sum(x['selected']==k for x in queries) for k in ['baseline','gas_upper','brake_lower','brake_upper']},model_wall_s=sum(x['model_wall_s'] for x in queries));save(folder/'teacher-receipt.json',receipt);receipts.append(receipt);print(json.dumps(receipt),flush=True)
 except Exception as e:error=type(e).__name__+': '+str(e)
 save(D/'collection-outcome.json',dict(receipts=receipts,technical_error=error,budget=read(D/'budget.json'),wall_s=time.time()-read(D/'opening.json')['start_epoch'],CPU_this_process_s=time.process_time()-cpu))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--plan',type=Path,required=True);run(a.parse_args().plan.resolve())
