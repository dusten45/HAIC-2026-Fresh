# Behavior Cloning: Reproduction and Evidence

## Current Entry Point

Current scope and next gates live in [plan/BC.md](plan/BC.md); the sections below
are chronological evidence, not concurrent instructions. The latest diagnosis is
[Train Fit and Prefix Gate](#train-fit-and-prefix-gate).
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

## Train Fit and Prefix Gate

The 2026-09-30 user instruction pauses more data and simple frame-stack increases.
First distinguish poor fitting on training roads from a train/validation gap,
then intervene on startup with a fixed student, before choosing one next change.
No privileged state may become a learned-policy input. No RL or official action.

### Fixed-Checkpoint Offline Diagnosis

No new training: evaluated the selected expanded four-frame v10 and history8 v11
checkpoints, unchanged hashes above, on all **111,394 train rows / 100 roads /
20 geometries** (IDs 1-5 x seeds 11-30) and **15,676 validation rows / 15 roads /
three exposed geometries** (IDs 1-5 x seeds 31-33). Same conditional thresholds,
metrics, model eval mode and causal history in both splits. The first ten actions
are indexed 0-9, restart per road and are reported individually plus pooled.
These are the full training-source datasets, not a claim that every row was
sampled during the five budgeted epochs. CUDA evaluation can differ minutely
from saved CPU evaluation through numerical kernels; no model was changed.

```bash
python -m bc.diagnose --checkpoint runs/bc_model_geometry_expanded_v10/best.pt runs/bc_model_history8_v11/best.pt --dataset runs/bc_train_v1 --extra-train-dataset runs/bc_train_geometry_v10 --val-dataset runs/bc_val_v1 --device cuda --output runs/bc_offline_fit_v12
```

| Condition | Train Count | Val Count | Four Frames Train / Val MAE | Eight Frames Train / Val MAE |
| --- | ---: | ---: | ---: | ---: |
| Gas >0.1 | 700 | 105 | 0.242433 / 0.242314 | 0.243509 / 0.243393 |
| Brake >0.1 | 100 | 15 | 0.214812 / 0.214889 | 0.215563 / 0.215610 |
| Absolute steer >0.1 | 20,735 | 2,386 | 0.009576 / 0.010273 | 0.012463 / 0.013617 |

History8 startup is equally poor on training roads. At step 0, gas MAE is
**0.371257 train / 0.371200 val**: target 0.4 versus prediction
0.028743 / 0.028800. The pooled first-ten-action MAE is steer
0.003601 / 0.005544, gas **0.174403 / 0.174365**, brake 0.043446 / 0.043449
(1,000 train / 150 val action rows). At action 4, brake MAE is
0.215563 / 0.215610; the student stays near 0.018 while the oracle asks for
about 0.233. It fails both acceleration and the early brake pulse, not just
the first gas command. Full per-step target/prediction means and MSE are in
`runs/bc_offline_fit_v12/summary.json` with checkpoint/manifest hashes and a
recoverable diagnostic source snapshot.

**Offline finding:** poor tail fitting already exists on the training pool,
with no material train/val gas/brake gap. A held-out-only generalization failure
is not supported; optimization/sampling/action representation must be checked
before privileging a state-decoding experiment. This does not prove that
observability is sufficient, or isolate which fitting mechanism is responsible.
The prefix outcomes and single selected intervention follow below.

### Fixed-Model Prefix Intervention

Executed oracle actions only for the first N actions, then handed control to the
unchanged history8 student. The student predicted on every observation, including
teacher-forced steps, so its causal history was not reset at handoff. Traces
separate prediction from execution; action errors during forced steps are not
mistaken for executed student controls. Same baseline wrapped environment,
physical obstacles, one complete episode per ID 1-5 x seed 31-33 per condition.

| Oracle Prefix | Student Finishes / Episodes | Successful Roads / Roads | Oracle Finishes / Episodes | First Post-Handoff Same-State Mismatch | First >2-Unit Pose Difference |
| ---: | ---: | ---: | ---: | --- | --- |
| 0 (v11 baseline) | 0/15 | 0/15 | 15/15 | Gas, step 0 | Step 4 |
| 1 | 0/15 | 0/15 | 15/15 | Gas, step 1 | Step 8 |
| 4 | 0/15 | 0/15 | 15/15 | Brake, step 4 | Steps 13-14 |
| 16 | 0/15 | 0/15 | 15/15 | Steer, steps 28-36 | Steps 117-140 |

All **45/45 diagnostic student episodes terminated without a finish on the same
15 roads / three geometries**, oracle **45/45**. These are three interventions,
not three independent geometries or reliability replicates. Prefix16 handoff
mean absolute errors steer/gas/brake are 0.003961/0.028523/0.040110, all below
the operational thresholds at handoff; nevertheless same-state steering differs
by >0.08 after only 12-20 autonomous actions. Delaying pose separation is a real
early-trajectory effect, not improved full-lap reliability. This establishes
that bypassing the first 16 actions is insufficient; it does not prove startup
never matters or isolate the later steering/state-shift mechanism.

Artifacts: `runs/bc_closed_prefix1_v12`, `bc_closed_prefix4_v12`, and
`bc_closed_prefix16_v12`. Commands use the same checkpoint and settings:

```bash
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_history8_v11/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --oracle-prefix-steps 1 --output runs/bc_closed_prefix1_v12
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_history8_v11/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --oracle-prefix-steps 4 --output runs/bc_closed_prefix4_v12
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_history8_v11/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --oracle-prefix-steps 16 --output runs/bc_closed_prefix16_v12
```

### Single Selected Intervention: Balanced Sampling

Both diagnoses support fixing training-pool tail fit before claiming a
held-out-only representation bottleneck; a startup override alone also failed.
Choose sampling only, not another historical weighted-loss variant. Keep the
history8 architecture/action transforms, fresh seed0 initialization, Adam
0.001, unit MSE and ordinary validation selection, five epochs, batch64,
20,000 presentations / 313 updates each, and the same 100 training roads.
Per road reserve floor(budget/8) high-gas and high-brake labels each, sample
with replacement only when needed, fill the remaining 3/4 from natural rows,
and shuffle target indices without reordering the chronological pixel source.
Missing bins return their budget to natural rows. Natural rows can also include
tails, so actual counts may slightly exceed the reserved fractions. These are
replayed original labels, not added trajectories or independent new evidence.

No loss weights, additional history, state auxiliary targets, recovery or new
model head are combined with this trial. Plain closed loop has no privileged
prefix. A source snapshot records concurrently added teacher-provenance tooling;
this run still uses the same frozen-v1 chronological datasets, not teacher views.
Completed outcomes are recorded below, after training and evaluation.

Sampler/startup/history/prefix/recording integration validation passed **49 tests
and 49 subtests**. Default sampling preserves its seeded natural-row order and
RNG, rare sampling preserves causal history, missing/threshold-equal bins return
their budget, and 100 roads still give 20,000 samples / 313 updates. The single
trial was launched persistently after the completed prefix gate, training then
plain evaluation and fixed-checkpoint offline diagnosis:

```bash
python -m bc.train --dataset runs/bc_train_v1 --extra-train-dataset runs/bc_train_geometry_v10 --val-dataset runs/bc_val_v1 --output runs/bc_model_balanced_v13 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device cuda --active-gas-weight 1 --active-brake-weight 1 --continuous-batches --history-frames 8 --balanced-actions
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_balanced_v13/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --output runs/bc_closed_balanced_v13
python -m bc.diagnose --checkpoint runs/bc_model_balanced_v13/best.pt --dataset runs/bc_train_v1 --extra-train-dataset runs/bc_train_geometry_v10 --val-dataset runs/bc_val_v1 --device cuda --output runs/bc_offline_balanced_v13
```

### Balanced Sampling Outcome and Gate Decision

Completed all five epochs, each **20,000 presentations / 313 updates**. Totals
are 100,000 presentations / 1,565 updates, with **12,976 high-gas** and
**12,560 high-brake** presentations, including natural draws. These are repeated
draws from the original 700/100 tail rows, not extra unique labels. Selected
epoch **4** by the unchanged ordinary validation mean MSE (0.000914352;
baseline 0.000578268). Checkpoint SHA-256:
`59d61c48c6da61c1d0f4fd82bd261c51aad27e23b7b7d35d6e6c765890a433a4`.
All three train/extra-train/val manifest hashes are identical to the previous
diagnosis. No road, action target, model input or controller was added/changed.

The same CUDA/batch128 fixed-checkpoint diagnosis provides the matched table:

| Metric | Train / Val Count | Natural Sampling Train / Val MAE | Balanced Sampling Train / Val MAE |
| --- | ---: | ---: | ---: |
| Gas >0.1 | 700 / 105 | 0.243509 / 0.243393 | 0.171502 / 0.172743 |
| Brake >0.1 | 100 / 15 | 0.215563 / 0.215610 | 0.154961 / 0.157208 |
| Absolute steer >0.1 | 20,735 / 2,386 | 0.012463 / 0.013617 | 0.017518 / 0.018576 |
| Step0 gas | 100 / 15 | 0.371257 / 0.371200 | 0.288174 / 0.291879 |
| First10 steer | 1,000 / 150 | 0.003601 / 0.005544 | 0.010884 / 0.011194 |
| First10 gas | 1,000 / 150 | 0.174403 / 0.174365 | 0.158636 / 0.159099 |
| First10 brake | 1,000 / 150 | 0.043446 / 0.043449 | 0.067862 / 0.066875 |

Gas/brake conditional errors improved on both splits, but neither fits the
training tails well. High-gas mean prediction is train 0.100679 / val 0.099393
versus targets 0.272180 / 0.272136. High-brake means are 0.078285 / 0.076164
versus 0.233247 / 0.233372. Step0 val still predicts gas **0.108121** instead
of 0.4, simultaneously predicting brake **0.078999** instead of 0. Full initial
0-9 component metrics are in `runs/bc_offline_balanced_v13/summary.json`.
Improved conditional tails alongside worse early pooled brake and steering is
not successful startup fitting. Raising both control baselines rather than
resolving the teacher's alternating pulses is consistent with these observations;
its underlying optimization/encoding cause is still a hypothesis.

Plain, **zero-prefix** closed loop completed **0/15 student full-episode finishes
on 0/15 successful roads**, versus **15/15 oracle on 15/15 roads**, IDs 1-5 x
seeds 31-33. All 15 terminated, none interrupted or missing; nine `off_track`,
six `crash`, and all 15 ended with nonzero damage. First same-state action
mismatch remains gas at step0 on every road; first >2-unit pose divergence is
step5 on every road (baseline step4). All traces are preserved in
`runs/bc_closed_balanced_v13`.

| Track ID | Seed31 Progress / Reason | Seed32 Progress / Reason | Seed33 Progress / Reason |
| ---: | --- | --- | --- |
| 1 | 0.3942 / off_track | 0.2237 / crash | 0.2792 / crash |
| 2 | 0.3650 / off_track | 0.1797 / off_track | 0.4064 / off_track |
| 3 | 0.1350 / crash | 0.3458 / off_track | 0.9505 / off_track |
| 4 | 0.6496 / crash | 0.4203 / off_track | 0.2120 / crash |
| 5 | 0.2518 / off_track | 0.1695 / crash | 0.3286 / off_track |

Progress is an internal proxy: even 0.9505 was an incomplete episode, not a
finisher. This is a **partially improved offline fit but negative reliability
result** for this bounded sampling trial, not evidence against every balanced
sampler. Only one training seed/budget was tested, rare brake has 15 val rows,
ordinary checkpoint selection can trade off tail fit, and these validation
roads are exposed development roads, not an untouched estimate or official score.

**Gate decision:** retain the diagnosis that training-pool rare-action fitting
is inadequate and no material gas/brake train/val gap has been established.
Startup alone is insufficient, and sampling alone at this fixed budget was
insufficient. Do not label the bottleneck proven partial observability or begin
privileged state decoding from these results. Action-mode/signed-longitudinal
parameterization or additional optimization remain possible later fitting
interventions, not experiments performed here. The requested diagnoses plus
exactly one selected intervention are complete; no second intervention, new
data, longer history, RL, protected seeds 34-35/38-40, submission or model
confirmation was started.

## Signed Longitudinal Only Trial (v14)

This historical user-authorized intervention changes longitudinal representation only.
First audited only `actions` arrays named by the training manifests, not
observations or validation/test data: `bc_train_v1` has 55,363 rows / 50 roads /
seeds 11-20; `bc_train_geometry_v10` has 56,031 rows / 50 roads / seeds 21-30.
Together these are **111,394 rows / 100 roads / 20 training geometries**, IDs 1-5.

| Strict Threshold | Gas Above | Brake Above | Both Above |
| --- | ---: | ---: | ---: |
| >0 | 55,777 | 55,617 | 0 |
| >0.01 | 55,674 | 55,513 | 0 |
| >0.05 | 54,940 | 1,500 | 0 |
| >0.1 | 700 | 100 | 0 |

No road had overlapping controls; `max(min(gas, brake))` is exactly zero.
Encoding `u = gas - brake` and decoding `gas=max(u,0), brake=max(-u,0)` therefore
preserves every audited training action, not just meaningfully active targets.
Both tail conditions occur on all 100 training roads. This verifies target
compatibility, not successful fitting or driving.

### Controlled Implementation

Keep the history8 CNN, 20 training geometries, unchanged per-road balanced
sampling, fresh seed0, Adam 0.001, batch64/continuous batches, five epochs and
20,000 draws / 313 updates per epoch. Build the original seeded architecture
before narrowing only its final linear layer to `[steer, signed_longitudinal]`,
copying its original first two rows without advancing initialization RNG.
All shared weights and the steering row initialize exactly as v13; steering
still uses tanh. Signed longitudinal uses tanh in [-1,1]. No classification head,
privileged inference input, recovery, new data or longer history is introduced.

Train directly on signed-control error, including incorrect direction, rather
than decoded gas/brake error. Loss is `(steer_MSE + signed_longitudinal_MSE)/3`,
preserving the original steering coefficient 1/3; a two-output mean would
silently increase it. This intentionally changes the longitudinal objective as
part of the representation intervention. Ordinary decoded three-action
validation mean MSE still selects the checkpoint; no tail-based selection or
extra loss weights. `BCPolicy-signed-history8-v4` retains image-only CPU `act`
and loads alongside the three existing saved formats. Train/validation metrics
now also report `prediction_gas - prediction_brake` error for all models using
the same original gas>0.1/brake>0.1 masks, plus signed startup errors at steps0-9.

Validation remains **IDs 1-5 x seeds 31-33**, unchanged physical obstacles,
frame_skip4, warmup50, cap2,000, domain_randomize false and official environment.
Seeds 34-35 and 38-40 remain unopened. These are exposed development roads, not
an untouched holdout or official ranking estimate.

Implementation checks: **48 tests passed** with
`python -m unittest tests.test_bc_history tests.test_bc_train tests.test_bc_evaluate`;
`git diff --check` passed. Covered shared/steering seeded initialization and RNG,
exclusive decoding, signed tail/startup arithmetic, trainer roundtrip, ordinary
selection and legacy saved checkpoints. The supplied environment and `agent.py`
are unchanged. Existing unrelated working-tree changes are preserved.

### Execution

Launched a persistent sequential pipeline: train, immediately evaluate plain
zero-prefix closed loop, then diagnose both fixed checkpoints with the same
CUDA/batch128 settings. No prefix intervention is used in this trial.

```bash
python -m bc.train --dataset runs/bc_train_v1 --extra-train-dataset runs/bc_train_geometry_v10 --val-dataset runs/bc_val_v1 --output runs/bc_model_signed_v14 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device cuda --active-gas-weight 1 --active-brake-weight 1 --continuous-batches --history-frames 8 --balanced-actions --signed-longitudinal
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_signed_v14/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --output runs/bc_closed_signed_v14
python -m bc.diagnose --checkpoint runs/bc_model_balanced_v13/best.pt runs/bc_model_signed_v14/best.pt --dataset runs/bc_train_v1 --extra-train-dataset runs/bc_train_geometry_v10 --val-dataset runs/bc_val_v1 --device cuda --output runs/bc_offline_signed_v14
```

At launch, outcomes were pending, not a candidate confirmation. The completed
outcome below still establishes no finisher. Accelerate/coast/brake classification
plus active magnitude remains only a subsequent candidate for consideration;
it was not started in parallel or automatically after this trial.

Training completed all five epochs with 20,000 draws / 313 updates each.
All train/extra-train/val manifest and collector-provenance hashes, road lists,
seed and budget match v13. Every epoch's sampled conditional counts match
v13 exactly: totals **12,976 high-gas / 12,560 high-brake / 13,984 large-steer**
presentations, not extra unique labels. Only the representation/objective
metadata differ in configuration. The chosen checkpoint is **epoch5**, ordinary
decoded val mean MSE **0.000467832** (v13 0.000914352), SHA-256
`efd671cd9c362185757742202455026499997ef1bf59792865952a8be1bdb518`.
Training artifact evaluates its fixed CPU checkpoint over the full training
pool: gas>0.1 MAE 0.010099, brake>0.1 MAE 0.001643, large-steer MAE 0.010690.
These are not a closed-loop claim; the complete paired evaluation and matched
CUDA startup/signed diagnosis are still pending at this checkpoint. Recorded
source hashes for `core/`, wrapper, damage and oracle-v1 controller match v13.

### Plain Closed-Loop Outcome

All planned **15 episodes on 15 roads** completed evaluation, IDs 1-5 x seeds
31-33, same baseline conditions/grid as v13, **oracle prefix0**. Student finished
**0/15 episodes on 0/15 roads**; paired oracle finished **15/15 on 15/15 roads**.
Every student episode terminated `off_track`; no missing/interrupted episodes.
Fourteen ended without damage, ID5/seed33 had one collision and damage0.2.
Across all **7,498 student actions**, simultaneous positive gas/brake count is
zero, as guaranteed by the decoder. Damage reduction is not finish reliability.

| Geometry Seed | Track IDs | First Same-State Action Mismatch | First >2-Unit Pose Divergence | Student Progress / Reason |
| ---: | --- | --- | ---: | --- |
| 31 | 1-5 | step3 gas | 11 | 0.109489 / off_track (all five) |
| 32 | 1-5 | step6 brake | 12 | 0.098305 / off_track (all five) |
| 33 | 1-4 | step3 gas | 11 | 0.120141 / off_track (all four) |
| 33 | 5 | step3 gas | 11 | 0.113074 / off_track (damage0.2) |

v13 first same-state mismatch was step0 gas on all 15 roads and pose divergence
step5 on all 15. v14 delays both without a prefix, but still no full lap; mean
progress fell from 0.354085 to 0.108841. Progress is an internal proxy, not a
score. Repeated IDs share base geometry and are not independent training-seed
replications. This is one training seed/budget on exposed validation.

Closed-loop first-ten-action analysis uses teacher labels on **each model's own
visited states**, not offline reference labels or a claim of matched states.
v13 unnecessarily brakes at **150/150** steps where that same-state teacher
brake is zero (mean brake0.078105); v14 does so at **0/60** such steps (mean0).
The denominators differ because v13 stays slow while v14 reaches teacher speed.
However, v14 misses braking entirely at **75/90** first-ten steps requiring
positive same-state brake, often accelerating instead. Same-state signed MAE
over all 150 initial actions falls from 0.372893 to 0.185217, still large.

Concrete example ID1/seed31: at step0 v14 executes gas0.404554/brake0 versus
teacher0.4/0. At step3, pre-speed12.2638, it executes gas0.146115/brake0 versus
teacher0/0.021103. At step4 it brakes0.232461 versus student-state teacher0.301238.
At step6, pre-speed14.3445, it accelerates0.100142 versus teacher brake0.187563;
by step9 pre-speed16.7786 it still accelerates0.065535 versus brake0.382288.
These traces substantiate an excessive-speed / missing-needed-braking pattern,
not proof of its underlying optimization, observability or distribution-shift
cause. Matched offline startup/signed results below distinguish these errors
from the teacher-trajectory fitting results.

### Matched Offline Outcome

Completed fixed v13/v14 diagnosis on the identical **111,394 train rows / 100
roads / 20 geometries** and **15,676 val rows / 15 roads / three geometries**,
CUDA/batch128, causal history8, no retraining. Tiny CPU/CUDA differences do not
change these conclusions; use this paired CUDA table rather than mixing devices.
Signed-control error is `abs((predicted_gas-predicted_brake)-(gas-brake))` and
tail masks remain exactly gas>0.1 and brake>0.1.

| Metric | Train / Val Count | Balanced v13 Train / Val MAE | Signed v14 Train / Val MAE |
| --- | ---: | ---: | ---: |
| Signed error on gas>0.1 | 700 / 105 | 0.245347 / 0.245581 | **0.010052 / 0.016039** |
| Signed error on brake>0.1 | 100 / 15 | 0.260821 / 0.260140 | **0.001643 / 0.001415** |
| Decoded gas error on gas>0.1 | 700 / 105 | 0.171502 / 0.172743 | **0.010052 / 0.016039** |
| Decoded brake error on brake>0.1 | 100 / 15 | 0.154961 / 0.157208 | **0.001643 / 0.001415** |
| Absolute steer>0.1 | 20,735 / 2,386 | 0.017518 / 0.018576 | **0.010704 / 0.009591** |
| All-row signed error | 111,394 / 15,676 | 0.045933 / 0.046352 | 0.041767 / 0.042266 |
| Step0 signed error | 100 / 15 | 0.370302 / 0.370878 | **0.012927 / 0.008249** |
| First10 signed error | 1,000 / 150 | 0.214279 / 0.214291 | **0.045471 / 0.059069** |
| First10 steer error | 1,000 / 150 | 0.010884 / 0.011194 | 0.004572 / 0.005052 |
| First10 gas error | 1,000 / 150 | 0.158636 / 0.159099 | 0.028241 / 0.042376 |
| First10 brake error | 1,000 / 150 | 0.067862 / 0.066875 | 0.017230 / 0.016693 |

Step0 mean targets are gas0.4/brake0 on every road. Predictions:
v13 train0.111826/0.082128, val0.108121/0.078999; v14
**train0.412927/0, val0.408249/0**. There is no unnecessary braking in the
matched reference first-ten steps requiring zero teacher brake: v14 predicted
brake is zero at every step0/1/2/5/7/9, **600/600 train and 90/90 val** rows.
This does not imply that required braking is correctly learned.

Even on teacher-trajectory pixels, small/moderate braking remains misfit:

| Pre-Action Step | Target Signed Train / Val Mean | v14 Prediction Train / Val Mean | v13 Signed Train / Val MAE | v14 Signed Train / Val MAE |
| ---: | ---: | ---: | ---: | ---: |
| 3 | -0.021038 / -0.020980 | +0.030986 / +0.117461 | 0.049115 / 0.048210 | 0.065902 / 0.138440 |
| 4 | -0.233247 / -0.233372 | -0.232048 / -0.233488 | 0.260821 / 0.260140 | **0.001643 / 0.001415** |
| 6 | -0.077305 / -0.077168 | +0.130443 / +0.154385 | 0.103770 / 0.103073 | **0.207748 / 0.231553** |
| 8 | -0.067458 / -0.067362 | +0.055711 / +0.050567 | 0.092418 / 0.092204 | 0.123170 / 0.117929 |

Counts are 100 train / 15 val rows at each listed step. Full steps0-9, MSE,
means and counts remain in `runs/bc_offline_signed_v14/summary.json`. These
errors on training reference pixels prevent diagnosing failure as solely
student-state distribution shift or a held-out-only perception problem.
The large brake pulse fits, but surrounding smaller required brakes have the
wrong direction, including train. It is also incorrect to say the entire
longitudinal representation bottleneck is resolved merely from the rare tails.

### Gate Decision

This isolated one-seed intervention **substantially improves rare-action fit,
step0, early pooled error and large-steer fit**, structurally removes overlapping
controls, and delays divergence without any privileged prefix. It **does not
improve full-episode finishes: both v13 and v14 remain 0/15 episodes on 0/15
roads**, and v14 progress is worse. Thus the old independent regression was a
material fitting limitation in this comparison, but signed representation alone
is insufficient for reliable driving; it is not a confirmed model or an
official performance result. Loss/head nonlinearity changes are part of this
single representation intervention, not a proof that every improvement was
caused exclusively by preventing simultaneous controls.

Remain at the longitudinal fitting/diagnosis gate. High-brake validation has
only 15 rows; no extra training seed/budget was tested. Do not reflexively add
data/history/recovery/RL, switch to privileged inference or open protected
seeds. A mode-classification plus magnitude head may be discussed as a later
directional-control candidate, with the evidenced small-brake sign errors as
the target, but its efficacy is untested and no second intervention was run.
Preserved all negative results, source snapshots and existing artifacts.
The requested signed-only experiment is complete. Updated `docs/plan/BC.md`
and regenerated the summary-only run catalog; no official submission or model
confirmation.

## Final BC Architecture Experiment: Mode and Magnitude (v15)

User-authorized on 2026-09-30 as exactly one last BC architecture trial, not
another search for BC15/15. Signed v14 fitted startup and large control tails but
still accelerated on training oracle small-brake states (notably steps6/8),
and mean closed-loop progress worsened 0.354085 -> 0.108841. Tail fitting and
a good closed-loop policy are distinct outcomes, not interchangeable gates.

Change only longitudinal output to three logits (accelerate/coast/brake) and one
sigmoid magnitude. Steering remains tanh regression with identical seeded shared
weights and steering row. Exact labels: gas>0 -> accelerate, brake>0 -> brake,
both zero -> coast. No epsilon/deadband discards small targets. Existing audited
training actions have 0 overlapping controls and **0 coast samples**, a limitation
of this lossless label definition; coast generalization is not established.
Inference uses hard argmax: accelerate emits gas magnitude, brake emits brake
magnitude, coast emits neither. The model still consumes only causal images.

Objective is `(steer_MSE + mode_CE + active_magnitude_MSE)/3`, no class weights;
active magnitude loss averages over non-coast targets regardless of predicted
mode. Steering retains its original 1/3 coefficient, but classification changes
the shared gradient scale, so this is a representation/objective intervention,
not a claim that only head shape matters. `BCPolicy-mode-history8-v5` checkpoint
retains CPU `act` and the existing evaluator without inference overrides.

Keep frozen-v1 train IDs1-5 x seeds11-30 / 100 roads / 20 geometries and validation
IDs1-5 x seeds31-33 / 15 roads / three exposed geometries. Fresh seed0, history8,
Adam0.001, batch64/continuous batches, five epochs, 20,000 draws / 313 updates
each, unchanged per-road 1/8 high-gas + 1/8 high-brake + 3/4 natural sampling.
Keep checkpoint selection by ordinary decoded steer/gas/brake validation mean
MSE to avoid combining another selection intervention. Prioritize reported mode
confusion, brake recall, accelerate/brake direction errors, first10 accuracy,
small-brake recall and steps6/8, plus raw magnitude MAE on active target modes
even when mode is incorrect. Baseline v14 mode is inferred from signed output;
its magnitude is absolute signed output. Confusion rows are target, columns
prediction, ordered accelerate/coast/brake. Null rates denote empty denominators.

Execution order is train -> matched fixed-checkpoint offline diagnosis -> plain
zero-prefix closed loop in the unchanged official environment, physical obstacles,
frame_skip4, warmup50, cap2,000, domain_randomize false:

```bash
python -m bc.train --dataset runs/bc_train_v1 --extra-train-dataset runs/bc_train_geometry_v10 --val-dataset runs/bc_val_v1 --output runs/bc_model_mode_v15 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device cuda --active-gas-weight 1 --active-brake-weight 1 --continuous-batches --history-frames 8 --balanced-actions --mode-longitudinal
python -m bc.diagnose --checkpoint runs/bc_model_signed_v14/best.pt runs/bc_model_mode_v15/best.pt --dataset runs/bc_train_v1 --extra-train-dataset runs/bc_train_geometry_v10 --val-dataset runs/bc_val_v1 --device cuda --output runs/bc_offline_mode_v15
OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 python -m bc.evaluate --checkpoint runs/bc_model_mode_v15/best.pt --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --output runs/bc_closed_mode_v15
```

Seeds34-35 and38-40 remain unopened. No extra data, longer history, recovery,
environment changes or official action. Regardless of outcome, this concludes
BC architecture exploration; next stage is review of RL fine-tuning, not another
BC fitting variant. RL training itself is not executed in this bounded trial.
Implementation validation: existing BC history/train/evaluate **48/48 tests**
and new mode regression **6/6 tests** passed. Covers lossless strict targets,
exclusive hard decoding, raw logits, shared/steer RNG initialization, checkpoint
CPU inference, unchanged selection and confusion/magnitude/startup arithmetic.
Training, matched offline diagnosis and closed-loop evaluation completed in that
order using persistent processes. Completed artifacts are recorded below.

### Training and Matched Offline Outcome

Completed five epochs, each 20,000 draws / 313 updates, training seed0. The
sampled high-gas/high-brake/large-steer counts match v14 exactly across all five
epochs: totals 12,976 / 12,560 / 13,984, not additional unique labels. Selected
**epoch5** by unchanged decoded validation mean MSE **0.001574630** (v14
0.000467832). Checkpoint SHA-256:
`75cd1ae4954c7f4497c40dce46929ef388443b3766ce42cf12f6946730924a12`.
Train/extra-train/val road and manifest contracts are unchanged; full configs,
collector/source hashes and snapshots are retained in the model artifact.

Matched CUDA/batch128 diagnosis uses **111,394 train rows / 100 roads / 20
geometries** and **15,676 val rows / 15 roads / three exposed geometries**.
Use the matched diagnostic below, not mixed CPU/CUDA aggregates: hard argmax
changes a few near-boundary mode decisions across CPU/batch64 versus CUDA/batch128
(v15 train counts differ by tens of rows); the key step6/8 failure is unchanged.

| Metric | v14 Train / Val | v15 Train / Val |
| --- | ---: | ---: |
| Overall mode accuracy | 52.843% / 52.858% | 53.084% / 52.941% |
| Brake recall (55,617 / 7,828 target rows) | 5.685% / 5.621% | 36.748% / 34.581% |
| Brake -> accelerate rate | 94.315% / 94.379% | 63.252% / 65.419% |
| Accelerate -> brake rate (55,777 / 7,848 target rows) | 0.134% / 0.025% | 30.627% / 28.746% |
| Small-brake recall, 0<brake<=0.1 (55,517 / 7,813 rows) | 5.515% / 5.440% | 36.634% / 34.455% |
| Raw active-target magnitude MAE, all rows | 0.021554 / 0.021979 | 0.031653 / 0.032250 |
| Raw magnitude MAE on accelerate targets | 0.029954 / 0.030446 | 0.024549 / 0.024928 |
| Raw magnitude MAE on brake targets | 0.013129 / 0.013490 | 0.038778 / 0.039591 |
| First10 mode accuracy (1,000 / 150 rows) | 71.0% / 70.0% | 80.0% / 80.0% |
| First10 brake recall (400 / 60 rows) | 27.5% / 25.0% | 50.0% / 50.0% |
| First10 brake -> accelerate count | 290/400 / 45/60 | 200/400 / 30/60 |
| First10 accelerate -> brake count | 0/600 / 0/90 | 0/600 / 0/90 |
| First10 active magnitude MAE | 0.015087 / 0.029326 | 0.155336 / 0.154864 |
| First10 signed-control MAE | 0.045471 / 0.059069 | 0.183513 / 0.182611 |
| Step0 gas MAE (100 / 15 rows) | 0.012927 / 0.008249 | 0.335840 / 0.334148 |
| Gas>0.1 decoded MAE (700 / 105 rows) | 0.010052 / 0.016039 | 0.201180 / 0.201859 |
| Brake>0.1 decoded MAE (100 / 15 rows) | 0.001643 / 0.001415 | 0.054766 / 0.060295 |
| Absolute steer>0.1 MAE (20,735 / 2,386 rows) | 0.010704 / 0.009591 | 0.026854 / 0.023116 |

Full target-row / prediction-column confusion matrices, order A/C/B:

| Model / Split | Accelerate Row | Coast Row | Brake Row |
| --- | --- | --- | --- |
| v14 train | [55,702, 0, 75] | [0, 0, 0] | [52,455, 0, 3,162] |
| v15 train | [38,694, 0, 17,083] | [0, 0, 0] | [35,179, 0, 20,438] |
| v14 val | [7,846, 0, 2] | [0, 0, 0] | [7,388, 0, 440] |
| v15 val | [5,592, 0, 2,256] | [0, 0, 0] | [5,121, 0, 2,707] |

Overall brake recall alone would falsely suggest the direction issue was fixed:
it also greatly increases false braking on accelerate targets. Crucially,
**step6 and step8 still classify accelerate on every train and val road**:
brake recall **0/100 train and 0/15 val at EACH step**, same as v14. First10's
accuracy gain comes from step3 becoming brake on all roads, not fixing6/8.
First10 small-brake recall is v15 100/300 train and15/45 val versus v14 10/300
and0/45; all these v15 correct small brakes are step3. Their magnitude is too
large: step3 train target brake0.021038 versus prediction0.121973.

| Training Pre-Action Step | Target Signed Mean | v14 Signed Prediction Mean | v15 Signed Prediction Mean | v15 Brake Recall |
| ---: | ---: | ---: | ---: | ---: |
| 0 | +0.400000 | +0.412927 | +0.064160 | N/A (accelerate100/100) |
| 3 | -0.021038 | +0.030986 | -0.121973 | 100/100 |
| 4 | -0.233247 | -0.232048 | -0.178480 | 100/100 |
| 6 | -0.077305 | +0.130443 | +0.075680 | 0/100 |
| 8 | -0.067458 | +0.055711 | +0.079023 | 0/100 |

Step0 val similarly predicts gas0.065852 instead of0.4 (mode accelerate is
correct). At step6/8 val, raw magnitude MAE is only0.006377/0.011333, but mode
is wrong15/15 each: fitting a magnitude does not ensure correct direction.
No coast labels or predictions occur in these source pools. Under this single
seed/five-epoch budget the primary small-brake direction gate remains unmet on
training pixels, and signed-v14 tail/startup/steering fitting gains regress.
Classification/objective shared-gradient interference is a hypothesis, not a
proven cause or authorization for another loss/architecture search. The result
does not substantiate purely distribution shift or proven partial observability.
All negative results and per-step metrics remain in the saved artifacts.

### Closed Loop and BC Closure

Completed all **15/15 planned paired evaluations**, IDs1-5 x seeds31-33,
three exposed geometries, unchanged conditions above and **oracle prefix0**.
Student finished **0/15 episodes on 0/15 roads**; reference oracle finished
**15/15 episodes on 15/15 roads**. All student episodes terminated `off_track`,
seven ended with damage (six0.2, one0.4); no missing/interrupted episodes. This
is one training seed and one rollout per road, not replicated learning evidence.

| Track ID | Seed31 Progress / Damage | Seed32 Progress / Damage | Seed33 Progress / Damage |
| ---: | --- | --- | --- |
| 1 | 0.160584 / 0 | 0.576271 / 0.2 | 0.250883 / 0 |
| 2 | 0.160584 / 0 | 0.633898 / 0.2 | 0.250883 / 0 |
| 3 | 0.135036 / 0.2 | 0.152542 / 0.4 | 0.250883 / 0 |
| 4 | 0.113139 / 0.2 | 0.237288 / 0 | 0.190813 / 0.2 |
| 5 | 0.160584 / 0 | 0.305085 / 0.2 | 0.204947 / 0 |

Mean progress is v13 **0.354085**, v14 **0.108841**, v15 **0.252228**. v15
improves this proxy relative to v14 but not v13, and none finishes a lap. It is
not an official ranking score or reason to call v15 successful. First same-state
action mismatch is **step0 gas on all15 roads** (v14 step3/6); >2-unit pose
divergence is **step6 on all15** (v14 step11/12). Online step0 gas predictions
are0.068086/0.062891/0.066589 for seeds31/32/33 instead of0.4, consistent with
the offline magnitude regression, not a held-out-only startup failure.

**Decision: close BC architecture exploration.** The intended final diagnostic
did not fix small-brake direction at steps6/8 even on training oracle states.
Higher aggregate brake recall and initial mode accuracy do not mean the fitting
gate passed: false braking increased, startup magnitude and tail/steering fit
regressed, and full-episode finishes remain0/15. Do not present this as having
removed every supervised fitting defect or isolated purely distribution shift.
This is a bounded negative result, not proof against all classification policies.

Per the user's stopping rule, do not tune CE weights, optimizer, history, recovery
or add data to chase BC15/15. The next research stage is **RL fine-tuning review**
using actual closed-loop reward, not another BC loss/architecture trial. v15 is
not automatically chosen as the RL initialization; retain v13/v14/v15 checkpoints
and justify that choice in the subsequent RL scope. No RL training, official
submission or model confirmation has run. Seeds34-35/38-40 remain unopened.

Evidence: `runs/bc_model_mode_v15/history.json`,
`runs/bc_offline_mode_v15/summary.json`,
`runs/bc_closed_mode_v15/summary.json` and its complete paired traces/source
snapshots. Updated this task's plan and summary-only catalog, preserving all
historical negative runs. Supplied environment and `agent.py` remain unchanged;
54 targeted BC tests passed before execution. No further experiment follows.
