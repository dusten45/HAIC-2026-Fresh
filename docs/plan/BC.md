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
