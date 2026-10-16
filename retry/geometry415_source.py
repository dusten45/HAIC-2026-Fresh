"""H2 once-only source factorial after fixed static clearance gates; no native runs."""
import copy,datetime,json,math,os,signal,sys,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.branch401_gate import fingerprint
from retry.headroom413_run import Meter,Trace,row_fidelity,wheel_compare,hull_compare,metrics,signature
from retry.terminal410_model import from_actual_full,snapshot
from retry.terminal410_run import Controller,compare,rnghash,ModelFailure
from retry.executor397 import canonical_projection
from retry.cross404_common import executor
from retry.scalar392_audit import pedals
G=Path(__file__).resolve().parents[1]

def prepare(root):
 d=root/'stage415';assert read(d/'result.json')['status']=='GEOMETRY_PASS_SOURCE_GATE_PENDING';assert not(d/'source-plan.json').exists();base=read(d/'plan.json');patch=read(d/'patch-private.json');old=[json.loads(z) for z in (root/'stage413/actual_A/trace-private.jsonl').read_text().splitlines()];line=np.asarray(patch['old_line']);ds=np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1);sarc=np.r_[0,np.cumsum(ds)];start=sarc[patch['patch_start_node']];entry=next(i for i,z in enumerate(old) if z['post_projection']['arc']>=start)
 assert old[entry]['post_projection']['arc']>=start and old[entry]['pre']['time']<old[entry]['post']['time'];assert entry+13<=len(old)
 files=[Path(__file__),G/'retry/headroom413_run.py',G/'retry/terminal410_run.py',G/'retry/terminal410_model.py',G/'retry/cross404_common.py',G/'retry/closed411_run.py',root/'stage413/actual_A/trace-private.jsonl',root/'stage413/actual_A/initial-private.json',d/'plan.json',d/'result.json',d/'patch-private.json']
 p=dict(stage=415,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=base['deadline_utc'],entry_step=entry+1,prefix_actions=entry,entry_rule='Firstoldrecordwhosepostoriginalarcreachespatchstart; useitsstoredpreboundary strictlybeforepatchstart. No futurepedal/tire/timechoice.',H=13,exit_original_arc=patch['common_exit_original_arc'],progress_goal_m=3.24,progress_deadline_actions=13,order=['old_nominal','old_fullgas','new_nominal','new_fullgas'],repetitions=2,source_caps=base['source_if_geometry_pass'],gate='Firstrestore/prefix/nominalbody-wheel-hull/fidelity/mutation/independence/technicalfailure stopsall. Armfirstsafety/domain/progressdeadlinefailure censored; nofailedarmarrivalimputation. Eachfourarmindependentduplicatedfromsameparentstate/memory/RNG, ownfeedback. Firstfullgasactiononlynominalsteer gas1brake0. Originalreferencearcguard/progress/exit forallarms. Allfourvalidandexitreachedrequiredfornumericinteraction; noactual.',parent='PrefixmodelrestoredfromoldactualAinitial; preserve liveparent acrossbranches; recheckbodywheelhull snapshot/memory/RNG unchanged aftereach; oldnominalagainpostbranches thenadvanceparentone oldnominalcomparebranchfirststep+storedactual.',fidelity=read(root/'stage413/plan.json')['fidelity'],sources={str(f):sha(f) for f in files},protected=base['protected'],original408_preserve=base['original408_preserve'],supplement_correction='Static415originalsupplementusedgenericCdefault1.5nodes bymistake. CorrectexistingC268viaexecutor(fixed,frozen268). Originalstaticresultpreserved; correctiononlyalgebra, no world orrollout. Report signednegative sigma domainunqualified withoutfloor.')
 save(d/'source-plan.json',p);(d/'source-plan.sha256').write_text(sha(d/'source-plan.json')+'\n');save(d/'source-preparation-result.json',dict(implementation_wall_s=time.time()-read(d/'source-preparation-opening.json')['epoch'],implementation_CPU_s=None,CPU_fully_measured=False));print('source frozen',sha(d/'source-plan.json'),'entry',entry+1)

def corrected_algebra(root,fixed,pace):
 final=read(root/'stage414/final-private.json');h=final['physical']['hull'];pos=np.asarray(h['position']);vel=np.asarray(h['velocity']);speed=float(np.linalg.norm(vel));line=np.asarray(fixed['line']);q=canonical_projection(line,pos,vel,'FIRST_LAP');c=executor(fixed,pace);r,f=c._reference(q);i=final['controller']['index']%len(line);edge=line[(i+1)%len(line)]-line[i];u=float(np.clip((pos-line[i])@edge/(edge@edge),0,1));nodes=np.asarray(fixed['free_profile']['speed'])*pace;rO=float(np.sqrt((1-u)*nodes[i]**2+u*nodes[i+1]**2));fO=float((nodes[i+1]**2-nodes[i]**2)/(2*fixed['free_profile']['ds'][i]));O=fO+1.5*(rO-speed);C=f*q['sigma']/r+1.5*(r-speed)
 return dict(status='CORRECTED_EXISTING_C268_NODE_ADAPTER',supersedes='result.json stationary414_algebra genericC1.5nodecomparison',O=pedals(O,speed,fixed['model']),C_algebra=pedals(C,speed,fixed['model']),speed=speed,sigma=q['sigma'],O_target=rO,C_target=r,O_feed=fO,C_feed=f,same_segment=i==q['index'],same_nodes=True,stationary_symbolic_O=fO+1.5*rO,stationary_symbolic_C=1.5*r,negative_feed_term_O=fO,progress_scaled_feed_term_C=f*q['sigma']/r,negative_progress_domain_violation=q['sigma']<0,C_runtime_command_qualified=False,scope='Existingformulaonly. Tinysignednegative sigmaisnotrounded/clipped; existingexecutorwouldrejectnegativeprogress. Positivealgebra/zerobrakeisnotruntimeorprogress/safetyproof. No newrollout.')

def run(root):
 d=root/'stage415';p=read(d/'source-plan.json');assert sha(d/'source-plan.json')==(d/'source-plan.sha256').read_text().strip();assert not(d/'source-opening.json').exists()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 cpu=time.process_time();wall=time.perf_counter();meter=Meter(d);meter.phase_cpu=cpu;meter.phase_wall=wall;save(d/'source-opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));parent=None;status='RUNNING';error=None;branches={};checks=[];overhead={};independent={};parentcheck=None;stage='prefix';start_arc=start_time=None
 def timeout(*a):raise TimeoutError('sourceCPU30_wall60')
 prev={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,30);signal.setitimer(signal.ITIMER_REAL,60)
 try:
  fixed=read(root/'stage269/N1-plan-private.json');pace=np.asarray(read(root/'stage404/profiles-private.json')['frozen268']);patch=read(d/'patch-private.json');newfixed=copy.deepcopy(fixed);newfixed['line']=patch['new_line'];newfixed['free_profile']['ds']=patch['new_ds'];from retry.racing258_plan import curvature
  newfixed['free_profile']['curvature']=curvature(np.asarray(newfixed['line'])).tolist();line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);old=[json.loads(z) for z in (root/'stage413/actual_A/trace-private.jsonl').read_text().splitlines()];index=p['prefix_actions'];memory=dict(index=old[index]['memory_before']['index'],laststeer=old[index]['memory_before']['laststeer'],C=None);parent=meter.world(from_actual_full(read(root/'stage413/actual_A/initial-private.json')));tr=Trace(lambda:parent.t);prefix=[]
  for i,r in enumerate(old[:index]):
   tr.reset();tr.enable()
   try:q=meter.step(parent,np.asarray(r['command'],np.float32))
   finally:tr.disable()
   f=dict(predicted=q,tires=copy.deepcopy(tr.rows),raw_hull=copy.deepcopy(tr.hulls));z=row_fidelity(f,r)
   if not z['passed']:raise ModelFailure('prefixbodywheelhull:'+str(i+1))
   checks.append(z);prefix.append(f)
  save(d/'source-prefix-private.json',prefix);save(d/'prefix-qualification.json',dict(passed=True,actions=index,checks=checks));overhead['prefix']=tr.overhead();state=snapshot(parent);sh=fingerprint(state);mh=fingerprint(memory);rh=rnghash();start_arc=canonical_projection(line,list(parent.car.hull.position),list(parent.car.hull.linearVelocity),'FIRST_LAP')['arc'];start_time=parent.t
  assert start_arc<sum(fixed['free_profile']['ds'][:patch['patch_start_node']]);save(d/'source-entry-private.json',dict(state=state,memory=memory,start_arc=start_arc,start_time=start_time,prefix_actions=index,exit_original_arc=p['exit_original_arc']))
  def branch(label,conf,gas):
   m=meter.world(state);ctrl=Controller(conf,pace,'O',copy.deepcopy(memory));trace=Trace(lambda:m.t);rows=[];s=start_arc;previous=start_arc;goal=start_arc+3.24;deadline=13;hit=False;flags=[];domain=None;last_t=start_time;last_s=start_arc;arrival=None
   try:
    for k in range(13):
     if s>=goal:goal=s+3.24;deadline=k+13
     try:act=ctrl.act(m)
     except Exception as e:domain=type(e).__name__+': '+str(e);break
     if k==0 and gas:act=act.copy();act[1:]=[1.,0.]
     trace.reset();trace.enable()
     try:q=meter.step(m,act)
     finally:trace.disable()
     proj,why=metrics(q,trace.rows,trace.hulls,line,'FIRST_LAP');arc=proj['arc'];s+=(arc-previous+L/2)%L-L/2;previous=arc;reached=s>=goal or q['finished'];hit=hit or reached
     if k+1>=deadline and not reached:why.append('progress_deadline')
     # Arrival uses actualraw20ms andpostpoints inoriginalreferencearc only.
     samples=[(h['time'],canonical_projection(line,h['origin_position'],h['origin_linear_velocity'],'FIRST_LAP')['arc']) for h in trace.hulls]+[(q['time'],arc)]
     for t,arcpoint in samples:
      ps=start_arc+(arcpoint-start_arc+L/2)%L-L/2
      if arrival is None and last_s<p['exit_original_arc']<=ps:arrival=[last_t-start_time,t-start_time]
      last_t,last_s=t,ps
     rows.append(dict(offset=k+1,predicted=q,command=act.tolist(),progress=s,path_error_m=proj['path_error_m'],safety=why,tires=copy.deepcopy(trace.rows),raw_hull=copy.deepcopy(trace.hulls)));flags.extend(why)
     if why or q['terminal']:break
   finally:trace.disable();m.close()
   if fingerprint(snapshot(parent))!=sh or fingerprint(state)!=sh or fingerprint(memory)!=mh or rnghash()!=rh:raise ModelFailure('parent_input_memory_RNG_mutation')
   valid=len(rows)==13 and not flags and domain is None and hit
   z=dict(rows=rows,safety=sorted(set(flags)),domain=domain,goal_reached=hit,valid=valid,arrival_bracket_s=arrival if valid else None,exit_reached=valid and arrival is not None,final_progress_m=s-start_arc,controller_memory=ctrl.memory(),overhead=trace.overhead());save(d/(label+'-private.json'),z);overhead[label]=trace.overhead();return z
  stage='old_nominal';A=branch('old_nominal_1',fixed,False);checksNom=[row_fidelity(f,r) for f,r in zip(A['rows'],old[index:index+13])]
  if len(checksNom)!=13 or not all(z['passed'] for z in checksNom) or A['domain']:raise ModelFailure('nominalbodywheelhullfidelity')
  save(d/'nominal-qualification.json',dict(passed=True,checks=checksNom));A2=branch('old_nominal_2',fixed,False)
  if signature(A)!=signature(A2):raise ModelFailure('old_nominal_independentrepeat')
  branches['old_nominal']=A;independent['old_nominal']=True
  for label,conf,gas in [('old_fullgas',fixed,True),('new_nominal',newfixed,False),('new_fullgas',newfixed,True)]:
   stage=label;one=branch(label+'_1',conf,gas);two=branch(label+'_2',conf,gas)
   if signature(one)!=signature(two):raise ModelFailure(label+'_independentrepeat')
   branches[label]=one;independent[label]=True
  stage='postbranch_parent';A3=branch('old_nominal_post',fixed,False)
  if signature(A)!=signature(A3):raise ModelFailure('postbranch_nominal_changed')
  tr.reset();tr.enable()
  try:q=meter.step(parent,np.asarray(A['rows'][0]['command'],np.float32))
  finally:tr.disable()
  f=dict(predicted=q,tires=tr.rows,raw_hull=tr.hulls);z=row_fidelity(f,old[index]);first=A['rows'][0];bc=compare(q,old[index],None);wc=wheel_compare(tr.rows,first['tires']);hc=hull_compare(tr.hulls,first['raw_hull']);parentcheck=dict(passed=z['passed'] and bc['passed'] and wc['passed'] and hc['passed'],stored=z,body=bc,wheel=wc,hull=hc)
  if not parentcheck['passed']:raise ModelFailure('continuousparent_vsbranch')
  status='ALL_FOUR_SOURCE_QUALIFIED' if all(z['valid'] and z['exit_reached'] for z in branches.values()) else 'SOURCE_FACTORIAL_INELIGIBLE_CENSORED'
 except Exception as e:status='SOURCE_GATE_STOP';error=type(e).__name__+': '+str(e)
 finally:
  if parent:parent.close()
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
  for s,v in prev.items():signal.signal(s,v)
  meter.persist()
 arms={label:dict(valid=z['valid'],actions=len(z['rows']),safety=z['safety'],domain=z['domain'],goal_reached=z['goal_reached'],exit_reached=z['exit_reached'],arrival_bracket_s=z['arrival_bracket_s'],final_progress_m=z['final_progress_m'],max_path_error_m=max((r['path_error_m'] for r in z['rows']),default=None)) for label,z in branches.items()};interaction=None;gains=None
 if status=='ALL_FOUR_SOURCE_QUALIFIED':
  A,B,C,D=[arms[k]['arrival_bracket_s'] for k in p['order']];interaction=[D[0]-C[1]-B[1]+A[0],D[1]-C[0]-B[0]+A[1]];gains=dict(new_fullgas_vs_old_nominal=[A[0]-D[1],A[1]-D[0]],new_vs_old_nominal=[A[0]-C[1],A[1]-C[0]],new_vs_old_fullgas=[B[0]-D[1],B[1]-D[0]])
 # Read-only correction does not callact/world/step.
 acpu=time.process_time();awall=time.perf_counter();algebra=corrected_algebra(root,fixed,pace);algebra.update(CPU_s=time.process_time()-acpu,wall_s=time.perf_counter()-awall);save(d/'stationary414-corrected.json',algebra)
 result=dict(stage=415,status=status,last_stage=stage,error=error,arms=arms,independent_repeats=independent,parent_qualification=parentcheck,all_four_qualified=status=='ALL_FOUR_SOURCE_QUALIFIED',time_interaction_bracket_s=interaction,interaction_sign='(newgas-newnominal)-(oldgas-oldnominal); negative meansgasbenefitlargeronnewpath' if interaction is not None else None,gain_brackets_s=gains,failed_arm_time_imputed=False,source_only=True,new_native_actions=0,new_environment_resets=0,new_actor_learning_SEALED_reserve_paid=0,budget=meter.b,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,telemetry=overhead,stationary414_algebra=algebra,plan_sha256=sha(d/'source-plan.json'))
 save(d/'source-result.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['telemetry','parent_qualification']}))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
