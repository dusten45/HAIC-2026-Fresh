"""Local-only paired oracle/student full-episode evaluation and deviation trace."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from uuid import uuid4

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
from gymnasium.wrappers.time_limit import TimeLimit

from core.vendor.car_racing import CarRacing
from env_wrapper import CarEnvironment
from oracle.oracle_controller import OracleController
from oracle.recording import encode, execution_fingerprint, snapshot_sources, vehicle_state
from bc.contracts import BASELINE_CONDITIONS, SPLIT_SEEDS, TRACK_IDS


ACTION_THRESHOLDS = (0.08, 0.12, 0.08)
POSITION_THRESHOLD = 2.0


def first_deviations(records):
    """Find first reference-action, same-state action and pose departures."""
    answer: dict[str, dict | None] = {"reference_action": None, "on_state_action": None, "position": None}
    for row in records:
        student = np.asarray(row["student_action"])
        reference = np.asarray(row["reference_action"]) if row["reference_action"] is not None else student
        teacher = np.asarray(row["teacher_on_student_action"])
        for name, difference in (("reference_action", np.abs(student - reference)),
                                 ("on_state_action", np.abs(student - teacher))):
            if name == "reference_action" and row["reference_action"] is None:
                continue
            if answer[name] is None and np.any(difference > ACTION_THRESHOLDS):
                answer[name] = {"step": row["step"], "component": ["steer", "gas", "brake"][int(np.argmax(difference / ACTION_THRESHOLDS))],
                                "absolute_difference": difference.tolist(),
                                "oracle_prefix": row.get("oracle_prefix", False),
                                "curvature": row["teacher_diagnostics"]["curvature"],
                                "speed": row["pre_state"]["speed"],
                                "nearest_obstacle_distance": row["nearest_obstacle_distance"]}
        if answer["position"] is None and row["reference_position"] is not None:
            distance = float(np.linalg.norm(np.asarray(row["pre_state"]["position"]) - row["reference_position"]))
            if distance > POSITION_THRESHOLD:
                answer["position"] = {"step": row["step"], "distance": distance,
                                      "curvature": row["teacher_diagnostics"]["curvature"],
                                      "speed": row["pre_state"]["speed"],
                                      "nearest_obstacle_distance": row["nearest_obstacle_distance"]}
    return answer


def rollout(track_id, seed, max_steps, policy=None, trace_path=None, samples=None, oracle_prefix_steps=0):
    """Run original wrapped environment; policy sees only the actual image stack."""
    if oracle_prefix_steps < 0 or (oracle_prefix_steps and policy is None):
        raise ValueError("oracle prefix requires a policy and a nonnegative step count")
    base = CarRacing(continuous=True, render_mode=BASELINE_CONDITIONS["render_mode"],
                     domain_randomize=BASELINE_CONDITIONS["domain_randomize"])
    env = CarEnvironment(TimeLimit(base, max_episode_steps=max_steps * BASELINE_CONDITIONS["frame_skip"] + 200),
                         skip_frames=BASELINE_CONDITIONS["frame_skip"],
                         no_operation=BASELINE_CONDITIONS["warmup"],
                         stack_frames=BASELINE_CONDITIONS["stack_frames"])
    rows = []
    try:
        obs, info = env.reset(seed=seed, options={"track_id": track_id})
        teacher = OracleController(base, target_speed=BASELINE_CONDITIONS["target_speed"],
                                   avoid_obstacles=BASELINE_CONDITIONS["avoid_obstacles"])
        if base.track_variables is None:
            raise RuntimeError("Reset did not generate track variables")
        if policy is not None and hasattr(policy, "reset"):
            policy.reset(obs)
        obstacles = [np.asarray(item.position) for item in base.track_variables.obstacles]
        start_t = base.t
        terminated = truncated = False
        for step in range(max_steps):
            pre_state = vehicle_state(base)
            pre_state["progress"] = env._calculate_progress()
            pre_state["damage"] = env.damage.damage
            oracle_action, diagnostics = teacher.act()
            # Advance pixel history even while the teacher controls the environment.
            predicted_action = None if policy is None else np.asarray(policy.act(obs), dtype=np.float32)
            oracle_prefix = policy is not None and step < oracle_prefix_steps
            action = oracle_action if predicted_action is None or oracle_prefix else predicted_action
            if samples is not None:
                samples.append((np.asarray(obs, dtype=np.float32).copy(), oracle_action.copy()))
            if action.shape != (3,) or not np.all(np.isfinite(action)) or not env.action_space.contains(action):
                raise ValueError(f"Invalid policy action at step {step}: {action}")
            if predicted_action is not None and (predicted_action.shape != (3,)
                    or not np.all(np.isfinite(predicted_action)) or not env.action_space.contains(predicted_action)):
                raise ValueError(f"Invalid predicted policy action at step {step}: {predicted_action}")
            distance = min(float(np.linalg.norm(np.asarray(pre_state["position"]) - point))
                           for point in obstacles)
            obs, reward, terminated, truncated, info = env.step(action)
            post_state = vehicle_state(base)
            row = {"step": step, "pre_state": pre_state, "post_state": post_state,
                   "oracle_action": oracle_action.tolist(), "action": action.tolist(),
                   "predicted_action": predicted_action.tolist() if predicted_action is not None else None,
                   "oracle_prefix": oracle_prefix,
                   "teacher_diagnostics": diagnostics,
                   "nearest_obstacle_distance": distance,
                   "reward": float(reward), "progress": env._calculate_progress(),
                   "damage": env.damage.damage, "collision": bool(info.get("collision")),
                   "terminated": bool(terminated), "truncated": bool(truncated),
                   "finished": base.finish_time_s is not None,
                   "retire_reason": info.get("retire_reason")}
            rows.append(row)
            if terminated or truncated:
                break
        if trace_path is not None:
            with trace_path.open("x") as stream:
                for row in rows:
                    stream.write(encode(row) + "\n")
        finish_time = base.finish_time_s
        finished = finish_time is not None
        summary = {"track_id": track_id, "geometry_seed": seed, "finished": finished,
                   "steps": len(rows), "progress": env._calculate_progress(),
                   "damage": env.damage.damage, "terminated": bool(terminated),
                   "truncated": bool(truncated), "reason": "finished" if finished else info.get("retire_reason") or "max_steps",
                   "lap_time_ms": round((finish_time - start_t) * 1000) if finish_time is not None else None}
        return rows, summary
    finally:
        env.close()


def compare(reference, student):
    """Compare predictions, not teacher-forced execution, with oracle labels."""
    paired = []
    for row in student:
        index = row["step"]
        expected = reference[index] if index < len(reference) else None
        paired.append({"step": index, "pre_state": row["pre_state"],
                       "student_action": row.get("predicted_action", row["action"]),
                       "executed_action": row["action"],
                       "oracle_prefix": row.get("oracle_prefix", False),
                       "teacher_on_student_action": row["oracle_action"],
                       "reference_action": expected["action"] if expected else None,
                       "reference_position": expected["pre_state"]["position"] if expected else None,
                       "teacher_diagnostics": row["teacher_diagnostics"],
                       "nearest_obstacle_distance": row["nearest_obstacle_distance"]})
    deviations = first_deviations(paired)
    if any(row["oracle_prefix"] for row in paired):
        autonomous = [row for row in paired if not row["oracle_prefix"]]
        deviations["handoff"] = None
        deviations["after_handoff"] = first_deviations(autonomous)
        if autonomous:
            handoff = autonomous[0]
            error = np.abs(np.asarray(handoff["student_action"]) - handoff["teacher_on_student_action"])
            deviations["handoff"] = {
                "step": handoff["step"], "student_action": handoff["student_action"],
                "executed_action": handoff["executed_action"],
                "teacher_on_student_action": handoff["teacher_on_student_action"],
                "same_state_absolute_error": error.tolist(),
                "same_state_threshold_exceeded": (error > ACTION_THRESHOLDS).tolist(),
                "speed": handoff["pre_state"]["speed"],
                "curvature": handoff["teacher_diagnostics"]["curvature"],
                "nearest_obstacle_distance": handoff["nearest_obstacle_distance"],
            }
    if student:
        last = student[-1]
        deviations["terminal_context"] = {"step": last["step"], "progress": last["progress"],
                                           "speed": last["post_state"]["speed"],
                                           "curvature": last["teacher_diagnostics"]["curvature"],
                                           "nearest_obstacle_distance": last["nearest_obstacle_distance"],
                                           "collision": last["collision"]}
    return deviations


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    diagnostic = parser.add_argument_group("Historical diagnostic options", "Explicit opt-in; not the plain BC baseline")
    parser.add_argument("--checkpoint", type=Path, required=True)
    diagnostic.add_argument("--steer-checkpoint", type=Path,
                        help="Diagnostic: take steering from another observation-only BC policy")
    diagnostic.add_argument("--oracle-prefix-steps", type=int, default=0,
                        help="Diagnostic only: execute oracle for the first N actions, still predict every step")
    parser.add_argument("--track-ids", type=int, nargs="+", default=list(TRACK_IDS))
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--max-steps", type=int, default=BASELINE_CONDITIONS["max_steps"])
    parser.add_argument("--split", choices=("train", "val", "test"), required=True)
    diagnostic.add_argument("--collect-recovery", action="store_true",
                        help="Store oracle labels on visited student states on training roads")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--resume", action="store_true",
                        help="Continue compatible paired evaluation, without recovery collection")
    args = parser.parse_args(argv)
    if (args.max_steps < 1 or args.oracle_prefix_steps < 0 or not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or not args.track_ids or len(set(args.track_ids)) != len(args.track_ids)
            or any(t not in TRACK_IDS for t in args.track_ids)
            or any(s < 0 or s > 0xFFFFFFFF for s in args.seeds)):
        parser.error("invalid track IDs, seeds, max steps or oracle prefix steps")
    if any(seed not in SPLIT_SEEDS[args.split] for seed in args.seeds):
        parser.error("seeds do not belong to selected geometry split")
    if args.collect_recovery and args.split != "train":
        parser.error("recovery labels may only be collected on training geometry")
    if args.collect_recovery and args.oracle_prefix_steps:
        parser.error("oracle prefix is diagnostic only; recovery collection is not supported")
    if args.resume and args.collect_recovery:
        parser.error("resume does not support recovery collection")
    if not args.resume and (args.output.exists() or not args.output.parent.is_dir()):
        parser.error("output must be a new directory with an existing parent")
    if args.resume and not (args.output / "summary.json").is_file():
        parser.error("resume requires an existing summary.json")
    settings = {
        **execution_fingerprint(("bc/evaluate.py", "bc/model.py", "bc/contracts.py",
                                  "oracle/recording.py", "oracle/oracle_controller.py",
                                  "env_wrapper.py", "damage.py")),
        "checkpoint_sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
        "steer_checkpoint_sha256": (hashlib.sha256(args.steer_checkpoint.read_bytes()).hexdigest()
                                    if args.steer_checkpoint is not None else None),
        "split": args.split, "max_steps": args.max_steps,
        "oracle_prefix_steps": args.oracle_prefix_steps,
        "frame_skip": BASELINE_CONDITIONS["frame_skip"], "warmup": BASELINE_CONDITIONS["warmup"],
        "conditions": {**BASELINE_CONDITIONS, "max_steps": args.max_steps,
                       "raw_frame_budget": args.max_steps * BASELINE_CONDITIONS["frame_skip"] + 200},
        "thresholds": {"action": list(ACTION_THRESHOLDS), "position": POSITION_THRESHOLD},
    }
    grid = {(track_id, seed) for track_id in args.track_ids for seed in args.seeds}
    results = []
    completed = set()
    previous = {}
    if args.resume:
        previous = json.loads((args.output / "summary.json").read_text())
        if not previous.get("source_sha256") or not previous.get("packages") or not previous.get("python"):
            parser.error("legacy summary has no execution fingerprint; verification impossible, use a new output directory")
        for key, value in settings.items():
            if key == "oracle_prefix_steps" and previous.get(key, 0) == value:
                continue
            if key not in previous or previous[key] != value:
                parser.error(f"resume incompatible {key}")
        for key, value in (("track_ids", args.track_ids), ("seeds", args.seeds)):
            if key in previous and sorted(previous[key]) != sorted(value):
                parser.error(f"resume incompatible {key} grid")
        if previous.get("collect_recovery"):
            parser.error("resume does not support recovery collection")
        results = previous["results"]
        for result in results:
            road = (result["track_id"], result["geometry_seed"])
            if road not in grid or road in completed:
                parser.error("resume results must be a unique subset of the requested grid")
            for side in ("reference", "student"):
                episode = result[side]
                if (episode.get("track_id"), episode.get("geometry_seed")) != road or not isinstance(episode.get("finished"), bool):
                    parser.error("resume requires complete paired results")
                if "recovery_file" in episode:
                    parser.error("resume does not support recovery collection")
            completed.add(road)
    from bc.model import BCPolicy
    policy = BCPolicy.from_checkpoint(args.checkpoint)
    if args.steer_checkpoint is not None:
        controls_policy = policy
        steering_policy = BCPolicy.from_checkpoint(args.steer_checkpoint)

        class SplitHeads:
            def reset(self, observation):
                for head in (controls_policy, steering_policy):
                    if hasattr(head, "reset"):
                        head.reset(observation)

            def act(self, observation):
                action = controls_policy.act(observation)
                action[0] = steering_policy.act(observation)[0]
                return action

        policy = SplitHeads()
    if args.resume:
        archive = args.output / "interrupted_attempts" / uuid4().hex
        archive.mkdir(parents=True)
        shutil.copy2(args.output / "summary.json", archive / "summary.json")
        for track_id, seed in sorted(grid - completed):
            for side in ("oracle", "student"):
                trace = args.output / f"track{track_id}_seed{seed}.{side}.jsonl"
                if trace.exists():
                    trace.rename(archive / trace.name)
    else:
        args.output.mkdir()
    source_snapshot = (previous.get("source_snapshot") if args.resume
                       else snapshot_sources(args.output, settings))

    def write_summary():
        summary_path = args.output / "summary.json.tmp"
        summary_path.write_text(encode({"checkpoint": str(args.checkpoint), **settings,
            "source_snapshot": source_snapshot,
            "track_ids": args.track_ids, "seeds": args.seeds,
            "collect_recovery": args.collect_recovery,
            "diagnostic_only": bool(args.oracle_prefix_steps),
            "episode_count": len(results), "finish_count": sum(r["student"]["finished"] for r in results),
            "reference_finish_count": sum(r["reference"]["finished"] for r in results),
            "road_count": len(results), "results": results}) + "\n")
        summary_path.replace(args.output / "summary.json")

    if not args.resume:
        write_summary()
    for track_id in args.track_ids:
        for seed in args.seeds:
            if (track_id, seed) in completed:
                continue
            name = f"track{track_id}_seed{seed}"
            reference, reference_summary = rollout(track_id, seed, args.max_steps,
                                                     trace_path=args.output / f"{name}.oracle.jsonl")
            samples = [] if args.collect_recovery else None
            student, student_summary = rollout(track_id, seed, args.max_steps, policy=policy,
                                                 trace_path=args.output / f"{name}.student.jsonl",
                                                 samples=samples, oracle_prefix_steps=args.oracle_prefix_steps)
            if samples is not None and not student_summary["finished"]:
                with (args.output / f"{name}_recovery.npz").open("xb") as stream:
                    np.savez_compressed(stream,
                        observations=np.stack([observation for observation, _ in samples]),
                        actions=np.stack([teacher_action for _, teacher_action in samples]))
                student_summary["recovery_file"] = f"{name}_recovery.npz"
            result = {"track_id": track_id, "geometry_seed": seed,
                      "reference": reference_summary, "student": student_summary,
                      "first_deviations": compare(reference, student)}
            results.append(result)
            print(f"{name}: oracle={reference_summary['finished']} student={student_summary['finished']} "
                  f"progress={student_summary['progress']:.4f} deviations={result['first_deviations']}", flush=True)
            write_summary()


if __name__ == "__main__":
    main()
