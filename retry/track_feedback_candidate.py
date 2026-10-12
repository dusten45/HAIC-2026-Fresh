"""One privileged model-feedback candidate; never reads actual future frames.

The source physics and normal candidate filters/rank are unchanged. A frozen
track-following law generates float32 controls from each predicted model state;
the real evaluator executes only the selected, already generated prefix.
"""
import time
import numpy as np

from retry.parameter_agent import SpeedController
from retry.privileged_state import _local_road
from retry.source_vehicle_transition import SourceVehicleTransition


def predict_track_feedback(snapshot, track, nominal, previous_steer, configuration, horizon=12):
    started = time.perf_counter()
    model = SourceVehicleTransition(snapshot)
    reconstruction_wall = time.perf_counter() - started
    restored = dict(tiles=model.initial_tiles_exact, progress=model.initial_progress_exact,
                    bodies=model.initial_bodies_exact)
    points = np.asarray(track, dtype=np.float64)[:, 2:4]
    lengths = np.linalg.norm(np.roll(points, -1, axis=0)-points, axis=1)
    arc = np.r_[0., np.cumsum(lengths)]
    assert np.isfinite(points).all() and np.all(lengths > 1e-6)
    controller = SpeedController(configuration['speed_cap'], configuration['lateral_fast'])
    controller.previous_steer = float(previous_steer)
    occupied = {int(t.idx) for w in model.car.wheels for t in w.tiles}
    initial_indices = sorted({i for tile in occupied for i in ((tile-1) % len(points), tile)}) or list(range(len(points)))
    position = np.asarray(model.car.hull.position)
    cursor = int(initial_indices[int(np.argmin(np.sum((points[initial_indices]-position)**2, axis=1)))])
    initially_visited = {road['idx'] for road in snapshot['roads'] if road['visited']}
    actions, rows, diagnostics = [], [], []
    control_cpu = control_wall = integration_wall = 0.
    try:
        for _ in range(horizon):
            wall, cpu = time.perf_counter(), time.process_time()
            hull = model.car.hull
            position, velocity = np.asarray(hull.position), np.asarray(hull.linearVelocity)
            heading = float(hull.angle)
            speed = float(np.linalg.norm(velocity))
            delta_arc = (arc[:-1]-arc[cursor]+arc[-1]/2) % arc[-1]-arc[-1]/2
            indices = np.flatnonzero((delta_arc >= -configuration['search_behind_m']) & (delta_arc <= configuration['search_ahead_m']))
            cursor = int(indices[int(np.argmin(np.sum((points[indices]-position)**2, axis=1)))])
            lookahead = float(np.clip(4.+.35*speed, 6., 14.))
            _, _, geometry = _local_road(points, position, (lookahead,), indices)
            target = geometry[0]-position
            right = np.array([np.cos(heading), np.sin(heading)])
            forward = np.array([-np.sin(heading), np.cos(heading)])
            x, y = float(target @ right), float(target @ forward)
            near = any(float((np.asarray(o.position)-position) @ forward) > 0
                       and np.linalg.norm(np.asarray(o.position)-position) <= lookahead+2.6+o.fixtures[0].shape.radius
                       for o in model.obstacles)
            lateral = configuration['lateral_safe'] if near else configuration['lateral_fast']
            controller.lateral_acceleration = lateral
            action = controller.action_target(x, y, speed)
            # Reuse steering and smoothing; use the champion's verified
            # zero-offset curvature speed law instead of the older helper's .003.
            curvature = 2.*x/max(x*x+y*y, 1e-6)
            target_speed = min(configuration['speed_cap'], float(np.sqrt(lateral/max(abs(curvature), 1e-6))))
            action[1:] = [np.clip(.08*(target_speed-speed), 0., .5), np.clip(.04*(speed-target_speed), 0., .5)]
            assert action.dtype == np.float32 and np.isfinite(action).all()
            assert np.all(action >= [-1, 0, 0]) and np.all(action <= [1, 1, 1])
            actions.append(action.tolist())
            diagnostics.append(dict(speed_m_s=speed, target_speed_m_s=target_speed, lookahead_m=lookahead,
                                    near=near, cursor=cursor, target_body=[x,y]))
            control_cpu += time.process_time()-cpu
            control_wall += time.perf_counter()-wall
            wall = time.perf_counter()
            row = model.step(action)
            row['newly_visited_tile_ids'] = sorted(int(t.idx) for t in model.roads if t.road_visited and t.idx not in initially_visited)
            rows.append(row)
            integration_wall += time.perf_counter()-wall
            if row['terminal']:
                break
    finally:
        model.close()
    deviations = [abs(float(a[0])-float(nominal[0])) for a in actions]
    split = horizon//2
    rank_spec = dict(steer_offsets=[float(np.mean(deviations[:split])), float(np.mean(deviations[split:])) if len(deviations)>split else 0.],
                     brake_first_block=any(a[2]>0 for a in actions[:split]))
    return dict(rows=rows, actions=actions, rank_spec=rank_spec, initialization=restored,
        controller_diagnostics=diagnostics, control_CPU_s=control_cpu, control_wall_s=control_wall,
        reconstruction_wall_s=reconstruction_wall, integration_wall_s=integration_wall,
        wall_s=time.perf_counter()-started, model_physics_ticks=model.native_ticks,
        event_initialization=model.initial_event_receipt, zero_time_contact_initializations=1)
