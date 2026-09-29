# Oracle Experiments: Phase 1-2

## Scope and Fixed Conditions

All observations in this log come from this independent restart. No earlier
research code/results were imported. Only local diagnostics and privileged
geometry control are in scope; no training or official submission is performed.

- Exposed evaluation configurations: track IDs 1-4, geometry seeds 1-5.
- Denominators: 20 road/obstacle configurations, five distinct base geometries.
- Unmodified official `variables-6` environment, initial source `dfb7a2d`.
- Python 3.11.14, Gymnasium 0.29.1, Box2D 2.3.5, NumPy 1.26.0, OpenCV 4.8.1.
- `continuous=True`, `domain_randomize=False`, physical obstacles enabled by
  `options={"track_id": id}`, grass friction 0.6, six obstacles of radius 1.2.
- Frame skip 4, stack 4, no-op warmup 50, negative-reward limit 100, outer budget
  2,000 actions; raw TimeLimit is `max_steps*frame_skip+200` as in local runner.
- Headless SDL affects display only. All physics and RGB observation rendering
  remain enabled; the wrapper's actual preprocessed observation is checked.
- Completion uses `info["finished"]` / non-null `finish_time_s`, never progress
  alone. Reward is not an official score. Repetitions on the same seeds test
  determinism/repeatability, not statistical generalization to unseen tracks.

## Artifacts and Reproduction

`oracle_runner.py` creates a fresh output directory, saves run/source/package
metadata, actual centerline and obstacle conditions, per-action JSONL traces,
and a summary. Existing output directories are rejected to preserve evidence.
Generated artifacts live under ignored `runs/`; this compact log is versioned.
Every trace links pre-action state and diagnostics to action, reward, post-action
state, environment done flags, and observation summary/hash. Images themselves
are not being collected as a Phase 3 imitation dataset.

Create the artifact parent once with `mkdir -p runs`. Commands below are run
from the repository root. Use a new output name when repeating an experiment.

## Phase 1 Verification

- Official template revision checked remotely on 2026-09-29 and matched local
  starting source. Public website ranking semantics agree with the template.
- Original test suite: 15 passed, 1 server-parity test skipped (server absent).
  Later test commands select individual local files to avoid the optional
  sibling-repository probe.
- Projection/wrap, steering sign, and proportional speed feedback unit tests:
  3 passed before actual controller evaluation.
- Real diagnostics on track 1 / seed 1 (one road, one full episode per mode):

| Mode | Finish | Steps | Progress | Damage | Termination |
| --- | --- | ---: | ---: | ---: | --- |
| No-op | 0/1 | 101 | 0.007273 | 0 | negative-reward off_track |
| Random (action seed 0) | 0/1 | 299 | 0.076364 | 0 | negative-reward off_track |
| Constant gas 0.2, steer 0 | 0/1 | 89 | 0.076364 | 0 | playfield exit, y=334.86 |

No-op verifies that a stationary car on the centerline can be retired as
`off_track`. Reset time is 1.02 s, observation is `(4,84,84)` float32 within
`[0,1]`. Full baseline lengths are 7.12-23.92 simulation seconds after warmup;
these are not representative of successful driving.

Matched 20-action manual checks with steering +/-0.2 and gas 0.2 confirm action
positive means right: final joints -0.200001 rad, yaw rate -2.19379, lateral error
-26.6596. Negative action reverses these signs (lateral error +26.8719). These
are deliberately bounded diagnostics, NOT complete episodes; both stop at the
runner cap without environment termination/truncation, first leaving road width
at action 12. No changes to steering sign are needed.

```bash
python oracle_runner.py --mode noop --track-ids 1 --seeds 1 --output runs/phase1_noop_track1_seed1
python oracle_runner.py --mode random --track-ids 1 --seeds 1 --output runs/phase1_random_track1_seed1
python oracle_runner.py --mode manual --track-ids 1 --seeds 1 --output runs/phase1_manual_track1_seed1
python oracle_runner.py --mode manual --manual-steering 0.2 --max-steps 20 --track-ids 1 --seeds 1 --output runs/phase1_manual_right_track1_seed1
python oracle_runner.py --mode manual --manual-steering -0.2 --max-steps 20 --track-ids 1 --seeds 1 --output runs/phase1_manual_left_track1_seed1
```

These artifacts and the first oracle episode predate diagnostic-only additions
of velocity components, wheel-on-road counts, tile counts, reward streak and
lap milliseconds. Their source hashes remain in metadata. No physics/controller
parameters changed during these additions.

## Initial Controller Hypothesis

Baseline: cyclic centerline pure pursuit from the rear axle, wheelbase 3.24,
lookahead `6 + 0.25*speed`, target speed 12 world units/s. Proportional gas
`clip(0.12*(12-speed),0,0.4)` and brake `clip(0.08*(speed-12),0,0.5)`.
Steering commands the simulator's joint-angle target with its correct sign,
without an incorrect division by the physical 0.4-rad steering limit.

This intentionally ignores obstacles initially, to separate geometric following
from obstacle interaction. Hypothesis: conservative pursuit can follow road
geometry, but centerline obstacles may cause collision/stall failures.

## Results and Decisions

### Initial Single-Road Probe

```bash
python oracle_runner.py --mode oracle --track-ids 1 --seeds 1 --output runs/centerline_initial
python oracle_report.py runs/centerline_initial --events
```

0/1 complete episodes finished on 0/1 road. At step 612, progress 0.501818,
damage 0.4, negative-reward `off_track`. Maximum center error only 1.536;
no hull-center departure beyond road half-width.

Earliest directly observed failure onset: collision at action 494, near waypoint
134-135, position (-109.1814,8.0883). At action 493 speed was 11.558 and center
error 0.072; next action speed fell to 2.937 and damage rose from 0 to 0.2. By
the terminal window speed was zero at (-109.1404,6.3459), despite gas 0.4, near
an obstacle center (distance 3.805); progress remained fixed. This supports a
collision/stuck classification, not corner overshoot or incorrect steering.
Collision avoidance is the next isolated candidate change, after measuring the
unchanged centerline baseline across all 20 configurations.

All negative results remain in this log and local artifacts. Do not advance to
learning based on incomplete episodes or high tile-visit percentage alone.

### Unchanged Centerline Matrix

```bash
python oracle_runner.py --mode oracle --output runs/centerline_matrix
python oracle_report.py runs/centerline_matrix --events
```

At code checkpoint `073cb4f`: **0/20 episodes, 0/20 configurations finished**.
All 20 encountered collisions. Fifteen terminated via collision-associated
stall/negative-reward streak; five via damage retirement (1/4, 1/5, 3/1, 3/2,
3/3). No hull center left the road half-width. Episodes lasted 128-612 actions.
First-collision and terminal windows were inspected for every failure. This
supports changing obstacle handling rather than adjusting road-following speed
or steering gain. The first collision is the earliest directly observed adverse
event, not a claim to identify the earliest sub-frame causal deviation.

### Single Change: Obstacle-Offset Reference Path

Keep target speed, gas/brake gains, pursuit wheelbase/lookahead, physics and
evaluation conditions unchanged. Only change the reference path: project each
obstacle onto centerline, choose the opposite side, and shift waypoints to give
radius + 1.4 vehicle half-width + 1.2 tracking margin (3.8 total for radius 1.2).
Blend displacement with a raised cosine over +/-25 arc-length units; unchanged
centerline elsewhere. This is not MPC or learned planning. Explicitly select
with `--avoid-obstacles`; omitting that flag preserves the negative baseline.

```bash
python oracle_runner.py --mode oracle --avoid-obstacles --track-ids 1 --seeds 1 --output runs/avoidance_initial
python oracle_runner.py --mode oracle --avoid-obstacles --output runs/avoidance_matrix
```

Single-road probe: 1/1 full episode finished (track 1 / seed 1), 1,006 actions,
progress 1.0, damage 0. Initial matched matrix command hit the external shell's
600-second wall limit after 13 completed episodes, all finished with zero damage
(IDs 1-2/seeds 1-5 and ID 3/seeds 1-3). ID 3/seed 4 trace was interrupted and
is excluded from complete-episode denominators; do not count this operational
interruption as a simulator failure. The partial directory is preserved.

Current action: finish the remaining seven matrix cases in fresh directories,
then verify all 20 configurations twice more with the same frozen controller.
