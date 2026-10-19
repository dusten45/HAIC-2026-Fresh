"""World-free telemetry-equivalence, counter and trial-history isolation tests."""
import itertools,math,unittest
from retry.feedback596_trace import Trial,post_flags
class PureTests(unittest.TestCase):
 def test_old537_post_order_and_boundaries(self):
  for m,o,d,s in itertools.product([math.nextafter(.5,0),.5,1.],[4.85,math.nextafter(4.85,math.inf)],[3.,math.nextafter(3.,math.inf)],[-.500001,-.5,0.,5.,5.000001]):
   old='FORECAST_FOOTPRINT_MARGIN' if m<.5 else 'REFERENCE_WITH_NUMERIC_RESERVE' if o>4.85 else 'PROJECTION_OR_PATH' if d>3 or s<-.5 or s>5 else None
   self.assertEqual(post_flags(m,o,d,s,5)[2],old)
 def test_each_trial_uses_actual_history_independently(self):
  actual=[15,240];a=Trial(actual,151.,1.);b=Trial(actual,151.,1.);a.force([dict(ratio=1.01,clipped=True)]*4,1.059);self.assertEqual(actual,[15,240]);self.assertEqual(b.history,[15,240]);self.assertEqual(a.history,[19,244])
 def test_force_failure_before_tick_is_an_attempt(self):
  t=Trial([15,240],151.,1.);self.assertEqual(t.force([dict(ratio=1.06,clipped=True)]*4,1.059),'FORCE_PEAK');self.assertEqual((t.attempts,t.ticks),(1,0))
 def test_path_projection_numeric_branches(self):
  t=Trial([15,240],151.,1.);flags,first=t.post(.6,4.,3.01,1.7,5.);self.assertEqual(first,'PATH');self.assertEqual(t.reason,'PROJECTION_OR_PATH');self.assertFalse(flags['PROJECTION_FORWARD']);self.assertEqual(post_flags(.6,4.,2.,5.1,5.)[1],'PROJECTION_FORWARD')

class CertificateEquivalence(unittest.TestCase):
 def test_original_certificate_matches_passive_trial_without_physics(self):
  from dataclasses import dataclass,replace
  from unittest.mock import patch
  import retry.structure537_control as p
  @dataclass(frozen=True)
  class Linear: velocity:tuple=(2.,0.)
  @dataclass(frozen=True)
  class Planar: linear:object=None;steer:float=0.
  @dataclass(frozen=True)
  class Root: planar:object=None;center:tuple=(0.,0.);roads:tuple=()
  root=Root(Planar(Linear()));a=__import__('numpy').array([0.,1.,0.],dtype='float32')
  for fail_at in [None,3]:
   t=Trial([15,240],0.,1.);n=[0];counter=[0];cost=dict(forecast_calls=0,force_evaluations=0,forecast_ticks=0)
   def forces(r,a):
    n[0]+=1;f=[dict(ratio=1.06 if n[0]==fail_at else .5,clipped=n[0]==fail_at)]*4;t.force(f,p.ADMISSION);return f
   def tick(r,gas,brake,index,c):c[0]+=1;t.ticks+=1;return replace(r,center=(r.center[0]+.04,0.))
   def projection(position,path,previous):t.post(1.,-1.,0.,.04,5.);return dict(s=position[0],distance=0.)
   with patch.multiple(p,bounds=lambda roads:None,margin=lambda *a:1.,force_rows=forces,tick=tick,project=projection,reference=lambda *a:(3.,0.),backup=lambda *a:a):
    # Backup must return an action, independently of the Root argument.
    with patch.object(p,'backup',lambda *args:a):
     report=p.certifier(root,{}, {},0.,counter,cost,dict(max_checks=100,roads=(),road_index=None,boundary=(),edge_index=None,obstacles=()),history=(15,240))(a)
   for k in ['ok','reason','peak','max_reference_overspeed','clipped','samples','model_ticks','min_footprint_margin_m']:self.assertEqual(report[k],t.summary()[k],k)
   self.assertEqual(counter[0],48 if fail_at is None else 2)
