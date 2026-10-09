"""Frozen packaged-policy full DEV gate and same-speed target controls."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.clearance_agent import ClearanceAgent
from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest
from retry.process_probe import Participant, valid_action


class PackagedAgent:
    def __init__(self, package_root):
        python = Path(__file__).resolve().parents[1] / ".venv/bin/python"
        self.child = Participant(python, package_root=package_root)

    def reset(self, observation):
        self.child.call("reset", observation)

    def act(self, observation):
        response, _ = self.child.call("act", observation)
        assert valid_action(response), "Invalid packaged policy action"
        return np.asarray(response["action"], dtype=np.float32)

    def close(self):
        self.child.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mode", choices=["candidate", "controls"], default="candidate")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    check_window(plan)
    freeze_path = args.plan.parent / "freeze-v1.json"
    freeze = json.loads(freeze_path.read_text())
    assert digest(freeze_path) == plan["freeze_sha256"]
    package = args.plan.parent / "submission"
    assert digest(package / "candidate.zip") == freeze["zip_sha256"]
    for name, sha in freeze["members_sha256"].items():
        assert digest(package / "extracted" / name) == sha
    output = args.plan.parent / ("full-DEV" if args.mode == "candidate" else "full-controls")
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for source in Path(__file__).parent.glob("*.py"):
        (sources / source.name).write_bytes(source.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan), "freeze_sha256": digest(freeze_path),
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "scope": "Full reset->normal finish/retire/max2000; candidate uses extracted ZIP in isolated participant process."}, indent=2) + "\n")
    budget = Budget(args.plan, "full_DEV" if args.mode == "candidate" else "full_controls")
    indices = range(8) if args.mode == "candidate" else plan["control_indices"]
    calibration = freeze["calibration"]
    records = []
    for index in indices:
        factory = (lambda: PackagedAgent(package / "extracted")) if args.mode == "candidate" else lambda: ClearanceAgent(
            calibration["coefficient_speed_per_intensity"], calibration["intercept"])
        rows, summary = trace(plan["cases"][index], "frozen_arc" if args.mode == "candidate" else "fixed_corrected_full",
            budget, output / f"case-{index}", max_steps=plan["full_DEV_max_steps"], factory=factory)
        if summary["steps"] == plan["full_DEV_max_steps"] and not summary["completed"]:
            summary["retire_reason"] = "max_steps"
        records.append({**summary, "DEV_index": index, "evaluation_scope": "full_episode2000",
            "onsets": onsets(rows), "invalid_actions": 0, "frozen_package_sha256": freeze["zip_sha256"] if args.mode == "candidate" else None})
        (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    decision = {"cases": len(records), "completions": sum(r["completed"] for r in records),
        "median_progress": float(np.median([r["progress"] for r in records])),
        "median_damage": float(np.median([r["damage"] for r in records])),
        "invalid_actions": 0, "full_scope": True}
    if args.mode == "candidate":
        decision["G2_pass"] = len(records) == 8 and decision["completions"] >= 6 and decision["median_damage"] <= .4
    (output / "decision.json").write_text(json.dumps(decision, indent=2) + "\n")
    print(json.dumps(decision), flush=True)


if __name__ == "__main__":
    main()
