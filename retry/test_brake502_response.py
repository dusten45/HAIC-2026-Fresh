"""Independent one-force checks against the actual Car methods, without Box2D."""
import ast
import itertools
import math
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import numpy as np
from retry.brake502_response import Wheel, State, wheel_response, choose_brake, f32


def source_car_class():
    path = Path(__file__).resolve().parents[1]/'core/vendor/car_dynamics.py'
    tree = ast.parse(path.read_text())
    car = next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Car')
    names = {'SIZE','ENGINE_POWER','WHEEL_MOMENT_OF_INERTIA','FRICTION_LIMIT'}
    constants = [n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in names for t in n.targets)]
    methods = [n for n in car.body if isinstance(n,ast.FunctionDef) and n.name in ('gas','brake','step')]
    reduced = ast.Module(body=constants+[ast.ClassDef(name='SourceCar',bases=[],keywords=[],body=methods,decorator_list=[])],type_ignores=[])
    ast.fix_missing_locations(reduced)
    namespace = {'np':np}
    exec(compile(reduced,str(path)+'#force-only-no-constructor','exec'),namespace)
    return namespace['SourceCar']


class FakeWheel:
    def __init__(self,omega,gas,velocity,heading,friction):
        self.omega,self.gas,self.linearVelocity,self.heading = omega,gas,velocity,heading
        self.joint=NS(angle=0.,motorSpeed=0.)
        self.steer=0.; self.brake=0.; self.phase=0.; self.wheel_rad=.54
        self.tiles=[NS(road_friction=friction/400.)]
        self.skid_particle=None; self.skid_start=None; self.position=(0.,0.)
    def GetWorldVector(self,axis):
        c,s=math.cos(self.heading),math.sin(self.heading)
        return (c*axis[0]-s*axis[1],s*axis[0]+c*axis[1])
    def ApplyForceToCenter(self,force,wake):
        self.force=force


class ResponseTests(unittest.TestCase):
    def test_force_matches_actual_source(self):
        Car=source_car_class(); count=0
        for speed,slip,lateral,brake,heading,grip,engine in itertools.product(
                (20.,60.,95.),(-12.,0.,12.),(0.,8.),(0.,.2,f32(.9),1.),(0.,.2),(.5,1.),(.6,1.)):
            car=Car(); car.fuel_spent=0.; car.grass_friction_multiplier=.6
            car.grip_multiplier=grip; car.engine_multiplier=engine;car.steering_multiplier=1.
            omega=(speed+slip)/.54
            car.wheels=[FakeWheel(omega,0. if i<2 else .7,(lateral,speed),heading,400.) for i in range(4)]
            car.gas(.9);car.brake(brake)
            expected=[]
            for w in car.wheels:
                expected.append(wheel_response(Wheel(omega,heading=heading,friction=400*grip),(lateral,speed),w.gas,brake,engine))
            car.step(.02)
            for w,(after,force,detail) in zip(car.wheels,expected):
                self.assertAlmostEqual(w.omega,after.omega,places=10)
                for a,b in zip(w.force,force): self.assertAlmostEqual(a,b,places=10)
            count+=1
        self.assertEqual(count,576)

    def test_torque_reaction_identity(self):
        w=Wheel(170.)
        after,force,detail=wheel_response(w,(0.,90.),0.,.3)
        angular_impulse=1.6*(after.omega-w.omega)
        self.assertAlmostEqual(angular_impulse,1.6*(detail['omega_braked']-w.omega)-.02*detail['longitudinal_force']*.54,places=12)

    def test_state_sensitive_brake_and_float32_lock(self):
        def state(extra):return State((0.,95.),tuple(Wheel((95.+extra)/.54) for _ in range(4)),7.30192)
        rolling,_=choose_brake(state(0.),94.2)
        spinning,_=choose_brake(state(12.),94.2)
        self.assertGreater(spinning,rolling)
        self.assertLess(f32(.9),.9)
        with self.assertRaisesRegex(ValueError,'UNREACHABLE'):
            choose_brake(state(0.),0.)


if __name__=='__main__':unittest.main()
