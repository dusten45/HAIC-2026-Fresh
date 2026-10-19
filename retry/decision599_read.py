"""599 reads saved evidence only. No controller, integrator, evaluator or solver imports."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import bisect,hashlib,json,math,mmap,signal,statistics,subprocess,datetime
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response599-private')
FILES=dict(result598=G/'retry/cold598_result.json',audit598=G/'retry/cold598_audit.json',contract598=G/'retry/cold598_contract.json',code598=G/'retry/cold598_native.py',support598=G/'retry/cold598_support.py',runner=G/'local_runner.py',analysis578=G/'retry/reframe578_analysis.json',reader578=G/'retry/reframe578_analyze.py',journal598=Path('/workspace/haic-response598-private/journal-private.jsonl'),baseline598=Path('/workspace/haic-response598-private/arm-baseline-private.json'),candidate598=Path('/workspace/haic-response598-private/arm-candidate-private.json'),source577=Path('/workspace/haic-response577-private/final-independent-tape-private.json'),path551=Path('/workspace/haic-response551-private/frozen-paths-private.json'),path541=Path('/workspace/haic-response541-private/frozen-paths-private.json'),static=Path('/workspace/haic-response515-private/collected-map-state-private.json'))
NAMES=['beam579','forensic580','slip581','return582','return583','cone584','kinematic585','shoot586','reselect587','smoother588','corridor589','retime590']
FILES.update({n:G/f'retry/{n}_result.md' for n in NAMES})
rd=lambda p:json.loads(p.read_text())
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  while b:=f.read(1024*1024):h.update(b)
 return h.hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def save(p,x):
 with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False);f.write('\n')
def native_rows(arm,score):
 out=[]
 for q in arm['raw_records']:
  if q['phase']!='action':continue
  i=len(out)+1
  if i>score:break
  out.append(dict(index=q['action'],progress=q['station'],center=q['position'],before=q['before_position'],velocity=q['velocity'],before_velocity=q['before']['velocity'],speed=q['speed'],margin=q['margin'],path_error=q['path_error'],overspeed=q['speed']-q['reference_speed'],force_peak=max(v['ratio'] for v in q['forces']),t=i*.02))
 return out
def source_rows(tape):
 return [dict(index=q['index'],progress=q['progress'],center=q['root_without_roads']['center'],before=q['before_root_without_roads']['center'],velocity=q['root_without_roads']['planar']['linear']['velocity'],before_velocity=q['before_root_without_roads']['planar']['linear']['velocity'],speed=math.hypot(*q['root_without_roads']['planar']['linear']['velocity']),margin=q['margin'],path_error=q['path_error'],overspeed=q['reference_overspeed'],force_peak=max(v['ratio'] for v in q['forces']),t=(i+1)*.02) for i,q in enumerate(tape['rows'][:660])]
def allocate(rows,path,obstacles):
 groups={k:[] for k in ['launch','straight_acceleration_or_cruise','corner_curvature','avoidance_proximity','recovery_window']};last_zone=None
 for q in rows:
  s=q['progress'];j=max(0,min(len(path['curvature'])-1,bisect.bisect_right(path['arcs'],s%path['length'])-1));near=min(math.dist(q['center'],center)-radius for center,radius in obstacles)<8.;turn=abs(path['curvature'][j])>=.0125
  if near or turn:last_zone=s
  label='launch' if q['index']<=24 else 'avoidance_proximity' if near else 'corner_curvature' if turn else 'recovery_window' if last_zone is not None and 0<=s-last_zone<=35 else 'straight_acceleration_or_cruise';groups[label].append(q)
 return {k:dict(raw=len(v),elapsed_s=.02*len(v),COM_distance_m=sum(math.dist(q['before'],q['center']) for q in v),median_COM_speed_m_s=statistics.median(q['speed'] for q in v) if v else None,positive_acceleration_raw=sum(q['speed']>math.hypot(*q['before_velocity'])+.001 for q in v),fullgas_command_raw=None,tracking_near_reference_within_point1_raw=sum(q['index']>24 and 4.85-q['overspeed']<.1 for q in v),tracking_near_force_within_point009_raw=sum(q['index']>24 and q['force_peak']>1.05 for q in v),footprint_below_point6_raw=sum(q['margin']<.6 for q in v),path_above2point9_raw=sum(q['path_error']>2.9 for q in v),reference_ceiling_saturation_proxy_s=sum(.02*max(0.,1-q['speed']/(q['speed']-q['overspeed']+4.85)) for q in v if q['index']>24)) for k,v in groups.items()}
def crossing(rows,s):
 old_s=0.;old_t=0.
 for i,q in enumerate(rows):
  if old_s<s<=q['progress']:
   return dict(before_raw=i,after_raw=i+1,earliest_s=i*.02,latest_s=(i+1)*.02,interpolated_diagnostic_s=old_t+(q['t']-old_t)*(s-old_s)/(q['progress']-old_s))
  old_s=q['progress'];old_t=q['t']
 return None
def selected_events(path,kind):
 out=[];needle=('"kind":"'+kind+'"').encode()
 with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
  start=0
  while (p:=m.find(needle,start))>=0:
   a=m.rfind(b'\n',0,p)+1;b=m.find(b'\n',p);q=json.loads(m[a:b]);start=b+1
   if q['kind']==kind:out.append(q)
 return out
def main():
 D.mkdir(mode=0o700,exist_ok=False)
 def stop(*a):raise RuntimeError('599_READ_ONLY_TIME_CAP')
 signal.signal(signal.SIGPROF,stop);signal.signal(signal.SIGALRM,stop);signal.setitimer(signal.ITIMER_PROF,60);signal.setitimer(signal.ITIMER_REAL,90)
 c=dict(study=599,status='READ_ONLY_NO_NEW_EVALUATION',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',caps=dict(CPU_s=60,wall_s=90,source=0,native=0,force=0,geometry_evaluator=0,solver=0,new_policy_evaluations=0),input_sha256={k:sha(p) for k,p in FILES.items()},implementation_sha256=sha(Path(__file__)),scope='ReadsavedJSON/code/aggregatearithmeticonly.No rollout/choose/force/project/certify/solver/timingbenchmarkcall. Native/privateposesnotpublished.',research_remaining=22211,reserve=84000,reserve_used=0)
 save(G/'retry/decision599_contract.json',c)
 r=rd(FILES['result598']);a=rd(FILES['audit598']);old=rd(FILES['analysis578']);assert a['status']=='READ_ONLY_AUDIT_PASS' and r['status']=='COLD_ONLY_NATIVE_POSITIVE_DIAGNOSTIC';assert c['input_sha256']['journal598']==r['private_sha256']['journal-private.jsonl'];assert c['input_sha256']['baseline598']==r['private_sha256']['arm-baseline-private.json'] and c['input_sha256']['candidate598']==r['private_sha256']['arm-candidate-private.json']
 paths=rd(FILES['path551']);baselinepath=rd(FILES['path541'])['candidate'];path=paths['candidate'];static=rd(FILES['static']);geometry_keys=['points','ds','arcs','curvature','length'];assert all(digest(path[k])==digest(baselinepath[k]) for k in geometry_keys),'NO_COMMON_GEOMETRY'
 bas=rd(FILES['baseline598']);cand=rd(FILES['candidate598']);data=dict(source577=source_rows(rd(FILES['source577'])),baseline598=native_rows(bas,683),candidate598=native_rows(cand,661));allocation={k:allocate(v,path,static['obstacles']) for k,v in data.items()}
 recomputed=all(abs(allocation['source577'][k][field]-v[field])<1e-8 for k,v in old['allocation_current'].items() for field in ['raw','elapsed_s','COM_distance_m','median_COM_speed_m_s','positive_acceleration_raw','tracking_near_reference_within_point1_raw','tracking_near_force_within_point009_raw','footprint_below_point6_raw','path_above2point9_raw','reference_ceiling_saturation_proxy_s']);assert recomputed,'578_RULE_REPRODUCTION'
 common={str(s):{k:crossing(v,s) for k,v in data.items()} for s in range(100,1000,100)};assert all(q for v in common.values() for q in v.values());interval=[];previous={k:0. for k in data}
 for endpoint in [*range(100,1000,100),'official_finish']:
  t={k:(common[str(endpoint)][k]['interpolated_diagnostic_s'] if endpoint!='official_finish' else len(v)*.02) for k,v in data.items()};elapsed={k:t[k]-previous[k] for k in data};interval.append(dict(endpoint=endpoint,elapsed_s=elapsed,candidate_minus_baseline_ms=1000*(elapsed['candidate598']-elapsed['baseline598']),candidate_minus_source577_ms=1000*(elapsed['candidate598']-elapsed['source577']),cumulative_candidate_minus_baseline_ms=1000*(t['candidate598']-t['baseline598'])));previous=t
 holds={(q['label'],q['next_hold']):q for q in selected_events(FILES['journal598'],'HOLD_RESERVE')};actions=selected_events(FILES['journal598'],'ACTION_CHARGED');work=[]
 for q in actions:
  if q['label']!='candidate' or q['index']<40:continue
  h=holds[('candidate',q['index'])];before=h['counts'];after=q['counts'];deltas={k:after.get(k,0)-before.get(k,0) for k in ['model_attempted','model_completed','external_force','internal_force','geometry']};w=dict(hold=q['index'],chooser_model_attempts=deltas['model_attempted']-4,chooser_model_completed=deltas['model_completed']-4,chooser_external_force=deltas['external_force']-16,chooser_internal_force=deltas['internal_force']-16,chooser_geometry=deltas['geometry']-4,certificate_mode=q['certificate']['mode'],measured_latency_available=False);assert w['chooser_model_attempts']>=96 and w['chooser_geometry']>=0;work.append(w)
 assert len(work)==127;chosen=min(work,key=lambda q:(-q['chooser_model_attempts'],q['hold']));event=next(q for q in actions if q['label']=='candidate' and q['index']==chosen['hold']);running=[0,0];launch=[0,0];prior=None
 for q in cand['raw_records']:
  if q['phase']!='action' or q['action']>=chosen['hold']:continue
  group=launch if q['action']<=24 else running;group[0]+=sum(f['ratio']>1 for f in q['forces']);group[1]+=4;prior=q
 assert prior is not None
 packet=dict(scope='DECISION_SUFFICIENT_MODEL_INPUT_NOT_NATIVE_OR_PIXEL_CHECKPOINT',hold=chosen['hold'],root=event['before_root'],progress=prior['station'],actual_running_history=running,actual_launch_history=launch,tracker=event['tracker'],visited=event['visited'],clock=event['clock'],expected_action_bits=event['payload_bits'],expected_certificate=event['certificate'],paths_sha256=c['input_sha256']['path551'],roads_static_sha256=c['input_sha256']['static'],source_event_sha256=event['sha256'],source_event_sequence=event['sequence'],stored_work=chosen)
 save(D/'proposed-timing-input-private.json',packet);save(D/'chooser-work-private.json',work)
 timing=dict(actual_Agent_act_boundary='local_runner.safe_actthread:Agent.act(observation)+np.asarray(dtype=float32).reshape,join5seconds;env.step/render/nativephysicsoccurafterreturn.',native598_call_boundary='Directprivilegedchoose/candidate_select,thenactualstatehash,4rawpreview,fsyncedACTION_CHARGED,thenenv.step(nativeoracle/trace/render).NotAgent.act.',per_chooser_elapsed_measurements=False,per_trial_elapsed_measurements=False,fsync_duration_measurements=False,oracle_duration_measurements=False,hold_CPU60_wall75_are='RESERVATION_LIMITS_NOT_MEASUREMENTS',raw_clock_time_fields_are='SIMULATION_TIME_NOT_COMPUTATION_LATENCY',available_measured_scope='WHOLE_ARM_CPU_WALL_ONLY',candidate_arm_measured_CPU_s=r['arms'][1]['CPU_s'],candidate_arm_measured_wall_s=r['arms'][1]['wall_s'],episode_average_is_not_chooser_latency=True,no_subtraction_or_5s_pass_fail_inference=True,recorded_actual_feedback_calls=len(work),maximum_recorded_work_input=chosen,latency_rank_not_proven_by_work_rank=True,proposed_input_sha256=sha(D/'proposed-timing-input-private.json'))
 target=dict(current_native_raw=661,current_native_s=13.22,requested_target_s=11.99,arithmetic_gap_s=1.23,official_raw_at_or_below_target=599,official_attainable_target_s=11.98,required_official_gain_raw=62,required_official_gain_s=1.24,same_distance_average_speed_increase=13.22/11.99-1,no_verified_1point23_gain_reservoir=True,latency_optimization_is_not_physics_lap_gain=True)
 out=dict(study=599,status='READ_ONLY_ANALYSIS_COMPLETE',timing=timing,target=target,allocation=allocation,allocation_rule='Exactly578storedpathcurvature/proximity/35mrecoverypriority;nativeCOM/endpointsfromsavedraw,lookup/arithmeticonly. Fixedhold1..24categoryis1.92sbydefinition. Elapsedoccupancyisnotrecoverableloss.',classification578_reproduced=True,common_path_geometry_equal=True,common_progress_crossing_intervals=interval,crossing_time_scope='Projection-progresscrossingchordinterpolationDIAGNOSTIC;notnewworld-planeprojectionorofficialgain,categorychangesmayreflectsampling/policy/dynamics.',comparison_scope='598freshbaseline-vs-candidateiscontrollednativewholepolicybundle. 578source577-vs-598nativecandidatechangespolicyandbackend;deltaisnotmodelbias/fidelityloss.',COM_speed_max={k:max(q['speed'] for q in v) for k,v in data.items()},source_ticks=0,native_calls=0,new_chooser_calls=0,force_calls=0,geometry_evaluator_calls=0,solver_calls=0,policy_evaluations=0,HOLDOUT=0,SEALED=0,research_remaining=22211,reserve=84000,reserve_used=0,input_sha256=c['input_sha256'],private_sha256={p.name:sha(p) for p in D.glob('*.json')},read_CPU_s=time.process_time()-CPU+5,read_wall_s=time.perf_counter()-WALL+5,prior_preparation_charge_s=5)
 assert all(abs(sum(z['elapsed_s'] for z in x.values())-len(data[k])*.02)<1e-9 for k,x in allocation.items());save(G/'retry/decision599_analysis.json',out);print(json.dumps(dict(timing=timing,target=target,allocation={k:{z:v['elapsed_s'] for z,v in x.items()} for k,x in allocation.items()},intervals=interval,read_CPU_s=out['read_CPU_s'],read_wall_s=out['read_wall_s']),indent=2));signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
