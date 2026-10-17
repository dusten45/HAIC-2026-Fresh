"""470 one whole-law pair: pure control and no-physics startup fixtures."""
import ast,copy,inspect,json,pickle,random,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock,patch
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop,TechnicalStop

class Compare470Tests(unittest.TestCase):
 def fixture_plan(self,root):
  d=root/'stage469-revision1';d.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]})
  p=dict(stage=470,revision='469-revision1',deadline_utc='2026-10-20T10:01:55Z',fixed_plan=str(fixed),pace_path=str(pace),scope=dict(ticks=2018,worlds=43),caps=dict(ticks=2048,worlds=43,CPU_s=180,wall_s=300,actual_actions=0,resets=0),sources={},semantic_sources={},protected={},original408_preserve={},contract_sha256='fixture')
  save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
  return d,p

 def test_two_whole_parents_add_only560ticks2worlds_without_whole_repeat(self):
  self.assertEqual((1458+2*70*4,41+2),(2018,43));self.assertLessEqual(2018,2048)
  from retry import compare470 as r
  c=r.contract();self.assertEqual(c['hard'],dict(ticks=2048,worlds=43,CPU_s=180,wall_s=300,actual_actions=0,resets=0))
  self.assertFalse(c['qualification']['independent_whole_arm_repetition']);self.assertEqual(c['whole_parent']['max_actions_each'],70);self.assertEqual(c['whole_parent']['extra_ticks_after_pending_at_cap'],0);self.assertEqual(c['whole_parent']['capture_held_auxiliary_extra_worlds'],0)

 def test_finish_confirmation_keeps_own_final_reference_with_original_point_law(self):
  from retry.signed417_executor import CoherentExecutor
  fixed=dict(line=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]],free_profile=dict(ds=[10.]*4,speed=[0.,20.,30.,20.,20.]),model=dict(rear_traction_accel=100.,brake_accel=100.,effective_mass=10.))
  finish=dict(finish_time_s=None,candidate_crossing_time_s=1.9,qualified_time_s=1.9,crossing_from_back=True,center=[0.,0.],forward=[1.,0.],half_width=4.,half_depth=1.)
  state=dict(pos=[.5,0.],vel=[10.,0.],speed=10.,time=2.);commands=[]
  for nodes in ([0.,20.,30.,20.,20.],[0.,18.,24.,18.,9.]):
   executor=CoherentExecutor(fixed);executor.nodes=np.asarray(nodes);executor.nodes.setflags(write=False);executor.phase='FINISH_CONFIRM'
   command,detail=executor.act(state,np.asarray([.2,.5,0.],np.float32),finish)
   self.assertEqual(executor.phase,'FINISH_CONFIRM');self.assertEqual(detail['r'],nodes[-1]);self.assertEqual(detail['f'],0.);self.assertEqual(command[0],np.float32(.2));commands.append(command)
  self.assertGreater(commands[0][1],0.);self.assertGreater(commands[1][2],0.)

 def test_scope_hard_guard_and_native_authority_remain_closed(self):
  from retry.meter470 import Meter470
  with tempfile.TemporaryDirectory() as td:
   d,p=self.fixture_plan(Path(td));meter=Meter470(d)
   with patch.object(meter,'guard'):
    meter.active=(0.,0.)
    for ticks in (2018,2048):
     meter.b['reserved_ticks']=ticks
     with self.assertRaises(ResourceStop):meter.step(object(),[],'fixture')
    meter.b['worlds']=43
    with self.assertRaises(ResourceStop):meter.world({},'fixture')
   meter.active=None
   with self.assertRaises(TechnicalStop):meter.begin_actual()
   with self.assertRaises(TechnicalStop):meter.charge('action','fixture')

 def fake_whole(self,unsafe=False,prefix_mismatch=False):
  from retry import law470 as law,law468
  from retry.planner419 import GoalLedger
  created=[];first=np.asarray([.2,1.,0.],np.float32)
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   meter=SimpleNamespace(d=Path(td),qualification_passed=True,b=dict(ticks=0,worlds=0),capture_inputs=Mock(),checkpoint=Mock())
   class FakeChild:
    def __init__(self,meter,state,memory,ledger,fixed,pace,label,*args,**kw):
     self.meter=meter;self.label=label;self.rows=[];self.nominal_log=[];self.status='ACTIVE';self.error=None;self.initial_count=0;self.tail_count=0;self.ledger=ledger;self.closed=False;self.finish_ticks=None;self.memory=dict(C=dict(phase='FIRST_LAP'),calls=0)
     self.m=SimpleNamespace(finish_line_tracker=SimpleNamespace(candidate_crossing_time_s=None,finish_time_s=None));self.ctrl=SimpleNamespace(policy=SimpleNamespace(nodes=np.zeros(2)),memory=lambda:copy.deepcopy(self.memory),phase=lambda:self.memory['C']['phase'])
     def act(model):
      self.memory['calls']+=1
      if self.memory['calls']>=69:self.memory['C']['phase']='FINISH_CONFIRM';self.m.finish_line_tracker.candidate_crossing_time_s=1.
      command=(first if law.PROJECTED in self.label else np.asarray([.2,.3,.1],np.float32)) if self.memory['calls']==1 else np.asarray([.2,.4,0.],np.float32)
      self.nominal_log.append(command.copy());return command
     self.ctrl.act=Mock(side_effect=act);meter.b['worlds']+=1;created.append(self)
    def one(self,tag,**kw):
     self.rows.append(dict(memory_before=copy.deepcopy(kw['prepared_before']),memory_after=copy.deepcopy(self.memory),command=kw['first_override'].tolist(),safety=['path_error_over3m'] if unsafe else [],predicted=dict(raw_ticks=4)))
     self.meter.b['ticks']+=4
     if unsafe:self.status='UNSAFE';self.error='path_error_over3m'
    def dump(self,d):pass
    def close(self):self.closed=True
   stack.enter_context(patch.object(law,'Child',side_effect=FakeChild));stack.enter_context(patch.object(law,'profile_inputs468',return_value=(np.asarray([0.,10.]),np.asarray([0.,9.]),Path('/synthetic-frozen-profile'))));stack.enter_context(patch.object(law,'natural_first468',return_value=first));stack.enter_context(patch.object(law,'compare_first'));stack.enter_context(patch.object(law468,'snapshot',return_value=dict(synthetic='no-world')))
   qualified=[]
   for index in range(13):
    qualified.append(dict(memory_before=dict(C=dict(phase='FIRST_LAP'),calls=index),memory_after=dict(C=dict(phase='FIRST_LAP'),calls=index+1),command=(first if index==0 else np.asarray([.2,.4,0.],np.float32)).tolist(),safety=[],predicted=dict(raw_ticks=4)))
   for arm in (law.ORIGINAL,law.PROJECTED):save(Path(td)/(arm+'_H13_1-private.json'),dict(rows=qualified))
   if prefix_mismatch:
    changed=copy.deepcopy(qualified);changed[-1]['command'][1]=.1;save(Path(td)/(law.ORIGINAL+'_H13_1-private.json'),dict(rows=changed))
   ledger=GoalLedger.start(0.,0);before=ledger.digest()
   if prefix_mismatch:
    with self.assertRaisesRegex(Exception,'470_FRESH_QUALIFICATION_PREFIX13_MISMATCH'):law.whole_parents(Path(td),meter,{},[],{}, {},ledger,[dict(command=first.tolist())])
    self.assertEqual(ledger.digest(),before);self.assertEqual(len(created),1);self.assertTrue(created[0].closed);return None,created
   out=law.whole_parents(Path(td),meter,{},[],{}, {},ledger,[dict(command=first.tolist())])
   self.assertEqual(ledger.digest(),before);self.assertEqual(meter.capture_inputs.call_count,2);self.assertEqual(len(created),2);self.assertTrue(all(c.closed for c in created));self.assertFalse(out['whole_arm_repeated']);self.assertFalse(out['actual_execution_allowed'])
   self.assertEqual([p['whole_arm_runs'] for p in out['policies']],[1,1]);self.assertTrue(all(not p['actual_finish_witness'] and p['tail_count']==p['initial_count']==0 for p in out['policies']))
   return out,created

 def test_pending_at70_is_censored_without_extra_tail_world_rescue_or_whole_repeat(self):
  out,children=self.fake_whole();self.assertEqual(out['model_ticks'],560);self.assertEqual(out['model_worlds'],2)
  self.assertEqual([p['status'] for p in out['policies']],['SCOPE_CENSORED','SCOPE_CENSORED']);self.assertIsNone(out['model_remaining_finish_gain_bracket_s'])
  for child in children:
   self.assertEqual(len(child.rows),70);self.assertEqual(child.ctrl.act.call_count,70);self.assertEqual(child.memory['C']['phase'],'FINISH_CONFIRM');self.assertIsNotNone(child.m.finish_line_tracker.candidate_crossing_time_s)
   np.testing.assert_array_equal(np.asarray(child.rows[0]['command'],np.float32),np.asarray([.2,1.,0.],np.float32))
  self.assertFalse(np.array_equal(children[0].nominal_log[0],children[1].nominal_log[0]))

 def test_typed_unsafe_closes_fixed_law_without_neutral_rescue(self):
  out,children=self.fake_whole(unsafe=True);self.assertEqual([p['status'] for p in out['policies']],['UNSAFE','UNSAFE']);self.assertIsNone(out['model_remaining_finish_gain_bracket_s'])
  self.assertEqual(out['model_ticks'],8);self.assertEqual(out['model_worlds'],2)
  for child in children:self.assertEqual((len(child.rows),child.ctrl.act.call_count),(1,1))

 def test_fresh_H13_mismatch_stops_before14_without_next_parent_or_world(self):
  out,children=self.fake_whole(prefix_mismatch=True);self.assertEqual(len(children[0].rows),13);self.assertEqual(children[0].ctrl.act.call_count,13)

 def test_actual_readonly_root_forecast_cannot_authorize_whole_parent(self):
  from retry import law470 as law
  from retry.planner419 import GoalLedger
  from retry.planner419_model_ledger import ForecastLedger
  meter=SimpleNamespace(qualification_passed=True)
  with patch.object(law,'Child') as constructor:
   with self.assertRaises(Exception):law.whole_parents(Path('/unused'),meter,{},[],{}, {},ForecastLedger.fork(GoalLedger.start(0.,0)),[])
   constructor.assert_not_called()

 def test_real_runner_same_meter_to_source_and_single_H13_driver_no_extra_rollout(self):
  from retry import compare470 as r,diagnose
  from retry.meter470 import Meter470
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
   stack.enter_context(patch.object(Meter470,'check_storage'))
   real_create=r.create_meter
   def create(path):
    meter=real_create(path);seen['meter']=meter;self.assertIs(type(meter),Meter470);self.assertEqual(meter.worker_start,r.WORKER_START);return meter
   stack.enter_context(patch.object(r,'create_meter',side_effect=create))
   def oldqual(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertIsNotNone(meter.active);meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35);seen['oldqual']=True
   def h13(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertTrue(seen['oldqual']);self.assertTrue(meter.qualification_passed);self.assertIsNotNone(meter.active)
    self.assertTrue(read(d/'preflight-private.json')['passed']);self.assertEqual((meter.nb['actions'],meter.nb['resets']),(0,0));meter.b.update(ticks=1353,reserved_ticks=1353,worlds=41)
    cohorts=[dict(arm=arm,status='COMPLETE_H13') for arm in ['OriginalReferenceCommonPulse','Projected4ReferenceCommonPulse']]
    return dict(status='TWO_H13_COHORTS_COMPLETED_REPEAT_EXACT',passed=True,cohorts=cohorts,model_ticks=216,model_worlds=6,policyrecords_path=str(d/'policyrecords-private.json'),cohortresults_path=str(d/'cohortresults.json'),actual_execution_allowed=False)
   def whole(_root,meter,*args):
    self.assertIs(meter,seen['meter']);self.assertEqual((meter.b['ticks'],meter.b['worlds']),(1353,41));self.assertIsNotNone(meter.active);meter.b.update(ticks=1913,reserved_ticks=1913,worlds=43);seen['whole_entered']=True
    return dict(status='TWO_WHOLE_PARENTS_FINISHED',policies=[dict(arm='OriginalReferenceCommonPulse'),dict(arm='Projected4ReferenceCommonPulse')],model_worlds=2,model_ticks=560,whole_arm_repeated=False,actual_execution_allowed=False)
   whole_driver=stack.enter_context(patch.object(r,'whole_parents',side_effect=whole))
   stack.enter_context(patch.object(r,'qualify',side_effect=oldqual));stack.enter_context(patch.object(r,'qualify_pending'));stack.enter_context(patch.object(r,'qualify_parent'));driver=stack.enter_context(patch.object(r,'root_h13',side_effect=h13))
   timers=stack.enter_context(patch.object(r.signal,'setitimer'));forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE'))));forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_WORLD'))))
   r.run(root);driver.assert_called_once();whole_driver.assert_called_once();self.assertTrue(seen['whole_entered']);out=read(d/'result.json');self.assertEqual(out['status'],'WHOLE_COMPARISON_COMPLETE');self.assertIsNone(out['error']);self.assertEqual(sha(ledger_path),p['ledger_sha256'])
   self.assertEqual((seen['meter'].b['ticks'],seen['meter'].b['worlds']),(1913,43));nonzero=[x.args for x in timers.call_args_list if x.args[1]>0];self.assertTrue(nonzero)
   for kind,seconds in nonzero:self.assertLessEqual(seconds,180 if kind==r.signal.ITIMER_PROF else 300)
   for mock in forbidden:mock.assert_not_called()
  self.assertEqual(random.getstate(),py);now=np.random.get_state();self.assertEqual(now[0],npr[0]);np.testing.assert_array_equal(now[1],npr[1]);self.assertEqual(now[2:],npr[2:])
