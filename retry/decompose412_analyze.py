"""Stored-boundary algebra only: same-reference-position additive time ledger.
No environment, controller evaluation, model integration, training or search.
"""
import datetime,hashlib,json,math,os,signal,sys,time
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def new(p,x):
 assert not p.exists(),p;p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
def lines(p):return [json.loads(s) for s in Path(p).read_text().splitlines()]
def projection(line,pos,vel,phase):
 # Same canonical polyline projection as397, imported only as pure geometry.
 from retry.executor397 import canonical_projection
 return canonical_projection(line,pos,vel,phase)

class Reference:
 def __init__(self,fixed,nodes):
  self.line=np.asarray(fixed['line'],float);self.ds=np.asarray(fixed['free_profile']['ds'],float);self.nodes=np.asarray(nodes,float);self.curve=np.asarray(fixed['free_profile']['curvature'],float);self.s=np.r_[0,np.cumsum(self.ds)];self.L=float(self.s[-1]);e=np.roll(self.line,-1,axis=0)-self.line;self.tangents=e/np.linalg.norm(e,axis=1)[:,None];assert np.max(abs(np.linalg.norm(e,axis=1)-self.ds))<1e-8
 def clock(self,a,b):
  assert -1e-8<=a<=b<=self.L+1e-8;(a,b)=(max(0,a),min(self.L,b));total=0.
  for j,d in enumerate(self.ds):
   lo=max(a,self.s[j]);hi=min(b,self.s[j+1])
   if hi<=lo:continue
   wl=self.nodes[j]**2;dw=self.nodes[j+1]**2-wl;l=math.sqrt(max(0,wl+dw*(lo-self.s[j])/d));r=math.sqrt(max(0,wl+dw*(hi-self.s[j])/d))
   if l+r==0:raise ValueError('zero_target_plateau')
   total+=2*(hi-lo)/(l+r)
  return total
 def endpoint(self,state,q):
  v=float(state['speed']);t=self.tangents[q['index']];f=np.asarray([-math.sin(state['angle']),math.cos(state['angle'])]);right=np.asarray([math.cos(state['angle']),math.sin(state['angle'])]);vel=np.asarray(state['vel']);h=v*float(f@t);sig=float(vel@t);slip=abs(math.atan2(float(vel@right),float(vel@f))) if v>=1 else None;delta=abs(math.atan2(float(f[0]*t[1]-f[1]*t[0]),float(f@t))) if v>=1 else None
  return dict(v=v,h=h,q=sig,body_slip=slip,heading=delta,curvature=abs(float(self.curve[q['index']])))

def prepare(root):
 d=root/'stage412';assert not(d/'plan.json').exists();v=read(root/'project-effective-budget-v431.json');assert (v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(30334,84000,0);old=read(root/'stage411/plan.json');p404=read(root/'stage404/plan.json');folders=['stage404/O_base','stage404/O_268','stage404/C_268','stage408','stage411/policy_O','stage411/policy_C'];sources=[Path(__file__),G/'retry/executor397.py',G/'retry/closed411_run.py',G/'retry/terminal410_run.py',G/'retry/source_vehicle_transition.py',G/'core/vendor/car_dynamics.py',G/'env_wrapper.py',Path(p404['fixed_plan']),root/'stage404/profiles-private.json',root/'stage404/plan.json',root/'stage411/result.json',root/'stage411/cost.json',root/'stage411/posthoc-result.json',root/'project-effective-budget-v431.json',root/'research-deadline-current.json',G/'retry/envelope399_result.md',G/'retry/methods380_result.md',G/'retry/loss403_result.md']
 for folder in folders:
  sources += [root/folder/'trace-private.jsonl']
  sources += [root/folder/('final-private.json' if folder.startswith('stage411') else 'final-full-private.json')]
 p=dict(stage=412,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],CPU_cap_s=60,execution_wall_cap_s=180,max_parallel=1,new_native_actor_model_learning_SEALED_reserve_paid_cap=0,folders=folders,fixed_plan=p404['fixed_plan'],bins=10,curve_bins=[0,.02,.05,.10],scope='Storedboundary/tire/profile algebra anddesignonly, no optimization/control/modelcalls. Duplicate404/411O and408/411C checked, notindependentsamples.',decomposition='ForpositivefirstpassD, chordd, trapezoidboundaryV,H=mean(vbodyforward dot tangent), Q=mean(vel dot tangent): tauR=integral ds/r(s); A=D/V-tauR; Bheading=D/H-D/V; Bslip=D/Q-D/H; Cmetric=d/V-D/Q; R=dt-d/V. Exact telescoping. Netpathchord=(d-D)/V=Bheading+Bslip+Cmetric, nonadditivediagnostic only. Signedterms, no causal/recoverable claim.',boundary='NormalizefirstprojectionLto0firstlap, unwrapsequentialshortestarc,no sorting. Reverse/zero/nonpositiveendpointproxy/revisit separatelytimeledger, notdividebyepsilon. Officialfinalwrapper officialdt separate becausecenterpositionsmissing; no interpolatedofficialstate. Mainfullrowsendatpre-final. Commonspatialbins allocate bylinearprogressfraction descriptiveproxy; crossingtimebracketsrecorded, notexactmatchedstates.',target='268speednodes referenceatcurrentcanonicalarc, analyticpiecewiseWlinearclock;10.027 isnotphysicalfeasibility/bound. Longitudinalslipdeceleration staysA, notaddedagainasdirectionloss. Truehullpathlengthnotstoredraw,chordlowerproxy andfiniteintervalresidualexplicit.',gates='Source/schema/nonfinite/halfperiodambiguity/timepartition/telescopingorprofileclockfailure stopsanalysis. No assumptions/thresholds tunedafteroutcomes. Atmost2futurehypotheses, native/modelcostsproposalonly.',sources={str(f):sha(f) for f in sources},protected=old['protected'],original408_preserve=old['original408_preserve']);new(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');new(d/'preparation-result.json',dict(implementation_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,implementation_CPU_fully_measured=False,includes_reasoning_tool_latency=True));print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'))))

def run(root):
 d=root/'stage412';p=read(d/'plan.json');assert not(d/'result.json').exists() and not(d/'opening.json').exists();assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 cpu=time.process_time();wall=time.perf_counter();new(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 def timeout(*a):raise TimeoutError('412CPU60_wall180')
 sig={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.01,59-time.process_time()));signal.setitimer(signal.ITIMER_REAL,179)
 fixed=read(Path(p['fixed_plan']));ref=Reference(fixed,read(root/'stage404/profiles-private.json')['speed_nodes268']);datasets={};rawrows={};proxies={};keys=['O_base404','O268404','C268failed404','Cfixed408','Oclosed411','Cclosed411'];terms=['reference_clock_s','speed_tracking_s','heading_s','body_slip_s','path_metric_s','quadrature_residual_s']
 try:
  for key,folder in zip(keys,p['folders']):
   rr=lines(root/folder/'trace-private.jsonl');rawrows[key]=rr;full=read(root/folder/('final-private.json' if folder.startswith('stage411') else 'final-full-private.json'));finish=full['wrapper']['finish_time_s'];t0=rr[0]['pre']['time'];end=finish if finish is not None else rr[-1]['post']['time'];s=0.;frontier=0.;intervals=[];special=dict(terminal_official_s=0.,reverse_s=0.,stationary_s=0.,revisit_s=0.,nonpositive_endpoint_proxy_s=0.);first=True;prevpost=None
   for r in rr:
    if prevpost is not None:assert r['pre']==prevpost
    phase='LAUNCH' if key.startswith('C') and r['step']==1 else 'FIRST_LAP';q0=projection(ref.line,r['pre']['pos'],r['pre']['vel'],phase);q1=r['post_projection'];delta=(q1['arc']-q0['arc']+ref.L/2)%ref.L-ref.L/2;assert abs(delta)<ref.L/2;sp=s+delta;dt=max(0,min(r['post']['time'],end)-r['pre']['time']);prevpost=r['post']
    if r['completed'] or r['post']['time']>end+1e-8:special['terminal_official_s']+=dt;s=sp;continue
    if delta<=0:
     special['stationary_s' if delta==0 else 'reverse_s']+=dt;s=sp;continue
    newdistance=max(0,sp-max(frontier,s));fraction=newdistance/delta;special['revisit_s']+=dt*(1-fraction)
    if fraction==0:s=sp;continue
    e0=ref.endpoint(r['pre'],q0);e1=ref.endpoint(r['post'],q1);V=(e0['v']+e1['v'])/2;H=(e0['h']+e1['h'])/2;Q=(e0['q']+e1['q'])/2;chord=math.dist(r['pre']['pos'],r['post']['pos']);frontier=max(frontier,sp)
    if min(V,H,Q)<=0:special['nonpositive_endpoint_proxy_s']+=dt*fraction;s=sp;continue
    assert sp<=ref.L+1e-8
    tires=r['raw_tire_samples'];rear=[z for z in tires if z['wheel']>=2];front=[z for z in tires if z['wheel']<2];lag=max(abs(z['joint_angle']+r['command'][0]) for z in front);lo=sp-newdistance
    intervals.append(dict(step=r['step'],s0=lo,s1=sp,full_D=delta,dt=dt*fraction,full_dt=dt,chord=chord*fraction,V=V,H=H,Q=Q,heading_mean=np.mean([e['heading'] for e in [e0,e1] if e['heading'] is not None]) if any(e['heading'] is not None for e in [e0,e1]) else None,body_slip_mean=np.mean([e['body_slip'] for e in [e0,e1] if e['body_slip'] is not None]) if any(e['body_slip'] is not None for e in [e0,e1]) else None,curve=(e0['curvature']+e1['curvature'])/2,front_clip=sum(z['clipped'] for z in front)/len(front),rear_clip=sum(z['clipped'] for z in rear)/len(rear),rear_qmax=max(z['force_ratio'] for z in rear),rear_lateral_slip_max=max(abs(z['lateral_slip_m_s']) for z in rear),steer_lag_max=lag,brake=r['command'][2],gas=r['command'][1],t0=r['pre']['time']-t0,t1=r['post']['time']-t0))
    s=sp
   proxies[key]=intervals
   def aggregate(aa,lo=0.,hi=ref.L):
    total={k:0. for k in terms};total.update(scored_time_s=0.,reference_progress_m=0.,boundary_chord_m=0.,net_chord_path_time_s=0.,positive_speed_deficit_s=0.,negative_speed_deficit_s=0.);diag=dict(front_clip=0.,rear_clip=0.,steer_lag=0.,rear_lateral_slip=0.,heading_rad=0.,body_slip_rad=0.,mean_speed=0.,mean_same_position_target=0.);n=0
    for a in aa:
     left=max(lo,a['s0']);right=min(hi,a['s1'])
     if right<=left:continue
     f=(right-left)/(a['s1']-a['s0']);D=right-left;dt=a['dt']*f;chord=a['chord']*f;V,H,Q=a['V'],a['H'],a['Q'];clock=ref.clock(left,right);vals=[clock,D/V-clock,D/H-D/V,D/Q-D/H,chord/V-D/Q,dt-chord/V];assert abs(sum(vals)-dt)<1e-9
     for k,v in zip(terms,vals):total[k]+=v
     total['scored_time_s']+=dt;total['reference_progress_m']+=D;total['boundary_chord_m']+=chord;total['net_chord_path_time_s']+=(chord-D)/V;total['positive_speed_deficit_s']+=max(0,vals[1]);total['negative_speed_deficit_s']+=min(0,vals[1]);n+=1
     for k,v in [('front_clip',a['front_clip']),('rear_clip',a['rear_clip']),('steer_lag',a['steer_lag_max']),('rear_lateral_slip',a['rear_lateral_slip_max']),('heading_rad',a['heading_mean']),('body_slip_rad',a['body_slip_mean']),('mean_speed',V),('mean_same_position_target',D/clock)]:diag[k]+=dt*(v if v is not None else 0.)
    assert abs(total['net_chord_path_time_s']-sum(total[k] for k in ['heading_s','body_slip_s','path_metric_s']))<1e-8
    return dict(**total,intervals=n,diagnostics_time_mean={k:v/total['scored_time_s'] if total['scored_time_s'] else None for k,v in diag.items()},time_identity_residual_s=sum(total[k] for k in terms)-total['scored_time_s'])
   whole=aggregate(intervals);assert abs(whole['scored_time_s']+sum(special.values())-(end-t0))<1e-8
   datasets[key]=dict(official_lap_s=finish-t0 if finish is not None else None,observed_elapsed_s=end-t0,censored=finish is None,actions=len(rr),main_last_progress_m=max(a['s1'] for a in intervals),main=whole,special_time_ledger=special,reference_full_clock_s=ref.clock(0,ref.L),same_fixed_target_not_feasibility=True)
   datasets[key]['curvature_groups']=[dict(range=[lo,hi],**aggregate([a for a in intervals if a['curve']>=lo and (hi is None or a['curve']<hi)])) for lo,hi in [(0,.02),(.02,.05),(.05,.10),(.10,None)]]
   datasets[key]['_aggregate']=aggregate
  # Bind aggregate to each data's reference/terms only; it takes explicit intervals.
  common_end=min(datasets[k]['main_last_progress_m'] for k in ['Oclosed411','Cclosed411']);bins={}
  agg=datasets['Cclosed411']['_aggregate']
  for key in ['Oclosed411','Cclosed411','O_base404']:
   bins[key]=[dict(arc_fraction=[j/10,(j+1)/10],**agg(proxies[key],common_end*j/10,common_end*(j+1)/10)) for j in range(10)]
  prefix_end=datasets['C268failed404']['main_last_progress_m'];matched_failure={key:agg(proxies[key],0,prefix_end) for key in ['C268failed404','Oclosed411','Cclosed411']}
  crossings={}
  for key in ['Oclosed411','Cclosed411']:
   crossings[key]=[dict(fraction=j/10,time_bracket_s=[a['t0'],a['t1']],step=a['step']) for j in range(1,10) for a in proxies[key] if a['s0']<common_end*j/10<=a['s1']]
  for z in datasets.values():z.pop('_aggregate')
  assert datasets['O268404']['main']==datasets['Oclosed411']['main'] and datasets['Cfixed408']['main']==datasets['Cclosed411']['main']
  q411=read(root/'stage411/result.json');essential=(18616+19110)//2;assert essential==18863
  compute=dict(total_411_model_ticks=38038,gate_qualification_ticks=312,policy_required_single_copy_recipe_ticks=essential,policy_duplicate_qualification_ticks=essential,total_worlds=756,gate_worlds=6,policy_required_recipe_worlds=375,policy_duplicate_worlds=375,mandatory_actual_safety_and_domain_checks_not_removed=True,query_wall_max_p95_O_s=[q411['policy_results'][0]['query_wall_max_s'],q411['policy_results'][0]['query_wall_p95_s']],query_wall_max_p95_C_s=[q411['policy_results'][1]['query_wall_max_s'],q411['policy_results'][1]['query_wall_p95_s']],CPU_saving_if_duplicates_removed_not_measured=True,no_latency_scaling_claim=True)
  elapsed=time.process_time()-cpu;w=time.perf_counter()-wall;assert time.process_time()<60 and w<180;assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00'))
  result=dict(stage=412,status='COMPLETED_STORED_ALGEBRA',reference_length_m=ref.L,reference_clock_s=ref.clock(0,ref.L),reference_clock_not_feasibility_or_bound=True,common_main_end_fraction=common_end/ref.L,datasets=datasets,common_spatial_bins=bins,common_failure_prefix=matched_failure,common_spatial_crossing_brackets=crossings,compute411=compute,new_native_actor_model_learning_SEALED_reserve_paid=0,CPU_s=elapsed,wall_s=w,wholeprocess_CPU_s=time.process_time(),additive_terms=terms,all_time_identities_passed=True,source_hashes_exact=all(sha(f)==h for f,h in p['sources'].items()));new(d/'result.json',result);new(d/'intervals-private.json',proxies)
  print(json.dumps(dict(stage=412,CPU_s=elapsed,wall_s=w,main={k:z['main'] for k,z in datasets.items()},common_bins={k:[{kk:bb[kk] for kk in ['arc_fraction','scored_time_s','speed_tracking_s','heading_s','body_slip_s','path_metric_s','quadrature_residual_s']} for bb in vv] for k,vv in bins.items()}),ensure_ascii=False))
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,h in sig.items():signal.signal(s,h)
if __name__=='__main__':
 root=Path(sys.argv[2]);{'prepare':prepare,'run':run}[sys.argv[1]](root)
