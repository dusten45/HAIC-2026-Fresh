"""468 frozen-reference gate: pure law, explicit budget and runner wiring."""
import ast,copy,inspect,json,pickle,random,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop,TechnicalStop

class Compare468Tests(unittest.TestCase):
 def fixture_plan(self,root):
  d=root/'stage468';d.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]})
  p=dict(stage=468,deadline_utc='2026-10-20T10:01:55Z',fixed_plan=str(fixed),pace_path=str(pace),scope=dict(ticks=1458,worlds=41),caps=dict(ticks=1536,worlds=41,CPU_s=180,wall_s=300,max_parallel=1,actual_actions=0,resets=0),sources={},semantic_sources={},protected={},original408_preserve={},contract_sha256='fixture')
  save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
  return d,p

 def test_fresh_world_audit_29_plus3_plus3_plus6_no_hidden_parent(self):
  from retry.qualify453 import qualify,qualify_pending
  from retry.qualify_parent453 import qualify as qualify_parent
  from retry.law468 import root_h13
  def loops(function):
   tree=ast.parse(inspect.getsource(function));return [ast.unparse(node.iter) for node in ast.walk(tree) if isinstance(node,ast.For)]
  old=loops(qualify);self.assertIn("['C0', 'P']",old);self.assertIn('range(2)',old);self.assertIn('range(12)',old)
  self.assertIn('range(2)',loops(qualify_pending));self.assertIn('range(2)',loops(qualify_parent))
  root=loops(root_h13);self.assertIn('[1, 2]',root);self.assertIn('range(13)',root)
  world_parts=dict(saved_replay=1+2*2+12*2,pending=1+2,parent_pending=1+2,law_trajectories=2*2,held_first=2)
  self.assertEqual(world_parts,dict(saved_replay=29,pending=3,parent_pending=3,law_trajectories=4,held_first=2));self.assertEqual(sum(world_parts.values()),41)
  self.assertEqual((1242+2*(2*13*4+4),35+2*3),(1458,41))

 def test_scope_and_hard_caps_stop_before_any_world_or_step_and_native_forbidden(self):
  from retry.meter468 import Meter468
  with tempfile.TemporaryDirectory() as td:
   d,p=self.fixture_plan(Path(td));meter=Meter468(d)
   with patch.object(meter,'guard'):
    meter.active=(0.,0.)
    for ticks in (1458,1536):
     meter.b['reserved_ticks']=ticks
     with self.assertRaises(ResourceStop):meter.step(object(),[],'fixture')
    meter.b['worlds']=41
    with self.assertRaises(ResourceStop):meter.world({},'fixture')
   meter.active=None
   for timing in ((180,0),(0,300)):
    with patch.object(meter,'wholetime',return_value=timing),patch.object(meter,'check_storage'):
     with self.assertRaises(ResourceStop):meter.guard()
   with self.assertRaises(TechnicalStop):meter.begin_actual()
   with self.assertRaises(TechnicalStop):meter.charge('action','OriginalReferenceCommonPulse')
   self.assertEqual((meter.nb['actions'],meter.nb['resets']),(0,0))

 def test_original_point_feedforward_matches_real_executor_for_each_own_reference(self):
  from retry.law468 import command468
  from retry.signed417_executor import CoherentExecutor
  fixed=dict(line=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]],free_profile=dict(ds=[10.]*4,speed=[0.,20.,30.,20.,10.]),model=dict(rear_traction_accel=100.,brake_accel=100.,effective_mass=10.))
  nominal=np.asarray([.123456789,.2,0],np.float32);state=dict(pos=[10.,2.],vel=[0.,15.],speed=15.,time=1.);outputs=[]
  for nodes in ([0.,20.,30.,20.,10.],[0.,18.,24.,18.,9.]):
   executor=CoherentExecutor(fixed);executor.nodes=np.asarray(nodes);executor.phase='FIRST_LAP'
   expected,detail=executor.act(state,nominal,dict(finish_time_s=None,candidate_crossing_time_s=None))
   actual=command468(fixed,nodes,state['pos'],state['vel'],nominal,'FIRST_LAP')
   np.testing.assert_array_equal(actual,expected);self.assertEqual(actual.dtype,np.dtype(np.float32));self.assertEqual(actual[0],nominal[0]);outputs.append(actual)
  self.assertFalse(np.array_equal(*outputs))
  with self.assertRaises(Exception):command468(fixed,nodes,state['pos'],state['vel'],nominal,'FINISH_CONFIRM')

 def test_frozen_own_profile_injection_preserves_memory_world_and_ledger(self):
  from retry import law468 as law
  from retry.planner419 import GoalLedger
  nodes=np.asarray([0.,18.,24.,18.,9.]);first=np.asarray([.2,1.,0.],np.float32);binding=law.ReferencePolicy468(law.PROJECTED,nodes,'a'*64,first)
  memory=dict(index=3,C=dict(phase='FIRST_LAP'));ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(memory),policy=SimpleNamespace(nodes=np.zeros(5)));child=SimpleNamespace(ctrl=ctrl,m=object(),ledger=GoalLedger.start(0.,0))
  stamp=child.ledger.digest()
  with patch.object(law,'snapshot',return_value=dict(immutable='synthetic')):binding.inject(child)
  self.assertEqual(ctrl.memory(),memory);self.assertEqual(child.ledger.digest(),stamp);self.assertIs(child.reference468,binding);self.assertFalse(ctrl.policy.nodes.flags.writeable)
  nodes[1]=999.;self.assertEqual(binding.nodes[1],18.);binding.check(child)
  with self.assertRaises(ValueError):binding.nodes[1]=999.
  ctrl.policy.nodes=np.asarray([0.,18.,24.,18.,9.])
  with self.assertRaises(Exception):binding.check(child)
  ctrl.policy.nodes=binding.nodes.copy();ctrl.policy.nodes.setflags(write=False);binding.source_sha='b'*64
  with self.assertRaises(Exception):binding.check(child)

 def test_common_first_and_prepared_memory_act_once_then_own_nominal(self):
  from retry import law468 as law
  for arm in (law.ORIGINAL,law.PROJECTED):
   memory=dict(C=dict(phase='FIRST_LAP'),calls=0);first=np.asarray([.2,1.,0.],np.float32);nominals=[first,np.asarray([.2,.4,.1],np.float32)];binding=law.ReferencePolicy468(arm,[0.,10.],'a'*64,first)
   ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(memory),phase=lambda:'FIRST_LAP',policy=SimpleNamespace(nodes=binding.nodes.copy()))
   ctrl.policy.nodes.setflags(write=False)
   def act(model):
    command=nominals[memory['calls']];memory['calls']+=1;return command
   ctrl.act=Mock(side_effect=act);child=SimpleNamespace(ctrl=ctrl,m=object(),rows=[],status='ACTIVE',reference468=binding)
   def one(tag,**kw):child.rows.append(dict(memory_before=copy.deepcopy(kw['prepared_before']),memory_after=copy.deepcopy(memory),command=kw['first_override'].tolist()))
   child.one=Mock(side_effect=one)
   a=law.one468(child,arm,0,'fixture');law.one468(child,arm,1,'fixture')
   self.assertEqual(ctrl.act.call_count,2);self.assertEqual(memory['calls'],2);self.assertTrue(a['first_fullgas_alias'])
   for i,call in enumerate(child.one.call_args_list):
    self.assertIs(call.kwargs['prepared_nominal'],nominals[i]);self.assertEqual(call.kwargs['prepared_before']['calls'],i);np.testing.assert_array_equal(call.kwargs['first_override'],nominals[i])
   with self.assertRaises(Exception):law.one468(child,arm,13,'fixture')
   self.assertEqual(ctrl.act.call_count,2)

 def test_forecast_ledger_never_replaces_readonly_native_root_and_no_hidden_world(self):
  from retry import law468 as law
  from retry.planner419 import GoalLedger
  from retry.planner419_model_ledger import ForecastLedger
  ledger=ForecastLedger.fork(GoalLedger.start(0.,0));meter=SimpleNamespace(qualification_passed=True)
  with patch.object(law,'Child') as constructor:
   with self.assertRaises(Exception):law.root_h13(Path('/unused'),meter,{},[],{}, {},ledger,[])
   constructor.assert_not_called()

 def test_frozen_projected_source_original_match_natural_first_and_no_secant_contract(self):
  from retry import law468 as law,compare468 as runner
  root=Path('/workspace/haic-private-retry-20261009');p=read(root/'stage453/plan.json');fixed=read(p['fixed_plan']);pace=np.asarray(read(p['pace_path'])['frozen268'])
  original,projected,path=law.profile_inputs468(root,fixed,pace)
  self.assertEqual(sha(path),law.PROJECTED_SHA);np.testing.assert_array_equal(original,np.asarray(fixed['free_profile']['speed'])*pace);self.assertTrue(np.all(projected<=original))
  state,memory,ledger,rng,blob,expected=runner.root_inputs(root);actual=law.natural_first468(fixed,projected,expected[0]);alias=np.asarray(expected[0]['nominal'],np.float32);alias[1:]=[1.,0.];np.testing.assert_array_equal(actual,alias)
  c=runner.contract();self.assertEqual(c['selected_contract']['arms'],[law.ORIGINAL,law.PROJECTED]);self.assertNotIn('secant',str(c['selected_contract']['policy']).lower());self.assertEqual((c['selected_contract']['hard']['ticks'],c['selected_contract']['hard']['worlds']),(1536,41))

 def test_real_runner_same_meter_to_source_and_single_H13_driver_no_extra_rollout(self):
  from retry import compare468 as r,diagnose
  from retry.meter468 import Meter468
  from retry.planner419 import GoalLedger
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  import Box2D
  py=random.getstate();npr=np.random.get_state();seen={}
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   root=Path(td);d,p=self.fixture_plan(root);c=r.contract();ledger_path=root/'untouched-global-ledger.json';save(ledger_path,dict(fixture='immutable'))
   p.update(execution=c,caps=c['selected_contract']['hard'],budget_fixture=r.calculate(c),world_audit=r.world_audit(),ledger_path=str(ledger_path),ledger_sha256=sha(ledger_path));save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
   folder=root/'stage423/actual_C0';folder.mkdir(parents=True);save(folder/'fork-private.json',dict(controller=dict(before={})));row=dict(progress_before=0.,goal_before=3.24,deadline_before=131);(folder/'trace-private.jsonl').write_text('\n'.join(json.dumps(row) for _ in range(119)))
   state=dict(physical=dict(actual_time=0.));ledger=GoalLedger.start(0.,0);blob=pickle.dumps((py,npr))
   stack.enter_context(patch.object(r,'root_inputs',return_value=(state,{},ledger,{},blob,[])));stack.enter_context(patch.object(r,'from_actual_full',return_value=state));stack.enter_context(patch.object(r,'check_storage',return_value={}))
   stack.enter_context(patch.object(Meter468,'check_storage'))
   real_create=r.create_meter
   def create(path):
    meter=real_create(path);seen['meter']=meter;self.assertIs(type(meter),Meter468);self.assertEqual(meter.worker_start,r.WORKER_START);return meter
   stack.enter_context(patch.object(r,'create_meter',side_effect=create))
   def oldqual(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertIsNotNone(meter.active);meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35);seen['oldqual']=True
   def h13(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertTrue(seen['oldqual']);self.assertTrue(meter.qualification_passed);self.assertIsNotNone(meter.active)
    self.assertTrue(read(d/'preflight-private.json')['passed']);self.assertEqual((meter.nb['actions'],meter.nb['resets']),(0,0));meter.b.update(ticks=1353,reserved_ticks=1353,worlds=41)
    cohorts=[dict(arm=arm,status='COMPLETE_H13') for arm in ['OriginalReferenceCommonPulse','Projected4ReferenceCommonPulse']]
    return dict(status='TWO_H13_COHORTS_COMPLETED_REPEAT_EXACT',passed=True,cohorts=cohorts,model_ticks=216,model_worlds=6,policyrecords_path=str(d/'policyrecords-private.json'),cohortresults_path=str(d/'cohortresults.json'),actual_execution_allowed=False)
   stack.enter_context(patch.object(r,'qualify',side_effect=oldqual));stack.enter_context(patch.object(r,'qualify_pending'));stack.enter_context(patch.object(r,'qualify_parent'));driver=stack.enter_context(patch.object(r,'root_h13',side_effect=h13))
   timers=stack.enter_context(patch.object(r.signal,'setitimer'));forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE'))));forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_WORLD'))))
   r.run(root);driver.assert_called_once();out=read(d/'result.json');self.assertEqual(out['status'],'H13_COMPARISON_COMPLETE');self.assertIsNone(out['error']);self.assertEqual(sha(ledger_path),p['ledger_sha256'])
   self.assertEqual((seen['meter'].b['ticks'],seen['meter'].b['worlds']),(1353,41));nonzero=[x.args for x in timers.call_args_list if x.args[1]>0];self.assertTrue(nonzero)
   for kind,seconds in nonzero:self.assertLessEqual(seconds,180 if kind==r.signal.ITIMER_PROF else 300)
   for mock in forbidden:mock.assert_not_called()
  self.assertEqual(random.getstate(),py);now=np.random.get_state();self.assertEqual(now[0],npr[0]);np.testing.assert_array_equal(now[1],npr[1]);self.assertEqual(now[2:],npr[2:])
