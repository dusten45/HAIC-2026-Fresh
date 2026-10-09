"""Offline, identity-matched DEV diagnostics; no environment steps or policy truth.

The instrumented tracker preserves the frozen tracker arithmetic and verifies all
recorded actions. Truth is consulted only after each policy step to label its
events. Counts are repeated frames/tracks, never independent road samples.
"""

import argparse
import hashlib
import json
from pathlib import Path

import cv2
import numpy as np

from retry.clearance_agent import road_and_obstacles
from retry.schedule_agent import HazardScheduledAgent
from retry.submission_probe import stack


class InstrumentedTracker(HazardScheduledAgent):
    def reset(self, observation):
        super().reset(observation)
        self.track_ids = []
        self.next_track_id = 0

    def tracked_obstacles(self, image, speed):
        current = np.rint(image * 255).astype(np.uint8)
        transform = None
        flow = {"features": 0, "valid": 0, "determinant": None}
        if self.previous_image is not None and self.hazards:
            mask = np.ones((84, 84), np.uint8) * 255
            mask[61:] = 0
            mask[50:61, 34:51] = 0
            points = cv2.goodFeaturesToTrack(self.previous_image, 100, 0.02, 4, mask=mask)
            if points is not None:
                flow["features"] = len(points)
            if points is not None and len(points) >= 4:
                following, status, _ = cv2.calcOpticalFlowPyrLK(self.previous_image, current, points,
                    None, winSize=(11, 11), maxLevel=2)
                valid = status[:, 0] != 0
                flow["valid"] = int(np.sum(valid))
                if np.sum(valid) >= 4:
                    candidate, _ = cv2.estimateAffinePartial2D(points[valid], following[valid], method=cv2.LMEDS)
                    if candidate is not None:
                        flow["determinant"] = float(np.linalg.det(candidate[:, :2]))
                    if candidate is not None and np.isfinite(candidate).all() and 0.8 <= np.linalg.det(candidate[:, :2]) <= 1.2:
                        transform = candidate
        predicted, ids, predictions = [], [], []
        for (x, y, radius, age), track_id in zip(self.hazards, self.track_ids):
            previous = [float(x), float(y)]
            if transform is None:
                y -= speed * 0.08
            else:
                pixel = transform @ np.array([42 + 1.3608 * x, 63 - 1.701 * y, 1])
                x, y = (pixel[0] - 42) / 1.3608, (63 - pixel[1]) / 1.701
            retained = bool(age < 8 and abs(x) <= 35 and -5 <= y <= 35)
            predictions.append({"track_id": track_id, "previous": previous, "position": [float(x), float(y)],
                "age": int(age + 1), "retained_before_association": retained, "removed_by_detection": []})
            if retained:
                predicted.append((float(x), float(y), radius, age + 1))
                ids.append(track_id)
        fresh = road_and_obstacles(image)[1]
        for detection_index, (x, y, radius) in enumerate(fresh):
            keep = [np.hypot(p[0] - x, p[1] - y) > 2 for p in predicted]
            for track_id, retained in zip(ids, keep):
                if not retained:
                    for event in predictions:
                        if event["track_id"] == track_id:
                            event["removed_by_detection"].append(detection_index)
            predicted = [p for p, retained in zip(predicted, keep) if retained]
            ids = [track_id for track_id, retained in zip(ids, keep) if retained]
            predicted.append((x, y, radius, 0))
            ids.append(self.next_track_id)
            self.next_track_id += 1
        self.previous_image, self.hazards, self.track_ids = current, predicted, ids
        self.event = {"flow": flow, "transform": None if transform is None else transform.tolist(),
            "fresh": [list(p) for p in fresh], "predictions": predictions,
            "output": [{"track_id": i, "position": list(p[:2]), "radius": p[2], "age": p[3]}
                for p, i in zip(predicted, ids)]}
        return [p[:3] for p in predicted]


def nearest(position, truth):
    errors = np.linalg.norm(truth[:, :2] - np.asarray(position), axis=1)
    index = int(np.argmin(errors))
    return index, float(errors[index])


def in_roi(position):
    x, y = position[:2]
    return bool(3 <= 42 + 1.3608 * x <= 81 and 0 <= 63 - 1.701 * y < 61)


def transport(position, transform, speed):
    x, y = position[:2]
    if transform is None:
        return np.array([x, y - speed * .08])
    pixel = np.asarray(transform) @ np.array([42 + 1.3608 * x, 63 - 1.701 * y, 1])
    return np.array([(pixel[0] - 42) / 1.3608, (63 - pixel[1]) / 1.701])


def diagnose(source, frozen):
    data = np.load(source / "pixels-actions.npz")
    rows = [json.loads(line) for line in (source / "trace.jsonl").read_text().splitlines()]
    c, p = frozen["calibration"], frozen["parameters"]
    actor = InstrumentedTracker(c["coefficient_speed_per_intensity"], c["intercept"],
        p["speed_cap"], p["lateral_fast"], p["lateral_safe"])
    actor.reset(stack(data["frames"], 0))
    records, lineage = [], {}
    first_contact = next((i for i, row in enumerate(rows) if row["collision"]), None)
    for i, expected in enumerate(data["actions"]):
        observation = stack(data["frames"], i)
        np.testing.assert_array_equal(actor.act(observation), expected)
        event = actor.event
        truth = np.asarray(rows[i]["truth"]["obstacles_local"])
        previous_truth = np.asarray(rows[max(0, i - 1)]["truth"]["obstacles_local"])
        speed = max(0., actor.speed_gain * float(observation[-1, 74:83, 9:14].sum()) + actor.speed_bias)
        fresh_labels = []
        for detection in event["fresh"]:
            truth_id, error = nearest(detection[:2], truth)
            fresh_labels.append({"truth_id": truth_id, "error_m": error, "valid_match": error <= 2,
                "position": detection[:2]})
        for output in event["output"]:
            if output["age"] == 0:
                truth_id, error = nearest(output["position"], truth)
                lineage[output["track_id"]] = {"birth_frame": i, "birth_truth_id": truth_id,
                    "birth_error_m": error, "birth_valid_match": error <= 2}
        for prediction in event["predictions"]:
            ancestry = lineage[prediction["track_id"]]
            tid = ancestry["birth_truth_id"]
            prediction.update(ancestry)
            prediction["same_identity_error_m"] = float(np.linalg.norm(np.asarray(prediction["position"]) - truth[tid, :2]))
            prediction["previous_same_identity_error_m"] = float(np.linalg.norm(np.asarray(prediction["previous"]) - previous_truth[tid, :2]))
            prediction["motion_on_true_center_error_m"] = float(np.linalg.norm(transport(previous_truth[tid], event["transform"], speed) - truth[tid, :2]))
            prediction["wrong_identity_removal"] = any(fresh_labels[j]["valid_match"]
                and fresh_labels[j]["truth_id"] != tid for j in prediction["removed_by_detection"])
        for output in event["output"]:
            ancestry = lineage[output["track_id"]]
            tid = ancestry["birth_truth_id"]
            output.update(ancestry)
            output["same_identity_error_m"] = float(np.linalg.norm(np.asarray(output["position"]) - truth[tid, :2]))
            output["nearest_truth_id"], output["nearest_truth_error_m"] = nearest(output["position"], truth)
            output["truth_in_geometric_roi"] = in_roi(truth[tid])
            output["same_identity_fresh"] = [d for d in fresh_labels if d["truth_id"] == tid and d["valid_match"]]
        matched = []
        for tid, center in enumerate(truth):
            fresh = [d for d in fresh_labels if d["truth_id"] == tid and d["valid_match"]]
            memory = [o for o in event["output"] if o["birth_truth_id"] == tid and o["birth_valid_match"] and o["age"] > 0]
            before = [o for o in event["predictions"] if o["birth_truth_id"] == tid and o["birth_valid_match"] and o["retained_before_association"]]
            if in_roi(center) or fresh or memory:
                matched.append({"truth_id": tid, "truth_position": center.tolist(), "truth_in_geometric_roi": in_roi(center),
                    "fresh_errors_m": [d["error_m"] for d in fresh],
                    "predicted_errors_m": [o["same_identity_error_m"] for o in before],
                    "memory_errors_m": [o["same_identity_error_m"] for o in memory], "memory_ages": [o["age"] for o in memory]})
        event.update(frame_index=i, step=i + 1, speed_estimate=speed, fresh_labels=fresh_labels, matched_truth=matched,
            pre_first_contact=first_contact is not None and first_contact - 25 <= i < first_contact,
            frozen_action_exact=True, collision_after=rows[i]["collision"])
        records.append(event)
    return records


def summarize(records):
    def group(frames):
        outputs = [o for r in frames for o in r["output"] if o["position"][1] > 0]
        aged = [o for o in outputs if o["age"] > 0]
        ghosts = [o for o in aged if o["birth_valid_match"] and o["same_identity_fresh"] and o["same_identity_error_m"] > 2]
        useful = [o for o in aged if o["birth_valid_match"] and not o["same_identity_fresh"] and o["same_identity_error_m"] <= 2]
        predictions = [p for r in frames for p in r["predictions"] if p["birth_valid_match"]]
        initial_motion_fail = [p for p in predictions if p["previous_same_identity_error_m"] <= 2 and p["same_identity_error_m"] > 2]
        fresh = [d for r in frames for d in r["fresh_labels"] if d["position"][1] > 0]
        return {"frames": len(frames), "fresh_detections_forward": len(fresh),
            "fresh_bad_forward": sum(not d["valid_match"] for d in fresh),
            "output_forward": len(outputs), "aged_forward": len(aged),
            "aged_false_birth": sum(not o["birth_valid_match"] for o in aged),
            "aged_valid_birth_error_gt2": sum(o["birth_valid_match"] and o["same_identity_error_m"] > 2 for o in aged),
            "aged_bad_duplicate_despite_valid_fresh_same_identity": len(ghosts),
            "aged_good_when_fresh_missing": len(useful),
            "aged_good_when_fresh_missing_and_center_in_roi": sum(o["truth_in_geometric_roi"] for o in useful),
            "wrong_identity_association_removals": sum(p["wrong_identity_removal"] for p in predictions),
            "same_identity_error_first_crossings_gt2": len(initial_motion_fail),
            "crossing_true_center_motion_error_m": [p["motion_on_true_center_error_m"] for p in initial_motion_fail],
            "aged_by_age": {str(age): {"count": sum(o["age"] == age for o in aged),
                "error_gt2_valid_birth": sum(o["age"] == age and o["birth_valid_match"] and o["same_identity_error_m"] > 2 for o in aged),
                "good_fresh_missing": sum(o["age"] == age for o in useful)} for age in range(1, 9)}}
    return {"all": group(records), "pre_first_contact_25": group([r for r in records if r["pre_first_contact"]]),
        "recorded_actions_exact": len(records), "new_simulation_actions": 0,
        "truth_use": "Post-action identity matching and diagnosis only; never used by actor.",
        "limitations": ["Counts are correlated repeated frames and track instances.",
            "Geometric ROI membership does not establish unobstructed visibility.",
            "Birth identity uses existing 2 m association radius; invalid births are explicitly separate.",
            "Position error alone does not establish closed-loop usefulness or harm."]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    frozen = json.loads(args.freeze.read_text())
    records = diagnose(args.source, frozen)
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "matched-tracking.jsonl").open("w") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")
    result = summarize(records)
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["trace_sha256"] = hashlib.sha256((args.source / "trace.jsonl").read_bytes()).hexdigest()
    (args.output / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
