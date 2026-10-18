import json,math,time,signal,hashlib,bisect
from pathlib import Path
cpu=time.process_time();wall=time.perf_counter();signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,60);signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,120)
G=Path('/workspace/HAIC-2026-Fresh');D=Path('/workspace/haic-response536-private');O=Path('/workspace/haic-response537-private');read=lambda p:json.loads(Path(p).read_text())
p=read(D/'frozen-paths-private.json')['candidate'];static=read('/workspace/haic-response515-private/collected-map-state-private.json');A=.70*sum(w['friction'] for w in static['root']['planar']['linear']['wheels'])/static['root']['planar']['linear']['mass'];M=29.249793766661764;R=35.0188778925416
acts={read(f)['record']['index']:read(f) for f in D.glob('action-candidate-*.json')};raw=[read(f) for f in sorted(D.glob('raw-*.json'))];raw=raw[1022:];assert len(raw)==755 and raw[0]['phase']=='action' and raw[0]['action']==1

def ref(s):
 s=min(max(s,0.),p['length']);i=min(len(p['ds'])-1,bisect.bisect_left(p['arcs'],s)-1);i=max(i,0);f=(s-p['arcs'][i])/p['ds'][i];q=p['launch_squared'];return math.sqrt(max(0.,q[i]+f*(q[i+1]-q[i]))),(q[i+1]-q[i])/(2*p['ds'][i]),i

def integral(a,b):
 a=max(0.,min(p['length'],a));b=max(0.,min(p['length'],b));total=0.
 if b<a:return -integral(b,a)
 while a<b-1e-10:
  j=min(len(p['ds'])-1,bisect.bisect_right(p['arcs'],a)-1);end=min(b,p['arcs'][j+1]);va=ref(a)[0];vb=ref(end)[0];total+=2*(end-a)/max(1e-12,va+vb);a=end
 return total

def stats(rows):
 if not rows:return {'seconds':0.}
 return dict(seconds=.02*len(rows),mean_speed=sum(x['v'] for x in rows)/len(rows),mean_reference=sum(x['target'] for x in rows)/len(rows),mean_positive_speed_deficit=sum(max(0.,x['target']-x['v']) for x in rows)/len(rows),mean_force_peak=sum(x['force'] for x in rows)/len(rows),max_force_peak=max(x['force'] for x in rows),mean_abs_steering=sum(x['steer'] for x in rows)/len(rows),mean_path_error=sum(x['path_error'] for x in rows)/len(rows),min_margin=min(x['margin'] for x in rows),reference_time_account_s=sum(x['dt_account'] for x in rows),actual_minus_reference_time_account_s=sum(.02-x['dt_account'] for x in rows))
rows=[];previous=ref(0.)[0];s0=None
for q in raw:
 a=acts[q['action']];r=a['record'];v0=math.hypot(*q['before']['velocity']);v=q['speed'];target,ff,i=ref(q['station']);start_s=q['station'] if s0 is None else s0
 if s0 is None:
  # Initial s from first action before center projected using path segments, pure arithmetic.
  pos=a['before_root_without_roads']['center'];best=(1e99,0.)
  for j,(x,y) in enumerate(p['points']):
   b=p['points'][(j+1)%len(p['points'])];dx,dy=b[0]-x,b[1]-y;t=max(0.,min(1.,((pos[0]-x)*dx+(pos[1]-y)*dy)/(dx*dx+dy*dy)));d=math.hypot(pos[0]-x-t*dx,pos[1]-y-t*dy)
   if d<best[0]:best=(d,p['arcs'][j]+t*p['ds'][j])
  start_s=best[1];start_s=start_s if start_s<p['length']/2 else start_s-p['length']
 dtacc=integral(start_s,q['station']);s0=q['station'];force=max(z['ratio'] for z in q['forces']);bound=[]
 for j in (i,(i+1)%len(p['ds'])):
  z=p['periodic_squared'][j];prev=(j-1)%len(p['ds']);nxt=(j+1)%len(p['ds']);drv=min(R,80000/(M*(math.sqrt(p['periodic_squared'][prev])+2.7)))
  if abs(z-6400)<1e-5:bound.append('top80')
  if abs(z-A/max(abs(p['curvature'][j]),1e-8))<1e-4:bound.append('curvature')
  if abs(z-(p['periodic_squared'][prev]+2*drv*p['ds'][prev]))<1e-4:bound.append('source_forward')
  if abs(z-(p['periodic_squared'][nxt]+160*p['ds'][j]))<1e-4:bound.append('backward80')
 root=a['before_root_without_roads'];s_before=ref(start_s)[0];vel=root['planar']['linear']['velocity'];v_before=math.hypot(*vel);desired=ref(start_s)[1]+2*(s_before-v_before)
 rows.append(dict(desired_accel=desired,conventional_ceiling_active=desired>=R-1e-5,index=q['action'],v=v,target=target,ff=ff,force=force,steer=abs(r['action'][0]),gas=r['action'][1],brake=r['action'][2],path_error=q['path_error'],margin=q['margin'],mode=r['governor_mode'],binding=set(bound),dt_account=dtacc,s=q['station'],actual_accel=(v-v0)/.02,actual_lat=abs(v*q['yaw'])))
groups={}
for name,fn in [('conventional_ceiling',lambda x:x['index']>24 and x['conventional_ceiling_active']),('ceiling_with_force_slack',lambda x:x['index']>24 and x['conventional_ceiling_active'] and x['force']<.9),('fixed_launch',lambda x:x['index']<=24),('post_launch_HIGH',lambda x:x['index']>24 and x['mode']=='HIGH'),('governor',lambda x:x['index']>24 and x['mode']!='HIGH'),('positive_ff',lambda x:x['ff']>1),('negative_ff',lambda x:x['ff']< -1),('near_constant_ff',lambda x:abs(x['ff'])<=1),('actual_brake',lambda x:x['brake']>0),('actual_acceleration',lambda x:x['actual_accel']>1),('force_below_0_7',lambda x:x['force']<.7),('force_over_1',lambda x:x['force']>1),('under_reference_by_5',lambda x:x['target']-x['v']>5),('above_reference',lambda x:x['v']>x['target'])]:groups[name]=stats([x for x in rows if fn(x)])
for b in ('top80','curvature','source_forward','backward80'):groups['touches_'+b]=stats([x for x in rows if b in x['binding']])
q=p['launch_squared'];scalar=sum(2*d/max(1e-10,math.sqrt(q[i])+math.sqrt(q[i+1])) for i,d in enumerate(p['ds']));launch_end=next(x for x in reversed(rows) if x['index']==24)
summary=dict(status='SAVED_ACTUAL_ACCOUNTING_CORRECTED',correction='Original near-start dt/reference proxy incorrectly floored zero reference at signed seam; replaced by exact piecewise q-profile clock integral, clamped to supported [0,L]. Original v1 retained. This clock is accounting only.',all=stats(rows),groups_overlap=True,groups=groups,scalar_profile_clock_s=scalar,actual_minus_scalar_s=15.1-scalar,launch_end_speed=launch_end['v'],launch_end_reference=launch_end['target'],remaining_target_gap_s=3.11,warning='Durations and reference clock differences are accounting, not intervention/recoverable gains. Scalar reference clock is not a physical lower bound.',source_input_sha256={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in (D/'frozen-paths-private.json',G/'retry/brake536_native_result.json')},CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,native_actions=0,model_ticks=0)
with (G/'retry/structure537_analysis_corrected.json').open('x') as f:json.dump(summary,f,indent=2)
for x in rows:x['binding']=list(x['binding'])
with (O/'accounting-corrected-rows-private.json').open('x') as f:json.dump(rows,f)
print(json.dumps(summary,indent=2))
