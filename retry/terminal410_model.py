"""Finish-aware source transition; all raw ticks charged by the external meter.

Preserves the historical source implementation. Adds the actual current finish
tracker, clock, elapsed counter and causal raw-tick terminal checks. No render,
challenge environment, actor, future trajectory, or stored future command input.
"""
import copy,math
from types import SimpleNamespace
import numpy as np
from core.finish_line import FinishLineTracker
from core.vendor.car_racing import FPS,PLAYFIELD
from core.obstacle_contacts import clear_obstacle_hit
from retry.source_vehicle_transition import SourceVehicleTransition,capture,obstacle_contact_pair

class TerminalVehicleTransition(SourceVehicleTransition):
 def __init__(self,state):
  physical=state['physical'];super().__init__(physical);self.t=float(physical['actual_time']);self.finish_line_tracker=FinishLineTracker(**copy.deepcopy(state['finish_tracker']));self.elapsed_raw_steps=state['elapsed_raw_steps'];self.finished=self.finish_line_tracker.finish_time_s is not None;self.terminal=self.finished;self.last_raw_ticks=0
  self.initial_finish_exact=self.finish_line_tracker.__dict__==state['finish_tracker']
 def step(self,action):
  if self.terminal:raise RuntimeError('Action_after_terminal')
  action=np.asarray(action,dtype=np.float64);assert action.shape==(3,) and np.isfinite(action).all();before_tiles=self.tile_visited_count;before=self.native_ticks;collision=False;terminated=truncated=False;self.contacts.clear()
  for _ in range(4):
   self._collision_this_step=False;self.car.steer(-action[0]);self.car.gas(action[1]);self.car.brake(action[2]);self.car.step(1./FPS)
   if self._initial_events_pending:
    for wheel,geometric in zip(self.car.wheels,self._initial_geometric_tiles):wheel.tiles.intersection_update(geometric)
    for pair in self._initial_obstacle_ends:clear_obstacle_hit(self.obstacles[pair[0]])
    self._initial_obstacle_ends.clear()
    for contact,begin in self._initial_contact_events:
     pair=obstacle_contact_pair(contact,self.car,self.obstacles)
     if pair is not None and pair in self._restored_obstacle_contacts:continue
     self.listener._contact(contact,begin)
    self._initial_contact_events.clear();self._initial_events_pending=False
   self.world.Step(1./FPS,180,60);self.native_ticks+=1;self.elapsed_raw_steps+=1;self.t+=1./FPS;collision|=bool(self._collision_this_step);h=self.car.hull
   self.finish_line_tracker.update(tuple(h.position),tuple(h.linearVelocity),self.tile_visited_count/len(self.track),self.t);self.finished=self.finish_line_tracker.finish_time_s is not None;terminated=abs(h.position[0])>PLAYFIELD or abs(h.position[1])>PLAYFIELD;truncated=self.finished or self.elapsed_raw_steps>=8200
   if terminated or truncated:break
  crashed=self.damage.update(collision);self._effects();assert len(self.track)<2500;self.off_track_counter=self.off_track_counter+1 if self.tile_visited_count==before_tiles else 0;terminated=bool(terminated or crashed or self.off_track_counter>100);self.terminal=bool(terminated or truncated);self.last_raw_ticks=self.native_ticks-before;h=self.car.hull
  return dict(position=list(h.position),angle=float(h.angle),velocity=list(h.linearVelocity),angular_velocity=float(h.angularVelocity),speed_m_s=math.hypot(*h.linearVelocity),unique_tiles=self.tile_visited_count,damage=self.damage.damage,off_track_counter=self.off_track_counter,wheel_road_contacts=sum(bool(w.tiles) for w in self.car.wheels),collision=collision,contact_obstacle_ids=sorted(self.contacts),terminal=self.terminal,terminated=terminated,truncated=bool(truncated),finished=self.finished,time=self.t,raw_ticks=self.last_raw_ticks,finish_time_s=self.finish_line_tracker.finish_time_s,qualified_time_s=self.finish_line_tracker.qualified_time_s)

def snapshot(model):
 raw=SimpleNamespace(car=model.car,world=model.world,road=model.roads,obstacles=model.obstacles,track=model.track,tile_visited_count=model.tile_visited_count,t=model.t)
 return dict(physical=capture(SimpleNamespace(unwrapped=raw,damage=model.damage,off_track_counter=model.off_track_counter)),finish_tracker=copy.deepcopy(model.finish_line_tracker.__dict__),elapsed_raw_steps=model.elapsed_raw_steps)

def from_actual_full(full):
 return dict(physical=copy.deepcopy(full['physical']),finish_tracker=copy.deepcopy(full['wrapper']['finish_tracker']),elapsed_raw_steps=full['wrapper']['elapsed_raw_steps'])
