"""Budgeted three-arm DEV target-law test with exact physical prefix checks.

Private plans supply cases and frozen artifacts. Seeds and simulator diagnostics
remain in this harness; the isolated participant receives current pixels only.
"""

import argparse
import hashlib
import json
from pathlib import Path
import time
import traceback

import numpy as np

from retry.diagnose import Budget, make_env, state
from retry.evaluate import check_window
from retry.fresh_dev_pair import digest_track
from retry.process_probe import Participant, valid_action


def load_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--mode", choices=["roi", "distance", "slow"], required=True)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    cfg = plan["cases"][args.case]
    role = args.case + "-" + args.mode
    output = args.plan.parent / "runs" / role
    output.mkdir(parents=True, exist_ok=False)
    root = Path(__file__).resolve().parents[1]
    package = Path(plan["package"])
    for name, expected in plan["member_sha256"].items():
        assert sha(package / name) == expected
    for name, expected in plan["source_sha256"].items():
        assert sha(root / name) == expected
    reference = cfg.get("reference", {})
    for key, expected in reference.get("sha256", {}).items():
        assert sha(reference[key]) == expected
    source = None
    if "pixels_actions" in reference:
        with np.load(reference["pixels_actions"]) as archive:
            source = {key: archive[key] for key in archive.files}
    metrics = load_rows(reference["metrics"]) if "metrics" in reference else None
    diagnostics = load_rows(reference["diagnostics"]) if "diagnostics" in reference else None
    policies = load_rows(reference["policy"]) if "policy" in reference else None
    traces = load_rows(reference["trace"]) if "trace" in reference else None
    prefix = cfg["prefix"]
    budget = Budget(args.plan, role)
    env = child = None
    steps = 0
    result = {"case": args.case, "mode": args.mode, "technical_valid": False,
              "prefix_actions": prefix, "planned_horizon": cfg["horizon"],
              "privileged_inputs": False, "future_actions_copied": False}
    started = time.perf_counter()
    latencies = []
    max_counter = 0
    cap_count = 0
    unselected_exact = 0
    first_damage = None
    prefix_state = None
    observations, actions = [], []
    try:
        child = Participant(root / ".venv/bin/python", package_root=package,
                            command_override=[str(root / ".venv/bin/python"),
                                              str(root / "retry/distance_target_worker.py"),
                                              str(package), args.mode, cfg["prefix_kind"]])
        env = make_env()
        reset_start = time.perf_counter()
        observation, _ = env.reset(seed=cfg["seed"], options={"track_id": cfg["track_id"]})
        result["reset_s"] = time.perf_counter() - reset_start
        result["geometry_sha256"] = digest_track(env.unwrapped.track)
        if cfg.get("geometry_sha256"):
            assert result["geometry_sha256"] == cfg["geometry_sha256"]
        if cfg.get("initial_observation_sha256"):
            assert hashlib.sha256(observation.tobytes()).hexdigest() == cfg["initial_observation_sha256"]
        child.call("reset", observation)
        if prefix == 0:
            prefix_state = state(env)
            child.call("activate", observation)
        with (output / "trace.jsonl").open("w") as tf, (output / "policy.jsonl").open("w") as pf:
            while steps < cfg["horizon"]:
                check_window(plan)
                before = state(env)
                prehash = hashlib.sha256(observation.tobytes()).hexdigest()
                response, elapsed = child.call("act", observation)
                latencies.append(elapsed)
                assert valid_action(response)
                action = np.asarray(response["action"], dtype=np.float32)
                assert np.all(action >= [-1, 0, 0]) and np.all(action <= [1, 1, 1])
                index = steps
                exact_reference = index < prefix or (args.mode == "roi" and cfg["prefix_kind"] == "roi")
                if exact_reference and source is not None and index < len(source["actions"]):
                    np.testing.assert_array_equal(action, source["actions"][index])
                    if "observations" in source:
                        np.testing.assert_array_equal(observation, source["observations"][index])
                    elif index < prefix:
                        np.testing.assert_array_equal(np.rint(observation[-1] * 255).astype(np.uint8), source["frames"][index])
                if index < prefix and diagnostics:
                    assert before == diagnostics[index]["state_before"]
                if index < prefix and policies:
                    old = policies[index]["policy_state_after"]
                    assert response["policy_state_after"] == {
                        "previous_steer": old["controller"]["attributes"]["previous_steer"],
                        "hazards": old["hazards"],
                        "previous_image_sha256": old["previous_image"]["sha256"]}
                features = response["features"]
                shadow = np.asarray(features.get("roi_shadow_action", action), dtype=np.float32)
                assert action[0] == shadow[0]
                if index >= prefix:
                    if features.get("cap_active"):
                        cap_count += 1
                    else:
                        np.testing.assert_array_equal(action, shadow)
                        unselected_exact += 1
                observations.append(observation.copy())
                actions.append(action.copy())
                observation, _, ended, truncated, info = budget.step(env, action)
                steps += 1
                after = state(env)
                row = {"step": steps, "progress": info["progress"], "damage": info["damage"],
                       "off_track_counter": env.off_track_counter, "collision": info["collision"],
                       "terminated": ended, "truncated": truncated, "retire_reason": info["retire_reason"]}
                if exact_reference and metrics and index < len(metrics):
                    assert row == metrics[index]
                if index < prefix and diagnostics:
                    assert after == diagnostics[index]["state_after"]
                if index < prefix and traces:
                    assert before == traces[index]["state_before"]
                    assert after == traces[index]["state_after"]
                if first_damage is None and row["damage"] > 0:
                    first_damage = steps
                max_counter = max(max_counter, row["off_track_counter"])
                tf.write(json.dumps({**row, "state_before": before, "state_after": after,
                                     "observation_sha256": prehash}) + "\n")
                tf.flush()
                pf.write(json.dumps({"step": steps, **response}) + "\n")
                pf.flush()
                if steps == prefix:
                    prefix_state = after
                    activated, _ = child.call("activate", observation)
                    result["branch_boundary"] = {"physical_state": after,
                        "observation_sha256": hashlib.sha256(observation.tobytes()).hexdigest(),
                        "policy_state": activated["policy_state"]}
                if ended or truncated:
                    break
        result.update(technical_valid=True, steps=steps, **{k: row[k] for k in
                      ("progress", "damage", "terminated", "truncated", "retire_reason")},
                      completed=env.unwrapped.finish_time_s is not None,
                      censored=not (row["terminated"] or row["truncated"]),
                      first_damage_step=first_damage, max_off_track_counter=max_counter,
                      prefix_tiles=prefix_state["tiles"], prefix_damage=prefix_state["damage"],
                      progress_delta_tiles=after["tiles"] - prefix_state["tiles"],
                      damage_delta=after["damage"] - prefix_state["damage"],
                      cap_active_actions=cap_count, unselected_shadow_exact_actions=unselected_exact,
                      lap_ms=(None if env.unwrapped.finish_time_s is None else
                              round((env.unwrapped.finish_time_s - 1.02) * 1000)),
                      actor_latency_p95_s=float(np.percentile(latencies, 95)),
                      policy_modules=child.ready["policy_modules"])
    except Exception as error:
        result.update(error=repr(error), traceback=traceback.format_exc(), steps=steps)
    finally:
        result["charged_actions"] = json.loads(budget.path.read_text())["stages"].get(role, 0)
        result["wall_s"] = time.perf_counter() - started
        if observations:
            np.savez_compressed(output / "pixels-actions.npz", observations=np.asarray(observations), actions=np.asarray(actions))
        (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
        if child:
            child.close()
        if env:
            env.close()
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
