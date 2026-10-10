"""Compare the decomposed adapter to the actual champion controller, no fit."""
import unittest
import numpy as np
from retry.parameter_agent import SpeedController
from retry.structured_follower import actions_from_targets
from retry.imitation_model import SmallActionMLP, clip_actions


class StructuredFollowerTest(unittest.TestCase):
    def test_original_equations_match_for_unsaturated_and_saturated_controls(self):
        targets, speeds, previous, expected = [], [], [], []
        for x, forward, speed, past, lateral in [(0,6,0,0,7),(2,10,15,.1,5),(-3,8,30,-.2,7),(0,14,27,0,5)]:
            controller = SpeedController(28,lateral); controller.previous_steer=past
            curvature=2*x/max(forward*forward+x*x,1e-6)
            desired=min(28,float(np.sqrt(lateral/(abs(curvature)+.003))))
            expected.append(controller.action_target(x,forward,speed))
            targets.append([x,forward,desired]);speeds.append(speed);previous.append(past)
        np.testing.assert_array_equal(actions_from_targets(targets,np.array(speeds),np.array(previous)),expected)

    def test_external_desired_speed_changes_only_longitudinal_control(self):
        out=actions_from_targets([[1,10,10],[1,10,25]],np.array([20.,20.]),np.array([.1,.1]))
        self.assertEqual(out[0,0],out[1,0]);self.assertEqual(out[0,1],0)
        self.assertGreater(out[0,2],0);self.assertGreater(out[1,1],0);self.assertEqual(out[1,2],0)

    def test_action_prediction_still_clips_raw_regression(self):
        model=SmallActionMLP();model.mean=np.zeros(2,np.float32);model.scale=np.ones(2,np.float32)
        model.label_mean=np.array([2.,-1.,3.],np.float32);model.label_scale=np.ones(3,np.float32)
        model.arrays=[(np.zeros((3,2),np.float32),np.zeros(3,np.float32))]
        inputs=np.ones((2,2),np.float32)
        np.testing.assert_array_equal(model.predict(inputs),clip_actions(model.predict_unclipped(inputs)))


if __name__=='__main__':
    unittest.main()
