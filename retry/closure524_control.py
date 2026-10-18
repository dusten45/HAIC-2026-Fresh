"""One model correction: wheel velocity closure uses pre-position-step levers.

Geometry/pose still advances normally. No future actual state, gains or tuning.
This retains the rigid approximation; it does not emulate the full Box2D solver.
"""
from dataclasses import replace
from retry.plan512_control import tick as original_tick


def tick(root,gas,brake,index,counter):
    after=original_tick(root,gas,brake,index,counter)
    yaw=after.planar.yaw
    wheels=tuple(replace(w,offset=(-yaw*r[1],yaw*r[0])) for w,r in zip(after.planar.linear.wheels,root.planar.levers))
    return replace(after,planar=replace(after.planar,linear=replace(after.planar.linear,wheels=wheels)))
