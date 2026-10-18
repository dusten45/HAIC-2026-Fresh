"""Read-only552 stopping witness, physical distance and state-alignment audit."""
import bisect,hashlib,json,math,subprocess,time
from pathlib import Path
import numpy as np
from retry.plan513_model import load_root
from retry.lap518_finish import hull_pose
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response552-private')
def stats(a):
 a=np.asarray(a,float);return dict(n=len(a),median=float(np.median(a)),p95=float(np.quantile(a,.95)),max=float(max(a)))
def finite(x):
 if isinstance(x,float):return math.isfinite(x)
 if isinstance(x,list):return all(finite(z) for z in x)
 if isinstance(x,dict):return all(finite(z) for z in x.values())
 return True

def scalar_euler_stop(v,target,a=80.):
 distance=0.;steps=0
 while v>target:
  nxt=max(0.,v-.02*a);f=min(1.,(v-target)/(v-nxt));distance+=.02*nxt*f;v=nxt;steps+=1
  if steps>1000:raise RuntimeError('SCALAR_NO_STOP')
 return distance

def run():
 cpu=time.process_time();wall=time.perf_counter();rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=rd(G/'retry/defect552_probe_contract.json');r=rd(G/'retry/defect552_probe_result.json');data=rd(D/'braking-witness-private.json');entry=rd(D/'probe-input-private.json');static=rd(Path('/workspace/haic-response515-private/collected-map-state-private.json'));design=rd(Path('/workspace/haic-response549-private/curvature-force-design-private.json'));paths=rd(Path('/workspace/haic-response551-private/frozen-paths-private.json'));checks=dict(source_pins=all(sha(G/p)==h for p,h in c['source_sha256'].items()),private_input_pins=all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items()),finite=finite(data),raw_count=len(data['trace'])==r['executed_raw'],no_prefix_replay=data['trace'][0]['index']==entry['completed']+1 and data['trace'][0]['raw']==1,root_is_first_noncap_ref_veto=entry['completed']==25,original551_440ms_gate_preserved=not rd(G/'retry/whole551_cold_result.json')['passed'] and rd(G/'retry/whole551_cold_result.json')['gain_vs541_ms']==440)
 before=entry['root'];history=entry['history'].copy();initial=load_root(dict(before,roads=static['root']['roads']));minimum=margin(initial,static['roads'],bounds(static['roads']),static['boundary'],boundary_index(static['boundary']),static['obstacles']);peak=over=pathmax=bodymax=balance=0.;maxclip=history[0]/history[1];cross=None;arc=0.;arc_upper=None;v0=math.hypot(*before['planar']['linear']['velocity']);target=entry['target_speed'];stopindex=None
 for j,row in enumerate(data['trace']):
  after=row['root_without_roads'];p=before['planar'];pa=after['planar'];sv=math.hypot(*pa['linear']['velocity']);prevv=math.hypot(*p['linear']['velocity']);ds=math.dist(before['center'],after['center']);arc+=ds;minimum=min(minimum,row['margin']);peak=max(peak,max(f['ratio'] for f in row['forces']));over=max(over,sv-row['target']);pathmax=max(pathmax,row['path_error']);history[0]+=sum(f['clipped'] for f in row['forces']);history[1]+=4;maxclip=max(maxclip,history[0]/history[1]);root=load_root(dict(after,roads=static['root']['roads']));body=max(math.hypot(*hull_pose(root)[1]),*(math.hypot(*(root.planar.linear.velocity[t]+w.offset[t] for t in range(2))) for w in root.planar.linear.wheels));bodymax=max(bodymax,body);torque=sum(v[0]*f['vector'][1]-v[1]*f['vector'][0] for v,f in zip(p['levers'],row['forces']));M=p['angular_momentum']+.02*torque;yaw=(M-sum(I*q for I,q in zip(pa['wheel_inertias'],pa['rates'])))/pa['inertia'];balance=max(balance,abs(M-pa['angular_momentum']),abs(yaw-pa['yaw']))
  if cross is None and prevv>target>=sv:
   f=(prevv-target)/(prevv-sv);old_s=entry['progress'] if j==0 else data['trace'][j-1]['progress'];cross=dict(lower_time_s=.02*j,upper_time_s=.02*(j+1),interpolated_time_s=.02*(j+f),upper_progress_m=row['progress']-entry['progress']);arc_upper=arc;stopindex=j
  before=after
 d80=((v0-.15)**2-(target+.15)**2)/160;upper=cross['upper_progress_m']+.20;discrete=scalar_euler_stop(v0-.15,target+.15);com_upper=arc_upper+.20;checks['target_event_recomputed']=all(abs(cross[k]-r['source_stopping'][k])<1e-12 for k in cross);checks['surrogate_and_gate_recomputed']=abs(d80-r['constant80_lower_distance_m'])<1e-12 and abs(upper-r['source_stopping_distance_upper_with_error_m'])<1e-12 and r['passed']==(r['safe_source_stopping_witness'] and d80>upper);checks['absolute_bounds']=minimum>=.5 and peak<=1.059 and over<=4.85 and pathmax<=3 and bodymax<100 and maxclip<=.1;checks['metrics_match']=all(abs(a-b)<1e-12 for a,b in [(minimum,r['min_margin_m']),(peak,r['max_force_ratio']),(maxclip,r['max_cumulative_clipping'])]);checks['source_balance']=balance<1e-10;checks['all_model_body_checked']=r['cost']['model_body_checks']==r['model_ticks'] and r['cost']['max_all_model_body_speed_m_s']<100;checks['bounded_brake_calls']=all(x['detail']['source_calls']<=32 for x in data['commands']);checks['selected_FINALs']=all(next(z for z in x['detail']['reports'] if z['mode']=='FINAL')['ok'] for x in data['commands']);checks['fresh537_witness']=data['future_witness']['passed'] and not data['future_witness']['executed'];checks['same_source_time_discretization_still_positive']=com_upper<discrete
 lim=c['caps'];checks['caps']=r['model_ticks']<=lim['model_ticks'] and r['cost']['force_evaluations']<=lim['force'] and r['cost']['geometry_checks']<=lim['geometry'] and r['CPU_s']<=lim['CPU_s'] and r['wall_s']<=lim['wall_s'] and r['executed_holds']<=c['max_holds'];checks['actual0']=r['new_native_actions']==r['new_resets']==0;checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31';checks['no_deeper_execution']=not any((D/(p+'-STARTED.json')).exists() for p in ['cold','carry','native','actual'])
 # Preliminary552 lateral mismatch used after-step speed/station. Recompute on force BEFORE state and also show unclipped source lateral force.
 aligned=[]
 for arm,p in [('baseline541',Path('/workspace/haic-response541-private/cold-candidate-private.json')),('candidate551',Path('/workspace/haic-response551-private/cold-candidate-private.json'))]:
  old=rd(p);before=static['root'];before_s=0.;raw_errors=[];clipped_errors=[]
  for row in old['trace']:
   if row['index']>24:
    state=before['planar'];speed=math.hypot(*state['linear']['velocity']);i=min(len(paths['candidate']['ds'])-1,bisect.bisect_left(paths['candidate']['arcs'][1:],before_s));K=design['segment_curvature'][i];expected=[design['body_mass']*w/2*speed**2*K for w in design['axle_load_fractions'] for _ in range(2)];unclipped=[];applied=[]
    for w,f in zip(state['linear']['wheels'],row['forces']):
     side=(math.cos(w['heading']),math.sin(w['heading']));v=[state['linear']['velocity'][t]+w['offset'][t] for t in range(2)];unclipped.append(abs(82*sum(side[t]*v[t] for t in range(2))));applied.append(abs(sum(side[t]*f['vector'][t] for t in range(2))))
    raw_errors.append(max(abs(x-y) for x,y in zip(unclipped,expected)));clipped_errors.append(max(abs(x-y) for x,y in zip(applied,expected)))
   before=row['root_without_roads'];before_s=row['progress']
  aligned.append(dict(arm=arm,pre_force_state_aligned_unclipped_lateral_error_N=stats(raw_errors),pre_force_state_aligned_applied_lateral_error_N=stats(clipped_errors)))
 out=dict(passed=all(checks.values()),checks=checks,source_torque_yaw_balance_max_error=balance,source_COM_path_distance_to_first_below_target_upper_m=arc_upper,source_COM_distance_upper_with_guard_m=com_upper,source_compatible_scalar80_Euler_lower_distance_m=discrete,conservative_COM_vs_discrete80_advantage_m=discrete-com_upper,stopping_raw_index=stopindex+1,clipped_at_end=history[0],wheel_samples_at_end=history[1],preliminary_alignment_correction='Originalanalysis lateral mismatch used after-step speed/station for before-step forces. This read-only pre-force alignment supersedes those mismatch statistics only; original retained. Selection and stopping gate unchanged.',aligned_normal_force_mismatch=aligned,new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/defect552_audit.json').open('x') as f:json.dump(out,f,indent=2,allow_nan=False)
 print(json.dumps(out,indent=2));assert out['passed']
if __name__=='__main__':run()
