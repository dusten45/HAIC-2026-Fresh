import unittest
import numpy as np
from retry.direct577_math import propose,choose,bases

class Direct577(unittest.TestCase):
    def test_quantized_domain_and_global_trust(self):
        seed=np.tile(np.asarray([.4,1.],np.float32).astype(float),132);x,r=propose(seed,seed,np.ones(264),.004,1);self.assertTrue(np.array_equal(x,seed));self.assertTrue(r['exact_float32']);x,r=propose(seed,seed,np.ones(264),.004,-1);self.assertGreater(max(abs(x-seed)),0.);self.assertLessEqual(r['normalized_seed_displacement'],.012)
    def test_unsafe_and_raw_regression_never_win(self):
        cases=[dict(safe=False,raw=650,hull=13.),dict(safe=True,raw=661,hull=13.),dict(safe=True,raw=660,hull=13.1935)];self.assertEqual(choose(13.1936,660,cases),2);self.assertIsNone(choose(13.1935,660,cases))
    def test_six_disjoint_projected_bases(self):
        p=dict(A=np.zeros((8760,396)),b=np.ones(8760),ratio_rows=np.arange(4734,6656),objective=np.linspace(-1,1,264));linear=dict(J=np.zeros((5260,264)));g=np.ones(5260);B,details=bases(p,linear,g);self.assertEqual(B.shape,(6,264));self.assertEqual(np.linalg.matrix_rank(B),6)
        for k,v in enumerate(B):self.assertEqual(max(abs(v)),1.);self.assertTrue(np.all(v[:44*k]==0));self.assertTrue(np.all(v[44*(k+1):]==0));self.assertLessEqual(p['objective']@v,0.)

if __name__=='__main__':unittest.main()
