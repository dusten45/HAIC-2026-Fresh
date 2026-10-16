"""Separate predicted-goal ledger; never emits or commits an actual observation."""
from dataclasses import dataclass,replace
import math
from retry.planner419 import GoalLedger,H,PROGRESS_GOAL_M,ContractError
@dataclass(frozen=True)
class ModelPrediction:
 progress_m:float
 raw_clock_tick:int
 official_finished:bool=False
 provenance:str='SOURCE_MODEL'
@dataclass(frozen=True)
class ForecastLedger:
 actual_root_digest:str
 actual_root_goal_m:float
 progress_m:float
 goal_m:float
 age_actions:int
 last_clock_tick:int
 actual_root_goal_reached:bool=False
 deadline_missed:bool=False
 done:bool=False
 @classmethod
 def fork(cls,actual:GoalLedger):
  if actual.done or actual.deadline_missed:raise ContractError('cannot_predict_after_actual_stop')
  return cls(actual.digest(),actual.goal_m,actual.progress_m,actual.goal_m,actual.age_actions,actual.last_clock_tick)
 def advance_prediction(self,predicted:ModelPrediction):
  if predicted.provenance!='SOURCE_MODEL':raise ContractError('separate_predicted_channel_required')
  if self.done or self.deadline_missed:raise ContractError('prediction_after_model_stop')
  if not math.isfinite(predicted.progress_m) or type(predicted.raw_clock_tick) is not int or not 1<=predicted.raw_clock_tick-self.last_clock_tick<=4:raise ContractError('model_clock_or_progress_invalid')
  age=self.age_actions+1;hit=self.actual_root_goal_reached or predicted.progress_m>=self.actual_root_goal_m or predicted.official_finished
  if predicted.official_finished:return replace(self,progress_m=predicted.progress_m,last_clock_tick=predicted.raw_clock_tick,actual_root_goal_reached=hit,done=True)
  if predicted.progress_m>=self.goal_m:return replace(self,progress_m=predicted.progress_m,goal_m=predicted.progress_m+PROGRESS_GOAL_M,age_actions=0,last_clock_tick=predicted.raw_clock_tick,actual_root_goal_reached=hit)
  return replace(self,progress_m=predicted.progress_m,age_actions=age,last_clock_tick=predicted.raw_clock_tick,actual_root_goal_reached=hit,deadline_missed=age>=H)
 def progress_qualified(self):return self.actual_root_goal_reached and not self.deadline_missed
