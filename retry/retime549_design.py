"""One whole-path axle-force-coupled retiming, cap90 unchanged. Pure algebra."""
import bisect,datetime,hashlib,json,math,signal,time,traceback
from pathlib import Path
from retry.envelope500 import MASS as EFFECTIVE_LONGITUDINAL_MASS,REAR
from retry.profile539_profile import rebuild_profile


def clock(path):
 q=path['launch_squared'];return sum(2*d/(math.sqrt(max(0.,q[i]))+math.sqrt(max(0.,q[i+1])) ) for i,d in enumerate(path['ds']))


def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response549-private');read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=read(G/'retry/retime549_contract.json');D.mkdir(mode=0o700,exist_ok=False);cost=dict(force_bound_evaluations=0,bisection_updates=0,passes=0)
 def guard(*a):
  if time.process_time()-cpu>=60 or time.perf_counter()-wall>=90:raise RuntimeError('DESIGN_COST_CAP')
  if cost['force_bound_evaluations']>=1000000:raise RuntimeError('BOUND_EVALUATION_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(c['deadline_utc']):raise RuntimeError('DEADLINE')
 def save(p,value):
  with p.open('x') as f:json.dump(value,f,indent=2)
  p.chmod(0o600 if D in p.parents else 0o644)
 assert all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items());save(D/'DESIGN_STARTED.json',dict(contract_sha256=sha(G/'retry/retime549_contract.json')));signal.signal(signal.SIGPROF,guard);signal.setitimer(signal.ITIMER_PROF,60);signal.signal(signal.SIGALRM,guard);signal.setitimer(signal.ITIMER_REAL,90);out={}
 try:
  static=read(Path('/workspace/haic-response515-private/collected-map-state-private.json'));old=read(Path('/workspace/haic-response541-private/frozen-paths-private.json'));high=old['candidate'];low=old['backup'];full=read(Path('/workspace/haic-response541-private/native-full-records-private.json'));split=51+sum(x['raw_ticks'] for x in full[0]['rows']);rows=read(Path('/workspace/haic-response549-input-private/saved541-candidate-rows-private.json'));assert len(rows)==683;n=len(high['ds']);assert set(mu for poly,mu in static['roads'])=={1.};mass=static['root']['planar']['linear']['mass'];a=static['root']['planar']['angle'];f=(-math.sin(a),math.cos(a));levers=static['root']['planar']['levers'];front=sum(sum(f[j]*r[j] for j in range(2)) for r in levers[:2])/2;rear=-sum(sum(f[j]*r[j] for j in range(2)) for r in levers[2:])/2;weights=(rear/(front+rear),front/(front+rear));coeff=(mass*weights[0]/2,mass*weights[1]/2);mu=[w['friction'] for w in static['root']['planar']['linear']['wheels']];assert mu==[400.]*4;limit=[.999*z for z in mu];obs=[0.]*n
  for r in rows:
   if r['action']<=24:continue
   v0=r['before']['velocity'];v1=r['velocity'];v=(math.hypot(*v0)+math.hypot(*v1))/2;k=abs(math.atan2(v0[0]*v1[1]-v0[1]*v1[0],sum(v0[j]*v1[j] for j in range(2)))/(.02*v));i=min(n-1,max(0,bisect.bisect_left(high['arcs'][1:],r['station'])));obs[i]=max(obs[i],k)
  k=[max(abs(high['curvature'][i]),obs[i-1],obs[i],obs[(i+1)%n]) for i in range(n)];segment_k=[max(k[i],k[(i+1)%n]) for i in range(n)];cap=[]
  for i in range(n):
   support=max(segment_k[i-1],segment_k[i]);cap.append(min(90.**2,min(limit[j]/((coeff[0] if j<2 else coeff[1])*max(support,1e-12)) for j in range(4))))
  def acceleration(q,K,braking):
   guard();cost['force_bound_evaluations']+=1;lat=[(coeff[0] if j<2 else coeff[1])*q*K for j in range(4)];available=[math.sqrt(max(0.,limit[j]**2-lat[j]**2)) for j in range(4)]
   if braking:return min(80.,min(4*z/mass for z in available))
   return min(REAR,80000./(EFFECTIVE_LONGITUDINAL_MASS*(math.sqrt(max(q,0.))+2.7)),min(2*z/mass for z in available[2:]))
  def restrict(current,other,K,ds,braking):
   if current<=other:return current
   if current-other<=2*acceleration(current,K,braking)*ds:return current
   lo=other;hi=current
   for _ in range(40):
    mid=(lo+hi)/2;cost['bisection_updates']+=1
    if mid-other<=2*acceleration(mid,K,braking)*ds:lo=mid
    else:hi=mid
   return lo
  q=cap.copy()
  for it in range(2*n):
   before=q.copy()
   for i in range(n-1,-1,-1):q[i]=restrict(q[i],q[(i+1)%n],segment_k[i],high['ds'][i],True)
   for i in range(n):j=(i+1)%n;q[j]=restrict(q[j],q[i],segment_k[i],high['ds'][i],False)
   cost['passes']=it+1
   if q==before:break
  else:raise RuntimeError('FINITE_PROFILE_PASSES_EXHAUSTED')
  launch=[0.]
  for i,d in enumerate(high['ds']):launch.append(restrict(q[(i+1)%n],launch[-1],segment_k[i],d,False))
  candidate=dict(high,periodic_squared=q,launch_squared=launch,periodic_pass_rounds=cost['passes']);reconstructed=rebuild_profile(high,.70*1600/mass,90.);assert reconstructed['periodic_squared']==high['periodic_squared'] and reconstructed['launch_squared']==high['launch_squared'];worst=0.
  for values in (q+[q[0]],launch):
   for i,d in enumerate(high['ds']):
    qmax=max(values[i:i+2]);acc=(values[i+1]-values[i])/(2*d);lat=[(coeff[0] if j<2 else coeff[1])*qmax*segment_k[i] for j in range(4)];long=[mass*max(acc,0)/2 if j>=2 else 0 for j in range(4)] if acc>=0 else [mass*abs(acc)/4]*4;worst=max(worst,max(math.hypot(x,y)/m for x,y,m in zip(lat,long,mu)));assert qmax<=90**2+1e-8
  assert worst<=.9990000001
  paths=dict(baseline=high,baseline_backup=low,candidate=candidate,backup=low);save(D/'frozen-paths-private.json',paths);save(D/'curvature-force-design-private.json',dict(observed_curvature=obs,design_curvature=k,segment_curvature=segment_k,periodic_q=q,launch_q=launch,body_mass=mass,axle_load_fractions=weights))
  # Predeclared selection: greatest scalar clock advantage over a 32-action oldactual window; no propagation outcomes used.
  candidates=[]
  for entry in range(25,116):
   ar=[r for r in rows if entry<=r['action']<=entry+31]
   if len(ar)!=128:continue
   score=0.
   for r in ar:
    s=min(high['length'],max(0,r['station']));i=min(n-1,bisect.bisect_left(high['arcs'][1:],s));fraction=min(1,max(0,(s-high['arcs'][i])/high['ds'][i]));oldv=math.sqrt(max(0,high['launch_squared'][i]+fraction*(high['launch_squared'][i+1]-high['launch_squared'][i])));newv=math.sqrt(max(0,launch[i]+fraction*(launch[i+1]-launch[i])));score+=.02*(1-oldv/max(newv,1.))
   candidates.append((score,-entry))
  score,negentry=max(candidates);entry=-negentry;act=read(Path('/workspace/haic-response541-private')/f'action-candidate-{entry:03d}.json');past=[r for r in rows if 24<r['action']<entry];endrow=next(r for r in reversed(rows) if r['action']==entry+31);i=min(n-1,bisect.bisect_left(high['arcs'][1:],endrow['station']));p0=high['points'][i];p1=high['points'][(i+1)%n];d=math.dist(p0,p1);gate=dict(point=endrow['position'],tangent=[(p1[j]-p0[j])/d for j in range(2)],curvature=high['curvature'][i]);save(D/'probe-private.json',dict(entry=entry,completed=entry-1,root=act['before_root_without_roads'],history=[sum(z['ratio']>1 for r in past for z in r['forces']),4*len(past)],gate=gate))
  post=[r for r in rows if r['action']>24];near=[r for r in post if r['speed']-r['reference_speed']>=4.];lowforce=[r for r in near if max(z['ratio'] for z in r['forces'])<.7]
  out=dict(passed=True,whole_reference_clock_old_s=clock(high),whole_reference_clock_candidate_s=clock(candidate),scalar_clock_difference_s=clock(high)-clock(candidate),scalar_not_actual_gain_or_bound=True,nominal_cap_unchanged90=True,geometry_unchanged=True,backup_unchanged=True,design_peak_axle_wheel_ratio=worst,axle_load_fractions=weights,body_mass_kg=mass,effective_longitudinal_mass_kg=EFFECTIVE_LONGITUDINAL_MASS,reference_near_bound_seconds=.02*len(near),reference_near_with_low_force_seconds=.02*len(lowforce),selected_entry=entry,selected_window_scalar_proxy_s=score,frozen_paths_sha256=sha(D/'frozen-paths-private.json'),new_model_ticks=0,new_native_actions=0)
 except BaseException as exc:
  out=dict(passed=False,error=type(exc).__name__+':'+str(exc),new_model_ticks=0,new_native_actions=0);save(D/'design-error-private.json',dict(error=out['error'],traceback=traceback.format_exc(),cost=cost))
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);out.update(cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,research_remaining=22758,reserve=84000,reserve_used=0);save(G/'retry/retime549_design_result.json',out);print(json.dumps(out,indent=2))
if __name__=='__main__':run()
