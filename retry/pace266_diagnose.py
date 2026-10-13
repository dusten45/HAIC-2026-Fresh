"""Exact existing1.5 prefix + four tiny source-force probes; no new pace search."""
import argparse,json,time,hashlib,datetime
from pathlib import Path
import numpy as np

def run(D):
 from retry.diagnose import make_env
 from retry.source_vehicle_transition import capture
 from retry.force255_probe import forecast
 p=json.loads((D/'diagnostic-plan.json').read_text())
 def sha(q):return hashlib.sha256(Path(q).read_bytes()).hexdigest()
 def save(q,x):q.write_text(json.dumps(x,indent=2,allow_nan=False)+'\n');q.chmod(0o600)
 for q,h in p['hashes'].items():assert sha(q)==h
 assert not (D/'diagnostic-opening.json').exists(),'Started prefix: no replay'
 save(D/'diagnostic-opening.json',dict(epoch=time.time()));env=None;snaps={};ticks=0;error=None;queries=0;mticks=0;results=[];start=time.perf_counter()
 try:
  old=json.loads(Path(p['reference']).read_text());env=make_env();obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});assert hashlib.sha256(obs.tobytes()).hexdigest()==p['initial_observation'];reset=round(env.unwrapped.t*50)
  for step in range(1,170):
   assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc']).timestamp();raw=env.unwrapped;assert abs(float(np.linalg.norm(raw.car.hull.linearVelocity))-old[step-1]['speed_m_s'])<1e-8
   if step in [13,54,165,167]:snaps[str(step)]=capture(env)
   b=json.loads((D/'budget.json').read_text());b['actions']+=1;assert b['actions']<=3737;save(D/'budget.json',b);before=raw.t;_,_,end,trunc,info=env.step(np.asarray(old[step-1]['action'],np.float32));ticks+=round((raw.t-before)*50);assert raw.tile_visited_count==old[step-1]['visited'];assert env.damage.damage==old[step-1]['damage'];assert not end and not trunc
  env.close();env=None;save(D/'prefix-snapshots-private.json',snaps);save(D/'prefix-receipt.json',dict(road='N0',pace=1.5,native_actions=169,raw_step_ticks=ticks,raw_reset_ticks=reset,wall_s=time.perf_counter()-start,matched_speed_damage_tiles=True))
  model=p['model']
  for anchor in [13,54,165,167]:
   sample=old[anchor-1:anchor+2];baseline=np.array([r['action'] for r in sample],np.float32);candidate=baseline.copy()
   for i,r in enumerate(sample):
    unclipped=r['feedforward_accel']+r['feedback_accel'];positive=max(unclipped,0);candidate[i,1]=np.clip(model['effective_mass']*positive*(r['speed_m_s']+2.7)/80000,0,1)
   trials={}
   for name,commands in [('baseline',baseline),('positive_unclamped',candidate)]:
    q=forecast(snaps[str(anchor)],commands,True);queries+=1;mticks+=q['physics_ticks'];save(D/(str(anchor)+'-'+name+'-private.json'),q);force=q['forces']
    def group(indices):
     z=[f for f in force if f['wheel'] in indices];ts=sorted({f['physics_tick'] for f in z});return dict(mean_body_forward_N=float(np.mean([sum(f['body_forward_N'] for f in z if f['physics_tick']==t) for t in ts])),clipped_fraction=float(np.mean([f['clipped'] for f in z])),mean_raw_long_N=float(np.mean([f['raw_long_N'] for f in z])),mean_applied_long_N=float(np.mean([f['applied_long_N'] for f in z])))
    trials[name]=dict(commands=commands.tolist(),front=group([0,1]),rear=group([2,3]),end_speed_m_s=q['rows'][-1]['speed_m_s'],end_damage=q['rows'][-1]['damage'],collision=any(x['collision'] for x in q['rows']),all_wheels_road=all(x['wheel_road_contacts']==4 for x in q['rows']))
    if name=='baseline':
     gaps=[abs(row['speed_m_s']-old[anchor+j]['speed_m_s']) for j,row in enumerate(q['rows'])];assert max(gaps)<.01
     for j,row in enumerate(q['rows']):assert row['unique_tiles']==old[anchor+j-1]['visited'] and row['collision']==old[anchor+j-1]['collision'] and abs(row['damage']-old[anchor+j-1]['damage'])<1e-6
     trials[name]['max_baseline_speed_match_error']=max(gaps)
   gain=trials['positive_unclamped']['end_speed_m_s']-trials['baseline']['end_speed_m_s'];results.append(dict(anchor=anchor,group={13:'unused positive acceleration',54:'braking despite positive lag',165:'full gas actuator ceiling',167:'braking despite positive lag'}[anchor],trials=trials,end_speed_gain_m_s=gain));save(D/'probe-results.json',results);save(D/'model-cost-progress.json',dict(queries=queries,physics_ticks=mticks));print(json.dumps(dict(anchor=anchor,end_speed_gain=gain,baseline_match=trials['baseline']['max_baseline_speed_match_error'])),flush=True)
  assert results[0]['end_speed_gain_m_s']>0 and not results[0]['trials']['positive_unclamped']['collision'] and results[0]['trials']['positive_unclamped']['all_wheels_road'];save(D/'candidate-gate.json',dict(passed=True,reason='Matched source13 three-action positive-clamp removal increases speed without contact/road loss. This is local availability evidence, not full-lap safety.',single_change='Remove upper scalar acceleration clamp only; retain brake lower bound, inverse pedal law,0..1 actions,source gas slew/friction, globalpath/pace1.5/steering.',no_new_gain=True))
 except Exception as e:error=type(e).__name__+': '+str(e)
 finally:
  if env:env.close()
 save(D/'diagnostic-outcome.json',dict(technical_error=error,results=results,model_queries=queries,model_physics_ticks=mticks,budget=json.loads((D/'budget.json').read_text()),wall_s=time.time()-json.loads((D/'diagnostic-opening.json').read_text())['epoch']))

if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--stage-dir',type=Path,required=True);run(a.parse_args().stage_dir.resolve())
