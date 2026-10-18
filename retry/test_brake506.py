import math,unittest
from retry.brake506_geometry import rectangle,polygon_distance,contacts,Geometry,forecast,select
from retry.test_brake505 import fixture


class GeometryTests(unittest.TestCase):
    def test_polygon_distance_edge_corner_and_overlap(self):
        a=[(0.,0.),(1.,0.),(1.,1.),(0.,1.)]
        self.assertEqual(polygon_distance(a,a),0.)
        self.assertAlmostEqual(polygon_distance(a,[(2.,2.),(3.,2.),(3.,3.),(2.,3.)]),math.sqrt(2))
        self.assertAlmostEqual(polygon_distance(a,[(1.1,0.),(2.,0.),(2.,1.),(1.1,1.)]),.1)
    def test_footprint_and_skin_not_center_membership(self):
        road=([(0.,-5.),(5.,-5.),(5.,5.),(0.,5.)],1.)
        self.assertEqual(contacts(rectangle((-.2,0.),0.),(road,),.02),(0,))
        self.assertEqual(contacts(rectangle((-.299,0.),0.),(road,),.02),(0,))
        self.assertEqual(contacts(rectangle((-.301,0.),0.),(road,),.02),())
    def test_sensor_prepose_updates_next_force(self):
        p=fixture();road=([(-10.,-20.),(10.,-20.),(10.,2.6),(-10.,2.6)],1.)
        state=Geometry(p,(0.,0.),(road,),((0,),)*4,240.,.02)
        _,rows=forecast(state,.2)
        self.assertEqual(rows[0]['contacts_used'],((0,),)*4)
        self.assertEqual(rows[1]['contacts_used'],rows[0]['contacts_for_next_force'])
        self.assertEqual(rows[1]['contacts_used'],((0,),)*4)
    def test_nonmonotone_contact_response_selects_feasible_boundary(self):
        end=lambda b:0. if .1<=b<.15 or b>=.7 else 2.
        b,value=select(end,.5)
        self.assertGreaterEqual(b,.1);self.assertLess(b,.15)
        self.assertLessEqual(value,.5)


if __name__=='__main__':unittest.main()
