"""Privileged rear-wheel traction allocation: source first-tick inverse, no world rollout."""
import math
import numpy as np
from core.vendor.car_dynamics import SIZE,ENGINE_POWER,WHEEL_MOMENT_OF_INERTIA,FRICTION_LIMIT

def control(base,car):
 action=np.array(base,np.float32);brake=float(action[2]);requested=float(action[1]);dt=.02;C=205000*SIZE*SIZE;wheelrows=[]
 if brake>=.9:return action,dict(applied=False,reason='Full wheel lock brake makes firsttick gas ineffective')
 caps=[]
 for w in car.wheels[2:]:
  forward=w.GetWorldVector((0,1));side=w.GetWorldVector((1,0));vel=w.linearVelocity;vf=float(forward[0]*vel[0]+forward[1]*vel[1]);vs=float(side[0]*vel[0]+side[1]*vel[1]);omega=float(w.omega);radius=float(w.wheel_rad)
  limit=FRICTION_LIMIT*car.grass_friction_multiplier
  for tile in w.tiles:limit=max(limit,FRICTION_LIMIT*tile.road_friction)
  limit*=car.grip_multiplier;latforce=-vs*C;remaining=math.sqrt(max(limit*limit-latforce*latforce,0.));desired_omega=(vf+remaining/C)/radius
  # For forward omega, source brake subtracts15*b, clipping at0. Negative/reverse
  # or nonfinite states retain240 rather than applying this forward inversion.
  if not all(math.isfinite(v) for v in [vf,vs,omega,radius,limit,car.engine_multiplier]) or vf<0 or omega<0 or radius<=0:return np.array(base,np.float32),dict(applied=False,reason='Invalid/reverse wheel state')
  cap=(desired_omega+15*brake-omega)*WHEEL_MOMENT_OF_INERTIA*(abs(omega)+5)/(dt*ENGINE_POWER*car.engine_multiplier)
  cap=float(np.clip(cap,0,requested));caps.append(cap)
  def first_force(gas):
   effective=float(w.gas)+min(gas-float(w.gas),.1);om=omega+dt*ENGINE_POWER*car.engine_multiplier*effective/WHEEL_MOMENT_OF_INERTIA/(abs(omega)+5);om=max(0.,om-15*brake);return (om*radius-vf)*C
  wheelrows.append(dict(vf=vf,vs=vs,omega=omega,gas_before=float(w.gas),friction_limit=limit,lateral_force=latforce,longitudinal_budget=remaining,gas_cap=cap,baseline_first_tick_long_force=first_force(requested)))
 gas=min([requested]+caps);action[1]=np.float32(gas)
 for row,w in zip(wheelrows,car.wheels[2:]):
  effective=float(w.gas)+min(float(action[1])-float(w.gas),.1);om=row['omega']+dt*ENGINE_POWER*car.engine_multiplier*effective/WHEEL_MOMENT_OF_INERTIA/(abs(row['omega'])+5);om=max(0.,om-15*brake);row['returned_first_tick_long_force']=(om*float(w.wheel_rad)-row['vf'])*C
 return action,dict(applied=True,gas_changed=bool(action[1]!=base[1]),rear=wheelrows)
