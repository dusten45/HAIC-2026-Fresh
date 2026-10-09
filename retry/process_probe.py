"""Separate-process/resource checks; results do not establish deployment eligibility."""

import argparse
import base64
import json
import os
from pathlib import Path
import selectors
import subprocess
import time

import cv2
import numpy as np

from retry.evaluate import check_window, digest, percentiles


class Participant:
    def __init__(self, python, variant="basic", fault="none", calibration=None):
        env = {**os.environ, "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}
        root = Path(__file__).resolve().parents[1]
        started = time.perf_counter()
        command = [str(python), "-m", "retry.isolated_worker", variant, fault]
        if calibration:
            command.extend([str(calibration["coefficient_speed_per_intensity"]), str(calibration["intercept"])])
        self.process = subprocess.Popen(command,
            cwd=root, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, bufsize=1, start_new_session=True)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.process.stdout, selectors.EVENT_READ)
        self.ready = self.read(10)
        self.import_init_s = time.perf_counter() - started
        assert self.ready["ready"] and not self.ready["simulator_imported"]

    def read(self, timeout):
        if not self.selector.select(timeout):
            self.close()
            raise TimeoutError("Participant response deadline")
        line = self.process.stdout.readline()
        if not line:
            raise RuntimeError(f"Participant exited {self.process.poll()}")
        return json.loads(line)

    def call(self, op, observation, timeout=5):
        request = {"op": op, "observation": base64.b64encode(observation.tobytes()).decode("ascii")}
        started = time.perf_counter()
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        response = self.read(timeout)
        return response, time.perf_counter() - started

    def close(self):
        if self.process.poll() is None:
            self.process.kill()
        self.process.wait(timeout=2)
        self.selector.close()
        for stream in [self.process.stdin, self.process.stdout, self.process.stderr]:
            stream.close()


def valid_action(response):
    action = np.asarray(response.get("action", []), dtype=np.float32)
    return action.shape == (3,) and bool(np.isfinite(action).all())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frame", type=Path, required=True)
    parser.add_argument("--variant", choices=["basic", "adaptive", "geometry", "clearance", "arc"])
    parser.add_argument("--calibration", type=Path)
    parser.add_argument("--normal-only", action="store_true")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    assert args.output.resolve().is_relative_to(args.plan.parent.resolve())
    args.output.mkdir(exist_ok=False)
    frame = cv2.imread(str(args.frame), cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
    observation = np.tile(frame, (4, 1, 1))
    python = Path(__file__).resolve().parents[1] / ".venv/bin/python"
    records = {}
    calibration = json.loads(args.calibration.read_text()) if args.calibration else None
    for variant in [args.variant] if args.variant else ["basic", "adaptive"]:
        check_window(plan)
        child = Participant(python, variant, calibration=calibration)
        try:
            _, reset_s = child.call("reset", observation)
            latencies, rss = [], []
            for _ in range(200):
                check_window(plan)
                response, elapsed = child.call("act", observation)
                assert valid_action(response)
                latencies.append(elapsed)
                rss.append(response["rss_mib"])
            records[variant] = {"init_ms": child.import_init_s * 1000, "reset_ms": reset_s * 1000,
                "act_with_ipc": percentiles(latencies), "child_peak_rss_mib": max(rss),
                "simulator_imported": child.ready["simulator_imported"], "normal_runtime_limits_observed": True}
        finally:
            child.close()
    faults = {}
    for fault in [] if args.normal_only else ["timeout", "memory", "crash", "invalid"]:
        check_window(plan)
        child = Participant(python, fault=fault)
        try:
            if fault == "invalid":
                invalid_streak = 0
                for _ in range(10):
                    response, _ = child.call("act", observation)
                    invalid_streak = 0 if valid_action(response) else invalid_streak + 1
                faults[fault] = {"retired_at_invalid_streak": invalid_streak, "passed": invalid_streak == 10}
            elif fault == "memory":
                response, _ = child.call("act", observation)
                faults[fault] = {"allocation_blocked": response["allocation_blocked"], "passed": response["allocation_blocked"]}
            else:
                try:
                    child.call("act", observation, timeout=0.15 if fault == "timeout" else 5)
                    faults[fault] = {"passed": False}
                except (TimeoutError, RuntimeError) as error:
                    faults[fault] = {"passed": True, "error": str(error), "process_reaped": child.process.poll() is not None}
        finally:
            child.close()
    assert all(r["passed"] for r in faults.values())
    result = {"policies": records, "faults": faults, "plan_sha256": digest(args.plan),
        "source_sha256": {p.name: digest(p) for p in Path(__file__).parent.glob("*.py")},
        "deployment_eligible": False,
        "remaining": ["Official process implementation/container unavailable for exact parity.",
            "RLIMIT_AS tests virtual address space, not official RSS/cgroup memory accounting.",
            "Repeated reset image tests IPC/resources, not driving quality or complete submission packaging."],
        "simulation_actions_consumed": 0}
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
