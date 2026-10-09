"""Small fixed-budget DEV sensitivity, surrogate search and random comparison."""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path
import subprocess

import numpy as np

from retry.evaluate import check_window, digest
from retry.parameter_probe import guard_reference


def save(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def baseline_records(directory):
    rows = [r for p in (directory / "baseline").glob("partition-*/result.json") for r in json.loads(p.read_text())]
    return sorted(rows, key=lambda r: r["case_index"])


def assess(rows, baseline, candidate_id, parameters):
    by_index = {r["case_index"]: r for r in baseline}
    assert len(rows) == len({r["case_index"] for r in rows})
    paired = [(by_index[r["case_index"]], r) for r in rows]
    lost = [a["case_index"] for a, b in paired if a["completed"] and not b["completed"]]
    common = [(a, b) for a, b in paired if a["completed"] and b["completed"]]
    ratios = [b["lap_ms"] / a["lap_ms"] for a, b in common]
    log_ratio = float(np.median(np.log(ratios))) if ratios else 0.0
    damage = float(np.median([r["damage"] for r in rows]))
    baseline_damage = float(np.median([a["damage"] for a, _ in paired]))
    completions = sum(r["completed"] for r in rows)
    feasible = not lost and damage <= baseline_damage + 0.2 and all(r["invalid_actions"] == 0 for r in rows)
    return {"id": candidate_id, "parameters": parameters, "cases": len(rows), "completions": completions,
        "lost_baseline_completions": lost, "common_completed_pairs": len(common), "lap_ratios": ratios,
        "median_log_lap_ratio": log_ratio, "median_lap_ratio": float(np.median(ratios)) if ratios else None,
        "median_damage": damage, "feasible": bool(feasible),
        "utility": completions + 0.1 * float(np.clip(-log_ratio, -1, 1)),
        "actual_actions": sum(r["steps"] for r in rows), "episode_wall_s": sum(r["wall_s"] for r in rows), "rows": rows}


def ranking(record):
    return (-record["completions"], record["median_log_lap_ratio"], record["median_damage"], record["id"])


def run_job(plan_path, job):
    directory = plan_path.parent
    check_window(json.loads(plan_path.read_text()))
    job["plan_sha256"] = digest(plan_path)
    job["candidate_source_sha256"] = digest(Path(__file__).parent / "parameter_agent.py")
    path = directory / "jobs" / (job["id"] + ".json")
    assert not path.exists()
    save(path, job)
    path.with_suffix(".sha256").write_text(digest(path) + "\n")
    root = Path(__file__).resolve().parents[1]
    command = [str(root / ".venv/bin/python"), "-m", "retry.parameter_probe", "--plan", str(plan_path), "--job", str(path)]
    with (directory / (job["id"] + ".log")).open("x") as output:
        subprocess.run(command, cwd=root, stdout=output, stderr=subprocess.STDOUT, check=True)
    return json.loads((directory / job["output"] / "result.json").read_text())


def gp(x, y, grid, prior_mean):
    def kernel(a, b):
        return np.exp(-0.5 * np.sum(((a[:, None] - b[None]) / 0.35) ** 2, axis=2))
    k = kernel(x, x) + np.eye(len(x)) * (0.05 ** 2 + 1e-6)
    l = np.linalg.cholesky(k)
    cross = kernel(x, grid)
    centered = y - prior_mean
    mean = prior_mean + cross.T @ np.linalg.solve(l.T, np.linalg.solve(l, centered))
    projection = np.linalg.solve(l, cross)
    variance = np.maximum(1 - np.sum(projection ** 2, axis=0), 1e-9)
    return mean, np.sqrt(variance)


def normal_cdf(z):
    return np.asarray([0.5 * (1 + math.erf(float(v) / math.sqrt(2))) for v in z])


def acquire(records, dimensions, bounds):
    lower = np.asarray([bounds[d][0] for d in dimensions])
    width = np.asarray([bounds[d][1] - bounds[d][0] for d in dimensions])
    def vector(p):
        return (np.asarray([p[d] for d in dimensions]) - lower) / width
    grid = np.asarray(list(__import__("itertools").product(*[np.linspace(0, 1, 17) for _ in dimensions])))
    x = np.asarray([vector(r["parameters"]) for r in records])
    unused = np.all(np.linalg.norm(grid[:, None] - x[None], axis=2) > 1e-8, axis=1)
    grid = grid[unused]
    feasible = np.asarray([r["feasible"] for r in records], dtype=bool)
    assert feasible.any()
    y = np.asarray([r["utility"] for r in records])[feasible]
    mean, sigma = gp(x[feasible], y, grid, float(np.mean(y)))
    z = (mean - max(y)) / sigma
    ei = (mean - max(y)) * normal_cdf(z) + sigma * np.exp(-0.5 * z ** 2) / np.sqrt(2 * np.pi)
    safe_mean, safe_sigma = gp(x, feasible.astype(float), grid, 0.5)
    probability = normal_cdf((safe_mean - 0.5) / safe_sigma)
    score = ei * probability
    index = int(np.argmax(score))
    parameter = {"speed_cap": 28.0, "lateral_acceleration": 5.0}
    parameter.update({d: float(lower[i] + width[i] * grid[index, i]) for i, d in enumerate(dimensions)})
    return parameter, {"expected_improvement": float(ei[index]), "feasibility_probability": float(probability[index]),
        "acquisition": float(score[index]), "eligible_grid_points": len(grid), "observations": len(records)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--mode", choices=["sensitivity", "auto", "random", "winners"], required=True)
    args = parser.parse_args()
    directory, plan = args.plan.parent, json.loads(args.plan.read_text())
    check_window(plan)
    guard_reference(plan, directory)
    registration = directory / "P7-before-outcomes-v1.json"
    manifest = json.loads(registration.read_text())
    assert digest(registration) == registration.with_suffix(".sha256").read_text().split()[0]
    assert manifest["plan_sha256"] == digest(args.plan)
    assert manifest["parameter_source_sha256"] == digest(Path(__file__).parent / "parameter_agent.py")
    analysis = json.loads((directory / "baseline-analysis.json").read_text())
    assert analysis["default_exact_equivalence_pass"]
    baseline = baseline_records(directory)
    base_subset = [r for r in baseline if r["case_index"] in plan["search_indices"]]
    if args.mode == "sensitivity":
        (directory / "sensitivity").mkdir(exist_ok=False)
        def one(item):
            name, parameters = item
            rows = run_job(args.plan, {"id": name, "kind": "parameter", "split": "SCREEN", "stage": "sensitivity",
                "case_indices": plan["search_indices"], "output": f"sensitivity/{name}", "parameters": parameters})
            return assess(rows, baseline, name, parameters)
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(one, plan["one_factor_arms"].items()))
        save(directory / "sensitivity/result.json", result)
        print(json.dumps([{k: r[k] for k in ["id", "completions", "feasible", "median_lap_ratio", "lost_baseline_completions"]} for r in result]), flush=True)
    elif args.mode in ["auto", "random"]:
        mode = args.mode
        output = directory / f"search-{mode}"
        output.mkdir(exist_ok=False)
        dimensions = analysis["search_dimensions"]
        records = [assess(base_subset, baseline, "default", plan["default_parameters"])]
        records.extend(json.loads((directory / "sensitivity/result.json").read_text()))
        if dimensions == ["lateral_acceleration"]:
            records = [r for r in records if r["parameters"]["speed_cap"] == 28]
        initial = len(records)
        random_points = manifest["random_points_2D" if len(dimensions) == 2 else "random_points_1D"]
        for index in range(4):
            check_window(plan)
            parameters, acquisition = acquire(records, dimensions, plan["parameter_domain"]) if mode == "auto" else (random_points[index], None)
            candidate_id = f"{mode}-{index}"
            choice = {"id": candidate_id, "parameters": parameters, "acquisition": acquisition,
                "registered_before_simulation": True, "parent_plan_sha256": digest(args.plan)}
            save(output / f"choice-{index}.json", choice)
            rows = run_job(args.plan, {"id": candidate_id, "kind": "parameter", "split": "SCREEN", "stage": f"search_{mode}",
                "case_indices": plan["search_indices"], "output": f"search-{mode}/{candidate_id}", "parameters": parameters})
            record = assess(rows, baseline, candidate_id, parameters)
            records.append(record)
            save(output / "observations.json", records)
            print(json.dumps({k: record[k] for k in ["id", "parameters", "completions", "feasible", "median_lap_ratio"]}), flush=True)
        winner = min([r for r in records if r["feasible"]], key=ranking)
        save(output / "decision.json", {"mode": mode, "winner": winner, "common_warm_start_configurations": initial,
            "new_configuration_evaluations": 4, "new_episode_evaluations": 12,
            "new_actual_actions": sum(r["actual_actions"] for r in records[initial:]),
            "new_episode_wall_s": sum(r["episode_wall_s"] for r in records[initial:]),
            "validation_used": False, "protected_used": False})
    else:
        output = directory / "winners"
        output.mkdir(exist_ok=False)
        selected = {m: json.loads((directory / f"search-{m}/decision.json").read_text())["winner"] for m in ["auto", "random"]}
        unique = {r["id"]: r for r in selected.values()}
        remaining = [i for i in range(8) if i not in plan["search_indices"]]
        def complete(item):
            candidate_id, record = item
            if candidate_id == "default":
                rows = baseline
            else:
                rest = run_job(args.plan, {"id": "winner-" + candidate_id, "kind": "parameter", "split": "SCREEN", "stage": "winner_screen",
                    "case_indices": remaining, "output": f"winners/{candidate_id}", "parameters": record["parameters"]})
                rows = sorted(record["rows"] + rest, key=lambda r: r["case_index"])
            result = assess(rows, baseline, candidate_id, record["parameters"])
            base_count = sum(r["completed"] for r in baseline)
            ratios = result["lap_ratios"]
            result["screen_gate_pass"] = result["feasible"] and result["completions"] >= 6 and bool(ratios) and (
                (result["completions"] > base_count and result["median_lap_ratio"] <= 1.02) or
                (result["completions"] == base_count and result["median_lap_ratio"] <= 0.97 and max(ratios) <= 1.05))
            return result
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(complete, unique.items()))
        save(output / "result.json", results)
        eligible = [r for r in results if r["screen_gate_pass"]]
        chosen = min(eligible, key=ranking) if eligible else None
        save(output / "decision.json", {"method_winner_ids": {m: r["id"] for m, r in selected.items()},
            "screen_results": [{k: r[k] for k in ["id", "completions", "lost_baseline_completions", "median_lap_ratio", "feasible", "screen_gate_pass"]} for r in results],
            "selected": chosen, "deeper_gate_pass": chosen is not None, "validation_opened": False,
            "method_general_superiority_established": False})
        print(json.dumps({"eligible": len(eligible), "selected_id": chosen["id"] if chosen else None}), flush=True)


if __name__ == "__main__":
    main()
