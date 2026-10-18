"""One-switch, full-state braking reachability MPC on the fixed552 segment.

Physics plans define a reference before execution. Cap90/reference4.85 unchanged;
old551 reference resumes at fixed gate. No fixed stopping-distance lookup.
"""
import bisect,hashlib,json,math
from dataclasses import asdict,replace
import numpy as np
from retry.drive519_control import steering,project,reference,force_rows
from retry.preview527_control import backup
from retry.structure537_control import ADMISSION

class Planner:
 def __init__(self,stage,entry):self.st=stage;self.e=entry;self.path=stage.paths['candidate'];self.braking=False;self.serial=0;self.last_curve=None
 def dot(self,p):return sum((p[j]-self.e['gate']['point'][j])*self.e['gate']['tangent'][j] for j in range(2))
 def ref(self,root,s,curve):
  if curve is None or self.dot(root.center)>=0:return reference(s,self.path)[0]
  i=bisect.bisect_right([z[0] for z in curve],s)-1
  if i<0:q=curve[0][1]
  elif i>=len(curve)-1:q=curve[-1][1]
  else:a,b=curve[i:i+2];f=max(0.,min(1.,(s-a[0])/(b[0]-a[0])));q=a[1]+f*(b[1]-a[1])
  return math.sqrt(max(0.,q))
 def hold(self,root,s,history,action):
  start_s=s;rows=[];h=list(history);root=replace(root,planar=replace(root.planar,steer=-float(action[0])));reason=None
  for k in range(4):
   self.st.guard(4);before=root;old_s=s;fs=force_rows(root,action);self.st.cost['force_evaluations']+=4;peak=max(z['ratio'] for z in fs);h[0]+=sum(z['clipped'] for z in fs);h[1]+=4
   if peak>ADMISSION or h[0]/h[1]>.1:return dict(ok=False,reason='FORCE' if peak>ADMISSION else 'CLIP',rows=rows)
   root=self.st.checked_tick(root,float(action[1]),float(action[2]),self.st.index,self.st.counter);q=project(root.center,self.path,s);s=q['s'];v=math.hypot(*root.planar.linear.velocity);gap=self.st.measure_margin(root);body=self.st.body_speed(root);delta=s-old_s
   if gap<.5:reason='FOOTPRINT'
   elif q['distance']>3 or delta<-.5 or delta>max(5.,2*math.dist(root.center,before.center)):reason='PATH_OR_PROJECTION'
   elif body>=100:reason='BODY'
   elif self.dot(root.center)>=0 and v-reference(s,self.path)[0]>4.85:reason='OLD_REFERENCE_AFTER_GATE'
   elif self.dot(root.center)<0 and v>90+4.85:reason='CAP90_REFERENCE_CORRIDOR'
   elif not all(math.isfinite(z) for z in [s,v,gap,body]):reason='NONFINITE'
   rows.append(dict(root=root,s=s,speed=v,margin=gap,path_error=q['distance'],body=body,forces=fs,history=h.copy(),action=action.copy()))
   if reason:return dict(ok=False,reason=reason,rows=rows)
  return dict(ok=True,reason='PHYSICAL_HOLD',root=root,s=s,history=h,rows=rows,first_speed=v,first_progress=s-start_s)
 def goal_action(self,root,s,history):
  target=self.e['target_speed'];steer=steering(root,self.path,s);lock=np.float32(.9)
  if lock<.9:lock=np.nextafter(lock,np.float32(1.))
  points=sorted(set([float(np.float32(-1+i/8)) for i in range(17)]+[-float(lock),-float(np.nextafter(lock,np.float32(0.)))]));cache={};summaries=[]
  def evaluate(u):
   u=float(np.float32(u))
   if u not in cache:
    self.st.guard()
    if len(cache)>=31:raise RuntimeError('GOAL_QUERY_CAP')
    a=np.array([steer,max(0.,u),max(0.,-u)],np.float32);r=self.hold(root,s,history,a);cache[u]=dict(u=u,action=a,result=r);summaries.append(dict(u=u,ok=r['ok'],reason=r['reason'],end_speed=r.get('first_speed')))
   return cache[u]
  coarse=[evaluate(u) for u in points];regime=lambda u:'locked' if -u>=.9 else 'brake' if u<0 else 'gas';edges=[]
  for a,b in zip(coarse,coarse[1:]):
   if regime(a['u'])!=regime(b['u']):continue
   ra,rb=a['result'],b['result']
   if ra['ok'] and rb['ok'] and (ra['first_speed']-target)*(rb['first_speed']-target)<0:edges.append(dict(kind='goal',a=a['u'],b=b['u'],score=min(abs(ra['first_speed']-target),abs(rb['first_speed']-target)),active=True))
   elif ra['ok']!=rb['ok']:
    safe=a if ra['ok'] else b;bad=b if ra['ok'] else a;edges.append(dict(kind='limit',safe=safe['u'],bad=bad['u'],score=abs(safe['result']['first_speed']-target),active=True))
  edges.sort(key=lambda e:(e['score'],e['kind']))
  for j in range(9):
   active=[e for e in edges if e['active']]
   if not active or len(cache)>=31:break
   edge=active[j%len(active)];a,b=(edge['a'],edge['b']) if edge['kind']=='goal' else (edge['safe'],edge['bad']);mid=float(np.float32((a+b)/2))
   if not min(a,b)<mid<max(a,b):edge['active']=False;continue
   r=evaluate(mid)['result']
   if edge['kind']=='limit':edge['safe' if r['ok'] else 'bad']=mid
   elif not r['ok']:edge['active']=False
   elif (cache[edge['a']]['result']['first_speed']-target)*(r['first_speed']-target)<=0:edge['b']=mid
   else:edge['a']=mid
  good=[x for x in cache.values() if x['result']['ok']]
  if not good:return None,dict(reason='NO_GOAL_HOLD',trials=summaries)
  best=min(good,key=lambda x:(abs(x['result']['first_speed']-target),-x['result']['first_speed'],-x['u']));return best,dict(reason='INVERSE_GOAL_SPEED',trials=summaries,queries=len(cache))
 def crossing(self,start,rows):
  before=start
  for j,z in enumerate(rows):
   a,b=self.dot(before.center),self.dot(z['root'].center)
   if a<0<=b:
    f=-a/(b-a);v=[before.planar.linear.velocity[t]+f*(z['root'].planar.linear.velocity[t]-before.planar.linear.velocity[t]) for t in range(2)];return dict(raw=j+1,fraction=f,speed=math.hypot(*v),time_s=.02*(j+f))
   before=z['root']
  return None
 def build(self,root,s,history,first_u=None):
  self.serial+=1;number=self.serial;self.st.checkpoint();start=root;start_s=s;records=[];controls=[];inner=[];h=list(history);failure=None
  if first_u is not None:
   a=np.array([steering(root,self.path,s),max(0.,first_u),max(0.,-first_u)],np.float32);r=self.hold(root,s,h,a)
   if not r['ok']:return dict(ok=False,reason='FULL_FIRST_'+r['reason'],number=number)
   records.extend(r['rows']);controls.append(a);root,s,h=r['root'],r['s'],r['history']
  for j in range(self.st.c['planner_tail_holds']-len(controls)):
   if self.dot(root.center)>=0:break
   self.st.checkpoint();best,detail=self.goal_action(root,s,h);inner.append(detail)
   if best is None:return dict(ok=False,reason=detail['reason'],number=number,inner=inner)
   r=best['result'];records.extend(r['rows']);controls.append(best['action']);root,s,h=r['root'],r['s'],r['history']
  cross=self.crossing(start,records)
  if cross is None:return dict(ok=False,reason='TAIL_DID_NOT_REACH_FIXED_GATE',number=number)
  if cross['speed']<self.e['baseline_gate']['speed']-.15:return dict(ok=False,reason='TERMINAL_SPEED_UNDERSHOOT',number=number,crossing=cross)
  qknots={start_s:min(90.,math.hypot(*start.planar.linear.velocity))**2}
  for row in records:
   value=min(90.,row['speed'])**2 if self.dot(row['root'].center)<0 else reference(row['s'],self.path)[0]**2
   if row['s'] in qknots:qknots[row['s']]=max(qknots[row['s']],value)
   else:qknots[row['s']]=value
   if self.dot(row['root'].center)>=0:break
  curve=sorted(qknots.items());maxover=max(z['speed']-self.ref(z['root'],z['s'],curve) for z in records)
  if maxover>4.85:return dict(ok=False,reason='COMMITTED_PLAN_REFERENCE',number=number)
  self.st.guard(6400);a,future=self.st.original_select(root,s,tuple(h));final=next((z for z in future.get('reports',[]) if z['mode']=='FINAL'),None)
  if a is None or final is None or not final['ok']:return dict(ok=False,reason='NO_POST_GATE_537_CERTIFICATE',number=number,future=future)
  minimum=min([z['margin'] for z in records]+[final['min_footprint_margin_m']]);peak=max([max(f['ratio'] for f in z['forces']) for z in records]+[final['peak']]);return dict(ok=True,reason='STATEFUL_STOP_HOLD_AND_FUTURE_CERTIFIED',number=number,root=start,s=start_s,history=list(history),records=records,controls=controls,curve=curve,first_progress=records[3]['s']-start_s,crossing=cross,inner=inner,future=future,future_action=a,min_margin=minimum,peak=peak,max_reference_overspeed=max(maxover,final['max_reference_overspeed']))
 def replay(self,plan,root,s,history):
  h=list(history);records=[]
  for a in plan['controls']:
   r=self.hold(root,s,h,a)
   if not r['ok']:return False,'FRESH_REPLAY_'+r['reason']
   for row in r['rows']:
    if row['speed']-self.ref(row['root'],row['s'],plan['curve'])>4.85:return False,'FRESH_COMMITTED_REFERENCE'
   records.extend(r['rows']);root,s,h=r['root'],r['s'],r['history']
  assert [z['root'] for z in records]==[z['root'] for z in plan['records']]
  self.st.guard(6400);a,d=self.st.original_select(root,s,tuple(h));f=next((z for z in d.get('reports',[]) if z['mode']=='FINAL'),None)
  if a is None or f is None or not f['ok']:return False,'FRESH_POST_GATE_CERTIFICATE'
  assert np.array_equal(a,plan['future_action']);return True,'FRESH_FULL_STATE_PLAN_IDENTICAL'
 def store(self,plan,backup,proposal,latched,transition_trials):
  def summary(p):return {k:p[k] for k in ['ok','reason','number','first_progress','crossing','min_margin','peak','max_reference_overspeed'] if k in p} if p is not None else None
  states=[]
  for row in plan['records']:
   state=asdict(row['root']);state.pop('roads');states.append(dict(root_without_roads=state,progress=row['s'],speed=row['speed'],margin=row['margin'],forces=row['forces'],history=row['history'],action=row['action'].tolist()))
  state=asdict(plan['root']);state.pop('roads');fingerprint=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest();self.st.save(self.st.private/f'plan-{self.st.phase}-{plan["number"]:04d}-private.json',dict(before_root_without_roads=state,before_sha256=fingerprint,before_history=plan['history'],curve=plan['curve'],controls=[a.tolist() for a in plan['controls']],states=states,backup_summary=summary(backup),full_proposal_summary=summary(proposal),chosen_summary=summary(plan),braking_latched=latched,transition_trials=transition_trials,inner=plan['inner'],future=plan['future'],full_fresh_replay_identical=True));return summary(backup),summary(proposal),fingerprint
 def decide(self,root,s,history):
  self.st.guard(6400);back=self.build(root,s,history,None)
  if not back['ok']:return None,dict(mode='NO_DYNAMIC_BRAKING_BACKUP',backup=back)
  proposal=None;chosen=back;transition=[];transition_now=False
  if not self.braking:
   proposal=self.build(root,s,history,1.)
   if proposal['ok'] and proposal['first_progress']>=back['first_progress']:chosen=proposal
   else:
    self.braking=True;transition_now=True;a=back['controls'][0];low=float(a[1]) if a[1]>0 else -float(a[2]);high=1.
    for k in range(4):
     if high-low<=.125:break
     mid=float(np.float32((low+high)/2));trial=self.build(root,s,history,mid);transition.append(dict(u=mid,ok=trial['ok'],reason=trial['reason'],number=trial['number']))
     if trial['ok']:
      low=mid
      if trial['first_progress']>chosen['first_progress']:chosen=trial
     else:high=mid
  fresh,why=self.replay(chosen,root,s,history)
  if not fresh:return None,dict(mode='DYNAMIC_FINAL_FAILED',reason=why)
  b,p,fingerprint=self.store(chosen,back,proposal,self.braking,transition);self.last_curve=tuple(chosen['curve']);report=dict(mode='FINAL',ok=True,reason='SOURCE_REACHABILITY_REFERENCE_CERTIFIED',peak=chosen['peak'],min_footprint_margin_m=chosen['min_margin'],max_reference_overspeed=chosen['max_reference_overspeed']);return chosen['controls'][0],dict(mode='DYNAMIC_TRANSITION' if transition_now else 'DYNAMIC_BRAKE' if self.braking else 'DYNAMIC_ACCEL',reports=[report],final_recertified=True,backup=b,full_proposal=p,transition_trials=transition,full_state_sha256=fingerprint,committed_reference_curve=chosen['curve'],planned_gate_speed=chosen['crossing']['speed'],fresh_replay_identical=True,plan_number=chosen['number'])
