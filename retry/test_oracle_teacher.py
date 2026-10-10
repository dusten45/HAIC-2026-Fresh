"""Synthetic geometry checks, with no simulator or private experimental data."""
import unittest

import numpy as np

from retry.oracle_teacher import OracleTeacher, segment_clearance


def circle_road(radius=60., n=180):
    a = np.linspace(0., 2. * np.pi, n, endpoint=False)
    return np.column_stack((a, a, radius * np.cos(a), radius * np.sin(a)))


class TeacherGeometryTests(unittest.TestCase):
    def test_circle_tracking_sign_and_current_speed(self):
        teacher = OracleTeacher()
        teacher.reset(circle_road(), np.empty((0,3)), 40./6.)
        action = teacher.act([62.,0.], 0., [0.,10.])
        self.assertLess(action[0], 0.)  # Road lies to the vehicle's left.
        self.assertEqual(teacher.last_diagnostic['speed_m_s'], 10.)
        self.assertTrue(np.isfinite(action).all())

    def test_center_obstacle_has_a_clear_detour(self):
        teacher = OracleTeacher()
        obstacles = np.array([[0.,60.,1.2]])
        teacher.reset(circle_road(), obstacles, 40./6.)
        clearance = segment_clearance(teacher.path, obstacles)[0]
        self.assertGreaterEqual(clearance, 4.3 - 1e-10)
        self.assertLessEqual(teacher.plan_diagnostic['max_abs_lateral_offset_m'], 40./6. - 1.65)

    def test_periodic_braking_envelope(self):
        teacher = OracleTeacher()
        teacher.reset(circle_road(), np.array([[0.,60.,1.2]]), 40./6.)
        profile = teacher.speed_profile
        self.assertTrue(np.all(profile**2 <= np.roll(profile,-1)**2 + 2.*2.5*teacher.ds + 1e-9))

    def test_nonfinite_state_is_rejected(self):
        teacher = OracleTeacher()
        teacher.reset(circle_road(), np.empty((0,3)), 40./6.)
        with self.assertRaises(ValueError):
            teacher.act([float('nan'),0.], 0., [0.,0.])


if __name__ == '__main__':
    unittest.main()
