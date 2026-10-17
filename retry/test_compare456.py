"""456 model-only contract and adapter tests; no constructors or integration."""
import ast,copy,inspect,textwrap,unittest,tempfile
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch
from retry.loss389_analyze import read
from retry.pilot420_backend import ResourceStop,TechnicalStop
G=Path(__file__).resolve().parents[1]

class Compare456Tests(unittest.TestCase):
 def test_preregistered_cost_arithmetic_includes_all_four_parents_and_qualification(self):
  planner_queries=2*8;guardian_queries=4*100-planner_queries
  ticks=planner_queries*3*2*(13+308)*4+guardian_queries*2*2*13*4+4*100*4+1242+216
  worlds=planner_queries*3*2+guardian_queries*2*2+4+35+6
  self.assertEqual((ticks,worlds),(206194,1677));self.assertLessEqual(ticks,212992);self.assertLessEqual(worlds,1792)
  self.assertEqual((1242+216,35+6),(1458,41))
 def test_scope_C0_always_guardian_and_cap100(self):
  from retry.compare456 import scope456
  for used in (0,7,8,9):
   for phase,pending in [('FIRST_LAP',False),('FIRST_LAP',True),('FINISH_CONFIRM',True)]:self.assertEqual(scope456('C0',used,phase,pending),(100,False))
 def test_scope_P_exactly_eight_eligible_decisions(self):
  from retry.compare456 import scope456
  for used in range(8):self.assertEqual(scope456('P',used,'FIRST_LAP',False),(100,True))
  for used in (8,9,100):self.assertEqual(scope456('P',used,'FIRST_LAP',False),(100,False))
 def test_scope_pending_and_finish_never_consume_planner_quota(self):
  from retry.compare456 import scope456
  self.assertEqual(scope456('P',0,'FIRST_LAP',True),(100,False))
  self.assertEqual(scope456('P',0,'FINISH_CONFIRM',False),(100,False))
  self.assertEqual(scope456('P',0,'FINISH_CONFIRM',True),(100,False))
  with self.assertRaises(Exception):scope456('hardcoded_spatial_pulses',0,'FIRST_LAP',False)
 def test_planning_query_is_old436_except_two_budget_limits(self):
  from retry.budget456 import Planning456
  from retry.pilot436_run import Pilot
  old=ast.parse(textwrap.dedent(inspect.getsource(Pilot.planning_query)))
  new=ast.parse(textwrap.dedent(inspect.getsource(Planning456.planning_query)))
  class BoundAdapter(ast.NodeTransformer):
   def visit_Constant(self,node):
    if type(node.value) is int and node.value in (524288,1024):
     key='ticks' if node.value==524288 else 'worlds'
     return ast.parse("self.meter.p['caps']['"+key+"']",mode='eval').body
    return node
  expected=BoundAdapter().visit(copy.deepcopy(old))
  self.assertEqual(ast.dump(expected,include_attributes=False),ast.dump(new,include_attributes=False))
 def test_planner_inherits_recipe_tail_pending_and_authority_unchanged(self):
  from retry.budget456 import Planning456
  from retry.pilot436_run import Pilot
  self.assertTrue(issubclass(Planning456,Pilot))
  for method in ('new','short_pair','runtime_evidence','validate_child','validate_saved_child'):
   self.assertIs(getattr(Planning456,method),getattr(Pilot,method))
 def test_tick_cap_stops_before_unregistered_step_or_integration(self):
  from retry.budget456 import Meter
  m=Meter.__new__(Meter);m.p=dict(caps=dict(ticks=212992,worlds=1792,CPU_s=6000,wall_s=9000));m.b=dict(reserved_ticks=212992)
  with self.assertRaises(ResourceStop):m.step(object(),[0.,0.,0.],'static_cap')
 def test_world_cap_stops_before_constructor(self):
  from retry.budget456 import Meter
  m=Meter.__new__(Meter);m.p=dict(caps=dict(ticks=212992,worlds=1792,CPU_s=6000,wall_s=9000));m.inputs=dict(static='proof');m.guard=lambda:None;m.b=dict(worlds=1792)
  with patch('retry.budget456.TerminalVehicleTransition') as constructor:
   with self.assertRaises(ResourceStop):m.world({},'static_cap')
   constructor.assert_not_called()
 def test_missing_input_proof_stops_before_constructor(self):
  from retry.budget456 import Meter
  m=Meter.__new__(Meter);m.inputs=None
  with patch('retry.budget456.TerminalVehicleTransition') as constructor:
   with self.assertRaises(TechnicalStop):m.world({},'static_no_inputs')
   constructor.assert_not_called()
 def test_world1024_is_not_hidden_stop_and_restore_proof_is_required(self):
  from retry.budget456 import Meter
  with tempfile.TemporaryDirectory() as td:
   m=Meter.__new__(Meter);m.p=dict(caps=dict(worlds=1792));m.inputs=dict(static='recorded');m.guard=lambda:None;m.persist=lambda:None;m.timing=lambda *args:None;m.d=Path(td);m.sequence=0;m.live=[];m.auth={};m.b=dict(worlds=1024,worlds_by_tag={},confirmed_worlds=1024,max_live_worlds=0)
   fake=SimpleNamespace(initial_bodies_exact=True,initial_tiles_exact=True,initial_progress_exact=True,initial_finish_exact=True)
   with patch('retry.budget456.TerminalVehicleTransition',return_value=fake) as constructor:
    self.assertIs(m.world({},'static_restore'),fake);constructor.assert_called_once_with({})
   self.assertEqual(m.b['worlds'],1025);self.assertEqual(len(m.auth),1)
   self.assertTrue(all(m.auth[id(fake)]['restore_gates'].values()))
 def test_model_meter_has_no_actual_dispatch_entrypoint(self):
  from retry.budget456 import Meter
  self.assertFalse(hasattr(Meter,'charge'))
