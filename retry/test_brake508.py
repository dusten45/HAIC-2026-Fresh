import math,unittest
from dataclasses import replace
from retry.brake506_geometry import Geometry,rectangle,contacts,forecast as old
from retry.brake508_corridor import budget,corridor,bounds,indexed_contacts,forecast
from retry.test_brake505 import fixture


class CorridorTests(unittest.TestCase):
    def test_complete_branch_budget(self):
        b=budget();self.assertEqual(b['worlds'],4);self.assertEqual(b['positive_ticks'],128);self.assertEqual(b['zero_dt_primes'],4)
        self.assertEqual(b['failure_analysis_extra_worlds'],0)
        self.assertEqual(budget(2,2,2)['positive_ticks'],32)
    def test_contact_index_matches_full_polygon_search(self):
        roads,_,_=corridor(mixed=True);index=bounds(roads)
        for x in (-4.,-1.,0.,2.):
            for y in (0.,8.,16.,28.,40.):
                for angle in (0.,.2,.5):
                    p=rectangle((x,y),angle)
                    self.assertEqual(indexed_contacts(p,roads,index,.02),contacts(p,roads,.02))
    def test_accelerated_forecast_is_identical(self):
        roads,_,_=corridor(mixed=True);p=fixture();s=Geometry(p,(0.,0.),roads,((0,),)*4,240.,.02)
        for brake in (0.,.1,.4):
            a,rows=old(s,brake);b,other=forecast(s,brake)
            self.assertEqual(a,b)
            self.assertEqual([r['contacts_used'] for r in rows],[r['contacts_used'] for r in other])


if __name__=='__main__':unittest.main()
