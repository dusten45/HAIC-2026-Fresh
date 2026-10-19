import unittest
from types import SimpleNamespace
import numpy as np
from retry.rounding573 import rounding_box,solve,check,TOL

class Rounding573(unittest.TestCase):
    def problem(self):
        return dict(x0=np.asarray([.1,.2],np.float32).astype(float),scale=np.asarray([.003,.03]),A=np.asarray([[1.,0.,.01],[-1.,1.,.02],[0.,-1.,.01],[1.,0.,-1.],[0.,1.,-1.],[-1.,0.,-1.],[0.,-1.,-1.]]),b=np.asarray([.03,.03,.03,0,0,0,0]),bounds=np.asarray([[-.05,.05],[-.05,.05],[0,.05]]),objective=np.asarray([-1.,-.2]),path=None)
    def test_joint_rows_and_trust_after_quantization(self):
        p=self.problem();x,r=solve(p);self.assertTrue(r['accepted']);self.assertTrue(check(p,x)['pass_all']);self.assertTrue(np.array_equal(x,x.astype(np.float32).astype(float)));self.assertLessEqual(r['LP_solves'],8)
    def test_binade_tie_subnormal_and_negative_enclosure(self):
        # Adjacent-float midpoint ties, and points on both sides of each tie.
        for v in [np.float32(0),np.nextafter(np.float32(0),np.float32(1)),np.float32(.5),np.float32(1),np.float32(-1)]:
            u=np.nextafter(v,np.float32(np.inf));middle=(float(v)+float(u))/2
            radius=max(abs(float(u)-float(v))*2,1e-44);bounds=np.asarray([[-radius,radius],[0,radius]])
            q=rounding_box(np.asarray([float(v)]),np.ones(1),bounds)[0]
            for x in [float(v),float(u),middle,np.nextafter(middle,-np.inf),np.nextafter(middle,np.inf)]:self.assertLessEqual(abs(float(np.float32(x))-x),q)
    def test_exact_seed_survives_empty_robust_branch(self):
        p=self.problem();p['A']=np.asarray([[1.,0.,0.],[-1.,0.,0.]]);p['b']=np.zeros(2)
        x,r=solve(p);self.assertIsNone(x);self.assertTrue(r['seed_fallback_preserved']);self.assertTrue(check(p,p['x0'])['pass_all']);self.assertEqual(r['stop'],'CERTIFIED_BRANCH_LP_FAILED')
    def test_injected_rounder_cannot_open_source_gate(self):
        p=self.problem();x,r=solve(p,round_fn=lambda v:(v+.01).astype(np.float32).astype(float));self.assertIsNone(x);self.assertFalse(r['accepted']);self.assertEqual(r['stop'],'ROUNDING_OUTSIDE_CERTIFICATE')
    def test_injected_solver_cannot_open_source_gate(self):
        p=self.problem();fake=lambda *a,**k:SimpleNamespace(success=True,x=np.asarray([1.,1.,.05]),status=0)
        x,r=solve(p,solve_fn=fake);self.assertIsNone(x);self.assertFalse(r['accepted']);self.assertEqual(r['stop'],'QUANTIZED_JOINT_CHECK_FAILED')
    def test_nonfinite_and_nonexact_seed_rejected(self):
        for change in ['nan','seed']:
            p=self.problem()
            if change=='nan':p['A'][0,0]=np.nan
            else:p['x0'][0]+=.00000000001
            with self.assertRaises(ValueError):solve(p)
    def test_acceptance_tolerance_unchanged(self):
        self.assertEqual(TOL,1e-8);p=self.problem();p['A']=np.zeros((1,3));p['b']=np.asarray([-np.nextafter(TOL,np.inf)]);self.assertFalse(check(p,p['x0'])['pass_all']);p['b'][0]=-TOL;self.assertTrue(check(p,p['x0'])['pass_all'])

if __name__=='__main__':unittest.main()
