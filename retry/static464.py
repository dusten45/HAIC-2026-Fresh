"""One saved-only464 gate: meaningful law arithmetic and zero physics calls."""
import contextlib,io,json,math,signal,sys,time,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from retry.design464_math import saved_secant_terms,calculate

class Design464Tests(unittest.TestCase):
    def fixture(self,nodes=None,pos=(2.,0.),vel=(10.,0.)):
        fixed=dict(line=[[0.,0.],[10.,0.],[10.,10.],[0.,10.]],free_profile=dict(ds=[10.]*4,speed=nodes or [10.,20.,20.,20.,10.]),model=dict(rear_traction_accel=100.,brake_accel=100.,effective_mass=10.))
        row=dict(pre=dict(pos=list(pos),vel=list(vel),speed=math.hypot(*vel)),nominal_memory_after=dict(C=dict(phase='FIRST_LAP')),nominal=[0.,0.,0.],command=[0.,0.,0.])
        return fixed,np.ones(5),row
    def test_secant_differs_within_squared_speed_segment_without_node_switch(self):
        fixed,pace,row=self.fixture();z=saved_secant_terms(fixed,pace,row)
        self.assertTrue(z['eligible']);self.assertEqual(z['crossed_nodes'],0)
        r=math.sqrt(160);end=math.sqrt(184)
        self.assertAlmostEqual(z['ff_secant'],(end-r)/.08)
        self.assertAlmostEqual(z['ff_secant']/z['ff_point'],2*r/(r+end))
        self.assertLess(z['ff_secant'],z['ff_point'])
    def test_constant_reference_keeps_zero_feedforward(self):
        fixed,pace,row=self.fixture(nodes=[20.]*5);z=saved_secant_terms(fixed,pace,row)
        self.assertEqual(z['ff_secant'],0.);self.assertEqual(z['ff_point'],0.)
        self.assertAlmostEqual(z['raw'],1.5*(20-10))
    def test_endpoint_average_does_not_protect_an_interior_speed_valley(self):
        fixed,pace,row=self.fixture(nodes=[20.,5.,20.,20.,20.],pos=(.9,0.),vel=(15.,0.))
        fixed['line']=(np.asarray(fixed['line'])*.1).tolist();fixed['free_profile']['ds']=[1.]*4
        z=saved_secant_terms(fixed,pace,row)
        self.assertTrue(z['interior_reference_valley']);self.assertTrue(z['endpoint_drives_despite_interior_target_below_speed'])
    def test_strict_domain_has_no_epsilon_clamp_or_periodic_extension(self):
        fixed,pace,row=self.fixture()
        for vel in ([0.,0.],[-10.,0.],[1000.,0.]):
            row['pre']['vel']=vel;self.assertFalse(saved_secant_terms(fixed,pace,row)['eligible'])
        row['nominal_memory_after']['C']['phase']='FINISH_CONFIRM'
        self.assertEqual(saved_secant_terms(fixed,pace,row)['reason'],'phase')
    def test_all_worlds_and_two_independent_trajectories_are_costed(self):
        c=json.loads((Path(__file__).resolve().parent/'design464_next.json').read_text());b=calculate(c)
        self.assertEqual((b['ticks'],b['worlds']),(1242+2*(2*13*4+4),35+2*3))
        self.assertEqual((b['trajectory_worlds'],b['held_first_worlds'],b['separate_main_parent_worlds']),(4,2,0))
        self.assertEqual((b['actual_actions'],b['resets']),(0,0))
        self.assertLessEqual(b['ticks'],c['selected_contract']['hard']['ticks']);self.assertLessEqual(b['worlds'],c['selected_contract']['hard']['worlds'])

def run(root):
    from retry.source_vehicle_transition import SourceVehicleTransition
    from retry.terminal410_model import TerminalVehicleTransition
    from retry import diagnose
    from retry.analyze464 import run as analyze
    import Box2D
    cpu,wall=time.process_time(),time.perf_counter();stream=io.StringIO();result=None;public=None;error=None;forbidden=[]
    def timeout(*args):raise RuntimeError('464_saved_gate_CPU180_wall300')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};signal.setitimer(signal.ITIMER_PROF,max(.001,179-time.process_time()));signal.setitimer(signal.ITIMER_REAL,299)
    try:
        with contextlib.ExitStack() as stack:
            for cls in [SourceVehicleTransition,TerminalVehicleTransition]:
                for method in ['__init__','step']:forbidden.append(stack.enter_context(patch.object(cls,method,side_effect=AssertionError('464_FORBIDDEN_PHYSICS'))))
            forbidden.append(stack.enter_context(patch.object(diagnose,'make_env',side_effect=AssertionError('464_FORBIDDEN_NATIVE'))))
            forbidden.append(stack.enter_context(patch.object(Box2D,'b2World',side_effect=AssertionError('464_FORBIDDEN_WORLD'))))
            result=unittest.TextTestRunner(stream=stream,verbosity=2,failfast=True).run(unittest.defaultTestLoader.loadTestsFromTestCase(Design464Tests))
            if result.wasSuccessful():public=analyze(root)
            for guard in forbidden:guard.assert_not_called()
    except BaseException as exc:error=type(exc).__name__+': '+str(exc)
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for sig,handler in handlers.items():signal.signal(sig,handler)
    g=Path(__file__).resolve().parent;gate=dict(stage=464,passed=bool(result and result.wasSuccessful() and public is not None and error is None),error=error,tests=0 if result is None else result.testsRun,failures=0 if result is None else len(result.failures),errors=0 if result is None else len(result.errors),forbidden_physics_calls=sum(x.call_count for x in forbidden),new_actual_model_world_reset_seed_learning_HOLDOUT_SEALED_reserve_paid=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    (g/'structural464_gate.json').write_text(json.dumps(gate,indent=2)+'\n')
    if public is not None:(g/'structural464_result.json').write_text(json.dumps(public,indent=2)+'\n')
    print(json.dumps(gate));print(stream.getvalue() if not gate['passed'] else 'Saved-only gate passed; no integration.')

if __name__=='__main__':run(Path(sys.argv[1]).resolve())
