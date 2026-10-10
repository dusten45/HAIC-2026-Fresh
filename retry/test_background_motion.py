"""Source-defined camera/body/COM conventions and unavailable texture."""
import unittest
import numpy as np
from retry.background_motion import (PIXELS_PER_UNIT, LOCAL_COM, register,
                                     motion_from_registration, calibrate_anchor)


class BackgroundMotionTests(unittest.TestCase):
    def test_static_world_camera_motion_has_correct_body_sign_units_and_COM(self):
        # Independent static world points projected from two translated cameras.
        angle0, angle1 = .3, .37
        rot = lambda a: np.array([[np.cos(a), -np.sin(a)], [np.sin(a), np.cos(a)]])
        o0 = np.array([3., -2.]);o1 = np.array([3.04, -.8])
        world = np.array([[-3., 10.], [5., 8.], [10., -1.], [-5., -6.]])
        anchor = np.array([52., 62.5]);f = np.diag([1., -1.])
        p0 = anchor+(world-o0)@rot(-angle0).T@f*PIXELS_PER_UNIT
        p1 = anchor+(world-o1)@rot(-angle1).T@f*PIXELS_PER_UNIT
        mapped = np.linalg.lstsq(np.c_[p0, np.ones(len(p0))], p1, rcond=None)[0]
        record = {'status': 'registered', 'rotation': mapped[:2].T,
                  'translation': mapped[2], 'delta_yaw_rad': .07}
        displacement, mean = motion_from_registration(record, anchor=anchor, interval_s=.08)
        com0=o0+rot(angle0)@LOCAL_COM;com1=o1+rot(angle1)@LOCAL_COM
        expected=np.r_[rot(-angle1)@(com1-com0), .07]
        np.testing.assert_allclose(displacement, expected, atol=1e-12)
        np.testing.assert_allclose(mean, expected/.08, atol=1e-11)
        calibrated, info = calibrate_anchor([record], [rot(-angle1)@(o1-o0)], [1.])
        np.testing.assert_allclose(calibrated, anchor, atol=1e-10)
        self.assertEqual(info['rank'], 2)

    def test_uniform_background_abstains_instead_of_claiming_zero_motion(self):
        frame = np.full((84, 84), 100, np.uint8)
        result = register(frame, frame)
        self.assertEqual(result['status'], 'abstain')
        self.assertEqual(result['reason'], 'insufficient_background_corners')


if __name__ == '__main__':
    unittest.main()
