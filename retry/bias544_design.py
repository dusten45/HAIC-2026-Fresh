"""One deterministic counter-bias reference; no solver, no geometry/performance sweep."""
import datetime,hashlib,json,math,signal,time,traceback
from pathlib import Path
import numpy as np
from retry.lap518_control import project,point_at
from retry.line530_control import rebuild
from retry.profile539_profile import rebuild_profile
from retry.feasible531_geometry import Geometry,shape,KMAX
from retry.line530_design import frames

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response544-private');read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=read(G/'retry/bias544_contract.json');cost={};error=None;out={}
 def guard(*a):
  if time.process_time()-cpu>=30 or time.perf_counter()-wall>=60:raise RuntimeError('DESIGN_COST_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
 signal.signal(signal.SIGPROF,guard);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,60)
 assert all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items())
 with (D/'DESIGN_STARTED.json').open('x') as f:json.dump(dict(contract_sha256=sha(G/'retry/bias544_contract.json')),f)
 try:
  static=read(Path('/workspace/haic-response515-private/collected-map-state-private.json'));old=read(Path('/workspace/haic-response541-private/frozen-paths-private.json'));high=old['candidate'];low=old['backup'];e=read(D/'bias-evidence-private.json');entry=read(D/'entry-root-private.json');actual=e['all_candidate_actual_rows'];start=project(entry['root']['center'],high,None)['s'];start=start+high['length'] if start<0 else start;endrow=next(r for r in reversed(actual) if r['action']==87);end=endrow['station'];peak=e['station'];assert 0<start<peak<end<high['length'];arcs=np.array(high['arcs'][:-1]);points=np.array(high['points']);normal=frames(points)[1];weights=np.zeros(len(points))
  def smooth(t):return t**3*(10+t*(-15+6*t))
  for j,s in enumerate(arcs):
   if start<s<=peak:weights[j]=smooth((s-start)/(peak-start))
   elif peak<s<end:weights[j]=smooth((end-s)/(end-peak))
  candidate=points-e['normal_error']*weights[:,None]*normal
  center=np.array([(p[2],p[3]) for p in static['track']]);roadnormal=frames(center)[1];offset=((candidate-center)*roadnormal).sum(axis=1);ds,kap=shape(candidate);geo=Geometry(static,center);geo.sample_cap=50000;baseline_min=float(np.min(geo.evaluate(points)));guard();candidate_min=float(np.min(geo.evaluate(candidate)));cost=dict(geometry_calls=geo.calls,geometry_segment_samples=geo.segment_samples)
  reasons=[]
  if candidate_min<1.252:reasons.append('STATIC_OUTERBOX_1_252')
  if max(abs(offset))>4.+1e-10:reasons.append('ORIGINAL_OFFSET_DOMAIN_4M')
  if min(ds)<2.:reasons.append('MIN_SEGMENT_2M')
  if max(abs(kap))>KMAX:reasons.append('ORIGINAL_STEERING_CURVATURE_DOMAIN')
  n=rebuild(candidate,static);primary=rebuild_profile(n,.70*sum(w['friction'] for w in static['root']['planar']['linear']['wheels'])/static['root']['planar']['linear']['mass'],90.);backup=rebuild(candidate,static,backup=True);new=dict(baseline=high,baseline_backup=low,candidate=primary,backup=backup);gate_s=end+max(7.,.3*endrow['speed']);gate_point=point_at(gate_s,high);j=min(len(high['ds'])-1,next(i for i,z in enumerate(high['arcs'][1:]) if z>=gate_s));v=np.array(high['points'][(j+1)%len(points)])-np.array(high['points'][j]);tangent=(v/np.linalg.norm(v)).tolist();gate=dict(point=gate_point,tangent=tangent,reference_station=gate_s,reference_curvature=high['curvature'][j],support_start=start,support_peak=peak,support_end=end)
  for name,value in [('frozen-paths-private.json',new),('common-gate-private.json',gate),('shape-private.json',dict(points=candidate.tolist(),weights=weights.tolist(),normal_error=e['normal_error']))]:
   p=D/name
   with p.open('x') as f:json.dump(value,f)
   p.chmod(0o600)
  out=dict(passed=not reasons,reason=reasons,baseline_static_minimum_m=baseline_min,candidate_static_minimum_m=candidate_min,max_original_normal_offset_m=float(max(abs(offset))),minimum_segment_m=float(min(ds)),maximum_abs_curvature_1_m=float(max(abs(kap))),counter_bias_amplitude_m=-e['normal_error'],unchanged_outside_support=bool(np.array_equal(points[weights==0],candidate[weights==0])),frozen_paths_sha256=sha(D/'frozen-paths-private.json'),new_model_ticks=0,new_native_actions=0)
 except BaseException as exc:
  error=type(exc).__name__+':'+str(exc);out=dict(passed=False,technical_error=error,new_model_ticks=0,new_native_actions=0)
  with (D/'design-error-private.json').open('x') as f:json.dump(dict(error=error,traceback=traceback.format_exc(),cost=cost),f)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);out.update(cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,research_remaining=22758,reserve=84000,reserve_used=0)
  with (G/'retry/bias544_design_result.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
  print(json.dumps(out,indent=2))
if __name__=='__main__':run()
