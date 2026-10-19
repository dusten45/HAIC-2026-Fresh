"""Deterministic beam mechanics. Pure operations; no source integration."""
import math
from dataclasses import fields,is_dataclass,asdict
import numpy as np
from retry.durable568 import digest
from retry.checkpoints574 import clone
from retry.lap518_control import point_at
from retry.drive519_control import project


def immutable(value):
    if value is None or isinstance(value,(str,bool,int,float)):return
    if isinstance(value,tuple):
        for x in value:immutable(x)
    elif is_dataclass(value) and value.__dataclass_params__.frozen:
        for f in fields(value):immutable(getattr(value,f.name))
    else:raise RuntimeError('MUTABLE_ROOT_SUBTREE:'+type(value).__name__)


def actions(state,path,factual):
    root=state['root'];q=project(root.center,path,state['progress']);s=q['s']+max(7.,.3*math.hypot(*root.planar.linear.velocity));p=point_at(s,path)
    u=s%path['length'];j=next((i for i in range(len(path['ds'])) if path['arcs'][i+1]>=u),len(path['ds'])-1);v=np.asarray(path['points'][(j+1)%len(path['points'])])-path['points'][j];v=v/np.linalg.norm(v);normal=(-v[1],v[0]);a=root.planar.angle;out=[];seen={};fact=np.asarray(factual,np.float32).tobytes()
    for offset in [-.75,0.,.75]:
        dx,dy=[p[k]+offset*normal[k]-root.center[k] for k in range(2)];den=dx*dx+dy*dy
        if not den>0 or not math.isfinite(den):raise RuntimeError('CONTROL_DOMAIN_SINGULAR')
        delta=math.atan(6.48*(-math.sin(a)*dy-math.cos(a)*dx)/den);steer=float(np.float32(-max(-.4,min(.4,delta))))
        for gas,brake in [(1.,0.),(0.,0.),(0.,.125),(0.,.25)]:out.append(np.asarray([steer,gas,brake],np.float32))
    out.append(np.asarray(factual,np.float32));unique=[]
    for i,action in enumerate(out):
        key=action.tobytes()
        if key not in seen:seen[key]=i;unique.append(dict(id=i,action=action,factual_action=key==fact))
    assert len(unique)<=13 and sum(x['factual_action'] for x in unique)==1
    return unique


def crossing(row,plane):
    p=np.asarray(plane['center']);n=np.asarray(plane['forward_normal']);before=np.asarray(row['before_root_without_roads']['center']);after=np.asarray(row['root_without_roads']['center']);a=float((before-p)@n);b=float((after-p)@n)
    if not a<0<=b:return None
    fraction=-a/(b-a);v0=np.asarray(row['before_root_without_roads']['planar']['linear']['velocity']);v1=np.asarray(row['root_without_roads']['planar']['linear']['velocity'])
    return dict(before_raw=row['global_raw_before'],after_raw=row['global_raw_after'],before_s=row['episode_before_s'],after_s=row['episode_after_s'],fraction=fraction,COM_speed_m_s=float(np.linalg.norm(v0+fraction*(v1-v0))),eligible=abs(row['progress']-plane['station_m'])<=10. and row['path_error']<=3.)


def passes(hit,stage):
    return bool(hit and hit['eligible'] and stage['baseline_before_raw']-hit['after_raw']>=stage['minimum_raw_gain'] and hit['COM_speed_m_s']>=stage['minimum_interpolated_COM_speed_m_s'])


def terminal_key(node):return (node['crossing']['after_raw'],-node['crossing']['COM_speed_m_s'],tuple(node['ids']))


def rank_key(node,path):
    state=node['state'];q=project(state['root'].center,path,state['progress']);v=state['root'].planar.linear.velocity
    return (-state['progress'],-sum(v[j]*q['tangent'][j] for j in range(2)),tuple(node['ids']))


def isolated(child,others):
    for other in others:
        if child is other:raise RuntimeError('BRANCH_STATE_ALIAS')
        for key in ['visited','tracker','launch','tracking']:
            if child[key] is other[key]:raise RuntimeError('BRANCH_MUTABLE_ALIAS:'+key)
