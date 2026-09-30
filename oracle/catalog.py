"""Index saved research summaries without opening traces, images, or weights."""

import argparse
import json
from pathlib import Path

from .recording import ROOT, encode


def read_json(path):
    return json.loads(path.read_text()) if path.is_file() else {}


def catalog(runs, previous=()):
    retained = {record["id"]: record for record in previous}
    records = []
    for directory in sorted(Path(runs).iterdir()):
        if not directory.is_dir():
            continue
        summary = read_json(directory / "summary.json")
        history = read_json(directory / "history.json")
        manifest = read_json(directory / "manifest.json")
        metadata = read_json(directory / "metadata.json") or read_json(directory / "provenance.json")
        paired = bool(summary.get("results") and "student" in summary["results"][0])
        kind = ("bc_model" if history else "bc_dataset" if manifest else
                "bc_evaluation" if paired or directory.name.startswith("bc_closed_") else "oracle_run")
        episodes = (manifest.get("episodes", []) if manifest else summary.get("results", summary.get("episodes", [])))
        episodes = episodes if isinstance(episodes, list) else []
        if not episodes and not history:
            episodes = [read_json(path) for path in sorted(directory.glob("track*.summary.json"))]
        finish_key = "student" if paired else None
        count = len(episodes)
        finishes = sum(bool((episode.get(finish_key, {}) if finish_key else episode).get("finished"))
                       for episode in episodes)
        roads = {(episode.get("track_id"), episode.get("geometry_seed")) for episode in episodes}
        fingerprints = [metadata, history, summary,
                        history.get("execution_fingerprint", {}), summary.get("execution_fingerprint", {})]
        source_hashes = next((value["source_sha256"] for value in fingerprints if value.get("source_sha256")), {})
        settings = metadata.get("args", metadata.get("arguments", summary))
        conditions = metadata.get("conditions", settings)
        record = {"id": directory.name, "kind": kind,
                  "decision": retained.get(directory.name, {}).get("decision", "historical"),
                  "evidence": "docs/BC.md" if kind.startswith("bc_") else "docs/EXPERIMENTS.md",
                  "source_record": "snapshot" if (directory / "source_snapshot").is_dir() else
                                   "hashes_only" if source_hashes else "unrecorded"}
        record["conditions"] = {key: settings[key] for key in ("track_ids", "seeds", "stage", "split")
                                if key in settings}
        record["conditions"].update({key: conditions[key] for key in ("frame_skip", "warmup", "target_speed")
                                     if key in conditions})
        if kind == "bc_model":
            record["checkpoint_sha256"] = history.get("best_checkpoint_sha256")
            record["conditions"].update({key: value for key, value in history.get("config", {}).items()
                                         if key in ("epochs", "history_frames", "active_gas_weight", "active_brake_weight")})
            record["status"] = "recorded" if history and (directory / "best.pt").is_file() else "partial"
        else:
            record.update(episodes=count, roads=len(roads), finishes=finishes,
                          status="recorded" if summary or manifest else "partial")
            if "track_ids" in settings and "seeds" in settings:
                record["planned_episodes"] = len(settings["track_ids"]) * len(settings["seeds"]) * settings.get("repeats", 1)
                if count != record["planned_episodes"]:
                    record["status"] = "partial"
            if paired:
                record["oracle_finishes"] = sum(bool(episode["reference"]["finished"]) for episode in episodes)
        if retained.get(directory.name, {}).get("note"):
            record["note"] = retained[directory.name]["note"]
        if directory.name.startswith("v2_selected_"):
            record["decision"] = "local_teacher_candidate"
        elif directory.name.startswith(("expanded_first_", "expanded_repeat_")):
            record["decision"] = "frozen_v1_reference"
        elif directory.name in ("bc_model_geometry_control_v10", "bc_model_geometry_expanded_v10", "bc_model_history8_v11"):
            record["decision"] = "negative_bc_comparison"
        elif directory.name.startswith(("v2_profile_", "v2_racing_")):
            record["decision"] = "rejected_variant"
        records.append(record)
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=Path, default=ROOT / "runs")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/RUNS.json")
    args = parser.parse_args(argv)
    previous = read_json(args.output).get("runs", [])
    records = catalog(args.runs, previous)
    args.output.write_text('{\n  "schema_version": 1,\n  "artifact_root": "runs",\n  "runs": [\n'
                          + ",\n".join("    " + encode(record) for record in records) + "\n  ]\n}\n")
    print(f"Indexed {len(records)} retained run directories in {args.output}")


if __name__ == "__main__":
    main()
