"""Only80->100 curvature speed-budget change;515 path/tracker/pedals unchanged."""
import copy,math
from retry.corner515_control import make_path,nominal,steering,project,reference,future_floor
from retry.plan512_control import tick


def path_for(static,budget):
    if budget not in (80.,100.):raise ValueError('UNREGISTERED_BUDGET')
    root=static['root'];path=make_path(static['boundary'],tuple(root['center']),static['obstacles'])
    original=list(path['speeds'])
    speed=[min(80.,math.sqrt(budget/max(abs(k),1e-8))) for k in path['curvature']];speed[0]=0.
    for i in range(len(speed)-2,-1,-1):speed[i]=min(speed[i],math.sqrt(speed[i+1]**2+2*45.*(path['arcs'][i+1]-path['arcs'][i])))
    for i in range(1,len(speed)):speed[i]=min(speed[i],math.sqrt(speed[i-1]**2+2*25.*(path['arcs'][i]-path['arcs'][i-1])))
    if budget==80. and original!=speed:raise ValueError('BASELINE515_SPEED_PROFILE_CHANGED')
    path['speeds']=speed;return path


def force_rows(root,action):
    from retry.brake502_response import wheel_response,STIFFNESS,RADIUS
    result=[]
    for i,w in enumerate(root.planar.linear.wheels):
        g=w.gas+min(.1,float(action[1])-w.gas) if i>=2 else w.gas
        after,force,d=wheel_response(w,root.planar.linear.velocity,g,float(action[2]),root.planar.linear.engine_multiplier)
        forward=(-math.sin(w.heading),math.cos(w.heading));side=(forward[1],-forward[0]);v=tuple(root.planar.linear.velocity[j]+w.offset[j] for j in range(2));vf=sum(forward[j]*v[j] for j in range(2));vs=sum(side[j]*v[j] for j in range(2))
        ratio=math.hypot(STIFFNESS*(d['omega_braked']*RADIUS-vf),STIFFNESS*vs)/w.friction
        result.append(dict(wheel=i,ratio=ratio,clipped=ratio>1.,vector=list(force)))
    return result


def forecast(root,action,index,counter):
    from dataclasses import replace,asdict
    root=replace(root,planar=replace(root.planar,steer=-float(action[0])));rows=[]
    for _ in range(4):
        used=root.current_contacts;root=tick(root,float(action[1]),float(action[2]),index,counter)
        rows.append(dict(contacts_used=used,velocity=root.planar.linear.velocity,position=root.center,angle=root.planar.angle,yaw=root.planar.yaw))
    return root,rows
