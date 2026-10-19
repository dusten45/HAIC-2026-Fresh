import unittest
from retry.cold597_core import *
class ColdTests(unittest.TestCase):
 def test_official_integer_not_interpolated_gain(self):
  self.assertEqual(official_raw(1.02+13.1999999999998),660)
  self.assertEqual(official_raw(1.02+13.6599999999998),683)
  with self.assertRaises(ValueError):official_raw(1.02+13.1936)
 def test_timelimit_and_warmup_exact_boundary(self):
  self.assertEqual(MAX_APPLIED,1174);self.assertLess(WARMUP+1173,TIME_LIMIT);self.assertEqual(WARMUP+1174,TIME_LIMIT)
  self.assertEqual(round((1+WARMUP)*DT,2),EPOCH)
 def test_conditional_replay_escrow_and_capacity_boundary(self):
  req=reserve_request(True);self.assertEqual(req['model_attempted'],2714);self.assertEqual(req['total_force'],21712);self.assertEqual(req['geometry'],6876)
  caps={k:v+10 for k,v in req.items()};self.assertTrue(fits({k:10 for k in req},req,caps));self.assertFalse(fits({'geometry':11},req,caps))
 def test_failed_whole_never_replayed(self):
  for status in ['NO_ADMISSIBLE_ACTION','APPLIED_STRICT_FAILURE','TIME_LIMIT','TECHNICAL_STOP','COST_OR_DOMAIN_STOP']:
   self.assertFalse(replay_allowed(status,None))
  self.assertFalse(replay_allowed('WHOLE_STRICT_SAFE_OFFICIAL_FINISH','IO'))
  self.assertTrue(replay_allowed('WHOLE_STRICT_SAFE_OFFICIAL_FINISH',None))
