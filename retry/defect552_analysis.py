"""Saved541/551 whole-lap mechanism analysis; force algebra only, no integrator."""
import bisect,collections,datetime,hashlib,json,math,signal,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.plan513_model import load_root
from retry.drive519_control import force_rows,steering,reference
from retry.structure537_control import ADMISSION
from retry.retime549_design import clock
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response552-private')

def stats(a):
 z=np.asarray(a,float);return dict(n=len(z),min=float(min(z)) if len(z) else None,p05=float(np.quantile(z,.05)) if len(z) else None,median=float(np.median(z)) if len(z) else None,p95=float(np.quantile(z,.95)) if len(z) else None,max=float(max(z)) if len(z) else None)

def run():
 cpu=time.process_time();wall=time.perf_counter();rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();D.mkdir(mode=0o700,exist_ok=False);cost=dict(force_evaluations=0,model_ticks=0);sourcefiles=['retry/defect552_analysis.py','retry/speed516_control.py','retry/brake502_response.py','retry/brake504_planar.py','retry/lap518_control.py','retry/structure537_control.py'];inputs=[Path('/workspace/haic-response515-private/collected-map-state-private.json'),Path('/workspace/haic-response549-private/curvature-force-design-private.json'),Path('/workspace/haic-response551-private/frozen-paths-private.json'),Path('/workspace/haic-response541-private/cold-candidate-private.json'),Path('/workspace/haic-response551-private/cold-candidate-private.json')]
 def save(p,x):
  with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False)
  p.chmod(0o600 if D in p.parents else 0o644)
 c=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',scope='Read full saved541/551. Force algebra at actual before-hold states using same537 finite pedal grid; no propagated state/model tick, no candidate. Instantaneous grid-feasible derivative range is NOT a multi-tick reachability certificate.',caps={'CPU_s':60,'wall_s':90,'force_evaluations':100000,'model_ticks':0},source_sha256={p:sha(G/p) for p in sourcefiles},private_inputs_sha256={str(p):sha(p) for p in inputs})
 save(G/'retry/defect552_analysis_contract.json',c);save(D/'analysis-STARTED.json',dict(contract_sha256=sha(G/'retry/defect552_analysis_contract.json')))
 def guard(*a):
  if time.process_time()-cpu>=60 or time.perf_counter()-wall>=90 or cost['force_evaluations']>=100000:raise RuntimeError('ANALYSIS_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
 signal.signal(signal.SIGPROF,guard);signal.setitimer(signal.ITIMER_PROF,60);signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,90);out={}
 try:
  static=rd(inputs[0]);design=rd(inputs[1]);paths=rd(inputs[2]);private={};public=[];refs=[]
  lock=np.float32(.9)
  if lock<.9:lock=np.nextafter(lock,np.float32(1.))
  pedals=sorted(set([float(np.float32(-1+i/8)) for i in range(17)]+[-float(lock),-float(np.nextafter(lock,np.float32(0.)))]));n=len(paths['candidate']['ds'])
  for arm,p in [('baseline541',inputs[3]),('candidate551',inputs[4])]:
   data=rd(p);path=paths['baseline'] if arm=='baseline541' else paths['candidate'];trace=data['trace'];previous=static['root'];byhold={};history=[0,0];near=[];nc=[];ranges=[];laterr=[];torques=[];allrecords=[];reasons=collections.Counter();refonly=[]
   commands={r['index']:r for r in data['commands']}
   for j,row in enumerate(trace):
    guard();idx=row['index'];v=row['root_without_roads']['planar']['linear']['velocity'];speed=math.hypot(*v);over=speed-row['target'];peak=max(f['ratio'] for f in row['forces'])
    if idx>24:
     if over>=4:near.append(peak)
     if over>=4 and row['target']<89.999:nc.append(peak)
     p0=previous['planar'];i=min(n-1,bisect.bisect_left(path['arcs'][1:],row['progress']));coeff=[design['body_mass']*w/2 for w in design['axle_load_fractions']];K=design['segment_curvature'][i];normal=[coeff[k//2]*speed**2*K for k in range(4)];actual=[]
     for w,f in zip(p0['linear']['wheels'],row['forces']):
      side=(math.cos(w['heading']),math.sin(w['heading']));actual.append(abs(sum(side[t]*f['vector'][t] for t in range(2))))
     laterr.append(max(abs(a-b) for a,b in zip(actual,normal)));torques.append(abs(sum(r[0]*f['vector'][1]-r[1]*f['vector'][0] for r,f in zip(p0['levers'],row['forces']))))
     if row['raw']==1:
      before=previous;root=load_root(dict(before,roads=static['root']['roads']));root=replace(root,planar=replace(root.planar,steer=-float(row['action'][0])));vs=root.planar.linear.velocity;sv=math.hypot(*vs);feasible=[]
      for u in pedals:
       action=np.array([row['action'][0],max(0.,u),max(0.,-u)],np.float32);fs=force_rows(root,action);cost['force_evaluations']+=4;ratio=max(f['ratio'] for f in fs);a=sum(sum(f['vector'][t]*vs[t]/max(sv,1.) for t in range(2)) for f in fs)/root.planar.linear.mass
       if ratio<=ADMISSION:feasible.append(dict(u=u,instant_accel_m_s2=a,force_peak=ratio))
      if feasible:
       rec=dict(index=idx,root=before,progress=trace[j-1]['progress'],history=history.copy(),speed=sv,instant_min_accel=min(z['instant_accel_m_s2'] for z in feasible),instant_max_accel=max(z['instant_accel_m_s2'] for z in feasible),instant_feasible_pedals=feasible);ranges.append(rec['instant_max_accel']-rec['instant_min_accel']);allrecords.append(rec)
      command=commands[idx];high=next((r for r in command['detail'].get('reports',[]) if r['mode']=='HIGH'),None)
      if high and not high['ok']:
       reasons[high['reason']]+=1
       if high['reason']=='REFERENCE_WITH_NUMERIC_RESERVE':
        rr=dict(index=idx,first_hold_pass=high['first_hold_pass'],force_peak=high['peak'],min_margin=high['min_footprint_margin_m'],reported_overspeed=high['max_reference_overspeed'],ticks_to_ref_veto=high['model_ticks'],first_hold=high['first_hold']);refonly.append(rr)
        if arm=='candidate551':refs.append(dict(**rr,root=before,progress=trace[j-1]['progress'],history=history.copy(),baseline_command=command['action']))
     history[0]+=sum(f['clipped'] for f in row['forces']);history[1]+=4
    previous=row['root_without_roads']
   private[arm]=dict(full_before_hold_ranges=allrecords,reference_only=refonly);public.append(dict(arm=arm,near_ref_seconds=.02*len(near),near_ref_low_force_seconds=.02*sum(p<.7 for p in near),noncap_near_ref_seconds=.02*len(nc),noncap_near_ref_low_force_seconds=.02*sum(p<.7 for p in nc),high_rejection_reasons=dict(reasons),reference_rejections_low_force=sum(z['force_peak']<.7 for z in refonly),reference_rejections_before_first_hold=sum(not z['first_hold_pass'] for z in refonly),normal_vs_actual_max_wheel_lateral_force_error_N=stats(laterr),absolute_source_yaw_torque=stats(torques),instantaneous_grid_feasible_acceleration_range_width_m_s2=stats(ranges),finite_grid_only=True))
  # ONE root rule set before any propagation: source551 reference-only veto with minimum observed peak force, ties earliest. A diagnostic, not candidate selection.
  selected=min(refs,key=lambda r:(r['force_peak'],r['index']));save(D/'analysis-detail-private.json',private);save(D/'selected-root-private.json',selected);out=dict(passed=True,cases=public,selected_root_index=selected['index'],selected_partial_HIGH_peak_force=selected['force_peak'],selected_first_hold_pass=selected['first_hold_pass'],selected_ticks_to_ref_veto=selected['ticks_to_ref_veto'],selected_partial_margin_m=selected['min_margin'],selected_root_sha256=sha(D/'selected-root-private.json'),reference_clock_old_s=clock(paths['baseline']),reference_clock551_s=clock(paths['candidate']),surrogate_gain_s=clock(paths['baseline'])-clock(paths['candidate']),observed_source_gain_s=.44,surrogate_not_actual_bound=True,no_new_candidate=True)
 except BaseException as exc:out=dict(passed=False,error=type(exc).__name__+':'+str(exc));save(D/'analysis-error-private.json',dict(error=out['error'],traceback=traceback.format_exc()))
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);out.update(cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_native_actions=0,new_seeds=0,protected_queries=0,research_remaining=22758,reserve=84000,reserve_used=0);save(G/'retry/defect552_analysis.json',out);print(json.dumps(out,indent=2))
if __name__=='__main__':run()
