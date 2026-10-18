"""Fixed small physical-goal probe, not a PixelAgent performance change."""
import math
import numpy as np
from retry.pixel_agent import PixelAgent
from retry.brake509_adapter import context
from retry.brake508_corridor import choose,bounds

PREFIX=24
MAX_ACTIONS=40
DROP=2.
MAX_DECEL=10.
TOL=.10


def caps():
    return dict(worlds=2,resets=2,actions=2*40,prefix_actions=2*24,braking_actions_reserved=2*(40-24),reset_raw_ticks=2*51,action_raw_ticks=2*40*4,total_raw_ticks=422)


def boundary(speed,goal):
    if not math.isfinite(speed) or not math.isfinite(goal):raise ValueError('NONFINITE_GOAL_STATE')
    if speed>goal+TOL:return 'RUN'
    if speed<goal-TOL:return 'EXCESS_BRAKING'
    return 'GOAL_BAND'


def request(speed,goal):
    if goal<=0 or speed<=goal:raise ValueError('INVALID_ACTIVE_GOAL')
    target=max(goal,speed-.08*MAX_DECEL)
    return target,(speed-target)/.08


class Reference:
    """24 pixel-reference actions, then same cached steer and zero gas.

    One act call advances reference memory once. Physical speed control remains
    outside this pixel steering reference and is identical in both arms.
    """
    def __init__(self):self.pixel=PixelAgent(adaptive=True);self.calls=0;self.last_steer=0.
    def reset(self,observation):self.pixel.reset(observation);self.calls=0;self.last_steer=0.
    def act(self,observation):
        self.calls+=1
        if self.calls<=PREFIX:
            action=self.pixel.act(observation);self.last_steer=float(action[0]);return action
        return np.array([self.last_steer,0.,0.],np.float32)


def command(reference_action,car,road,goal,arm,skin):
    root=context(car,road,reference_action,skin=skin)
    speed=math.hypot(*root.planar.linear.velocity);target,deceleration=request(speed,goal)
    mass=root.planar.linear.mass+4*1.6/.54**2
    nominal=np.asarray(reference_action,np.float32).copy();nominal[1]=0.
    nominal[2]=mass*deceleration/(4*1.6*15/(.02*.54))
    action=nominal.copy()
    if arm=='response':action[2]=choose(root,target,bounds(root.roads))[0]
    elif arm!='steady':raise ValueError('ARM')
    return action,root,dict(global_goal=goal,requested_end_speed=target,requested_deceleration=deceleration,steady_brake=float(nominal[2]))
