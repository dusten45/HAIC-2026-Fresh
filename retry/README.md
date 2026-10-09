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
