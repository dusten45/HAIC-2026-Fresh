"""One privileged straight approach: scalar stopping envelope vs response distance."""
from dataclasses import replace
import math
import numpy as np
from retry.brake504_planar import step
from retry.brake508_corridor import bounds,indexed_contacts
from retry.brake506_geometry import rectangle
from retry.envelope500 import solve,command as scalar_pedals

DT=.02
GOAL=30.
BRAKE=float(np.float32(.3))
TARGET=GOAL-.15
MAX_MODEL_TICKS=200000


def axis_plan(track,initial):
    points=[(x,y) for _,beta,x,y in track]
    i=min(range(len(points)),key=lambda k:math.dist(points[k],initial))
    start=points[i];following=points[(i+1)%len(points)]
    length=math.dist(start,following);axis=tuple((following[j]-start[j])/length for j in range(2))
    for k in range(2,len(points)//2):
        a,b,c=(points[(i+k+z)%len(points)] for z in (-1,0,1))
        u=tuple(b[j]-a[j] for j in range(2));v=tuple(c[j]-b[j] for j in range(2))
        turn=math.atan2(u[0]*v[1]-u[1]*v[0],sum(x*y for x,y in zip(u,v)))
        if abs(turn)>.08:
            gate=sum((a[j]-start[j])*axis[j] for j in range(2))
            if gate<50 or any(abs((p[0]-start[0])*axis[1]-(p[1]-start[1])*axis[0])>.02 for p in [points[(i+t)%len(points)] for t in range(k)]):
                raise ValueError('NO_VALID_STRAIGHT_APPROACH')
            return dict(start=start,axis=axis,gate=gate,goal=GOAL,corner_turn=turn,derivation='last straight station before first abs heading change >0.08rad')
    raise ValueError('NO_FIRST_CORNER')


def station(position,plan):return sum((position[j]-plan['start'][j])*plan['axis'][j] for j in range(2))


def tick(root,gas,brake,index,counter):
    counter[0]+=1
    if counter[0]>MAX_MODEL_TICKS:raise RuntimeError('MODEL_TICK_CAP')
    p=root.planar
    memberships=tuple(indexed_contacts(rectangle(tuple(root.center[j]+r[j] for j in range(2)),w.heading),root.roads,index,root.skin) for r,w in zip(p.levers,p.linear.wheels))
    gases=tuple((w.gas+min(.1,gas-w.gas) if i>=2 else w.gas) for i,w in enumerate(p.linear.wheels))
    # Apply the exact source engine update before the existing brake/force step.
    # The existing step uses gas0, so drive is applied once, then gas memory restored.
    driven=tuple(replace(w,omega=w.omega+DT*40000*p.linear.engine_multiplier*g/1.6/(abs(w.omega)+5.)) for w,g in zip(p.linear.wheels,gases))
    p=step(replace(p,linear=replace(p.linear,wheels=driven)),brake)
    wheels=tuple(replace(w,gas=g,friction=max([root.floor,*[400*root.roads[i][1] for i in ids]])) for w,g,ids in zip(p.linear.wheels,gases,memberships))
    return replace(root,planar=replace(p,linear=replace(p.linear,wheels=wheels)),center=tuple(root.center[j]+DT*p.linear.velocity[j] for j in range(2)),current_contacts=memberships)


def hold(root,action,index,counter):
    rows=[]
    for _ in range(4):
        used=root.current_contacts;root=tick(root,float(action[1]),float(action[2]),index,counter)
        rows.append(dict(contacts_used=used,velocity_after=root.planar.linear.velocity,position_after=root.center))
    return root,rows


def pedal(u,steer):return np.array([steer,max(0.,u),max(0.,-u)*BRAKE],np.float32)


def braking_arrival(root,action,plan,index,counter):
    previous=root
    for i in range(104):
        if i==4 and math.hypot(*root.planar.linear.velocity)<=TARGET:
            return station(root.center,plan),i,None
        gas,brake=(float(action[1]),float(action[2])) if i<4 else (0.,BRAKE)
        root=tick(root,gas,brake,index,counter)
        old,new=station(previous.center,plan),station(root.center,plan)
        if new<=old:raise ValueError('PREDICTED_REVERSE')
        speed=math.hypot(*root.planar.linear.velocity)
        if old<plan['gate']<=new:
            v0=math.hypot(*previous.planar.linear.velocity);f=(plan['gate']-old)/(new-old)
            crossing=v0+f*(speed-v0)
            return plan['gate']+(crossing-TARGET),i+1,crossing
        if i>=4 and speed<=TARGET:
            v0=math.hypot(*previous.planar.linear.velocity);f=(v0-TARGET)/(v0-speed) if v0>speed else 1.
            return old+f*(new-old),i+1,None
        previous=root
    raise ValueError('BRAKE_HORIZON_EXHAUSTED')


def response_action(root,steer,plan,counter):
    index=bounds(root.roads);probes=[]
    def feasible(u):
        action=pedal(u,steer);stop,ticks,cross=braking_arrival(root,action,plan,index,counter)
        ok=(cross<=TARGET if cross is not None else stop<=plan['gate'])
        probes.append(dict(u=u,feasible=ok,stop_station=stop,model_ticks=ticks))
        return ok
    if feasible(1.):chosen=1.
    else:
        samples=[1.-i/4 for i in range(1,9)]
        # Descending coarse search; only first feasible bracket, no global claim.
        high=1.;low=None
        for u in samples:
            if feasible(u):low=u;break
            high=u
        if low is None:raise ValueError('RESPONSE_STOPPING_SET_EMPTY')
        for _ in range(18):
            middle=(low+high)/2
            if feasible(middle):low=middle
            else:high=middle
        chosen=low
    action=pedal(chosen,steer)
    # Float32 command must itself pass; arithmetic search cannot certify rounding.
    stop,nt,cross=braking_arrival(root,action,plan,index,counter)
    if not (cross<=TARGET if cross is not None else stop<=plan['gate']):raise ValueError('FLOAT32_PLAN_UNCERTIFIED')
    return action,dict(mode='RESPONSE_STOPPING_DISTANCE',probes=probes,stop_station=stop)


def scalar_action(root,steer,plan):
    s=station(root.center,plan);v=math.hypot(*root.planar.linear.velocity);sigma=sum(root.planar.linear.velocity[j]*plan['axis'][j] for j in range(2))
    # Same fixed speed reserve for both plans, as a target-node reduction.
    solution,c=solve(s,v,sigma,[0.,plan['gate']],[0.,TARGET])
    mapped=scalar_pedals(solution,c,steer)
    action=np.array(mapped['action'],np.float32)
    if action[2]>BRAKE:raise ValueError('SCALAR_PEDAL_CAP')
    return action,dict(mode='SCALAR_CONSTANT_DECEL',accel=solution['accel'],predicted_end_speed=v+.08*solution['accel'])
