"""Analyze saved v2 teacher runs, optionally matched against historical v1 runs."""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import statistics

import numpy as np

from .oracle_controller import TrackPath


DEFINITIONS = {
    "curvature": "Signed circumcircle curvature of centerline samples at arc -8, arc, arc +8m.",
    "straight": "Post-action speed where absolute local centerline curvature < .008/m; not preview curvature.",
    "local_centerline_straight_max_speed": "Maximum post-action speed with |local centerline curvature| < .008/m, recomputed offline.",
    "straight_max_speed": "Legacy report alias of local_centerline_straight_max_speed; NOT the historical runner summary's identically named metric.",
    "planner_limited_straight_max_speed": "Runner summary maximum post-action speed where |planner limiting-point reference curvature| < .008/m. Historical runner straight_max_speed is preserved under this distinct name.",
    "corners": "2m centerline grid; connected samples with |curvature| >= .012/m and same sign, circularly grouped. Entry/exit are first/last samples; apex is maximum |curvature|.",
    "corner_speed": "Nearest post-action projected arc sample, circular distance <= 2m; missing samples stay null. Means pool available corners, including failed episodes.",
    "brake_onset": "Command crosses from <= .002 to > .002; forward centerline arc distance from pre-state to nearest upcoming geometric apex. The low threshold reflects v2's low brake gain; not necessarily braking caused by that corner. Planner limiting-point distance is recorded separately.",
    "saturation": "Absolute commanded steering >= .4; not measured wheel angle.",
    "matched": "Successful replicate mean laps paired by track/seed and v2 stage; same saved geometry/obstacles, environment source hashes (env_wrapper.py, damage.py, core/), Python/platform, simulator packages, SDL/render mode, FPS, domain randomization, frame skip, warmup and start time. Teacher/recording source differences are intentional and excluded from environment matching. Missing comparison fields are unverifiable, not matched. Delta = v2 - v1 ms; negative is faster. Replicates are not independent road pairs.",
    "packages": "Comparison normalizes distribution names and compares numpy, gymnasium, opencv-python and box2d-py, shared by historical full-package and current simulator-package provenance schemas; unrelated installed packages are not simulation conditions.",
    "execution_groups": "All recorded source hashes plus control arguments (excluding output/grid/repeats), Python and packages. Mixed-source aggregates are retained with warnings, not one frozen-source claim.",
    "limitations": "Privileged, exposed local evidence, not official score. Distances/speeds use simulator world units (nominal meters). Wrapper-boundary samples can miss extrema/onsets; coarse corners are not racing-line apexes. Missing artifacts are excluded from complete-episode denominators.",
}


def mean(values):
    return statistics.mean(values) if values else None


def curvature(path, arc):
    before, here, after = (path.sample(arc + offset) for offset in (-8, 0, 8))
    left, right, chord = here - before, after - here, after - before
    denominator = np.linalg.norm(left) * np.linalg.norm(right) * np.linalg.norm(chord)
    return float(2 * (left[0] * right[1] - left[1] * right[0]) / denominator) if denominator else 0.0


def corners(path):
    arcs = np.arange(0, path.length, 2.0)
    bends = np.array([curvature(path, arc) for arc in arcs])
    signs = np.where(np.abs(bends) >= .012, np.sign(bends), 0)
    starts = np.flatnonzero((signs != 0) & (signs != np.roll(signs, 1)))
    if not len(starts) and np.any(signs):
        starts = [0]
    result = []
    for start in starts:
        indices = [int(start)]
        while len(indices) < len(arcs):
            next_index = (indices[-1] + 1) % len(arcs)
            if signs[next_index] != signs[start]:
                break
            indices.append(next_index)
        apex = max(indices, key=lambda index: abs(bends[index]))
        result.append({"sign": int(signs[start]), "entry_arc_m": float(arcs[start]),
                       "apex_arc_m": float(arcs[apex]), "exit_arc_m": float(arcs[indices[-1]])})
    return result


def driving_metrics(metadata, trace):
    path = TrackPath(np.asarray(metadata["track_points"])[:, 2:4])
    turns = corners(path)
    arcs = np.array([path.project(row["post_state"]["position"])[0] for row in trace])
    speeds = [row["post_state"]["speed"] for row in trace]
    straight = [speed for arc, speed in zip(arcs, speeds) if abs(curvature(path, arc)) < .008]
    for turn in turns:
        for phase in ("entry", "apex", "exit"):
            distances = np.abs((arcs - turn[f"{phase}_arc_m"] + path.length / 2)
                               % path.length - path.length / 2)
            index = int(np.argmin(distances)) if len(distances) else None
            turn[f"{phase}_sample"] = ({"speed": speeds[index], "step": trace[index]["step"],
                                        "arc_error_m": float(distances[index])}
                                       if index is not None and distances[index] <= 2 else None)
    onsets, previous_brake = [], 0.0
    for row in trace:
        brake = row["action"][2]
        if brake > .002 and previous_brake <= .002 and turns:
            arc = path.project(row["pre_state"]["position"])[0]
            index = min(range(len(turns)), key=lambda i: (turns[i]["apex_arc_m"] - arc) % path.length)
            onsets.append({"step": row["step"], "corner_index": index,
                           "distance_to_apex_m": (turns[index]["apex_arc_m"] - arc) % path.length,
                           "speed": row["pre_state"]["speed"],
                           "planner_limiting_distance": row.get("diagnostics", {}).get("limiting_distance"),
                           "required_braking_distance": row.get("diagnostics", {}).get("required_braking_distance")})
        previous_brake = brake
    return {"actions": len(trace), "collision_positive_actions": sum(bool(r["info"].get("collision")) for r in trace),
            "steering_saturated_actions": sum(abs(r["action"][0]) >= .4 for r in trace),
            "local_centerline_straight_max_speed": max(straight, default=None),
            "straight_max_speed": max(straight, default=None), "corners": turns,
            "brake_onsets": onsets}


def signature(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def execution_config(provenance):
    return {"source_sha256": provenance.get("source_sha256"),
            "control": {k: v for k, v in provenance["args"].items()
                        if k not in ("output", "track_ids", "seeds", "repeats")},
            "python": provenance.get("python"), "packages": provenance.get("packages")}


def comparison_conditions(metadata):
    """Extract only shared simulation conditions, not the intentionally different teachers."""
    provenance = metadata.get("run_provenance", {})
    args = provenance.get("args", {})
    sources = provenance.get("source_sha256", {})
    environment = {k: v for k, v in sources.items()
                   if k in ("env_wrapper.py", "damage.py") or k.startswith("core/")}
    conditions = {"environment_source_sha256": environment}
    missing = [f"source_sha256.{k}" for k in
               ("env_wrapper.py", "damage.py", "core/vendor/car_racing.py") if not environment.get(k)]
    missing.extend(f"source_sha256.{k}" for k, v in environment.items() if v is None)
    packages = {k.lower().replace("_", "-"): v for k, v in provenance.get("packages", {}).items()}
    conditions["packages"] = {k: packages.get(k) for k in
                              ("numpy", "gymnasium", "opencv-python", "box2d-py")}
    missing.extend(f"packages.{k}" for k, v in conditions["packages"].items() if v is None)
    for key in ("python", "platform", "sdl", "render_mode", "fps", "domain_randomize"):
        conditions[key] = provenance.get(key)
        if conditions[key] is None:
            missing.append(key)
    for key in ("frame_skip", "warmup", "start_t"):
        conditions[key] = metadata.get(key, args.get(key))
        if conditions[key] is None:
            missing.append(key)
    # V1 saves randomization globally; v2 also saves it per episode.
    if "domain_randomize" in metadata:
        if metadata["domain_randomize"] != conditions["domain_randomize"]:
            missing.append("inconsistent_domain_randomize")
        conditions["domain_randomize"] = metadata["domain_randomize"]
    return conditions, sorted(set(missing))


def load_runs(directories, baseline=False):
    if len({Path(p).resolve() for p in directories}) != len(directories):
        raise ValueError("Duplicate run directories would double-count episodes")
    episodes, artifacts = [], []
    for directory in map(Path, directories):
        provenance = json.loads((directory / "metadata.json").read_text())
        planned = provenance["args"]
        execution = execution_config(provenance)
        group = signature(execution)
        suffixes = (".summary.json", ".metadata.json", ".jsonl")
        observed = {p.name.removesuffix(suffix) for suffix in suffixes
                    for p in directory.glob(f"track*{suffix}")}
        repeats = range(1, planned.get("repeats", 1) + 1) if baseline else (None,)
        expected = {f"track{t}_seed{s}" + (f"_repeat{r}" if baseline else ""):
                    {"track_id": t, "geometry_seed": s, **({"repeat": r} if baseline else
                                                           {"stage": planned.get("stage")})}
                    for t in planned["track_ids"] for s in planned["seeds"] for r in repeats}
        incomplete = []
        complete = 0
        for name in sorted(observed):
            missing = [suffix for suffix in suffixes if not (directory / f"{name}{suffix}").exists()]
            summary_path = directory / f"{name}.summary.json"
            summary = {}
            if summary_path.exists():
                try:
                    summary = json.loads(summary_path.read_text())
                except json.JSONDecodeError:
                    missing.append("summary_json")
            metadata = {}
            trace = []
            if not missing:
                try:
                    metadata = json.loads((directory / f"{name}.metadata.json").read_text())
                except json.JSONDecodeError:
                    missing.append("metadata_json")
                try:
                    trace = [row for line in (directory / f"{name}.jsonl").read_text().splitlines()
                             if "action" in (row := json.loads(line))]
                    if len(trace) != summary.get("steps"):
                        missing.append("trace_steps")
                except json.JSONDecodeError:
                    missing.append("trace_json")
            if missing:
                incomplete.append({"episode": name, "missing": missing, "summary": summary})
                continue
            if name not in expected:
                raise ValueError(f"Unexpected complete episode artifacts in {directory}: {name}")
            if summary.get("episode") != name:
                raise ValueError(f"Episode filename/summary identity mismatch: {directory}/{name}")
            for key, value in expected[name].items():
                if value is None or summary.get(key) != value or metadata.get(key) != value:
                    raise ValueError(f"Episode {key} identity mismatch: {directory}/{name}")
            metadata["run_provenance"] = provenance
            entry = {**summary, "directory": str(directory), "execution_group": group}
            if not baseline:
                entry["planner_limited_straight_max_speed"] = summary.get(
                    "planner_limited_straight_max_speed", summary.get("straight_max_speed"))
                entry.update(driving_metrics(metadata, trace))
            if entry.get("lap_time_ms") is None and entry["finished"]:
                entry["lap_time_ms"] = round((entry["finish_time_s"] - entry["start_t"]) * 1000)
            episodes.append((entry, metadata))
            complete += 1
        artifacts.append({"directory": str(directory), "provenance": provenance,
                          "execution_group": group, "execution_config": execution,
                          "planned_episodes": len(expected),
                          "complete_episodes": complete, "incomplete_episodes": len(incomplete),
                          "missing_planned_episodes": len(expected.keys() - observed),
                          "unexpected_episodes": sorted(observed - expected.keys()), "incomplete": incomplete})
    return episodes, artifacts


def aggregate(episodes, artifacts):
    entries = [entry for entry, _ in episodes]
    roads = {(e["track_id"], e["geometry_seed"]) for e in entries}
    successful = [e for e in entries if e["finished"]]
    laps = [e["lap_time_ms"] for e in successful]
    actions = sum(e.get("actions", 0) for e in entries)
    saturated = sum(e.get("steering_saturated_actions", 0) for e in entries)
    result = {"complete_episodes": len(entries), "distinct_roads": len(roads),
              "finished_episodes": len(successful),
              "finished_roads": len({(e["track_id"], e["geometry_seed"]) for e in successful}),
              "all_observed_episodes_finished_roads": sum(all(e["finished"] for e in entries
                  if (e["track_id"], e["geometry_seed"]) == road) for road in roads),
              "damaged_episodes": sum(e["damage"] > 0 for e in entries),
              "failure_reasons": dict(Counter(e["reason"] for e in entries if not e["finished"])),
              "success_mean_lap_ms": mean(laps), "success_median_lap_ms": statistics.median(laps) if laps else None,
              "success_best_lap_ms": min(laps, default=None), "actions": actions,
              "collision_positive_actions": sum(e.get("collision_positive_actions", 0) for e in entries),
              "steering_saturated_actions": saturated, "steering_saturation_fraction": saturated / actions if actions else None,
               "local_centerline_straight_max_speed": max((e["local_centerline_straight_max_speed"] for e in entries
                                          if e.get("local_centerline_straight_max_speed") is not None), default=None),
               "planner_limited_straight_max_speed": max((e["planner_limited_straight_max_speed"] for e in entries
                                          if e.get("planner_limited_straight_max_speed") is not None), default=None)}
    result["straight_max_speed"] = result["local_centerline_straight_max_speed"]
    for key in ("planned_episodes", "incomplete_episodes", "missing_planned_episodes"):
        result[key] = sum(a[key] for a in artifacts)
    for phase in ("entry", "apex", "exit"):
        samples = [c[f"{phase}_sample"]["speed"] for e in entries for c in e.get("corners", [])
                   if c[f"{phase}_sample"] is not None]
        result[f"corner_{phase}_mean_speed"] = mean(samples)
        result[f"corner_{phase}_samples"] = len(samples)
    distances = [b["distance_to_apex_m"] for e in entries for b in e.get("brake_onsets", [])]
    result.update(brake_onset_samples=len(distances), brake_onset_mean_distance_m=mean(distances))
    return result


def matched_deltas(current, baseline):
    groups, references = defaultdict(list), defaultdict(list)
    for entry, metadata in current:
        groups[(entry["track_id"], entry["geometry_seed"], entry.get("stage"))].append((entry, metadata))
    for entry, metadata in baseline:
        references[(entry["track_id"], entry["geometry_seed"])].append((entry, metadata))
    pairs, excluded = [], []
    for (track, seed, stage), values in sorted(groups.items()):
        prior = references[(track, seed)]
        identity = {"track_id": track, "geometry_seed": seed, "stage": stage}
        signatures = {json.dumps([m.get("track_points"), m.get("obstacles")], sort_keys=True)
                      for _, m in values + prior}
        extracted = [comparison_conditions(m) for _, m in values + prior]
        missing = sorted({key for _, fields in extracted for key in fields})
        if any("track_points" not in m or "obstacles" not in m for _, m in values + prior):
            missing.append("geometry_or_obstacles")
        conditions = {signature(c) for c, _ in extracted}
        good, old = ([e for e, _ in rows if e["finished"]] for rows in (values, prior))
        reason = ("missing_baseline" if not prior else "geometry_or_obstacles_mismatch" if len(signatures) != 1
                  else "unverifiable_conditions" if missing
                  else "environment_or_execution_conditions_mismatch" if len(conditions) != 1
                  else "no_successful_pair" if not good or not old else None)
        if reason:
            excluded.append(dict(identity, reason=reason, **({"missing_fields": missing} if missing else {})))
        else:
            v2, v1 = (statistics.mean([e["lap_time_ms"] for e in rows]) for rows in (good, old))
            pairs.append(dict(identity, v2_successful_episodes=len(good), v1_successful_episodes=len(old),
                              v2_mean_lap_ms=v2, v1_mean_lap_ms=v1, delta_ms=v2 - v1,
                              conditions=extracted[0][0]))
    return {"successful_road_stage_pairs": len(pairs), "mean_delta_ms": mean([p["delta_ms"] for p in pairs]),
            "pairs": pairs, "excluded": excluded}


def report(directories, baseline=None):
    episodes, artifacts = load_runs(directories)
    groups = {}
    for artifact in artifacts:
        group = groups.setdefault(artifact["execution_group"], {
            "fingerprint": artifact["execution_group"], "directories": [], "complete_episodes": 0,
            "configuration": artifact["execution_config"]})
        group["directories"].append(artifact["directory"])
        group["complete_episodes"] += artifact["complete_episodes"]
    source_groups = {signature(a["provenance"].get("source_sha256")) for a in artifacts}
    warnings = []
    if len(source_groups) > 1:
        warnings.append("Mixed source groups: aggregate retained, but does not establish one frozen-source execution.")
    if len(groups) > 1:
        warnings.append("Mixed execution groups: inspect per-stage and execution-group evidence before comparing pooled laps.")
    unverifiable = [dict(directory=e["directory"], episode=e["episode"], missing_fields=missing)
                    for e, m in episodes if (missing := comparison_conditions(m)[1])]
    if unverifiable:
        warnings.append("Legacy/missing comparison conditions: affected episodes are unverifiable, not silently matched.")
    stages = sorted(({e["stage"] for e, _ in episodes} | {a["provenance"]["args"].get("stage")
                    for a in artifacts}) - {None})
    result = {"definitions": DEFINITIONS, "aggregate": aggregate(episodes, artifacts),
              "per_stage": {stage: aggregate([(e, m) for e, m in episodes if e["stage"] == stage],
                            [a for a in artifacts if a["provenance"]["args"].get("stage") == stage])
                            for stage in stages},
              "execution_groups": list(groups.values()), "source_group_count": len(source_groups),
              "warnings": warnings, "unverifiable_episodes": unverifiable,
              "artifacts": artifacts, "episodes": [e for e, _ in episodes]}
    if baseline:
        old, old_artifacts = load_runs(baseline, baseline=True)
        result["baseline_artifacts"] = old_artifacts
        result["matched_v1_v2"] = matched_deltas(episodes, old)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    parser.add_argument("--baseline", type=Path, nargs="+", help="Historical v1 run directories")
    parser.add_argument("--output", type=Path, help="Write the full JSON report")
    args = parser.parse_args(argv)
    result = report(args.directories, args.baseline)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: result[key] for key in ("definitions", "aggregate", "per_stage", "execution_groups", "warnings", "artifacts")},
                     indent=2, allow_nan=False))
    if "matched_v1_v2" in result:
        print(json.dumps(result["matched_v1_v2"], indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
