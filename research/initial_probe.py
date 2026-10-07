"""Bounded diagnostic of the unchanged starter; never a submission policy."""

import argparse
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import multiprocessing
import os
from pathlib import Path
import platform
import resource
import subprocess
import time

import numpy as np
from gymnasium.wrappers import TimeLimit

from agent import Agent
from core.vendor.car_racing import CarRacing, FPS
from env_wrapper import CarEnvironment
from local_runner import safe_act, safe_reset


MAX_STEPS = 256
FRAME_SKIP = 4
DEV_SEEDS = [42, 43, 44]


class NoOpProbe:
    """Stationary diagnostic control, not a candidate algorithm."""

    def act(self, observation):
        return np.zeros(3, dtype=np.float32)


def digest_json(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def latency_ms(samples):
    return {name: float(np.percentile(samples, percentile) * 1000)
            for name, percentile in [("p50", 50), ("p95", 95), ("max", 100)]}


def episode(case):
    track_id, seed, policy = case
    episode_start = time.perf_counter()
    cpu_start = time.process_time()
    env = CarEnvironment(TimeLimit(
        CarRacing(continuous=True, render_mode=None),
        max_episode_steps=MAX_STEPS * FRAME_SKIP + 200,
    ), skip_frames=FRAME_SKIP)
    agent = Agent() if policy == "starter" else NoOpProbe()
    try:
        reset_start = time.perf_counter()
        observation, _ = env.reset(seed=seed, options={"track_id": track_id})
        reset_wall_s = time.perf_counter() - reset_start
        simulation_start = env.unwrapped.t
        # Privileged metadata stays here; no policy receives it.
        geometry_sha256 = digest_json(env.unwrapped.track)
        obstacles_sha256 = digest_json([
            [list(spec.position), spec.radius]
            for spec in env.unwrapped.track_variables.obstacles
        ])
        assert observation.shape == (4, 84, 84)
        assert observation.dtype == np.float32
        assert env.observation_space.contains(observation)
        safe_reset(agent, observation)
        trajectory = hashlib.sha256(observation.tobytes())
        act_times, step_times = [], []
        reward_sum = 0.0
        collisions = 0
        last_info = {}
        terminated = truncated = False
        for _ in range(MAX_STEPS):
            started = time.perf_counter()
            action, valid = safe_act(agent, observation)
            act_times.append(time.perf_counter() - started)
            assert valid, "invalid action: stop diagnostic"
            started = time.perf_counter()
            observation, reward, terminated, truncated, last_info = env.step(action)
            step_times.append(time.perf_counter() - started)
            assert env.observation_space.contains(observation), "invalid observation"
            reward_sum += float(reward)
            collisions += int(last_info["collision"])
            trajectory.update(observation.tobytes())
            trajectory.update(np.asarray(action, dtype=np.float32).tobytes())
            trajectory.update(json.dumps([
                float(reward), bool(terminated), bool(truncated),
                last_info["progress"], last_info["damage"], last_info["finish_time_s"],
            ]).encode())
            if terminated or truncated:
                break
        raw_ticks = round((env.unwrapped.t - simulation_start) * FPS)
        finish_time = last_info.get("finish_time_s")
        reason = last_info.get("retire_reason")
        if finish_time is None and reason is None:
            reason = "playfield_exit" if terminated else "max_steps"
        return {
            "track_id": track_id, "seed": seed, "policy": policy, "split": "DEV",
            "agent_input": "pixel_only_float32_4x84x84",
            "geometry_sha256_diagnostic_only": geometry_sha256,
            "obstacles_sha256_diagnostic_only": obstacles_sha256,
            "trajectory_sha256": trajectory.hexdigest(),
            "steps": len(step_times), "raw_action_ticks": raw_ticks,
            "reset_raw_ticks_including_internal_initial_step": round(simulation_start * FPS),
            "reset_wall_s": reset_wall_s,
            "safe_act_ms": latency_ms(act_times),
            "env_step_ms": latency_ms(step_times),
            "env_step_wall_s": sum(step_times),
            "episode_wall_s": time.perf_counter() - episode_start,
            "episode_process_cpu_s": time.process_time() - cpu_start,
            "process_lifetime_peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
            "finished": finish_time is not None,
            "lap_time_ms": round((finish_time - simulation_start) * 1000) if finish_time is not None else None,
            "progress": last_info["progress"], "reward_diagnostic_only": reward_sum,
            "collision_action_intervals": collisions, "damage": last_info["damage"],
            "terminated": bool(terminated), "truncated": bool(truncated),
            "retire_reason": reason,
        }
    finally:
        env.close()


def text_if_available(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    report = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "environment_diagnostics_only_no_training_no_candidate_selection",
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_hashes": {str(path): hashlib.sha256(path.read_bytes()).hexdigest()
                          for path in [Path("agent.py"), Path("env_wrapper.py"), Path("local_runner.py"),
                                       *sorted(Path("core").rglob("*.py")), Path(__file__).relative_to(Path.cwd())]},
        "hardware": {
            "platform": platform.platform(), "python": platform.python_version(),
            "logical_cpus": os.cpu_count(), "affinity_cpus": sorted(os.sched_getaffinity(0)),
            "cgroup_cpu_max": text_if_available("/sys/fs/cgroup/cpu.max"),
            "cgroup_memory_max": text_if_available("/sys/fs/cgroup/memory.max"),
            "cpu_model": next((line.split(":", 1)[1].strip()
                               for line in Path("/proc/cpuinfo").read_text().splitlines()
                               if line.startswith("model name")), None),
        },
        "packages": {name: importlib.metadata.version(name)
                     for name in ["numpy", "gymnasium", "torch", "opencv-python", "box2d-py", "pygame"]},
        "settings": {"max_steps": MAX_STEPS, "frame_skip": FRAME_SKIP,
                     "physics_fps": FPS, "pixels_rendered": True,
                     "omp_num_threads": os.environ.get("OMP_NUM_THREADS"),
                     "openblas_num_threads": os.environ.get("OPENBLAS_NUM_THREADS")},
        "dev_contamination": {"all_track_ids_for_seeds": DEV_SEEDS,
                              "holdout_evaluations": 0, "sealed_evaluations": 0},
        "methodology_gate": "blocked_original_documents_unavailable",
    }
    # A fixed diagnostic schedule, registered before execution.
    cases = [(1, 42, "starter"), (1, 42, "starter"), (2, 42, "starter"),
             (1, 43, "starter"), (1, 44, "starter"), (1, 42, "noop")]
    report["episodes"] = [episode(case) for case in cases]
    first, repeat, alternate_track = report["episodes"][:3]
    report["checks"] = {
        "same_case_trajectory_identical": first["trajectory_sha256"] == repeat["trajectory_sha256"],
        "same_seed_different_track_id_geometry_identical":
            first["geometry_sha256_diagnostic_only"] == alternate_track["geometry_sha256_diagnostic_only"],
        "different_track_id_obstacles_differ":
            first["obstacles_sha256_diagnostic_only"] != alternate_track["obstacles_sha256_diagnostic_only"],
        "noop_offtrack_at_101": report["episodes"][-1]["steps"] == 101
                                and report["episodes"][-1]["retire_reason"] == "off_track",
    }
    if not report["checks"]["same_case_trajectory_identical"]:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
        raise RuntimeError("determinism failure; stop before throughput probe")
    report["throughput"] = []
    # Equal workload across worker counts. Timings include process startup and teardown.
    batch = [(1, 42, "starter"), (1, 43, "starter"),
             (1, 44, "starter"), (1, 42, "starter")]
    for workers in [1, 2, 4]:
        batch_start = time.perf_counter()
        with ProcessPoolExecutor(max_workers=workers,
                                 mp_context=multiprocessing.get_context("spawn")) as pool:
            episodes = list(pool.map(episode, batch))
        wall_s = time.perf_counter() - batch_start
        steps = sum(row["steps"] for row in episodes)
        report["throughput"].append({
            "workers": workers, "episodes": episodes, "wall_s_including_spawn": wall_s,
            "total_agent_steps": steps, "total_raw_action_ticks": sum(row["raw_action_ticks"] for row in episodes),
            "agent_steps_per_wall_s": steps / wall_s,
            "episode_cpu_s_sum": sum(row["episode_process_cpu_s"] for row in episodes),
        })
    report["total_wall_s"] = time.perf_counter() - started
    report["completed_utc"] = datetime.now(timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"output": str(args.output), "checks": report["checks"],
                      "total_wall_s": report["total_wall_s"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
