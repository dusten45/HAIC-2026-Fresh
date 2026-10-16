"""Conditional four-arm source-model diagnostic with fixed six-candidate control."""
import datetime,json,math,sys,time,signal,traceback
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from retry.numeric401_audit import read,save,sha
from retry.branch401_gate import Meter,snapshot,fingerprint,compare
from retry.executor397 import CoherentExecutor,canonical_projection
from retry.probe390_run import control_code
from retry.fork394_run import ForkTrace
G=Path(__file__).resolve().parent.parent
class QualificationFailure(RuntimeError):pass

def sensor(m,t):
 c=m.car;h=c.hull
 return dict(time=t,pos=list(h.position),vel=list(h.linearVelocity),speed=math.hypot(*h.linearVelocity),angle=float(h.angle),yaw=float(h.angularVelocity),joint=[float(w.joint.angle) for w in c.wheels],road_contacts=[len(w.tiles) for w in c.wheels])
def metrics(m,q,line,phase,initial_damage,grass):
 z=canonical_projection(line,q['position'],q['velocity'],phase);bodyforward=float(np.asarray(q['velocity'])@np.array([-math.sin(q['angle']),math.cos(q['angle'])]));flags=[]
 if z['path_error_m']>3:flags.append('path_error_over3m')
 if q['damage']>initial_damage:flags.append('damage_increase')
 if q['collision']:flags.append('collision')
 if q['wheel_road_contacts']<4 or grass:flags.append('wheel_road_loss_or_grass')
 if z['sigma']<-.1 or bodyforward<-.1:flags.append('meaningful_reverse')
 return dict(arc=z['arc'],path_error=z['path_error_m'],abs_yaw=abs(q['angular_velocity']),speed=q['speed_m_s'],flags=flags)
def prepare(root):
 d=root/'stage401';assert read(d/'numeric-result.json')['numeric_passed'] and read(d/'branch-result.json')['passed'];assert not(d/'factorial-plan.json').exists();p398=read(root/'stage398/plan.json')
 p=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),arms=[dict(name='P15_C',pace=1.5,joint=False),dict(name='P10_C',pace=1.,joint=False),dict(name='P15_J',pace=1.5,joint=True),dict(name='P10_J',pace=1.,joint=True)],case='N1',max_actions_per_arm=160,target_arc=read(root/'stage398/analysis.json')['cases'][1]['failure_arc_m'],preserve='Originalfixedplan/sourceprofile/physicsfiles unchanged. Perarmnewcontrollernodes areoriginalspeed*registeredpace. PursuitASTownstateandnominalpersistentmemory, originalgainclamps/map. Jointdoesnotoverwritepursuitlaststeermemory. Explicitlaunchphase unchanged;no finishclaim.',candidates='Orderedsteer[pursuit,negativefrontmeanjoint,0] x pedals[nominal,coast]; float32 originalbounds. Safetyinvalidcandidatesexcluded; choose(patherror,absyaw,-arcdelta,index). Ifallunsafe/unqualified stoparm. No extra candidates/fallback.',qualification='Eachcandidatefreshsnapshotmustinitialbody/tile/progressmatch;parentsnapshot/inputimmutable. Chosenpredictionvscontinuousparent actualstep mustpass391speed/yaw/position+discretecriteria. FirstfailurestopsALLremainingarms andmarksmodelcomparisonunqualified.',stops='Eacharmstoponsafetyflag or targetarc reached or160cap; sharedqualification/source/domain/technical/resource/deadlinefailurestopsall. Targetreachedwithsafetyfails. Nonreachingarmcensorednotpass. NoactualenvironmentDNF.',readout='Same399/400commonarc,time(.08s),error(.1m)criteria. Model-only;nonidentificationallowed.',sources={str(f):sha(f) for f in [Path(__file__),G/'retry/branch401_gate.py',G/'retry/executor397.py',G/'retry/pace265_run.py',G/'retry/probe390_run.py',G/'retry/fork394_run.py',G/'retry/source_vehicle_transition.py',Path(p398['fixed_plans']['N1']),root/'stage398/N1/initial-private.json',d/'numeric-result.json',d/'branch-result.json',d/'plan.json']},fixed_plan=p398['fixed_plans']['N1'])
 save(d/'factorial-plan.json',p);print('Fixed factorial preregistered after both qualification gates')
def run(root):
 d=root/'stage401';p=read(d/'factorial-plan.json');assert not(d/'factorial-opening.json').exists()
 for f,h in p['sources'].items():assert sha(f)==h,f
 save(d/'factorial-opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));meter=Meter(d);fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);prof=fixed['free_profile'];ds=np.asarray(prof['ds']);curve=np.asarray(prof['curvature']);sarc=np.r_[0,np.cumsum(ds)];results=[];error=None;qualification=None;active=[];observer=ForkTrace();code,astsha=control_code(G/'retry/pace265_run.py');initial=read(root/'stage398/N1/initial-private.json')['physical'];status='RUNNING';start_cpu=time.process_time();start_wall=time.perf_counter()
 def timeout(*args):raise TimeoutError('401totalCPU180')
 oldsig=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,max(.01,179-meter.basecpu))
 try:
  for arm in p['arms']:
   meter.guard();m=meter.world(initial);active.append(m)
   if not all([m.initial_bodies_exact,m.initial_tiles_exact,m.initial_progress_exact]):raise QualificationFailure('Arm_initialization')
   policy=CoherentExecutor(fixed);policy.nodes=np.asarray(prof['speed'])*arm['pace'];scope=dict(line=line,vprof=np.asarray(prof['speed']),ds=ds,curvature=curve,sarc=sarc,L=sarc[-1],model=fixed['model'],index=0,laststeer=0.,pace=arm['pace'],env=SimpleNamespace(unwrapped=m));rows=[];reason='ACTION_CAP_CENSORED';initial_damage=m.damage.damage
   for step in range(1,161):
    meter.guard();t=initial['actual_time']+(step-1)*.08;pre=sensor(m,t);exec(code,dict(np=np),scope);nominal,ref=policy.act(pre,scope['action'],{},scope['arc']);preq=ref['projection']
    if preq['path_error_m']>3 or any(n<=0 for n in pre['road_contacts']):reason='PRE_SAFETY_STOP';break
    chosen=nominal;prediction=None;candidate_summary=[]
    if arm['joint']:
     ss=snapshot(m,t);unchanged=fingerprint(ss);joint=float(np.mean([w.joint.angle for w in m.car.wheels[:2]]));aa=[np.asarray([a,*b],np.float32) for a in [nominal[0],np.clip(-joint,-.4,.4),0.] for b in [nominal[1:],[0.,0.]]];valid=[]
     for idx,a in enumerate(aa):
      branch=meter.world(ss);active.append(branch)
      if not all([branch.initial_bodies_exact,branch.initial_tiles_exact,branch.initial_progress_exact]):raise QualificationFailure(f'Candidate_initialization_arm{arm["name"]}_step{step}_candidate{idx}')
      observer.rows=[];observer.enable()
      try:pred=meter.step(branch,a)
      finally:observer.disable()
      met=metrics(branch,pred,line,policy.phase,initial_damage,any(s['grass'] for s in observer.rows));branch.close();active.remove(branch)
      if fingerprint(ss)!=unchanged or fingerprint(snapshot(m,t))!=unchanged:raise QualificationFailure('Candidate_parent_or_input_mutation')
      candidate_summary.append(dict(index=idx,metrics=met))
      if not met['flags']:valid.append(((met['path_error'],met['abs_yaw'],-(met['arc']-preq['arc']),idx),idx,pred))
     if not valid:reason='ALL_CANDIDATES_UNSAFE';break
     _,idx,prediction=min(valid,key=lambda z:z[0]);chosen=aa[idx]
    observer.rows=[];observer.enable()
    try:q=meter.step(m,chosen)
    finally:observer.disable()
    met=metrics(m,q,line,policy.phase,initial_damage,any(s['grass'] for s in observer.rows));record=dict(step=step,elapsed_post_s=step*.08,arc=met['arc'],path_error=met['path_error'],yaw_abs=met['abs_yaw'],speed=met['speed'],safety_flags=met['flags'],candidate_summary=candidate_summary)
    if prediction is not None:
     cmp=compare(prediction,q);record['chosen_prediction_vs_parent']=cmp
     if not cmp['passed']:
      rows.append(record);save(d/(arm['name']+'-rows-private.json'),rows);raise QualificationFailure(f'Chosen_branch_prediction_mismatch_arm{arm["name"]}_step{step}: {cmp}')
    rows.append(record);save(d/(arm['name']+'-rows-private.json'),rows)
    if met['flags']:reason='MODEL_SAFETY_STOP';break
    if met['arc']>=p['target_arc']:reason='TARGET_ARC_REACHED';break
   results.append(dict(arm=arm['name'],pace=arm['pace'],joint=arm['joint'],status=reason,actions=len(rows),target_reached=bool(rows and rows[-1]['arc']>=p['target_arc']),safe_target=reason=='TARGET_ARC_REACHED',max_path_error=max([r['path_error'] for r in rows] or [preq['path_error_m']]),arrival_interval_s=[(len(rows)-1)*.08,len(rows)*.08] if reason=='TARGET_ARC_REACHED' else None,max_abs_yaw=max([r['yaw_abs'] for r in rows] or [abs(pre['yaw'])]),diagnostic_only=True));m.close();active.remove(m);save(d/'factorial-progress.json',dict(results=results,budget=meter.b))
  status='COMPLETED_MODEL_DIAGNOSTIC'
 except QualificationFailure as e:qualification=str(e);status='STOPPED_AT_QUALIFICATION_FAILURE'
 except BaseException as e:error=type(e).__name__+': '+str(e);status='TECHNICAL_STOP';save(d/'factorial-error-private.json',dict(error=error,traceback=traceback.format_exc()))
 finally:
  observer.disable();signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,oldsig)
  for m in active:m.close()
  meter.persist()
 x=dict(status=status,qualification_failure=qualification,technical_error=error,results=results,uncompleted_arms=[a['name'] for a in p['arms'] if a['name'] not in [r['arm'] for r in results]],budget=meter.b,CPU_this_phase_s=time.process_time()-start_cpu,wall_this_phase_s=time.perf_counter()-start_wall,actual_environment_performance=False);save(d/'factorial-result.json',x);print(json.dumps(x,ensure_ascii=False))
if __name__=='__main__':
 root=Path(sys.argv[2]);(prepare if sys.argv[1]=='prepare' else run)(root)
