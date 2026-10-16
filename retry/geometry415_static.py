"""One frozen H2 Hermite geometry qualification; no environment or model rollout."""
import collections,datetime,json,math,signal,sys,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.racing258_plan import curvature
from retry.scalar392_audit import pedals
from retry.executor397 import canonical_projection

G=Path(__file__).resolve().parents[1]
def prepare(root):
 d=root/'stage415';assert not(d/'plan.json').exists();old=read(root/'stage414/plan.json');v=read(root/'project-effective-budget-v434.json');assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(29880,84000,0)
 files=[Path(__file__),G/'retry/racing258_plan.py',G/'retry/executor397.py',G/'retry/scalar392_audit.py',G/'retry/hypotheses412_plan.md',root/'stage412/design.json',root/'stage269/N1-plan-private.json',root/'stage404/profiles-private.json',root/'stage413/source-anchor-private.json',root/'stage414/final-private.json',root/'stage414/trace-private.jsonl',root/'project-effective-budget-v434.json',root/'research-deadline-current.json']
 for f,h in {**old['protected'],**old['original408_preserve']}.items():assert sha(f)==h
 p=dict(stage=415,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(root/'research-deadline-current.json')['deadline_utc'],selection='Original node arc fraction in[.30,.50], largest abs(k_i-k_(i-1)), existing258 threepoint signedcurvature; exactties earliestnode. Patch nodes j-2..j+2, foursegments. No outcome/tire/speed selection.',patch='One cubicHermite endpoints oldj-2,j+2, endpointunit tangents normalized central secants old(p[a+1]-p[a-1]) andold(p[b+1]-p[b-1]); derivatives equal unit tangent timesoriginalfoursegmentlength. Five samples atoldnormalizedarc fractions. Onlythreeinteriornodeschange.',speed='Keep frozen268 runtime speed nodes indexedtocorrespondingoriginalnode, no new speedsolver/profile/pace. New ds=Euclideannewsegmentlength andnew curvature=258threepoint forgeometry; feed=(oldruntimev[i+1]^2-oldruntimev[i]^2)/(2newds[i]). Neveruseold ds withnewpath.',geometry_gates='Allfinitepositive ds, no new nonadjacentsegmentcrossing; rawroadquads edge cancellation exact floatvertices (counts1or2only) withboundarydegree2; footprint boundingrectangle ±1.75lateral ±2.9longitudinal includes .35roadlateral/.25longitudinal margins overactualhull/wheelsteeringenvelope. At .025m max translation and .005rad max heading samples, road/obstacle clearance must exceed sweptmotion bound: max(.0125, hypot(1.75,2.9)*.0025)+1e-6. Entirefootprint boundary vsroadboundary exactsegments, center insideunion. Fornodeheadingturn includeallintermediateheadings. Extraobstacle margin .25. Originalpathguard<=3m, samplecertifiedviaLipschitz .0125. Checkchangedfoursegments plusoneunchangedneighbor oneachside; diagnosticoldcomparisons samewindow. Curvaturetransition max absadjacentcurvaturejump overa-1..b+1 must strictlydecreaseby>1e-12; no steeringcurvature increaseabove tan(.4)/3.24. Firstfailedgate closespatchwithoutrepair/search.',source_if_geometry_pass=dict(ticks=4096,worlds=64,CPU_s=30,wall_s=60,max_parallel=1,scope='Storedentrybeforepatch, oldprefix/nominalbody+wheel/rawhullfidelity, restore/isolation/parentRNG gates. Independentrepeat old/newpath xnominal/fullgasfirst, 13actions each, originalarc patchend+10m exit, 3.24m/13progress and413safety. Interpret timeinteraction onlyallfourqualified; neverimputefailedarmtime. Noactual.'),static_caps=dict(CPU_s=30,wall_s=60,max_parallel=1),new_native_actor_learning_SEALED_reserve_paid_cap=0,static414='Evaluate existing O feed+1.5(r-v), existing C feed*(sigma/r)+1.5(r-v) atrecordedfinalstate withownexistingCnodes/canonicalprojection, reportcursoralignment andno rollout. Do notinventnewformula.',sources={str(f):sha(f) for f in files},protected=old['protected'],original408_preserve=old['original408_preserve'])
 save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'preparation-result.json',dict(implementation_wall_s=time.time()-read(d/'preparation-opening.json')['epoch'],implementation_CPU_s=None,CPU_fully_measured=False,new_native_model=0));print('415 frozen',sha(d/'plan.json'))

def pointseg(p,a,b):
 v=b-a;u=np.clip(np.sum((p-a)*v,axis=-1)/np.sum(v*v,axis=-1),0,1);return np.linalg.norm(p-a-u[...,None]*v,axis=-1)
def segdist(a,b,c,d):
 # Supports broadcasting: distance of closed 2D segments, including crossings.
 cross=lambda u,v:u[...,0]*v[...,1]-u[...,1]*v[...,0]
 v=b-a;w=d-c;z=c-a;den=cross(v,w);ok=abs(den)>1e-14;s=np.divide(cross(z,w),den,out=np.zeros_like(den),where=ok);t=np.divide(cross(z,v),den,out=np.zeros_like(den),where=ok)
 dist=np.minimum.reduce([pointseg(a,c,d),pointseg(b,c,d),pointseg(c,a,b),pointseg(d,a,b)])
 return np.where(ok&(s>=0)&(s<=1)&(t>=0)&(t<=1),0,dist)
def inside(p,quads):
 v=np.roll(quads,-1,axis=1)-quads;w=p-quads;z=v[:,:,0]*w[:,:,1]-v[:,:,1]*w[:,:,0];return bool(np.any(np.all(z>=-1e-9,axis=1)|np.all(z<=1e-9,axis=1)))
def run(root):
 d=root/'stage415';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert not(d/'opening.json').exists()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 cpu=time.process_time();wall=time.perf_counter();save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 def timeout(*args):raise TimeoutError('staticCPU30_wall60')
 prev={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,30);signal.setitimer(signal.ITIMER_REAL,60)
 result={};error=None
 try:
  assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00'))
  fixed=read(root/'stage269/N1-plan-private.json');line=np.asarray(fixed['line']);N=len(line);ds=np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1);sarc=np.r_[0,np.cumsum(ds)];k=curvature(line);pool=np.flatnonzero((sarc[:-1]/sarc[-1]>=.3)&(sarc[:-1]/sarc[-1]<=.5));j=int(pool[np.argmax(abs(k[pool]-k[(pool-1)%N]))]);a=j-2;b=j+2;length=sum(ds[a:b]);u=(sarc[a:b+1]-sarc[a])/length
  tang=[]
  for i in [a,b]:v=line[i+1]-line[i-1];tang.append(v/np.linalg.norm(v))
  def hermite(t):
   t=np.asarray(t)[:,None];return (2*t**3-3*t**2+1)*line[a]+(t**3-2*t**2+t)*length*tang[0]+(-2*t**3+3*t**2)*line[b]+(t**3-t**2)*length*tang[1]
  new=line.copy();new[a:b+1]=hermite(u);new[a]=line[a];new[b]=line[b];nd=np.linalg.norm(np.roll(new,-1,axis=0)-new,axis=1);nk=curvature(new);runtime=np.asarray(fixed['free_profile']['speed'])*np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);feed=np.diff(runtime**2)/(2*nd)
  save(d/'patch-private.json',dict(selected_node=j,patch_start_node=a,patch_end_node=b,old_line=line.tolist(),new_line=new.tolist(),sample_u=u.tolist(),new_ds=nd.tolist(),corresponding_runtime_speed=runtime.tolist(),new_feed=feed.tolist(),common_exit_original_arc=float(sarc[b]+10),selected_fraction=float(sarc[j]/sarc[-1])))
  gates=[]
  def gate(name,passed,**kw):gates.append(dict(name=name,passed=bool(passed),**kw));return bool(passed)
  finite=gate('finite_positive_ds',np.isfinite(new).all() and np.all(nd>0));assert finite
  cross=[]
  for i in range(a,b):
   for z in range(N):
    if z in [i,(i-1)%N,(i+1)%N]:continue
    if segdist(new[i],new[(i+1)%N],new[z],new[(z+1)%N])<=1e-10:cross.append([i,z])
  selfok=gate('no_nonadjacent_crossing',not cross,crossings=len(cross))
  physical=read(root/'stage413/source-anchor-private.json')['state']['physical'];quads=np.asarray([x['fixture']['geometry']['vertices'] for x in physical['roads']]);edges=collections.Counter()
  for q in quads:
   for x,y in zip(q,np.roll(q,-1,axis=0)):edges[tuple(sorted((tuple(x),tuple(y))))]+=1
  boundary=[edge for edge,n in edges.items() if n==1];degree=collections.Counter(x for edge in boundary for x in edge);topology=gate('road_boundary_topology',all(n in [1,2] for n in edges.values()) and all(n==2 for n in degree.values()),boundary_edges=len(boundary),max_edge_multiplicity=max(edges.values()))
  ba=np.asarray([z[0] for z in boundary]);bb=np.asarray([z[1] for z in boundary]);obs=np.asarray([z['body']['position'] for z in physical['obstacles']]);rad=np.asarray([z['fixture']['radius'] for z in physical['obstacles']]);radius=math.hypot(1.75,2.9);bound=max(.0125,radius*.0025)+1e-6;shape=np.asarray([[-1.75,-2.9],[1.75,-2.9],[1.75,2.9],[-1.75,2.9]])
  def corridor(path):
   poses=[]
   for i in range(a-1,b+1):
    vec=path[i+1]-path[i];le=np.linalg.norm(vec);theta=math.atan2(-vec[0],vec[1]);steps=math.ceil(le/.025)
    poses.extend((path[i]+z*vec,theta) for z in np.linspace(0,1,steps+1))
    if i<b:
     v2=path[i+2]-path[i+1];t2=math.atan2(-v2[0],v2[1]);delta=(t2-theta+math.pi)%(2*math.pi)-math.pi
     poses.extend((path[i+1],theta+x*delta) for x in np.linspace(0,1,max(1,math.ceil(abs(delta)/.005))+1))
   roadmin=obmin=math.inf;allinside=True;guard=0.
   for pt,theta in poses:
    co=math.cos(theta);si=math.sin(theta);rot=np.asarray([[co,-si],[si,co]]);v=shape@rot.T+pt;vn=np.roll(v,-1,axis=0)
    road=float(np.min(segdist(v[:,None,:],vn[:,None,:],ba[None,:,:],bb[None,:,:])));on=inside(pt,quads);allinside=allinside and on;roadmin=min(roadmin,road if on else -road)
    od=np.min(pointseg(obs[None,:,:],v[:,None,:],vn[:,None,:])-rad[None,:]-.25)
    # Obstacle entirely inside rectangle must count as intrusion too.
    oblocal=(obs-pt)@rot;intrude=(abs(oblocal[:,0])<=1.75)&(abs(oblocal[:,1])<=2.9)
    if np.any(intrude):od=min(od,-float(np.max(rad[intrude]))-.25)
    obmin=min(obmin,float(od));guard=max(guard,float(np.min(pointseg(pt,line,np.roll(line,-1,axis=0)))))
   return dict(poses=len(poses),road_clearance_m=roadmin,road_inside=allinside,obstacle_clearance_after_extra_margin_m=obmin,original_path_sample_max_distance_m=guard,motion_bound_m=bound,road_pass=allinside and roadmin>bound,obstacle_pass=obmin>bound,guard_pass=guard+.0125<=3)
  # One geometry qualification computes all static diagnostics; no repaired alternative.
  corr=corridor(new);oldcorr=corridor(line)
  roadok=gate('road_footprint_clearance',corr['road_pass'],minimum_m=corr['road_clearance_m'],required_motion_bound_m=bound)
  obsok=gate('obstacle_footprint_clearance',corr['obstacle_pass'],minimum_after_extra_margin_m=corr['obstacle_clearance_after_extra_margin_m'])
  guardok=gate('original_path_3m_guard',corr['guard_pass'],sample_max_m=corr['original_path_sample_max_distance_m'],certificate_upper_m=corr['original_path_sample_max_distance_m']+.0125)
  ix=np.arange(a-1,b+2);oldjump=float(max(abs(k[ix]-k[ix-1])));newjump=float(max(abs(nk[ix]-nk[ix-1])));curveok=gate('curvature_transition_decrease',newjump<oldjump-1e-12,old_max_adjacent_jump=oldjump,new_max_adjacent_jump=newjump)
  steerok=gate('steering_curvature_bound',max(abs(nk[ix]))<=math.tan(.4)/3.24,new_max_abs_curvature=float(max(abs(nk[ix]))),limit=math.tan(.4)/3.24)
  result=dict(stage=415,status='GEOMETRY_PASS_SOURCE_GATE_PENDING' if all(z['passed'] for z in gates) else 'GEOMETRY_REJECTED_NO_SOURCE',selected_fraction=float(sarc[j]/sarc[-1]),patch_segments=4,changed_nodes=3,patch_length_old_m=float(length),patch_length_new_m=float(sum(nd[a:b])),gates=gates,first_failed_gate=next((z['name'] for z in gates if not z['passed']),None),new_corridor=corr,old_corridor_diagnostic=oldcorr,source_2x2_executed=False,numeric_time_interaction=None,promotion=False,H1_whole_rejected=False,H2_whole_rejected=False,new_wrapper_actions=0,new_environment_resets=0,new_model_ticks=0,new_worlds=0,new_actor_learning_SEALED_reserve_paid=0)
  # Independent supplemental algebra only: exact existing O and C laws at stored414 finalstate.
  final=read(root/'stage414/final-private.json');ph=final['physical'];h=ph['hull'];pos=np.asarray(h['position']);vel=np.asarray(h['velocity']);speed=float(np.linalg.norm(vel));index=final['controller']['index'];i=index%N;edge=line[(i+1)%N]-line[i];fu=float(np.clip((pos-line[i])@edge/(edge@edge),0,1));rO=float(np.sqrt((1-fu)*runtime[i]**2+fu*runtime[i+1]**2));fO=float(np.diff(runtime**2)[i]/(2*ds[i]));q=canonical_projection(line,pos,vel,'FIRST_LAP');jC=q['index'];uC=q['u'];nodesC=np.asarray(fixed['free_profile']['speed'])*1.5;rC=float(np.sqrt((1-uC)*nodesC[jC]**2+uC*nodesC[jC+1]**2));fC=float(np.diff(nodesC**2)[jC]/(2*ds[jC]));rawO=fO+1.5*(rO-speed);rawC=fC*(q['sigma']/rC)+1.5*(rC-speed)
  result['stationary414_algebra']=dict(recorded_final_speed=speed,O_cursor_index=i,O_u=fu,O_target=rO,O_feed=fO,O=pedals(rawO,speed,fixed['model']),C_projection_index=jC,C_u=uC,C_target=rC,C_feed=fC,C_sigma=q['sigma'],C=pedals(rawC,speed,fixed['model']),same_segment=(i==jC),same_speed_nodes=bool(np.array_equal(runtime,nodesC)),progress_scaled_negative_feed_removed=(rawO<0 and rawC>0),scope='ExistingO268 vs existingCexecutor ownnodes/projection, stationarysavedstate only. C memory/runtime domain notqualified; notnewtrajectory/safety/progress/fullrun evidence.')
 except Exception as e:error=type(e).__name__+': '+str(e);result.update(stage=415,status='STATIC_TECHNICAL_STOP',error=error,source_2x2_executed=False,new_wrapper_actions=0,new_model_ticks=0)
 finally:
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,v in prev.items():signal.signal(s,v)
 result.update(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,plan_sha256=sha(d/'plan.json'));save(d/'result.json',result);print(json.dumps(result))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
