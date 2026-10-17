"""473 pre23 natural-control comparison: pure contracts and no-physics wiring."""
import ast,copy,inspect,json,pickle,random,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop,TechnicalStop

class Compare473Tests(unittest.TestCase):
 def fixture_plan(self,root):
  d=root/'stage473';d.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]})
  p=dict(stage=473,deadline_utc='2026-10-20T10:01:55Z',fixed_plan=str(fixed),pace_path=str(pace),scope=dict(ticks=3458,worlds=43),caps=dict(ticks=4096,worlds=43,CPU_s=300,wall_s=600,actual_actions=0,resets=0),sources={},semantic_sources={},protected={},original408_preserve={})
  save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')));return d,p

 def test_all_worlds_qualification_and_once250_parent_costed_without_pulses(self):
  self.assertEqual((1242+216+2*250*4,35+6+2),(3458,43));self.assertLessEqual(3458,4096)
  from retry import compare473 as r
  c=r.contract();self.assertEqual(c['hard'],dict(ticks=4096,worlds=43,CPU_s=300,wall_s=600,actual_actions=0,resets=0,max_parallel=1))
  self.assertEqual(c['root']['native_pre_step'],23);self.assertFalse(c['policy']['forced_first_fullgas']);self.assertEqual(c['whole_parent']['independent_repetitions'],0);self.assertTrue(c['goal']['profile_clock12_260_is_diagnostic_only'])

 def test_source_closure_includes_new_law_and_all_qualification_readers(self):
  from retry import compare473 as r
  code=Path(__file__).resolve().parent;closure=r.source_closure([code/'compare473.py',code/'static473.py'])
  for name in ('law473.py','meter473.py','test_compare473.py','qualify453.py','qualify_parent453.py','observer435.py','terminal410_model.py'):
   self.assertIn((code/name).resolve(),closure)
  paths=r.qualification_source_paths(Path('/workspace/haic-private-retry-20261009'));self.assertTrue(all(path.is_file() for path in paths));self.assertTrue(any(path.name=='qualification_restore12_2-private.json' for path in paths))

 def test_scope_hard_and_native_charge_barriers_stop_before_constructor_or_step(self):
  from retry.meter473 import Meter473
  with tempfile.TemporaryDirectory() as td:
   d,p=self.fixture_plan(Path(td));meter=Meter473(d)
   with patch.object(meter,'guard'):
    meter.active=(0.,0.)
    for ticks in (3458,4096):
     meter.b['reserved_ticks']=ticks
     with self.assertRaises(ResourceStop):meter.step(object(),[],'fixture')
    meter.b['worlds']=43
    with self.assertRaises(ResourceStop):meter.world({},'fixture')
   meter.active=None
   for timing in ((300,0),(0,600)):
    with patch.object(meter,'wholetime',return_value=timing),patch.object(meter,'check_storage'):
     with self.assertRaises(ResourceStop):meter.guard()
   with self.assertRaises(TechnicalStop):meter.begin_actual()
   with self.assertRaises(TechnicalStop):meter.charge('action','fixture')

 def test_saved_common_pre23_join_and_Original_factual_natural_commands(self):
  from retry.law473 import root_inputs473,root_source_paths
  from retry.receipt421_io import load_receipt
  from retry.terminal410_model import from_actual_full
  root=Path('/workspace/haic-private-retry-20261009');state,memory,ledger,rng,blob,expected=root_inputs473(root)
  baseline=load_receipt(root/'stage453/actual_baseline/baseline_step23-before-native-private.json');candidate=load_receipt(root/'stage453/actual_candidate/candidate_step23-before-native-private.json')
  self.assertEqual(baseline['full_pre_before_nominal'],candidate['full_pre_before_nominal']);self.assertEqual(state,from_actual_full(baseline['full_pre_before_nominal']));self.assertEqual(memory,baseline['full_pre_before_nominal']['controller']);self.assertEqual(memory['C']['phase'],'FIRST_LAP');self.assertFalse(ledger.done)
  self.assertEqual(expected[0]['step'],23);self.assertEqual(len(expected),13);self.assertTrue(all(row['command']==row['nominal'] for row in expected));self.assertIs(type(blob),bytes);self.assertTrue(all(path.is_file() for path in root_source_paths(root)))

 def test_first_natural_command_is_not_overridden_and_memory_act_once_per_arm(self):
  from retry import law473 as law
  for arm,nodes,nominal in [(law.ORIGINAL,[0.,20.],[.2,.3,.1]),(law.PROJECTED,[0.,9.],[.2,.7,0.])]:
   binding=law.ReferencePolicy473(arm,nodes,'a'*64);memory=dict(C=dict(phase='FIRST_LAP'),calls=0);ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(memory),phase=lambda:memory['C']['phase'],policy=SimpleNamespace(nodes=binding.nodes.copy()));ctrl.policy.nodes.setflags(write=False)
   def act(model):memory['calls']+=1;return np.asarray(nominal,np.float32)
   ctrl.act=Mock(side_effect=act);child=SimpleNamespace(ctrl=ctrl,m=SimpleNamespace(finish_line_tracker=SimpleNamespace(candidate_crossing_time_s=None)),reference473=binding,initial_count=0,tail_count=0,rows=[],status='ACTIVE')
   def one(tag,**kw):child.rows.append(dict(memory_before=kw['prepared_before'],memory_after=copy.deepcopy(memory),command=kw['first_override'].tolist()))
   child.one=Mock(side_effect=one);record=law.one473(child,arm,0,'first-natural')
   self.assertFalse(record['forced_fullgas']);self.assertTrue(record['natural_command']);self.assertEqual(ctrl.act.call_count,1);self.assertEqual(child.one.call_args.kwargs['prepared_before']['calls'],0);np.testing.assert_array_equal(child.one.call_args.kwargs['first_override'],np.asarray(nominal,np.float32));self.assertNotEqual(child.rows[0]['command'][1:], [1.,0.])
   with self.assertRaises(Exception):law.one473(child,arm,250,'outside')
   self.assertEqual(ctrl.act.call_count,1)

 def test_reference_namespace_digest_immutable_injection_and_Forecast_root_refused(self):
  from retry import law473 as law
  from retry.planner419 import GoalLedger
  from retry.planner419_model_ledger import ForecastLedger
  policies=[law.ReferencePolicy473(arm,[0.,20.],'a'*64) for arm in [law.ORIGINAL,law.PROJECTED]];self.assertNotEqual(policies[0].policy_digest,policies[1].policy_digest)
  memory=dict(C=dict(phase='FIRST_LAP'));ledger=GoalLedger.start(0.,0);child=SimpleNamespace(ctrl=SimpleNamespace(memory=lambda:copy.deepcopy(memory),policy=SimpleNamespace(nodes=np.zeros(2))),m=object(),ledger=ledger)
  with patch.object(law,'snapshot',return_value=dict(immutable=True)):policies[0].inject(child)
  self.assertEqual(child.ctrl.memory(),memory);self.assertIs(child.ledger,ledger);self.assertFalse(child.ctrl.policy.nodes.flags.writeable)
  with self.assertRaises(ValueError):policies[0].nodes[1]=99.
  child.ctrl.policy.nodes=policies[0].nodes.copy()
  with self.assertRaises(Exception):policies[0].check(child)
  meter=SimpleNamespace(qualification_passed=True)
  with patch.object(law,'Child') as constructor:
   with self.assertRaises(Exception):law.root_h13(Path('/unused'),meter,{},[],{}, {},ForecastLedger.fork(ledger),[])
   with self.assertRaises(Exception):law.whole_parents(Path('/unused'),meter,{},[],{}, {},ForecastLedger.fork(ledger),[])
   constructor.assert_not_called()

 def test_after_official_finish_reference_is_not_wrapped_or_recomputed(self):
  from retry.signed417_executor import CoherentExecutor
  fixed=dict(line=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]],free_profile=dict(ds=[10.]*4,speed=[0.,20.,30.,20.,20.]),model=dict(rear_traction_accel=100.,brake_accel=100.,effective_mass=10.));controller=CoherentExecutor(fixed);controller.phase='FINISH_CONFIRM'
  state=dict(time=2.,speed=10.,pos=[.5,0.],vel=[10.,0.])
  with patch.object(controller,'_reference',side_effect=AssertionError('NO_POSTFINISH_REFERENCE')) as reference:
   command,info=controller.act(state,np.asarray([.2,.3,0],np.float32),dict(finish_time_s=1.98));self.assertIsNone(command);self.assertEqual(info['phase'],'DONE');reference.assert_not_called()

 def fake_join(self,mismatch=False,unsafe=False):
  from retry import law473 as law
  from retry.planner419 import GoalLedger
  created=[]
  def frame(index,nodes):
   command=np.asarray([.2,nodes[-1]/100.,0.],np.float32).tolist()
   return dict(memory_before=dict(C=dict(phase='FIRST_LAP'),calls=index),memory_after=dict(C=dict(phase='FIRST_LAP'),calls=index+1),command=command,nominal=command,safety=[],predicted=dict(raw_ticks=4))
  expected=[frame(i,[0.,20.]) for i in range(13)]
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   meter=SimpleNamespace(d=Path(td),qualification_passed=True,b=dict(ticks=0,worlds=0),capture_inputs=Mock(),checkpoint=Mock(),p={})
   class FakeChild:
    def __init__(self,meter,state,memory,ledger,fixed,pace,label,*args,**kw):
     self.label=label;self.rows=[];self.status='ACTIVE';self.error=None;self.initial_count=0;self.tail_count=0;self.closed=False;self.finish_ticks=None;self.memory=dict(C=dict(phase='FIRST_LAP'),calls=0);self.ledger=SimpleNamespace(progress_qualified=lambda:True,deadline_missed=False,done=False)
     self.m=SimpleNamespace(finish_line_tracker=SimpleNamespace(candidate_crossing_time_s=None,finish_time_s=None));self.ctrl=SimpleNamespace(policy=SimpleNamespace(nodes=np.zeros(2)),memory=lambda:copy.deepcopy(self.memory),phase=lambda:self.memory['C']['phase'])
     def act(model):self.memory['calls']+=1;return np.asarray([.2,self.ctrl.policy.nodes[-1]/100.,0.],np.float32)
     self.ctrl.act=Mock(side_effect=act);meter.b['worlds']+=1;created.append(self)
    def one(self,tag,**kw):
     self.rows.append(dict(memory_before=copy.deepcopy(kw['prepared_before']),memory_after=copy.deepcopy(self.memory),command=kw['first_override'].tolist(),nominal=np.asarray(kw['prepared_nominal'],np.float32).tolist(),safety=['path_error_over3m'] if unsafe and self.label.startswith('whole_') else [],predicted=dict(raw_ticks=4)));meter.b['ticks']+=4
     if unsafe and self.label.startswith('whole_'):self.status='UNSAFE';self.error='path_error_over3m'
    def _end_vector(self):return None
    def signature(self):return copy.deepcopy(self.rows)
    def dump(self,d):save(Path(d)/(self.label+'-private.json'),dict(rows=self.rows,status=self.status))
    def close(self):self.closed=True
   stack.enter_context(patch.object(law,'Child',side_effect=FakeChild));stack.enter_context(patch.object(law,'profile_inputs468',return_value=(np.asarray([0.,20.]),np.asarray([0.,9.]),Path('/synthetic-frozen-profile'))));stack.enter_context(patch.object(law,'snapshot',return_value=dict(immutable=True)));replay=stack.enter_context(patch.object(law,'replay',return_value=dict(certified_prefix_actions=13,fresh_current_first_pass=1)));compare=stack.enter_context(patch.object(law,'compare_first'));stack.enter_context(patch.object(law,'compare_frames',return_value=dict(passed=True,wheel=dict(clipped_flag_mismatches=0))))
   stack.enter_context(patch.object(law,'sha',return_value=law.PROJECTED_SHA))  # synthetic profile has no physical file
   ledger=GoalLedger.start(0.,0);stamp=ledger.digest();qualification=law.root_h13(Path(td),meter,{},[],{}, {},ledger,expected)
   self.assertTrue(qualification['passed']);self.assertEqual((meter.b['ticks'],meter.b['worlds']),(216,6));self.assertEqual(replay.call_count,2);self.assertEqual(compare.call_count,2)
   p4=qualification['cohorts'][1];self.assertTrue(all(x['native_factual_actions']==0 and x['factual_calibration'] is None for x in p4['trajectories']))
   if mismatch:
    path=Path(td)/(law.ORIGINAL+'_H13_1-private.json');raw=read(path);raw['rows'][-1]['command'][1]=.999;save(path,raw)
    with self.assertRaisesRegex(Exception,'473_FRESH_QUALIFICATION_PREFIX13_MISMATCH'):law.whole_parents(Path(td),meter,{},[],{}, {},ledger,expected)
    self.assertEqual(len(created),7);self.assertEqual(len(created[-1].rows),13);return qualification,None,created
   whole=law.whole_parents(Path(td),meter,{},[],{}, {},ledger,expected)
   self.assertEqual(ledger.digest(),stamp);self.assertEqual(len(created),8);self.assertTrue(all(c.closed for c in created));self.assertFalse(whole['whole_arm_repeated']);self.assertFalse(whole['actual_execution_allowed']);self.assertEqual(compare.call_count,3)
   self.assertEqual(whole['policies'][1]['native_factual_actions'],0);self.assertEqual(whole['policies'][0]['native_factual_actions'],1)
   self.assertTrue(all(p['initial_count']==p['tail_count']==0 and p['whole_arm_runs']==1 and not p['actual_finish_witness'] for p in whole['policies']))
   return qualification,whole,created

 def test_own_H13_joins_each250_parent_namespace_and_P4_factual_scope_zero(self):
  qualification,whole,children=self.fake_join();self.assertEqual(whole['model_worlds'],2);self.assertEqual(whole['model_ticks'],2000);self.assertIsNone(whole['model_remaining_finish_gain_bracket_s']);self.assertEqual([p['status'] for p in whole['policies']],['SCOPE_CENSORED','SCOPE_CENSORED']);self.assertTrue(all(p['prefix_match13'] for p in whole['policies']))
  for child in children[-2:]:self.assertEqual(len(child.rows),250);self.assertEqual(child.ctrl.act.call_count,250)
  self.assertNotEqual(children[-2].rows[0]['command'],children[-1].rows[0]['command'])

 def test_bad_own_H13_join_stops_before14_and_before_other_whole_parent(self):
  qualification,whole,children=self.fake_join(mismatch=True);self.assertEqual(children[-1].ctrl.act.call_count,13);self.assertTrue(children[-1].closed)

 def test_unsafe_whole_window_closes_each_fixed_law_without_neutral_rescue(self):
  qualification,whole,children=self.fake_join(unsafe=True);self.assertEqual([p['status'] for p in whole['policies']],['UNSAFE','UNSAFE']);self.assertEqual(whole['model_ticks'],8);self.assertEqual(whole['model_worlds'],2);self.assertIsNone(whole['model_remaining_finish_gain_bracket_s'])
  for child in children[-2:]:self.assertEqual((len(child.rows),child.ctrl.act.call_count),(1,1))

 def test_real_runner_same_meter_to_source_and_single_H13_driver_no_extra_rollout(self):
  from retry import compare473 as r,diagnose
  from retry.meter473 import Meter473
  from retry.planner419 import GoalLedger
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  import Box2D
  py=random.getstate();npr=np.random.get_state();seen={}
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   root=Path(td);d,p=self.fixture_plan(root);c=r.contract();ledger_path=root/'untouched-global-ledger.json';save(ledger_path,dict(fixture='immutable'))
   p.update(execution=c,caps=c['hard'],budget_fixture=r.cost_fixture(),world_audit=r.world_audit(),ledger_path=str(ledger_path),ledger_sha256=sha(ledger_path));save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
   folder=root/'stage423/actual_C0';folder.mkdir(parents=True);save(folder/'fork-private.json',dict(controller=dict(before={})));row=dict(progress_before=0.,goal_before=3.24,deadline_before=131);(folder/'trace-private.jsonl').write_text('\n'.join(json.dumps(row) for _ in range(119)))
   state=dict(physical=dict(actual_time=0.));ledger=GoalLedger.start(0.,0);blob=pickle.dumps((py,npr))
   stack.enter_context(patch.object(r,'root_inputs',return_value=(state,{},ledger,{},blob,[])));stack.enter_context(patch.object(r,'from_actual_full',return_value=state));stack.enter_context(patch.object(r,'check_storage',return_value={}))
   stack.enter_context(patch.object(Meter473,'check_storage'))
   real_create=r.create_meter
   def create(path):
    meter=real_create(path);seen['meter']=meter;self.assertIs(type(meter),Meter473);self.assertEqual(meter.worker_start,r.WORKER_START);return meter
   stack.enter_context(patch.object(r,'create_meter',side_effect=create))
   def oldqual(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertIsNotNone(meter.active);meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35);seen['oldqual']=True
   def h13(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertTrue(seen['oldqual']);self.assertTrue(meter.qualification_passed);self.assertIsNotNone(meter.active)
    self.assertTrue(read(d/'preflight-private.json')['passed']);self.assertEqual((meter.nb['actions'],meter.nb['resets']),(0,0));meter.b.update(ticks=1353,reserved_ticks=1353,worlds=41)
    cohorts=[dict(arm=arm,status='COMPLETE_H13') for arm in ['OriginalReference','Projected4Reference']]
    return dict(status='TWO_H13_COHORTS_COMPLETED_REPEAT_EXACT',passed=True,cohorts=cohorts,model_ticks=216,model_worlds=6,policyrecords_path=str(d/'policyrecords-private.json'),cohortresults_path=str(d/'cohortresults.json'),actual_execution_allowed=False)
   def whole(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertEqual((meter.b['ticks'],meter.b['worlds']),(1353,41));self.assertIsNotNone(meter.active);meter.b.update(ticks=3353,reserved_ticks=3353,worlds=43);seen['whole_entered']=True
    return dict(status='TWO_WHOLE_PARENTS_FINISHED',policies=[dict(arm='OriginalReference'),dict(arm='Projected4Reference')],model_worlds=2,model_ticks=2000,whole_arm_repeated=False,actual_execution_allowed=False)
   whole_driver=stack.enter_context(patch.object(r,'whole_parents',side_effect=whole))
   stack.enter_context(patch.object(r,'qualify',side_effect=oldqual));stack.enter_context(patch.object(r,'qualify_pending'));stack.enter_context(patch.object(r,'qualify_parent'));driver=stack.enter_context(patch.object(r,'root_h13',side_effect=h13))
   timers=stack.enter_context(patch.object(r.signal,'setitimer'));forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE'))));forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_WORLD'))))
   r.run(root);driver.assert_called_once();whole_driver.assert_called_once();self.assertTrue(seen['whole_entered']);out=read(d/'result.json');self.assertEqual(out['status'],'WHOLE_COMPARISON_COMPLETE');self.assertIsNone(out['error']);self.assertEqual(sha(ledger_path),p['ledger_sha256'])
   self.assertEqual((seen['meter'].b['ticks'],seen['meter'].b['worlds']),(3353,43));nonzero=[x.args for x in timers.call_args_list if x.args[1]>0];self.assertTrue(nonzero)
   for kind,seconds in nonzero:self.assertLessEqual(seconds,300 if kind==r.signal.ITIMER_PROF else 600)
   for mock in forbidden:mock.assert_not_called()
  self.assertEqual(random.getstate(),py);now=np.random.get_state();self.assertEqual(now[0],npr[0]);np.testing.assert_array_equal(now[1],npr[1]);self.assertEqual(now[2:],npr[2:])
