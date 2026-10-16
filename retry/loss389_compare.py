"""Existing/new TRAIN diagnosis merges; no policy/env/model execution."""
import datetime,json,math,sys,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha,lines,analyze_case,projection,phases
G=Path(__file__).resolve().parent.parent

def new_case(root,key):
 f=root/'stage389/replay'/key;rr=lines(f/'trace-private.jsonl');g=read(f/'geometry-private.json');rows=[]
 for x in rr:
  s=x['pre'];rows.append(dict(step=x['step'],time=s['time'],pos=s['pos'],vel=s['vel'],angle=s['angle'],yaw=s['yaw'],joint=s['joint'],road_contacts=s['road_contacts'],visited=s['visited'],action=x['action'],features=x['features'],path=x['pixel_path'],direct=x['tracker']['direct'],collision=x['collision'],damage=x['damage']))
 return rows,read(f/'result.json'),np.asarray(g['line']),g['road_polygons'],[dict(center=o[:2],radius=o[2]) for o in g['obstacles']]

def candidate375(root,key,geometry):
 f=root/'stage375'/key/'B';rr=lines(f/'trace-private.jsonl');rows=[]
 for x in rr:
  s=x['pre_physical'];h=s['hull'];rows.append(dict(step=x['step'],time=s['actual_time'],pos=h['position'],vel=h['velocity'],angle=h['angle'],yaw=h['angular_velocity'],joint=[w['joint']['angle'] for w in s['wheels'][:2]],road_contacts=[len(w['tiles']) for w in s['wheels']],visited=s['unique_tiles'],action=x['executed'],features=x['features'],path=x['pixel_path'],direct=x['tracker']['direct'],collision=x['collision'],damage=x['damage']))
 g=geometry;return rows,read(f/'result.json'),np.asarray(g['line']),g['road_polygons'],[dict(center=o[:2],radius=o[2]) for o in g['obstacles']]

def milestone(rows,total,kind='visited'):
 out=[]
 for f in np.arange(.1,1,.1):
  threshold=int(math.ceil(f*total));x=next((x for x in rows if x[kind]>=threshold),None);out.append(None if x is None else float(x['t_from_start']))
 return out

def oracle(root,folder):
 f=root/folder;rr=read(f/'trajectory-private.json');result=read(f/'result.json');n=len(rr);dt=np.full(n,.08);dt[-1]=result['raw_step_ticks']/50-.08*(n-1);assert 0<dt[-1]<=.080001
 if result['completed']:dt=np.minimum(dt,np.maximum(0,result['lap_ms']/1000-np.arange(n)*.08))
 speed=np.array([x['speed_m_s'] for x in rr]);q=np.array([x['target_speed_m_s'] for x in rr]);action=np.array([x['action'] for x in rr]);visited=[dict(visited=x['visited'],t_from_start=float(min((i+1)*.08,result['raw_step_ticks']/50))) for i,x in enumerate(rr)]
 return dict(folder=folder,result={k:result.get(k) for k in ['completed','actual_DNF','censored','lap_ms','native_actions','damage','retire_reason','first_collision','first_large_error']},duration_s=float(dt.sum()),mean_speed_m_s=float(np.average(speed,weights=dt)),mean_target_m_s=float(np.average(q,weights=dt)),peak_speed_m_s=float(speed.max()),below_target_by10_s=float(dt[q-speed>10].sum()),brake_below_target_s=float(dt[(speed<q)&(action[:,2]>0)].sum()),gas_brake_overlap_s=float(dt[(action[:,1]>.05)&(action[:,2]>.05)].sum()),gas1_s=float(dt[action[:,1]>=.999999].sum()),mean_gas=float(np.average(action[:,1],weights=dt)),mean_brake=float(np.average(action[:,2],weights=dt)),max_path_error_m=max(x['path_error_m'] for x in rr),recorded_geometry_position_fields=any('position' in x or 'pos' in x for x in rr),coverage_milestone_rows=visited,rows=rr,dt=dt)

def run(root):
 d=root/'stage389';assert not(d/'comparison-plan.json').exists();start,cpu=time.perf_counter(),time.process_time();sources=[Path(__file__),G/'retry/loss389_analyze.py',d/'baseline-decomposition.json',d/'instrumentation-plan.json',d/'instrumentation-cost.json',root/'stage306/plan.json',root/'stage221/evaluation/plan.json',root/'stage258/plan.json',root/'stage265/plan.json',root/'stage267/plan.json',root/'stage269/plan.json',root/'stage308/plan.json']
 for key in ['N0','N1','N2']:sources += [d/'replay'/key/name for name in ['result.json','trace-private.jsonl','geometry-private.json','initial-scene-private.json','initial-RNG-private.json']]
 sources += [root/'stage375/N2/B'/name for name in ['result.json','trace-private.jsonl','initial-scene-private.json','initial-RNG-private.json']]
 folders=['stage258/O0_free','stage265/O0_1.5','stage265/N0_1.5','stage267/g2_p3','stage267/g1_p3','stage266/O0','stage308/O0','stage269/N1_baseline']
 folders=[x for x in folders if (root/x/'trajectory-private.json').exists()]
 for folder in folders:sources += [root/folder/name for name in ['result.json','trajectory-private.json']]
 for key in ['T2950','T2953','T2956','T2959','O0','O2']:sources += [root/'stage306/collection'/key/name for name in ['teacher-labels-private.json','teacher-receipts-private.json']]
 sources += [root/'stage258/O0-plan-private.json',root/'stage306/collection/O0/track-private.json']
 p221=read(root/'stage221/evaluation/plan.json');p306=read(root/'stage306/plan.json');teacher_runs=[]
 for key,ix in [('O0',0),('O2',2)]:
  case=p221['cases'][ix];assert (case['seed'],case['track_id'])==(p306['cases'][key]['seed'],p306['cases'][key]['track_id']);f=root/'stage221/evaluation/runs'/(case['id']+'__C')/'result.json';sources.append(f);teacher_runs.append((key,f))
 plan=dict(stage=389,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),native_cap=0,scope='KnownTRAIN existingGT/source/action/teacher plus3authorizedunchanged296replays only; no372failureorSEALED',alignment='N2 actualsameinitial375metadata/fullcapture/accessRNG checked; fullphase metrics bypreactionGT. O0GT258referencecursor nodes anduniquevisitedcoverage bands are distinct alignments, notsamevehicle state.',sources={str(p):sha(p) for p in sources});save(d/'comparison-plan.json',plan)
 base=read(d/'baseline-decomposition.json');normal={}
 for key in ['N0','N1','N2']:
  rows,r,line,pol,ob=new_case(root,key);s,n=analyze_case(key,rows,r,line,pol,ob);s['missing'][0]='Common pre-state window omits terminal chord; terminal post pose additionally recorded in389, not imputed at earlier finish-crossing time';base.append(s);normal[key]=n;save(d/(key+'-normalized-private.json'),n)
 geometry=read(d/'replay/N2/geometry-private.json');rows,r,line,pol,ob=candidate375(root,'N2',geometry);cs,cn=analyze_case('N2_candidate374',rows,r,line,pol,ob);save(d/'N2-candidate374-normalized-private.json',cn)
 initialproof=dict(captured_initial_physics_equal=read(d/'replay/N2/initial-scene-private.json')==read(root/'stage375/N2/B/initial-scene-private.json'),accessible_initial_rng_equal=read(d/'replay/N2/initial-RNG-private.json')==read(root/'stage375/N2/B/initial-RNG-private.json'),pixel_geometry_obstacle_hashes_equal=read(d/'replay/N2/reset-qualification.json')['initial_pixel_geometry_obstacle_hashes_match375'])
 b=next(x for x in base if x['case']=='N2');N=len(line);m1=milestone(normal['N2'],N);m2=milestone(cn,N)
 pair=dict(baseline=b,candidate=cs,initial_proof=initialproof,phase_time_candidate_minus_baseline_s={k:cs['phases'][k]['time_s']-b['phases'][k]['time_s'] for k in b['phases']},coverage_milestones=[dict(fraction=round((i+1)/10,1),baseline_t_s=x,candidate_t_s=y,delta_s=y-x if x is not None and y is not None else None) for i,(x,y) in enumerate(zip(m1,m2))],scope='Samecondition actualtwo legalpolicies, owntrajectories, notsinglecomponentcausalcomparison; fieldsinitial capture excludeshiddenwarmstartproof')
 oracles=[];o0base=read(d/'O0-normalized-private.json');N0=len(read(root/'stage306/collection/O0/track-private.json'));mb=milestone(o0base,N0)
 for folder in folders:
  x=oracle(root,folder);rr=x.pop('rows');dt=x.pop('dt');visit=x.pop('coverage_milestone_rows');key='N0' if '/N0' in folder else 'N1' if '/N1' in folder else 'O0';x['case']=key
  if key=='O0':
   mm=milestone(visit,N0);x['coverage_milestones']=[dict(fraction=round((i+1)/10,1),baseline296_t_s=a,oracle_t_s=b,delta_s=b-a if b is not None and a is not None else None) for i,(a,b) in enumerate(zip(mb,mm))]
  if folder=='stage258/O0_free':
   gp=read(root/'stage258/O0-plan-private.json');rawline=np.asarray(read(root/'stage306/collection/O0/track-private.json'))[:,2:4];center=np.asarray(gp['center']);assert rawline.shape==center.shape and np.max(abs(rawline-center))<1e-4;x['recorded_reference_center_maxdiff_m']=float(np.max(abs(rawline-center)));idx=np.array([r['road_progress_index'] for r in rr])%len(center);fake=projection(rawline,rawline[idx]);oarc=projection(rawline,np.array([z[:2] for z in read(d/'replay/N0/geometry-private.json')['obstacles']]))['arc'] if False else None
   # O0 obstaclepositions are from the frozen258plan materialization's baseline306 capture.
   import gzip
   with gzip.open(root/'stage306/collection/O0/full-source-captures-private.jsonl.gz','rt') as f0:truth=json.loads(next(f0))['snapshot']
   oarc=projection(rawline,np.array([z['body']['position'] for z in truth['obstacles']]))['arc'];phase=phases(fake,oarc,45);x['reference_cursor_phase_times_s']={k:float(sum(dt[i] for i,p in enumerate(phase) if p==k)) for k in ['straight','corner','obstacle_approach','post_obstacle','off_reference']};x['phase_scope']='Recorded plannedfreepath cursor-to-roadnode correspondence; actualGTposition missing, not matchedphysicalphase.'
   cuts=[]
   for frac in np.arange(.1,1,.1):
    node=int(math.ceil(frac*len(center)));br=next((v for v in o0base if v['segment']>=node),None);ii=next((i for i,r in enumerate(rr) if r['road_progress_index']>=node),None);cuts.append(dict(node_fraction=round(float(frac),1),baseline_first_node_t_s=br['t_from_start'] if br else None,oracle_reference_cursor_t_s=ii*.08 if ii is not None else None))
   x['node_crossing_observations']=cuts
  oracles.append(x)
 labels=[]
 for key in ['T2950','T2953','T2956','T2959','O0','O2']:
  data=read(root/'stage306/collection'/key/'teacher-labels-private.json');receipt=read(root/'stage306/collection'/key/'teacher-receipts-private.json');assert len(data)==len(receipt);a=np.array([x['base'] for x in data]);t=np.array([x['teacher'] for x in data]);err=abs(a[:,0]-t[:,0]);labels.append(dict(case=key,queries=len(data),teacher_first_steer_diff_fraction=float(np.mean(a[:,0]!=t[:,0])),mean_abs_first_steer_diff=float(err.mean()),max_abs_first_steer_diff=float(err.max()),mean_teacher_gas=float(t[:,1].mean()),mean_teacher_brake=float(t[:,2].mean()),mean_actual296_gas=float(a[:,1].mean()),mean_actual296_brake=float(a[:,2].mean()),teacher_simultaneous_positive_fraction=float(np.mean((t[:,1]>0)&(t[:,2]>0))),student_simultaneous_positive_fraction=float(np.mean((a[:,1]>0)&(a[:,2]>0))),source_initialization_flags_passed=all(x['initialization_all_exact'] for x in receipt),labels_apply_first_command_only=True,teacher_future_steering_not_executed_by_pedal_student=True))
 tr=[]
 for key,f in teacher_runs:
  x=read(f);tr.append(dict(case=key,completed=x['completed'],lap_ms=x['lap_ms'],damage=x['damage'],inputs=x['oracle_inputs_to_policy'],offline_GT_timing=x['offline_GT_timing'],official_timing_compliance_claim_allowed=x['official_timing_compliance_claim_allowed'],saved_trajectory_rows=x['saved_trajectory_rows']))
 for f,h in plan['sources'].items():assert sha(f)==h,f
 report=dict(stage=389,baseline_cases=base,legal_faster_N2_comparison=pair,privileged_oracles=oracles,teacher221_actual_same_TRAIN=tr,teacher306_label_conditions=labels,missing='Oracle265/267/308lackactualpose/cursor fields; uniquevisitedbands not exactsamephysicalsegment. GT258cursor correspondence approximatewithoutactualpose. No causal time allocation, force saturation/counterfactuals measured389.',cost=dict(analysis_wall_s=time.perf_counter()-start,analysis_CPU_s=time.process_time()-cpu,new_native=0,new_actor=0,new_model_or_world=0))
 save(d/'comparison-summary.json',report);print(json.dumps(dict(N2_pair={k:v for k,v in pair.items() if k not in ['baseline','candidate']},oracles=[{k:v for k,v in o.items() if k not in ['coverage_milestones','node_crossing_observations']} for o in oracles],teacher_labels=labels,teacher_actual=tr),ensure_ascii=False),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
