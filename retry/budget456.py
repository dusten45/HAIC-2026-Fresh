"""456 plan-bound budget adapter; unchanged436 planning and453 restore proofs."""
import datetime,os,signal,time,copy
from retry.pilot436_run import *
from retry.pilot436_run import Pilot as Pilot436
from retry.pilot436_meter import Meter as Meter436
from retry.receipt421_io import save_receipt
from retry.loss389_analyze import save,sha

class Meter(Meter436):
    def __init__(self,d,start_wall=None):
        super().__init__(d)
        if start_wall is not None:self.wall=start_wall
        self.context=dict(arm=None,parent_action=0,planner_used=0);self.last_checkpoint=0.
    def checkpoint(self,phase,**facts):
        self.last_checkpoint=time.perf_counter()
        q=dict(stage=456,pid=os.getpid(),phase=phase,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_ticks=self.b['ticks'],reserved_ticks=self.b['reserved_ticks'],model_worlds=self.b['worlds'],CPU_s=time.process_time(),wall_s=time.perf_counter()-self.wall,actual_actions=0,resets=0,**self.context)
        q.update(facts);save(self.d/'progress-private.json',q);return q
    def guard(self):
        self.persist();caps=self.p['caps']
        if time.process_time()>=caps['CPU_s'] or time.perf_counter()-self.wall>=caps['wall_s']:raise ResourceStop('456_worker_CPU_wall_cap')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00')):raise ResourceStop('456_deadline')
        if time.perf_counter()-self.last_checkpoint>=30:self.checkpoint('MODEL_WORKING')
    def timers(self):
        signal.setitimer(signal.ITIMER_PROF,max(.001,self.p['caps']['CPU_s']-time.process_time()))
        remaining=(datetime.datetime.fromisoformat(self.p['deadline_utc'].replace('Z','+00:00'))-datetime.datetime.now(datetime.timezone.utc)).total_seconds()
        signal.setitimer(signal.ITIMER_REAL,max(.001,min(self.p['caps']['wall_s']-(time.perf_counter()-self.wall),remaining)))
    def step(self,m,act,tag):
        if self.b['reserved_ticks']+4>self.p['caps']['ticks']:raise ResourceStop('456_model_tick_cap')
        return super().step(m,act,tag)
    def world(self,state,tag):
        # Same433 input proof +428 constructor/restore logic; explicit1792 cap
        # avoids inheriting428's narrower1024 cap. Physics class is unchanged.
        if self.inputs is None:raise TechnicalStop('missing_preconstructor_input_proof')
        self.guard()
        if self.b['worlds']>=self.p['caps']['worlds']:raise ResourceStop('456_world_cap')
        self.sequence+=1;number=self.sequence
        proof=dict(sequence=number,tag=tag,input_proof=self.inputs,state=copy.deepcopy(state),global_RNG_digest=rnghash(),restore_gate='NOT_YET_CONSTRUCTED',new_actual_actions=0)
        path=self.d/('world'+str(number)+'-before-constructor-private.json');save_receipt(path,proof)
        self.b['worlds']+=1;self.b['worlds_by_tag'][tag]=self.b['worlds_by_tag'].get(tag,0)+1;self.persist();cpu=time.process_time();wall=time.perf_counter()
        try:m=TerminalVehicleTransition(state)
        finally:self.timing(tag+'_world_setup',cpu,wall)
        self.live.append(m);self.b['confirmed_worlds']+=1;self.b['max_live_worlds']=max(self.b['max_live_worlds'],len(self.live));self.persist()
        if rnghash()!=proof['global_RNG_digest']:raise TechnicalStop('world_constructor_global_RNG_mutation')
        gates=dict(bodies=m.initial_bodies_exact,tiles=m.initial_tiles_exact,progress=m.initial_progress_exact,finish=m.initial_finish_exact)
        if not all(gates.values()):raise TechnicalStop('restore_body_tile_progress_finish')
        self.auth[id(m)]=dict(number=number,input_proof=self.inputs,constructor_proof_sha256=sha(path),restore_gates=gates,first_step=False)
        return m

class Planning456(Pilot436):
    def planning_query(self,parent,ctx,before,label):
     schedule=query_schedule(ctx,Budget(self.meter.p['caps']['ticks']-self.meter.b['reserved_ticks'],self.meter.p['caps']['worlds']-self.meter.b['worlds']))
     if schedule.mode!='STATE_QUERY_LONG_C_WITNESSES':raise ResourceStop('full_frozen_planner_query_budget_not_available')
     state=snapshot(parent.m);ph=fingerprint(state);mh=fingerprint(parent.ctrl.memory());rh=rnghash();pairs={};early={};timings={}
     for recipe in [r for r in ['nominal','neutralbrake','fullgas'] if r in schedule.recipes]:
      pair=[];tm=[]
      for rep in range(2):
       c0=time.process_time();w0=time.perf_counter();tag='planner_required_initial13' if rep==0 else 'planner_repeat_initial13'
       c=self.new(state,before,ctx.ledger,label+'_'+recipe+'_'+str(rep+1),recipe,'planner_required' if rep==0 else 'planner_independent_repeat');c.initial13(tag);c.dump(self.d);self.unchanged(parent,ph,mh,rh);self.validate_child(c);pair.append(c);tm.append(dict(CPU_s=time.process_time()-c0,wall_s=time.perf_counter()-w0))
      if pair[0].signature()!=pair[1].signature():raise TechnicalStop('planner_initial13_repeat')
      pairs[recipe]=pair;timings[recipe]=tm
      if not pair[0].initial_ok:
       paths=[self.d/(c.label+'-private.json') for c in pair];raw=[read(x) for x in paths];rootstate,rootmem,_=ctx.parent.fork_inputs()
       e=audit_pair(raw[0],raw[1],np.asarray(self.fixed['line']),rootstate,rootmem,ctx.parent.raw_clock_tick,[sha(x) for x in paths])
       proofs=GateProofs(True,True,True,True,self.meter.qualification_passed,True,True)
       e=replace(e,cost=replace(e.cost,required_CPU_s=tm[0]['CPU_s'],repeat_CPU_s=tm[1]['CPU_s'],required_wall_s=tm[0]['wall_s'],repeat_wall_s=tm[1]['wall_s']))
       early[recipe]=bind_before_query_proof(e,ctx,proofs);early[recipe].authenticate(ctx)
       wire=to_wire(early[recipe]);path=self.d/(label+'_'+recipe+'-early-private.json');save_receipt(path,wire)
       if from_wire(load_receipt(path))!=early[recipe]:raise TechnicalStop('early_wire_roundtrip')
      if recipe=='neutralbrake' and not(pairs['nominal'][0].initial_ok and pairs['nominal'][0].initial_safe and pairs['nominal'][0].initial_progress) and not(pair[0].initial_ok and pair[0].initial_safe and pair[0].initial_progress):raise PilotStop('planner_baseline_guardian_both_infeasible')
     for recipe,pair in pairs.items():
      if recipe in early:continue
      for c in pair:
       if c.status=='ACTIVE' and c.initial_safe and c.initial_progress:c.stream.prepare_boundary(ctx)
      for rep,c in enumerate(pair):
       if c.status=='ACTIVE' and c.initial_safe and c.initial_progress:c.continue_tail('planner_required_tail' if rep==0 else 'planner_repeat_tail')
       c.dump(self.d);self.unchanged(parent,ph,mh,rh);self.validate_child(c)
      if pair[0].signature()!=pair[1].signature():raise TechnicalStop('planner_full_C_tail_repeat')
     receipts={}
     for r,cs in pairs.items():
      if r in early:receipts[r]=early[r];continue
      typed=[self.runtime_evidence(c,ctx) for c in cs];receipts[r]=typed[0]
     decision=choose(ctx,receipts)
     payload=dict(query=asdict(schedule),context=asdict(ctx),evidence={r:asdict(e) for r,e in receipts.items() if type(e) is Evidence},runtime_evidence={r:runtime_wire(e) for r,e in receipts.items() if type(e) in [Completion434,UnfinishedPending435]},early_evidence={r:to_wire(e) for r,e in early.items()},decision=asdict(decision),preintegration=self.meter.query_proof,scope='436MODEL_ONLY_NEW_AUTHENTICATED_CONTEXT; no428UNBOUNDreuse')
     path=self.d/(label+'-evidence-private.json');dg=save_receipt(path,payload)
     if receipt_digest(load_receipt(path))!=dg:raise TechnicalStop('runtime_receipt_roundtrip')
     self.unchanged(parent,ph,mh,rh);save(self.d/(label+'-receipt-digest.json'),dict(digest=dg,readback_verified=True,parent_unchanged=True,RNG_unchanged=True))
     if decision.recipe is None or decision.status not in ['MODEL_TIME_CHOICE','GUARDIAN_REFERENCE_ONLY']:raise PilotStop('planner_no_qualified_first_action:'+decision.status)
     selected=pairs[decision.recipe][0];summary=dict(decision=asdict(decision),recipes={r:dict(status='EARLY_PHYSICAL_INELIGIBLE' if r in early else cs[0].status,initial_actions=cs[0].initial_count,tail_actions=cs[0].tail_count,finish_ticks=None if cs[0].finish_ticks is None else asdict(cs[0].finish_ticks),authenticated=True,actual_physics_qualified=False) for r,cs in pairs.items()})
     first=copy.deepcopy(selected.rows[0])
     for pair in pairs.values():
      for c in pair:self.close_saved(c)
     return dict(recipe=decision.recipe,first=first,summary=summary)
