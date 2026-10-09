"""Build private candidate ZIP and check extracted entrypoint/local runner path."""

import argparse
import ast
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import zipfile

import numpy as np

from retry.arc_agent import ArcAgent
from retry.diagnose import Budget
from retry.evaluate import check_window, digest, percentiles
from retry.process_probe import Participant, valid_action


POLICY_FILES = ["__init__.py", "pixel_agent.py", "geometry_agent.py", "clearance_agent.py", "arc_agent.py"]
FORBIDDEN = {"ctypes", "importlib", "multiprocessing", "os", "pathlib", "resource", "shutil", "signal", "socket", "subprocess", "sys"}


class Reservation:
    def step(self, action):
        return None


def validate_source(name, source):
    tree = ast.parse(source, filename=name)
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not any(a.name.split(".")[0] in FORBIDDEN for a in node.names), name
        elif isinstance(node, ast.ImportFrom):
            assert node.module.split(".")[0] not in FORBIDDEN, name
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {"compile", "eval", "exec", "__import__"}, name


def make_package(output, calibration, candidate="arc", parameters=None):
    root = Path(__file__).resolve().parents[1]
    module, class_name = {"arc": ("arc_agent", "ArcAgent"), "temporal": ("temporal_agent", "TemporalRouteAgent"),
        "connected": ("connected_agent", "ConnectedTemporalAgent"),
        "parameter": ("parameter_agent", "ParameterizedConnectedAgent")}[candidate]
    policy_files = POLICY_FILES + (["ridge_agent.py", "route_agent.py", "temporal_agent.py"] if candidate != "arc" else [])
    if candidate in ["connected", "parameter"]:
        policy_files.append("connected_agent.py")
    if candidate == "parameter":
        policy_files.append("parameter_agent.py")
    extra = f", {parameters['speed_cap']!r}, {parameters['lateral_acceleration']!r}" if candidate == "parameter" else ""
    entry = (f"from retry.{module} import {class_name}\n\nclass Agent({class_name}):\n"
             "    def __init__(self):\n"
             f"        super().__init__({calibration['coefficient_speed_per_intensity']!r}, {calibration['intercept']!r}{extra})\n")
    members = {"agent.py": entry.encode(), "LICENSE": (root / "LICENSE").read_bytes(),
               **{f"retry/{name}": (root / "retry" / name).read_bytes() for name in policy_files}}
    for name, content in members.items():
        if name.endswith(".py"):
            validate_source(name, content.decode())
    archive = output / "candidate.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for name, content in sorted(members.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            handle.writestr(info, content)
    extracted = output / "extracted"
    with zipfile.ZipFile(archive) as handle:
        assert len(handle.infolist()) <= 1000
        assert sum(i.file_size for i in handle.infolist()) <= 2 * 1024**3
        assert all(i.file_size <= 500 * 1024**2 and i.file_size / max(i.compress_size, 1) <= 100 for i in handle.infolist())
        handle.extractall(extracted)
    assert archive.stat().st_size <= 500 * 1024**2
    manifest = {"zip_sha256": digest(archive), "members_sha256": {name: hashlib.sha256(content).hexdigest() for name, content in members.items()},
                "zip_bytes": archive.stat().st_size, "static_and_size_checks_passed": True,
                "contains_harness_or_private_records": False, "calibration": calibration}
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return extracted, manifest


def stack(frames, index):
    return np.asarray([frames[max(0, index - i)] for i in [3, 2, 1, 0]], dtype=np.float32) / 255


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--candidate", choices=["arc", "temporal", "connected", "parameter"], default="arc")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    if args.candidate == "temporal":
        assert json.loads((args.plan.parent / "boundary/decision.json").read_text())["gate_pass"]
        for name, expected in plan["candidate_source_sha256"].items():
            assert digest(Path(name)) == expected
    if args.candidate == "connected":
        from retry.connectivity_probe import verify_reference
        verify_reference(plan, args.plan.parent)
        assert json.loads((args.plan.parent / "component/decision.json").read_text())["local_gate_pass"]
        assert digest(Path("retry/connected_agent.py")) == plan["challenger_source_sha256"]
    if args.candidate == "parameter":
        from retry.parameter_probe import guard_reference
        guard_reference(plan, args.plan.parent)
        validation = args.plan.parent / plan["validation_decision"]
        assert digest(validation) == plan["validation_decision_sha256"]
        assert json.loads(validation.read_text())["validation_gate_pass"]
        assert digest(Path("retry/parameter_agent.py")) == plan["parameter_source_sha256"]
    output = args.plan.parent / plan.get("submission_output", "submission")
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for source in Path(__file__).parent.glob("*.py"):
        (sources / source.name).write_bytes(source.read_bytes())
    package_root, manifest = make_package(output, plan["pixel_speed_calibration"], args.candidate, plan.get("parameters"))
    root = Path(__file__).resolve().parents[1]
    python = root / ".venv/bin/python"
    source_trace = (args.plan.parent / plan["submission_trace"]).resolve() if "submission_trace" in plan else args.plan.parent / "boundaries" / f"case-{plan['submission_check']['local_runner_case_index']}-arc_corrected"
    until = time.monotonic() + 120
    while not (source_trace / "pixels-actions.npz").exists():
        check_window(plan)
        if time.monotonic() >= until:
            raise RuntimeError("Boundary source trace not available within budget")
        time.sleep(0.25)
    data = np.load(source_trace / "pixels-actions.npz")
    frames, actions = data["frames"], data["actions"]
    child = Participant(python, package_root=package_root)
    latencies, rss = [], []
    try:
        _, reset_s = child.call("reset", stack(frames, 0))
        for index in range(min(128, len(actions))):
            check_window(plan)
            response, elapsed = child.call("act", stack(frames, index))
            assert valid_action(response)
            np.testing.assert_array_equal(np.asarray(response["action"], dtype=np.float32), actions[index])
            latencies.append(elapsed)
            rss.append(response["rss_mib"])
        ipc = {"import_init_ms": child.import_init_s * 1000, "reset_ms": reset_s * 1000,
               "actions_exactly_equal": len(latencies), "act_including_IPC": percentiles(latencies),
               "child_peak_rss_mib": max(rss), "policy_modules_loaded_from_archive": child.ready["policy_modules"]}
    finally:
        child.close()
    # This copy is a test tree only. The ZIP remains the policy-only archive above.
    runtime = output / "local_runtime"
    shutil.copytree(package_root, runtime)
    copied = ["local_runner.py", "env_wrapper.py", "damage.py", "core/__init__.py", "core/finish_line.py", "core/track_variables.py", "core/obstacle_contacts.py", "core/vendor/__init__.py", "core/vendor/car_racing.py", "core/vendor/car_dynamics.py"]
    for name in copied:
        target = runtime / name
        target.parent.mkdir(parents=True, exist_ok=True)
        original = subprocess.check_output(["git", "show", f"{plan['base']}:{name}"], cwd=root)
        assert original == (root / name).read_bytes()
        target.write_bytes(original)
    cap = plan["submission_check"]["max_steps"]
    budget_stage = plan.get("submission_budget_stage", "submission_path")
    budget = Budget(args.plan, budget_stage)
    for _ in range(cap):
        budget.step(Reservation(), None)
    case = plan["cases"][plan["submission_check"]["local_runner_case_index"]]
    command = [str(python), "local_runner.py", "--track-id", str(case["track_id"]), "--seed", str(case["seed"]),
               "--max-steps", str(cap), "--no-render"]
    env = {**os.environ, "SDL_VIDEODRIVER": "dummy", "SDL_AUDIODRIVER": "dummy", "OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1"}
    check_window(plan)
    process = subprocess.Popen(command, cwd=runtime, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    started = time.monotonic()
    try:
        while True:
            check_window(plan)
            if time.monotonic() - started >= 30:
                raise TimeoutError("Local runner probe deadline")
            try:
                stdout, stderr = process.communicate(timeout=0.25)
                break
            except subprocess.TimeoutExpired:
                pass
    except Exception:
        process.kill()
        process.wait()
        raise
    (output / "local_runner.stdout.txt").write_text(stdout)
    (output / "local_runner.stderr.txt").write_text(stderr)
    assert process.returncode == 0, stderr
    used = int(re.search(r"simulation agent steps: (\d+)", stdout)[1])
    progress = float(re.search(r"progress: ([0-9.]+)", stdout)[1])
    # Return only unconsumed reserved actions, preserving exact physical accounting.
    if used < cap:
        with budget.path.open("r+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            ledger = json.load(handle)
            ledger["actions"] -= cap - used
            ledger["stages"][budget_stage] -= cap - used
            handle.seek(0)
            json.dump(ledger, handle)
            handle.truncate()
    rows = [json.loads(line) for line in (source_trace / "trace.jsonl").read_text().splitlines()]
    assert abs(progress - rows[used - 1]["progress"]) <= 1e-6
    result = {"manifest": manifest, "isolated_archive_entrypoint": ipc,
              "original_local_runner": {**case, "steps": used, "progress": progress, "wall_s": time.monotonic() - started,
                    "progress_matches_research_prefix": True, "canonical_files_sha256": {name: digest(runtime / name) for name in copied}},
              "plan_sha256": digest(args.plan), "source_sha256": {f.name: digest(f) for f in sources.glob("*.py")},
              "local_submission_path_passed": True, "official_server_parity_verified": False,
              "deployment_eligible": False, "remaining": ["Official server/process/container implementation and RSS accounting not available for exact parity.", "Full DEV completion gate not yet assessed."]}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"local_submission_path_passed": True, "archive_actions_equal": ipc["actions_exactly_equal"],
        "local_runner_actions": used, "progress": progress, "official_server_parity_verified": False}), flush=True)


if __name__ == "__main__":
    main()
