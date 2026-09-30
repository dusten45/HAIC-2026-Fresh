"""Pure shared split, observation and unchanged BC baseline contracts."""

SPLIT_SEEDS = {"train": list(range(11, 31)), "val": list(range(31, 36)),
               "test": list(range(36, 41))}
EXPOSED_SEEDS = list(range(1, 11))
TRACK_IDS = (1, 2, 3, 4, 5)
OBSERVATION_SHAPE = (4, 84, 84)
SIMULATOR_FPS = 50
BASELINE_CONDITIONS = {
    "render_mode": "rgb_array", "domain_randomize": False,
    "frame_skip": 4, "warmup": 50, "stack_frames": OBSERVATION_SHAPE[0],
    "target_speed": 12.0, "avoid_obstacles": True, "max_steps": 2000,
    "raw_frame_budget": 8200,
}


def environment_conditions(conditions):
    """Separate environment settings from legacy v1 teacher settings."""
    return {key: value for key, value in conditions.items()
            if key not in ("target_speed", "avoid_obstacles")}


def verify_environment_conditions(provenance, label):
    actual = environment_conditions(provenance.get("conditions", {}))
    deviations = {key: {"expected": value, "actual": actual.get(key)}
                  for key, value in environment_conditions(BASELINE_CONDITIONS).items()
                  if actual.get(key) != value}
    if deviations:
        raise ValueError(f"{label} collector conditions deviate from BC baseline: {deviations}")
    return actual
