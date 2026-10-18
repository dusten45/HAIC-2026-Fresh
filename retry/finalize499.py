"""Saved499 derived-record summaries only; no raw copies, control or simulation."""
import time
START=time.perf_counter()
import hashlib,json,os,math
from pathlib import Path
G=Path(__file__).resolve().parents[1];R=Path('/workspace/haic-private-retry-20261009');D=R/'stage499/qualified-analysis-private'
def run():
 r=json.loads((D/'result-private.json').read_text());raw=json.loads((D/'raw-derived-private.json').read_text())['raw'];N=12;L=r['canonical_line_length_m']
 for i,b in enumerate(r['bins']):
  selected=[x for x in raw if min(N-1,max(0,int(x['progress0']/L*N)))==i]
  b.update(raw_count=len(selected),clipped_wheel_samples=sum(x['clipped'] for x in selected),wheel_samples=sum(x['tires'] for x in selected),raw_count_assignment='raw interval starting arc; time is apportioned across boundaries')
 assert sum(x['clipped_wheel_samples'] for x in r['bins'])==r['global_metrics']['clipped_wheel_samples']
 assert sum(x['wheel_samples'] for x in r['bins'])==r['global_metrics']['wheel_samples']
 body={k:sum(x['dt'] for x in raw if pred(x)) for k,pred in [('accelerating_gt1_m_s2',lambda x:x['accel']>1),('decelerating_ltminus1_m_s2',lambda x:x['accel']< -1),('approximately_constant_abs_le1',lambda x:abs(x['accel'])<=1)]};r['body_acceleration_time_s']=body
 r['reference_ceiling_caution']={'observed_max_speed_m_s':r['global_metrics']['max_speed_m_s'],'time_active_reference_over100_s':sum(x['dt'] for x in raw if x['ref']>100),'time_speed_ge99_s':sum(x['dt'] for x in raw if x['speed']>=99),'interpretation':'Observed plateau near100; references above it do not imply recoverable tracking loss. No hard physics cap inferred solely from these samples.'}
 episodes=[];cur=[]
 for x in raw+[{'mode':'end'}]:
  if x['mode']=='brake':cur.append(x)
  elif cur:
   first,last=cur[0],cur[-1];finish=last['t']+last['dt'];recovered=next((q for q in raw if q['t']>=finish and q['speed_post']>=first['speed']),None)
   episodes.append(dict(start_episode_s=first['t'],end_episode_s=finish,duration_s=sum(q['dt'] for q in cur),arc_fraction_start=first['progress0']/L,speed_before_m_s=first['speed'],speed_after_m_s=last['speed_post'],speed_drop_m_s=first['speed']-last['speed_post'],duration_until_regain_entry_speed_s=None if recovered is None else recovered['t']+recovered['dt']-first['t'],clipped_wheel_samples=sum(q['clipped'] for q in cur),max_force_ratio=max(q['force_ratio'] for q in cur),max_raw_guard_error_m=max(q['error'] for q in cur),below_current_and_future40_by5_s=sum(q['dt'] for q in cur if q['speed']<min(q['ref'],q['future40_ref_min'])-5)));cur=[]
 r['braking_episodes']=episodes
 r['time_scale_decomposition']={'measured_target_gap_s':r['gap_s'],'best_prefix_time_s':r['phases']['prefix1_125']['time_s'],'best_suffix_time_s':r['phases']['P4suffix126_171']['time_s'],'hypothetical_P4_prefix_clock_s':r['reference_clocks']['P4_full_s']-r['reference_clocks']['P4_suffix_clock_s'],'prefix_minus_hypothetical_P4_s':r['phases']['prefix1_125']['time_s']-(r['reference_clocks']['P4_full_s']-r['reference_clocks']['P4_suffix_clock_s']),'suffix_minus_hypothetical_P4_s':r['phases']['P4suffix126_171']['time_s']-r['reference_clocks']['P4_suffix_clock_s'],'P4_clock_minus11_99_s':r['reference_clocks']['P4_full_s']-11.99,'measured_bin5_8_time_s':sum(b['time_s'] for b in r['bins'][4:8]),'bin5_8_minus_hypothetical_P4_clock_s':sum(b['observed_minus_P4_clock_s'] for b in r['bins'][4:8]),'launch_idealized40_at_model_rear_accel_s':40/35.0188778925416,'interpretation':'Reference and constant-acceleration arithmetic are hypothetical scales, not realizable savings, optimality bounds or participant comparisons.'}
 r['cost_accounting']={'main_worker_CPU_s':r['CPU_s'],'main_worker_wall_s':r['wall_s'],'supplement_CPU_s':time.process_time(),'supplement_wall_s':time.perf_counter()-START,'conservative_other_preparation_failure_and_closure_allowance_CPU_s':10,'conservative_other_preparation_failure_and_closure_allowance_wall_s':20,'cap_CPU_s':120,'cap_wall_s':180}
 r['new_derived_bytes_before_finalization']=sum(p.stat().st_size for p in (R/'stage499').rglob('*') if p.is_file())
 r['input_authentication_scope']='472 trace matches prior full raw retention manifest SHA; frozen reference inputs and selected historical traces match472 registered source pins where present. Other paired trace hashes pinned at499 first read, exact paired-prefix and baseline-bridge bytes verified. No new whole archive audit.'
 r['event_confirmation_boundary']='All stored raw ticks validated through confirmation; duration/geometry metrics stop at official event.458P and463Original confirmation-only tick is excluded from episode time, not erased from source.'
 data=(json.dumps(r,ensure_ascii=False,indent=2)+'\n').encode();assert len(data)<4*1024**2 and r['new_derived_bytes_before_finalization']+len(data)<16*1024**2
 p=G/'retry/diagnostic499_result.json';p.write_bytes(data)
 private=R/'stage499/final-derived-summary-private.json';assert not private.exists();private.write_bytes(data);private.chmod(0o600)
 print(json.dumps({'body_acceleration_time_s':body,'braking_episodes':episodes,'time_scale_decomposition':r['time_scale_decomposition'],'cost':r['cost_accounting'],'private_bytes':r['new_derived_bytes_before_finalization']},ensure_ascii=False))
if __name__=='__main__':run()
