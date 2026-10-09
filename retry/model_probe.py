"""Calibrate one yaw coefficient and test a different planning assumption on DEV."""

import argparse
import json
from pathlib import Path

import numpy as np

from retry.connectivity_probe import verify_reference
from retry.evaluate import check_window, digest
from retry.motion_model import advance_front_angle


def samples(source, gain, bias):
    rows = [json.loads(x) for x in (source / "trace.jsonl").read_text().splitlines()]
    angle, records = 0.0, []
    for row in rows:
        angle, tangent = advance_front_angle(angle, row["action"][0])
        speed = max(0.0, gain * row["pixels"]["hud_white_integral"] + bias)
        before, after = row["state_before"], row["state_after"]
        dt = after["time"] - before["time"]
        yaw = (after["angle"] - before["angle"] + np.pi) % (2 * np.pi) - np.pi
        velocity = np.asarray(before["velocity"])
        theta = before["angle"]
        lateral = float(np.dot(velocity, [np.cos(theta), np.sin(theta)]))
        actual_speed = row["truth"]["speed_m_s"]
        eligible = (row["damage"] == 0 and not row["collision"] and 3 <= actual_speed <= 35
            and abs(lateral) <= 0.25 * actual_speed and abs(dt - 0.08) < 1e-6)
        records.append({"predictor": -speed * tangent, "yaw": float(yaw), "dt": dt, "eligible": eligible})
    return records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    plan, manifest = json.loads(args.plan.read_text()), json.loads(args.manifest.read_text())
    check_window(plan)
    assert digest(args.plan) == manifest["plan_sha256"]
    assert digest(Path("retry/motion_model.py")) == manifest["motion_source_sha256"]
    freeze = verify_reference(plan, args.plan.parent)
    c = freeze["calibration"]
    data = {}
    for index in manifest["training_indices"] + manifest["validation_indices"]:
        source = (args.plan.parent / f"../stage6/full-DEV/case-{index}").resolve()
        assert digest(source / "trace.jsonl") == manifest["trace_sha256"][str(index)]
        data[index] = samples(source, c["coefficient_speed_per_intensity"], c["intercept"])
    train = [x for i in manifest["training_indices"] for x in data[i] if x["eligible"]]
    x = np.asarray([v["predictor"] for v in train])
    y = np.asarray([v["yaw"] / v["dt"] for v in train])
    coefficient = float(np.dot(x, y) / np.dot(x, x))
    errors = []
    for index in manifest["validation_indices"]:
        for start in range(len(data[index]) - 4):
            window = data[index][start:start + 5]
            if not all(v["eligible"] for v in window):
                continue
            errors.append(abs(sum(coefficient * v["predictor"] * v["dt"] - v["yaw"] for v in window)))
    median, p95 = float(np.median(errors)), float(np.percentile(errors, 95))
    output = args.plan.parent / "motion-model"
    output.mkdir(exist_ok=False)
    sources = output / "sources"
    sources.mkdir()
    for name in ["model_probe.py", "motion_model.py"]:
        (sources / name).write_bytes((Path(__file__).parent / name).read_bytes())
    result = {"yaw_coefficient": coefficient, "training_samples": len(train),
        "validation_windows": len(errors), "median_heading_error_0_4s_rad": median,
        "p95_heading_error_0_4s_rad": p95,
        "model_gate_pass": median <= 0.08 and p95 <= 0.25 and 0.05 <= coefficient <= 0.5,
        "privileged_motion_calibration_diagnostic_only": True, "runtime_features": "pixel_speed+own_steering_history",
        "validation_scope": "correlated_existing_DEV_windows_not_unseen_population",
        "new_simulation_actions": 0, "plan_sha256": digest(args.plan), "manifest_sha256": digest(args.manifest)}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
