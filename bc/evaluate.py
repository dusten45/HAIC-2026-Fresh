"""Local-only paired oracle/student full-episode evaluation and deviation trace."""

import argparse
import hashlib
import os
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
from gymnasium.wrappers.time_limit import TimeLimit

from core.vendor.car_racing import CarRacing
from env_wrapper import CarEnvironment
from oracle.oracle_controller import OracleController
from oracle.oracle_runner import encode, vehicle_state


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


def rollout(track_id, seed, max_steps, policy=None, trace_path=None, samples=None):
    """Run original wrapped environment; policy sees only the actual image stack."""
    base = CarRacing(continuous=True, render_mode="rgb_array")
    env = CarEnvironment(TimeLimit(base, max_episode_steps=max_steps * 4 + 200),
                         skip_frames=4, no_operation=50)
    rows = []
    try:
        obs, info = env.reset(seed=seed, options={"track_id": track_id})
        teacher = OracleController(base, target_speed=12.0, avoid_obstacles=True)
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
            action = oracle_action if policy is None else np.asarray(policy.act(obs), dtype=np.float32)
            if samples is not None:
                samples.append((np.asarray(obs, dtype=np.float32).copy(), oracle_action.copy()))
            if action.shape != (3,) or not np.all(np.isfinite(action)) or not env.action_space.contains(action):
                raise ValueError(f"Invalid policy action at step {step}: {action}")
            distance = min(float(np.linalg.norm(np.asarray(pre_state["position"]) - point))
                           for point in obstacles)
            obs, reward, terminated, truncated, info = env.step(action)
            post_state = vehicle_state(base)
            row = {"step": step, "pre_state": pre_state, "post_state": post_state,
                   "oracle_action": oracle_action.tolist(), "action": action.tolist(),
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
    paired = []
    for row in student:
        index = row["step"]
        expected = reference[index] if index < len(reference) else None
        paired.append({"step": index, "pre_state": row["pre_state"],
                       "student_action": row["action"],
                       "teacher_on_student_action": row["oracle_action"],
                       "reference_action": expected["action"] if expected else None,
                       "reference_position": expected["pre_state"]["position"] if expected else None,
                       "teacher_diagnostics": row["teacher_diagnostics"],
                       "nearest_obstacle_distance": row["nearest_obstacle_distance"]})
    deviations = first_deviations(paired)
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
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--steer-checkpoint", type=Path,
                        help="Diagnostic: take steering from another observation-only BC policy")
    parser.add_argument("--track-ids", type=int, nargs="+", default=[1, 2, 3, 4, 5])
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument("--max-steps", type=int, default=2000)
    parser.add_argument("--split", choices=("train", "val", "test"), required=True)
    parser.add_argument("--collect-recovery", action="store_true",
                        help="Store oracle labels on visited student states on training roads")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if (args.max_steps < 1 or not args.seeds or len(set(args.seeds)) != len(args.seeds)
            or len(set(args.track_ids)) != len(args.track_ids)
            or any(t not in (1, 2, 3, 4, 5) for t in args.track_ids)
            or any(s < 0 or s > 0xFFFFFFFF for s in args.seeds)):
        parser.error("invalid track IDs, seeds or max steps")
    allowed = {"train": range(11, 31), "val": range(31, 36), "test": range(36, 41)}
    if any(seed not in allowed[args.split] for seed in args.seeds):
        parser.error("seeds do not belong to selected geometry split")
    if args.collect_recovery and args.split != "train":
        parser.error("recovery labels may only be collected on training geometry")
    if args.output.exists() or not args.output.parent.is_dir():
        parser.error("output must be a new directory with an existing parent")
    from bc.model import BCPolicy
    policy = BCPolicy.from_checkpoint(args.checkpoint)
    if args.steer_checkpoint is not None:
        controls_policy = policy
        steering_policy = BCPolicy.from_checkpoint(args.steer_checkpoint)

        class SplitHeads:
            def act(self, observation):
                action = controls_policy.act(observation)
                action[0] = steering_policy.act(observation)[0]
                return action

        policy = SplitHeads()
    args.output.mkdir()
    results = []
    for track_id in args.track_ids:
        for seed in args.seeds:
            name = f"track{track_id}_seed{seed}"
            reference, reference_summary = rollout(track_id, seed, args.max_steps,
                                                     trace_path=args.output / f"{name}.oracle.jsonl")
            samples = [] if args.collect_recovery else None
            student, student_summary = rollout(track_id, seed, args.max_steps, policy=policy,
                                                trace_path=args.output / f"{name}.student.jsonl",
                                                samples=samples)
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
            (args.output / "summary.json").write_text(encode({"checkpoint": str(args.checkpoint),
                "checkpoint_sha256": hashlib.sha256(args.checkpoint.read_bytes()).hexdigest(),
                "steer_checkpoint_sha256": (hashlib.sha256(args.steer_checkpoint.read_bytes()).hexdigest()
                                            if args.steer_checkpoint is not None else None),
                "split": args.split, "max_steps": args.max_steps, "frame_skip": 4, "warmup": 50,
                "thresholds": {"action": ACTION_THRESHOLDS, "position": POSITION_THRESHOLD},
                "episode_count": len(results), "finish_count": sum(r["student"]["finished"] for r in results),
                "reference_finish_count": sum(r["reference"]["finished"] for r in results),
                "road_count": len(results), "results": results}) + "\n")


if __name__ == "__main__":
    main()
