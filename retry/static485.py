"""Mandatory integrated485 static gate; every physics entry point is poisoned.

Bootstrap tests are required, never skipped. This module defines tests on import;
only its explicit run() executes pure fixtures and temporary serialization.
"""
import contextlib
import importlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import Mock,patch

from retry.meter485 import Meter485
from retry.paired442_meter import Meter as Meter442


class Gate485Tests(unittest.TestCase):
    def meter(self,d):
        m=Meter485.__new__(Meter485)
        m.d=Path(d);m.active=True;m.guard=lambda:None;m.persist=lambda:None
        m.b={'worlds':0,'ticks':0};m.live=[];m.streams={};m.auth={}
        m.charged_ticks=0;m.wrapper_slots=0;m.integrating_worlds=0
        m.peak_integrating=0;m.closed_worlds=0;m.qualification_passed=True
        return m

    def test_fixed_counts_and_live_caps_before_dispatch(self):
        self.assertEqual((Meter485.HARD_WORLDS,Meter485.HARD_TICKS),(226,1064))
        with tempfile.TemporaryDirectory(prefix='haic485-meter-static-') as d:
            m=self.meter(d);m.live=[object(),object()]
            with self.assertRaises(Exception):m.world({},'forbidden')
            for attr,value in [('charged_ticks',1064),('wrapper_slots',266)]:
                setattr(m,attr,value)
                with patch.object(Meter442,'step') as dispatch:
                    with self.assertRaises(Exception):m.step(m.live[0],None,'forbidden')
                    dispatch.assert_not_called()
                setattr(m,attr,0)

    def test_world_header_sum_before_first_dispatch_exact_boundary(self):
        for total,accepted in [(829464,True),(829465,False)]:
            with self.subTest(total=total),tempfile.TemporaryDirectory(prefix='haic485-header-static-') as d:
                m=self.meter(d);model=object();m.live=[model]
                m.auth[id(model)]={'number':1,'first_step':False}
                m.streams[id(model)]=NS(label='fixture')
                (m.d/'world1-before-constructor-private.json').write_bytes(b'x'*400000)
                (m.d/'fixture-runtime-link-private.json').write_bytes(b'x'*200000)
                def first_receipt(path,value):Path(path).write_bytes(b'x'*(total-600000))
                with patch('retry.meter485.save_receipt',side_effect=first_receipt),patch('retry.meter485.snapshot',return_value={}),patch('retry.meter485.rnghash',return_value='0'*64),patch.object(Meter442,'step',return_value='pure-stub') as dispatch:
                    if accepted:
                        self.assertEqual(m.step(model,[0.,0.,0.],'fixture'),'pure-stub')
                        dispatch.assert_called_once();self.assertEqual((m.charged_ticks,m.wrapper_slots),(4,1))
                    else:
                        with self.assertRaises(Exception):m.step(model,[0.,0.,0.],'fixture')
                        dispatch.assert_not_called();self.assertEqual((m.charged_ticks,m.wrapper_slots),(0,0))
                self.assertEqual(m.integrating_worlds,0)

    def test_native_caps_before_hook_or_dispatch(self):
        with tempfile.TemporaryDirectory(prefix='haic485-native-static-') as d:
            m=self.meter(d);m.active=None;m.actual_start=(1.,1.);m.native_charge_hook=Mock()
            m.nb={'actions':256,'resets':2,'arm_actions':{'D485-A':128},'arm_resets':{'D485-A':1}}
            m.raw_counts={'D485-A':dict(reset_raw=64,action_raw=512)}
            for kind in ('action','reset','action_raw','reset_raw'):
                with self.assertRaises(Exception):m.charge(kind,'D485-A')
            m.native_charge_hook.assert_not_called()

    def test_close_releases_actual_world_and_retained_references(self):
        world=NS(bodies=[1,2],joints=[]);world.DestroyBody=lambda body:world.bodies.remove(body)
        model=NS(world=world);model.close=lambda:None
        child=NS(m=model);stream=NS(child=child,world=model,ctrl=object())
        with tempfile.TemporaryDirectory(prefix='haic485-close-static-') as d:
            m=self.meter(d);m.live=[model];m.streams={id(model):stream};m.auth={id(model):{}}
            m.close(model)
            self.assertFalse(world.bodies);self.assertFalse(m.live);self.assertFalse(m.auth);self.assertFalse(m.streams)
            self.assertIsNone(child.m);self.assertIsNone(stream.world);self.assertIsNone(stream.ctrl)
            self.assertEqual(model.__dict__,{'closed485':True});self.assertEqual(m.closed_worlds,1)


def run():
    names=('test_policy485','test_history485','test_quota485','test_bootstrap485')
    missing=[n for n in names if not (Path(__file__).parent/(n+'.py')).is_file()]
    if missing:
        return dict(passed=False,tests=0,failures='Required test modules missing: '+','.join(missing),new_worlds=0,new_ticks=0,new_native=0,new_resets=0)
    import Box2D
    from core.vendor.car_racing import CarRacing
    from core.vendor.car_dynamics import Car
    from retry.pilot420_backend import TerminalVehicleTransition
    from retry.source_vehicle_transition import SourceVehicleTransition
    import retry.diagnose as diagnose
    stream=io.StringIO();suite=unittest.TestSuite()
    forbidden=AssertionError('485_STATIC_PHYSICS_OR_CONSTRUCTOR_FORBIDDEN')
    targets=[(Box2D,'b2World'),(CarRacing,'__init__'),(CarRacing,'reset'),(CarRacing,'step'),(Car,'step'),(TerminalVehicleTransition,'__init__'),(TerminalVehicleTransition,'step'),(SourceVehicleTransition,'__init__'),(SourceVehicleTransition,'step'),(diagnose,'make_env')]
    with contextlib.ExitStack() as stack:
        for obj,attr in targets:stack.enter_context(patch.object(obj,attr,side_effect=forbidden))
        for name in names:
            suite.addTests(unittest.defaultTestLoader.loadTestsFromModule(importlib.import_module('retry.'+name)))
        from retry.static481 import Gate481Tests
        suite.addTest(Gate481Tests('test_sourceC_real_pre23_and_pending_without_world'))
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(Gate485Tests))
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    return dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=stream.getvalue(),new_worlds=0,new_ticks=0,new_native=0,new_resets=0)


if __name__=='__main__':
    result=run();print(json.dumps(result));raise SystemExit(0 if result['passed'] else 1)
