import copy,itertools,math,unittest
from types import SimpleNamespace as NS
import numpy as np
import gymnasium as gym
from env_wrapper import CarEnvironment
from damage import calculate_damage_effects
from retry.brake509_adapter import context,brake_action,act_once,native_caps
from retry.test_brake502_response import source_car_class,FakeWheel
from retry.brake502_response import wheel_response,Wheel
from retry.pixel_agent import PixelAgent


class Road:
    def __init__(self,mu=1.):
        self.road_friction=mu
        self.fixtures=[NS(shape=NS(vertices=[(-20.,-20.),(20.,-20.),(20.,100.),(-20.,100.)]))]
    def GetWorldPoint(self,v):return v


class Body:
    def __init__(self,mass,position,local=(0.,0.)):
        self.mass=mass;self.worldCenter=position;self.position=(position[0]-local[0],position[1]-local[1]);self.localCenter=local
        self.inertia=mass*(1.+sum(x*x for x in local));self.linearVelocity=(0.,60.);self.angle=0.;self.angularVelocity=0.


class Car:
    def __init__(self,grip=1.,grass=.6,road_mu=1.):
        self.grip_multiplier=grip;self.engine_multiplier=.9;self.steering_multiplier=.85;self.grass_friction_multiplier=grass
        self.hull=Body(7.,(0.,.2),(0.,.2));self.road=Road(road_mu);self.wheels=[]
        for x,y in ((-1.1,1.6),(1.1,1.6),(-1.1,-1.64),(1.1,-1.64)):
            w=Body(.075,(x,y));w.omega=60/.54;w.gas=0.;w.wheel_rad=.54;w.tiles={self.road};self.wheels.append(w)


class FakeRaw(gym.Env):
    def __init__(self):
        self.observation_space=gym.spaces.Box(0,255,(96,96,3),dtype=np.uint8)
        self.action_space=gym.spaces.Box(np.array([-1.,0.,0.]),np.ones(3),dtype=np.float32)
        self.raw_calls=0;self.reset_calls=0;self.effects=(1.,1.,1.);self.seen=[];self.track=[None]*10;self.tile_visited_count=0
        self.car=NS(set_damage_effects=self.set_effects)
    def set_effects(self,*values):self.effects=values
    def reset(self,**kwargs):
        self.reset_calls+=1;self.raw_calls+=1
        return np.zeros((96,96,3),np.uint8),{}
    def step(self,action):
        self.raw_calls+=1;self.seen.append((self.raw_calls,self.effects,np.asarray(action).copy()))
        return np.zeros((96,96,3),np.uint8),0.,False,False,dict(collision=self.raw_calls==52)


class AdapterTests(unittest.TestCase):
    def test_full_native_reservation_and_reset_warmup(self):
        c=native_caps();self.assertEqual(c['actions'],64);self.assertEqual(c['total_raw_ticks'],358);self.assertEqual(c['remaining_if_full'],25963)
        raw=FakeRaw();env=CarEnvironment(raw);obs,_=env.reset()
        self.assertEqual((raw.reset_calls,raw.raw_calls),(1,51));self.assertEqual(obs.shape,(4,84,84));self.assertEqual(obs.dtype,np.float32)
        action=np.array([.1,0.,.2],np.float32);env.step(action)
        self.assertEqual(raw.raw_calls,55)
        self.assertTrue(all(e==(1.,1.,1.) for n,e,a in raw.seen if n>=52))
        self.assertEqual(raw.effects,(.9,.95,.95))
        self.assertTrue(all(np.array_equal(a,action.astype(np.float64)) for n,e,a in raw.seen if n>=52))
    def test_com_frame_sign_and_effect_normalization(self):
        car=Car(.7,.6,1.2);n=np.array([.125,0.,.02],np.float32);root=context(car,[car.road],n)
        expected=sum(b.mass*b.worldCenter[1] for b in [car.hull,*car.wheels])/7.3
        self.assertAlmostEqual(root.center[1],expected)
        self.assertNotEqual(root.center,car.hull.position)
        self.assertEqual(root.planar.steer,-float(n[0]));self.assertEqual(root.floor,168.)
        self.assertAlmostEqual(root.roads[0][1],.84)
        self.assertAlmostEqual(root.planar.linear.wheels[0].friction,336.)
        self.assertEqual(root.planar.linear.engine_multiplier,.9);self.assertEqual(root.planar.steering_multiplier,.85)
        original=root.center;car.hull.position=(999.,999.)
        self.assertEqual(context(car,[car.road],n).center,original)
    def test_grass_floor_precedes_grip_and_current_contacts(self):
        for grip,grass,mu in itertools.product((.6,1.),(.35,.6),(.4,1.2)):
            car=Car(grip,grass,mu);root=context(car,[car.road],[0.,0.,.02])
            self.assertAlmostEqual(root.planar.linear.wheels[0].friction,400*max(grass,mu)*grip)
            for w in car.wheels:w.tiles=set()
            root=context(car,[car.road],[0.,0.,.02]);self.assertEqual(root.current_contacts,((),)*4)
            self.assertAlmostEqual(root.planar.linear.wheels[0].friction,400*grass*grip)
    def test_single_nominal_memory_commit_and_gas_steer_passthrough(self):
        class Reference:
            def __init__(self,action):self.calls=0;self.action=action
            def act(self,observation):self.calls+=1;return self.action
        car=Car();n=np.array([.001,0.,.02],np.float32);ref=Reference(n)
        output,details=act_once(ref,None,car,[car.road])
        self.assertEqual(ref.calls,1);self.assertEqual(output.dtype,np.float32);self.assertTrue(np.array_equal(output[:2],n[:2]))
        self.assertEqual(details['mode'],'BRAKE_RESPONSE_ONLY');self.assertLessEqual(details['predicted_end_speed'],details['target_speed'])
        n=np.array([.123,.35,0.],np.float32);ref=Reference(n);output,details=act_once(ref,None,None,None)
        self.assertEqual(ref.calls,1);self.assertTrue(np.array_equal(output,n));self.assertFalse(details['prediction_claim'])
    def test_unsupported_inputs_stop_without_reference_replay(self):
        car=Car()
        for command in ([0.,.1,.1],[0.,0.,1.]):
            with self.assertRaises(ValueError):brake_action(command,car,[car.road])
        with self.assertRaisesRegex(ValueError,'SKIP'):context(car,[car.road],[0.,0.,.1],skip_frames=3)
    def test_public_pixel_reference_single_call_on_synthetic_observation(self):
        class Counted(PixelAgent):
            def __init__(self):super().__init__(adaptive=True);self.calls=0
            def act(self,observation):self.calls+=1;return super().act(observation)
        image=np.zeros((4,84,84),np.float32);image[:,:,30:55]=.4;image[:,74:82,10:13]=1.
        car=Car();reference=Counted();reference.reset(image)
        action,details=act_once(reference,image,car,[car.road])
        self.assertEqual(reference.calls,1);self.assertEqual(details['mode'],'BRAKE_RESPONSE_ONLY')
        self.assertEqual(float(action[1]),0.)
    def test_effects_against_actual_source_force_and_steering(self):
        Source=source_car_class();count=0
        for grip,grass,road,engine,steering in itertools.product((.6,1.),(.35,.6),(.4,1.2),(.8,1.),(.8,1.)):
            car=Source();car.grip_multiplier=grip;car.grass_friction_multiplier=grass;car.engine_multiplier=engine;car.steering_multiplier=steering;car.fuel_spent=0.
            car.wheels=[FakeWheel(100.,0.,(4.,60.),.1,400*road) for _ in range(4)]
            for w in car.wheels:w.steer=.2;w.joint.angle=0.
            car.gas(.8);car.brake(.2);expected=[]
            for w in car.wheels:
                expected.append(wheel_response(Wheel(w.omega,heading=.1,friction=400*max(grass,road)*grip),(4.,60.),w.gas,.2,engine))
            car.step(.02)
            for w,(after,force,_) in zip(car.wheels,expected):
                self.assertAlmostEqual(w.omega,after.omega,places=10)
                self.assertAlmostEqual(w.joint.motorSpeed,3.*steering)
                for a,b in zip(w.force,force):self.assertAlmostEqual(a,b,places=10)
            count+=1
        self.assertEqual(count,32)


if __name__=='__main__':unittest.main()
