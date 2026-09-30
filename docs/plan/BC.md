# Behavior Cloning Plan

This plan owns Phase 3/4 trajectory collection, learned-policy training, and BC
diagnosis. Read [COMMON.md](COMMON.md) for the shared research contract and frozen
oracle-v1 evidence. The separate [ORACLE_V2.md](ORACLE_V2.md) plan does not change
this plan's teacher, splits, gates, or status. Splitting the documents does not
authorize starting or resuming experiments; follow the user's task-specific scope.

Evidence and reproduction commands: [../BC.md](../BC.md).

## Phase 3: Frozen Oracle and Trajectories

- `oracle-v1` points at `a70b35950414a930d5ddaad4ac15733e65774345` before
  BC work; do not tune its control parameters absent a demonstrated defect.
- Preserve the already exposed IDs 1-5 x seeds 1-10 as oracle validation only.
  Repeated deterministic traces are not independent learning examples. Geometry
  seeds 11-30 are the BC training pool, 31-35 validation, and 36-40 final local
  test, each with track IDs 1-5 / physical obstacles and original wrapper settings.
  Splitting by *seed* prevents one geometry shared by different IDs crossing splits.
- Collect at most one successful trajectory per selected road, preserve true
  pre-action policy observation and teacher action, and keep vehicle/track state
  strictly in separate analysis records. Failed teacher rollouts are recorded but
  ineligible for successful-action training. Log exact tested subsets and missing
  roads; do not silently claim complete split coverage.
- Final local test seeds must not influence model design, epoch selection, or
  tuning. Collect/evaluate them only after fixing the candidate using validation.

## Phase 4: Simple BC and Closed Loop

1. Fit a small supervised image-stack-to-action model on training roads. Track
   both training and held-out validation error by steer/gas/brake. Select using
   validation only; attractive loss alone is not evidence of reliable driving.
2. Run complete closed-loop episodes in the unchanged wrapped environment.
   Record finish counts with episode and road denominators, oracle reference,
   student-state teacher labels, earliest component mismatch, earliest pose
   divergence, curvature/speed/obstacle context, and termination reasons.
3. Diagnose poor offline prediction as observation/representation/encoding first;
   good offline prediction but progressive divergence as distribution shift; and
   concentrated failures as possible data-coverage/recovery problems. These are
   hypotheses to test, not automatic causal claims.
4. If validation closed-loop shows distribution shift, *then* collect labels on
   actually visited student states and retrain (DAgger/recovery). Do not duplicate
   deterministic oracle trajectories. If BC succeeds, freeze its baseline and
   reconsider whether any RL is needed. No RL work is authorized at this gate.

Never represent local results as official submission performance. Obtain fresh
explicit user authorization before any official submission/model confirmation.

## Current Status

- **BC ARCHITECTURE EXPLORATION CLOSED (2026-09-30).** Final v15 experiment
  completed implementation, five-epoch training, matched offline diagnosis and
  all 15 zero-prefix validation episodes. Student **0/15 episodes on 0/15 roads**,
  paired oracle **15/15 on 15/15 roads**, IDs1-5 x seeds31-33 / three exposed
  geometries. All student episodes ended off_track, seven had damage; none
  missing/interrupted. Mean progress0.252228 (v14 0.108841, v13 0.354085) is only
  an internal proxy, not reliability or an official score. Same-state mismatch
  regresses to step0 gas on all15; >2-unit pose divergence step6 on all15.
  Critical small-brake training direction fit remains unresolved; do not claim
  the fitting issue was removed or failure is exclusively distribution shift.
  No more BC architecture/loss/sampling trials, BC15/15 target, new data/history
  or recovery are authorized. Next stage is **RL fine-tuning review**, with
  initial policy selection still to be justified; v15 is not adopted merely
  from higher brake recall. RL execution and official actions have not started.
  Seeds34-35/38-40 remain unopened. Preserve all checkpoints and negative evidence.
  The dated entries below are historical gates, not instructions to resume BC.
- 2026-09-30 user authorizes exactly one FINAL BC architecture experiment:
  replace only longitudinal with accelerate/coast/brake classification plus
  active-mode magnitude regression; retain steering/tanh/shared initialization,
  history8, frozen-v1 IDs1-5 x seeds11-30, fresh seed0, Adam0.001, batch64,
  continuous batches, balanced sampling, five epochs and 20,000 draws / 313
  updates per epoch. Mode labels use strict positive gas/brake and exact-zero
  coast, without thresholding away small brakes; prior training audit has
  zero overlap and zero coast examples. Loss is
  `(steer_mse+mode_ce+active_magnitude_mse)/3` with no class weights; magnitude
  sigmoid, hard mode argmax at inference. Ordinary decoded validation MSE
  selects the checkpoint unchanged; prioritize reporting confusion, brake recall,
  accelerate/brake confusion, first10 and step6/8 mode fit, and raw active-target
  magnitude MAE even when the selected mode is wrong. Run matched v14/v15 offline
  train/val diagnosis, THEN zero-prefix closed loop on IDs1-5 x seeds31-33.
  Seeds34-35/38-40 remain unopened; no new data, history, recovery or official
  actions. After this experiment BC architecture exploration ends regardless of
  outcome; review RL fine-tuning as the next stage, not another BC15/15 search.
  RL execution itself is not started by this bounded BC experiment. Existing
  research/tool changes are preserved. Completed artifacts in
  `runs/bc_model_mode_v15`, `runs/bc_offline_mode_v15`, `runs/bc_closed_mode_v15`.
  Implementation verified by 48 existing BC and six mode-specific tests. Training
  and matched offline diagnosis completed, followed by complete zero-prefix
  closed-loop evaluation. Epoch5 selected, decoded val MSE0.001574630,
  identical v14 five-epoch sampled counts/budget. Matched CUDA train/val brake
  recall5.685%/5.621% ->36.748%/34.581%, but accelerate->brake increases to
  30.627%/28.746% and overall mode accuracy stays near53%. First10 accuracy80%
  both splits (was71%/70%) only corrects step3: key step6/8 recall remains
  0/100 train and0/15 val EACH. Step0 gas fitting regresses to0.064160/0.065852
  versus target0.4; first10 active magnitude MAE0.155336/0.154864. Training-pixel
  direction gate unmet; no follow-up BC intervention authorized regardless of
  closed-loop result. Not a confirmed policy; full evidence in docs/BC.md.
- 2026-09-30 next user-authorized fitting trial: audit simultaneous gas/brake
  activation in the existing training oracle actions, then (if negligible)
  replace only independent longitudinal outputs with tanh signed gas-minus-brake.
  Decode positive to gas and negative to brake, without overlap. Retain history8,
  IDs 1-5 x training seeds 11-30 (20 geometries), balanced per-road sampling,
  seed0, Adam 0.001, batch64/continuous batches, five epochs and 20,000 draws /
  313 updates per epoch. Preserve steering initialization/head/tanh and its MSE
  coefficient 1/3: signed objective is (steer error squared + signed-control
  error squared)/3, not a two-output mean that rescales steering. Select by the
  same ordinary decoded steer/gas/brake validation mean MSE as v13. Diagnose
  matched train/val signed tail errors and first ten actions, then evaluate
  zero-prefix closed loop on IDs 1-5 x seeds 31-33 (15 roads). Seeds 34-35 and
  38-40 remain unopened; no extra data, longer history, recovery, RL, mode-head
  trial, or official actions. Classification plus active magnitude is only a
  possible subsequent candidate, not authorized as a concurrent experiment.
  Training audit completed: overlap is exactly 0/111,394 rows on 0/100 roads at
  strict >0, >0.01, >0.05 and >0.1; signed targets are lossless. Signed-only
  implementation passed 48 targeted tests. Training -> plain closed loop ->
  matched v13/v14 signed diagnosis launched persistently in
  `runs/bc_model_signed_v14`, `runs/bc_closed_signed_v14` and
  `runs/bc_offline_signed_v14`; all stages now complete, not a confirmed candidate.
  Training completed five epochs with exactly matched v13 draw counts; epoch5
  selected by ordinary decoded val MSE 0.000467832. Matched CUDA signed-control
  high-gas train/val MAE improves 0.245347/0.245581 -> 0.010052/0.016039;
  high-brake 0.260821/0.260140 -> 0.001643/0.001415. Step0 val now predicts
  gas0.408249/brake0, signed MAE0.008249 versus v13 0.370878. First10 signed
  train/val MAE0.045471/0.059069 versus 0.214279/0.214291. Large-steer improves
  too. Plain closed loop remains **0/15 student episodes on 0/15 roads** versus
  oracle15/15; all off_track, only ID5/seed33 has damage0.2. Pose divergence
  delays step5 -> 11-12; same-state mismatch step0 -> 3/6. Mean progress worsens
  0.354085 -> 0.108841 (internal proxy). No interrupted/missing episodes.
  Required small brakes are still predicted as acceleration even on TRAIN
  teacher pixels: step6 target-0.077305, prediction+0.130443; step8
  target-0.067458, prediction+0.055711. On actual initial student states,
  unnecessary brake is0/60 teacher-zero-brake steps, but needed brake is absent
  on75/90 teacher-positive-brake steps. This is strong rare/startup fit improvement
  but no finisher, not proof of purely distribution shift or observability.
  Signed-only gate complete; keep longitudinal fitting diagnosis, consider
  mode+magnitude only as an untested later candidate, no automatic second trial.
  Protected seeds, new data/history/recovery/RL and official actions remain
  untouched. Evidence/limitations in docs/BC.md; 48 BC plus five recording/catalog
  tests passed, supplied environment and agent.py unchanged.
- 2026-09-30 user-directed diagnostic gate supersedes the prior next-step
  auxiliary-target suggestion: pause new data and longer frame stacks. Without
  retraining, measure identical train/val conditional errors (gas >0.1,
  brake >0.1, absolute steer >0.1) and each episode's first ten actions. Fix the
  latest history8 checkpoint and run oracle-action prefixes 1/4/16 on IDs 1-5 x
  seeds 31-33 before student handoff; keep causal image history advancing during
  teacher execution. This is privileged diagnostic intervention, not inference.
  Select exactly one subsequent intervention from both diagnoses: poor train
  tail fit directs sampling/action parameterization/optimization first; good
  train fit with poor validation directs state-decoding auxiliary supervision
  or perception-to-controller, never privileged inference inputs. A large prefix
  benefit directs startup treatment; persistent failure with prefix16 means
  startup alone is insufficient. Do not infer partial observability merely from
  zero finishes or poor fit. Preserve 34-35 and 38-40; no RL or official actions.
- This gate completed: fixed history8 train/val high-gas MAE 0.243509/0.243393
  and high-brake 0.215563/0.215610; full training-source pool 111,394 rows / 100
  roads, val 15,676 rows / 15 roads. Prefix 1/4/16 each finished **0/15 student
  episodes on 0/15 roads**, paired oracle 15/15, IDs 1-5 x seeds 31-33. Prefix16
  delayed >2-unit pose divergence to steps 117-140 but same-state steering
  mismatch appeared at 28-36 (12-20 actions after handoff). Startup is an early
  contributor, not sufficient to explain/fix complete failures. No material
  train/val tail gap supports an optimization/sampling-first intervention.
  Select **balanced sampling only**: existing history8 CNN, fresh seed0,
  unit action MSE/unchanged selection, Adam 0.001, five epochs, 20,000 samples /
  313 updates each, same train/val roads. Per road reserve 1/8 high-gas and
  1/8 high-brake targets with replacement if needed; 3/4 natural, missing bins
  revert to natural. No new observations, weights, mode heads, recovery, or
  auxiliary targets. Test fit and plain non-prefix closed loop before another
   intervention. This single trial is now complete: five epochs / 100,000 total
   presentations, selected epoch4 by unchanged ordinary validation MSE. Sampled
   12,976 high-gas and 12,560 high-brake presentations from existing rows.
   Train/val conditional MAE improved to gas 0.171502/0.172743 and brake
   0.154961/0.157208, but large-steer worsened to 0.017518/0.018576. Step0
   gas MAE remains 0.288174/0.291879 and val predicts unnecessary brake 0.079.
   Plain closed loop finished **0/15 student episodes on 0/15 roads**, oracle
   15/15, same IDs/seeds; nine off_track, six crash, all fifteen with damage.
   No missing/interrupted episodes. Partial tail-fit improvement did not establish
   sufficient training fit or any full-lap reliability. Remain at the BC fitting
   gate; no held-out-only representation claim, state-decoding trial, second
   intervention, new data, protected seeds, RL or official actions. Artifacts
   and limitations are recorded in docs/BC.md; implementation checks passed
   49 tests / 49 subtests. This bounded user-directed gate is complete.
- 2026-09-29 user-directed next gate: distinguish training geometry coverage
  from pixel temporal/partial-observability limits. Collect unchanged oracle on
  IDs 1-5 x new training seeds 21-30 once, combine with 11-20, and compare a
  plain four-frame CNN at 10 versus 20 geometries under matched training budgets.
  Do not repeat rare-gas weighting, recovery-ratio, motion-feature, or split-head
  variants. Development remains seeds 31-33; preserve 34-35 and never open 38-40.
  If geometry expansion does not improve full-episode finishes meaningfully,
  compare longer pixel history or a lightweight temporal encoder directly with
  that CNN. Privileged quantities may be auxiliary training targets, never inputs.
  Prioritize conditional high-gas/high-brake/large-steer errors and full laps.
  No RL, official submission, or model confirmation is authorized.
- Geometry gate progress: new IDs 1-5 x seeds 21-30 collection completed
  50/50 full episodes on 50/50 roads (56,031 rows; ID 3 / seed 25 damage 0.2,
  other 49 damage-free). Combined training is 111,394 rows / 100 roads /
  20 geometries. Matched plain four-frame CNN control on ten geometries completed
  0/15 validation episodes on 0/15 roads versus oracle 15/15, IDs 1-5 x
  seeds 31-33. Expanded-data CNN also completed 0/15 on 0/15 roads versus
  oracle 15/15. High-gas/high-brake conditional errors were essentially
  unchanged; conditional large-steer MAE worsened. Geometry diversity alone
  was insufficient under this fixed budget/one training seed, not disproven
  generally. Isolated eight-frame pixel-history CNN also completed **0/15
  episodes on 0/15 roads** versus oracle 15/15; high-gas/high-brake fit remained
  essentially unchanged and large-steer conditional error worsened. Neither
  geometry expansion alone nor this simple history extension was sufficient.
  Partial observability is not proven; no latent-state decoding/auxiliary-target
  experiment has run. These are one-training-seed, equal-budget comparisons on
  exposed validation; no successful BC baseline. Fifty BC/local-contract tests
  passed. Seeds 34-35 and 38-40 stay unexamined; no RL or official actions.
  Restart recovery preserved completed roads and archived incomplete attempts;
  subsequent long-running jobs have persistent process lifetimes.

- `oracle-v1` tag created from clean `a70b359` before BC changes. BC evidence and
  decisions are recorded separately in `docs/BC.md`.
- Phase 3 collected 50/50 successful unique training roads (IDs 1-5 x seeds
  11-20, 55,363 frames) and 15/15 successful validation roads (IDs 1-5 x
  seeds 31-33). No privileged feature entered BC inference. Train on CUDA when
  available; submitted-style inference stays on CPU.
- Phase 4: initial CNN failed 0/1 validation episode; low aggregate prediction
  loss masked rare high-gas failure. Targeted gas weighting, image-only motion
  features and student-visited steering/control recovery were evaluated.
  Best-progress split-head diagnostic still failed 0/3 validation roads (ID 1
  x seeds 31-33); no BC finisher baseline was established.
- Freeze that diagnostic before the untouched local test: student **0/10
  episodes on 0/10 roads** versus oracle **10/10 on 10/10**, IDs 1-5 x seeds
  36-37 (two geometries). All student runs encountered an obstacle collision;
  8 retired from collision-associated off_track streak and 2 from damage.
  The first measured action mismatch was gas at step 0 on all 10 roads.
  Seeds 36-37 are now exposed and cannot be used to tune an untouched test;
  38-40 remain unexamined. No change was made from final-test results.
- The conditional DAgger/recovery gate was met by observed student-state shift,
  but sampled recovery did not produce a reliable finisher. Remain in BC
  diagnosis; no RL, official submission, or model confirmation. Complete
  evidence, commands, negative variants and checkpoints are in `docs/BC.md`.
