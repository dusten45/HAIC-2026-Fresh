"""DEV-only privileged diagnostics, explicitly separate from participant policies."""

import argparse
import copy
import fcntl
import hashlib
import json
import math
from pathlib import Path
import pickle
import resource
import time

import numpy as np
from gymnasium.wrappers import TimeLimit

from core.vendor.car_racing import CarRacing, TRACK_WIDTH, ZOOM, SCALE
from env_wrapper import CarEnvironment
from retry.evaluate import check_window, digest, observation_contract
from retry.pixel_agent import PixelAgent


SX, SY = ZOOM * SCALE * 84 / 1000, ZOOM * SCALE * 84 / 800


class BudgetStop(RuntimeError):
    pass


class Budget:
    def __init__(self, plan_path, stage):
        self.plan = json.loads(plan_path.read_text())
        self.path = (plan_path.parent / self.plan.get("ledger_relative_path", "budget.json")).resolve()
        assert self.path.is_relative_to(plan_path.parent.parent.resolve()), "Budget ledger must stay in private research area"
        self.stage = stage
        with self.path.open("a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            handle.seek(0)
            if not handle.read():
                json.dump({"started_epoch": time.time(), "actions": 0, "stages": {}}, handle)

    def step(self, env, action):
        try:
            check_window(self.plan)
        except RuntimeError as error:
            raise BudgetStop(str(error)) from error
        with self.path.open("r+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            ledger = json.load(handle)
            if time.time() - ledger["started_epoch"] >= self.plan["max_experiment_wall_s"]:
                raise BudgetStop("Wall budget exhausted")
            if ledger["actions"] >= self.plan["max_actions"]:
                raise BudgetStop("Global action budget exhausted")
            if ledger["stages"].get(self.stage, 0) >= self.plan["stage_budgets"][self.stage]:
                raise BudgetStop("Stage action budget exhausted")
            ledger["actions"] += 1
            ledger["stages"][self.stage] = ledger["stages"].get(self.stage, 0) + 1
            handle.seek(0)
            json.dump(ledger, handle)
            handle.truncate()
            handle.flush()
        return env.step(action)


class HealthyEffectsEnvironment(CarEnvironment):
    """Counterfactual only: collision counts/retirement retained, physics effects removed."""
    def _apply_damage_effects(self):
        self.unwrapped.car.set_damage_effects(1.0, 1.0, 1.0)


def make_env(healthy=False):
    wrapper = HealthyEffectsEnvironment if healthy else CarEnvironment
    return wrapper(TimeLimit(CarRacing(continuous=True, render_mode=None), max_episode_steps=8200))


def state(env):
    raw = env.unwrapped
    hull = raw.car.hull
    return {"position": list(hull.position), "velocity": list(hull.linearVelocity),
        "angle": float(hull.angle), "angular_velocity": float(hull.angularVelocity),
        "wheels": [[float(w.angle), float(w.omega), float(w.joint.angle), float(w.gas), float(w.brake)] for w in raw.car.wheels],
        "time": raw.t, "tiles": raw.tile_visited_count, "damage": env.damage.damage,
        "off_track_counter": env.off_track_counter}


def fingerprint(observation):
    return hashlib.sha256(observation.tobytes()).hexdigest()


def truth_features(env):
    raw = env.unwrapped
    hull = raw.car.hull
    track = np.asarray(raw.track)
    position = np.asarray(hull.position)
    nearest = int(np.argmin(np.sum((track[:, 2:4] - position) ** 2, axis=1)))
    beta = float(track[nearest, 1])
    lateral = float(np.dot(position - track[nearest, 2:4], [math.cos(beta), math.sin(beta)]))
    heading = float((hull.angle - beta + math.pi) % (2 * math.pi) - math.pi)
    # Projection is derived from the unchanged renderer, never fed to a deployed policy.
    points = np.array([hull.GetLocalPoint(tuple(track[(nearest + i) % len(track), 2:4])) for i in range(-2, 38)])
    centers = {}
    for row in [52, 36]:
        forward = (63 - row) / SY
        candidates = []
        for i, (a, b) in enumerate(zip(points[:-1], points[1:])):
            if (a[1] - forward) * (b[1] - forward) <= 0 and abs(b[1] - a[1]) > 1e-8:
                x = a[0] + (b[0] - a[0]) * (forward - a[1]) / (b[1] - a[1])
                candidates.append((i, float(42 + SX * x)))
        centers[str(row)] = candidates[0][1] if candidates else None
    obstacles = [[*map(float, hull.GetLocalPoint(tuple(o.position))), float(o.fixtures[0].shape.radius)] for o in raw.obstacles]
    return {"nearest_tile": nearest, "lateral_m": lateral, "heading_error_rad": heading,
        "speed_m_s": float(np.linalg.norm(hull.linearVelocity)), "centers": centers,
        "forward_points_local": points.tolist(), "obstacles_local": obstacles,
        "nearest_obstacle_distance_m": min(math.hypot(x, y) for x, y, _ in obstacles)}


def pixel_features(policy, observation):
    image = observation[-1]
    centers = policy.road_centers(image)
    near = far = None
    if centers:
        rows, xs = np.array(centers).T
        near = float(xs[np.argmin(abs(rows - 52))])
        far = float(xs[np.argmin(abs(rows - 36))])
    speed_bar = float(np.sum(image[74:82, 10:13] > 0.75)) / 3
    speed_integral = float(image[74:83, 9:14].sum())
    return {"near_x": near, "far_x": far, "row_count": len(centers),
        "centers": centers, "hud_speed_legacy_m_s": speed_bar / 0.042,
        "hud_white_integral": speed_integral}


def trace(case, variant, budget, output, max_steps=400, healthy=False, factory=None, input_source="pixels", replay_source=None, prefix=0):
    check_window(budget.plan)
    env = make_env(healthy)
    policy = PixelAgent(adaptive=variant == "adaptive") if factory is None else factory()
    rows, frames, actions = [], [], []
    start = time.perf_counter()
    try:
        reset_start = time.perf_counter()
        observation, _ = env.reset(seed=case["seed"], options={"track_id": case["track_id"]})
        reset_s = time.perf_counter() - reset_start
        if replay_source is not None:
            recorded = np.load(replay_source / "pixels-actions.npz")["actions"]
            expected = [json.loads(line) for line in (replay_source / "trace.jsonl").read_text().splitlines()]
            for i in range(prefix):
                observation, _, ended, truncated, _ = budget.step(env, recorded[i])
                assert not (ended or truncated)
            assert fingerprint(observation) == expected[prefix - 1]["observation_sha256_after"]
            assert state(env) == expected[prefix - 1]["state_after"]
        policy.reset(observation)
        if replay_source is not None:
            policy.controller.previous_steer = float(recorded[prefix - 1][0])
        frames.append(np.rint(observation[-1] * 255).astype(np.uint8))
        local_stop = None
        for step in range(1, max_steps + 1):
            observation_contract(observation)
            before = state(env)
            truth = truth_features(env)
            pixels = pixel_features(PixelAgent(), observation)
            if input_source == "oracle":
                action = policy.act_features(truth)
            else:
                action = np.asarray(policy.act(observation), dtype=np.float32)
            assert action.shape == (3,) and np.isfinite(action).all()
            assert np.all(action >= [-1, 0, 0]) and np.all(action <= [1, 1, 1])
            try:
                observation, reward, terminated, truncated, info = budget.step(env, action)
            except BudgetStop as error:
                local_stop = str(error)
                break
            observation_contract(observation)
            rows.append({"step": step, "truth": truth, "pixels": pixels, "state_before": before,
                "state_after": state(env), "observation_sha256_after": fingerprint(observation),
                "action": action.tolist(), "reward": reward, "progress": info["progress"],
                "damage": info["damage"], "collision": info["collision"],
                "off_track_counter": env.off_track_counter, "terminated": terminated,
                "truncated": truncated, "retire_reason": info["retire_reason"]})
            actions.append(action)
            frames.append(np.rint(observation[-1] * 255).astype(np.uint8))
            if terminated or truncated:
                break
        finish = env.unwrapped.finish_time_s
        summary = {**case, "variant": variant, "input_source": input_source, "healthy_effects_counterfactual": healthy,
            "completed": finish is not None, "progress": env._calculate_progress(), "damage": env.damage.damage,
            "replay_prefix_actions": prefix, "exact_prefix_verified": replay_source is not None,
            "steps": len(rows), "reset_s": reset_s, "wall_s": time.perf_counter() - start,
            "lap_ms": round((finish - 1.02) * 1000) if finish else None,
            "retire_reason": None if finish is not None else local_stop or (rows[-1]["retire_reason"] or ("raw_terminated" if rows[-1]["terminated"] else "budget") if rows else "no_actions"),
            "RSS_mib_harness": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024}
        output.mkdir(exist_ok=False)
        (output / "trace.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))
        np.savez_compressed(output / "pixels-actions.npz", frames=np.asarray(frames), actions=np.asarray(actions))
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        print(json.dumps(summary), flush=True)
        return rows, summary
    finally:
        env.close()
        if hasattr(policy, "close"):
            policy.close()


def persistent_onset(rows, predicate, length=3):
    streak = 0
    for row in rows:
        streak = streak + 1 if predicate(row) else 0
        if streak >= length:
            return row["step"] - length + 1
    return None


def onsets(rows):
    def pixel_bad(row):
        far = row["truth"]["centers"]["36"]
        if far is None or not 3 <= far <= 81:
            return False
        guessed = row["pixels"]["far_x"]
        return guessed is None or abs(guessed - far) > 6
    return {"lateral": persistent_onset(rows, lambda r: abs(r["truth"]["lateral_m"]) > 0.75 * TRACK_WIDTH),
        "heading": persistent_onset(rows, lambda r: abs(r["truth"]["heading_error_rad"]) > 0.7),
        "stagnation": next((r["step"] for r in rows if r["off_track_counter"] >= 10), None),
        "collision": next((r["step"] for r in rows if r["collision"]), None),
        "pixel_far_error": persistent_onset(rows, pixel_bad),
        "hud_speed_error": persistent_onset(rows, lambda r: abs(r["pixels"]["hud_speed_legacy_m_s"] - r["truth"]["speed_m_s"]) > 10)}


def replay_branch(case, source, prefix, budget, intervention):
    data = np.load(source / "pixels-actions.npz")
    rows = [json.loads(line) for line in (source / "trace.jsonl").read_text().splitlines()]
    env = make_env()
    start = time.perf_counter()
    try:
        reset_start = time.perf_counter()
        obs, _ = env.reset(seed=case["seed"], options={"track_id": case["track_id"]})
        reset_s = time.perf_counter() - reset_start
        replay_start = time.perf_counter()
        for i in range(prefix):
            obs, _, ended, truncated, _ = budget.step(env, data["actions"][i])
            assert not (ended or truncated)
        replay_s = time.perf_counter() - replay_start
        expected = rows[prefix - 1]
        assert fingerprint(obs) == expected["observation_sha256_after"], "Replay observation diverged"
        assert state(env) == expected["state_after"], "Replay physical state diverged"
        clone_tests = {}
        if intervention == "recorded":
            for name, clone in [("deepcopy", copy.deepcopy), ("pickle", lambda e: pickle.loads(pickle.dumps(e)))]:
                cloned = None
                started = time.perf_counter()
                try:
                    cloned = clone(env)
                    identical = state(cloned) == state(env) and np.array_equal(cloned.stack_state, obs)
                    clone_tests[name] = {"faithful": bool(identical), "wall_ms": (time.perf_counter() - started) * 1000}
                except Exception as error:
                    clone_tests[name] = {"faithful": False, "error": f"{type(error).__name__}: {error}", "wall_ms": (time.perf_counter() - started) * 1000}
                finally:
                    if cloned is not None:
                        cloned.close()
        rollout_start = time.perf_counter()
        steps = 0
        for i in range(prefix, min(prefix + 64, len(data["actions"]))):
            action = data["actions"][i] if intervention == "recorded" else np.array([data["actions"][i][0], 0, 0.15], dtype=np.float32)
            obs, _, ended, truncated, _ = budget.step(env, action)
            steps += 1
            if intervention == "recorded":
                assert fingerprint(obs) == rows[i]["observation_sha256_after"], "Recorded rollout observation diverged"
                assert state(env) == rows[i]["state_after"], "Recorded rollout physical state diverged"
            if ended or truncated:
                break
        rollout_s = time.perf_counter() - rollout_start
        return {**case, "prefix_actions": prefix, "intervention": intervention, "prefix_observation_and_state_exact": True,
            "reset_s": reset_s, "prefix_replay_s": replay_s, "rollout_s": rollout_s, "rollout_steps": steps,
            "branch_total_s": time.perf_counter() - start, "overhead_to_rollout_ratio": (reset_s + replay_s) / rollout_s if rollout_s else None,
            "progress": env._calculate_progress(), "damage": env.damage.damage, "snapshot_tests": clone_tests}
    finally:
        env.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--phase", choices=["traces", "damage", "p2"], required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    output = args.plan.parent / args.phase
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for source in Path(__file__).parent.glob("*.py"):
        (sources / source.name).write_bytes(source.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "privilege": "Evaluator/oracle and healthy-effects arms diagnostic only; not official scores or deployment policy."}, indent=2) + "\n")
    stage = {"traces": "failure_traces", "damage": "damage_interventions", "p2": "replay_branches"}[args.phase]
    budget = Budget(args.plan, stage)
    records = []
    if args.phase == "traces":
        for index, case in enumerate(plan["cases"]):
            for variant in ["basic", "adaptive"]:
                rows, summary = trace(case, variant, budget, output / f"case-{index}-{variant}")
                records.append({**summary, "onsets": onsets(rows)})
    elif args.phase == "damage":
        for index in [0, 1, 3]:
            case = plan["cases"][index]
            source = args.plan.parent / "traces" / f"case-{index}-basic"
            original = [json.loads(line) for line in (source / "trace.jsonl").read_text().splitlines()]
            rows, summary = trace(case, "basic", budget, output / f"case-{index}-healthy", max_steps=300, healthy=True)
            first = next((r["step"] for r in original if r["collision"]), len(original) + 1)
            assert all(a["state_before"] == b["state_before"] and a["observation_sha256_after"] == b["observation_sha256_after"] for a, b in zip(original[:first], rows[:first]))
            base = original[min(300, len(original)) - 1]
            records.append({**summary, "first_collision_step": first if first <= len(original) else None,
                "identical_pre_collision_prefix": True, "reference_progress_at_same_cap": base["progress"],
                "progress_gain": summary["progress"] - base["progress"],
                "retirement_delay_steps": summary["steps"] - min(len(original), 300)})
    else:
        for index in [0, 1, 3]:
            case = plan["cases"][index]
            source = args.plan.parent / "traces" / f"case-{index}-basic"
            rows = [json.loads(line) for line in (source / "trace.jsonl").read_text().splitlines()]
            events = onsets(rows)
            first = min(x for name, x in events.items() if name in ["lateral", "heading", "collision", "stagnation"] and x is not None)
            prefix = max(1, min(128, first - 1))
            for intervention in ["recorded", "brake"]:
                record = replay_branch(case, source, prefix, budget, intervention)
                records.append(record)
                print(json.dumps(record), flush=True)
    (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")


if __name__ == "__main__":
    main()
