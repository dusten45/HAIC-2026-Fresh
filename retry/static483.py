"""Integrated zero-world gate for483 ranking, quota, cleanup and source root."""
import ast,copy,io,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np
import retry.online483 as online
import retry.online481 as base
from retry.io483 import Quota,load_receipt
from retry.meter483 import Meter483
from retry.paired417_common import SourceC
from retry.static481 import Gate481Tests
from retry.test_history481 import HistoryFinite481Tests
from retry.test_history483 import History483Tests
G=Path(__file__).resolve().parents[1]
ROOT=Path('/workspace/haic-private-retry-20261009')

class Gate483Tests(unittest.TestCase):
    def test_root_inclusive_margin_and_unchanged_geometry(self):
        row=dict(predicted=dict(position=[1.,0.],velocity=[1.,0.],raw_ticks=1),memory_after={'C':{'phase':'FIRST_LAP'}},raw_hull=[dict(origin_position=[1.,2.],origin_linear_velocity=[1.,0.])])
        line=[[0.,0.],[10.,0.],[10.,5.],[0.,5.]]
        self.assertEqual(online.max_guard_error(row,line),1.) # nearest side at x0
        row['raw_hull'][0]['origin_position']=[3.,2.]
        self.assertEqual(online.max_guard_error(row,line),2.)
    def test_exact_ranking_and_no_epsilon(self):
        a=dict(M80=.1,max_guard_path_error_m=1.,active_pedal=0.);b=dict(M80=.2,max_guard_path_error_m=.9,active_pedal=.3)
        self.assertLess(online.rank(a,'control'),online.rank(b,'control'));self.assertGreater(online.rank(a,'variant'),online.rank(b,'variant'))
        self.assertLess(online.rank({**a,'active_pedal':1.},'control'),online.rank(a,'control'))
        self.assertLess(online.rank({**a,'max_guard_path_error_m':1.-1e-12},'variant'),online.rank(a,'variant'))
    def test_decision_partial_holds_and_registered_typed_outcomes(self):
        control=dict(status='EMPTY_FINITE_CANDIDATE_DOMAIN',actions=4,raw_ticks=16,raw_lengths=[4]*4,margins_m=[1.]*4,official_own_finish=False)
        variant=dict(status='H6_SAFE_CENSORED',actions=6,raw_ticks=24,raw_lengths=[4]*6,margins_m=[1.3]*6,official_own_finish=False)
        self.assertTrue(online.decision(control,variant)['primary'])
        partial={**control,'raw_lengths':[4,4,4,1],'raw_ticks':13}
        self.assertEqual(online.decision(partial,variant)['verdict'],'LOCAL_INCONCLUSIVE')
        self.assertEqual(online.decision(control,{**variant,'status':'INFEASIBLE'})['verdict'],'LOCAL_INCONCLUSIVE')
        self.assertEqual(online.decision(control,{**variant,'status':'UNSAFE'})['verdict'],'LOCAL_HYPOTHESIS_REJECTED')
    def test_new_codec_full_context_and_tamper(self):
        value=load_receipt(ROOT/'stage481/context-198-private.json')
        with tempfile.TemporaryDirectory(prefix='haic483-static-') as name:
            d=Path(name);quota=Quota(d,201085448,16*1024**2);p=d/'context-001-private.json';quota.save_receipt(p,value)
            self.assertEqual(load_receipt(p),value);self.assertEqual(len(quota.objects),1)
            obj=next(d.glob('state-*.json'));x=json.loads(obj.read_text());x['full_state']['elapsed_raw_steps']+=1;obj.write_text(json.dumps(x))
            with self.assertRaises(Exception):load_receipt(p)
    def test_durable_ordinary_receipt_preserves_RNG_bytes(self):
        import pickle
        from retry.receipt421_io import save_receipt
        ctx=load_receipt(ROOT/'stage481/context-198-private.json')
        with tempfile.TemporaryDirectory(prefix='haic483-static-') as name:
            p=Path(name)/'durable-material.json';save_receipt(p,dict(context=ctx));r=load_receipt(p)
            self.assertIsInstance(r['context']['RNG']['global_pickle'],bytes)
            self.assertEqual(r['context']['RNG']['global_pickle'],ctx['RNG']['global_pickle']);self.assertEqual(len(pickle.loads(r['context']['RNG']['global_pickle'])),2)
    def test_caps_and_literal_codec_reuse(self):
        from retry.io481 import Quota as Old
        self.assertTrue(issubclass(Quota,Old));self.assertEqual(Quota.STATE_MAX*Quota.STATES_MAX+Quota.NONSTATE_MODEL_MAX,156860416)
        self.assertEqual((Meter483.HARD_TICKS,Meter483.HARD_WORLDS),(520,110))
        for caps in ((201085449,16*1024**2),(201085448,16*1024**2+1)):
            with self.assertRaises(Exception):Quota(Path('/tmp'),*caps)
    def test_close_destroys_bodies_and_breaks_retained_world_refs(self):
        world=NS(bodies=[1,2],joints=[]);world.DestroyBody=lambda body:world.bodies.remove(body)
        model=NS(world=world);model.close=lambda:None;child=NS(m=model);stream=NS(child=child,world=model,ctrl=object())
        meter=Meter483.__new__(Meter483);meter.live=[model];meter.integrating_worlds=0;meter.streams={id(model):stream};meter.auth={id(model):{}};meter.closed_worlds=0;meter.persist=lambda:None
        meter.close(model);self.assertEqual(world.bodies,[]);self.assertIsNone(child.m);self.assertIsNone(stream.world);self.assertFalse(meter.live);self.assertEqual(model.__dict__,{'closed483':True})
    def test_live_and_wrapper_caps_before_underlying_dispatch(self):
        meter=Meter483.__new__(Meter483);meter.active=True;meter.guard=lambda:None;meter.b={'worlds':0,'ticks':0};meter.live=[object(),object()];meter.integrating_worlds=0
        with self.assertRaises(Exception):meter.world({},'static')
        meter.wrapper_slots=130;meter.charged_ticks=0
        with self.assertRaises(Exception):meter.step(meter.live[0],None,'static')
    def test_SourceC_pre122_nominal_once_without_world(self):
        from retry.io481 import read
        p=read(ROOT/'stage481-plan-durable-private.json');m=read(p['input_material_path']);ctx=read(ROOT/'stage481/context-198-private.json');physical=ctx['state']['physical'];h=physical['hull']
        model=NS(t=physical['actual_time'],car=NS(hull=NS(position=h['position'],linearVelocity=h['velocity'],angle=h['angle'],angularVelocity=h['angular_velocity']),wheels=[NS(joint=NS(angle=w['joint']['angle']),tiles=w['tiles']) for w in physical['wheels']]),finish_line_tracker=NS(**ctx['state']['finish_tracker']),finished=False)
        pace=m['pace']['frozen268'] if isinstance(m['pace'],dict) else m['pace'];ctrl=SourceC(m['fixed'],np.asarray(pace),copy.deepcopy(ctx['before']));ctrl.policy.nodes=np.asarray(m['projected_nodes']);action=ctrl.act(model)
        self.assertEqual(action.tolist(),ctx['nominal']);self.assertEqual(ctrl.memory(),ctx['after'])
    def test_protocol_prepared_nominal_AST(self):
        tree=ast.parse((G/'retry/online483.py').read_text());prepare=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='prepare')
        self.assertEqual(sum(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='act' for n in ast.walk(prepare)),1)
        self.assertIn('>=26',(G/'retry/live483.py').read_text())
        self.assertIn('meter.allocator_CPU_s>10 or meter.allocator_wall_s>20',(G/'retry/live483.py').read_text())

def run():
    from retry.pilot420_backend import TerminalVehicleTransition
    from retry.source_vehicle_transition import SourceVehicleTransition
    suite=unittest.TestSuite()
    for cls in (Gate481Tests,HistoryFinite481Tests,History483Tests,Gate483Tests):suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
    stream=io.StringIO()
    with patch.object(TerminalVehicleTransition,'__init__',side_effect=AssertionError('483_STATIC_WORLD_FORBIDDEN')),patch.object(TerminalVehicleTransition,'step',side_effect=AssertionError('483_STATIC_STEP_FORBIDDEN')),patch.object(SourceVehicleTransition,'__init__',side_effect=AssertionError('483_STATIC_SOURCE_WORLD_FORBIDDEN')),patch.object(SourceVehicleTransition,'step',side_effect=AssertionError('483_STATIC_SOURCE_STEP_FORBIDDEN')):
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    return dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=stream.getvalue(),new_worlds=0,new_ticks=0)
if __name__=='__main__':
    x=run();print(json.dumps(x));raise SystemExit(0 if x['passed'] else 1)
