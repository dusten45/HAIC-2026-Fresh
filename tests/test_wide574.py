import unittest
from types import SimpleNamespace
import numpy as np
from retry.checkpoints574 import fd_ticks,clone
from retry.causal574_rounding import solve,check,actual_aux
from retry.clip561_core import nonexempt_branch,count_pass
from retry.wide574_math import prefix_radii,empirical
from core.finish_line import FinishLineTracker

class Wide574(unittest.TestCase):
    def problem(self,fixed=False):
        N=4;G=2;A=[];b=[]
        for j in range(N):
            for sign in [1.,-1.]:
                row=np.zeros(N+G);row[j]=sign;row[N+j//2]=-1;A.append(row);b.append(0.)
        A.append([0,0,0,0,1,-1]);b.append(0.)
        # Separate force/road rows plus bounds, sharing causal auxiliaries.
        A.extend([[1,0,0,0,.02,0],[-1,1,0,0,.01,0],[0,0,1,0,0,.02],[0,0,-1,1,0,.01]])
        b.extend([.04,.04,.04,.04]);bounds=np.asarray([[-.05,.05]]*4+[[0,.05]]*2,float)
        if fixed:bounds[:2]=0.;bounds[4]=0.
        return dict(x0=np.asarray([.1,.2,.3,.4],np.float32).astype(float),scale=np.asarray([.003,.03,.003,.03]),A=np.asarray(A,float),b=np.asarray(b),bounds=bounds,objective=np.asarray([-.3,-.2,-1.,-.2]),groups=[2,4],ratio_rows=[],path=None)
    def test_suffix_cost_and_common_history_arithmetic(self):
        self.assertEqual(fd_ticks(),69696);self.assertEqual(2*fd_ticks()+4*526+6*2*526+662+1+264,148735);self.assertLess(264*526+2*526+3*2*526+662+1+132,160000)
    def test_fixed_early_controls_and_prefix_aux_remain_exact_zero(self):
        p=self.problem(True);x,r=solve(p);self.assertTrue(r['accepted']);self.assertTrue(np.array_equal(x[:2],p['x0'][:2]));self.assertEqual(actual_aux((x-p['x0'])/p['scale'],[2,4])[0],0.);self.assertTrue(check(p,x)['pass_all'])
    def test_joint_extended_rows_and_bounds(self):
        p=self.problem();x,r=solve(p);self.assertTrue(r['accepted']);self.assertTrue(check(p,x)['pass_all'])
    def test_exact_clip_condition_is_stricter_than_algebra_tolerance(self):
        p=self.problem();p['A']=np.zeros((1,6));p['b']=np.asarray([-1e-9]);p['ratio_rows']=[0];v=check(p,p['x0']);self.assertLess(v['linear_violation'],1e-8);self.assertFalse(v['pass_all'])
    def test_rank_branch_sufficient_despite_rank_changes(self):
        ratios=np.full(160,.9);ratios[[1,7,19,25,41]]=1.01;ids=nonexempt_branch(ratios,3,160);changed=ratios.copy();exempt=np.setdiff1d(np.arange(len(ratios)),ids);changed[exempt]=np.linspace(1.03,1.04,len(exempt));changed[ids]=1.
        for n in range(4,len(changed)+1,4):self.assertTrue(count_pass(changed[:n],3,160))
    def test_injected_bad_rounder_and_solver_are_rejected(self):
        p=self.problem();x,r=solve(p,round_fn=lambda a:(a+.01).astype(np.float32).astype(float));self.assertIsNone(x);self.assertFalse(r['accepted'])
        fake=lambda *a,**k:SimpleNamespace(success=True,x=np.ones(6),status=0);x,r=solve(p,solve_fn=fake);self.assertIsNone(x);self.assertFalse(r['accepted'])
    def test_zero_prefix_error_is_integrity_failure(self):
        x=np.zeros(264);center=dict(x=x,rows=[None]*526,g=np.zeros(5260),ratios=np.zeros(2104),order=np.zeros(526),P=np.zeros((526,2)));linear=dict(J=np.zeros((5260,264)),R=np.zeros((2104,264)),O=np.zeros((526,264)),P=np.zeros((526,2,264)));obs={k:(v.copy() if isinstance(v,np.ndarray) else v) for k,v in center.items()};obs['x'][-1]=.0015;obs['g'][0]=1e-12
        self.assertEqual(prefix_radii(obs['x'])[-1],.05);self.assertEqual(prefix_radii(obs['x'])[0],0.)
        with self.assertRaises(RuntimeError):empirical(center,linear,[obs])
    def test_full_matrix_seed_dimensions_and_clip_branch(self):
        from retry.wide574_math import matrix
        H=526;N=264;labels=(['footprint','path','reference']+['force']*4+['body','projection','projection'])*H
        center=dict(x=np.zeros(N),rows=[None]*H,labels=labels,g=np.tile([.5,3,4.85,.159,.159,.159,.159,100,.5,5.],H),ratios=np.full(4*H,.9),P=np.zeros((H,2)),V=np.zeros((H,4,2)))
        linear=dict(J=np.zeros((10*H,N)),R=np.zeros((4*H,N)),O=np.zeros((H,N)),T=np.zeros(N),P=np.zeros((H,2,N)),V=np.zeros((H,4,2,N)));env=dict(g=np.zeros(10*H),ratio=np.zeros(4*H),position=np.zeros(H))
        owner=SimpleNamespace(start=dict(tracking=[3,160]),seed_x=np.zeros(N),segA=np.tile([-1.,0.],(H,1)),segB=np.tile([1.,0.],(H,1)))
        features=[dict(raw=0,normal=[1.,0.],offset=-1.,polygon=0,kind='road',feature=0)]
        p,detail=matrix(owner,center,linear,env,features,[[0,1,2,3]],[],.05);self.assertEqual(p['A'].shape[1],396);self.assertTrue(check(p,center['x'])['pass_all']);self.assertEqual(detail['initial_counts'],[3,160])
    def test_checkpoint_clone_preserves_clock_and_does_not_alias_mutables(self):
        tracker=FinishLineTracker(center=(0.,0.),forward=(1.,0.),half_width=2.,half_depth=.875);elapsed=0.
        for _ in range(136):elapsed+=.02
        state=dict(root=object(),visited={1},tracker=tracker,elapsed=elapsed,global_raw=136,progress=132.,launch=[55,384],tracking=[3,160]);cp=clone(state);cp['visited'].add(2);cp['tracking'][0]=4;cp['tracker'].departed_start_area=True
        self.assertEqual(cp['elapsed'],elapsed);self.assertNotEqual(elapsed,.02*136);self.assertEqual(state['visited'],{1});self.assertEqual(state['tracking'],[3,160]);self.assertFalse(state['tracker'].departed_start_area)

if __name__=='__main__':unittest.main()
