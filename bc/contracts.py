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
