"""Saved404 lead-time and common-position diagnosis only; no model import."""
import datetime,hashlib,json,math,sys,time,signal
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 assert not p.exists(),p
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
def prepare(root):
 d=root/'stage405';assert not d.exists();d.mkdir(mode=0o700);fixed=Path(read(root/'stage404/plan.json')['fixed_plan']);files=[Path(__file__),fixed,root/'stage404/plan.json',root/'stage404/result.json',root/'stage404/prefix-analysis.json',root/'stage404/profiles-private.json',root/'stage404/O_268/trace-private.jsonl',root/'stage404/C_268/trace-private.jsonl',root/'stage404/O_268/initial-private.json',root/'stage404/C_268/initial-private.json',root/'stage402/P10_C/trace-private.jsonl',root/'stage402/P10_C/initial-private.json',root/'stage401/P15_J-rows-private.json',root/'stage401/P10_J-rows-private.json',root/'project-effective-budget-v424.json',root/'research-deadline-current.json']+[G/f for f in ['core/vendor/car_dynamics.py','retry/source_vehicle_transition.py','retry/factorial401_run.py','retry/cross404_common.py','retry/cross404_run.py','retry/loss403_result.md','retry/contact_timing191_result.md','retry/receding_horizon192_result.md','retry/matched251_result.md','retry/pace267_result.md','retry/pace268_result.md','retry/intervention327_result.md','retry/hybrid328_result.md','retry/h1_330_result.md']]
 p=dict(stage=405,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),CPU_cap_s=60,wall_cap_s=120,new_wrapper_cap=0,actor_cap=0,model_tick_cap=0,learning_cap=0,SEALED_cap=0,new_paid_cap=0,scope='Retrospectivedescriptiveleadtime/commonarc, not onlineclassifier/effectidentification. No dynamics/control candidateevaluation orfit.',arc='Subtracteachtraceinitialunwrappedgauge, shortperiodicpre/postdelta. Common0..Cfailurearc;last120m splitfixed10m prearc bins. Wholeactionwithinbin stats include endpoints thatmayleavebin; neverinterpolatepositions/times.',events='First rear any/allvectorclip(q>1),any/alllateralraw>400, any q>2 fromexisting source skiddingbranch, endrunfullrearclip, postnearesterror>1/2/3. Availabletime is POSTaction forraw/postsignals. Report O occurrences beforeCcommonarc too;notcalibratedfalsealarmrate. Yaw/lat slipcontinuous no fittedthreshold.',anchors='H13alreadyfixed403, Cpre(lastCstep-12)=91, O firstprearc>=C91prearc(no interpolation), reset402Cbase. Selection usesknownfailureOFFLINEonly;notfutureactualpolicyinput. Show currentinputs,and13actualCpaththroughfailure;alignedO13ifavailable.',decel='Actualbrake/request/gas andnorm-speeddeceleration; remainingtimes/distancesfromobservedCfailure. Nonclippinglateralreserve notbodybrakingguarantee. No minimumavoidablehorizonclaim.',sources={str(f):sha(f) for f in files},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']})
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');print('405 lead-time/common-position stored-data audit registered')
def run(root):
 d=root/'stage405';p=read(d/'plan.json');assert not(d/'result.json').exists()
 for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
 start,cpu=time.perf_counter(),time.process_time();fixed=read(Path(read(root/'stage404/plan.json')['fixed_plan']));L=sum(fixed['free_profile']['ds']);data={}
 def deadline(*args):raise TimeoutError('405CPU60')
 previous=signal.signal(signal.SIGPROF,deadline);signal.setitimer(signal.ITIMER_PROF,60)
 for key in ['O','C']:
  rows=[json.loads(s) for s in (root/f'stage404/{key}_268/trace-private.jsonl').read_text().splitlines()];origin=rows[0]['reference']['measured_unwrapped_arc'];out=[];t0=rows[0]['pre']['time']
  for r in rows:
   a=r['reference']['measured_unwrapped_arc']-origin;post=a+(r['post_projection']['arc']-r['reference']['projection']['arc']+L/2)%L-L/2;ss=[s for s in r['raw_tire_samples'] if s['wheel']>=2];assert all(not s['grass'] for s in ss);dt=r['post']['time']-r['pre']['time'];out.append(dict(raw=r,step=r['step'],pre_arc=a,post_arc=post,pre_t=r['pre']['time']-t0,post_t=r['post']['time']-t0,pre_yaw=abs(r['pre']['yaw']),post_yaw=abs(r['post']['yaw']),pre_error=r['reference']['projection']['path_error_m'],post_error=r['post_projection']['path_error_m'],pre_speed=r['pre']['speed'],post_speed=r['post']['speed'],norm_accel=(r['post']['speed']-r['pre']['speed'])/dt,gas=r['command'][1],brake=r['command'][2],rear_clip=sum(s['clipped'] for s in ss),rear_all_clip=all(s['clipped'] for s in ss),rear_any_clip=any(s['clipped'] for s in ss),rear_lat_over=sum(abs(s['raw_lat_N'])>400 for s in ss),rear_all_lat=all(abs(s['raw_lat_N'])>400 for s in ss),rear_any_lat=any(abs(s['raw_lat_N'])>400 for s in ss),rear_twice=any(s['force_ratio']>2 for s in ss),rear_max_ratio=max(s['force_ratio'] for s in ss),rear_max_abs_lat_slip=max(abs(s['lateral_slip_m_s']) for s in ss)))
  data[key]=out
 c=data['C'];end=c[-1]['post_t'];s_end=c[-1]['post_arc'];events=[]
 predicates=[('rear_any_vector_clip',lambda a:a['rear_any_clip']),('rear_all_vector_clip',lambda a:a['rear_all_clip']),('rear_any_lateral_alone_over400',lambda a:a['rear_any_lat']),('rear_all_lateral_alone_over400',lambda a:a['rear_all_lat']),('rear_any_vector_ratio_over2',lambda a:a['rear_twice']),('path_error_over1',lambda a:a['post_error']>1),('path_error_over2',lambda a:a['post_error']>2),('path_error_over3',lambda a:a['post_error']>3)]
 for name,fn in predicates:
  for key in ['C','O']:
   rr=[a for a in data[key] if a['pre_arc']<s_end];hit=next((a for a in rr if fn(a)),None);events.append(dict(event=name,arm=key,first_action=hit['step'] if hit else None,available_post_time_s=hit['post_t'] if hit else None,C_time_to_failure_after_signal_s=end-hit['post_t'] if hit and key=='C' else None,C_distance_to_failure_after_signal_m=s_end-hit['post_arc'] if hit and key=='C' else None,occurrences_in_common_prefix=sum(fn(a) for a in rr),denominator_actions=len(rr)))
 runstart=len(c)-1
 while runstart>0 and c[runstart-1]['rear_all_clip']:runstart-=1
 lastbrake=next((a for a in reversed(c) if a['brake']>0),None)
 def summary(rr):
  if not rr:return dict(actions=0)
  return dict(actions=len(rr),pre_yaw_range=[min(a['pre_yaw'] for a in rr),max(a['pre_yaw'] for a in rr)],post_yaw_range=[min(a['post_yaw'] for a in rr),max(a['post_yaw'] for a in rr)],pre_speed_range=[min(a['pre_speed'] for a in rr),max(a['pre_speed'] for a in rr)],max_post_error=max(a['post_error'] for a in rr),rear_all_clip_actions=sum(a['rear_all_clip'] for a in rr),rear_lat_over_samples=sum(a['rear_lat_over'] for a in rr),rear_max_ratio=max(a['rear_max_ratio'] for a in rr),rear_max_abs_lateral_slip=max(a['rear_max_abs_lat_slip'] for a in rr),gas_actions=sum(a['gas']>0 for a in rr),brake_actions=sum(a['brake']>0 for a in rr),norm_accel_range=[min(a['norm_accel'] for a in rr),max(a['norm_accel'] for a in rr)])
 bins=[]
 for i in range(12):
  lo,hi=s_end-120+i*10,s_end-120+(i+1)*10;bins.append(dict(distance_before_failure_m=[s_end-hi,s_end-lo],C=summary([a for a in c if lo<=a['pre_arc']<hi]),O=summary([a for a in data['O'] if lo<=a['pre_arc']<hi])))
 thresholds=[]
 for distance in [120,80,40,20]:
  arc=s_end-distance;pair=[]
  for key in ['C','O']:
   hit=next((a for a in data[key] if a['pre_arc']<arc<=a['post_arc']),None)
   pair.append(dict(arm=key,action=hit['step'],time_interval_s=[hit['pre_t'],hit['post_t']],C_remaining_time_interval_s=[end-hit['post_t'],end-hit['pre_t']] if key=='C' else None,current_window=summary([hit])))
  thresholds.append(dict(distance_before_failure_m=distance,pair=pair))
 anchor=c[-13];Oanchor=next(a for a in data['O'] if a['pre_arc']>=anchor['pre_arc']);anchors=[]
 for key,a in [('C',anchor),('O',Oanchor)]:
  win=data[key][a['step']-1:a['step']+12];anchors.append(dict(arm=key,step=a['step'],pre_time_s=a['pre_t'],arc_offset_from_C_anchor_m=a['pre_arc']-anchor['pre_arc'],pre_yaw_rad_s=a['pre_yaw'],pre_path_error_m=a['pre_error'],pre_speed_m_s=a['pre_speed'],actual_13step_window=summary(win),C_failure_horizon_s=end-a['pre_t'] if key=='C' else None))
 rawfields=['rear_all_clip','rear_lat_over','rear_max_ratio','pre_yaw','post_error','brake','norm_accel']
 rows_summary=[{k:a[k] for k in ['step','pre_t','post_t','pre_arc','post_arc',*rawfields]} for a in c[-20:]]
 result=dict(stage=405,events=events,last_continuous_rear_all_clip=dict(first_action=c[runstart]['step'],available_post_time_s=c[runstart]['post_t'],lead_to_failure_s=end-c[runstart]['post_t'],length_actions=len(c)-runstart),last_brake=dict(action=lastbrake['step'],post_time_s=lastbrake['post_t'],lead_to_failure_s=end-lastbrake['post_t'],norm_accel=lastbrake['norm_accel']) if lastbrake else None,common_last120m_bins=bins,position_thresholds=thresholds,anchors=anchors,C_last20_diagnostic=rows_summary,new_wrapper_actions=0,new_actor_calls=0,new_model_integration_ticks=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,scope='Signalsavailablepostaction; leadtimesareknownCtrajectorydescriptive,notminimumrecoveryhorizon;matchedpositionbinsnotmatchedphysicalstate;horizon13notoptimized.')
 signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,previous);assert result['CPU_s']<60 and result['wall_s']<120;save(d/'result.json',result);print(json.dumps(dict(stage=405,events=events,anchors=anchors,run=result['last_continuous_rear_all_clip'],last_brake=result['last_brake']),ensure_ascii=False))
if __name__=='__main__':
 root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
