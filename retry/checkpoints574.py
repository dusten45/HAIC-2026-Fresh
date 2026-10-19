"""Exact stored-trajectory checkpoint reconstruction; no source integration."""
import math
from dataclasses import replace,asdict
from retry.durable568 import digest
import retry.handoff562_model as d

START=136;END=662;FIRST=35;LAST=166;HORIZON=526

def clone(state):
    return dict(root=state['root'],visited=set(state['visited']),tracker=d.FinishLineTracker(**asdict(state['tracker'])),elapsed=state['elapsed'],global_raw=state['global_raw'],progress=state['progress'],launch=list(state['launch']),tracking=list(state['tracking']))

def same(a,b):return d.canonical(a)==d.canonical(b)

def checkpoint_map(owner,rows,expected_final=None):
    state=d.Study.initial(owner);points={};checks=0
    for expected,row in enumerate(rows,1):
        if state['global_raw']>=START and state['global_raw']%4==0 and state['global_raw']<=660:
            points[state['global_raw']//4+1]=clone(state)
        index,raw=divmod(expected-1,4);index+=1;raw+=1
        assert row['index']==index and row['raw']==raw and row['global_raw_before']==expected-1 and row['global_raw_after']==expected
        assert state['elapsed']==row['episode_before_s'];assert state['launch']==row['launch_history_before'] and state['tracking']==row['tracking_history_before']
        action=row['action'];before=replace(state['root'],planar=replace(state['root'].planar,steer=-float(action[0])))
        assert same(d.short(before),row['before_root_without_roads'])
        group='launch' if index<=24 else 'tracking';forces=row['forces'];assert len(forces)==4 and all(math.isfinite(f['ratio']) and bool(f['clipped'])==(f['ratio']>1.) for f in forces)
        history=[state[group][0]+sum(f['ratio']>1. for f in forces),state[group][1]+4];assert history==row['proposed_history']
        after=d.load_root(dict(row['root_without_roads'],roads=owner.static['root']['roads']));q=d.project(after.center,owner.paths['candidate'],state['progress']);assert q['s']==row['progress'] and q['distance']==row['path_error']
        state.update(root=after,progress=q['s'],global_raw=expected,elapsed=state['elapsed']+.02);state[group]=history
        for ids in after.current_contacts:state['visited'].update(ids)
        assert len(state['visited'])==row['visited_count']
        pose,velocity=d.hull_pose(after);state['tracker'].update(pose,velocity,len(state['visited'])/len(owner.static['track']),1.02+state['elapsed'])
        assert same(asdict(state['tracker']),row['tracker']) and state['elapsed']==row['episode_after_s'];checks+=1
    if expected_final is not None:assert same(d.Study.checkpoint(owner,state),expected_final)
    assert sorted(points)==list(range(FIRST,LAST+1))
    assert points[FIRST]['global_raw']==136 and points[LAST]['global_raw']==660
    return points,dict(rows_checked=checks,prehold_checkpoints=len(points),all_root_tracker_clock_history_visited_exact=True,first_tracking=points[FIRST]['tracking'],first_launch=points[FIRST]['launch'],checkpoint_sha256={str(h):digest(d.Study.checkpoint(owner,s)) for h,s in points.items()})

def fd_ticks():return 2*sum(END-4*(h-1) for h in range(FIRST,LAST+1))
