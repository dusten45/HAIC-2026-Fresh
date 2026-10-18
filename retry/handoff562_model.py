"""Two preregistered suffixes from exact same altered561 handoff; native cap0."""
import copy,datetime,json,math,signal,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.clip561_core import atomic_write,plain
from retry.plan513_model import load_root
from retry.closure524_control import tick as source_tick
from retry.speed516_control import force_rows
from retry.corner515_model import margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
from retry.drive519_control import project,reference
from retry.lap518_finish import hull_pose,tracker_for
from core.finish_line import FinishLineTracker
import retry.structure537_control as tracking

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response562-private')
rd=lambda p:json.loads(p.read_text())
import hashlib
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canonical=lambda x:json.loads(json.dumps(plain(x)))
def short(root):
 z=asdict(root);z.pop('roads');return z
INPUTS=[Path('/workspace/haic-response515-private/collected-map-state-private.json'),Path('/workspace/haic-response551-private/frozen-paths-private.json'),Path('/workspace/haic-response551-private/cold-candidate-private.json'),Path('/workspace/haic-response519-private/model-ledger-private.json'),Path('/workspace/haic-response560-private/segment-private.json'),Path('/workspace/haic-response561-private/branch-00-00-private.json')]
SOURCES=['retry/handoff562_model.py','retry/clip561_core.py','retry/structure537_control.py','retry/preview527_control.py','retry/lap518_finish.py','core/finish_line.py','retry/closure524_control.py','retry/plan512_control.py','retry/brake504_planar.py','retry/brake502_response.py','retry/plan513_model.py','retry/corner515_model.py','retry/lap518_control.py','retry/speed516_control.py']
CAPS=dict(preparation=dict(model_ticks=300,force=1200,geometry=300,CPU_s=20,wall_s=30),fixed=dict(model_ticks=1000,force=5000,geometry=1100,CPU_s=30,wall_s=45),feedback=dict(model_ticks=130000,force=600000,geometry=145000,CPU_s=1800,wall_s=2100),verification=dict(model_ticks=2500,force=12000,geometry=2600,CPU_s=60,wall_s=90))

class Phase:
 def __init__(self,study,name):self.s=study;self.name=name;self.limits=CAPS[name];self.counter=[0];self.cost=dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0,body_checks=0,max_all_model_body=0.);self.current=None
 def __enter__(self):
  atomic_write(D/f'{self.name}-STARTED.json',dict(contract_sha256=sha(G/'retry/handoff562_contract.json')));self.cpu,self.wall=time.process_time(),time.perf_counter();signal.signal(signal.SIGPROF,self.guard);signal.setitimer(signal.ITIMER_PROF,self.limits['CPU_s']);signal.signal(signal.SIGALRM,self.guard);signal.setitimer(signal.ITIMER_REAL,self.limits['wall_s']);return self
 def guard(self,*_,reserve=0):
  if self.counter[0]>self.limits['model_ticks'] or self.cost['force_evaluations']+reserve>self.limits['force'] or self.cost['geometry_checks']>self.limits['geometry']:raise RuntimeError('PHASE_WORK_CAP:'+self.name)
  if time.process_time()-self.cpu>=self.limits['CPU_s'] or time.perf_counter()-self.wall>=self.limits['wall_s']:raise RuntimeError('PHASE_TIME_CAP:'+self.name)
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.s.contract['deadline_utc']):raise RuntimeError('DEADLINE')
 def tick(self,root,gas,brake,index,counter):
  self.guard()
  if counter[0]>=self.limits['model_ticks']:raise RuntimeError('PHASE_MODEL_CAP')
  after=source_tick(root,gas,brake,index,counter);body=max(math.hypot(*hull_pose(after)[1]),*(math.hypot(*(after.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in after.planar.linear.wheels));self.cost['body_checks']+=1;self.cost['max_all_model_body']=max(self.cost['max_all_model_body'],body)
  if not math.isfinite(body) or body>=100:
   atomic_write(D/f'{self.name}-body-domain-private.json',dict(root=short(after),body=body));raise RuntimeError('MODEL_BODY_DOMAIN')
  return after
 def force(self,root,action):
  self.guard(reserve=4);return force_rows(root,action)
 def geometry(self,root):
  self.guard()
  if self.cost['geometry_checks']>=self.limits['geometry']:raise RuntimeError('PHASE_GEOMETRY_CAP')
  self.cost['geometry_checks']+=1;return margin(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles'])
 def snapshot(self,label):
  z=dict(self.cost,model_ticks=self.counter[0],internal_wheel_force_evaluations=4*self.counter[0],CPU_s=time.process_time()-self.cpu,wall_s=time.perf_counter()-self.wall);atomic_write(D/f'{self.name}-cost-ledger-private.json',dict(label=label,current=self.current,cost=z),True);return z
 def __exit__(self,typ,exc,tb):
  signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);z=self.snapshot('phase-finally-FIRST');z['error']=str(exc) if exc else None;self.s.phase_costs[self.name]=z;atomic_write(G/f'retry/handoff562_{self.name}_cost.json',z);return False

class Study:
 def __init__(self):
  D.mkdir(mode=0o700,exist_ok=False);self.phase_costs={};self.static,self.paths,self.saved,self.ledger,self.segment,self.candidate=map(rd,INPUTS);self.index=bounds(self.static['root']['roads']);self.edge=boundary_index(self.static['boundary']);self.commands={z['index']:np.array(z['action'],np.float32) for z in self.saved['commands']};self.contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',question='New full-source handoff diagnosis, preserving561 aperture failure. Reproduce reset->original actions1..34->same561 first candidate actions35..67 exactly, then fixed551 suffix68..last once. If fixed fails, ONE unchanged551/537 feedback suffix from the SAME altered after67 checkpoint. Never start feedback at an unsafe failed state, reset history or restore baseline physical state.',finish='Unchanged FinishLineTracker and hull/contact visited sensors; qualification.95,departure/forward crossing/width confirmation. Clock1.02+accumulated actual raw elapsed; source officialfinish=tracker.finish_time-1.02,not holdcount/arc/local plane subtraction.',safety='Every actual raw original global criteria: footprint>=.50,path<=3,tracking force<=1.059/clip<=.10,reference overspeed<=4.85,body<100,projection continuity. Saved launch first24holds peak<=2.5/clip<=.15 by end24; no tracking reference veto in launch. All forecast body<100. Position aperture/yaw delta diagnostics ONLY,not suffix veto.',suffix_order='Fixed stored commands first,including full last saved command if candidate finish not yet confirmed. If nofinish/firstsafetyviolation/NO_COMMAND then feedback from unchanged altered handoff root+actuallaunch/trackingcounts+visited+tracker+elapsed. Budget/domain/technical errors stop,not silently retry.',feedback='Unchanged structure537 choose,551candidate/backup,actualcurrentfullstate/progress/history and12holdfullgeometry certification; selected action freshly FINAL-certified. No parameter/action-family expansion. At most300 model action decisions and original1224limit with50warmup accounting.',verification='If a suffix safely finishes,independently replay entire recorded reset/prefix/modified/winning suffix command tape to samefinish,comparing every source root/force/visited/tracker. If both fail,independently replay both actual command tapes to first physicalfailure or lastsafe policyfailure root WITHOUT rerunning chooser. No candidate fulltime claim without safefinish.',phase_caps=CAPS,aggregate_caps=dict(model_ticks=133800,force=618200,geometry=149000,CPU_s=1910,wall_s=2265),storage='Exclusive per-phaseSTARTED,atomicJSON-safe perhold ledgers and phasefinally costFIRST,fullcheckpoint including current tracker/visited/history/clock; originalfailure raw saved. No native world/reset/step.',source_kernel_hardcap_unchanged=200000,actual_cap=0,new_seed_HOLDOUT_SEALED_other_environment_paid=0,research_remaining=22758,reserve=84000,reserve_used=0,source_sha256={p:sha(G/p) for p in SOURCES},private_inputs_sha256={str(p):sha(p) for p in INPUTS})
  atomic_write(G/'retry/handoff562_contract.json',self.contract);atomic_write(D/'STARTED.json',dict(contract_sha256=sha(G/'retry/handoff562_contract.json')))
 def initial(self):
  root=load_root(self.static['root']);visited=set(self.ledger['initial_visited']);tracker=tracker_for(self.static,root,visited,False,1.02)
  return dict(root=root,visited=visited,tracker=tracker,elapsed=0.,global_raw=0,progress=project(root.center,self.paths['candidate'],0.)['s'],launch=[0,0],tracking=[0,0])
 def checkpoint(self,state):return dict(root_without_roads=short(state['root']),visited=sorted(state['visited']),tracker=asdict(state['tracker']),elapsed=state['elapsed'],global_raw=state['global_raw'],progress=state['progress'],launch=state['launch'].copy(),tracking=state['tracking'].copy())
 def checkpoint_hash(self,state):return hashlib.sha256(json.dumps(self.checkpoint(state),sort_keys=True,separators=(',',':')).encode()).hexdigest()
 def raw(self,state,action,index,raw_in_hold,phase):
  root=replace(state['root'],planar=replace(state['root'].planar,steer=-float(action[0])));before=short(root);f=phase.force(root,action);phase.cost['force_evaluations']+=4;group='launch' if index<=24 else 'tracking';counts=state[group];new=[counts[0]+sum(z['clipped'] for z in f),counts[1]+4];peak=max(z['ratio'] for z in f);reason='FORCE' if peak>(2.5 if group=='launch' else 1.059) else 'CLIP_HISTORY' if ((group=='tracking' or index>=24) and new[0]/new[1]>(.15 if group=='launch' else .10)) else None
  row=dict(index=index,raw=raw_in_hold,action=action.tolist(),global_raw_before=state['global_raw'],episode_before_s=state['elapsed'],before_root_without_roads=before,forces=f,tracking_history_before=state['tracking'].copy(),launch_history_before=state['launch'].copy(),proposed_history=new,pre_failure=reason)
  if reason:return row,reason
  after=phase.tick(root,float(action[1]),float(action[2]),self.index,phase.counter);state['root']=after;state[group]=new;state['elapsed']+=.02;state['global_raw']+=1;old_s=state['progress'];q=project(after.center,self.paths['candidate'],old_s);state['progress']=q['s'];gap=phase.geometry(after);ref=reference(state['progress'],self.paths['candidate'])[0];over=math.hypot(*after.planar.linear.velocity)-ref;body=max(math.hypot(*hull_pose(after)[1]),*(math.hypot(*(after.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in after.planar.linear.wheels))
  for ids in after.current_contacts:state['visited'].update(ids)
  pose,velocity=hull_pose(after);state['tracker'].update(pose,velocity,len(state['visited'])/len(self.static['track']),1.02+state['elapsed']);delta=state['progress']-old_s
  reason='FOOTPRINT' if gap<.5 else 'PATH' if q['distance']>3 else 'REFERENCE' if group=='tracking' and over>4.85 else 'PROJECTION' if delta<-.5 or delta>max(5.,2*math.dist(root.center,after.center)) else 'BODY' if body>=100 else None
  row.update(root_without_roads=short(after),episode_after_s=state['elapsed'],global_raw_after=state['global_raw'],progress=state['progress'],margin=gap,path_error=q['distance'],reference_overspeed=over,body=body,visited_count=len(state['visited']),tracker=asdict(state['tracker']),post_failure=reason)
  return row,reason
 def run_commands(self,label,initial,tape,phase,feedback=False):
  state=copy.deepcopy(initial);start_hash=self.checkpoint_hash(state);rows=[];commands=[];failure=None;stop='FIXED_SUFFIX_EXHAUSTED_NO_FINISH';phase.current=label
  try:
   iterator=range(68,368) if feedback else sorted(tape)
   for index in iterator:
    phase.snapshot('before-hold')
    if feedback:
     geometry=tracking.geometry_context(self.static,phase.limits['geometry']);phase.guard(reserve=6400)
     old_tick,old_force=tracking.tick,tracking.force_rows;tracking.tick=phase.tick;tracking.force_rows=phase.force
     try:action,detail=tracking.choose(state['root'],self.paths['candidate'],self.paths['backup'],state['progress'],phase.counter,phase.cost,phase.limits['model_ticks'],history=tuple(state['tracking']),geometry=geometry)
     finally:tracking.tick,tracking.force_rows=old_tick,old_force
     if action is None:failure=dict(index=index,reason='NO_ADMISSIBLE_ACTION',root_without_roads=short(state['root']),detail=detail,tracking_history=state['tracking'].copy());stop=failure['reason'];break
     assert detail['final_recertified'] and next(z for z in detail['reports'] if z['mode']=='FINAL')['ok']
    else:action=tape[index];detail=None
    commands.append(dict(index=index,action=action.tolist(),detail=detail))
    for k in range(4):
     row,reason=self.raw(state,action,index,k+1,phase);rows.append(row)
     if reason:failure=dict(index=index,raw=k+1,reason=reason,row=row);stop=reason;break
     if state['tracker'].finish_time_s is not None:stop='SOURCE_FINISH';break
     if 50+state['global_raw']>=1224:failure=dict(index=index,raw=k+1,reason='SOURCE_TIME_LIMIT');stop='SOURCE_TIME_LIMIT';break
    if failure or stop=='SOURCE_FINISH':break
   return dict(label=label,start_hash=start_hash,state=state,rows=rows,commands=commands,stop=stop,failure=failure,safe_finish=stop=='SOURCE_FINISH' and failure is None,finish_s=state['tracker'].finish_time_s-1.02 if state['tracker'].finish_time_s is not None and failure is None else None)
  finally:
   atomic_write(D/f'{label}-private.json',dict(label=label,start_hash=start_hash,checkpoint=self.checkpoint(state),rows=rows,commands=commands,stop=stop,failure=failure));phase.snapshot('case-finally')
 def run(self):
  out={};prep=fixed=feedback=winning=None;checks={};verifications=[];error=None
  try:
   #Pure stored-state finish replay checks old551 event semantics,no integrator.
   original=self.initial()
   for row in self.saved['trace']:
    original['elapsed']+=.02;root=load_root(dict(row['root_without_roads'],roads=self.static['root']['roads']))
    for ids in root.current_contacts:original['visited'].update(ids)
    pose,v=hull_pose(root);original['tracker'].update(pose,v,len(original['visited'])/len(self.static['track']),1.02+original['elapsed'])
   checks['saved551_tracker_exact']=canonical(asdict(original['tracker']))==self.saved['source_tracker'];assert checks['saved551_tracker_exact']
   candidate_tape={i:self.commands[i] for i in range(1,68)}
   for j in range(20):u=self.candidate['x'][2*j+1];candidate_tape[35+j]=np.array([self.candidate['x'][2*j],max(0.,u),max(0.,-u)],np.float32)
   with Phase(self,'preparation') as phase:
    prep=self.run_commands('prefix-modified',self.initial(),candidate_tape,phase);assert prep['failure'] is None and len(prep['rows'])==268
    checks['original_prefix_exact']=all(canonical(r['root_without_roads'])==s['root_without_roads'] and canonical(r['forces'])==s['forces'] for r,s in zip(prep['rows'][:136],self.saved['trace'][:136]))
    checks['candidate_fullstate_commands_exact']=all(canonical(r['root_without_roads'])==s['root_without_roads'] and canonical(r['forces'])==s['forces'] and r['action']==s['action'] if 'action' in s else canonical(r['root_without_roads'])==s['root_without_roads'] and canonical(r['forces'])==s['forces'] for r,s in zip(prep['rows'][136:],self.candidate['rows']));assert all(checks.values())
   handoff=prep['state'];handoff_hash=self.checkpoint_hash(handoff);atomic_write(D/'altered-handoff-private.json',dict(checkpoint=self.checkpoint(handoff),hash=handoff_hash,baseline_root=self.saved['trace'][267]['root_without_roads']))
   with Phase(self,'fixed') as phase:fixed=self.run_commands('fixed-suffix',handoff,{i:a for i,a in self.commands.items() if i>=68},phase)
   checks['fixed_uses_unchanged_altered_handoff']=fixed['start_hash']==handoff_hash
   if fixed['safe_finish']:winning=fixed
   else:
    with Phase(self,'feedback') as phase:feedback=self.run_commands('feedback-suffix',handoff,{},phase,True)
    checks['feedback_uses_same_altered_handoff']=feedback['start_hash']==handoff_hash
    if feedback['safe_finish']:winning=feedback
   cases=[winning] if winning else [x for x in (fixed,feedback) if x is not None]
   with Phase(self,'verification') as phase:
    for case in cases:
     tape=dict(candidate_tape);tape.update({x['index']:np.array(x['action'],np.float32) for x in case['commands']});verify=self.run_commands('verify-'+case['label'],self.initial(),tape,phase);expected=prep['rows']+case['rows'];actual=verify['rows'];same=len(actual)==len(expected) and all(canonical(a.get('root_without_roads',a.get('before_root_without_roads')))==canonical(b.get('root_without_roads',b.get('before_root_without_roads'))) and canonical(a['forces'])==canonical(b['forces']) for a,b in zip(actual,expected));checkpoint_exact=canonical(self.checkpoint(verify['state']))==canonical(self.checkpoint(case['state']));finish_same=verify['finish_s']==case['finish_s'];assert same and checkpoint_exact and finish_same;verifications.append(dict(case=case['label'],raw_records=len(actual),fullstate_force_exact=same,checkpoint_exact=checkpoint_exact,finish_same=finish_same,stop=verify['stop']))
   def public(case):
    if case is None:return None
    rows=[r for r in case['rows'] if 'root_without_roads' in r];failure=case['failure'];return dict(stop=case['stop'],safe_finish=case['safe_finish'],finish_s=case['finish_s'],actual_raw=len(rows),commands=len(case['commands']),first_failure_reason=failure['reason'] if failure else None,first_failure_index=failure.get('index') if failure else None,first_failure_raw=failure.get('raw') if failure else None,first_failure_episode_s=failure.get('row',{}).get('episode_after_s',failure.get('row',{}).get('episode_before_s')) if failure else None,initial_handoff_hash=case['start_hash'],final_global_raw=case['state']['global_raw'],tracking_history=case['state']['tracking'],visited_count=len(case['state']['visited']),minimum_suffix_margin=min((r['margin'] for r in rows),default=None),maximum_suffix_path=max((r['path_error'] for r in rows),default=None),maximum_suffix_reference_overspeed=max((r['reference_overspeed'] for r in rows),default=None))
   out.update(completed=True,checks=checks,fixed=public(fixed),feedback=public(feedback),winning_suffix=winning['label'] if winning else None,whole_source_finish_s=winning['finish_s'] if winning else None,baseline551_source_finish_s=self.saved['summary']['model_finish_episode_s'],whole_source_gain_ms=1000*(self.saved['summary']['model_finish_episode_s']-winning['finish_s']) if winning else None,independent_verification=verifications,prior561_aperture_failure_preserved=True)
  except BaseException as e:
   error=type(e).__name__+':'+str(e);out.update(completed=False,error=error,checks=checks);atomic_write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc()))
  finally:
   sums={k:sum(v[k] for v in self.phase_costs.values()) for k in ['model_ticks','force_evaluations','internal_wheel_force_evaluations','geometry_checks','body_checks','CPU_s','wall_s']};atomic_write(G/'retry/handoff562_cost.json',dict(phases=self.phase_costs,total=sums))
   out.update(cost=sums,phase_costs=self.phase_costs,error=error,new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_native_gain_observation=True)
   atomic_write(G/'retry/handoff562_result.json',out);print(json.dumps(plain(out),indent=2))

if __name__=='__main__':
 from core.vendor.car_racing import CarRacing
 def forbidden(*args,**kwargs):raise RuntimeError('NATIVE_FORBIDDEN')
 CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
 Study().run()
