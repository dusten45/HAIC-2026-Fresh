"""Diagnose saved near-path intent with bounded, sequential arc projections.

This module only reads telemetry and performs geometry. It never imports a
policy or simulator. A route anchored at the current origin has tautological
zero pre-action lateral error; its first edge may describe an unsupported
connector rather than observed road beneath the vehicle.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import time

import numpy as np


def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def rotation(angle):
    return np.array([[math.cos(angle), -math.sin(angle)],
                     [math.sin(angle), math.cos(angle)]])


def path_geometry(points):
    points = np.asarray(points, dtype=float)
    if points.ndim != 2 or points.shape[1] != 2 or len(points) < 2:
        return None
    vectors = np.diff(points, axis=0)
    lengths = np.linalg.norm(vectors, axis=1)
    if not np.isfinite(points).all() or np.any(lengths <= 0):
        return None
    return points, vectors, lengths, np.r_[0., np.cumsum(lengths)]


def bounded_projection(point, geometry, previous_arc, movement, previous_segment):
    """Clip each segment to the allowed arc interval before projecting."""
    points, vectors, lengths, arcs = geometry
    lower = max(0., previous_arc - movement)
    upper = min(float(arcs[-1]), previous_arc + movement)
    choices = []
    for index, length in enumerate(lengths):
        left, right = max(lower, arcs[index]), min(upper, arcs[index + 1])
        if left > right:
            continue
        minimum, maximum = (left - arcs[index]) / length, (right - arcs[index]) / length
        fraction = float(np.clip(np.dot(point - points[index], vectors[index]) /
                                 (length * length), minimum, maximum))
        foot = points[index] + fraction * vectors[index]
        arc = float(arcs[index] + fraction * length)
        choices.append((float(np.linalg.norm(point - foot)), abs(arc - previous_arc),
                        abs(index - previous_segment), index, arc))
    if not choices:
        return None
    distance, _, _, index, arc = min(choices)
    tangent = vectors[index] / lengths[index]
    return {"arc_m": arc, "segment": int(index), "distance_m": distance,
            "tangent_right_bearing_rad": math.atan2(float(tangent[0]), float(tangent[1])),
            "allowed_arc_m": [lower, upper], "actual_origin_movement_m": movement,
            "arc_change_m": arc - previous_arc,
            "arc_bound_satisfied": abs(arc - previous_arc) <= movement + 1e-9,
            "geometry_valid": True, "active_connector": index == 0}


def point_at_arc(geometry, arc):
    points, vectors, lengths, arcs = geometry
    index = min(int(np.searchsorted(arcs[1:], arc, side="left")), len(lengths) - 1)
    return points[index] + vectors[index] * ((arc - arcs[index]) / lengths[index])


def analyze(rows):
    output = []
    previous_pre_bearing = None
    for row in rows:
        telemetry = row["route_telemetry"]
        geometry = path_geometry(telemetry["selected_path"])
        result = {"step": row["step"], "pre_time_s": row["before_time"],
                  "post_time_s": row["after_time"], "actual_fallback": telemetry["actual_fallback_called"],
                  "path_present": geometry is not None, "raw_samples": [],
                  "current_detections": telemetry["current_detections"],
                  "memory_hazards": telemetry["memory_hazards_after_tracker"],
                  "target": telemetry["selected_target"], "pixel_speed_m_s": telemetry["speed_estimate"],
                  "cap": row.get("cap_diagnostic"), "final_action": row["action"],
                  "unique_gain": row["truth_after"]["unique_tiles"] - row["truth_before"]["unique_tiles"],
                  "collision": row["collision"]}
        if geometry is None:
            output.append(result)
            previous_pre_bearing = None
            continue
        points, vectors, lengths, arcs = geometry
        pre_bearing = math.atan2(float(vectors[0, 0]), float(vectors[0, 1]))
        secant = point_at_arc(geometry, min(1., float(arcs[-1]))) - points[0]
        result.update(pre_near_right_bearing_rad=pre_bearing,
                      pre_origin_lateral_error_m=0., pre_lateral_error_tautological=True,
                      first_grid_arc_m=float(arcs[1]), first_grid_forward_m=float(points[1, 1]),
                      fixed_one_m_secant_bearing_rad=math.atan2(float(secant[0]), float(secant[1])),
                      one_m_secant_is_connector=bool(arcs[1] >= 1.),
                      first_grid_segment_right_bearing_rad=(None if len(vectors) < 2 else
                          math.atan2(float(vectors[1, 0]), float(vectors[1, 1]))),
                      decision_path_head_change_rad=(None if previous_pre_bearing is None else
                          wrap(pre_bearing - previous_pre_bearing)))
        previous_pre_bearing = pre_bearing
        target = telemetry["selected_target"]
        if target is not None:
            x, forward = map(float, target)
            curvature = 2. * x / max(x*x + forward*forward, 1e-6)
            derived = math.atan(3.24 * curvature)
            result.update(target_right_bearing_rad=math.atan2(x, forward),
                          derived_unclipped_steer=derived,
                          derived_clipped_steer=float(np.clip(derived, -.4, .4)),
                          recorded_pre_cap_steer=(row["cap_diagnostic"]["original_action"][0]
                              if row.get("cap_diagnostic") else row["action"][0]),
                          previous_steer_before=telemetry.get("previous_steer_before"))
        origin = np.asarray(row["truth_before"]["position"], dtype=float)
        angle = float(row["truth_before"]["angle"])
        inverse = rotation(angle)
        previous_position = origin.copy()
        previous_arc, previous_segment = 0., 0
        for raw_index, interval in enumerate(row["raw_intervals"], 1):
            for phase in ("before", "after"):
                state = interval[phase]
                world = np.asarray(state["position"], dtype=float)
                local = (world - origin) @ inverse
                movement = float(np.linalg.norm(world - previous_position))
                projection = bounded_projection(local, geometry, previous_arc, movement, previous_segment)
                sample = {"raw_tick": raw_index, "phase": phase, "time_s": state["time"],
                          "local_origin_m": local.tolist(), "speed_m_s": state["speed_m_s"],
                          "hull_angle_rad": state["angle"], "angular_velocity_rad_s": state["angular_velocity"],
                          "wheel_joint_angles_rad": [wheel["joint_angle"] for wheel in state["wheels"]],
                          "body_right_bearing_rad": wrap(angle - state["angle"]),
                          "projection": projection}
                if projection is not None:
                    sample["signed_near_heading_gap_rad"] = wrap(
                        projection["tangent_right_bearing_rad"] - sample["body_right_bearing_rad"])
                    previous_arc, previous_segment = projection["arc_m"], projection["segment"]
                previous_position = world
                result["raw_samples"].append(sample)
        output.append(result)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    wall, cpu = time.perf_counter(), time.process_time()
    rows = []
    digest = hashlib.sha256()
    with args.trace.open("rb") as handle:
        for line in handle:
            digest.update(line)
            match = re.search(rb'"step"\s*:\s*(\d+)', line[:128])
            if match and args.start <= int(match.group(1)) <= args.end:
                rows.append(json.loads(line))
    assert [row["step"] for row in rows] == list(range(args.start, args.end + 1))
    result = {"source_trace_sha256": digest.hexdigest(), "step_range": [args.start, args.end],
              "rows": analyze(rows), "new_env_policy_model_calls": 0,
              "analysis_CPU_s": time.process_time() - cpu,
              "analysis_wall_s": time.perf_counter() - wall,
              "qualifications": ["Pre-action origin/path lateral zero is tautological.",
                 "The synthetic connector is not observed road beneath the body.",
                 "Near heading and target bearing differ; sequential projection excludes remote jumps.",
                 "A heading gap or delayed wheel response alone does not identify a failing controller."]}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"rows": len(rows), "analysis_CPU_s": result["analysis_CPU_s"],
                      "analysis_wall_s": result["analysis_wall_s"]}))


if __name__ == "__main__":
    main()
