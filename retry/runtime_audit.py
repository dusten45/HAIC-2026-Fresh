"""Audit remaining local execution guarantees on the unchanged reference ZIP."""

import argparse
import importlib.util
import json
import os
from pathlib import Path
import signal
import time

import numpy as np

from retry.connectivity_probe import verify_reference
from retry.evaluate import check_window, digest, percentiles
from retry.process_probe import Participant, valid_action
from retry.submission_probe import stack, validate_source


class ExternalGuard(RuntimeError):
    pass


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--mode", choices=["fault", "stream"], required=True)
    parser.add_argument("--adapter", type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    freeze = verify_reference(plan, args.plan.parent)
    package = (args.plan.parent / plan["baseline_package"] / "extracted").resolve()
    root = Path(__file__).resolve().parents[1]
    participant = Participant
    if args.adapter:
        spec = importlib.util.spec_from_file_location("trusted_old_transport", args.adapter)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Preserve the original wrapper's repository lookup while loading its
        # unchanged source snapshot. This never alters participant policy input.
        module.__file__ = str(root / "retry/process_probe.py")
        participant = module.Participant
    args.output.mkdir(exist_ok=False)
    result = {"plan_sha256": digest(args.plan), "baseline_zip_sha256": freeze["zip_sha256"],
        "adapter_sha256": digest(args.adapter or root / "retry/process_probe.py"),
        "new_simulation_actions": 0, "official_server_parity_verified": False,
        "official_RSS_cgroup_enforcement_verified": False}
    child = participant(root / ".venv/bin/python", package_root=package)
    try:
        if args.mode == "fault":
            obs = np.zeros((4, 84, 84), np.float32)
            child.call("reset", obs)
            os.kill(child.process.pid, signal.SIGSTOP)
            signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(ExternalGuard("External eight-second bound")))
            signal.alarm(8)
            started = time.perf_counter()
            try:
                child.call("act", obs, timeout=5)
                outcome = "unexpected_response"
            except TimeoutError:
                outcome = "whole_call_timeout"
            except ExternalGuard:
                outcome = "external_guard_only"
            result.update(outcome=outcome, elapsed_s=time.perf_counter() - started,
                five_second_transport_guard_pass=outcome == "whole_call_timeout")
        else:
            source = (args.plan.parent / "../stage6/full-DEV/case-1").resolve()
            data = np.load(source / "pixels-actions.npz")
            frames, actions = data["frames"], data["actions"]
            latency, rss, resets = [], [], []
            for _ in range(2):
                check_window(plan)
                response, elapsed = child.call("reset", stack(frames, 0))
                assert response["ok"]
                resets.append(elapsed)
                for i, expected in enumerate(actions):
                    check_window(plan)
                    response, elapsed = child.call("act", stack(frames, i))
                    assert valid_action(response)
                    action = np.asarray(response["action"], np.float32)
                    assert np.all(action >= [-1, 0, 0]) and np.all(action <= [1, 1, 1])
                    np.testing.assert_array_equal(action, expected)
                    latency.append(elapsed)
                    rss.append(response["rss_mib"])
            for name in freeze["members_sha256"]:
                if name.endswith(".py"):
                    validate_source(name, (package / name).read_text())
            result.update(import_init_ms=child.import_init_s * 1000, reset=percentiles(resets),
                act=percentiles(latency), child_peak_RSS_mib=max(rss), exact_actions=len(latency),
                twice_reset_long_stream_determinism_pass=True, action_bounds_pass=True,
                static_input_eligibility_pass=True, simulator_imported=child.ready["simulator_imported"])
    finally:
        signal.alarm(0)
        try:
            child.close()
        except (BrokenPipeError, OSError):
            # The old buffered writer may fail during close after its child is
            # killed. Always reap the test process and close its remaining FDs.
            if child.process.poll() is None:
                child.process.kill()
            child.process.wait(timeout=2)
            for stream in [child.process.stdin, child.process.stdout, child.process.stderr]:
                try:
                    stream.close()
                except (BrokenPipeError, OSError):
                    pass
        result["process_reaped"] = child.process.poll() is not None
    verify_reference(plan, args.plan.parent)
    (args.output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
