"""Saved402 lap decomposition and honest lightweight269 comparison; no dynamics."""
import datetime,json,hashlib,math,time,sys,signal
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parent.parent

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 assert not p.exists(),p
 p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n');p.chmod(0o600)
def prepare(root):
 d=root/'stage403';assert not d.exists();d.mkdir(mode=0o700);p402=read(root/'stage402/plan.json');p269=read(root/'stage269/plan.json');files=[Path(__file__),root/'stage402/plan.json',root/'stage402/P10_C/trace-private.jsonl',root/'stage402/P10_C/result.json',root/'stage402/P10_C/final-full-private.json',root/'stage269/plan.json',root/'stage269/N1_candidate/trajectory-private.json',root/'stage269/N1_candidate/result.json',Path(p402['fixed_plan']),Path(p269['frozen_plans']['N1']),root/'stage401/P15_J-rows-private.json',root/'stage401/P10_J-rows-private.json',G/'retry/factorial401_run.py',G/'retry/executor397.py',G/'retry/pace268_profile.py',G/'retry/pace269_run.py',G/'core/vendor/car_dynamics.py',G/'env_wrapper.py',root/'project-effective-budget-v422.json',root/'research-deadline-current.json']
 p=dict(stage=403,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),CPU_cap_s=60,wall_cap_s=120,new_wrapper_cap=0,actor_cap=0,model_tick_cap=0,learning_cap=0,SEALED_cap=0,new_paid_cap=0,scope='Descriptive402wholelap and269lightweightstoredrecords only; fixed10equalactualarcbins,curvature[.02,.05,.10],pedal/magnitudeclamp/targetgap/projectionprogress;no newprofile/forwardpass/controller evaluation.',time_rule='Scoredlapclocktruncateeachactualwrapperintervalatofficialcenterfinish. Attributeintervalto preunwrappedreferencearcbin,neverinventinterpolatedboundarytime;markstraddlersandgivecrossingintervalsfor10..90%.Tire samples includeallactualticks including1clearance tick. Instantaneouspre-sigma weighted byscoredtime; sigma/v onlyspeed>=1,exclusionreported. TargetmissingLAUNCHexcludednotzero.',comparison='Verifyfixedpath/profile/roadinitialregistrationequal. Compareofficiallaps andpre-speed/target/pedals summary andfirstpostvisitedcountthreshold intervals10..100%;visitedcountnotgeometricarc/state identity. Historicalregularstep .08 fromwrappercontract,terminaldurationactualrawticks. No historicalpositions/yaw/force/feed reconstruction. Incrementalvisitbandbounds fromintervaldifference.',joint='Analyzeall320Jrows,fixed6candidatelexrank;reconstructchoicefromstoredmetrics, comparelowestnominalerror/progress vswinningcoast. Designonlyonefixeddeadlinefiniteprogressalternative,notexecuted.',failure='Source/schema/nonfinite/timepartition failure ->stopanalysis,no substitutes/model calls. Allcomparisonlimits explicit. No11simpossibility/296promotion.',sources={str(f):sha(f) for f in files},protected={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']})
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');print('403 saved-data analysis registered')
def run(root):
 d=root/'stage403';p=read(d/'plan.json');assert not(d/'result.json').exists()
 for f,h in {**p['sources'],**p['protected']}.items():assert sha(f)==h,f
 start,cpu=time.perf_counter(),time.process_time()
 def timeout(*args):raise TimeoutError('403CPU60')
 prior=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,60)
 p402=read(root/'stage402/plan.json');p269=read(root/'stage269/plan.json');fixed=read(Path(p402['fixed_plan']));histfixed=read(Path(p269['frozen_plans']['N1']));assert fixed['line']==histfixed['line'] and fixed['free_profile']==histfixed['free_profile'] and p402['case']['road_geometry_sha256']==p269['cases']['N1']['road_geometry_sha256']
 rows=[json.loads(s) for s in (root/'stage402/P10_C/trace-private.jsonl').read_text().splitlines()];old=read(root/'stage269/N1_candidate/trajectory-private.json');oldres=read(root/'stage269/N1_candidate/result.json');final=read(root/'stage402/P10_C/final-full-private.json');ds=np.asarray(fixed['free_profile']['ds']);L=float(sum(ds));curve=np.abs(np.asarray(fixed['free_profile']['curvature']));t0=rows[0]['pre']['time'];finish=final['wrapper']['finish_time_s'];prepared=[];initialvisited=read(root/'stage402/P10_C/initial-private.json')['physical']['unique_tiles']
 for i,r in enumerate(rows):
  ref=r['reference'];s=ref['actual_arc'];postarc=r['post_projection']['arc'];prearc=ref['projection']['arc'];sp=s+(postarc-prearc+L/2)%L-L/2;duration=max(0,min(r['post']['time'],finish)-r['pre']['time']);speed=r['pre']['speed'];q=ref['projection'];raw=ref.get('raw_accel');command=ref.get('command_accel');prepared.append(dict(row=r,dt=duration,s=s,sp=sp,bin=min(9,max(0,int(s/L*10))),curve=float(curve[q['index']]),v=speed,target=ref.get('r'),sigma=q['sigma'],ratio=q['sigma']/speed if speed>=1 else None,gas=r['command'][1],brake=r['command'][2],raw=raw,command=command,previsited=initialvisited if i==0 else rows[i-1]['post']['visited']))
 assert abs(sum(a['dt'] for a in prepared)-(finish-t0))<1e-10
 def weighted(aa,key):
  z=[a for a in aa if a[key] is not None];return sum(a['dt']*a[key] for a in z)/sum(a['dt'] for a in z) if z else None
 def agg(aa):
  ss=[s for a in aa for s in a['row']['raw_tire_samples']];dt=sum(a['dt'] for a in aa);st={}
  for n,indices in [('front',[0,1]),('rear',[2,3])]:
   q=[s for s in ss if s['wheel'] in indices];st[n]=dict(samples=len(q),clipped=sum(s['clipped'] for s in q))
  return dict(actions=len(aa),scored_time_s=dt,mean_speed=weighted(aa,'v'),mean_target=weighted(aa,'target'),mean_target_minus_speed=sum(a['dt']*(a['target']-a['v']) for a in aa if a['target'] is not None)/sum(a['dt'] for a in aa if a['target'] is not None) if any(a['target'] is not None for a in aa) else None,mean_sigma=weighted(aa,'sigma'),mean_sigma_speed_ratio=weighted(aa,'ratio'),ratio_excluded_time_s=sum(a['dt'] for a in aa if a['ratio'] is None),gas_time_s=sum(a['dt'] for a in aa if a['gas']>0),brake_time_s=sum(a['dt'] for a in aa if a['brake']>0),coast_time_s=sum(a['dt'] for a in aa if a['brake']==a['gas']==0),both_pedals_time_s=sum(a['dt'] for a in aa if a['brake']>0 and a['gas']>0),positive_clamp_time_s=sum(a['dt'] for a in aa if a['raw'] is not None and a['raw']>fixed['model']['rear_traction_accel']),negative_clamp_time_s=sum(a['dt'] for a in aa if a['raw'] is not None and a['raw']<-fixed['model']['brake_accel']),braking_below_target_time_s=sum(a['dt'] for a in aa if a['target'] is not None and a['v']<a['target'] and a['brake']>0),under_target5_time_s=sum(a['dt'] for a in aa if a['target'] is not None and a['target']-a['v']>=5),max_post_path_error_m=max([a['row']['post_projection']['path_error_m'] for a in aa] or [0]),tires=st)
 bins=[dict(arc_fraction=[i/10,(i+1)/10],**agg([a for a in prepared if a['bin']==i])) for i in range(10)];crossings=[]
 for j in range(1,10):
  bound=L*j/10;a=next(a for a in prepared if a['s']<bound<=a['sp']);crossings.append(dict(fraction=j/10,interval_s=[a['row']['pre']['time']-t0,min(a['row']['post']['time'],finish)-t0],crossing_action=a['row']['step']))
 curv=[]
 for lower,upper in [(0,.02),(.02,.05),(.05,.10),(.10,float('inf'))]:curv.append(dict(curvature_range=[lower,None if math.isinf(upper) else upper],**agg([a for a in prepared if lower<=a['curve']<upper])))
 N=oldres['total_tiles'];assert N==initialvisited+sum(t['visited']-old[j-1]['visited'] for j,t in enumerate(old) if j) or N==old[-1]['visited']
 hist_terminal_raw=oldres['raw_step_ticks']-4*(len(old)-1);assert 1<=hist_terminal_raw<=4
 visit=[]
 for fraction in [j/10 for j in range(1,11)]:
  threshold=math.ceil(N*fraction);a=next(r for r in rows if r['post']['visited']>=threshold);o=next(r for r in old if r['visited']>=threshold);nt=[a['pre']['time']-t0,min(a['post']['time'],finish)-t0];ot=[(o['step']-1)*.08,(o['step']*.08 if o['step']<len(old) else oldres['raw_step_ticks']*.02)];visit.append(dict(fraction=fraction,visited_threshold=threshold,new_interval_s=nt,old_interval_s=ot,new_minus_old_interval_s=[nt[0]-ot[1],nt[1]-ot[0]]))
 bands=[]
 for i,q in enumerate(visit):
  pr=visit[i-1] if i else dict(new_interval_s=[0,0],old_interval_s=[0,0]);nt=[q['new_interval_s'][0]-pr['new_interval_s'][1],q['new_interval_s'][1]-pr['new_interval_s'][0]];ot=[q['old_interval_s'][0]-pr['old_interval_s'][1],q['old_interval_s'][1]-pr['old_interval_s'][0]];bands.append(dict(visited_fraction=[i/10,(i+1)/10],new_duration_interval_s=nt,old_duration_interval_s=ot,new_minus_old_duration_interval_s=[nt[0]-ot[1],nt[1]-ot[0]]))
 hist=dict(actions=len(old),lap_s=oldres['lap_ms']/1000,raw_step_ticks=oldres['raw_step_ticks'],terminal_raw_ticks=hist_terminal_raw,actual_speed_median=float(np.median([r['speed_m_s'] for r in old])),target_speed_median=float(np.median([r['target_speed_m_s'] for r in old])),gas_actions=sum(r['action'][1]>0 for r in old),brake_actions=sum(r['action'][2]>0 for r in old),coast_actions=sum(r['action'][1]==r['action'][2]==0 for r in old),max_path_error=max(r['path_error_m'] for r in old),positions_forces_yaw_feed_unavailable=True)
 joints=[]
 for name in ['P15_J','P10_J']:
  rr=read(root/f'stage401/{name}-rows-private.json');counts={};gaps=[];coast_wins=0
  for r in rr:
   valid=[c for c in r['candidate_summary'] if not c['metrics']['flags']];best=min(valid,key=lambda c:(c['metrics']['path_error'],c['metrics']['abs_yaw'],-c['metrics']['arc'],c['index']));counts[str(best['index'])]=counts.get(str(best['index']),0)+1;nom=[c for c in valid if c['index']%2==0];gaps.append(min(c['metrics']['path_error'] for c in nom)-best['metrics']['path_error']);coast_wins+=best['index']%2==1
  joints.append(dict(arm=name,actions=len(rr),chosen_counts=counts,coast_choices=coast_wins,nominal_min_error_minus_winner_min=float(min(gaps)),nominal_min_error_minus_winner_max=float(max(gaps)),final_arc=rr[-1]['arc'],speed_max=max(r['speed'] for r in rr)))
 signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,prior)
 result=dict(stage=403,same_geometry_profile_registration=True,reference_length_m=L,official_lap_s=finish-t0,historical_lap_difference_s=(finish-t0)-hist['lap_s'],gap_to11_s=(finish-t0)-11,stored_profile_estimated_time_s=fixed['free_profile']['estimated_time_s'],whole=agg(prepared),arc_bins=bins,arc_crossing_intervals=crossings,curvature_groups=curv,visit_threshold_comparison=visit,visit_band_duration_comparison=bands,historical=hist,joint_objective=joints,new_wrapper_actions=0,new_actor_calls=0,new_model_integration_ticks=0,new_learning_fits=0,new_SEALED_queries=0,new_paid_resources=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,source_hashes_rechecked=all(sha(f)==h for f,h in p['sources'].items()),protected_hashes_rechecked=all(sha(f)==h for f,h in p['protected'].items()),scope='Descriptiveknownsavedconditions;visitcountsnotspatialmatch,arcbintimesprestateattributionnotexactcontinuoussegmentation;nooptimalityboundor296promotion')
 assert result['CPU_s']<60 and result['wall_s']<120;save(d/'result.json',result);print(json.dumps(dict(stage=403,CPU_s=result['CPU_s'],lap_s=result['official_lap_s'],old_lap_s=hist['lap_s'],partition_time=sum(b['scored_time_s'] for b in bins)),ensure_ascii=False))
if __name__=='__main__':
 root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
