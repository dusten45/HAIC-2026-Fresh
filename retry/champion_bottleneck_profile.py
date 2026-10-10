"""Descriptive, overlapping champion events from saved interval telemetry only."""

import math


DEFAULT_THRESHOLDS = {
    "stall_seconds": 0.8,
    "stall_speed": 2.0,
    "strong_steer": 0.30,
    "recovery_seconds": 2.0,
    "initial_unique_tiles": 2,
}
FLAGS = (
    "stall", "progress_stall", "obstacle_avoidance", "strong_steer",
    "road_recognition_missing", "route_target_missing", "recovery",
)


def profile(rows, thresholds=None):
    """Return seconds, shares and continuous runs; events are not causal labels.

    ``unique_tiles`` is the count after the interval. Event age uses the last
    gain's after-time; initially it uses the first interval's before-time.
    Recovery begins on the interval *after* a clear interval gains a tile.
    Shares use observed interval duration, so missing time is not attributed.
    ``road_recognition_missing`` concerns pixel centerline perception, whereas
    ``route_target_missing`` also permits connectivity/planning failure.
    """
    limits = dict(DEFAULT_THRESHOLDS)
    if thresholds is not None:
        unknown = set(thresholds) - set(limits)
        if unknown:
            raise ValueError(f"unknown thresholds: {sorted(unknown)}")
        limits.update(thresholds)
    if any(not math.isfinite(float(v)) or float(v) < 0 for v in limits.values()):
        raise ValueError("thresholds must be finite and nonnegative")
    rows = list(rows)
    seconds = dict.fromkeys(FLAGS, 0.0)
    longest = dict.fromkeys(FLAGS, None)
    current_runs = dict.fromkeys(FLAGS, None)
    intervals, recoveries = [], []
    previous_tiles = int(limits["initial_unique_tiles"])
    last_new_tile_time = float(rows[0]["before_time"]) if rows else None
    previous_after = previous_step = None
    pending, recovery_start, recovery_until = False, None, None
    elapsed = union_seconds = 0.0

    for index, row in enumerate(rows):
        step = int(row.get("step", index + 1))
        before, after = float(row["before_time"]), float(row["after_time"])
        tiles = int(row["unique_tiles"])
        policy = row["policy"]
        speed = float(policy["speed_estimate"])
        steer = float(row["action"][0])
        if not all(math.isfinite(v) for v in (before, after, speed, steer)):
            raise ValueError("nonfinite interval telemetry")
        if after <= before or tiles < previous_tiles:
            raise ValueError("intervals must advance time and unique tiles must be monotonic")
        if previous_after is not None and (before < previous_after - 1e-9 or step <= previous_step):
            raise ValueError("intervals must be ordered and nonoverlapping")
        duration = after - before
        age = before - last_new_tile_time
        gain = tiles > previous_tiles
        events = {
            "stall": age >= limits["stall_seconds"] and speed <= limits["stall_speed"],
            "progress_stall": age >= limits["stall_seconds"],
            "obstacle_avoidance": bool(policy["hazard_near"]),
            "strong_steer": abs(steer) >= limits["strong_steer"],
            "road_recognition_missing": int(policy["centerline_points"]) == 0,
            "route_target_missing": bool(policy["route_target_missing"]),
        }
        anomaly = (events["road_recognition_missing"] or events["route_target_missing"]
                   or events["progress_stall"] or bool(row["collision"]))
        events["recovery"] = bool(
            not anomaly and recovery_start is not None
            and recovery_start <= before < recovery_until)
        if anomaly:
            pending = True
            recovery_start = recovery_until = None
        elif pending and gain:
            pending = False
            recovery_start = after
            recovery_until = after + limits["recovery_seconds"]
            recoveries.append({"trigger_step": step, "start_time": after,
                               "until_time": recovery_until})
        continuous = (previous_after is not None and step == previous_step + 1
                      and abs(before - previous_after) <= 1e-9)
        for name, active in events.items():
            if active:
                seconds[name] += duration
                run = current_runs[name]
                if run is None or not continuous:
                    run = {"start_step": step, "end_step": step,
                           "start_time": before, "end_time": after,
                           "duration_s": duration, "intervals": 1}
                else:
                    run = dict(run, end_step=step, end_time=after,
                               duration_s=run["duration_s"] + duration,
                               intervals=run["intervals"] + 1)
                current_runs[name] = run
                if longest[name] is None or run["duration_s"] > longest[name]["duration_s"]:
                    longest[name] = dict(run)
            else:
                current_runs[name] = None
        elapsed += duration
        if any(events.values()):
            union_seconds += duration
        intervals.append({"step": step, "before_time": before, "after_time": after,
                          "duration_s": duration, "new_tile_gain": tiles - previous_tiles,
                          "seconds_since_last_new_tile": age, "anomaly": anomaly,
                          "flags": events})
        if gain:
            last_new_tile_time = after
        previous_tiles, previous_after, previous_step = tiles, after, step

    return {
        "thresholds": limits, "interval_count": len(rows), "elapsed_s": elapsed,
        "time_span_s": float(rows[-1]["after_time"]) - float(rows[0]["before_time"]) if rows else 0.0,
        "flag_seconds": seconds,
        "flag_shares": {name: value / elapsed if elapsed else 0.0 for name, value in seconds.items()},
        "max_continuous_runs": longest,
        "union_seconds": union_seconds,
        "union_share": union_seconds / elapsed if elapsed else 0.0,
        "sum_flag_seconds": sum(seconds.values()),
        "sum_flag_shares": sum(seconds.values()) / elapsed if elapsed else 0.0,
        "recovery_count": len(recoveries), "recoveries": recoveries,
        "intervals": intervals,
    }
