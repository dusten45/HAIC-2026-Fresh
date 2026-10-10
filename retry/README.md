# Fresh pixel experiments

This package provides a small observation-only baseline and a local evaluation
harness for the unchanged `variables-6` simulator. It does not import any previous
research packages or replace the root `agent.py`.

`pixel_agent.py` contains the straight-gas control, a gray-road-following policy,
and one speed/curvature variant. Policies receive only `(4, 84, 84)` observations.
The harness owns seeds, simulator state, metrics, and timing.

Use a Python 3.11 environment with the repository dependencies:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -m retry.evaluate \
  --plan /path/to/private/preregistered-v1.json \
  --output /path/to/private/new-run \
  --policy pixel_basic --split DEV --case-limit 3 --max-steps 120

.venv/bin/python -m unittest retry.test_boundaries -v
```

The private JSON plan contains `start_utc`, `deadline_utc`, `base`, `frame_skip`,
`max_steps`, and disjoint `split` lists of `{track_id, seed}` objects. Register the
plan and acceptance criteria before starting simulations. Outputs must be inside
the private plan directory and may not overwrite an existing run. Every run logs
plan/source SHA-256, observation/stack audits, actual raw ticks, completion,
progress, damage, diagnostic reward, reset/act/environment latency, and process
RSS. No plotting or training is required to run the harness.

Long DEV evaluations require `gate-cost.json` with passing `G0`/`G1` and the
matching `plan_sha256`. HOLDOUT/SEALED additionally require a private
`promotion.json` with the previous passing gate, frozen policy name and
`policy_sha256`; each protected split can be opened once. The harness checks the
authorization window before starting cases and simulation steps. On expiry it
stops and writes the available summary; it creates no scheduled work.

At 50 FPS, an action normally advances four raw ticks. Reset includes one internal
physics tick plus 50 warmup ticks, so the lap clock starts at `t=1.02`. Completion
uses `finish_time_s`, the finish-line center crossing tick, rather than the later
confirmation tick or the action count. `render_mode=None` still computes state
pixels on every raw tick.

The local thread guards match `local_runner.py`. They do not reproduce the
official isolated participant process, import deadline, or memory limit. Process
RSS includes the harness and is only a local estimate. Never include the harness,
tests, private plans, seed lists, run logs, or discarded research in a submission.
Only the observation-only policy is intended as potential participant code.

The additional research harnesses `diagnose`, `contrast`, `clearance_probe`, and
`arc_probe` run only preregistered DEV diagnostics. `diagnose` records separate
pixel estimates and simulator truth, exact action replay, snapshot fidelity,
and damage-physics counterfactuals. Oracle inputs are confined to harness classes;
participant candidates `geometry_agent`, `clearance_agent`, and `arc_agent` read
only observations and frozen numeric speed calibration. Counterfactual/oracle
results are diagnostic evidence, not official driving scores.

These harnesses require a private stage plan with `cases`, `stage_budgets`,
`max_actions`, `max_experiment_wall_s`, and the existing authorization fields.
Their manifests must be fixed before the corresponding experiment. A shared,
locked budget ledger counts actions and stops before the configured cap/deadline.
Case logs contain per-action truth, estimates, observation hashes and compressed
pixel/action traces, with exact source snapshots for reconstruction.

`process_probe` and `isolated_worker` measure a separate persistent participant
process, observation-only IPC, parent-enforced wall deadlines, child RSS, and
address-space limits. Fault probes exercise timeout/reaping, invalid responses,
crash handling and memory allocation failure. These checks do not establish
parity with the official server/container, RSS accounting or submission packaging.
The worker, diagnostics and all private records must be excluded from submissions.

`submission_probe` builds a private deterministic policy archive, imports its actual
`Agent` entrypoint in a separate process, and compares its actions and the original
local runner with saved research prefixes. `full_dev` evaluates an exactly frozen
archive through the same participant process. Full reset-to-retirement results must
be distinguished from startup boundaries and branches after shared action prefixes.

`failure_probe`, `anchored_probe`, `visible_oracle_probe`, and `route_probe` support
small preregistered failure contrasts. A true-geometry diagnostic can include a
different field of view or distant track segments; its gain alone does not isolate
pixel-estimation error. Match visible geometric support and retain the observed
speed feature when testing that interpretation. Passing an offline center-error
check does not replace a driving gate.

The additional observation-only prototypes `anchored_agent`, `ridge_agent`,
`waypoint_agent`, and `route_agent` are separate experiments. They do not replace
the frozen Arc candidate or the root entrypoint. The route prototype searches a
road grid with a vehicle/obstacle margin, using an endpoint on the actual visible
road. Its static vertex clearance is not a guarantee about the swept vehicle hull
or the controller's tracking. Gate each version before allocating full episodes.

`temporal_agent` retains recently detected obstacles using image motion for a
bounded interval, while keeping the route cost and controller unchanged.
`case_followup` labels a single full-case diagnostic explicitly; it does not
constitute the eight-case DEV gate. `temporal_boundary` checks a separately
preregistered remaining-case startup cohort. The temporal submission path is
available with `submission_probe --candidate temporal` only after its boundary
passes. All numeric speed calibration and experimental manifests remain private.

`protected_eval` evaluates the original locked HOLDOUT once using the passing
DEV candidate's exact archive. It shares the original evaluator's exclusive
split-opening marker, checks the upstream decision and archive hashes, and saves
metrics without simulator-truth diagnostics or pixel traces. It cannot open SEALED
or tune a candidate, and a failed run does not authorize a second opening.

`connected_agent` constrains the safe-grid endpoint to the start's connected
component. Four-connected labels match the existing eight-neighbor search's
prohibition on crossing blocked diagonal corners. `connectivity_probe` first
reconstructs the exact reference actions, then compares branches with identical
physics prefixes and observed-image history. It preserves the reference policy
and requires a separate full reset-to-finish preservation gate before adoption.

`motion_model`, `model_probe`, `finite_horizon_agent`, and `alternative_probe`
provide a separate attainable-motion contrast. Model fitting uses DEV-only
diagnostics; the candidate receives pixels and its own action history. Short
prediction accuracy is a prerequisite for a small driving pilot, not evidence
that the planner can complete a race. A failed pilot blocks deeper evaluation.

The trusted `process_probe` transport bounds the entire request/response call,
including pipe writes and partial lines. `runtime_audit` checks a stopped actual
archive worker and repeated complete recorded observation streams.
`python -m unittest retry.test_transport -v` checks partial, oversized and
fragmented responses. These local checks still do not certify official server
memory accounting or execution parity.

`paired_protected_eval` supports one separately reserved fresh protected pool.
Register and hash the case reservation, selected two frozen archives, completion
preservation criteria, action/wall budgets and query caps before `--mode prepare`.
Run `--mode baseline` and `--mode challenger` independently, then `--mode decide`.
The locked query ledger charges an episode before reset, including a crash, and
exclusive role markers prevent retries. It records metrics without diagnostic
truth or images, never reopens an earlier pool, and never opens SEALED.

`parameter_agent` exposes only the speed ceiling and curvature-dependent lateral
acceleration in the reference controller. Perception, obstacle memory, grid route,
lookahead and steering remain inherited. `parameter_analysis` verifies exact
default-action equivalence and measures which speed limits actually bind on a
fresh DEV cohort. `parameter_search` shares one-factor observations between a
small fixed-kernel surrogate search and uniform random search. Both have the same
number of new configurations, cases and maximum episode lengths; consumed actions
and wall time are reported separately because completion changes episode cost.

`parameter_promote` tests method winners on remaining DEV cases, then only one
chosen version on a separately reserved validation cohort. It requires full
completion preservation before packaging and another full original-DEV check
on the actual archive. `parameter_falsify` reconstructs legal observed/action
history and full-precision controller state before changing one speed-law factor
in a bounded branch. Such branches do not replace full race results.

The paired protected evaluator also accepts an explicitly named fresh pool,
additional upstream gates, independent query ledger and registered lap-ratio
criteria. Its opening can require remaining action and wall reserves. Previous
protected outcomes and scenes are never inputs to these DEV workflows, and all
seed reservations, selected constants, archives and result records stay private.

`schedule_agent` provides a separate pixel-only hypothesis: select between two
registered speed-law constants when an observed forward hazard falls inside the
existing lookahead and vehicle/obstacle margin. The distance, tracking lifetime
and steering law remain inherited. All constants are mandatory constructor
arguments; experiments and selected values remain private. `schedule_branch`
first reconstructs the reference's full observed history and controller state,
then runs one bounded matched DEV contrast. Passing it permits the separately
registered full DEV gates; it does not authorize adoption. `parameter_probe`
can measure this worker, and `submission_probe --candidate schedule` packages
only the policy after its fresh validation gate. Its trusted worker and branch
harness are excluded from the archive.

`information_contrast` reconstructs the exact frozen policy history before
substituting obstacle positions or semantic road support inside the image ROI.
Speed observations, hazard-dependent speed law and the controller stay fixed.
The semantic substitute can reveal occluded geometry; these are privileged DEV
diagnostics, never official driving scores or deployable policies. An observed
continuation must reproduce every saved action, state and observation hash.

`projection_agent` and `chord_agent` are separate structural hypotheses. The
former tests a registered pixel-centre convention without fitting offsets; the
latter prevents a target chord from skipping an obstacle detour when a shorter
clear chord exists. Both inherit the speed law and memory. `structural_branch`
tests bounded matched branches before any full-reset cohort, and `chord_worker`
provides a separate pixel-only process for a qualifying full DEV pilot.
Coordinate accuracy, local contact reduction and full completion/lap improvement
are distinct gates. Report damage separately as robustness, not official ranking.
Neither prototype changes the root entrypoint or an already frozen archive.

`tracking_diagnostic` replays saved DEV observations without environment steps,
verifies the frozen actions, and labels detection births, pre-association motion,
and remembered outputs against the same physical obstacle at the same time.
Truth is diagnostic only. Repeated frame counts do not establish independent
sample sizes, visibility, collision causality, or driving improvement.

`memory_agent` provides a fresh-only ablation and one Boolean confirmation
hypothesis: fresh detections are used immediately, but persistence requires
confirmation across observations within the inherited association radius.
The motion estimator, lifetime, routing, controller and speed settings stay
fixed. `memory_branch` reconstructs each estimator from the same legal history
and restores the exact frozen controller state; `memory_worker` supplies only
pixels to the separate policy process for qualifying full-reset DEV probes.
Short branches, full completion/lap results and robustness gates remain separate.

`factorial_agent` independently selects the obstacle history used by the fixed
route and the recent hazard history used by the inherited speed schedule. Both
estimators and the fresh detector observe each actual frame in every mode.
`factorial_branch` reconstructs only the recorded past, then runs the registered
information intervention on actual future observations. Exact continuations and
terminal outcomes distinguish a first action difference from a closed-loop
failure; these partial-race diagnostics are not deployable-policy scores.

`separated_agent` gates persistence of path obstacles on confirmation while
retaining fresh detections immediately and the original recent-risk channel.
Its separate uniformly conservative speed control performs
the same estimator calls per frame. `separated_worker` exposes only current
pixels to these full-reset policies, and `parameter_probe` records their actual
latency and memory. Matching calls does not guarantee identical running time on
different trajectories. Completion, common-completion lap ratios, damage and
stagnation remain separate preregistered gates; a slowdown's damage reduction
alone does not establish perception improvement. These research prototypes do
not replace the root entrypoint or a frozen selected archive.

`risk_speed_diagnostic` reconstructs saved DEV actions without creating an
environment. It substitutes aligned pre-action speed only in the hazard gate,
while retaining recorded estimator history, path targets, steering and pixel
speed feedback. It reports decision-local changes and HUD pixels rather than
treating aggregate speed error as a driving gain. A sparse or irrelevant change
blocks a privileged driving contrast; the offline actions are not policy scores.

`feedback_branch` supplies privileged current speed only to the gas/brake
feedback calculation after the original controller computes steering and its
target from pixels. Hazard scheduling, target speed, path lookahead, tracking
motion and coefficients remain inherited. Each actual frame also records the
original longitudinal action as a local shadow comparison. Later cross-branch
observation and steering differences are closed-loop effects. Only registered
short outcome differences permit a terminal followup; neither branch is a new
eligible policy, and all physics prefix replays count against the shared budget.

`bar_feedback_agent` reads only the interior of the official white speed bar.
Its monotone inverse table must be derived from the official renderer without
fitting DEV scenes. The original pixel speed continues to govern hazard
scheduling, path lookahead and tracking motion; only gas/brake feedback uses
the bar reading. Steering, target speed and controller coefficients remain
inherited. Reward invariance and paired speed error are offline gates before
`bar_feedback_branch` runs actual matched legal-history continuations. Only
passing branches permit a separately registered full-reset pilot through
`bar_feedback_worker` and `parameter_probe`. The worker receives current pixels
and a fixed renderer-derived table, never simulator state. Tables, calibration,
seeds and experiment results stay private. A successful DEV pilot is a research
decision and does not replace the selected archive or open protected splits.

`fresh_dev_pair` compares two frozen archives on a privately registered new DEV
cohort. The registered road geometry is checked against each actual reset, and
both roles must have identical initial pixel observations. Shared action and
wall budgets cover both workers. Each pair is classified as preserved, new,
lost or common-failure completion before common-completion lap ratios are used;
early gates and incomplete horizons are reported separately as censored.
Preregistered robustness violations stop the remaining cohort. This development
validation does not open a protected split or select a champion. Archives,
splits, raw metrics and decisions remain private.

`distance_target_agent` adds one target-speed limit to an inherited pixel ROI
feedback policy. It uses the existing forward-hazard eligibility and Euclidean
center distance minus the existing radius/buffer. This is a proximity heuristic,
not distance along the route or a measured stopping-distance guarantee. Tracking,
route selection, steering, speed estimation and feedback gains remain inherited.
The uniform slow control applies the same minimum speed ceiling everywhere;
it does not match mean speed or braking energy. `distance_target_worker` keeps
the policy in a separate current-pixel-only process. `distance_target_probe`
charges every physical prefix replay, checks frozen actions/observations/state,
then activates the registered treatment on actual future observations. A local
ROI shadow checks action isolation at each branch's own state; divergent future
steering across trajectories is expected. Damage, progress, counters, completion
and censoring require separate gates. Plans, source traces and results remain
private; the prototype does not change the root submission entrypoint.
