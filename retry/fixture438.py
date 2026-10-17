"""Read-only Python stand-ins for saved437 capture; no Box2D/environment ctor."""
import copy
from types import SimpleNamespace
import numpy as np
from core.finish_line import FinishLineTracker
from retry.actual437_boundary import live_proxy
from retry.terminal410_model import snapshot,from_actual_full
from retry.fork394_run import complete_state
from retry.canonical438 import require_equal
from retry.pedal331_run import rng
class Record:
 def __init__(self,**values):self.__dict__.update(values)
def body(spec):
 return Record(position=copy.deepcopy(spec['position']),angle=spec['angle'],linearVelocity=copy.deepcopy(spec['velocity']),angularVelocity=spec['angular_velocity'],**spec['flags'])
def fixture(spec):
 shape=Record(radius=spec['radius'],**copy.deepcopy(spec['geometry']));return Record(shape=shape,density=spec['density'],friction=spec['friction'],restitution=spec['restitution'],sensor=spec['sensor'],filterData=Record(**{k:spec[k] for k in ['categoryBits','maskBits','groupIndex']}))
def stored_env(full):
 p=full['physical'];assert not p['touching_obstacle_contacts'],'Fixture supports the observed contact-free437 boundary only';roads=[]
 for s in p['roads']:
  r=body(s['body']);r.fixtures=[fixture(s['fixture'])];r.idx=s['idx'];r.road_visited=s['visited'];r.road_friction=s['friction'];r.userData=r;roads.append(r)
 by_id={r.idx:r for r in roads};obstacles=[]
 for s in p['obstacles']:
  o=body(s['body']);o.fixtures=[fixture(s['fixture'])];o.userData=Record(hit=s['hit']);obstacles.append(o)
 wheels=[]
 for s in p['wheels']:
  w=body(s['body']);w.tiles={by_id[i] for i in s['tiles']};w.__dict__.update(s['dynamics']);j=s['joint'];w.joint=Record(angle=j['angle'],GetReferenceAngle=lambda v=j['reference_angle']:v,motorSpeed=j['motorSpeed'],GetMaxMotorTorque=lambda v=j['maxMotorTorque']:v,limits=j['limits'],motorEnabled=j['motorEnabled'],limitEnabled=j['limitEnabled']);wheels.append(w)
 world=Record(bodies=[None]*(len(roads)+len(obstacles)+5),contacts=[],contactCount=p['source_world_contacts'],**p['world_flags']);car=Record(hull=body(p['hull']),wheels=wheels,grass_friction_multiplier=p['grass_friction_multiplier']);t=copy.deepcopy(full['wrapper']['finish_tracker']);t['center']=tuple(t['center']);t['forward']=tuple(t['forward']);tracker=FinishLineTracker(**t)
 raw=Record(car=car,world=world,road=roads,obstacles=obstacles,track=[None]*p['road_count'],tile_visited_count=p['unique_tiles'],t=p['actual_time'],finish_line_tracker=tracker,finish_time_s=full['wrapper']['finish_time_s'],finish_qualified_time_s=full['wrapper']['finish_qualified_time_s'],np_random=Record(bit_generator=Record(state=copy.deepcopy(full['RNG']['environment']))))
 return Record(unwrapped=raw,damage=Record(damage=p['damage']),off_track_counter=p['off_track_counter'],env=Record(_elapsed_steps=full['wrapper']['elapsed_raw_steps']))

def adapter_values(env,obs,ctrl):
 # Same production live_proxy -> snapshot -> capture and complete_state path.
 full=complete_state(env,obs,ctrl.memory());proxy=live_proxy(env);left=dict(snapshot=snapshot(proxy),memory=ctrl.memory(),RNG=rng(env));right=dict(snapshot=from_actual_full(full),memory=full['controller'],RNG=full['RNG']);return proxy,full,left,right

def check_adapter(env,obs,ctrl,directory,label):
 proxy,full,left,right=adapter_values(env,obs,ctrl);proof=require_equal(left,right,directory,label);return proxy,full,proof
