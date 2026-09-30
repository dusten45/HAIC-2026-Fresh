"""Local research recording helpers, independent of simulator and CLI bootstrap."""

import dataclasses
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

import numpy as np


ROOT = Path(__file__).resolve().parent.parent
FPS = 50
TRACK_WIDTH = 40 / 6
FROZEN_SOURCES = ("env_wrapper.py", "damage.py", "local_runner.py",
                  "oracle/oracle_runner.py", "oracle/oracle_controller.py")


def json_default(value):
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return dataclasses.asdict(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def encode(value):
    return json.dumps(value, default=json_default, allow_nan=False, sort_keys=True)


def vehicle_state(base):
    hull = base.car.hull
    position = np.asarray(hull.position, dtype=float)
    points = np.asarray(base.track, dtype=float)[:, 2:4]
    segments = np.roll(points, -1, axis=0) - points
    lengths2 = np.sum(segments * segments, axis=1)
    fractions = np.clip(np.sum((position - points) * segments, axis=1)
                        / np.maximum(lengths2, 1e-12), 0, 1)
    projections = points + fractions[:, None] * segments
    distances = np.linalg.norm(position - projections, axis=1)
    index = int(np.argmin(distances))
    tangent = segments[index] / max(float(np.sqrt(lengths2[index])), 1e-12)
    left = np.array([-tangent[1], tangent[0]])
    velocity = np.asarray(hull.linearVelocity, dtype=float)
    forward = np.array([-np.sin(hull.angle), np.cos(hull.angle)])
    return {"position": position, "angle": float(hull.angle), "velocity": velocity,
            "speed": float(np.linalg.norm(velocity)),
            "forward_velocity": float(np.dot(velocity, forward)),
            "right_velocity": float(np.dot(velocity, [forward[1], -forward[0]])),
            "wheels_on_road": sum(bool(w.tiles) for w in base.car.wheels),
            "tile_visited_count": base.tile_visited_count,
            "angularVelocity": float(hull.angularVelocity),
            "front_steering": [float(w.joint.angle) for w in base.car.wheels[:2]],
            "t": float(base.t), "raw_frame": round(base.t * FPS),
            "track": {"segment": index, "fraction": float(fractions[index]),
                      "projection": projections[index], "tangent": tangent,
                      "center_error": float(np.dot(position - projections[index], left)),
                      "center_distance": float(distances[index]), "road_halfwidth": TRACK_WIDTH}}


def execution_fingerprint(sources=()):
    paths = {ROOT / name for name in (*FROZEN_SOURCES, "oracle/recording.py", *sources)}
    paths.update((ROOT / "core").rglob("*.py"))
    packages = {}
    for name in ("numpy", "gymnasium", "opencv-python", "box2d-py", "torch"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {"source_sha256": {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in sorted(paths)},
            "python": sys.version, "packages": packages}


def snapshot_sources(output, fingerprint):
    """Keep recoverable source, not just hashes, without rewriting prior snapshots."""
    hashes = fingerprint["source_sha256"]
    digest = hashlib.sha256(encode(hashes).encode()).hexdigest()
    directory = Path(output) / "source_snapshot" / digest
    if not directory.exists():
        directory.mkdir(parents=True)
        for name, expected in hashes.items():
            source = ROOT / name
            if hashlib.sha256(source.read_bytes()).hexdigest() != expected:
                raise ValueError(f"Source changed before snapshot: {name}")
            destination = directory / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    return str(directory.relative_to(output))


def provenance(args, sources=()):
    def git(*command):
        return subprocess.check_output(["git", *command], cwd=ROOT, text=True).strip()

    status = git("status", "--porcelain", "--untracked-files=all")
    return {"args": vars(args), "command": sys.argv, "git_revision": git("rev-parse", "HEAD"),
            "git_dirty": bool(status), "git_status": status,
            **execution_fingerprint(sources), "platform": platform.platform(),
            "sdl": {key: os.environ.get(key) for key in ("SDL_VIDEODRIVER", "SDL_AUDIODRIVER")},
            "render_mode": "rgb_array", "fps": FPS, "domain_randomize": False,
            "center_error_convention": "signed left of increasing track index",
            "event_resolution": "wrapper step boundaries; collision may occur anywhere within skipped frames",
            "limits": "runner max_steps/timeout do not set environment truncated",
            "road_designation": "exposed development/evaluation, not untouched holdout"}
