# Matched Teacher Comparison

## Authorization And Scope

The 2026-09-30 user request authorizes small oracle-v2 generalization evaluation,
matched v1/v2 trajectory collection, and a tiny same-CNN/same-data/same-seed BC
comparison, including a mixed-teacher arm if practical. Read `COMMON.md` first.
This independent plan does not resume other BC diagnosis or v2 tuning. No RL,
teacher-replay/RLPD/DAgger implementation, submission, or official model
confirmation is authorized. A later v2-centered dataset recommendation is
conditional on actual student evidence.

## Stage 1: Teacher Generalization Gate

- Freeze v1 at `oracle-v1` and current v2 `pace` sources from `d08c370`.
- Full episodes on IDs 1-5 x seeds 11, 21 (existing BC training geometries),
  and 41, 42 (previously unexamined geometries, outside preserved BC splits).
  One episode per road: 20 episodes / 20 roads / four base geometries.
- Original physical obstacles, rendering, frame stack, warmup 50, frame skip 4,
  raw horizon 8,200, and 2,000-action external cap. No environment changes.
- Gate: 20/20 actual finishes, reporting damage/collision separately. If passed,
  operationally freeze pace for this experiment without parameter changes;
  this is not a robustness guarantee or official model confirmation. If failed,
  preserve failures, diagnose first departure, and stop before collecting v2
  learning data rather than quietly tuning the teacher.
- All examined roads become exposed development evaluation, not holdouts.
  Do not access seeds 34-35 or 38-40.

## Stage 2-4: Matched Small BC

- Use the existing plain four-frame image-only CNN, no privileged inputs,
  recurrent/history changes, recovery data, weighting variants, or RL.
- Training pool: IDs 1-5 x seeds 11, 12 (10 roads / two geometries).
  Validation pool: IDs 1-5 x seeds 31, 32, 33 (15 roads / three already exposed
  development geometries). Reuse the already successful frozen-v1 raw train/val
  trajectories (no duplicate deterministic collection); collect v2 once on the
  same pools and verify matched environment/geometry conditions before views.
- Derive 256 unique rows per road, selected without replacement with seed 0.
  Pure arms each contain 2,560 training rows; mixed contains 128 rows per
  teacher per road (also 2,560 total). Validation views likewise contain
  256 rows per road (3,840 each), teacher-specific pure targets and balanced
  mixed targets. Do not duplicate labels or average incompatible actions.
- Five epochs, batch size 64, continuous cross-road batching, all 2,560 rows
  per epoch: 40 updates/epoch, 200 updates and 12,800 presentations per arm.
  Adam learning rate .001, seed 0, CUDA, two Torch threads, four-frame
  `BCPolicy-v1` (31,659 parameters), unit gas/brake loss weights. No tuning.
  Same architecture, initialization seed, row/update budget, and checkpoint
  selection by unweighted held-out mean component MSE. Different target
  teachers mean validation loss scales are not directly comparable.
- Collect v1 and v2 once on identical train and validation roads/conditions.
  Preserve complete raw trajectories and unsuccessful episodes, train only on
  successful roads shared by both teachers. Equalize rows per shared road since
  faster v2 produces fewer actions. Record sampled row indices/source identity.
- Include a 50/50 v1/v2 mixture at the same total row count, not twice the data.
  Interleaved mixture tests mixed demonstrations, not an ordered curriculum.
- Use identical CNN initialization/training seed, row count, optimizer updates,
  and selection rule. Select checkpoint by held-out teacher-specific validation
  loss; evaluate all arms on the same full-episode validation roads.
- Primary comparison: complete-episode finishes with episode/road denominators.
  Secondary diagnostics: progress, damage, action errors (including conditional
  errors), and successful lap time. Losses against different teachers alone do
  not establish which teacher is easier to learn. One training seed is a pilot,
  not a replicated causal conclusion. A finish tie at zero is inconclusive even
  if progress or loss improves.

## Startup Checkpoint

- Clean worktree at start; no active research process in this repository.
- Generalization launched as five track-ID workers, four complete episodes each;
  learning has not launched. Persistent-process start was refused because another
  Kilo instance owns this project's persistent manager. Workers use tracked
  session lifetime; do not claim they survive application shutdown. Artifacts:
  `runs/teacher_gate_v2_t1` through `t5`.
- Existing collector cannot select v2 and trainer cannot mix same-road teachers.
  Minimal teacher-selector and provenance-preserving dataset-view tooling is
  being implemented with focused tests. Other sessions' concurrent BC diagnosis,
  trainer/evaluator and catalog edits are unrelated and must be preserved.
- Existing historical v2
  result is 100/100 on 50 exposed roads across two behavior-equivalent sources;
  final source itself was verified on 50/50 repeat episodes.

## Generalization Result: 2026-09-30

- **20/20 complete episodes on 20/20 roads**, one episode per road.
  Existing training seeds 11/21: 10/10; previously unexamined seeds 41/42:
  10/10, each across IDs 1-5. Zero damaged episodes and zero collision-positive
  actions over 13,149 actions. Mean/median/best successful lap:
  52.542/51.200/46.940 simulation seconds (not wall runtime or official scores).
- All 20 planned episodes have full metadata/trace/summary artifacts, no
  incomplete or missing roads; one execution/source group, no report warnings.
  Report: `runs/teacher_gate_v2_t1/gate_report.json`. V2 controller SHA-256:
  `9e884d73980318894120105003a90524e889a32f67729616325a5caa32d40e3a`.
- Gate passed. Operationally freeze this exact `pace` controller for collection
  and the pilot, without retuning. This small one-pass local gate does not prove
  private-track or perturbed-condition robustness. Seeds 41/42 are now exposed.
- Frozen v1 and supplied environment/Agent pass `git diff oracle-v1 --exit-code`
  on their protected paths. Collection/training/evaluation remain pending.
- Actual saved geometry hashes confirm four base geometries, identical within
  each seed across IDs 1-5. Seeds 11/21 exactly match the existing BC training
  geometry. Seeds 41/42 differ from each other and all 33 actual geometries in
  saved development seeds 1-10, training 11-30 and validation 31-33. Novelty is
  therefore 10/10 road configurations across two new base geometries, not ten
  independent new geometries. No protected validation/test seeds were opened.

| Seed | Track Points | Actual Geometry SHA-256 |
| --- | ---: | --- |
| 11 | 259 | `11b4b22dbfe360a1a4dabfcbc0e209b542120599fd55bd9362554932b3bb10ca` |
| 21 | 338 | `2d3a8384179ab4816f275d78fbd1d8dadb1164492e1b6c1ac1de51f633fbecc6` |
| 41 | 306 | `cbc6bd0fd8fae2feaaaaa4a9d7adc07bc2dd2bb1fde28708375ed393e1ee20aa` |
| 42 | 283 | `c0625fee83804895c2daf846322f86fe4977f7285dda87e783e662f66833a1ba` |

Geometry digest convention: SHA-256 of sorted-key JSON `track_points`, same as
`oracle.v2_report.signature`; coordinate-only digests gave the same identities.

## Pilot Reproduction

Existing raw v1 sources: `runs/bc_train_v1` (select seeds 11/12 only) and
`runs/bc_val_v1` (seeds 31-33). V2 uses five independent track-ID batches per
split, with explicit selected teacher and full episode horizon. Example ID 1:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m bc.dataset --teacher v2 --v2-stage pace --split train --track-ids 1 --seeds 11 12 --output runs/teacher_raw_v2_train_t1
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m bc.dataset --teacher v2 --v2-stage pace --split val --track-ids 1 --seeds 31 32 33 --output runs/teacher_raw_v2_val_t1
```

Generate exactly matched views after every selected raw road finishes:

```bash
python -m bc.teacher_views --v1-dataset runs/bc_train_v1 --v2-dataset runs/teacher_raw_v2_train_t{1,2,3,4,5} --output runs/teacher_views_train --split train --track-ids 1 2 3 4 5 --seeds 11 12 --rows-per-road 256 --seed 0
python -m bc.teacher_views --v1-dataset runs/bc_val_v1 --v2-dataset runs/teacher_raw_v2_val_t{1,2,3,4,5} --output runs/teacher_views_val --split val --track-ids 1 2 3 4 5 --seeds 31 32 33 --rows-per-road 256 --seed 0
```

Run training once per arm `v1`, `v2`, and `mixed`; example v1:

```bash
python -m bc.train --dataset runs/teacher_views_train/v1 --val-dataset runs/teacher_views_val/v1 --output runs/teacher_model_v1 --epochs 5 --batch-size 64 --lr .001 --seed 0 --num-threads 2 --device cuda --max-train-samples 2560 --continuous-batches --history-frames 4 --active-gas-weight 1 --active-brake-weight 1
OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m bc.evaluate --checkpoint runs/teacher_model_v1/best.pt --split val --track-ids 1 --seeds 31 32 33 --max-steps 2000 --output runs/teacher_closed_v1_t1
```

Closed-loop is likewise five track-ID batches per arm, identical three seeds,
with no oracle prefix, steering splice, or recovery collection. All arms use the
same frozen v1 oracle reference/on-student diagnostic labels; those labels are
not equivalent to v2-target fit and do not affect executed student actions.

## Collection Checkpoint

- V2 raw collection launched on all declared train/validation roads after the
  teacher-selector tests passed. Ten workers: `runs/teacher_raw_v2_train_t1`
  through `t5` (two roads each) and `runs/teacher_raw_v2_val_t1` through `t5`
  (three roads each). These are launches, not completed counts.
- Thirteen focused selector/view/environment-condition tests passed; collector
  tests verify v2 source snapshots, correct pre-action labels, explicit teacher
  metadata, legacy-v1 readability and teacher/stage resume rejection.
  The full-episode evaluator's 13 tests also passed, including unassisted rollout
  and interruption/resume behavior. Concurrent diagnostic additions are not used.
- Dataset views must additionally verify actual saved road geometry/obstacles
  and shared simulator source/package conditions, not just matching CLI settings.
  No training has started, and no student-imitation result is established.

## Matched Data And Training Launch

- Raw v2 collection completed **10/10 train episodes on 10/10 roads** and
  **15/15 validation episodes on 15/15 roads**. The view builder also verified
  successful, complete frozen-v1 raw episodes for every one of these same roads.
  Existing v1 data was reused, not freshly recollected or counted as independent
  new episodes. No paired road was dropped, substituted, or resampled by rollout.
- Both view commands completed successfully, checking actual geometry,
  obstacles, start/reset metadata, normalized environment settings, protected
  simulator source hashes, Python/platform and simulator package versions.
  Source paths and hashes bind each view row to its original teacher/trajectory.
- All three train views have exactly 2,560 rows / ten roads; validation views
  exactly 3,840 rows / 15 roads. Pure arms each sample 256 distinct rows per road;
  mixed uses 128 per teacher, nested within the corresponding pure selection.
- Final selector/view/metadata/batching suite: 21 tests passed. Additional
  evaluator suite: 13; model/history regression suite: eight; matched report
  tests: three. One mistyped test command also requested nonexistent
  `tests.test_bc_model`; corrected existing-module execution passed.
- Three matched training jobs launched sequentially on CUDA with the fixed
  protocol above, artifacts `runs/teacher_model_v1`, `_v2`, `_mixed`. No
  closed-loop or student-learning conclusion is recorded from a launch.
- Aggregate after all 45 student episodes complete:

```bash
python -m bc.teacher_report --runs runs --output runs/teacher_model_v1/pilot_report.json
```

The report checks matching training budgets/source hashes, checkpoint identity,
the entire identical unassisted 15-road grid per arm, and common evaluator
sources. An all-arm finish tie is explicitly inconclusive.

## Training Complete / Closed Loop Launched

- All three five-epoch jobs completed. Saved histories record 2,560 rows and
  40 updates every epoch, 12,800 presentations / 200 updates each, CUDA and
  seed 0. Every arm selected epoch 4 using its own fixed validation targets.
- All 15 track-ID evaluation workers launched (three episodes each):
  `runs/teacher_closed_v1_t1` through `t5`, `teacher_closed_v2_t1` through `t5`,
  and `teacher_closed_mixed_t1` through `t5`. Forty-five student episodes plus
  matched v1 reference episodes are planned; no prefix or recovery option.
- Offline selected-checkpoint diagnostics below are teacher-specific. Different
  target distributions/counts prohibit ranking teachers by these losses alone.
  High-brake bins are particularly sparse; no high-brake observation exists in
  the sampled v2 validation view.

| Arm | Mean Validation MSE | Large-Steer MAE (count) | High-Gas MAE (count) | High-Brake MAE (count) |
| --- | ---: | --- | --- | --- |
| v1 | .00142627 | .0673642 (576) | .247472 (31) | .231015 (3) |
| v2 | .00189486 | .0521725 (966) | .172810 (271) | unavailable (0) |
| mixed | .00164240 | .0624831 (780) | .169392 (165) | .231580 (2) |

All masks use absolute component target > .1. High-gas prediction means remain
well below target means: v1 .026116 vs .273588; v2 .025048 vs .197859; mixed
.026982 vs .196375. This is observed underfit in these sampled states, not a
proven explanation of closed-loop failures or a reason to change the fixed pilot.

## Completed Pilot And Decision: 2026-09-30

All 15 evaluator workers exited after the full requested grids. The aggregate
report verifies identical model budget/config/seed/training sources, evaluator
sources and settings, and each evaluated checkpoint's saved identity. There
are no missing or substituted paired roads. Evidence:
`runs/teacher_model_v1/pilot_report.json` plus all raw/view/model/closed-loop
directories named above. Seeds 31-33 were already exposed development geometry,
not a fresh holdout; three geometries / 15 roads per arm, one training seed.

| Arm | Student Finishes / Episodes / Roads | V1 Reference Finishes / Episodes | Mean Progress | Median Progress | Damaged Episodes | Terminal Reasons |
| --- | --- | --- | ---: | ---: | --- | --- |
| v1 | 0 / 15 / 15 | 15 / 15 | .328759 | .293286 | 14 / 15 | off_track 11, crash 3, max_steps 1 |
| v2 | 0 / 15 / 15 | 15 / 15 | .282872 | .248175 | 14 / 15 | off_track 15 |
| mixed | 0 / 15 / 15 | 15 / 15 | .334469 | .293286 | 15 / 15 | off_track 10, crash 5 |

- Combined student evidence: **0/45 completed finishes over 45 attempted full
  episodes on the same 15 distinct roads**, versus **45/45 reference finishes**.
  Roads must not be summed into 45 independent configurations; three arms share
  the grid, spanning three exposed validation geometries.
- Each arm's earliest thresholded same-state mismatch against the *common v1*
  diagnostic teacher is gas on all 15 roads. V2/mixed targets differ from that
  reference, so this does not measure their own teacher's action agreement.
  Offline high-gas underprediction is separately evidenced above. Distribution
  shift, sampled startup coverage, and limited fit budget are hypotheses, not
  experimentally isolated failure causes.
- **Teacher generalization gate passes, student-imitability gate does not.**
  Keep the unchanged operationally frozen v2 pace teacher available alongside
  v1, but do not declare it easier for a student to learn. The mixed arm's small
  mean-progress difference does not establish a curriculum benefit; damage was
  higher and neither arm finished. No successful BC baseline was created.
- This 200-update/two-training-geometry/one-seed negative pilot does not prove
  v2 is intrinsically less learnable, nor exhaust larger-budget or curriculum
  comparisons. No automatic tuning, retraining, broader seed replication, RL,
  teacher-replay/RLPD/DAgger implementation, or official action follows.
- Conditional user step 5 is **not triggered**: v2 did not win the finish
  comparison. Preserve both raw teacher datasets and mixed provenance for later
  authorized work; no v2-centered downstream-data commitment is made here.
- Current status: requested generalization/collection/three-arm BC pilot complete;
  no further experiment is running or authorized implicitly by this checkpoint.
