"""Read-only full-trace diagnosis of fresh404 and cached402; no new controls."""
import datetime,json,sys,time,hashlib
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha

def prepare(root):
 d=root/'stage404';assert read(d/'result.json')['shared_stop'] is None;paths=[Path(__file__),d/'plan.json',d/'qualification.json',d/'profiles-private.json',d/'result.json',root/'stage402/P10_C/trace-private.jsonl',root/'stage402/P10_C/result.json']
 for a in ['O_base','O_268','C_268']:paths += [d/a/'trace-private.jsonl',d/a/'result.json']
 p=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),CPU_cap_s=60,new_native_actor_model_learning_SEALED=0,scope='Descriptiveactualoutcome/profileclockgaps, clipping/road/damage; C268firstobservedsafetystopandfreshO268/cachedCbaseactionbracketscontainingthesameactualarc. No identicalstatecausalclaim; historicalrawforcesnotbackfilled.',metrics='Allfouroutcomes, onlycompletedtimecontrasts, no missingClapimputation. C last5,firstbadboundary,front/rearforces. Referencearc unwrap fromcurrentpre andpost shortestdelta; first bracketing fresh/cachedaction, boundedobservationsnotinterpolatedstates.',sources={str(f):sha(f) for f in paths})
 save(d/'analysis-plan.json',p);print('404 stored-trace diagnosis registered')
def run(root):
 d=root/'stage404';p=read(d/'analysis-plan.json');assert not(d/'analysis.json').exists()
 for f,h in p['sources'].items():assert sha(f)==h
 start,cpu=time.perf_counter(),time.process_time();fixed=read(Path(read(d/'plan.json')['fixed_plan']));L=sum(fixed['free_profile']['ds']);data={}
 for name in ['O_base','O_268','C_268']:
  data[name]=[json.loads(s) for s in (d/name/'trace-private.jsonl').read_text().splitlines()]
 data['C_base_cached402']=[json.loads(s) for s in (root/'stage402/P10_C/trace-private.jsonl').read_text().splitlines()]
 origins={id(r):rr[0]['reference'].get('measured_unwrapped_arc',rr[0]['reference'].get('actual_arc')) for rr in data.values() for r in rr}
 def group(rr,inds):
  ss=[s for r in rr for s in r['raw_tire_samples'] if s['wheel'] in inds];return dict(samples=len(ss),clipped=sum(s['clipped'] for s in ss),raw_lateral_alone_over400=sum(abs(s['raw_lat_N'])>400 for s in ss),max_vector_ratio=max(s['force_ratio'] for s in ss))
 def arcpair(r):
  a=r['reference'].get('measured_unwrapped_arc',r['reference'].get('actual_arc'))-origins[id(r)];q=r['reference']['projection']['arc'];b=a+(r['post_projection']['arc']-q+L/2)%L-L/2;return a,b
 def scalar(r,t0):
  return dict(step=r['step'],elapsed_interval_s=[r['pre']['time']-t0,r['post']['time']-t0],arc_interval_m=list(arcpair(r)),pre_speed_m_s=r['pre']['speed'],post_speed_m_s=r['post']['speed'],pre_yaw_rad_s=r['pre']['yaw'],post_yaw_rad_s=r['post']['yaw'],pre_error_m=r['reference']['projection']['path_error_m'],post_error_m=r['post_projection']['path_error_m'],r=r['reference'].get('r'),f=r['reference'].get('f'),raw_accel=r['reference'].get('raw_accel'),command_accel=r['reference'].get('command_accel'),command=r['command'],front=group([r],[0,1]),rear=group([r],[2,3]))
 summary=[]
 for name,rr in data.items():
  summary.append(dict(arm=name,actions=len(rr),front=group(rr,[0,1]),rear=group(rr,[2,3]),collision_actions=sum(r['collision'] for r in rr),raw_grass_samples=sum(s['grass'] for r in rr for s in r['raw_tire_samples']),all_wheels_onroad=all(all(x>0 for x in r['post']['road_contacts']) for r in rr),max_nearest_path_error=max(max(r['reference']['projection']['path_error_m'],r['post_projection']['path_error_m']) for r in rr),legacy_cursor_error_max=max(r.get('cursor',{}).get('path_error',0) for r in rr) if name.startswith('O_') else None))
 c=data['C_268'];failure=scalar(c[-1],c[0]['pre']['time']);target=arcpair(c[-1])[1];brackets=[]
 for name in ['O_268','C_base_cached402']:
  rr=data[name];matched=next((r for r in rr if arcpair(r)[0]<target<=arcpair(r)[1]),None);brackets.append(dict(arm=name,bracket=scalar(matched,rr[0]['pre']['time']) if matched else None))
 profiles=read(d/'qualification.json')['profile_clocks'];results=read(d/'result.json');times={r['arm']:r['lap_ms']/1000 if r['lap_ms'] is not None else None for r in results['results']};times['C_base_cached402']=results['cached_C_base']['lap_ms']/1000
 clocks=dict(base=profiles['base'],frozen268=profiles['268']);gaps={n:t-clocks['frozen268' if '268' in n else 'base'] if t is not None else None for n,t in times.items()}
 x=dict(stage=404,lap_times_s=times,ideal_reference_clocks_s=clocks,actual_minus_reference_s=gaps,completed_time_contrasts=dict(O_profile268_minus_base_s=times['O_268']-times['O_base'],Cbase_cached_minus_freshObase_s=times['C_base_cached402']-times['O_base']),numeric_time_interaction=None,reason_no_interaction='C268safetycensored,no lap, do notimpute',summaries=summary,C268_failure=failure,C268_last5=[scalar(r,c[0]['pre']['time']) for r in c[-5:]],same_actual_arc_brackets=brackets,new_native_actor_model_learning_SEALED=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start)
 assert x['CPU_s']<60;save(d/'analysis.json',x);print(json.dumps(dict(stage=404,times=times,clocks=clocks,gaps=gaps,failure=failure,brackets=brackets),ensure_ascii=False))
if __name__=='__main__':
 root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
