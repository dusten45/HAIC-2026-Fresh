# Oracle Experiments: Phase 1-2

Experiment protocol, reproduction commands, full-episode evidence, and limitations.

## Scope and Fixed Conditions

All observations in this log come from this independent restart. No earlier
research code/results were imported. Only local diagnostics and privileged
geometry control are in scope; no training or official submission is performed.

- Initial exposed evaluation configurations: track IDs 1-4, geometry seeds 1-5.
- Initial denominators: 20 road/obstacle configurations, five base geometries.
- Expanded scope (2026-09-29 user request): track IDs 1-5, seeds 1-10, 50
  configurations / 10 base geometry seeds; see the expansion record below.
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

`oracle/oracle_runner.py` creates a fresh output directory, saves run/source/package
metadata, actual centerline and obstacle conditions, per-action JSONL traces,
and a summary. Existing output directories are rejected to preserve evidence.
Generated artifacts live under ignored `runs/`; this compact log is versioned.
Every trace links pre-action state and diagnostics to action, reward, post-action
state, environment done flags, and observation summary/hash. Images themselves
are not being collected as a Phase 3 imitation dataset.

Create the artifact parent once with `mkdir -p runs`. Commands below are run
from the repository root. Use a new output name when repeating an experiment.
Historical commands below now explicitly select the original grid because the
runner defaults were expanded to 50 configurations. Original invocation strings
remain unchanged in the saved run metadata.

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
python -m oracle.oracle_runner --mode noop --track-ids 1 --seeds 1 --output runs/phase1_noop_track1_seed1
python -m oracle.oracle_runner --mode random --track-ids 1 --seeds 1 --output runs/phase1_random_track1_seed1
python -m oracle.oracle_runner --mode manual --track-ids 1 --seeds 1 --output runs/phase1_manual_track1_seed1
python -m oracle.oracle_runner --mode manual --manual-steering 0.2 --max-steps 20 --track-ids 1 --seeds 1 --output runs/phase1_manual_right_track1_seed1
python -m oracle.oracle_runner --mode manual --manual-steering -0.2 --max-steps 20 --track-ids 1 --seeds 1 --output runs/phase1_manual_left_track1_seed1
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
python -m oracle.oracle_runner --mode oracle --track-ids 1 --seeds 1 --output runs/centerline_initial
python -m oracle.oracle_report runs/centerline_initial --events
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
python -m oracle.oracle_runner --mode oracle --track-ids 1 2 3 4 --seeds 1 2 3 4 5 --output runs/centerline_matrix
python -m oracle.oracle_report runs/centerline_matrix --events
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
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 1 --seeds 1 --output runs/avoidance_initial
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 1 2 3 4 --seeds 1 2 3 4 5 --output runs/avoidance_matrix
```

Single-road probe: 1/1 full episode finished (track 1 / seed 1), 1,006 actions,
progress 1.0, damage 0. Initial matched matrix command hit the external shell's
600-second wall limit after 13 completed episodes, all finished with zero damage
(IDs 1-2/seeds 1-5 and ID 3/seeds 1-3). ID 3/seed 4 trace was interrupted and
is excluded from complete-episode denominators; do not count this operational
interruption as a simulator failure. The partial directory is preserved.

Remaining seven cases completed in fresh directories, yielding **20/20 complete
episodes finished on all 20/20 configurations**, with no collisions or damage.

```bash
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 3 --seeds 4 5 --output runs/avoidance_matrix_remaining3
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 4 --seeds 1 2 3 4 5 --output runs/avoidance_matrix_remaining4
python -m oracle.oracle_report runs/avoidance_matrix runs/avoidance_matrix_remaining3 runs/avoidance_matrix_remaining4
```

The combined report explicitly shows original 13/20 summaries, one interrupted
trace, six unstarted cases, and seven completed replacements. The interrupted
trace is retained but excluded. Summary counting does not silently relabel a
partial matrix as complete. Duplicate report directory arguments are rejected.

### Matched Per-Road Results

Baseline is 0/1 finished on every row; avoidance is 1/1 finished on every row.
First impact location uses the post-action centerline segment index. `stuck`
means collision followed by zero terminal speed and negative-reward retirement;
`damage` means damage=1 retirement, not necessarily five different obstacles.

| ID | Seed | Baseline Failure | First Impact Step / Segment | Avoidance Actions | Lap ms | Max Center Error |
| ---: | ---: | --- | --- | ---: | ---: | ---: |
| 1 | 1 | stuck | 494 / 134 | 1006 | 80400 | 3.531 |
| 1 | 2 | stuck | 466 / 126 | 1232 | 98420 | 2.635 |
| 1 | 3 | stuck | 114 / 30 | 998 | 79740 | 2.965 |
| 1 | 4 | damage | 425 / 116 | 1010 | 80680 | 3.289 |
| 1 | 5 | damage | 473 / 129 | 1210 | 96700 | 2.728 |
| 2 | 1 | stuck | 399 / 108 | 1009 | 80640 | 1.551 |
| 2 | 2 | stuck | 147 / 39 | 1234 | 98640 | 3.504 |
| 2 | 3 | stuck | 410 / 111 | 997 | 79660 | 3.544 |
| 2 | 4 | stuck | 261 / 70 | 1015 | 81080 | 3.009 |
| 2 | 5 | stuck | 217 / 58 | 1212 | 96840 | 3.367 |
| 3 | 1 | damage | 359 / 97 | 1014 | 81040 | 3.506 |
| 3 | 2 | damage | 221 / 60 | 1228 | 98120 | 3.315 |
| 3 | 3 | damage | 122 / 33 | 997 | 79680 | 3.273 |
| 3 | 4 | stuck | 414 / 112 | 1008 | 80540 | 3.699 |
| 3 | 5 | stuck | 191 / 51 | 1214 | 97040 | 3.093 |
| 4 | 1 | stuck | 144 / 38 | 1012 | 80880 | 3.591 |
| 4 | 2 | stuck | 312 / 84 | 1233 | 98540 | 3.287 |
| 4 | 3 | stuck | 275 / 74 | 987 | 78860 | 3.493 |
| 4 | 4 | stuck | 198 / 53 | 1012 | 80840 | 3.382 |
| 4 | 5 | stuck | 251 / 68 | 1208 | 96500 | 3.473 |

All avoidance runs reached progress 1.0 **and** confirmed the finish gate. Lap
range: 78.86-98.64 s; action range: 987-1,234, below the unchanged 2,000 limit.
Across 21,836 actions, no collision-positive action and no commanded steering
target at/above physical +/-0.4 rad. Maximum absolute command: 0.384628 rad.
Maximum sampled speed: 14.912719 (target 12); maximum sampled reference-path
error: 1.078458. Centerline error up to 3.699 is intentional obstacle clearance,
not failure to follow the shifted path. Events are sampled every wrapper action;
we do not claim raw-tick maxima between those samples.

Artifact comparison also verifies identical centerline/obstacle data for all
20 baseline-versus-avoidance pairs. The report correctly flags two execution
fingerprints for that comparison (baseline versus changed path), but just one
fingerprint across the resumed avoidance matrix. Fingerprints compare source
hashes, controller/wrapper arguments, Python and installed package versions,
rather than relying only on a Git revision that may contain uncommitted files.

### Frozen Repetitions

Controller and runner frozen at `bf85da7`; two additional full episodes per
configuration, in independent track-ID processes:

```bash
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 1 --seeds 1 2 3 4 5 --repeats 2 --output runs/verification_track1
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 2 --seeds 1 2 3 4 5 --repeats 2 --output runs/verification_track2
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 3 --seeds 1 2 3 4 5 --repeats 2 --output runs/verification_track3
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 4 --seeds 1 2 3 4 5 --repeats 2 --output runs/verification_track4
python -m oracle.oracle_report runs/verification_track1 runs/verification_track2 runs/verification_track3 runs/verification_track4
```

Use a sufficiently long shell budget (tested execution allowance 1,200 seconds
per command) rather than a 600-second allowance for the full serial 20-road
matrix. Simulated time and finish conditions are unchanged by wall-clock budget.
Repetition results: **40/40 complete episodes finished on all 20/20
configurations**, two further successes per configuration. No incomplete/missing
verification episodes, no collisions, no damage, progress 1.0 and actual finish
confirmation in every episode. Each road's two verification traces are byte-
identical; they also match that road's first-matrix trace exactly.

Combined main evaluation: **60/60 complete episodes finished, 20/20
configurations each successful 3/3 times**. This excludes the separate successful
single-road probe (1/1) and the explicitly preserved externally interrupted
attempt. All seven main-result directories share one execution fingerprint:
identical controller/runner/environment source hashes, control settings and
Python/package versions. Actual geometry/obstacles match on 20/20 roads; there
are five unique base geometries. Exact repeated trace hashes match on 20/20
roads. Across 65,508 actions: zero collision-positive actions and zero commanded
steering targets reaching physical +/-0.4 rad. Step/lap/error maxima remain
identical to the first-matrix table above.

```bash
python -m oracle.oracle_report runs/avoidance_matrix runs/avoidance_matrix_remaining3 runs/avoidance_matrix_remaining4 runs/verification_track1 runs/verification_track2 runs/verification_track3 runs/verification_track4
```

Decision: Phase 1-2 local success target met. The simple privileged system
actually produces repeatable complete laps on the requested set. No further
parameter tuning, broader-road claims, or transition to learning is justified
by this task. Stop here with the controller available as a future reference.

## Validation and Limits

```bash
python -m unittest tests.test_local_contract tests.test_oracle_controller tests.test_oracle_runner tests.test_oracle_report -v
git diff dfb7a2d --exit-code -- env_wrapper.py damage.py core/ agent.py local_runner.py requirements.txt
```

27 local tests pass. Original environment, sample Agent, official local runner
and dependency requirements remain unchanged. An independent review found two
reporting pitfalls (silent partial runs and repeated directory arguments); both
were fixed and tested. No controller/termination issue invalidating the current
20-road evidence was found.

This demonstrates successful local behavior using privileged geometry and state,
not pixel-only observability or submission eligibility. All five geometry seeds
and 20 obstacle configurations are exposed evaluation. Deterministic repetitions
do not establish generalization, robustness to perturbed starts/physics, or
private-track performance. Global nearest-path projection may jump on sufficiently
close nonadjacent road sections; the simple offset path is not a formal swept-
vehicle clearance guarantee. No such failure was observed on the declared set,
so additional mechanisms or broader experiments are not introduced speculatively.

No RL/BC model, Phase 3 bulk observation dataset, official submission, or model
confirmation has been created. The local diagnostic traces are retained for
reproduction/failure inspection, with images represented only by hashes/statistics.

## Expansion: IDs 1-5, Seeds 1-10

User-authorized expansion on 2026-09-29. Retain the existing controller from
`bf85da7` and all physics/wrapper/control parameters. Only change runner CLI
defaults and permit ID 5. The 30 added configurations join the 20 previously
exposed ones; none are claimed as an untouched holdout once examined.

First run all 50 configurations with explicit track/seed arguments in bounded
five-episode batches. Inspect failures before considering a controller change.
If all finish, repeat the same 50 once with frozen code, for a balanced 100
complete episodes across 50 configurations. This remains Phase 1-2 only.

CLI grid regression and actual ID 5 / seed 10 reset and
external-limit tests pass; full local suite now has 28 passing tests.

### Expansion Protocol and First Observation

Evaluation checkpoint: `27d9656`. Controller still byte-identical to `bf85da7`;
no speed, lookahead, clearance, physics or episode-limit change. Each of IDs
1-5 is evaluated in two batches with explicit seeds `1 2 3 4 5` and
`6 7 8 9 10`, output directories `runs/expanded_first_t<ID>_low` / `_high`.
Each batch uses normal full episodes and a generous external shell allowance,
not a shortened simulation horizon. Example commands:

```bash
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 5 --seeds 1 2 3 4 5 --output runs/expanded_first_t5_low
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 5 --seeds 6 7 8 9 10 --output runs/expanded_first_t5_high
python -m oracle.oracle_report runs/expanded_first_t5_low runs/expanded_first_t5_high
```

First completed ID: track 5, **10/10 full episodes finished** on seeds 1-10.
Actions 926-1,236, laps 73.94-98.80 s. Unlike the original 20-case result,
this includes one collision-positive action on ID 5 / seed 3: action 754, segment 206,
post-position (43.6545, -74.8166), damage 0.2. Obstacle center is
(46.6393, -73.4063). Before impact, path error increased from 0.007 at action 751
to 0.194, 0.347, then 0.540 at action 754 near a bend; command steer remained
unsaturated. All four wheels remained on-road in these samples, and speed did
not collapse (11.568 before impact, 12.559 afterward). It finished at action 995,
79.50 s, without another collision or stall. This is a **completed episode with
damage**, not a failure or evidence of zero-collision generalization. The
mechanism is consistent with insufficient vehicle clearance near the curved
reference path, but that causal explanation has not been isolated experimentally.
Keep the controller unchanged while completing the rest of the expanded matrix.

### Expanded First-Pass Result

**50/50 complete episodes finished on 50/50 configurations**, including all 30
added configurations. No interrupted traces or unstarted/missing episodes.
All 50 reached progress 1.0 and actual finish confirmation. Forty-nine had no
damage; only ID 5 / seed 3 had one collision-positive action and final damage 0.2.

| Track ID | Finishes / Episodes | Damaged Episodes | Action Range | Lap Range (ms) |
| ---: | ---: | ---: | --- | --- |
| 1 | 10/10 | 0/10 | 926-1232 | 73960-98420 |
| 2 | 10/10 | 0/10 | 925-1234 | 73900-98640 |
| 3 | 10/10 | 0/10 | 923-1228 | 73760-98120 |
| 4 | 10/10 | 0/10 | 927-1233 | 74080-98540 |
| 5 | 10/10 | 1/10 | 926-1236 | 73940-98800 |

Ten unique base geometries verified from actual geometry data. All 10 batch
directories share one source/settings/package fingerprint. Across 53,757 actions:
one collision-positive action, zero steering targets reaching +/-0.4, no hull-
center departure beyond road half-width. Sampled maxima: speed 14.927980,
absolute command steer 0.384628, reference-path error 1.293480. Largest centerline
error 4.125 occurred on ID 4 / seed 9; this is measured against the road centerline,
not the intentionally shifted reference path.

Decision: no controller change is warranted to achieve the requested finish
objective on this evidence. Retain the nonzero-damage case explicitly instead
of tuning unrelated parameters or claiming collision-free performance. Run one
additional full episode for each of the same 50 configurations, under identical
conditions, and compare complete trace hashes.

```bash
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 1 --seeds 1 2 3 4 5 6 7 8 9 10 --output runs/expanded_repeat_t1
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 2 --seeds 1 2 3 4 5 6 7 8 9 10 --output runs/expanded_repeat_t2
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 3 --seeds 1 2 3 4 5 6 7 8 9 10 --output runs/expanded_repeat_t3
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 4 --seeds 1 2 3 4 5 6 7 8 9 10 --output runs/expanded_repeat_t4
python -m oracle.oracle_runner --mode oracle --avoid-obstacles --track-ids 5 --seeds 1 2 3 4 5 6 7 8 9 10 --output runs/expanded_repeat_t5
```

### Expanded Repetition and Final Decision

The repeat pass finished **50/50 complete episodes**. Combined expanded result:
**100/100 episodes finished on all 50 configurations, each successful 2/2 times**.
No incomplete traces or missing episodes in either pass. Historical 60-episode
initial-set results are kept separate, not added into this balanced denominator.

All 50 roads have identical full trace hashes across the two executions,
including the collision on ID 5 / seed 3 at action 754. That configuration has
final damage 0.2 in each episode but finishes both; the other 49 configurations
are damage-free in both episodes. Thus **98/100 episodes were damage-free**,
not 100/100. There were two collision-positive actions across 107,514 actions.
There was no hull-center road departure or commanded steer reaching +/-0.4.

All 15 run directories share one execution fingerprint (source hashes, control
settings, Python/packages), actual geometry/obstacles match on 50/50 roads, and
10 distinct base geometries are present. Episode length remains 923-1,236
actions; actual finish lap range 73.76-98.80 simulation seconds. Sampled maxima
are unchanged from the first-pass report.

```bash
python -m oracle.oracle_report runs/expanded_first_t1_low runs/expanded_first_t1_high runs/expanded_first_t2_low runs/expanded_first_t2_high runs/expanded_first_t3_low runs/expanded_first_t3_high runs/expanded_first_t4_low runs/expanded_first_t4_high runs/expanded_first_t5_low runs/expanded_first_t5_high runs/expanded_repeat_t1 runs/expanded_repeat_t2 runs/expanded_repeat_t3 runs/expanded_repeat_t4 runs/expanded_repeat_t5
```

Final validation: 28 local tests passed. `oracle/oracle_controller.py` is unchanged
from `bf85da7`; protected environment, original Agent/runner and requirements
are unchanged from `dfb7a2d`. The only executable change for expansion is CLI
grid defaults and ID validation in the external `oracle/oracle_runner.py`.

Expanded local finish target met without retuning. Stop at Phase 1-2. These are
exposed evaluation roads and deterministic repeatability results, not an
untouched holdout, collision-free guarantee, submission policy or evidence of
private-track generalization. No BC/RL, Phase 3 collection or submission began.
