# Behavior Cloning: Reproduction and Evidence

## Current Entry Point

Current scope and next gates live in [plan/BC.md](plan/BC.md); the sections below
are chronological evidence, not concurrent instructions. The latest recorded
comparison is [History8 Closed Loop and Decision](#history8-closed-loop-and-decision).
Older pending/restart statements describe their checkpoint dates, not current jobs.
The compact [run catalog](RUNS.json) indexes preserved artifacts; regenerate it
with `python -m oracle.catalog` without rerunning experiments.

Tooling maintenance now uses unit action-loss weights by default. Historical
weighted/motion/recovery/split-head options remain explicit diagnostic settings,
not the current baseline. Historical commands below now spell out their recorded
gas weight of 40 instead of relying on the old default; saved invocation strings
and artifacts remain unchanged. New train/evaluation runs record source fingerprints
and recoverable snapshots. Old records are not retroactively source-certified.

## Frozen Teacher and Split

`oracle-v1` tags `a70b35950414a930d5ddaad4ac15733e65774345`, the
unchanged privileged obstacle-avoiding oracle that finished 100/100 episodes on
50/50 configurations (IDs 1-5 x seeds 1-10, twice each; ten base geometries).
ID 5/seed 3 finished with damage 0.2 both times. Those configurations were
exposed to earlier oracle decisions; they are not the BC final local test.
Duplicate deterministic runs of the same road are not additional training rows.

The BC geometry split was declared before collecting any new trajectories:

| Role | Geometry seeds | Track IDs | Base geometries | Status |
| --- | --- | --- | ---: | --- |
| Previously exposed oracle roads | 1-10 | 1-5 | 10 | Excluded from BC holdout |
| BC training pool | 11-30 | 1-5 | 20 | Select bounded subset below |
| BC validation pool | 31-35 | 1-5 | 5 | Select bounded subset below |
| Final local test pool | 36-40 | 1-5 | 5 | Do not inspect until model selection ends |

Track IDs change obstacle layouts, but the geometry is shared between IDs at
the same seed. Thus the split is by geometry seed, not independently by road
file, frame, or track ID. This is a *local* final test, not the unseen private
competition tracks. Every split uses `continuous=True`, physical obstacles,
`domain_randomize=False`, 50 no-op warmup frames, frame skip four, stack four,
and at most 2,000 actions in the original unmodified supplied environment.

## Data Contract

`python -m bc.dataset` creates a new directory; compatible existing collections
require `--resume`. Saved attempts are distinct from environment termination and
training eligibility, so finalized step-limit failures are retained, not rerun.
For each selected `(track_id, seed)` it stores one complete attempt: an `.npz`
with exact pre-action wrapper `float32` grayscale image stacks and the oracle
`float32` `[steer, gas, brake]` targets, plus a per-step JSONL analysis sidecar,
episode geometry/conditions, summary, SHA-256 and source/package provenance.
The sidecar contains progress, speed, pose, heading, damage, oracle diagnostics,
finish/termination and collision; **none of it enters the model**. The manifest
admits only fully completed oracle finishes as BC examples; failures remain
preserved for inspection. One road is collected once, not repeatedly.

The selected first-stage subset is IDs 1-5 with train seeds 11-20 (up to 50
distinct roads / ten geometries), validation seeds 31-33 (up to 15 roads / three
geometries). This is less than the reserved pool and must not be described as
testing all available seeds. Seed 11's separate one-episode oracle smoke test
finished (track 1, 957 actions, damage 0); this is already exposed development
evidence, not final evaluation. Collection commands:

```bash
python -m bc.dataset --output runs/bc_train_v1 --split train --track-ids 1 2 3 4 5 --seeds 11 12 13 14 15 16 17 18 19 20
python -m bc.dataset --output runs/bc_val_v1 --split val --track-ids 1 2 3 4 5 --seeds 31 32 33
```

Use fresh output directories when reproducing; `runs/` and weights are ignored
by Git. The training script opens only declared train and validation road
files, streams them one road at a time, samples no more than a fixed per-epoch
budget distributed over all training roads, and selects its best checkpoint by
validation mean component MSE in the first experiment. Subsequent experiments
also report and select by the explicitly noted rare-action-weighted metric.
It reports train and validation error separately
by action component. The final split is not loaded during fitting or selection.

```bash
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --output runs/bc_model_v1 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device cpu --active-gas-weight 1
python -m bc.evaluate --checkpoint runs/bc_model_v1/best.pt --split val --track-ids 1 --seeds 31 --output runs/bc_closed_val_probe_v1
```

The evaluator reruns the teacher and the image-only student separately on
identical reset conditions, and also queries the privileged teacher on student
states **for diagnostics only**. Saved traces preserve both actions, position,
speed, progress, damage, curvature, nearest-obstacle distance and done flags.
Summary reports the first component to differ from the reference at a fixed
action threshold, the first same-state teacher/student action mismatch, and
first 2-unit position deviation. Such thresholds are operational diagnostics,
not proof of cause; sub-frame deviations may precede them. Finish confirmation
is `finish_time_s`, not proxy reward or progress.

## Decision Gate

After the selected checkpoint and analysis plan are frozen using **validation
only**, execute the final local test on a previously unseen subset of seeds
36-40, documenting exact IDs, seeds, complete episode and road denominators.
Do not change the model in response to that test and then call it untouched.
Poor offline prediction directs investigation to observability/representation;
good offline prediction but gradual closed-loop error suggests compounding
distribution shift. Only if this is observed, consider oracle relabeling of
*student-visited* failure/recovery states (not repeated normal oracle runs).
No RL or official submission/confirmation is authorized by this phase.

## Outcomes

The training oracle collection in `runs/bc_train_v1` completed **50/50 full
episodes on 50/50 roads**, IDs 1-5 x seeds 11-20 (ten geometries): 55,363
unique pre-action image/action pairs, all with actual finish confirmation and
zero damage. Its manifest lists exactly 50 eligible trajectories. These are
distinct roads, not deterministic repeat copies.

The validation oracle collection in `runs/bc_val_v1` completed **15/15 full
episodes on 15/15 roads**, IDs 1-5 x seeds 31-33 (three geometries), all with
actual finish confirmation, progress 1.0 and zero damage. Its manifest lists
15 eligible trajectories. These oracle finishes do not establish BC success.

The first five-epoch CPU CNN run (`runs/bc_model_v1`, checkpoint SHA-256
`7d3ca4ff9ccf0ff27c5d0fa4e7fc69549fbe4c6234cd1e80c6754e0b72bce5a8`)
used at most 20,000 samples per epoch. Selected validation mean MSE was
0.0005833 across 15,676 held-out actions. Its final train prediction on 55,363
actions had component MAE steer 0.00712, gas 0.02907, brake 0.01696;
validation at the selected epoch had gas MAE 0.02930.

The first actual closed-loop trial, ID 1 / seed 31, **failed 0/1 episode on 0/1
road**: teacher finished in 1,013 actions, but student retired after 403 actions
at progress 0.2993, stopped near an obstacle (3.806 world units from center).
The first sampled action mismatch was **gas at step 0**: teacher
`[steer 0.03663, gas 0.4, brake 0]`, student approximately
`[steer 0.00905, gas 0.02890, brake 0.01669]`; first position separation
over 2 world units was step 4. Trace: `runs/bc_closed_val_probe_v1`.
The obstacle-adjacent stop is a terminal symptom, not the earliest departure.
In all 15,676 held-out teacher actions, 105 had gas >0.1; on those actions
student mean gas was 0.0281 versus teacher 0.2721 (MAE 0.2441). The low
aggregate loss obscured a crucial rare-action prediction failure. This is an
offline action-fit/encoding problem, **not evidence for DAgger** yet.

Targeted next experiment: keep data, observation, architecture, random seed,
and budget, but weight squared gas error 40x only on teacher actions >0.1;
select epoch by validation weighted component MSE. This is supervised loss
rebalancing, not reward shaping. Device `auto` uses available CUDA for training,
but `BCPolicy.from_checkpoint` still loads CPU for submission-style inference.
CUDA forward/backward and CPU unit smoke tests passed; no long auxiliary
verification. Run and result:

```bash
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --output runs/bc_model_weighted_v2 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --active-gas-weight 40
```

The weighted CUDA model selected epoch 5 (checkpoint SHA-256
`8caadb864572a06da3c5c32f51b8bb4a1575882da6234b8ca0f5c82325ab7a9b`).
Its held-out high-gas (>0.1) MAE improved from 0.2441 to 0.1882, but mean
prediction was still 0.0839 versus teacher 0.2721 (105/15,676 actions).
Normal validation gas MAE worsened from 0.02930 to 0.04460; this negative
tradeoff is retained. The same validation road ID 1/seed 31 failed again,
**0/1 episode on 0/1 road** (teacher 1/1): student retired at step 155,
progress 0.1022. Initial oracle/student gas 0.4/0.088; first >2-unit pose
divergence occurred at step 19. At student step 19, speed was 19.09 versus
oracle target speed 12, with teacher-on-student brake 0.5 versus student 0.011;
step 50 speed was 29.48, brake 0.5 versus 0.010. It ultimately ran at ~35,
far outside normal oracle trajectories. Trace:
`runs/bc_closed_val_weighted_probe_v2`. The initial gas error remains, and
the brake mismatch after leaving the demonstrated speed regime provides
direct evidence of student-state coverage/distribution shift; this does **not**
establish that compounding shift was the sole cause of the failure.

Only now introduce recovery labels: replay the *student* on six training roads
(IDs 1-3 x seeds 11-12), query the frozen oracle at each visited state, store
the actual student observation/teacher action in separate NPZ files, and
retrain with a fixed 25% budget of those states. Original oracle trajectories
are not duplicated, and validation seeds never enter recovery training:

```bash
python -m bc.evaluate --checkpoint runs/bc_model_weighted_v2/best.pt --split train --track-ids 1 2 3 --seeds 11 12 --output runs/bc_recovery_v2_train --collect-recovery
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --recovery-dataset runs/bc_recovery_v2_train --output runs/bc_model_recovery_v3 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --active-gas-weight 40
```

The same validation probe must be rerun after this targeted recovery pass.

Recovery collection completed **0/6 student finishes on 6/6 training roads**;
all 6/6 reference oracle episodes finished. On three track IDs at seed 12,
the complete student observation/action traces are exactly identical, so the
trainer includes that trace only once rather than inflating the recovery set.
Four distinct recovery trajectories remain (seed 11 on IDs 1-3, seed 12 on
ID 1). The 25% training budget replays their student-visited observations with
fresh oracle action labels, without changing the original 50-road dataset.

Recovery v3 (`runs/bc_model_recovery_v3`) was a negative result: the same
ID 1/seed 31 validation road still finished **0/1 episodes on 0/1 road**,
retiring after 136 actions with progress 0.1314. Initial gas was 0.074 vs
teacher 0.4; at student step 20 speed was 19.1 and oracle brake 0.5, but
student brake ~0.006. At step 100 speed exceeded 42. Recovery from only two
training geometries did not generalize speed control on this validation
geometry. The selected checkpoint's ordinary validation steer MSE also
worsened to 0.00161 (v2 was 0.00019). This does not imply recovery labels
are wrong; the representation/coverage explanation remains a hypothesis.

Image motion is observable without privileged speed: on student ID 1/seed 11,
mean absolute difference between the last and preceding grayscale frames rose
from ~0.0020 near speed 9.5 to ~0.0256 near speed 37.3. At normal oracle
speeds it was ~0.002-0.003. The next isolated representation change appends
two means of absolute temporal pixel differences, computed strictly from the
four available policy frames, to the CNN head; all trajectory labels, recovery
states, training budget and action loss remain fixed. This is still simple
supervised BC, not privileged speed input or a world model:

```bash
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --recovery-dataset runs/bc_recovery_v2_train --output runs/bc_model_motion_v4 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --motion-features --active-gas-weight 40
```

Motion+recovery v4 also failed **0/1 episode on 0/1 validation road** (ID 1,
seed 31, teacher finished 1/1). Compared with v3's unbounded acceleration,
student speed now stayed roughly 10-15 at sampled steps 26-130, consistent
with the image-motion feature being useful; causality is not isolated because
this is one seed. At step 15 steering differed by >0.08 (student +0.043,
same-state oracle -0.041). By steps 50/80/130 signed road-center error was
-5.7/-13.9/-29.4, with student steering often opposite the oracle. It retired
after 158 actions at progress 0.0730, speed 8.76 and center error about -55.
Its ordinary validation steer MSE was 0.000683 (v2: 0.000188), gas MSE
0.00470; recovery labels may have compromised normal-road fitting, but that
explanation is untested. The first mismatch still occurred at step 0 in gas.

To isolate recovery contamination from temporal representation, v5 keeps
the motion features and all other settings but removes recovery sampling:

```bash
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --output runs/bc_model_motion_no_recovery_v5 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --motion-features --active-gas-weight 40
```

Motion-only v5 reduced ordinary held-out steering MSE to 0.000142 but still
finished **0/1 episode on 0/1 road** (ID 1/seed 31), retiring after 126
actions at progress 0.0365. At step 18 student speed reached 17.4 and oracle
brake was 0.432 versus student 0.012; steering then reversed relative to
the oracle and it left the road. Ordinary validation gas MAE was 0.0469.
Thus aggregate offline steering accuracy did not rescue closed-loop control.

Diagnostic split-head v6, using v1's unweighted steering output and v4's
gas/brake output (both receive the same allowed image stack), likewise failed
**0/1 episode on 0/1 road** after 446 steps and progress 0.3029. It kept
speed closer to the target but stalled near an obstacle (3.807 units from
center). Before the impact, at step 100, student steering was -0.112 while
same-state oracle steering was +0.408, path error 4.8; by step 250 the obstacle
was 32 units away, and by step 300 student speed fell below 0.4 adjacent to it.
The terminal stall is not the first departure. Command:

```bash
python -m bc.evaluate --checkpoint runs/bc_model_motion_v4/best.pt --steer-checkpoint runs/bc_model_v1/best.pt --split val --track-ids 1 --seeds 31 --output runs/bc_closed_val_split_heads_probe_v6
```

Next, collect this composite *student's* actual pre-impact/obstacle-approach
states on training IDs 1-2 x geometry seeds 11-15 (never validation/test),
oracle-label them, and fit only the steering channel on those recovery states.
Keep the separately trained v4 gas/brake outputs and select the new steering
checkpoint by validation steering MSE. This isolates the observed new failure
mode rather than repeatedly copying successful teacher trajectories:

```bash
python -m bc.evaluate --checkpoint runs/bc_model_motion_v4/best.pt --steer-checkpoint runs/bc_model_v1/best.pt --split train --track-ids 1 2 --seeds 11 12 13 14 15 --output runs/bc_recovery_split_heads_v6_train --collect-recovery
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --recovery-dataset runs/bc_recovery_split_heads_v6_train --output runs/bc_model_steer_recovery_v7 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --active-gas-weight 1 --recovery-steering-only
```

The split-head student collected **0/10 finishes on 10/10 training roads**
(IDs 1-2 x seeds 11-15); paired oracle finished **10/10**. Its progress
ranged 0.105-0.640. These are off-policy visits, not normal oracle replay.
Steering-only recovery v7 paired with v4 gas/brake substantially improved
the same validation road to progress **0.7117**, but still **0/1 complete
episodes on 0/1 road**. At student steps 500/530 (ahead of an obstacle),
student speeds were 15.2/17.0 with brake ~0.03-0.04, whereas the oracle at
those states commanded brake 0.26/0.40. At step 550 the obstacle was 18.9
units away, and collision began at step 563. Repeated collision flags raised
damage from 0 to 1.0 by step 568; episode retired after 569 actions. Five
collision-positive wrapper steps may reflect continued/renewed contact with
the same obstacle, not necessarily five distinct objects. The first sampled
action mismatch remained initial gas at step 0; the brake shortfall before
impact is the directly observed proximate control issue. Command:

```bash
python -m bc.evaluate --checkpoint runs/bc_model_motion_v4/best.pt --steer-checkpoint runs/bc_model_steer_recovery_v7/best.pt --split val --track-ids 1 --seeds 31 --output runs/bc_closed_val_split_recovery_v7
```

Next fit only gas/brake on the existing split-head student's training-road
states while retaining v7 steering. Give teacher brake >0.1 tenfold loss
weight (rare on successful normal trajectories) and select by held-out
gas/brake weighted MSE. No more normal oracle trajectory collection:

```bash
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --recovery-dataset runs/bc_recovery_split_heads_v6_train --output runs/bc_model_controls_recovery_v8 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --motion-features --active-gas-weight 40 --active-brake-weight 10 --recovery-controls-only
```

Controls-recovery v8 was worse: **0/1 validation episode on 0/1 road**, after
81 actions at progress 0.1131, speed ~45. Student gas was ~0.17 even when
the teacher on that state commanded gas 0/brake 0.5. Validation gas MAE rose
to 0.1432 at the selected epoch (v4: 0.0587). Combining a 25% recovery
sampling fraction with 40x rare-gas loss gave much more weight to the stopped
student's high-gas labels than to normal low-gas driving, an interpretation
consistent with both offline and closed-loop regressions but not a proven
single cause. Do not report v8 as a recovery success.

One bounded corrective comparison retains the recovery labels and v7 steering
but sets high-gas weighting to 1, caps recovery at 5% of epoch samples, and
keeps 10x emphasis on important >0.1 brake labels. It remains image-only
supervised learning with explicit val-based selection:

```bash
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --recovery-dataset runs/bc_recovery_split_heads_v6_train --output runs/bc_model_controls_conservative_v9 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --motion-features --active-gas-weight 1 --active-brake-weight 10 --recovery-controls-only --recovery-fraction 0.05
```

Conservative controls v9 also finished **0/3 validation episodes on 0/3
roads** (ID 1 x seeds 31-33; oracle 3/3), with respective terminal progress
0.7117, 0.2203, 0.2721. The student was slower than v7 on seed 31 but still
ended beside the same obstacle. Initial gas fell to ~0.027 against teacher
0.4, and the first >2-unit pose difference occurred by step 4. v7/v4 on the
same three validation roads also finished **0/3**; seed 31 reached progress
0.7117 but retired from damage at step 569, while seeds 32/33 stalled near
obstacles at progress 0.2203/0.2721. The lack of a reliable full lap is a
clear BC limitation of these small image-action models and sampled recovery
states; no winner can be labeled a successful BC baseline. The repeated
local validation trials are exposed model-development evidence, not an
independent performance estimate.

Before reading any final-test road, freeze the *local diagnostic candidate*
as v7 steering checkpoint SHA-256
`c24703506cecd66a10103ffa182db09974c03face98885728fd780559d627d36`
plus v4 gas/brake checkpoint SHA-256
`423089cf44823c094b5349e1a311699be7d5bb3cb08e850d564bda7030f2a6c4`.
It is selected for farther progression on validation seed 31, not because it
finished. Keep it fixed. Evaluate exactly one episode per ID 1-5 x final-test
geometry seeds 36-37 (10 roads / two base geometries) without using these
results for another model choice. Remaining seeds 38-40 stay unexamined.

```bash
python -m bc.evaluate --checkpoint runs/bc_model_motion_v4/best.pt --steer-checkpoint runs/bc_model_steer_recovery_v7/best.pt --split test --track-ids 1 2 3 4 5 --seeds 36 37 --output runs/bc_final_local_v7
```

The frozen candidate final local test completed **0/10 student full-episode
finishes on 0/10 distinct roads** (IDs 1-5 x seeds 36-37, two base geometries);
paired unchanged oracle completed **10/10 on 10/10**. No episode is missing or
externally interrupted. These seeds are now exposed evidence and must not be
reused as an untouched holdout for a future candidate. Seeds 38-40 were not
examined. Student progress ranged 0.1103-0.8425; these numbers are internal
failure diagnostics, not official ranking scores. The complete traces and
source checkpoint hashes are in ignored `runs/bc_final_local_v7/`.

| Track ID | Seed 36: progress / termination | Seed 37: progress / termination |
| ---: | --- | --- |
| 1 | 0.2862 / off_track | 0.4799 / off_track |
| 2 | 0.2276 / off_track | 0.5165 / off_track |
| 3 | 0.1207 / off_track | 0.4103 / off_track |
| 4 | 0.1103 / off_track | 0.5897 / crash |
| 5 | 0.1517 / off_track | 0.8425 / crash |

All 10 students had at least one collision-positive action and nonzero damage;
8/10 retired from the wrapper's negative-reward `off_track` streak after
collision-associated stalls, 2/10 retired at damage 1.0. The terminal
nearest-obstacle-center distances were ~3.81-4.83 units. The *first*
collision on each road happened earlier, at action 93-410 (sampled pre-impact
speed 9.49-17.16); the oracle's same-state steering often had larger magnitude
near impact, but its difference alone does not establish a single collision
cause. On **10/10** roads the first sampled action mismatch was gas at step 0,
and the first >2-unit pose difference was step 26. Thus the earliest recorded
deviation predates obstacle impact, and impact/stall is not mislabeled as
the initial fault. Some camera/vehicle effects within frame-skip ticks remain
unobserved. No parameter, model, checkpoint, or split was changed in response
to this final-test result.

## Interpretation and Next Gate

The initial CNN's attractive aggregate validation MSE concealed a failure to
predict rare startup gas. Weighting those labels improved conditional offline
gas error but did not finish the first road. At student-visited speeds 19-45,
the oracle demanded hard braking while the image-only student often kept gas
on; recovery data from two geometries did not solve this. A temporal image
motion feature reduced runaway speed in one matched validation comparison,
but steering and obstacle avoidance still failed. Steering-only student-state
relabeling improved one exposed validation road to 0.7117 progress and the
final candidate reached as far as 0.8425 on a final local road, but *none*
finished. The likely bottlenecks are actionable offline tail prediction,
closed-loop state coverage, and visual obstacle/speed representation; causal
isolation and generalization remain unproven. More deterministic oracle
repeats or a prettier average loss are not an answer. `oracle-v1` remains the
successful **privileged local teacher**, not a submission policy; no BC model
is promoted to a reliable finisher baseline. A future BC iteration should
draw diverse *student-visited* failure/recovery states on new training roads,
preserve a fresh untouched final geometry group, and benchmark component-
conditional offline errors plus full laps before considering any different
algorithm. RL fine-tuning is **not started or authorized** on these results.
No official submission or model confirmation was made.

## Geometry Versus Observability Gate (v10 Onward)

The 2026-09-29 user instruction supersedes the earlier suggestion to collect
more recovery states first. Do not retry v1-v9 weighting, recovery proportions,
motion features, or split-head combinations. New training collection is exactly
IDs 1-5 x seeds 21-30, once per road, with the frozen oracle and original
environment settings. Combine eligible trajectories with existing seeds 11-20;
the intended pool is 100 roads / 20 geometries, not 100 independent geometries.
Validation remains IDs 1-5 x seeds 31-33. Seeds 34-35 and 38-40 stay unopened;
36-37 remain exposed historical evidence and are not used in this comparison.

Predeclared geometry-only comparison: plain `BCPolicy-v1`, no motion feature,
no recovery, unit action-loss weights, Adam learning rate 0.001, seed 0,
5 epochs, batch size 64, 20,000 training samples per epoch, CUDA for both arms.
The old road-local batching would give 350 versus 400 optimizer steps for 50
versus 100 roads. Both new arms instead carry partial batches across road
boundaries, giving 313 updates per epoch. A fresh 10-geometry matched control
is therefore necessary; historical CPU v1 is context, not the causal control.
Keep validation checkpoint selection unchanged (unweighted mean component MSE)
to avoid mixing data diversity with a selection change, but judge the comparison
by conditional errors and closed-loop finishes, not that aggregate loss.

Report gas >0.1, brake >0.1, and absolute steer >0.1 conditional counts, MAE,
MSE, target means and prediction means; empty bins are explicitly unavailable.
Evaluate both selected checkpoints on IDs 1-5 x seeds 31-33, one complete
episode per road (15 roads / three development geometries). Zero finishes in
both arms is insufficient evidence of meaningful reliability improvement even
if progress or offline errors improve. A gain on this one training seed is
provisional, not replicated causal proof or an unseen generalization estimate.
If neither arm finishes, proceed to a single longer-history pixel comparison
with identical data/loss/budget before auxiliary targets or other changes.
This tests diversity under a fixed sample budget: doubling roads halves samples
per road per epoch. A null result does not rule out more diverse data with more
training, nor establish partial observability as the cause. Changing history is
a next diagnostic intervention, not a conclusion inferred from two failures.

Collection:

```bash
python -m bc.dataset --output runs/bc_train_geometry_v10 --split train --track-ids 1 2 3 4 5 --seeds 21 22 23 24 25 26 27 28 29 30
```

Matched training and evaluation commands (run each training output once):

```bash
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --output runs/bc_model_geometry_control_v10 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device cuda --active-gas-weight 1 --active-brake-weight 1 --continuous-batches
python -m bc.train --dataset runs/bc_train_v1 --extra-train-dataset runs/bc_train_geometry_v10 --val-dataset runs/bc_val_v1 --output runs/bc_model_geometry_expanded_v10 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device cuda --active-gas-weight 1 --active-brake-weight 1 --continuous-batches
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_geometry_control_v10/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --output runs/bc_closed_geometry_control_v10
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_geometry_expanded_v10/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --output runs/bc_closed_geometry_expanded_v10
```

Historical launch checkpoint (superseded by the completed results below):
results pending; launching a run is not evidence of completion. Tooling checks:
13 trainer tests passed, including exact sampled-row order/RNG preservation,
20,000 samples / 313 updates for each road count, manifest separation and
conditional metrics. Another 22 dataset, rollout and local-contract tests passed.

### Restart Checkpoint

Kilo was closed and restarted during v10. At 2026-09-29 21:17 UTC the plain
10-geometry control had completed all five epochs, each with 20,000 samples and
313 updates. Its selected epoch is 5; checkpoint SHA-256 is
`3c0baf4bb17d1771024e06a79d0de6e1680f346721c6adcbb12b08c2ad8f661c`.
Its validation conditional MAE is high gas 0.243083 (105/15,676 actions), high
brake 0.215553 (15/15,676), and large steer 0.007834 (2,386/15,676).
These are offline results, not driving success. The partial closed-loop record
contains 0/5 student finishes on 0/5 roads versus 5/5 oracle finishes; the
planned 15-road comparison is not complete.

New-road collection had 17 completed road summaries and one interrupted
attempt (ID 2 / seed 28), not a completed 50-road dataset. Completed roads must
not be recollected; interrupted artifacts are retained separately when resumed.
Do not train the expanded arm before the full collection manifest is finalized.
Remaining work resumes from stored artifacts, not from original commands that
would overwrite/repeat output directories. Long-running jobs launched after
this restart use the process manager's persistent lifetime.

Validation resume was launched with persistent lifetime after compatible
checkpoint/settings checks and six evaluator tests (14 subtests) passed:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_geometry_control_v10/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --output runs/bc_closed_geometry_control_v10 --resume
```

Resume preserves the prior summary and interrupted traces, skips completed
paired roads, and atomically updates each new paired result. Its launch does
not imply the remaining ten roads have finished.

Collection also resumed persistently, with the original frozen teacher and
environment hashes verified; completed roads were skipped and the interrupted
ID 2 / seed 28 files archived instead of discarded:

```bash
python -m bc.dataset --output runs/bc_train_geometry_v10 --split train --track-ids 1 2 3 4 5 --seeds 21 22 23 24 25 26 27 28 29 30 --resume
```

Integrated dataset/trainer/evaluator/local-contract suite: 40 tests passed after
the restart changes. The manifests are finalized only after the full grid runs.

### Matched Control Result

The 10-geometry control evaluation is complete: **0/15 student complete-episode
finishes on 0/15 distinct roads**, versus **15/15 oracle finishes on 15/15 roads**
(IDs 1-5 x seeds 31-33; three exposed development geometries). No result is
missing or externally interrupted in the resumed final summary. Student
termination was `off_track` on 13 roads and `crash` on two roads (IDs 3 and 5,
seed 31). Progress ranged 0.1131-0.6678, an internal diagnostic only. The first
recorded action mismatch was gas at step 0 and first >2-unit pose divergence
was step 4 on every road. This is not a reliable finisher baseline.

| Track ID | Seed 31 Progress | Seed 32 Progress | Seed 33 Progress |
| ---: | ---: | ---: | ---: |
| 1 | 0.2993 | 0.2203 | 0.2721 |
| 2 | 0.5730 | 0.1797 | 0.6678 |
| 3 | 0.1350 | 0.1729 | 0.3145 |
| 4 | 0.1131 | 0.1390 | 0.2120 |
| 5 | 0.3650 | 0.1661 | 0.5618 |

Historical control-only checkpoint: expanded-data model results remain pending;
the control alone cannot distinguish
the two hypotheses. New collection is now complete: **50/50 full oracle episodes
on 50/50 roads**, IDs 1-5 x seeds 21-30, ten new base geometries and **56,031**
pre-action image/action rows. All 50 trajectories are eligible. ID 3 / seed 25
finished with damage 0.2; the other 49 finished without damage. No incomplete
episode remains in the finalized manifest; the restart-interrupted attempt is
retained separately, not counted as another successful learning trajectory.
Combined with the original 55,363 rows, training contains **111,394 unique
rows on 100 roads / 20 geometries**. At 21:53 UTC expanded CNN training followed
by the full 15-road validation evaluation was launched persistently.

### Expanded CNN Offline Result

The 20-geometry CNN completed all five epochs, each with 20,000 samples and
313 updates, identical to the control. Selected epoch 5 checkpoint SHA-256:
`ced7e5232c1090d42fd4423d06e00af9b328e71bffbb0374ec2ae391e191fa6d`.
Validation uses exactly the same 15,676 teacher-state action rows in both arms.

| Conditional Metric | Validation Count | 10 Geometries MAE / MSE | 20 Geometries MAE / MSE |
| --- | ---: | ---: | ---: |
| Gas >0.1 | 105 | 0.243083 / 0.077312 | 0.242314 / 0.076909 |
| Brake >0.1 | 15 | 0.215553 / 0.046463 | 0.214889 / 0.046177 |
| Absolute steer >0.1 | 2,386 | 0.007834 / 0.000101 | 0.010273 / 0.000202 |

High-gas prediction means are 0.029054/0.029823 against target 0.272136;
high-brake means are 0.017819/0.018484 against target 0.233372. Tail gas/brake
underprediction is essentially unchanged, and conditional steering worsened.
The gas/brake tails are tiny, especially 15 brake rows; do not overstate small
numerical differences as replicated effects. Mean component MSE is
0.000569686/0.000575290, but is not the primary success criterion.
Expanded closed-loop evaluation is now complete: **0/15 student full-episode
finishes on 0/15 roads**, versus **15/15 oracle finishes on 15/15 roads**, IDs
1-5 x seeds 31-33. Fourteen students terminated `off_track`; ID 3 / seed 31
terminated `crash`. Every road's first recorded action mismatch was gas at
step 0, with first >2-unit pose divergence at step 4. There are no missing
episodes. Progress ranged 0.1131-0.8248; farther progress on ID 1 / seed 31
does not rescue the unchanged zero finish count, and other roads regressed.

| Track ID | Expanded Seed 31 Progress | Expanded Seed 32 Progress | Expanded Seed 33 Progress |
| ---: | ---: | ---: | ---: |
| 1 | 0.8248 | 0.2203 | 0.2756 |
| 2 | 0.1752 | 0.1797 | 0.4028 |
| 3 | 0.2044 | 0.1729 | 0.5795 |
| 4 | 0.1131 | 0.1390 | 0.2085 |
| 5 | 0.2518 | 0.1661 | 0.3286 |

**Geometry gate:** expanding 10 to 20 training geometries alone did not improve
complete-episode reliability under this fixed budget and one training seed.
This rejects the sufficiency of this specific intervention, not geometry
diversity in general; reduced samples per road and limited training remain
alternative explanations. It does not prove partial observability. Proceed to
the predeclared longer-history comparison, without reweighting or recovery.

### Conditional Temporal Protocol

If the completed geometry comparison has no meaningful finish improvement,
test an eight-frame early-fusion CNN on exactly the expanded training roads.
The wrapper appends one image per decision, normally four simulator ticks
(80 ms), so four frames span 240 ms and eight span 560 ms. Reconstruct row `t`
from `observations[max(0, t-lag), 3]` for lags 7 through 0, then sample/shuffle
the target rows. Repeat the reset image for missing history; never cross roads,
include future frames, or concatenate overlapping four-frame stacks as if
their channels were independent timestamps. Online history must match this
reconstruction exactly and reset between episodes.

Change only the first convolution input from four to eight channels; retain
the remaining CNN/head, action transforms, loss and selection. Initialize from
the same fresh seed-0 four-frame CNN used by the expanded control: copy shared
parameters, copy its first-layer weights into the newest four channels and
zero the older four channels. This preserves the initial function, rather than
warm-starting from a trained checkpoint. Parameter count rises from 31,659 to
33,707 (6.5%); disclose this modest capacity confound. Keep five epochs,
20,000 samples / 313 updates per epoch, unit loss weights, no recovery or motion
features, and the same validation roads. This is a bounded test of additional
causal pixel history, not a complete observability diagnosis. Auxiliary targets
and recurrent encoders are separate possible later interventions, not mixed
into this first history comparison.

### History8 Implementation and Run

Implemented the above reconstruction and episode-reset semantics with only
the first convolution widened. Tests verify exact seeded shared parameters
and RNG preservation, equal initial function within numerical tolerance,
nonzero older-channel gradients, causal indexed batches, online/offline history
equality, episode isolation, and checkpoint compatibility. The new checkpoint
format is `BCPolicy-history8-v3`. Thirty-five targeted BC tests passed; supplied
environment and submission `agent.py` remain unchanged.

After the completed geometry gate, history8 training and full validation were
launched persistently at 22:19 UTC:

```bash
python -m bc.train --dataset runs/bc_train_v1 --extra-train-dataset runs/bc_train_geometry_v10 --val-dataset runs/bc_val_v1 --output runs/bc_model_history8_v11 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device cuda --active-gas-weight 1 --active-brake-weight 1 --continuous-batches --history-frames 8
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_history8_v11/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --output runs/bc_closed_history8_v11
```

Validation seeds 34-35 and final-local seeds 38-40 remain unexamined. No RL,
auxiliary-target trial, submission or model confirmation.

### History8 Offline Result

History8 completed five epochs, each 20,000 samples / 313 optimizer updates,
with the same expanded roads and sampled-row RNG as the four-frame model.
Selected epoch 5 checkpoint SHA-256:
`79e05ca13082bb0d41f27e02f7824bee14e90fba70865d425d6ca7001581cec7`.

| Conditional Metric | Validation Count | Expanded Four Frames MAE / MSE | Expanded Eight Frames MAE / MSE |
| --- | ---: | ---: | ---: |
| Gas >0.1 | 105 | 0.242314 / 0.076909 | 0.243393 / 0.077436 |
| Brake >0.1 | 15 | 0.214889 / 0.046177 | 0.215610 / 0.046488 |
| Absolute steer >0.1 | 2,386 | 0.010273 / 0.000202 | 0.013617 / 0.000288 |

High-gas mean prediction is 0.028743 versus target 0.272136; high-brake mean is
0.017762 versus target 0.233372. Mean component MSE is 0.000578268. Longer
history did not improve the action tails; large-steer conditional error worsened.
The integrated BC/local-contract suite passed 50 tests after history changes.

### History8 Closed Loop and Decision

History8 full evaluation completed **0/15 student full-episode finishes on
0/15 distinct roads**, versus **15/15 oracle finishes on 15/15 roads**, IDs
1-5 x seeds 31-33 (three exposed development geometries). All 15 student
episodes reached environment termination; none is missing or interrupted.
Every student road had at least one collision-positive action. Twelve students
terminated `off_track`; three terminated `crash` (IDs 2, 3 and 5 / seed 31).
Every road's first recorded action mismatch remained gas at step 0, and first
>2-unit pose divergence at step 4. The later collision is not the earliest
recorded departure. Progress ranged 0.1131-0.5051, not an official score.

| Track ID | History8 Seed 31 Progress | History8 Seed 32 Progress | History8 Seed 33 Progress |
| ---: | ---: | ---: | ---: |
| 1 | 0.2993 | 0.2203 | 0.2721 |
| 2 | 0.3613 | 0.3797 | 0.4028 |
| 3 | 0.4818 | 0.5051 | 0.3145 |
| 4 | 0.1131 | 0.1390 | 0.2933 |
| 5 | 0.3650 | 0.3424 | 0.3286 |

| Comparison | Training Geometries | Pixel History | Student Finishes / Episodes | Successful Roads / Roads | Paired Oracle Finishes / Episodes |
| --- | ---: | ---: | ---: | ---: | ---: |
| v10 matched control | 10 | 4 | 0/15 | 0/15 | 15/15 |
| v10 expanded data | 20 | 4 | 0/15 | 0/15 | 15/15 |
| v11 history8 | 20 | 8 | 0/15 | 0/15 | 15/15 |

**Evidence-limited conclusion:** neither doubling training geometry alone nor
doubling causal image history with this CNN established a finisher, and neither
improved the high-gas/high-brake conditional fit materially. The interventions
are separated, but each comparison uses only training seed 0, five epochs and
an equal 100,000 sample presentations; these are not replicated negative results
for all BC models. More geometries at the same budget reduce exposure per road;
history8 adds 6.5% parameters. Validation is exposed development evidence, not
an untouched estimate. Fifteen high-brake rows limit that conditional estimate.

At reset, all historical frames repeat the same image: history8 provides no
additional startup information, so its failure to correct the step-0 gas
underprediction does not diagnose whether speed/curvature/obstacle information
later in a lap is observable. We have not directly probed those latent quantities
or demonstrated observational aliasing. It would be incorrect to claim that
four-frame privileged-action imitation is fundamentally impossible, or that
partial observability is proven from zero finishes. Representation, optimization
and rare-action fit remain unresolved alongside off-policy state coverage.

Do not revisit v1-v9 small loss/recovery changes. A next discriminating BC
intervention can measure speed/curvature/lateral-error/obstacle-proximity decoding
from pixels, then test one lightweight temporal encoder or one auxiliary target
with matched action-training conditions. Privileged values must remain training
targets/diagnostics only, never policy inputs. Those trials are **not started**
in this comparison; no RL or successful submission candidate is established.
Protected seeds 34-35 and 38-40 remain unopened. All commands, conditional counts,
hashes, complete traces and negative results are retained in the named artifacts.
