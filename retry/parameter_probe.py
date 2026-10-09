"""Preregistered DEV jobs for a frozen reference or a two-parameter contrast."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.diagnose import Budget, onsets, trace
from retry.evaluate import check_window, digest, percentiles
from retry.process_probe import Participant, valid_action


def guard_reference(plan, directory):
    freeze_path = (directory / plan["reference_freeze"]).resolve()
    assert digest(freeze_path) == plan["reference_freeze_sha256"]
    freeze = json.loads(freeze_path.read_text())
    package = (directory / plan["reference_package"]).resolve()
    assert digest(package / "candidate.zip") == plan["reference_zip_sha256"] == freeze["zip_sha256"]
    for name, expected in freeze["members_sha256"].items():
        assert digest(package / "extracted" / name) == expected
        if name.startswith("retry/"):
            assert digest(Path(__file__).resolve().parents[1] / name) == expected
    return freeze, package


class MeasuredAgent:
    def __init__(self, plan, directory, job):
        freeze, package = guard_reference(plan, directory)
        root = Path(__file__).resolve().parents[1]
        python = root / ".venv/bin/python"
        if job["kind"] == "baseline":
            self.child = Participant(python, package_root=package / "extracted")
        elif job["kind"] == "parameter":
            assert job["candidate_source_sha256"] == digest(root / "retry/parameter_agent.py")
            c = freeze["calibration"]
            p = job["parameters"]
            command = [str(python), "-m", "retry.parameter_worker",
                str(c["coefficient_speed_per_intensity"]), str(c["intercept"]),
                str(p["speed_cap"]), str(p["lateral_acceleration"])]
            self.child = Participant(python, command_override=command)
        elif job["kind"] == "schedule":
            assert job["schedule_source_sha256"] == digest(root / "retry/schedule_agent.py")
            c, p = freeze["calibration"], job["parameters"]
            command = [str(python), "-m", "retry.schedule_worker",
                str(c["coefficient_speed_per_intensity"]), str(c["intercept"]),
                str(p["speed_cap"]), str(p["lateral_fast"]), str(p["lateral_safe"])]
            self.child = Participant(python, command_override=command)
        elif job["kind"] in ["separated", "slow"]:
            for name, expected in job["new_policy_sources_sha256"].items():
                assert digest(root / name) == expected
            c, p = freeze["calibration"], job["parameters"]
            command = [str(python), "-m", "retry.separated_worker", job["kind"],
                str(c["coefficient_speed_per_intensity"]), str(c["intercept"]),
                str(p["speed_cap"]), str(p["lateral_fast"]), str(p["lateral_safe"])]
            self.child = Participant(python, command_override=command)
        elif job["kind"] in ["fresh", "minimal"]:
            assert job["memory_source_sha256"] == digest(root / "retry/memory_agent.py")
            assert job["worker_source_sha256"] == digest(root / "retry/memory_worker.py")
            c, p = freeze["calibration"], job["parameters"]
            command = [str(python), "-m", "retry.memory_worker", job["kind"],
                str(c["coefficient_speed_per_intensity"]), str(c["intercept"]),
                str(p["speed_cap"]), str(p["lateral_fast"]), str(p["lateral_safe"])]
            self.child = Participant(python, command_override=command)
        elif job["kind"] == "chord":
            assert job["chord_source_sha256"] == digest(root / "retry/chord_agent.py")
            c, p = freeze["calibration"], job["parameters"]
            command = [str(python), "-m", "retry.chord_worker",
                str(c["coefficient_speed_per_intensity"]), str(c["intercept"]),
                str(p["speed_cap"]), str(p["lateral_fast"]), str(p["lateral_safe"])]
            self.child = Participant(python, command_override=command)
        else:
            assert job["kind"] == "frozen_challenger"
            frozen = directory / job["freeze_file"]
            assert digest(frozen) == job["freeze_sha256"]
            candidate = json.loads(frozen.read_text())
            archive = directory / job["package_directory"]
            assert digest(archive / "candidate.zip") == candidate["zip_sha256"]
            for name, expected in candidate["members_sha256"].items():
                assert digest(archive / "extracted" / name) == expected
            self.child = Participant(python, package_root=archive / "extracted")
        self.latencies, self.rss = [], []

    def reset(self, observation):
        _, self.reset_s = self.child.call("reset", observation)

    def act(self, observation):
        response, elapsed = self.child.call("act", observation)
        assert valid_action(response)
        self.latencies.append(elapsed)
        self.rss.append(response["rss_mib"])
        return np.asarray(response["action"], dtype=np.float32)

    def close(self):
        self.child.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--job", type=Path, required=True)
    args = parser.parse_args()
    plan, job = json.loads(args.plan.read_text()), json.loads(args.job.read_text())
    check_window(plan)
    assert digest(args.plan) == args.plan.with_suffix(".sha256").read_text().split()[0]
    assert digest(args.job) == args.job.with_suffix(".sha256").read_text().split()[0]
    assert digest(args.plan) == job["plan_sha256"]
    assert job["split"] in ["SCREEN", "VALIDATE", "OLD_DEV"]
    assert job["stage"] in plan["stage_budgets"]
    freeze, _ = guard_reference(plan, args.plan.parent)
    output = args.plan.parent / job["output"]
    assert output.resolve().is_relative_to(args.plan.parent.resolve())
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for source in Path(__file__).parent.glob("*.py"):
        (sources / source.name).write_bytes(source.read_bytes())
    (output / "metadata.json").write_text(json.dumps({"plan_sha256": digest(args.plan),
        "job_sha256": digest(args.job), "reference_zip_sha256": freeze["zip_sha256"],
        "source_sha256": {p.name: digest(p) for p in sources.glob("*.py")},
        "scope": "DEV full reset->finish/retirement/max2000; actual separate policy process"}, indent=2) + "\n")
    records, budget = [], Budget(args.plan, job["stage"])
    for index in job["case_indices"]:
        check_window(plan)
        actor = MeasuredAgent(plan, args.plan.parent, job)
        rows, summary = trace(plan["split"][job["split"]][index], job["id"], budget,
            output / f"case-{index}", max_steps=plan["max_steps"], factory=lambda: actor)
        if summary["steps"] == plan["max_steps"] and not summary["completed"]:
            summary["retire_reason"] = "max_steps"
        record = {**summary, "case_index": index, "split": job["split"],
            "parameters": job.get("parameters", plan["default_parameters"]), "onsets": onsets(rows),
            "act_including_IPC": percentiles(actor.latencies), "child_peak_RSS_mib": max(actor.rss, default=0),
            "import_init_ms": actor.child.import_init_s * 1000, "participant_reset_ms": actor.reset_s * 1000,
            "invalid_actions": 0}
        records.append(record)
        (output / "result.json").write_text(json.dumps(records, indent=2) + "\n")
    guard_reference(plan, args.plan.parent)


if __name__ == "__main__":
    main()
