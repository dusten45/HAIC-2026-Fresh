"""Pure transition semantics, no world or integrator."""
import unittest
import numpy as np
from retry.cold598_transition import horizon,payload
class TransitionTests(unittest.TestCase):
 def test_pretransition_last_fixed_horizon(self):self.assertEqual(horizon(28),[(h,'FIXED577') for h in range(28,40)])
 def test_transition_horizons_have_one_anchor_and_no_late_tape(self):
  for start in range(29,40):
   p=horizon(start);self.assertEqual(len(p),12);self.assertEqual(sum(m=='ANCHOR537' for h,m in p),1);self.assertTrue(all(h<40 if m=='FIXED577' else h==40 if m=='ANCHOR537' else h>40 for h,m in p))
  self.assertEqual(horizon(39)[:3],[(39,'FIXED577'),(40,'ANCHOR537'),(41,'BACKUP537')])
 def test_forecast_dispatch_uses_forecast_state_history_and_copies_payload(self):
  class PrefixOnly(dict):
   def __getitem__(self,h):
    if h>=40:raise AssertionError('FORBIDDEN_FUTURE_FIXED_TAPE')
    return super().__getitem__(h)
  commands=PrefixOnly({39:np.array([.1,.2,0],np.float32)});seen=[];root=object();history=[16,240]
  def choose(r,hi,lo,s,h):seen.append((r,hi,lo,s,h));return np.array([.3,.4,0],np.float32),{'final_recertified':True}
  def backup(r,hi,lo,s):return np.array([.3,0,.2],np.float32)
  a,_=payload(39,'FIXED577',commands,root,history,choose,backup,'H','L',151.);a[0]=0;self.assertEqual(float(commands[39][0]),float(np.float32(.1)))
  payload(40,'ANCHOR537',commands,root,history,choose,backup,'H','L',151.);payload(41,'BACKUP537',commands,root,history,choose,backup,'H','L',152.);self.assertEqual(seen,[(root,'H','L',151.,(16,240))]);self.assertEqual(history,[16,240])
 def test_prefix_domain_and_model_bound(self):
  for s in [0,40,294]:
   with self.assertRaises(ValueError):horizon(s)
  self.assertEqual(32*48+12*4+4,1588);self.assertEqual(4*1588+4*4,6368)
 def test_actual40_and_later_dispatch_replans_with_actual_history(self):
  from types import SimpleNamespace
  from unittest.mock import patch
  from retry.cold598_support import Support,tracking
  s=Support.__new__(Support);s.model=[0];s.planner={};s.geometry_context={};s.candidate_backup='candidate551backup';s.add=lambda *a:None;s.commands={};root=object();seen=[]
  raw=SimpleNamespace(road=[SimpleNamespace(idx=7,road_visited=True)],tile_visited_count=1)
  st=dict(force_groups={'launch':{'clipped':55,'samples':384},'running':{'clipped':15,'samples':240}},lap_progress=151.)
  action=np.array([.1,.2,0],np.float32);detail=dict(final_recertified=True,reports=[dict(mode='FINAL',ok=True)])
  def choose(r,hi,lo,progress,*args,**kw):seen.append((r,lo,kw['history']));return action,detail
  with patch.object(tracking,'choose',choose):
   for h in [40,52,166,167,294]:self.assertIs(s.candidate_select(root,'candidate551',st,h-1,raw,0)[0],action)
  self.assertEqual(seen,[(root,'candidate551backup',(15,240))]*5)
