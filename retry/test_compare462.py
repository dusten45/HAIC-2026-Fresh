"""462 frozen root, fixed-first scope and real startup cap wiring, no physics."""
import copy,json,pickle,random,tempfile,unittest
from contextlib import ExitStack
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch,Mock
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.pilot420_backend import ResourceStop

class Compare462Tests(unittest.TestCase):
 def test_frozen_schedule_budget_and_no_later_secant(self):
  from retry import compare462 as r
  p=dict(execution=r.contract());b=r.calculate(p['execution']);self.assertEqual((b['ticks'],b['worlds']),(43650,839))
  self.assertEqual(p['execution']['hard'],dict(ticks=49152,worlds=896,CPU_s=1800,wall_s=2400,max_parallel=1,actual_actions=0))
  for arm,recipe in [('Original','nominal'),('SecantOnce','fullgas')]:
   self.assertEqual(r.schedule462(p,arm,0,'FIRST_LAP',False),recipe)
   for n in range(1,100):self.assertIsNone(r.schedule462(p,arm,n,'FIRST_LAP',False))
   self.assertIsNone(r.schedule462(p,arm,99,'FINISH_CONFIRM',True))
   with self.assertRaises(Exception):r.schedule462(p,arm,0,'FINISH_CONFIRM',True)
  bad=copy.deepcopy(p['execution']);bad['hard']['ticks']=43649
  with self.assertRaises(AssertionError):r.calculate(bad)

 def test_saved_root_full_vector_alias_and_nominal_factual_suffix(self):
  from retry import compare462 as r
  root=Path('/workspace/haic-private-retry-20261009');state,memory,ledger,rng,blob,expected=r.root_inputs(root)
  self.assertEqual(expected[0]['step'],126);self.assertEqual(len(expected),51);self.assertTrue(all(x['command']==x['nominal'] for x in expected));self.assertFalse(ledger.done)
  old=read(root/'stage453/plan.json');fixed=read(old['fixed_plan']);pace=np.asarray(read(old['pace_path'])['frozen268']);pre=expected[0]['pre'];nominal=np.asarray(expected[0]['nominal'],np.float32)
  out=r.secant_command(fixed,pace,pre['pos'],pre['vel'],nominal);alias=nominal.copy();alias[1:]=[1,0];np.testing.assert_array_equal(out,alias)
  obj=r.Comparison462.__new__(r.Comparison462);obj.fixed=fixed;obj.pace=pace;obj.short_pair=Mock(return_value=dict(valid=True,recipe='fixture'))
  parent=SimpleNamespace(m=SimpleNamespace(car=SimpleNamespace(hull=SimpleNamespace(position=pre['pos'],linearVelocity=pre['vel']))));ctx=SimpleNamespace(nominal=nominal)
  obj.fixed_first(parent,ctx,{},'x','Original','nominal');obj.fixed_first(parent,ctx,{},'y','SecantOnce','fullgas');self.assertEqual([call.args[-1] for call in obj.short_pair.call_args_list],['nominal','fullgas'])
  obj.short_pair.return_value=dict(valid=False)
  with self.assertRaises(Exception):obj.fixed_first(parent,ctx,{},'z','SecantOnce','fullgas')

 def test_dispatch_uses_only_first_fixed_and_later_guardian(self):
  from retry import compare462 as r
  obj=r.Comparison462.__new__(r.Comparison462);obj.fixed_first=Mock(return_value='fixed');obj.guardian=Mock(return_value='guardian')
  self.assertEqual(obj.dispatch_query(None,None,None,'a','Original','nominal'),'fixed')
  self.assertEqual(obj.dispatch_query(None,None,None,'b','SecantOnce','fullgas'),'fixed')
  for phase,pending in [('FIRST_LAP',False),('FINISH_CONFIRM',True)]:
   recipe=r.schedule462(dict(execution=r.contract()),'SecantOnce',2,phase,pending)
   self.assertEqual(obj.dispatch_query(None,None,None,'c','SecantOnce',recipe),'guardian')
  self.assertEqual(obj.fixed_first.call_count,2);self.assertEqual(obj.guardian.call_count,2)

 def test_real_startup_binds_one_contract_meter_timers_and_both_arms(self):
  from retry import compare462 as r,budget456,diagnose
  from retry.source_vehicle_transition import SourceVehicleTransition
  from retry.terminal410_model import TerminalVehicleTransition
  from retry.planner419 import GoalLedger
  import Box2D
  py=random.getstate();npr=np.random.get_state();seen=dict(arms=[],rootcalls=0)
  with tempfile.TemporaryDirectory() as td,ExitStack() as stack:
   root=Path(td);d=root/'stage462';d.mkdir();fixed=root/'fixed.json';pace=root/'pace.json';save(fixed,{});save(pace,{'frozen268':[]});c=r.contract()
   p=dict(execution=c,caps=c['hard'],budget_fixture=r.calculate(c),deadline_utc=c['deadline_utc'],fixed_plan=str(fixed),pace_path=str(pace),contract_sha256='fixture',semantic_sources={},sources={},protected={},original408_preserve={},order=['Original','SecantOnce'],storage_free_stop_bytes=536870912)
   save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(d/'static-result.json',dict(passed=True,plan_sha256=sha(d/'plan.json')))
   folder=root/'stage423/actual_C0';folder.mkdir(parents=True);save(folder/'fork-private.json',dict(controller=dict(before={})));row=dict(progress_before=0.,goal_before=3.24,deadline_before=131);(folder/'trace-private.jsonl').write_text('\n'.join(json.dumps(row) for _ in range(119)))
   state=dict(physical=dict(actual_time=0.));ledger=GoalLedger.start(0.,0);blob=pickle.dumps((py,npr))
   stack.enter_context(patch.object(r,'root_inputs',return_value=(state,{},ledger,{},blob,[])));stack.enter_context(patch.object(r,'from_actual_full',return_value=state))
   stack.enter_context(patch.object(r.shutil,'disk_usage',return_value=SimpleNamespace(free=8*1024**3)))
   def oldqual(_root,meter,*args):seen['meter']=meter;meter.b.update(ticks=1137,reserved_ticks=1137,worlds=35)
   def rootqual(_root,meter,*args):
    self.assertIs(meter,seen['meter']);seen['rootcalls']+=1;meter.b.update(ticks=1353,reserved_ticks=1353,worlds=41)
   stack.enter_context(patch.object(r,'qualify',side_effect=oldqual));stack.enter_context(patch.object(r,'qualify_pending'));stack.enter_context(patch.object(r,'qualify_parent'));stack.enter_context(patch.object(r,'qualify_root460',side_effect=rootqual))
   def policy(pilot,name):
    self.assertIs(pilot.meter,seen['meter']);self.assertIs(type(pilot.meter),r.Meter462);self.assertEqual(pilot.meter.p['caps'],c['hard']);seen['arms'].append(name)
    self.assertEqual(read(d/(name+'-root-binding-private.json'))['observed_prefix_elapsed_s'],10.)
    pilot.results.append(dict(arm=name,finish_ticks=dict(lo=1,hi=2),official_model_finish=True))
   stack.enter_context(patch.object(r.Comparison462,'policy462',new=policy));timers=stack.enter_context(patch.object(r.signal,'setitimer'));forbidden=[]
   for cls in (SourceVehicleTransition,TerminalVehicleTransition):
    for method in ('__init__','step'):forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('FORBIDDEN_PHYSICS'))))
   forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('FORBIDDEN_NATIVE'))));forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('FORBIDDEN_WORLD'))))
   r.run(root);result=read(d/'result.json');self.assertEqual(result['status'],'TWO_MODEL_PARENTS_COMPLETED_NO_ARM_REPEAT');self.assertEqual(seen['arms'],['Original','SecantOnce']);self.assertEqual(seen['rootcalls'],1);self.assertFalse(result['whole_arm_repeated']);self.assertEqual(result['model_tail_Original_minus_SecantOnce_bracket_s'],[-.02,.02])
   meter=seen['meter'];self.assertEqual((meter.b['ticks'],meter.b['worlds']),(1353,41));meter.b['reserved_ticks']=49152
   with self.assertRaises(ResourceStop):meter.step(object(),[0.,0.,0.],'fixture')
   with patch.object(budget456.time,'process_time',return_value=1800):
    with self.assertRaises(ResourceStop):meter.guard()
   nonzero=[x.args for x in timers.call_args_list if x.args[1]>0];self.assertEqual(len(nonzero),2);self.assertLessEqual(nonzero[0][1],1800);self.assertLessEqual(nonzero[1][1],2400)
   for mock in forbidden:mock.assert_not_called()
  self.assertEqual(random.getstate(),py);now=np.random.get_state();np.testing.assert_array_equal(now[1],npr[1]);self.assertEqual(now[2:],npr[2:])
