# Behavior Cloning: Reproduction and Evidence

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

`python -m bc.dataset` creates a new directory and refuses existing outputs.
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
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --output runs/bc_model_weighted_v2 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto
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
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --recovery-dataset runs/bc_recovery_v2_train --output runs/bc_model_recovery_v3 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto
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
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --recovery-dataset runs/bc_recovery_v2_train --output runs/bc_model_motion_v4 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --motion-features
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
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --output runs/bc_model_motion_no_recovery_v5 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --motion-features
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
python -m bc.train --dataset runs/bc_train_v1 --val-dataset runs/bc_val_v1 --recovery-dataset runs/bc_recovery_split_heads_v6_train --output runs/bc_model_controls_recovery_v8 --epochs 5 --batch-size 64 --seed 0 --max-train-samples 20000 --device auto --motion-features --active-brake-weight 10 --recovery-controls-only
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
