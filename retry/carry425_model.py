"""Frozen419 first-twelve queries and existing guardian during actual carry; forecast memory never committed."""
import contextlib,copy,datetime,signal,time
from dataclasses import asdict
import numpy as np
from retry.pilot420_backend import *
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest
from retry.terminal410_model import from_actual_full
from retry.fork394_run import complete_state
from retry.paired417_common import shapecheck

class ActualMeter(Meter):
 def __init__(self,d):
  super().__init__(d);self.mb=self.b;self.queries=[];self.active=None;self.mc=time.process_time();self.mw=0.;self.regions=[];self.actual_start=None;self.model_base=None;self.nb=dict(actions=0,resets=0,CPU_s=0.,wall_s=0.,arm_actions={})
 def modeltime(self):return (self.mc+(time.process_time()-self.active[0] if self.active else 0),self.mw+(time.perf_counter()-self.active[1] if self.active else 0))
 def nativetime(self):
  if self.actual_start is None:return self.nb['CPU_s'],self.nb['wall_s']
  c,w=self.modeltime();return(time.process_time()-self.actual_start[0]-(c-self.model_base[0]),time.perf_counter()-self.actual_start[1]-(w-self.model_base[1]))
 def persist(self):
  mc,mw=self.modeltime();nc,nw=self.nativetime();self.b.update(CPU_s=mc,execution_wall_s=mw)
  save(self.d/'budget.json',dict(model={**self.b,'regions':self.regions},actual={**self.nb,'CPU_s':nc,'wall_s':nw},wholeworker_CPU_s=time.process_time(),whole_execution_wall_s=time.perf_counter()-self.wall,exclusive_accounting=True,model_CPU_includes_imports=True))
 def guard(self):
  self.persist();mc,mw=self.modeltime();nc,nw=self.nativetime()
  if mc>=600 or mw>=900:raise ResourceStop('modelCPU600_wall900')
  if nc>=120 or nw>=240:raise ResourceStop('actualCPU120_wall240')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):raise ResourceStop('deadline')
 def timers(self):
  if self.active:c,w=self.modeltime();limits=(600-c,900-w)
  elif self.actual_start:c,w=self.nativetime();limits=(120-c,240-w)
  else:limits=None
  signal.setitimer(signal.ITIMER_PROF,max(.001,limits[0]) if limits else 0);signal.setitimer(signal.ITIMER_REAL,max(.001,limits[1]) if limits else 0)
 @contextlib.contextmanager
 def model(self,label):
  assert self.active is None;self.guard();self.active=(time.process_time(),time.perf_counter());self.timers()
  try:yield
  finally:
   c,w=time.process_time()-self.active[0],time.perf_counter()-self.active[1];self.mc+=c;self.mw+=w;self.regions.append(dict(label=label,CPU_s=c,wall_s=w));self.active=None;self.timers();self.persist()
 def begin_actual(self):
  assert self.actual_start is None;self.actual_start=(time.process_time(),time.perf_counter());self.model_base=self.modeltime();self.timers();self.persist()
 def end_actual(self):
  if self.actual_start:self.nb['CPU_s'],self.nb['wall_s']=self.nativetime();self.actual_start=None;self.timers();self.persist()
 def charge(self,kind,arm):
  assert self.actual_start and self.active is None;self.guard();key='resets' if kind=='reset' else 'actions'
  if self.nb[key]>=(2 if key=='resets' else 620):raise ResourceStop('actualcap_'+key)
  self.nb[key]+=1
  if key=='actions':self.nb['arm_actions'][arm]=self.nb['arm_actions'].get(arm,0)+1
  self.persist()
 def world(self,state,tag):
  assert self.active;self.guard()
  if self.b['worlds']>=1000:raise ResourceStop('world1000')
  tag=self.phase_tag+tag;self.b['worlds']+=1;self.b['worlds_by_tag'][tag]=self.b['worlds_by_tag'].get(tag,0)+1;self.persist();c=time.process_time();w=time.perf_counter()
  try:m=TerminalVehicleTransition(state)
  finally:self.timing(tag+'_world_setup',c,w)
  self.live.append(m);self.b['confirmed_worlds']+=1;self.b['max_live_worlds']=max(self.b['max_live_worlds'],len(self.live));self.persist()
  if not(m.initial_bodies_exact and m.initial_tiles_exact and m.initial_progress_exact and m.initial_finish_exact):raise TechnicalStop('restore_body_tile_progress_finish')
  return m
 def step(self,m,act,tag):
  assert self.active;tag=self.phase_tag+tag;self.guard()
  if self.b['reserved_ticks']+4>131072:raise ResourceStop('tick131072')
  self.b['reserved_ticks']+=4;self.persist();before=m.native_ticks;c=time.process_time();w=time.perf_counter();success=False
  try:q=m.step(act);success=True;return q
  finally:
   count=m.native_ticks-before;self.b['ticks']+=count;self.b['ticks_by_tag'][tag]=self.b['ticks_by_tag'].get(tag,0)+count
   if success:self.b['reserved_ticks']-=4-count
   self.timing(tag,c,w);self.persist()

def require_planner_gate(ctx,optimize):
 # First-lap419 gate applies only to the twelve optional planning decisions.
 # Existing signedC/guardian handles its original phase and safety boundaries.
 if optimize and ctx.gate()!='QUERY_CURRENT':raise TechnicalStop('actual_current_context:'+ctx.gate())

def query(root,meter,env,obs,ctrl,fixed,pace,before,nominal,ledger,folder,step,optimize):
 meter.phase_tag='initial13_' if step<=131 else 'continuation_';label=folder.name+'_'+str(step);children=[];cpu=time.process_time();wall=time.perf_counter()
 with meter.model(label):
  full=complete_state(env,obs,ctrl.memory());stamp=fingerprint(full);mh=fingerprint(ctrl.memory());rh=rnghash();ld=ledger.digest();state=from_actual_full(full);line=np.asarray(fixed['line']);h=state['physical']['hull'];proj=canonical_projection(line,h['position'],h['velocity'],ctrl.phase());target,_=ctrl.policy._reference(proj);forward=float(np.asarray(h['velocity'])@np.asarray([-np.sin(h['angle']),np.cos(h['angle'])]));policy_digest=fingerprint(dict(selector=read(root/'stage425/plan.json')['selector_sha256'],signed=read(root/'stage425/plan.json')['signed_sha256'],fixed=fixed,pace=pace.tolist()));parent=Parent.current(dict(terminal_model=state,provenance='CURRENT_ACTUAL_PARENT'),before,full['RNG'],ledger.last_clock_tick);ctx=Current(parent,ledger,policy_digest,tuple(float(x) for x in nominal),ctrl.phase(),target,proj['sigma'],forward,sum(fixed['free_profile']['ds'])-ledger.progress_m,current_safety_qualified=env.damage.damage==0)
  require_planner_gate(ctx,optimize)
  def unchanged():
   if fingerprint(complete_state(env,obs,ctrl.memory()))!=stamp or fingerprint(ctrl.memory())!=mh or rnghash()!=rh or ledger.digest()!=ld:raise TechnicalStop('LIVE_actual_parent_memory_RNG_ledger_mutation')
  def pair(recipe,planner):
   out=[]
   for rep in range(2):
    tag=('planner' if planner else 'guardian')+('_required' if rep==0 else '_repeat');c=Child(meter,state,before,ledger,fixed,pace,label+'_'+recipe+'_'+str(rep+1),recipe,tag);children.append(c);c.initial13(tag+'_initial13');c.dump(folder);unchanged();out.append(c)
   if out[0].signature()!=out[1].signature():raise TechnicalStop('initial13_independent_repeat')
   if max(abs(np.asarray(out[0].rows[0]['command'])-np.asarray(ctx.command(recipe))))>1e-6:raise TechnicalStop('current_recipe_command_mismatch')
   # Before any actual intervention, requalify the old actual A/B calibration.
   if step==119 and recipe in ['nominal','fullgas']:
    arm='A' if recipe=='nominal' else 'B';refs=[__import__('json').loads(t) for t in (root/('stage418/actual_'+arm+'/trace-private.jsonl')).read_text().splitlines()][118:];checks=[shapecheck(f,r) for f,r in zip(out[0].rows,refs)];save(folder/(label+'_'+recipe+'-rootqualification.json'),dict(passed=len(checks)==13 and all(z['passed'] for z in checks),checks=checks))
    if len(checks)!=13 or not all(z['passed'] for z in checks):raise TechnicalStop('actual418_root13_fidelity')
   return out
  try:
   pairs={};schedule=None;decision=None
   if optimize:
    schedule=query_schedule(ctx,Budget(131072-meter.b['reserved_ticks'],1000-meter.b['worlds']))
    if schedule.mode!='STATE_QUERY_LONG_C_WITNESSES':raise ResourceStop('full_frozen_planner_query_budget_not_available')
    for recipe in ['nominal','neutralbrake','fullgas']:
     if recipe in schedule.recipes:
      pairs[recipe]=pair(recipe,True)
      if recipe=='neutralbrake' and not(pairs['nominal'][0].initial_safe and pairs['nominal'][0].initial_progress) and not(pairs[recipe][0].initial_safe and pairs[recipe][0].initial_progress):raise PilotStop('planner_guardian_both_infeasible')
    for recipe,cs in pairs.items():
     for rep,c in enumerate(cs):
      if not c.initial_ok:raise TechnicalStop('partial_initial_receipt_stop_without_padding')
      if c.initial_safe and c.initial_progress:c.continue_tail('planner_required_tail' if rep==0 else 'planner_repeat_tail')
      c.dump(folder);unchanged()
     if cs[0].signature()!=cs[1].signature():raise TechnicalStop('full_tail_independent_repeat')
    evidence={k:v[0].evidence(ctx) for k,v in pairs.items()};decision=choose(ctx,evidence)
    if decision.recipe is None or decision.status not in ['MODEL_TIME_CHOICE','GUARDIAN_REFERENCE_ONLY']:raise PilotStop('planner_no_action:'+decision.status)
    recipe=decision.recipe;payload=dict(query=asdict(schedule),context=asdict(ctx),evidence={k:asdict(v) for k,v in evidence.items()},decision=asdict(decision),scope='MODEL_WITNESSES_ONLY; separately authorized actualcarry; modelwitnessesnotactualresults')
    path=folder/(label+'-receipt-private.json');digest=save_receipt(path,payload)
    if receipt_digest(load_receipt(path))!=digest:raise TechnicalStop('fullreceipt_roundtrip')
   else:
    pairs['nominal']=pair('nominal',False);a=pairs['nominal'][0];recipe='nominal'
    if not(a.initial_ok and a.initial_safe and a.initial_progress):
     pairs['neutralbrake']=pair('neutralbrake',False);b=pairs['neutralbrake'][0]
     if not(b.initial_ok and b.initial_safe and b.initial_progress):raise PilotStop('guardian_both_infeasible')
     recipe='neutralbrake'
   selected=pairs[recipe][0];first=copy.deepcopy(selected.rows[0]);witness=copy.deepcopy(selected.rows[:selected.initial_count]);unchanged()
   record=dict(step=step,optimize=optimize,selected=recipe,decision=None if decision is None else asdict(decision),parent_before_sha256=stamp,parent_after_sha256=fingerprint(complete_state(env,obs,ctrl.memory())),parent_memory_RNG_ledger_unchanged=True,actual_parent_clock=ledger.last_clock_tick,recipes={k:dict(status=v[0].status,initial_count=v[0].initial_count,tail_count=v[0].tail_count,finish_ticks=None if v[0].finish_ticks is None else asdict(v[0].finish_ticks)) for k,v in pairs.items()},source_memory_committed=False,proposal_actual_execution_allowed=False)
   save(folder/(label+'-query-private.json'),record)
  finally:
   for c in children:
    try:c.dump(folder)
    finally:c.close()
  unchanged()
 latency=dict(**record,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);meter.queries.append(dict(arm=folder.name,**latency))
 return np.asarray(first['command'],np.float32),first,witness,latency
