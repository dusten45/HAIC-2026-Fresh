"""Requested numerical boundary checks; no environment or source propagation."""
import unittest
import numpy as np
from retry.risk548_boundary import near_risk,reserve_for


class RiskBoundary(unittest.TestCase):
    def test_exact_equal(self):
        self.assertTrue(near_risk(.1,.1))
    def test_adjacent_inside(self):
        self.assertTrue(near_risk(np.nextafter(.1,-np.inf),.1))
    def test_adjacent_outside_is_conservatively_risky(self):
        self.assertTrue(near_risk(np.nextafter(.1,np.inf),.1))
    def test_outside_roundoff_guard_is_not_risky(self):
        self.assertFalse(near_risk(.1+64*np.finfo(float).eps,.1))
    def test_reported_six_ulp_case_and_reserve(self):
        value=.10000000000000009
        self.assertFalse(value<=.1)
        self.assertTrue(near_risk(value,.1))
        self.assertEqual(float(reserve_for(value,.1)),.25*value)
    def test_expands_risk_only_vectorized(self):
        bands=np.array([.1,.02,.05,.15,.01])
        values=np.array([np.nextafter(bands,-np.inf),bands,np.nextafter(bands,np.inf),bands+64*np.finfo(float).eps])
        result=near_risk(values,bands)
        self.assertTrue(np.all(result[values<=bands]))
        self.assertTrue(np.all(result[:3]))
        self.assertFalse(np.any(result[3]))
    def test_does_not_relax_hard_physical_floor(self):
        floor=.5251524480367317
        below=np.nextafter(floor,-np.inf)
        self.assertTrue(near_risk(below-floor,.02))
        self.assertFalse(below>=floor)
        self.assertEqual(floor,.5251524480367317)
    def test_repaired_caller_uses_conservative_boundary(self):
        from retry.recover548_problem import risk_check
        g=np.full(1160,10.);g[1024]=.10000000000000009
        self.assertEqual(risk_check(g,g,g)['risky_constraints'],1)

    def test_nonfinite_classifies_conservatively(self):
        self.assertTrue(near_risk(np.nan,.1))
        self.assertTrue(near_risk(np.inf,.1))


if __name__=='__main__':unittest.main()
