"""Aggregate stored402actual transitions; never create a dynamics world."""
import json,time
from pathlib import Path
import numpy as np

def run(root):
 d=root/'stage402';p=json.loads((d/'analysis-plan.json').read_text());assert not(d/'analysis.json').exists();start,cpu=time.perf_counter(),time.process_time();out=[]
 for arm in ['P15_C','P10_C']:
  rows=[json.loads(l) for l in (d/arm/'trace-private.jsonl').read_text().splitlines()]
  def aggregate(rr):
   v=[r['pre']['speed'] for r in rr];target=[r['reference']['r'] for r in rr if 'r' in r['reference']];result=dict(actions=len(rr),median_actual_speed_m_s=float(np.median(v)),median_target_speed_m_s=float(np.median(target)),gas_actions=sum(r['command'][1]>0 for r in rr),brake_actions=sum(r['command'][2]>0 for r in rr),collision_actions=sum(r['collision'] for r in rr),raw_grass_samples=sum(s['grass'] for r in rr for s in r['raw_tire_samples']),all_wheels_onroad=all(all(n>0 for n in r['post']['road_contacts']) for r in rr))
   for label,inds in [('front',[0,1]),('rear',[2,3])]:
    ss=[s for r in rr for s in r['raw_tire_samples'] if s['wheel'] in inds];result[label]=dict(samples=len(ss),clipped=sum(s['clipped'] for s in ss),max_force_ratio=max(s['force_ratio'] for s in ss))
   return result
  x=dict(arm=arm,whole=aggregate(rows))
  if arm=='P10_C':x['through_model_gate']=aggregate(rows[:106]);x['after_model_gate']=aggregate(rows[106:]);final=json.loads((d/arm/'final-full-private.json').read_text());start_t=rows[0]['pre']['time'];x['finish']=dict(official_lap_s=final['wrapper']['finish_time_s']-start_t,forwardedge_clearance_episode_s=rows[-1]['post']['time']-start_t,terminal_action_raw_ticks=rows[-1]['raw_ticks'],qualified=final['wrapper']['finish_qualified_time_s'] is not None,official_center_timestamp_present=final['wrapper']['finish_time_s'] is not None)
  out.append(x)
 result=dict(cases=out,new_native_actor_model_learning_SEALED=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start);p=d/'analysis.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n');p.chmod(0o600);print(json.dumps(result,ensure_ascii=False))
if __name__=='__main__':run(Path(__import__('sys').argv[1]))
