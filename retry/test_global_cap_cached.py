"""Hand-calculated constraint and pedal examples; no simulator or policy."""
import math
import unittest
import numpy as np
from retry.global_cap_cached import cap_shadow


class CapShadowTests(unittest.TestCase):
    def test_both_sites_and_other_limits(self):
        full=cap_shadow(50,math.inf,25)
        self.assertEqual((full['old'],full['new'],full['one_site_only_target']),(28,40,28))
        self.assertEqual(full['group'],'reaches40')
        np.testing.assert_array_equal(full['old_pedals'],np.array([.24,0],np.float32))
        np.testing.assert_array_equal(full['new_pedals'],np.array([.5,0],np.float32))
        self.assertEqual(cap_shadow(35,math.inf,30)['group'],'partial_curvature')
        self.assertEqual(cap_shadow(20,math.inf,30)['group'],'unchanged_curvature')
        self.assertEqual(cap_shadow(50,12,30)['group'],'unchanged_distance')

    def test_target_gain_can_be_hidden_by_pedal_saturation(self):
        shadow=cap_shadow(50,math.inf,0)
        self.assertEqual(shadow['delta'],12)
        self.assertFalse(shadow['changed'])
        self.assertTrue(cap_shadow(50,math.inf,32)['changed'])


if __name__=='__main__':unittest.main()
