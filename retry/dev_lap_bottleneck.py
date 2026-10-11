"""Saved DEV telemetry arithmetic; never imports a policy or simulator.

World state is a posthoc diagnostic label. Counterfactual targets are immediate
arithmetic on fixed saved inputs, not closed-loop predictions of lap time.
Inputs and per-case outputs may be private; publish only reviewed aggregates.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np


def target_limits(telemetry, cap):
    """Reconstruct archived HazardScheduledAgent + FreshDistanceCap formulas.

    The 28 sentinel inside distance_cap is the same conceptual global ceiling.
    Removing that ceiling removes both code occurrences, keeping hazard limits.
    """
    speed = telemetry["speed_estimate"]
    lookahead = float(np.clip(4 + .35 * speed, 6, 14))
    near = any(y > 0 and math.hypot(x, y) <= lookahead + 2.6 + radius
               for x, y, radius in telemetry["route_obstacle_inputs"])
    x, y = telemetry["controller_target"]
    curvature = 2 * x / max(x*x + y*y, 1e-6)
    fast = math.sqrt(7 / (abs(curvature) + .003))
    curve = math.sqrt((5 if near else 7) / (abs(curvature) + .003))
    raw_distance = min([max(4., math.sqrt(10 * d))
                        for d in cap["radial_clearances"]], default=math.inf)
    limits = {"global": 28., "curvature": curve, "distance": raw_distance}
    target = min(limits.values())
    without = {name: min(v for k, v in limits.items() if k != name)
               for name in limits}
    # A single-site edit of the controller's 28 leaves the distance sentinel.
    without["one_global_code_site"] = min(curve, 28., raw_distance)
    without["near_safe_schedule"] = min(28., fast, raw_distance)
    return dict(near=near, curvature=curvature, requested=curve,
                curve_fast=fast, limits=limits, final=target,
                inherited=min(28., curve), distance=min(28., raw_distance),
                without=without)


def weighted(values, weights):
    values, weights = np.asarray(values, float), np.asarray(weights, float)
    return float(np.dot(values, weights) / weights.sum()) if weights.sum() else None


def distribution(values, weights):
    values, weights = np.asarray(values, float), np.asarray(weights, float)
    selected = weights > 0
    values, weights = values[selected], weights[selected]
    if not len(values):
        return None
    order = np.argsort(values)
    cumulative = np.cumsum(weights[order]) / weights.sum()
    return {"mean": weighted(values, weights), "p10": float(np.interp(.1, cumulative, values[order])),
            "median": float(np.interp(.5, cumulative, values[order])),
            "p90": float(np.interp(.9, cumulative, values[order])),
            "min": float(values.min()), "max": float(values.max())}


def project(points, track):
    """Nearest polyline position in saved geometry, diagnostic use only."""
    origin = np.asarray(track, float)[:, 2:4]
    vector = np.roll(origin, -1, axis=0) - origin
    lengths = np.linalg.norm(vector, axis=1)
    if np.any(lengths <= 0):
        raise ValueError("degenerate saved track segment")
    fraction = np.clip(np.einsum('nsi,si->ns', points[:, None] - origin, vector)
                       / lengths**2, 0., 1.)
    residual = points[:, None] - (origin + fraction[:, :, None] * vector)
    choice = np.argmin(np.sum(residual**2, axis=2), axis=1)
    indices = np.arange(len(points))
    arc = np.r_[0., np.cumsum(lengths)[:-1]][choice] + fraction[indices, choice] * lengths[choice]
    tangent = vector[choice] / lengths[choice, None]
    return arc, tangent, np.linalg.norm(residual[indices, choice], axis=1), float(lengths.sum())


def continuous_runs(mask, dt):
    runs, start = [], None
    for i, active in enumerate(list(mask) + [False]):
        if active and start is None:
            start = i
        if not active and start is not None:
            runs.append((start, i, float(dt[start:i].sum())))
            start = None
    return runs


def analyze_case(spec):
    rows = [json.loads(line) for line in Path(spec["trace"]).read_text().splitlines()]
    scene = json.loads(Path(spec["scene"]).read_text())
    result = json.loads(Path(spec["result"]).read_text())
    if not result["completed"]:
        raise ValueError("this complete-lap analysis requires a saved completed episode")
    n = len(rows)
    before, after = [r["truth_before"] for r in rows], [r["truth_after"] for r in rows]
    t0, t1 = [np.asarray([s["time"] for s in states]) for states in (before, after)]
    finish = rows[-1]["info"]["finish_time_s"]
    duration = finish - t0[0]
    dt = np.maximum(0., np.minimum(t1, finish) - t0)
    assert abs(duration - result["official_lap_ms"] / 1000) < 1e-6
    assert abs(dt.sum() - duration) < 1e-6
    assert np.allclose(t1[:-1], t0[1:], rtol=0., atol=1e-9)
    assert n == result["charged_wrapper_actions"]
    weight_fraction = dt / (t1 - t0)
    p0, p1 = [np.asarray([s["position"] for s in states]) for states in (before, after)]
    displacement = (p1 - p0) * weight_fraction[:, None]
    distance = np.linalg.norm(displacement, axis=1)
    actual = np.asarray([s["speed_m_s"] for s in before])
    actual_end = actual + (np.asarray([s["speed_m_s"] for s in after]) - actual) * weight_fraction
    actual_mid = (actual + actual_end) / 2
    action = np.asarray([r["action"] for r in rows])
    responses = [r["policy_response"] for r in rows]
    telemetry = [r["route_telemetry"] for r in responses]
    speed = np.asarray([r["speed_estimate"] for r in telemetry])
    fallback = np.asarray([r["actual_fallback_called"] for r in telemetry], bool)
    if fallback.any():
        raise ValueError("fallback has no target-speed interpretation; handle separately before analysis")
    reconstructed = [target_limits(t, r["cap_diagnostic"]) for t, r in zip(telemetry, responses)]
    target = np.asarray([r["final"] for r in reconstructed])
    requested = np.asarray([r["requested"] for r in reconstructed])
    near = np.asarray([r["near"] for r in reconstructed])
    curvature = np.asarray([r["curvature"] for r in reconstructed])
    inherited = np.asarray([r["inherited"] for r in reconstructed])
    curve = requested
    capped_distance = np.asarray([r["distance"] for r in reconstructed])
    saved = [r["cap_diagnostic"] for r in responses]
    previous_steer = np.asarray([r["previous_steer_before"] for r in telemetry])
    predicted = np.c_[.8 * np.clip(np.arctan(3.24 * curvature), -.4, .4) + .2 * previous_steer,
                      np.clip(.08 * (target - speed), 0, .5), np.clip(.04 * (speed - target), 0, .5)]
    errors = {"target_max_abs": float(np.max(abs(target - [r["effective_target"] for r in saved]))),
              "inherited_max_abs": float(np.max(abs(inherited - [r["inherited_target"] for r in saved]))),
              "distance_max_abs": float(np.max(abs(capped_distance - [r["distance_cap"] for r in saved]))),
              "action_max_abs": float(np.max(abs(predicted - action)))}
    assert max(errors.values()) < 1e-6, errors
    arc, tangent, center_offset, track_length = project(p0, scene["track"])
    end_arc, _, _, _ = project(p1, scene["track"])
    arc_delta = ((end_arc - arc + track_length/2) % track_length - track_length/2) * weight_fraction
    road_forward = np.einsum('ni,ni->n', displacement, tangent)
    road_lateral = displacement[:, 0] * -tangent[:, 1] + displacement[:, 1] * tangent[:, 0]
    angle = np.asarray([s["angle"] for s in before])
    body_forward = displacement[:, 0] * -np.sin(angle) + displacement[:, 1] * np.cos(angle)
    body_lateral = displacement[:, 0] * np.cos(angle) + displacement[:, 1] * np.sin(angle)
    damage_gain = np.asarray([a["damage"] > b["damage"] + 1e-9 for b, a in zip(before, after)])
    recovery = np.zeros(n, bool)
    for event in t0[damage_gain]:
        recovery |= (t0 >= event) & (t0 < event + 2. - 1e-9)
    collision = np.asarray([r["info"]["collision"] for r in rows], bool)
    # Despite its name, the wrapper counts negative-reward steps, not wheel/road
    # contact. A positive value often just means no new tile on this decision.
    negative_reward_counter = np.asarray([s["off_track_counter"] > 0 for s in before])
    no_progress = np.asarray([a["unique_tiles"] == b["unique_tiles"] for b, a in zip(before, after)])
    runs = continuous_runs(no_progress, dt)
    sustained = np.zeros(n, bool)
    for begin, end, seconds in runs:
        if seconds >= 2 - 1e-9:
            sustained[begin:end] = True
    stable = ~near & (abs(action[:, 0]) <= .1) & (actual >= 5) & ~negative_reward_counter & ~recovery
    error = speed - actual
    caps = {}
    for name in ("global", "curvature", "distance", "one_global_code_site", "near_safe_schedule"):
        delta = np.maximum(0., np.asarray([r["without"][name] for r in reconstructed]) - target)
        raised = delta > 1e-8
        binding = (np.asarray([r["limits"][name] for r in reconstructed]) <= target + 1e-8
                   if name in reconstructed[0]["limits"] else (near if name == "near_safe_schedule" else target >= 28-1e-8))
        exposure_key = "near_schedule_applied_s" if name == "near_safe_schedule" else "binding_including_ties_s"
        caps[name] = {exposure_key: float(dt[binding].sum()),
                      "single_removal_raises_target_s": float(dt[raised].sum()),
                      "delta_m_s_time_mean_all": weighted(delta, dt),
                      "delta_m_s_when_raised": distribution(delta, dt * raised),
                      "stable_raised_s": float(dt[raised & stable].sum()),
                      "stable_delta_mean": weighted(delta, dt * stable),
                      "not_lap_seconds_recoverable": True}
    def subset(mask):
        weights = dt * mask
        return {"seconds": float(weights.sum()), "actual_mean_m_s": weighted(actual_mid, weights),
                "estimate_bias_m_s": weighted(error, weights), "estimate_MAE_m_s": weighted(abs(error), weights),
                "target_mean_m_s": weighted(target, weights),
                "actual_minus_target_mean_m_s": weighted(actual - target, weights),
                "gas_mean": weighted(action[:, 1], weights), "brake_mean": weighted(action[:, 2], weights)}
    speed_bins = {f"{lo}-{hi}": subset((actual_mid >= lo) & (actual_mid < hi))
                  for lo, hi in [(0, 5), (5, 10), (10, 15), (15, 20), (20, 25), (25, 1000)]}
    # Posthoc proposed experiment exposure: all gate inputs exist in the legal
    # policy, unlike diagnostic stability's physical-speed/reward labels.
    gentle = ~near & (abs(curvature) >= .015) & (abs(curvature) <= .05) & (abs(action[:, 0]) <= .18)
    gentle_target = np.minimum(28., np.minimum(np.sqrt(8 / (abs(curvature)+.003)), capped_distance))
    gentle_delta = np.where(gentle, gentle_target - target, 0.)
    progress = np.asarray([r["unique_tiles"] / len(scene["track"]) for r in before])
    decile = np.minimum(9, (10 * progress).astype(int))
    segments = []
    for group in range(10):
        mask = decile == group
        segments.append({"progress_percent": [10*group, 10*(group+1)], **subset(mask),
                         "distance_chord_m": float(distance[mask].sum()),
                         "curve_binding_s": float(dt[mask & (curve <= target+1e-8)].sum()),
                         "distance_strict_s": float(dt[mask & (capped_distance < inherited-1e-8)].sum()),
                         "collision_recovery_s": float(dt[mask & recovery].sum())})
    ipc = np.asarray([r["act_including_IPC_ms"] for r in rows])
    compute = np.asarray([r["act_compute_ms"] for r in responses])
    return {"name": spec["name"], "actions": n, "official_lap_s": duration,
            "full_trace_sim_s": float((t1-t0).sum()), "post_finish_trace_s": float((t1-t0).sum()-duration),
            "damage": result["damage"], "formula_validation": errors,
            "path": {"saved_centerline_length_m": track_length, "sampled_chord_distance_m": float(distance.sum()),
                     "chord_to_centerline_ratio": float(distance.sum()/track_length),
                     "actual_speed_integral_trapezoid_m": float(np.dot(actual_mid, dt)),
                     "road_forward_m": float(np.maximum(road_forward, 0).sum()),
                     "road_reverse_m": float(np.maximum(-road_forward, 0).sum()),
                     "road_absolute_lateral_m": float(abs(road_lateral).sum()),
                     "body_forward_m": float(np.maximum(body_forward, 0).sum()),
                     "body_reverse_m": float(np.maximum(-body_forward, 0).sum()),
                     "body_absolute_lateral_m": float(abs(body_lateral).sum()),
                     "road_arc_net_m": float(arc_delta.sum()),
                     "projection_jump_over_2chords_plus2m_count": int((abs(arc_delta) > 2*distance+2).sum()),
                     "center_offset_m": distribution(center_offset, dt),
                     "mean_chord_speed_m_s": float(distance.sum()/duration),
                     "same_distance_at_constant28_s_arithmetic_only": float(distance.sum()/28),
                     "mean_speed_for_same_chords_in10s": float(distance.sum()/10),
                     "mean_speed_for_same_chords_in19s": float(distance.sum()/19)},
            "requested_speed": distribution(requested, dt), "target_speed": distribution(target, dt),
            "actual_speed": distribution(actual_mid, dt), "estimate": distribution(speed, dt),
            "speed_error": {"signed_estimate_minus_actual": distribution(error, dt),
                            "MAE_m_s": weighted(abs(error), dt),
                            "RMSE_m_s": math.sqrt(weighted(error**2, dt)),
                            "overestimate_gt3_s": float(dt[error > 3].sum()),
                            "underestimate_gt3_s": float(dt[error < -3].sum()),
                            "braking_while_true_speed_below_target_by1_s": float(dt[(action[:, 2] > 0) & (actual < target-1)].sum())},
            "caps": caps, "speed_bins": speed_bins, "progress_deciles": segments,
            "proposed_gentle_curve_gate": {**subset(gentle),
                    "delta_target_when_enabled_m_s": distribution(gentle_delta, dt * gentle),
                    "arithmetic_only_not_closed_loop": True},
            "subsets": {"stable": subset(stable), "near_hazard": subset(near),
                        "not_near_hazard": subset(~near), "collision_recovery": subset(recovery),
                        "outside_recovery": subset(~recovery), "negative_reward_counter_positive": subset(negative_reward_counter)},
            "controls": {"gas_on_s": float(dt[action[:, 1] > 1e-6].sum()),
                         "gas_saturated_s": float(dt[action[:, 1] >= .5-1e-6].sum()),
                         "brake_on_s": float(dt[action[:, 2] > 1e-6].sum()),
                         "brake_saturated_s": float(dt[action[:, 2] >= .5-1e-6].sum()),
                         "strong_steer_ge_point3_s": float(dt[abs(action[:, 0]) >= .3].sum()),
                         "abs_steer": distribution(abs(action[:, 0]), dt),
                         "gas": distribution(action[:, 1], dt), "brake": distribution(action[:, 2], dt)},
            "events": {"collision_s": float(dt[collision].sum()), "damage_increase_actions": int(damage_gain.sum()),
                       "collision_recovery_union_s": float(dt[recovery].sum()),
                       "no_new_tile_longest_s": max((r[2] for r in runs), default=0),
                       "no_new_tile_runs_ge2s_total_s": float(dt[sustained].sum()),
                       "actual_speed_below5_s": float(dt[actual_mid < 5].sum()), "fallback_actions": int(fallback.sum())},
            "compute": {"native_wall_s": result["wall_s"], "env_step_wall_s": result["sum_sim_step_wall_s"],
                        "actor_CPU_s": result["actor_CPU_s"], "IPC_sum_wall_s": float(ipc.sum()/1000),
                        "IPC_ms": distribution(ipc, np.ones(n)),
                        "actor_compute_sum_wall_s": float(compute.sum()/1000)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    wall, cpu = time.perf_counter(), time.process_time()
    specs = json.loads(args.inputs.read_text())["cases"]
    cases = [analyze_case(spec) for spec in specs]
    hashes = {str(path): hashlib.sha256(Path(path).read_bytes()).hexdigest()
              for spec in specs for path in (spec["scene"], spec["result"], spec["trace"])}
    output = {"new_environment_actions": 0, "new_policy_or_model_calls": 0,
              "cases": cases, "input_sha256": hashes,
              "analysis_wall_s": time.perf_counter()-wall, "analysis_CPU_s": time.process_time()-cpu}
    args.output.write_text(json.dumps(output, indent=2, allow_nan=False)+"\n")
    print(json.dumps({"cases": len(cases), "saved_actions": sum(c["actions"] for c in cases),
                      "new_actions": 0, "output": str(args.output)}))


if __name__ == "__main__":
    main()
