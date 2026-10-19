"""No solver calls or source evaluation: reproduce and bound the one correction."""
import unittest
from types import SimpleNamespace
import numpy as np
from retry.causal574_rounding import solve as oldsolve,check as oldcheck
from retry.causal575_rounding import solve,effective_uncertainty,numerical_margin,check

class Algebra575(unittest.TestCase):
    def problem(self):
        return dict(x0=np.asarray([.1,.2,.3,.4],np.float32).astype(float),scale=np.asarray([.003,.03,.003,.03]),bounds=np.asarray([[0,0],[0,0],[-.05,.05],[-.05,.05],[0,.05],[0,.05]],float),groups=[2,4],A=np.asarray([[1,0,0,0,-1,0],[-1,0,0,0,-1,0],[0,0,0,0,1,-1],[0,0,0,0,0,0]],float),b=np.asarray([0.,0.,0.,1.]),objective=np.asarray([0.,0.,-1.,0.]),ratio_rows=[],path=None)
    def capture(self,fn,p):
        captured={}
        def fake(*a,**k):captured.update(k);return SimpleNamespace(success=False,status=2)
        fn(p,solve_fn=fake);return captured
    def test_old_fixed_aux_negative_rhs_reproduced_without_solver_tolerance(self):
        p=self.problem();old=self.capture(oldsolve,p);new=self.capture(solve,p)
        self.assertLess(old['b_ub'][0],0.);self.assertEqual(new['b_ub'][0],0.);self.assertEqual(new['b_ub'][1],0.)
        self.assertEqual(old['bounds'][4],[0.,0.]);self.assertEqual(new['bounds'][4],[0.,0.])
    def test_only_provable_fixed_prefix_uncertainty_vanishes(self):
        p=self.problem();original=p['bounds'].copy();q,inward,mag=effective_uncertainty(p)
        self.assertTrue(np.all(q[:2]==0));self.assertTrue(np.all(q[2:]>0));self.assertEqual(mag[4],0.);self.assertEqual(mag[5],.05);self.assertTrue(np.array_equal(p['bounds'],original));self.assertTrue(np.array_equal(inward[4],[0.,0.]))
    def test_causal_zero_coefficients_have_no_future_rounding(self):
        p=self.problem();q,_,_=effective_uncertainty(p);self.assertEqual(float(abs(p['A'][0,:4])@q),0.);self.assertGreater(float(np.asarray([0,0,1,0])@q),0.)
    def test_free_bounds_are_not_replaced_by_smaller_inward_magnitudes(self):
        p=self.problem();p['bounds'][2]=[-.05,0.];_,inward,mag=effective_uncertainty(p);self.assertEqual(mag[2],.05);self.assertLess(max(abs(inward[2])),mag[2])
    def test_constant_rows_exact_and_positive_scaling_covariant(self):
        p=self.problem();_,_,mag=effective_uncertainty(p);n=numerical_margin(p['A'],p['b'],mag,1e-12);self.assertEqual(n[0],0.);self.assertEqual(n[3],0.);self.assertGreater(n[2],0.);self.assertTrue(np.array_equal(8*n,numerical_margin(8*p['A'],8*p['b'],mag,1e-12)))
    def test_original_seed_and_exact_ratio_checks_unchanged(self):
        p=self.problem();self.assertEqual(check(p,p['x0']),oldcheck(p,p['x0']));p['ratio_rows']=[3];p['b'][3]=-1e-9;self.assertFalse(check(p,p['x0'])['pass_all']);self.assertLess(check(p,p['x0'])['linear_violation'],1e-8)

if __name__=='__main__':unittest.main()
