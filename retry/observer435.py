"""Observer-only child adapters: preserve original physics/action implementations."""
import copy,hashlib,pickle,random
from dataclasses import asdict
import numpy as np
from retry.pilot420_backend import Child as BaseChild,TechnicalStop,snapshot,fingerprint,metrics,canonical_projection,rnghash
from retry.guardian426_confirmed import GuardianChild as BaseGuardian
from retry.capture434 import PostTrackerTap,CaptureBarrier
from retry.boundary434 import Authority434,capture_h13,TailRecord,require,encoded,legacy_digest
from retry.early429 import GateProofs
from retry.pilot420_json import json_ready
from retry.receipt421_io import save_receipt,load_receipt,receipt_digest


def current_rng():
 blob=pickle.dumps((random.getstate(),np.random.get_state()));return dict(global_pickle=blob,digest=hashlib.sha256(blob).hexdigest())

def authority(meter,fixed):
 return Authority434(tuple(sorted(meter.p['semantic_sources'].items())),sum(fixed['free_profile']['ds']),'LIVE_MODEL_POST_TICK_OBSERVER')

class Stream:
 def __init__(self,child):
  self.child=child;self.world=child.m;self.ctrl=child.ctrl;self.label=child.label;self.meter=child.meter;self.number=self.meter.auth[id(child.m)]['number'];self.child_id=self.meter.plan_sha[:12]+'-world'+str(self.number)+'-'+self.label;self.posts=[];self.actions=[];self.calls=0;self.failure=None;self.boundary=None;self.key=None;self.tail_started=False;self.final_saved=False;self.generic_sealed=False;self.ctx=None;self.authority=authority(self.meter,child.fixed)
  require(id(child.m) not in self.meter.streams,'duplicate_live_world_stream');self.meter.streams[id(child.m)]=self
  self.root_state=snapshot(child.m);self.root_memory=copy.deepcopy(child.ctrl.memory());self.root_rng=current_rng();self.root_ledger=asdict(child.ledger)
  self.link=dict(child_id=self.child_id,world_number=self.number,label=self.label,plan_sha256=self.meter.plan_sha,source_manifest=self.meter.p['semantic_sources'],constructor_proof=self.meter.auth[id(child.m)]['constructor_proof_sha256'],root_state_digest=fingerprint(self.root_state),root_memory_digest=fingerprint(self.root_memory),RNG_digest=self.root_rng['digest'],model_ledger=self.root_ledger,actual_execution_allowed=False)
  save_receipt(self.meter.d/(self.label+'-runtime-link-private.json'),self.link)
 def require_owner(self,child):
  require(child is self.child and child.m is self.world and child.ctrl is self.ctrl and child.label==self.label and self.meter.streams.get(id(child.m)) is self and self.meter.auth[id(child.m)]['number']==self.number,'live_world_or_command_stream_changed')
 def seal_generic(self):
  self.require_owner(self.child);require(len(self.child.rows)==13 and not self.generic_sealed,'generic_H13_wrong_point')
  if self.child.status=='ACTIVE':require(self.ctrl.memory()==self.actions[-1]['memory_after'],'H13_controller_already_advanced')
  p=self.meter.d/(self.child_id+'-observation-H13-private.json');value=dict(link=self.link,snapshot=snapshot(self.world),memory=self.ctrl.memory(),RNG=current_rng(),ledger=asdict(self.child.ledger),posts=self.posts,actions=self.actions,scope='OBSERVER_CAPTURE_ONLY_NO_RANKING_CERTIFICATE')
  h=save_receipt(p,value);require(receipt_digest(load_receipt(p))==h,'generic_H13_readback');self.generic_sealed=True
 def prepare_boundary(self,ctx):
  c=self.child;self.require_owner(c);require(c.status=='ACTIVE' and c.initial_count==13 and c.tail_count==0 and len(c.rows)==13,'planner_not_paused_at_H13');require(self.meter.qualification_passed,'observer_qualification_not_passed');self.ctx=ctx
  proofs=GateProofs(True,True,True,True,True,True,True)
  self.boundary=capture_h13(ctx,self.authority,child_id=self.child_id,recipe=c.recipe,snapshot=snapshot(c.m),memory=c.ctrl.memory(),rng=current_rng(),ledger=c.ledger,posts=self.posts,actions=self.actions,vector=c.end13,proofs=proofs)
  self.key=self.meter.barrier.seal(self.boundary,ctx,self.authority);return self.boundary
 def start_tail(self):
  self.require_owner(self.child);require(self.boundary is not None and self.key==self.boundary.key() and not self.tail_started,'tail_without_same_world_H13_seal');self.meter.barrier.begin_continuation(self.child_id,self.key);self.tail_started=True
 def tail_record(self):
  c=self.child;self.require_owner(c);require(self.tail_started and c.tail_count>0,'missing_tail_observations');memory=c.rows[-1]['memory_after']
  return TailRecord(self.child_id,self.key,self.authority.source_versions,encoded(self.posts[52:]),encoded(self.actions[13:]),encoded(snapshot(c.m)),encoded(memory),encoded(json_ready(current_rng())),encoded(asdict(c.ledger)),GateProofs(True,True,True,True,True,True,True),outcome=c.status)
 def save_final(self):
  self.require_owner(self.child)
  if self.final_saved:return
  save_receipt(self.meter.d/(self.child_id+'-observer-final-private.json'),dict(link=self.link,snapshot=snapshot(self.world),memory=self.ctrl.memory(),RNG=current_rng(),ledger=asdict(self.child.ledger),posts=self.posts,actions=self.actions,failure=self.failure,boundary_key=self.key,tail_started=self.tail_started));self.final_saved=True

class ObserveMixin:
 def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.stream=Stream(self)
 def one(self,tag,first_override=None,prepared_nominal=None,prepared_before=None):
  s=self.stream;s.require_owner(self)
  if len(self.rows)==13 and not s.generic_sealed:s.seal_generic()
  # Continuation through continue_tail requires the specific sealed same world.
  if self.initial_count==13 and len(self.rows)>=13:require(s.tail_started,'tail_step_before_barrier')
  oldlen=len(self.rows);clock=self.ledger.last_clock_tick;raw=[];nominal=[];had='act' in self.ctrl.__dict__;oldinstance=self.ctrl.__dict__.get('act');original=self.ctrl.act
  def spy(model):
   require(model is self.m,'nominal_for_different_world');value=original(model);nominal.append(np.asarray(value).tolist());return value
  self.ctrl.act=spy
  def observed(row):
   s.require_owner(self);row=copy.deepcopy(row);row.update(raw_clock=clock+len(raw)+1,post_wheel_contacts=sum(bool(w.tiles) for w in self.m.car.wheels),post_collision=bool(self.m._collision_this_step or self.m.contacts));raw.append(row)
  try:
   with PostTrackerTap(self.m.finish_line_tracker,observed):super().one(tag,first_override=first_override,prepared_nominal=prepared_nominal,prepared_before=prepared_before)
   if len(self.rows)==oldlen:return
   row=self.rows[-1];n=row['predicted']['raw_ticks'];require(len(raw)==n and len(row['raw_hull'])==n and len(row['tires'])==4*n,'observer_raw_phase_coverage')
   require((len(nominal)==1 if prepared_nominal is None else len(nominal)==0),'nominal_called_wrong_count');own_nominal=nominal[0] if prepared_nominal is None else np.asarray(prepared_nominal).tolist();phase=row['memory_after']['C']['phase'];projection,flags=metrics(row['predicted'],row['tires'],row['raw_hull'],self.line,phase);require(set(flags)==set(row['safety']),'observer_frozen_safety_changed')
   for i,post in enumerate(raw):
    pre=row['raw_hull'][i];tires=row['tires'][4*i:4*(i+1)];require(post['time']==pre['time']+1/50 and [(z['raw_tick'],z['wheel']) for z in tires]==[(i+1,w) for w in range(4)],'post_preclip_clock_or_wheel_join')
    pp=canonical_projection(self.line,post['position'],post['velocity'],phase);pr=canonical_projection(self.line,pre['origin_position'],pre['origin_linear_velocity'],phase)
    post.update(phase=phase,damage=row['predicted']['damage'],collision=post.pop('post_collision'),grass=any(z['grass'] for z in tires),wheel_road_contacts=post.pop('post_wheel_contacts'),path_error_m=max(pp['path_error_m'],pr['path_error_m']),preclip=copy.deepcopy(tires),pre_hull=copy.deepcopy(pre))
   observed_flags=set()
   for p in raw:
    if p['path_error_m']>3:observed_flags.add('path_error_over3m')
    if p['damage']>0:observed_flags.add('damage_increase')
    if p['collision']:observed_flags.add('collision_or_obstacle')
    if p['grass'] or p['wheel_road_contacts']<4:observed_flags.add('road_loss_or_grass')
   require(observed_flags==set(row['safety'])-{'reverse'},'observer_vs_frozen_physical_safety')
   require(raw[-1]['position']==row['predicted']['position'] and raw[-1]['velocity']==row['predicted']['velocity'] and raw[-1]['time']==row['predicted']['time'] and raw[-1]['tracker_after']==snapshot(self.m)['finish_tracker'],'observer_post_snapshot_join')
   action=dict(action_index=len(self.rows),raw_end_clock=self.ledger.last_clock_tick,memory_before=copy.deepcopy(row['memory_before']),memory_after=copy.deepcopy(row['memory_after']),command=copy.deepcopy(row['command']),nominal=own_nominal,model_progress_m=row['model_progress'],ledger_after=asdict(self.ledger),frozen_row=copy.deepcopy(row),outcome_after=self.status)
   s.posts.extend(raw);s.actions.append(action);s.calls+=1
   if len(self.rows)==13 and not s.generic_sealed:s.seal_generic()
  except BaseException as e:s.failure=type(e).__name__+': '+str(e);s.posts.extend(raw);raise
  finally:
   if had:self.ctrl.act=oldinstance
   else:del self.ctrl.__dict__['act']
 def continue_tail(self,tag):
  self.stream.start_tail();result=super().continue_tail(tag);self.stream.save_final();return result
 def dump(self,d):
  super().dump(d)
  from retry.loss389_analyze import save
  save(d/(self.label+'-observer-private.json'),dict(link=self.stream.link,posts=self.stream.posts,actions=self.stream.actions,failure=self.stream.failure,boundary_key=self.stream.key,tail_started=self.stream.tail_started))
 def close(self):
  if not self.closed:self.stream.save_final()
  super().close()

class Child(ObserveMixin,BaseChild):pass
class GuardianChild(ObserveMixin,BaseGuardian):pass
