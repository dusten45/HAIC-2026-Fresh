"""Feasible551-feedback tail retiming with retained-plan revalidation.

Only absolute hold/ref/crossing helpers reused from553, never its goal50 oracle.
One source-derived spatial compression proposal per current fullstate; no sweep.
"""
import bisect,hashlib,json,math
from dataclasses import asdict
import numpy as np
import retry.lap518_control as base_control
import retry.structure537_control as policy
from retry.dynamic553_control import Planner as PhysicalHelpers
from retry.drive519_control import steering
BASE_REFERENCE=base_control.reference

def curve_reference(s,path,curve,gate_s):
 if curve is None or s>=gate_s:return BASE_REFERENCE(s,path)
 i=bisect.bisect_right([z[0] for z in curve],s)-1
 if i<0:q=curve[0][1];dq=0.
 elif i>=len(curve)-1:q=curve[-1][1];dq=0.
 else:a,b=curve[i:i+2];dq=(b[1]-a[1])/(b[0]-a[0]);q=a[1]+max(0.,min(1.,(s-a[0])/(b[0]-a[0])))*(b[1]-a[1])
 return math.sqrt(max(0.,q)),dq/2

def dispatch_reference(s,path):
 if 'source_retime_curve' not in path:return BASE_REFERENCE(s,path)
 return curve_reference(s,path,path['source_retime_curve'],path['source_retime_gate_s'])

def install_dispatch():
 # nominal()/backup() keep the551 law, using the proposed reference as input.
 base_control.reference=dispatch_reference;policy.reference=dispatch_reference

class Planner(PhysicalHelpers):
 def __init__(self,stage,entry):
  super().__init__(stage,entry);self.retained=None;self.decision=0
 def ref(self,root,s,curve):
  if self.dot(root.center)>=0:return BASE_REFERENCE(s,self.path)[0]
  return curve_reference(s,self.path,curve,self.e['target_station'])[0]
 def feedback(self,root,s,history,curve):
  self.st.guard(6400);high=self.path if curve is None else dict(self.path,source_retime_curve=curve,source_retime_gate_s=self.e['target_station']);a,d=policy.choose(root,high,self.st.paths['backup'],s,self.st.counter,self.st.cost,self.st.tick_cap,history=history,geometry=self.st.geometry);return a,d
 def compressed_curve(self,seed,s0,s1,v1):
  gate=self.e['target_station'];q0=curve_reference(s0,self.path,seed,gate)[0]**2;qend=BASE_REFERENCE(gate,self.path)[0]**2
  if s1>=gate:return [(s0,q0),(gate,qend)]
  scale=(gate-s0)/(gate-s1);delta=min(8100.,v1*v1)-q0;points=[s0]+([z[0] for z in seed] if seed is not None else self.path['arcs'])+[gate];out={s0:q0,s1:min(8100.,v1*v1),gate:qend}
  for x in points:
   if not s0<x<gate:continue
   y=s1+(x-s0)/scale;value=curve_reference(x,self.path,seed,gate)[0]**2+delta*(gate-y)/(gate-s1);out[y]=max(0.,min(8100.,value))
  return sorted(out.items())
 def finish(self,start,start_s,history,controls,rows,curve,number,role,feedback_reports):
  cross=self.crossing(start,rows)
  if cross is None:return self.failed(number,role,'NO_FIXED_GATE',start,start_s,history,controls,rows,feedback_reports)
  if cross['speed']<self.e['baseline_gate']['speed']-.15:return self.failed(number,role,'TERMINAL_SPEED',start,start_s,history,controls,rows,feedback_reports)
  maxover=max(z['speed']-self.ref(z['root'],z['s'],curve) for z in rows)
  if maxover>4.85:return self.failed(number,role,'FROZEN_REFERENCE',start,start_s,history,controls,rows,feedback_reports)
  end=rows[-1];self.st.guard(6400);a,future=self.st.original_select(end['root'],end['s'],tuple(end['history']));f=next((z for z in future.get('reports',[]) if z['mode']=='FINAL'),None)
  if a is None or f is None or not f['ok']:return self.failed(number,role,'NO_551_FUTURE_CERTIFICATE',start,start_s,history,controls,rows,feedback_reports,future)
  return dict(ok=True,reason='FEEDBACK_TAIL_AND_551_FUTURE_CERTIFIED',number=number,role=role,root=start,s=start_s,history=list(history),records=rows,controls=controls,curve=curve,crossing=cross,first_progress=rows[3]['s']-start_s,min_margin=min([z['margin'] for z in rows]+[f['min_footprint_margin_m']]),peak=max([max(x['ratio'] for x in z['forces']) for z in rows]+[f['peak']]),max_reference_overspeed=max(maxover,f['max_reference_overspeed']),future=future,future_action=a,feedback_reports=feedback_reports)
 def failed(self,number,role,reason,root,s,history,controls,rows,reports,future=None):
  before=asdict(root);before.pop('roads');states=[]
  for z in rows:
   q=asdict(z['root']);q.pop('roads');states.append(dict(root_without_roads=q,progress=z['s'],speed=z['speed'],margin=z['margin'],history=z['history'],forces=z['forces']))
  self.st.save(self.st.private/f'failed-{self.st.phase}-{number:04d}-private.json',dict(role=role,reason=reason,before_root_without_roads=before,progress=s,history=list(history),controls=[a.tolist() for a in controls],curve=getattr(self,'trial_curve',None),states=states,feedback_reports=reports,future=future));return dict(ok=False,role=role,reason=reason,number=number)
 def build(self,root,s,history,seed,proposal=False,role='FEEDBACK'):
  self.serial+=1;n=self.serial;self.trial_curve=seed;self.st.checkpoint();start=root;s0=s;h=list(history);controls=[];rows=[];reports=[];curve=seed
  if proposal:
   a=np.array([steering(root,self.path,s),1.,0.],np.float32);r=self.hold(root,s,h,a)
   if not r['ok']:return self.failed(n,role,'PROPOSED_FIRST_'+r['reason'],start,s0,history,[a],r['rows'],reports)
   curve=self.compressed_curve(seed,s0,r['s'],r['first_speed']);self.trial_curve=curve;controls.append(a);rows.extend(r['rows']);root,s,h=r['root'],r['s'],r['history']
   if any(z['speed']-self.ref(z['root'],z['s'],curve)>4.85 for z in rows):return self.failed(n,role,'PROPOSED_FIRST_REFERENCE',start,s0,history,controls,rows,reports)
  for j in range(self.st.c['planner_tail_holds']-len(controls)):
   if self.dot(root.center)>=0:break
   self.st.checkpoint();a,d=self.feedback(root,s,tuple(h),curve);reports.append(dict(at_progress=s,detail=d))
   if a is None:return self.failed(n,role,'FEEDBACK_NO_ADMISSIBLE_ACTION',start,s0,history,controls,rows,reports)
   r=self.hold(root,s,h,a)
   if not r['ok']:return self.failed(n,role,'FEEDBACK_EXECUTION_'+r['reason'],start,s0,history,controls+[a],rows+r['rows'],reports)
   if any(z['speed']-self.ref(z['root'],z['s'],curve)>4.85 for z in r['rows']):return self.failed(n,role,'FEEDBACK_REFERENCE',start,s0,history,controls+[a],rows+r['rows'],reports)
   controls.append(a);rows.extend(r['rows']);root,s,h=r['root'],r['s'],r['history']
  return self.finish(start,s0,history,controls,rows,curve,n,role,reports)
 def revalidate(self,root,s,history,plan,role):
  self.serial+=1;n=self.serial;self.trial_curve=plan['curve'];h=list(history);start=root;s0=s;rows=[];controls=[]
  for stored in plan['controls']:
   a=np.array([steering(root,self.path,s),stored[1],stored[2]],np.float32);r=self.hold(root,s,h,a)
   if not r['ok']:return self.failed(n,role,'RETAINED_'+r['reason'],start,s0,history,controls+[a],rows+r['rows'],[])
   if any(z['speed']-self.ref(z['root'],z['s'],plan['curve'])>4.85 for z in r['rows']):return self.failed(n,role,'RETAINED_REFERENCE',start,s0,history,controls+[a],rows+r['rows'],[])
   controls.append(a);rows.extend(r['rows']);root,s,h=r['root'],r['s'],r['history']
   if self.dot(root.center)>=0:break
  return self.finish(start,s0,history,controls,rows,plan['curve'],n,role,[])
 def summarize(self,p):
  return {k:p[k] for k in ['ok','reason','number','role','crossing','first_progress','min_margin','peak','max_reference_overspeed'] if k in p} if p is not None else None
 def store_selected(self,plan,initial,regen,retained,proposal,mode,exact):
  before=asdict(plan['root']);before.pop('roads');fingerprint=hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest();states=[]
  for z in plan['records']:
   q=asdict(z['root']);q.pop('roads');states.append(dict(root_without_roads=q,progress=z['s'],speed=z['speed'],margin=z['margin'],forces=z['forces'],history=z['history'],action=z['action'].tolist()))
  self.st.save(self.st.private/f'plan-{self.st.phase}-{self.decision:03d}-private.json',dict(mode=mode,before_root_without_roads=before,before_sha256=fingerprint,history=plan['history'],curve=plan['curve'],controls=[a.tolist() for a in plan['controls']],states=states,initialization=initial,regenerated=self.summarize(regen),retained_revalidation=self.summarize(retained),proposal=self.summarize(proposal),chosen=self.summarize(plan),future=plan['future'],fresh_selected_replay_identical=exact));return fingerprint
 def decide(self,root,s,history):
  self.decision+=1;initial=self.retained is None;retained=None;regen=None;proposal=None
  if initial:
   regen=self.build(root,s,history,None,False,'INITIAL_551_FEEDBACK')
   if not regen['ok']:return None,dict(mode='INITIAL_551_BACKUP_UNAVAILABLE',initialization=False,regenerated=self.summarize(regen))
   baseline=json.loads((self.st.private/'baseline-prefix-private.json').read_text())['trace'];actual=[]
   for z in regen['records']:
    state=asdict(z['root']);state.pop('roads');actual.append(state)
   assert json.dumps(actual,sort_keys=True)==json.dumps([z['root_without_roads'] for z in baseline[:len(actual)]],sort_keys=True)
   self.st.save(self.st.private/f'{self.st.phase}-initial551-feedback-identity-private.json',dict(exact_saved551_state_prefix=True,raw_states=len(actual),full_feedback_recomputed=True,model_ticks=self.st.counter[0]));back=regen
  else:
   seed=self.retained['curve'];regen=self.build(root,s,history,seed,False,'CURRENT_STATE_551_FEEDBACK');retained=self.revalidate(root,s,history,self.retained,'RETAINED_PEDALS_FRESH_STEERING');good=[p for p in [regen,retained] if p['ok']]
   if not good:return None,dict(mode='CURRENT_BACKUP_REVALIDATION_UNAVAILABLE',initialization=True,regenerated=self.summarize(regen),retained=self.summarize(retained))
   back=min(good,key=lambda p:(p['crossing']['time_s'],-p['crossing']['speed'],-p['first_progress']))
  proposal=self.build(root,s,history,back['curve'],True,'ONE_FULL_HOLD_COMPRESSED_FEEDBACK');chosen=back;mode='RETAINED_FEASIBLE_BACKUP' if retained is back else 'REGENERATED_551_FEEDBACK'
  if proposal['ok'] and (proposal['crossing']['time_s'],-proposal['crossing']['speed'],-proposal['first_progress'])<(back['crossing']['time_s'],-back['crossing']['speed'],-back['first_progress']):chosen=proposal;mode='ACCEPTED_STATEFUL_RETIMING'
  final=self.revalidate(root,s,history,chosen,'FRESH_SELECTED_PLAN')
  if not final['ok']:
   # Preserve certified current backup if a modified proposal's fresh pass fails.
   if chosen is not back:
    final=self.revalidate(root,s,history,back,'FRESH_UNMODIFIED_BACKUP');chosen=back;mode='PRESERVED_AFTER_PROPOSAL_FINAL_FAILURE'
   if not final['ok']:return None,dict(mode='SELECTED_PLAN_REVALIDATION_FAILURE',initialization=True,failure=self.summarize(final),backup=self.summarize(back),proposal=self.summarize(proposal))
  exact=[z['root'] for z in final['records']]==[z['root'] for z in chosen['records']];fingerprint=self.store_selected(final,initial,regen,retained,proposal,mode,exact);self.last_curve=final['curve'];self.retained=dict(controls=final['controls'][1:],curve=final['curve']);f=dict(mode='FINAL',ok=True,reason='CURRENT_STATE_FEEDBACK_RETIME_CERTIFIED',peak=final['peak'],min_footprint_margin_m=final['min_margin'],max_reference_overspeed=final['max_reference_overspeed']);return final['controls'][0],dict(mode=mode,reports=[f],final_recertified=True,initialization_succeeded=True,regenerated=self.summarize(regen),retained_revalidation=self.summarize(retained),proposal=self.summarize(proposal),committed_reference_curve=final['curve'],reference_frozen_before_execution=True,full_state_sha256=fingerprint,planned_gate_speed=final['crossing']['speed'],fresh_replay_identical=exact,plan_number=self.decision)
