"""Local contract/cost harness. Research metadata stays outside the repository.

Run as `python -m retry.evaluate --plan PRIVATE_JSON --output PRIVATE_DIR`.
The policy receives only observations; environment metadata is evaluator-only.
"""

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import time

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import cv2
import numpy as np
from gymnasium.wrappers import TimeLimit

from core.vendor.car_racing import CarRacing, FPS
from env_wrapper import CarEnvironment
from local_runner import safe_act, safe_reset
from retry.pixel_agent import PixelAgent, StraightAgent


ROOT = Path(__file__).resolve().parents[1]
ENV_FILES = ["env_wrapper.py", "damage.py", *[
    str(p.relative_to(ROOT)) for p in sorted((ROOT / "core").rglob("*.py"))
]]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc)


def check_window(plan):
    current = now()
    if current < dt.datetime.fromisoformat(plan["start_utc"]):
        raise RuntimeError("Authorization has not started")
    if current >= dt.datetime.fromisoformat(plan["deadline_utc"]):
        raise RuntimeError("Authorization expired; no new simulation step allowed")


def window_open(plan):
    return (dt.datetime.fromisoformat(plan["start_utc"]) <= now()
            < dt.datetime.fromisoformat(plan["deadline_utc"]))


def percentiles(values):
    if not values:
        return {"count": 0, "median_ms": None, "p95_ms": None, "max_ms": None}
    a = np.asarray(values) * 1000
    return {"count": len(a), "median_ms": float(np.median(a)),
            "p95_ms": float(np.percentile(a, 95)), "max_ms": float(a.max())}


def observation_contract(observation):
    assert observation.shape == (4, 84, 84)
    assert observation.dtype == np.float32
    assert np.isfinite(observation).all()
    assert observation.min() >= 0 and observation.max() <= 1


class TimedAgent:
    def __init__(self, policy):
        self.policy = policy
        self.calls = []

    def reset(self, observation):
        self.policy.reset(observation)

    def act(self, observation):
        started = time.perf_counter()
        try:
            return self.policy.act(observation)
        finally:
            self.calls.append(time.perf_counter() - started)


def run_case(case, policy_name, plan, max_steps, snapshot=None):
    check_window(plan)
    initialized = time.perf_counter()
    policy = StraightAgent() if policy_name == "straight_gas" else PixelAgent(
        adaptive=policy_name == "pixel_adaptive")
    agent = TimedAgent(policy)
    init_s = time.perf_counter() - initialized
    env = CarEnvironment(TimeLimit(CarRacing(continuous=True, render_mode=None),
        max_episode_steps=plan["max_steps"] * plan["frame_skip"] + 200),
        skip_frames=plan["frame_skip"])
    reset_s = agent_reset_s = 0.0
    env_times, call_times, obs_times = [], [], []
    invalid_total = invalid_streak = steps = 0
    reward_sum = 0.0
    terminated = truncated = False
    local_reason = None
    telemetry = []
    wall_start = time.perf_counter()
    try:
        check_window(plan)
        started = time.perf_counter()
        observation, info = env.reset(seed=case["seed"], options={"track_id": case["track_id"]})
        reset_s = time.perf_counter() - started
        observation_contract(observation)
        assert all(np.array_equal(observation[0], o) for o in observation[1:])
        start_time = env.unwrapped.t
        # CarRacing.reset itself advances one tick, followed by 50 warmup ticks.
        assert abs(start_time - 51 / FPS) < 1e-8
        if snapshot:
            cv2.imwrite(str(snapshot), np.rint(observation[-1] * 255).astype(np.uint8))
        started = time.perf_counter()
        safe_reset(agent, observation)
        agent_reset_s = time.perf_counter() - started
        while steps < max_steps and not (terminated or truncated):
            if not window_open(plan):
                local_reason = "authorization_expired"
                break
            started = time.perf_counter()
            action, valid = safe_act(agent, observation)
            call_times.append(time.perf_counter() - started)
            invalid_total += int(not valid)
            invalid_streak = 0 if valid else invalid_streak + 1
            if invalid_streak >= 10:
                local_reason = "invalid_action"
                break
            previous = observation
            before_t = env.unwrapped.t
            if not window_open(plan):
                local_reason = "authorization_expired"
                break
            started = time.perf_counter()
            observation, reward, terminated, truncated, info = env.step(action)
            env_times.append(time.perf_counter() - started)
            started = time.perf_counter()
            observation_contract(observation)
            assert np.array_equal(observation[:3], previous[1:])
            tick_count = round((env.unwrapped.t - before_t) * FPS)
            assert 1 <= tick_count <= plan["frame_skip"]
            if not (terminated or truncated):
                assert tick_count == plan["frame_skip"]
            obs_times.append(time.perf_counter() - started)
            steps += 1
            reward_sum += reward
            if steps == 1 or steps % 25 == 0 or terminated or truncated:
                telemetry.append({"step": steps, "sim_time_s": env.unwrapped.t,
                    "progress": float(info["progress"]), "damage": float(info["damage"]),
                    "action": action.tolist(), "reward": reward,
                    "off_track_counter": env.off_track_counter})
        finish = env.unwrapped.finish_time_s
        completed = finish is not None
        if completed:
            assert env.unwrapped.finish_qualified_time_s is not None
            assert abs(finish * FPS - round(finish * FPS)) < 1e-6
        reason = local_reason or info.get("retire_reason")
        if not completed and reason is None:
            reason = "off_track" if terminated else "max_steps" if truncated or steps >= max_steps else "unknown"
        elapsed = env.unwrapped.t - start_time
        raw_frames = round(elapsed * FPS)
        env_wall = sum(env_times)
        return {**case, "policy": policy_name, "completed": completed,
            "progress": env._calculate_progress(), "finish_qualified": env.unwrapped.finish_qualified_time_s is not None,
            "finish_time_s": finish, "lap_time_ms": round((finish - start_time) * 1000) if completed else None,
            "retire_reason": reason, "terminated": terminated, "truncated": truncated,
            "steps": steps, "raw_frames": raw_frames, "start_time_s": start_time,
            "simulation_elapsed_s": elapsed, "reward_diagnostic": reward_sum,
            "damage": env.damage.damage, "invalid_actions": invalid_total,
            "init_ms": init_s * 1000, "reset_ms": reset_s * 1000,
            "agent_reset_ms": agent_reset_s * 1000, "wall_s": time.perf_counter() - wall_start,
            "env_step": percentiles(env_times), "policy_act": percentiles(agent.calls),
            "safe_act": percentiles(call_times), "observation_audit": percentiles(obs_times),
            "raw_frames_per_s_env": raw_frames / env_wall if env_wall else None,
            "rss_peak_mib_process": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024,
            "telemetry": telemetry}
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--policy", choices=["straight_gas", "pixel_basic", "pixel_adaptive"], default="straight_gas")
    parser.add_argument("--split", choices=["DEV", "HOLDOUT", "SEALED"], default="DEV")
    parser.add_argument("--case-limit", type=int)
    parser.add_argument("--max-steps", type=int)
    parser.add_argument("--snapshot", action="store_true")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    assert args.output.resolve().is_relative_to(args.plan.parent.resolve()), "Results must stay in the private plan directory"
    assert not args.output.exists(), "Output directory already exists"
    steps = args.max_steps or plan["max_steps"]
    assert 0 < steps <= plan["max_steps"]
    if steps > 1200:
        gates = json.loads((args.plan.parent / "gate-cost.json").read_text())
        assert gates["G0"] is True and gates["G1"] is True
        assert gates["plan_sha256"] == digest(args.plan)
    if args.split != "DEV":
        gate = "G2" if args.split == "HOLDOUT" else "G3"
        decision = json.loads((args.plan.parent / "promotion.json").read_text())
        assert decision[gate] is True, f"Upstream {gate} must pass first"
        assert decision["policy"] == args.policy
        assert decision["policy_sha256"] == digest(ROOT / "retry/pixel_agent.py")
        assert not args.case_limit and not args.max_steps, "Protected split requires full locked evaluation"
        # Refuse a second protected-split evaluation, including after a crash.
        with (args.plan.parent / f"{args.split}.opened").open("x") as handle:
            handle.write(now().isoformat() + "\n")
    args.output.mkdir(parents=True, exist_ok=False)
    cases = plan["split"][args.split]
    if args.case_limit:
        assert args.case_limit > 0
        cases = cases[:args.case_limit]
    # Verify original simulator files rather than trusting local modifications.
    for name in ENV_FILES:
        original = subprocess.check_output(["git", "show", f'{plan["base"]}:{name}'], cwd=ROOT)
        assert hashlib.sha256(original).hexdigest() == digest(ROOT / name), name
    metadata = {"plan_sha256": digest(args.plan), "started_at": now().isoformat(),
        "split": args.split, "policy": args.policy, "max_steps": steps,
        "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in
            [ROOT / "retry/evaluate.py", ROOT / "retry/pixel_agent.py", *[ROOT / f for f in ENV_FILES]]},
        "base": plan["base"], "frame_skip": plan["frame_skip"],
        "measurement_note": "RSS includes evaluator; safe_act thread guard matches local_runner, not official process isolation."}
    (args.output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    rows = []
    with (args.output / "cases.jsonl").open("x") as log:
        for index, case in enumerate(cases):
            if not window_open(plan):
                break
            row = run_case(case, args.policy, plan, steps,
                args.output / f"reset-{index}.png" if args.snapshot else None)
            log.write(json.dumps(row) + "\n")
            log.flush()
            rows.append(row)
            print(json.dumps({k: row[k] for k in ["track_id", "policy", "completed", "progress", "steps", "damage", "retire_reason", "wall_s"]}), flush=True)
            if row["retire_reason"] == "authorization_expired":
                break
    summary = {"completed": sum(row["completed"] for row in rows), "cases": len(rows),
        "planned_cases": len(cases), "authorization_expired": not window_open(plan),
        "median_progress": float(np.median([row["progress"] for row in rows])) if rows else None,
        "median_damage": float(np.median([row["damage"] for row in rows])) if rows else None,
        "invalid_actions": sum(row["invalid_actions"] for row in rows),
        "total_wall_s": sum(row["wall_s"] for row in rows), "finished_at": now().isoformat()}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
