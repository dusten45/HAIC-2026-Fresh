"""Synthetic channel/invariant tests; no generated physics or real performance claims."""
import unittest
from retry.planner419 import GoalLedger,ActualObservation,ContractError
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
class PredictedLedgerTests(unittest.TestCase):
 def test_forecast_hit_renews_only_child_goal(self):
  actual=GoalLedger.start(0.,100);stamp=actual.digest();child=ForecastLedger.fork(actual);child=child.advance_prediction(ModelPrediction(3.24,104));self.assertEqual(child.goal_m,6.48);self.assertEqual(child.actual_root_digest,stamp);self.assertEqual(actual.goal_m,3.24);self.assertEqual(actual.last_clock_tick,100);self.assertTrue(child.progress_qualified())
 def test_forecast_after_initial_hit_still_keeps_new_deadline(self):
  actual=GoalLedger.start(0.,100);child=ForecastLedger.fork(actual).advance_prediction(ModelPrediction(3.24,104))
  for j in range(1,14):child=child.advance_prediction(ModelPrediction(3.24+j*.01,104+4*j))
  self.assertTrue(child.deadline_missed);self.assertFalse(child.progress_qualified());self.assertFalse(actual.deadline_missed)
 def test_actual_and_model_channels_cannot_be_substituted(self):
  actual=GoalLedger.start(0.,100);child=ForecastLedger.fork(actual)
  with self.assertRaises(ContractError):actual.advance_actual(ModelPrediction(9.,104))
  with self.assertRaises(ContractError):child.advance_prediction(ActualObservation(9.,104))
 def test_model_root_goal_not_reset_before_hit(self):
  actual=GoalLedger.start(0.,100);child=ForecastLedger.fork(actual)
  for j in range(1,13):child=child.advance_prediction(ModelPrediction(j*.1,100+4*j));self.assertEqual(child.goal_m,3.24)
  child=child.advance_prediction(ModelPrediction(1.3,152));self.assertTrue(child.deadline_missed);self.assertFalse(child.progress_qualified())
if __name__=='__main__':unittest.main()
