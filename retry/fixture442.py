"""Recorded-transition stand-ins; fake step copies records, never integrates."""
import copy,json
from pathlib import Path
import numpy as np
from retry.fixture438 import stored_env
from retry.canonical438 import compare
from retry.ledger439 import require
from retry.loss389_analyze import read
from retry.receipt421_io import load_receipt
from retry.planner419 import GoalLedger,H
class RecordedControl442:
 def __init__(self,row):self.row=row;self.state=copy.deepcopy(row['memory_before']);self.act_calls=0
 def memory(self):return copy.deepcopy(self.state)
 def phase(self):return self.state['C']['phase']
 def act(self,env):self.act_calls+=1;require(self.act_calls==1,'FIXTURE_SINGLE_NOMINAL');self.state=copy.deepcopy(self.row['nominal_memory_after']);return np.asarray(self.row['nominal'],np.float32)
class RecordedTrace442:
 def __init__(self,row):self.row=row;self.rows=[];self.hulls=[]
 def reset(self):self.rows=[];self.hulls=[]
 def enable(self):self.rows=copy.deepcopy(self.row['raw_tire_samples']);self.hulls=copy.deepcopy(self.row['raw_hull'])
 def disable(self):pass
class RecordedEnv442:
 def __init__(self,pre,post,row):self.base=stored_env(pre);self.__dict__.update(self.base.__dict__);self.after=post;self.row=row;self.recorded_steps=0;self.obs=np.zeros((4,84,84),np.float32)
 def step(self,command):
  self.recorded_steps+=1;require(self.recorded_steps==1 and np.asarray(command,np.float32).tolist()==self.row['command'],'FIXTURE_SINGLE_RECORDED_TRANSITION');raw=self.unwrapped;tracker=raw.finish_line_tracker;post=self.row['post'];hulls=self.row['raw_hull'];raw._collision_this_step=self.row['collision']
  for i,h in enumerate(hulls):
   nxt=hulls[i+1] if i+1<len(hulls) else None;pos=nxt['origin_position'] if nxt else post['pos'];vel=nxt['COM_linear_velocity'] if nxt else post['vel'];time=nxt['time'] if nxt else post['time'];raw.car.hull.position=pos;raw.car.hull.linearVelocity=vel;raw.t=time;raw.tile_visited_count=post['visited'];tracker.update(tuple(pos),tuple(vel),post['visited']/len(raw.track),time)
  replacement=stored_env(self.after);require(compare(tracker.__dict__,replacement.unwrapped.finish_line_tracker.__dict__)['equal'],'FIXTURE_FINAL_TRACKER');replacement.unwrapped.finish_line_tracker=tracker;self.unwrapped.__dict__.update(replacement.unwrapped.__dict__);self.damage=replacement.damage;self.off_track_counter=replacement.off_track_counter;self.env._elapsed_steps=replacement.env._elapsed_steps
  return self.obs,0.,self.row['ended'],self.row['truncated'],dict(collision=self.row['collision'])

def recorded_case(root,kind):
 if kind=='prefix':
  row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[0]);pre=read(root/'stage423/actual_C0/initial-private.json');post=load_receipt(root/'stage438/actual_C0/step2-before-native-private.json')['full'];frame=read(root/'stage417/source-prefix-private.json')[0]
 elif kind=='first':
  row=json.loads((root/'stage438/actual_C0/trace-private.jsonl').read_text().splitlines()[-1]);pre=read(root/'stage438/actual_C0/fork-private.json');post=read(root/'stage438/actual_C0/final-private.json');frame=load_receipt(root/'stage438/C0_decision1-before-actual-dispatch-private.json')['selected_first']
 else:
  row=json.loads((root/'stage427/actual_P/trace-private.jsonl').read_text().splitlines()[-1]);pre=read(root/'stage425/actual_P/final-private.json');post=read(root/'stage427/actual_P/final-private.json');frame=read(root/'stage427/actual_P/actual_P_177_nominal_1-private.json')['rows'][0]
 ledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-(row['step']-1)),round(row['pre']['time']*50));return RecordedEnv442(pre,post,row),RecordedControl442(row),RecordedTrace442(row),ledger,frame,row
