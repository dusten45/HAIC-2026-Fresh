"""465 bounded H13 law and actual runner wiring fixtures; no integration."""
import copy,json,pickle,random,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop,TechnicalStop

class Compare465Tests(unittest.TestCase):
 def fixture_plan(self,root):
  d=root/'stage465';d.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]})
  p=dict(stage=465,deadline_utc='2026-10-20T10:01:55Z',fixed_plan=str(fixed),pace_path=str(pace),scope=dict(ticks=1458,worlds=41),caps=dict(ticks=2048,worlds=64,CPU_s=180,wall_s=300,max_parallel=1,actual_actions=0,resets=0),sources={},semantic_sources={},protected={},original408_preserve={},contract_sha256='fixture')
  save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
  return d,p

 def test_scope_separate_from_hard_caps_and_no_native_authority(self):
  from retry.meter465 import Meter465
  with tempfile.TemporaryDirectory() as td:
   d,p=self.fixture_plan(Path(td));meter=Meter465(d)
   with patch.object(meter,'guard'):
    meter.active=(0.,0.)
    for ticks in (1458,2048):
     meter.b['reserved_ticks']=ticks
     with self.assertRaises(ResourceStop):meter.step(object(),[],'fixture')
    for worlds in (41,64):
     meter.b['worlds']=worlds
     with self.assertRaises(ResourceStop):meter.world({},'fixture')
   meter.active=None
   for timing in ((180,0),(0,300)):
    with patch.object(meter,'wholetime',return_value=timing),patch.object(meter,'check_storage'):
     with self.assertRaises(ResourceStop):meter.guard()
   with self.assertRaises(TechnicalStop):meter.begin_actual()
   with self.assertRaises(TechnicalStop):meter.charge('action','PulseOnce')
   self.assertEqual((meter.nb['actions'],meter.nb['resets']),(0,0))

 def test_frozen_cost_has_only_four_H13_and_two_held_first_no_extra_main(self):
  from retry.design464_math import calculate
  c=read(Path(__file__).resolve().parent/'design464_next.json');b=calculate(c)
  self.assertEqual((b['ticks'],b['worlds']),(1458,41));self.assertEqual((b['trajectory_worlds'],b['held_first_worlds'],b['separate_main_parent_worlds']),(4,2,0))
  self.assertEqual(c['selected_contract']['actions_per_trajectory'],13);self.assertEqual(c['selected_contract']['independent_trajectories_per_arm'],2)

 def test_prepared_nominal_and_memory_advance_once_with_exact_full_command(self):
  from retry.law465 import _one465
  memory=dict(C=dict(phase='FIRST_LAP'),calls=0);nominal=np.asarray([.2,.3,.1],np.float32);calls=[]
  ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(memory),phase=lambda:'FIRST_LAP')
  def act(model):memory['calls']+=1;return nominal
  ctrl.act=Mock(side_effect=act);child=SimpleNamespace(ctrl=ctrl,m=object(),rows=[],status='ACTIVE')
  def one(tag,**kw):
   calls.append(kw);child.rows.append(dict(memory_before=copy.deepcopy(kw['prepared_before']),memory_after=copy.deepcopy(memory),command=kw['first_override'].tolist()))
  child.one=one;record=_one465(child,'PulseOnce',0,'fixture')
  self.assertEqual(ctrl.act.call_count,1);self.assertEqual(memory['calls'],1);self.assertEqual(calls[0]['prepared_before']['calls'],0);self.assertIs(calls[0]['prepared_nominal'],nominal)
  np.testing.assert_array_equal(calls[0]['first_override'],np.asarray([nominal[0],1.,0.],np.float32));self.assertEqual(record['nominal_calls'],1)
  _one465(child,'PulseOnce',1,'fixture');self.assertEqual(ctrl.act.call_count,2);np.testing.assert_array_equal(calls[1]['first_override'],nominal)
  with self.assertRaises(Exception):_one465(child,'PulseOnce',13,'fixture')
  self.assertEqual(ctrl.act.call_count,2)

 def test_S13_recomputes_each_boundary_and_passes_prepared_inputs(self):
  from retry import law465 as law
  memory=dict(C=dict(phase='FIRST_LAP'),calls=0);nominal=np.asarray([.2,.3,.1],np.float32);ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(memory),phase=lambda:'FIRST_LAP')
  def act(model):memory['calls']+=1;return nominal
  ctrl.act=Mock(side_effect=act);child=SimpleNamespace(ctrl=ctrl,m=SimpleNamespace(car=SimpleNamespace(hull=SimpleNamespace(position=[1.,2.],linearVelocity=[3.,4.]))),fixed={},pace=[],rows=[],status='ACTIVE')
  def one(tag,**kw):child.rows.append(dict(memory_before=copy.deepcopy(kw['prepared_before']),memory_after=copy.deepcopy(memory),command=kw['first_override'].tolist()))
  child.one=Mock(side_effect=one);commands=[np.asarray([.2,.7,0],np.float32),np.asarray([.2,0,.2],np.float32)]
  with patch.object(law,'command465',side_effect=commands) as command:
   law._one465(child,'S13',1,'fixture');child.m.car.hull.position=[2.,3.];law._one465(child,'S13',2,'fixture')
   self.assertEqual(command.call_count,2);self.assertEqual(command.call_args_list[0].args[2],[1.,2.]);self.assertEqual(command.call_args_list[1].args[2],[2.,3.])
  self.assertEqual(ctrl.act.call_count,2);self.assertEqual(memory['calls'],2)
  for call,expected in zip(child.one.call_args_list,commands):
   self.assertIs(call.kwargs['prepared_nominal'],nominal);np.testing.assert_array_equal(call.kwargs['first_override'],expected)

 def test_general_law_full_float32_matches_saved_math_and_strict_domain(self):
  from retry.law465 import command465
  from retry.static464 import Design464Tests
  from retry.design464_math import saved_secant_terms
  fixed,pace,row=Design464Tests().fixture();row['nominal']=[.123456789,.8,.2]
  expected=saved_secant_terms(fixed,pace,row)['command'];command=command465(fixed,pace,row['pre']['pos'],row['pre']['vel'],row['nominal'],'FIRST_LAP')
  self.assertEqual(command.dtype,np.dtype(np.float32));np.testing.assert_array_equal(command,np.asarray(expected,np.float32));self.assertEqual(command[0],np.float32(row['nominal'][0]))
  for vel in ([0.,0.],[-10.,0.],[1000.,0.]):
   with self.assertRaises(TechnicalStop):command465(fixed,pace,row['pre']['pos'],vel,row['nominal'],'FIRST_LAP')
  with self.assertRaises(TechnicalStop):command465(fixed,pace,row['pre']['pos'],row['pre']['vel'],row['nominal'],'FINISH_CONFIRM')

 def test_H13_early_progress_is_error_and_pending_is_scope_exit_without_tail(self):
  from retry.law465 import _finish465,_scope465
  child=SimpleNamespace(rows=[dict(safety=[]) for _ in range(12)],status='INFEASIBLE',error='predicted_progress_deadline',ledger=SimpleNamespace(progress_qualified=lambda:False,deadline_missed=True),_end_vector=lambda:{},m=SimpleNamespace(finish_line_tracker=SimpleNamespace(finish_time_s=None,candidate_crossing_time_s=None)),ctrl=SimpleNamespace(phase=lambda:'FIRST_LAP'))
  with self.assertRaisesRegex(TechnicalStop,'unsupported_early_progress'):_finish465(child)
  child.rows.append(dict(safety=[]));_finish465(child);self.assertFalse(child.initial_progress)
  child.m.finish_line_tracker.candidate_crossing_time_s=1.;self.assertEqual(_scope465(child),'PENDING_FINISH_SCOPE_EXIT')
  child.m.finish_line_tracker.finish_time_s=1.;self.assertEqual(_scope465(child),'OFFICIAL_MODEL_FINISH_SCOPE_EXIT')

 def test_saved_root_first_law_command_is_exact_fullgas_alias_only(self):
  from retry.compare462 import root_inputs
  from retry.law465 import command465
  root=Path('/workspace/haic-private-retry-20261009');state,memory,ledger,rng,blob,expected=root_inputs(root);p=read(root/'stage453/plan.json');fixed=read(p['fixed_plan']);pace=np.asarray(read(p['pace_path'])['frozen268']);row=expected[0];nominal=np.asarray(row['nominal'],np.float32)
  command=command465(fixed,pace,row['pre']['pos'],row['pre']['vel'],nominal,'FIRST_LAP');alias=nominal.copy();alias[1:]=[1.,0.]
  np.testing.assert_array_equal(command,alias)

 def test_real_runner_same_meter_to_source_and_single_H13_driver_no_extra_rollout(self):
  from retry import compare465 as r,diagnose
  from retry.meter465 import Meter465
  from retry.planner419 import GoalLedger
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  import Box2D
  py=random.getstate();npr=np.random.get_state();seen={}
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   root=Path(td);d,p=self.fixture_plan(root);c=r.contract();ledger_path=root/'untouched-global-ledger.json';save(ledger_path,dict(fixture='immutable'))
   p.update(execution=c,caps=c['selected_contract']['hard'],budget_fixture=r.calculate(c),ledger_path=str(ledger_path),ledger_sha256=sha(ledger_path));save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
   folder=root/'stage423/actual_C0';folder.mkdir(parents=True);save(folder/'fork-private.json',dict(controller=dict(before={})));row=dict(progress_before=0.,goal_before=3.24,deadline_before=131);(folder/'trace-private.jsonl').write_text('\n'.join(json.dumps(row) for _ in range(119)))
   state=dict(physical=dict(actual_time=0.));ledger=GoalLedger.start(0.,0);blob=pickle.dumps((py,npr))
   stack.enter_context(patch.object(r,'root_inputs',return_value=(state,{},ledger,{},blob,[])));stack.enter_context(patch.object(r,'from_actual_full',return_value=state));stack.enter_context(patch.object(r,'check_storage',return_value={}))
   stack.enter_context(patch.object(Meter465,'check_storage'))
   real_create=r.create_meter
   def create(path):
    meter=real_create(path);seen['meter']=meter;self.assertIs(type(meter),Meter465);self.assertEqual(meter.worker_start,r.WORKER_START);return meter
   stack.enter_context(patch.object(r,'create_meter',side_effect=create))
   def oldqual(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertIsNotNone(meter.active);meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35);seen['oldqual']=True
   def h13(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertTrue(seen['oldqual']);self.assertTrue(meter.qualification_passed);self.assertIsNotNone(meter.active)
    self.assertTrue(read(d/'preflight-private.json')['passed']);self.assertEqual((meter.nb['actions'],meter.nb['resets']),(0,0));meter.b.update(ticks=1353,reserved_ticks=1353,worlds=41)
    cohorts=[dict(arm=arm,status='COMPLETE_H13') for arm in ['PulseOnce','S13']]
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
