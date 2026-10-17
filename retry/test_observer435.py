"""Static live-identity and failed-continuation controls; no physical world."""
import copy,hashlib,tempfile,unittest
from dataclasses import replace,asdict
from pathlib import Path
from types import SimpleNamespace
from retry.test_boundary434 import fixture,PROOFS
from retry.boundary434 import *
from retry.capture434 import CaptureBarrier
from retry.observer435 import Stream
from retry.receipt435 import UnfinishedPending435,choose,runtime_wire,runtime_restore
from retry.receipt421_io import save_receipt,load_receipt
from retry.pilot420_json import json_ready
from retry.test_planner419 import evidence

class ObserverControls(unittest.TestCase):
 def test_live_world_controller_registry_identity(self):
  world=object();ctrl=object();child=SimpleNamespace(m=world,ctrl=ctrl,label='required');s=Stream.__new__(Stream);s.child=child;s.world=world;s.ctrl=ctrl;s.label='required';s.number=7;s.meter=SimpleNamespace(streams={id(world):s},auth={id(world):{'number':7}});s.require_owner(child)
  for field,value in [('m',object()),('ctrl',object()),('label','other')]:
   old=getattr(child,field);setattr(child,field,value)
   with self.assertRaises(ProtocolStop):s.require_owner(child)
   setattr(child,field,old)
  s.meter.streams[id(world)]=object()
  with self.assertRaises(ProtocolStop):s.require_owner(child)
 def unfinished(self):
  ctx,a,b,t=fixture();line=[[-10.,0.],[0.,0.],[10.,0.],[10.,10.],[-10.,10.]];line_bytes=encoded(line);versions=tuple(sorted([*a.source_versions,('geometry_line_json',hashlib.sha256(line_bytes).hexdigest())]));a=replace(a,source_versions=versions);b=replace(b,source_versions=versions);actions=decode(t.actions_bytes);posts=decode(t.posts_bytes);posts[0]['damage']=1.;snapshot=decode(t.snapshot_bytes);snapshot['physical']['damage']=1.;q=dict(position=posts[0]['position'],velocity=posts[0]['velocity'],angle=-1.5707963267948966,damage=1.,collision=False,contact_obstacle_ids=[],wheel_road_contacts=4,raw_ticks=1,finished=True,terminal=True,time=posts[0]['time'],finish_time_s=posts[0]['tracker_after']['finish_time_s']);tires=[dict(grass=False) for _ in range(4)];hulls=[dict(origin_position=[0.,0.],origin_linear_velocity=[2.,0.])];row=dict(command=actions[0]['command'],memory_after=actions[0]['memory_after'],predicted=q,tires=tires,raw_hull=hulls,safety=['damage_increase']);actions[0]['frozen_row']=row;t=replace(t,boundary_key=b.key(),source_versions=versions,posts_bytes=encoded(posts),actions_bytes=encoded(actions),snapshot_bytes=encoded(snapshot),outcome='UNSAFE')
  td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name);key=store.seal(b,ctx,a);store.begin_continuation(b.child_id,key);_,path,digest=store.pending[b.child_id];save_receipt(Path(td.name)/(b.child_id+'-continuation-final-private.json'),asdict(t));u=UnfinishedPending435(b,t,a,path,digest,line_bytes);return ctx,u,td
 def test_unsafe_raw_official_event_still_has_no_candidate_finish(self):
  ctx,u,_=self.unfinished();u.authenticate(ctx);self.assertIsNone(u.finish_ticks);self.assertFalse(u.finished_witness());self.assertFalse(u.actual_DONE_allowed);self.assertFalse(u.actual_execution_allowed)
  ev={'nominal':u,'neutralbrake':evidence(ctx,'neutralbrake',(100,101)),'fullgas':evidence(ctx,'fullgas',(1,2))};self.assertEqual(choose(ctx,ev).status,'GUARDIAN_REFERENCE_ONLY');self.assertEqual(choose(ctx,ev).recipe,'nominal')
 def test_unfinished_runtime_wire_roundtrip_and_no_authority_smuggling(self):
  ctx,u,td=self.unfinished();path=Path(td.name)/'runtime-private.json';save_receipt(path,runtime_wire(u));v=runtime_restore(load_receipt(path));self.assertEqual(v,u);self.assertIsNone(v.finish_ticks)
  wire=load_receipt(path);wire['kind']='Unknown'
  with self.assertRaises(ProtocolStop):runtime_restore(wire)
 def test_unfinished_source_child_clock_damage_and_proof_tamper(self):
  ctx,u,_=self.unfinished()
  for bad in [replace(u.tail,child_id='other'),replace(u.tail,boundary_key='foreign'),replace(u.tail,proofs=replace(PROOFS,RNG_unchanged=False))]:
   with self.assertRaises(ProtocolStop):replace(u,tail=bad)
  posts=decode(u.tail.posts_bytes);posts[0]['raw_clock']+=1
  with self.assertRaises(ProtocolStop):replace(u,tail=replace(u.tail,posts_bytes=encoded(posts)))
  snapshot=decode(u.tail.snapshot_bytes);snapshot['physical']['damage']=0
  with self.assertRaises(ProtocolStop):replace(u,tail=replace(u.tail,snapshot_bytes=encoded(snapshot)))
 def test_successful_runtime_wire_keeps_original_event_bracket(self):
  ctx,a,b,t=fixture();td=tempfile.TemporaryDirectory();self.addCleanup(td.cleanup);store=CaptureBarrier(td.name);key=store.seal(b,ctx,a);store.begin_continuation(b.child_id,key);w=store.complete(b,t,ctx,a);path=Path(td.name)/'successful-private.json';save_receipt(path,runtime_wire(w));restored=runtime_restore(load_receipt(path));self.assertEqual(restored.finish_ticks,TickBracket(51,52));self.assertFalse(restored.actual_execution_allowed)
 def test_no_world_constructor_in_435_static_receipt_path(self):
  import ast
  source=Path(__file__).with_name('receipt435.py').read_text();tree=ast.parse(source);self.assertFalse(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ['TerminalVehicleTransition','SourceVehicleTransition','make_env'] for n in ast.walk(tree)))
