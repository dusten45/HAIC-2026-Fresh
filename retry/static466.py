"""Pure466 arithmetic fixtures and saved analysis; all physics forbidden."""
import contextlib,io,json,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from retry.analyze466 import segment_proxy,project_four,clock_at

class Numeric466(unittest.TestCase):
    def model(self):return dict(mass=10.,effective_mass=30.,rear_traction_accel=5.,brake_accel=10.)
    def test_lateral_internal_extremum_is_same_location_not_global_max_mix(self):
        x=segment_proxy(1.,9.,9.,1.,1.,self.model())
        self.assertAlmostEqual(x['lateral_witness_fraction'],.5);self.assertAlmostEqual(x['max_lateral_force_abs_N'],250.)
    def test_contact_translation_and_engine_equivalent_masses_are_separate(self):
        x=segment_proxy(4.,8.,0.,0.,1.,self.model())
        self.assertAlmostEqual(x['aggregate_translation_circle_ratio'],20/1600)
        self.assertAlmostEqual(x['rear_equal_axle_drive_circle_ratio'],40/800)
    def test_four_pass_never_raises_upper_nodes_and_keeps_launch_zero(self):
        old=np.asarray([0.,50.,10.,50.]);new=project_four(old,[1.,1.,1.],self.model())
        self.assertEqual(new[0],0.);self.assertTrue(np.all(new<=old));self.assertTrue(np.all(new[1:]>0))
    def test_reference_clock_integrates_squared_speed_exactly(self):
        self.assertAlmostEqual(clock_at(10,[10.,20.],[10.]),20/30)
        self.assertAlmostEqual(clock_at(5,[10.,20.],[10.]),10/(10+np.sqrt(250)))

def run(root,output_name='stage466'):
    from retry import diagnose
    from retry.source_vehicle_transition import SourceVehicleTransition
    from retry.terminal410_model import TerminalVehicleTransition
    import Box2D
    from retry.analyze466 import run as analyze
    cpu,wall=time.process_time(),time.perf_counter();stream=io.StringIO();public=None;error=None;result=None;forbidden=[]
    try:
        with contextlib.ExitStack() as stack:
            for cls in [SourceVehicleTransition,TerminalVehicleTransition]:
                for method in ['__init__','step']:forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('466_FORBIDDEN_PHYSICS'))))
            forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('466_FORBIDDEN_NATIVE'))));forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('466_FORBIDDEN_WORLD'))))
            result=unittest.TextTestRunner(stream=stream,verbosity=2,failfast=True).run(unittest.defaultTestLoader.loadTestsFromTestCase(Numeric466))
            if result.wasSuccessful():public=analyze(root,output_name)
            for call in forbidden:call.assert_not_called()
    except BaseException as exc:error=type(exc).__name__+': '+str(exc)
    gate=dict(stage=466,passed=bool(result and result.wasSuccessful() and public is not None and error is None),error=error,tests=0 if result is None else result.testsRun,forbidden_physics_calls=sum(x.call_count for x in forbidden),compression_implementation_executed=False,new_physics_native_world_reset=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    g=Path(__file__).resolve().parent;(g/'structural466_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
    if public is not None:(g/'structural466_result.json').write_text(json.dumps(public,indent=2)+'\n')
    print(json.dumps(gate));print('Saved-only466 complete.' if gate['passed'] else stream.getvalue())

if __name__=='__main__':run(Path(sys.argv[1]).resolve(),sys.argv[2] if len(sys.argv)>2 else 'stage466')
