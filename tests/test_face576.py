import unittest
import numpy as np
from retry.face576_math import active_face,enclosures

class Face576(unittest.TestCase):
    def problem(self):
        return dict(x0=np.asarray([.4,1.,.1,.2],np.float32).astype(float),scale=np.asarray([.003,.03,.003,.03]),bounds=np.asarray([[-.05,0],[-.05,0],[-.05,.05],[-.05,.05],[0,.05],[0,.05]],float),groups=[2,4],A=np.zeros((1,6)),b=np.ones(1),objective=np.zeros(4),ratio_rows=[],path=None)
    def test_exact_endpoint_face_and_seed_union(self):
        original=self.problem();p,fixed,q,box=active_face(original,2);self.assertTrue(np.array_equal(fixed,[True,True,False,False]));self.assertTrue(np.all(q[:2]==0));self.assertEqual(box[4,1],0.);self.assertEqual(original['bounds'][0,0],-.05);self.assertTrue(enclosures(p,fixed,q,box)['all_pass'])
    def test_adjacent_binade_value_is_in_predetermined_excluded_set(self):
        p=self.problem();p['x0'][1]=float(np.nextafter(np.float32(1),np.float32(0),dtype=np.float32));p['bounds'][1,1]=(1.-p['x0'][1])/.03;face,fixed,q,box=active_face(p,2);self.assertTrue(np.array_equal(fixed,[True,True,False,False]));self.assertEqual(enclosures(face,fixed,q,box)['adjacent_float32_count'],1)
    def test_ordinary_interior_value_is_not_frozen(self):
        p=self.problem();p['x0'][1]=float(np.float32(.9));p['bounds'][1]=[-.05,.05];_,fixed,_,_=active_face(p,1);self.assertTrue(np.array_equal(fixed,[True,False,False,False]))
    def test_wrong_count_fails_without_branch_search(self):
        with self.assertRaises(ValueError):active_face(self.problem(),40)

if __name__=='__main__':unittest.main()
