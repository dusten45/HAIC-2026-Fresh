"""Privileged H24 diagnostic: frozen221 prefixes plus one common T tail.

The real execution plan still expires after12 and replans every3. R expires at
its original suffix boundary; forecast-only repeat-last padding is replaced by
T after that boundary. T continues its original feedback law throughout24.
No additional controls or random candidates are introduced.
"""
import time
import numpy as np
from retry import receding_horizon_oracle as rh
from retry.track_feedback_candidate import SpeedController, _local_road, SourceVehicleTransition


def extended_prediction(snapshot, track, nominal, previous_steer, configuration, prefix=None):
    """Single reconstructed source world, fixed prefix then frozen T feedback."""
    started=time.perf_counter();model=SourceVehicleTransition(snapshot)
    reconstruction_wall=time.perf_counter()-started
    restored=dict(tiles=model.initial_tiles_exact,progress=model.initial_progress_exact,bodies=model.initial_bodies_exact)
    points=np.asarray(track,dtype=np.float64)[:,2:4]
    lengths=np.linalg.norm(np.roll(points,-1,axis=0)-points,axis=1);arc=np.r_[0.,np.cumsum(lengths)]
    assert np.isfinite(points).all() and np.all(lengths>1e-6)
    initially_visited={r['idx'] for r in snapshot['roads'] if r['visited']}
    prefix=[] if prefix is None else [np.asarray(a,np.float32).copy() for a in prefix]
    assert len(prefix)<=12
    controller=None;cursor=None;actions=[];rows=[];diagnostics=[];control_cpu=control_wall=integration_wall=0.
    try:
        for i in range(24):
            if i<len(prefix):action=prefix[i].copy()
            else:
                wall,cpu=time.perf_counter(),time.process_time()
                if controller is None:
                    controller=SpeedController(configuration['speed_cap'],configuration['lateral_fast'])
                    controller.previous_steer=float(actions[-1][0]) if actions else float(previous_steer)
                    occupied={int(t.idx) for w in model.car.wheels for t in w.tiles}
                    initial_indices=sorted({j for tile in occupied for j in ((tile-1)%len(points),tile)}) or list(range(len(points)))
                    position=np.asarray(model.car.hull.position)
                    cursor=int(initial_indices[int(np.argmin(np.sum((points[initial_indices]-position)**2,axis=1)))])
                hull=model.car.hull;position,velocity=np.asarray(hull.position),np.asarray(hull.linearVelocity)
                heading=float(hull.angle);speed=float(np.linalg.norm(velocity))
                delta_arc=(arc[:-1]-arc[cursor]+arc[-1]/2)%arc[-1]-arc[-1]/2
                indices=np.flatnonzero((delta_arc>=-configuration['search_behind_m']) & (delta_arc<=configuration['search_ahead_m']))
                cursor=int(indices[int(np.argmin(np.sum((points[indices]-position)**2,axis=1)))])
                lookahead=float(np.clip(4.+.35*speed,6.,14.))
                _,_,geometry=_local_road(points,position,(lookahead,),indices);target=geometry[0]-position
                right=np.array([np.cos(heading),np.sin(heading)]);forward=np.array([-np.sin(heading),np.cos(heading)])
                x,y=float(target@right),float(target@forward)
                near=any(float((np.asarray(o.position)-position)@forward)>0 and np.linalg.norm(np.asarray(o.position)-position)<=lookahead+2.6+o.fixtures[0].shape.radius for o in model.obstacles)
                lateral=configuration['lateral_safe'] if near else configuration['lateral_fast'];controller.lateral_acceleration=lateral
                action=controller.action_target(x,y,speed)
                curvature=2.*x/max(x*x+y*y,1e-6)
                target_speed=min(configuration['speed_cap'],float(np.sqrt(lateral/max(abs(curvature),1e-6))))
                action[1:]=[np.clip(.08*(target_speed-speed),0.,.5),np.clip(.04*(speed-target_speed),0.,.5)]
                diagnostics.append(dict(action=i+1,speed_m_s=speed,target_speed_m_s=target_speed,lookahead_m=lookahead,near=near,cursor=cursor,target_body=[x,y]))
                control_cpu+=time.process_time()-cpu;control_wall+=time.perf_counter()-wall
            assert action.dtype==np.float32 and np.isfinite(action).all()
            assert np.all(action>=[-1,0,0]) and np.all(action<=[1,1,1])
            actions.append(action.tolist());wall=time.perf_counter();row=model.step(action)
            row['newly_visited_tile_ids']=sorted(int(t.idx) for t in model.roads if t.road_visited and t.idx not in initially_visited)
            rows.append(row);integration_wall+=time.perf_counter()-wall
            if row['terminal']:break
    finally:model.close()
    return dict(rows=rows,actions=actions,initialization=restored,event_initialization=model.initial_event_receipt,
        reconstruction_wall_s=reconstruction_wall,integration_wall_s=integration_wall,wall_s=time.perf_counter()-started,
        model_physics_ticks=model.native_ticks,zero_time_contact_initializations=1,control_CPU_s=control_cpu,control_wall_s=control_wall,
        controller_diagnostics=diagnostics,fixed_prefix_actions=len(prefix),feedback_tail_starts_at=len(prefix)+1)


def forecast_pool(snapshot,nominal,oracle,step,previous_plan,track,previous_steer,record_road_visits=False):
    assert oracle['horizon_actions']==12 and oracle['evaluation_horizon_actions']==24
    assert oracle['replan_interval_actions']==3 and len(oracle['specifications'])==9 and len(oracle['fixed_shooting_actions'])==32
    specs=dict(oracle['specifications']);actions={n:rh.controls(nominal,s) for n,s in specs.items()}
    actions['N']=[nominal.copy() for _ in range(12)]
    specs['N']=dict(steer_offsets=[0.,0.],brake_first_block=bool(nominal[2]>0))
    retained=rh.retained_candidate(previous_plan,step,nominal,12)
    if retained is not None:
        actions['R']=retained['actions'][:retained['remaining_actions']]
        specs['R']=retained['rank_spec']
        assert retained['expires_before']==retained['origin_step']+12
    for name,frozen in oracle['fixed_shooting_actions'].items():
        array=np.asarray(frozen,np.float32);assert array.shape==(12,3)
        actions[name]=[row.copy() for row in array]
        specs[name]=dict(steer_offsets=[float(np.mean(np.abs(block[:,0]-float(nominal[0])))) for block in (array[:6],array[6:])],brake_first_block=bool(np.any(array[:6,2]>0)))
    candidates={n:extended_prediction(snapshot,track,nominal,previous_steer,oracle['track_feedback'],a) for n,a in actions.items()}
    for n,a in actions.items():
        observed=candidates[n]['actions'][:len(a)]
        assert np.array_equal(np.asarray(observed,np.float32),np.asarray(a[:len(observed)],np.float32))
    t=extended_prediction(snapshot,track,nominal,previous_steer,oracle['track_feedback'])
    deviations=[abs(float(a[0])-float(nominal[0])) for a in t['actions'][:12]]
    specs['T']=dict(steer_offsets=[float(np.mean(deviations[:6])),float(np.mean(deviations[6:])) if len(deviations)>6 else 0.],brake_first_block=any(a[2]>0 for a in t['actions'][:6]))
    candidates['T']=t;actions['T']=[np.asarray(a,np.float32) for a in t['actions'][:12]]
    # The executor sees only original-length plans, never the hypothetical tail.
    return dict(candidates=candidates,model_physics_ticks=sum(q['model_physics_ticks'] for q in candidates.values())),specs,retained,actions
