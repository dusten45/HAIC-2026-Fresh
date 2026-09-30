"""Summarize the fixed matched-teacher pilot from saved model/evaluation artifacts."""

import argparse
from collections import Counter
import json
from pathlib import Path
import statistics


def report(root):
    arms = {}
    budgets = []
    grids = []
    sources = []
    for arm in ("v1", "v2", "mixed"):
        history = json.loads((root / f"teacher_model_{arm}" / "history.json").read_text())
        budget = {"seed": history["seed"], "config": history["config"],
                  "rows_per_epoch": [e["train_samples"] for e in history["history"]],
                  "updates_per_epoch": [e["optimizer_steps"] for e in history["history"]],
                  "train_roads": history["train_roads"], "val_roads": history["val_roads"]}
        budgets.append(budget)
        sources.append(history["source_sha256"])
        results = []
        evaluation_sources = []
        for track in range(1, 6):
            path = root / f"teacher_closed_{arm}_t{track}" / "summary.json"
            summary = json.loads(path.read_text())
            if summary["checkpoint_sha256"] != history["best_checkpoint_sha256"]:
                raise ValueError(f"Evaluation checkpoint mismatch: {path}")
            if (summary.get("diagnostic_only") or summary.get("oracle_prefix_steps", 0)
                    or summary.get("steer_checkpoint_sha256") or summary.get("collect_recovery")):
                raise ValueError(f"Assisted/diagnostic rollout is not the pilot: {path}")
            expected = {(track, seed) for seed in (31, 32, 33)}
            observed = [(e["track_id"], e["geometry_seed"]) for e in summary["results"]]
            if len(observed) != 3 or set(observed) != expected:
                raise ValueError(f"Missing, duplicate or unexpected roads: {path}")
            results.extend(summary["results"])
            evaluation_sources.append({key: summary.get(key) for key in
                                       ("source_sha256", "conditions", "max_steps", "split",
                                        "frame_skip", "warmup", "thresholds")})
        grids.append([(r["track_id"], r["geometry_seed"]) for r in results])
        students = [r["student"] for r in results]
        best = min(history["history"], key=lambda epoch: epoch["val"]["weighted_mean_mse"])
        arms[arm] = {
            "budget": budget, "checkpoint_sha256": history["best_checkpoint_sha256"],
            "selected_epoch": best["epoch"], "validation": best["val"],
            "episodes": len(students), "roads": len(set(grids[-1])),
            "base_geometries": len({seed for _, seed in grids[-1]}),
            "finishes": sum(e["finished"] for e in students),
            "reference_finishes": sum(r["reference"]["finished"] for r in results),
            "mean_progress": statistics.mean(e["progress"] for e in students),
            "median_progress": statistics.median(e["progress"] for e in students),
            "damaged_episodes": sum(e["damage"] > 0 for e in students),
            "failure_reasons": dict(Counter(e["reason"] for e in students if not e["finished"])),
            "first_on_state_mismatch_components": dict(Counter(
                r["first_deviations"]["on_state_action"]["component"]
                for r in results if r.get("first_deviations", {}).get("on_state_action"))),
            "roads_result": [{"track_id": r["track_id"], "geometry_seed": r["geometry_seed"],
                              **r["student"], "first_deviations": r.get("first_deviations")}
                             for r in results],
            "evaluation_source_groups": evaluation_sources,
        }
    if any(b != budgets[0] for b in budgets[1:]) or any(g != grids[0] for g in grids[1:]):
        raise ValueError("Pilot arms have different model budgets or evaluation grids")
    if any(source != sources[0] for source in sources[1:]):
        raise ValueError("Training sources differ across pilot arms")
    evaluation_sources = [source for a in arms.values() for source in a.pop("evaluation_source_groups")]
    if any(source != evaluation_sources[0] for source in evaluation_sources[1:]):
        raise ValueError("Evaluation sources or conditions differ across pilot arms")
    counts = {arm: result["finishes"] for arm, result in arms.items()}
    return {"kind": "matched_teacher_pilot", "arms": arms, "finish_counts": counts,
            "v2_finish_gain_over_v1": counts["v2"] - counts["v1"],
            "mixed_finish_gain_over_v1": counts["mixed"] - counts["v1"],
            "decision": "inconclusive_finish_tie" if len(set(counts.values())) == 1 else "one_seed_pilot_only",
            "limitations": "One training seed; exposed validation. Different teacher-target losses are not directly comparable. No RL or official confirmation."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=Path("runs"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = report(args.runs)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: value for key, value in result.items() if key != "arms"}, indent=2))


if __name__ == "__main__":
    main()
