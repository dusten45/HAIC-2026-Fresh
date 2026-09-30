# Independent Restart: Shared Research Contract

Shared research scope, original phase gates, declared oracle evaluation roads,
and frozen oracle-v1 checkpoint. Read this document first, then the plan for the
assigned task: [BC.md](BC.md) for learned-policy work or
[ORACLE_V2.md](ORACLE_V2.md) for the separate high-speed teacher experiment.
Task-specific plans own their current status; this shared document is not a
concurrent progress log. This reorganization does not authorize new experiments,
resume paused work, or change any research gate.

## Research Contract

Start independently from the official Participants template. Do not import code or
conclusions from previous HAIC research repositories. The immediate goal is the
simplest driving system that reliably finishes complete episodes, not reward,
speed, submission eligibility, or a particular learning algorithm.

Privileged vehicle state and track geometry remain allowed only for local
teacher generation and analysis, never as a learned policy input. Do not modify
`env_wrapper.py`, `damage.py`, or `core/`. Keep instrumentation external.
No RL, world model, offline RL, official submission, or model confirmation is
authorized by these plans. Obtain fresh explicit user authorization before any
official submission/model confirmation.

## Declared Oracle Evaluation Roads

- Track IDs: 1, 2, 3, 4, 5.
- Geometry seeds: 1 through 10 for each track ID.
- Total: 50 explicitly exposed development/evaluation configurations (10 base
  geometries), not a holdout. Expanded by user request on 2026-09-29 after the
  initial 20-configuration evaluation; preserve those historical results.
- Record actual reset arguments and all environment conditions per episode.
- Use matched conditions across controller comparisons; change one variable at
  a time. Repeat complete episodes to check reproducibility and disclose episode
  and distinct-road denominators separately.
- Prioritize finish count. Reward, progress, damage, speed, and diagnostics are
  internal proxies, not official ranking scores.
- BC training, validation, and local test splits are declared in [BC.md](BC.md);
  the oracle evaluation grid is not a learned-policy holdout.

## Phase 1: Understand and Exercise the Environment

1. Inspect the complete local template and current official sources; document
   observations, actions, reset, reward, termination, finish, evaluation limits,
   vehicle state, geometry, and coordinate transformations with code references.
2. Run bounded no-op, random, and simple manual-action diagnostics. Inspect actual
   observations, reward, privileged state, and termination. Run full baseline
   episodes where needed to establish typical episode length and failure rules.
3. Build minimal external diagnostics with per-step JSONL traces and episode
   summaries, recording versions, commands, seeds, and environment conditions.

Gate: contracts and control conventions must be verified from code and actual
execution before claiming controller performance.

## Phase 2: Primitive Oracle

1. Implement a minimal waypoint/centerline controller using privileged pose,
   speed, and geometry, beginning with simple pursuit and conservative speed.
2. Evaluate an initial full episode, then the declared 50-configuration matrix.
3. Classify each failure (overshoot, oscillation, insufficient steering, excessive
   speed, stuck, collision, waypoint progression, reset/termination, or another
   evidenced cause). Locate the earliest trajectory departure, not just the
   terminal symptom. Label causal explanations as hypotheses until tested.
4. If needed, make a single targeted change and run matched comparisons. Preserve
   negative results. Avoid blind multi-parameter searches.
5. Aim for 90-100% complete-episode finishes over all 50 configurations and verify the
   chosen controller with repeated matched full-episode evaluation. If this is
   not achieved, continue until a concrete fundamental blocker is evidenced.

Record finish/fail, progress, failure step/location/type, speed, steering,
saturation, curvature, vehicle and track-relative state, action, reward,
termination/truncation, and step/time/track identifiers. Oracle-policy action
difference is not applicable until a learned policy exists. Bulk observation
trajectory collection belongs to Phase 3 and is not started implicitly.

## Reproducibility and Checkpoints

Keep environment-contract documentation, compact experiment summaries, commands,
and failure evidence in the repository. Keep generated runs and weights out of
Git. Inspect status/diff before commits, verify author and committer are
`dusten45`, and verify authenticated GitHub identity, credential helper, actual
remote, and private origin before pushing. Never push to official upstream.
Do not include unrelated pre-existing changes without authorization.

## Completed Phase 1-2 Checkpoint

- 2026-09-29: plan established before implementation. `AGENTS.md` began as a
  pre-existing untracked guide and was later updated at user request with this
  repository guide and links to the major documents.
- Phase 1 complete: source contract in [../ENVIRONMENT.md](../ENVIRONMENT.md);
  real no-op/random/manual diagnostics in [../EXPERIMENTS.md](../EXPERIMENTS.md),
  including measured steering convention.
- Phase 2: unchanged centerline baseline finished 0/20 configurations; all failed
  after obstacle collision (15 stalled, 5 damage retirement). Added only smooth
  obstacle-offset reference geometry, retaining speed and steering parameters.
- Candidate first matrix is complete: 20/20 episodes on 20/20 configurations
  finished with zero damage/collision. Partial `runs/avoidance_matrix` (13 cases)
  plus `runs/avoidance_matrix_remaining3` (2) and `remaining4` (5) reconciles one
  preserved external-timeout trace. No simulator failure was hidden by timeout.
- Controller/runner frozen at `bf85da7`; two further episodes per configuration
  completed in `runs/verification_track1` through `track4`: 40/40 finished.
- Final main evaluation: **60/60 episodes, all 20/20 configurations successful
  3/3 times**, zero collision/damage. Each road's three full traces have identical
  hashes; all runs share one source/settings/package fingerprint. Five distinct
  base geometries verified. Initial single-road success probe is separate (1/1).
- Lap range 78.86-98.64 simulation seconds; 987-1,234 actions, unchanged cap2,000.
  At that checkpoint, 27 local tests passed; supplied environment and Agent unchanged.
- The user then expanded scope to IDs 1-5 / seeds 1-10, still Phase 1-2 only.
  Evaluated all 50 with the unchanged `bf85da7` controller and original settings;
  adjusted only the external runner's permitted/default grid. All traces retained.
- Expansion checkpoint `27d9656`: new CLI grid tested (28 local tests pass),
  controller unchanged. First-pass artifacts: `runs/expanded_first_t<ID>_low`
  (seeds 1-5) and `_high` (seeds 6-10). First pass finished 50/50, with 49/50
  without damage. Repeat pass completed in `runs/expanded_repeat_t1` through `t5`.
- **Expanded result: 100/100 complete episodes, all 50 configurations successful
  2/2 times.** No incomplete or missing episodes. Ten distinct base geometries,
  one execution fingerprint, and identical repeated trace hashes on all 50 roads.
  Episode range: 923-1,236 actions, lap 73.76-98.80 simulation seconds.
- ID5/seed3 had one collision at action 754 and final damage 0.2 in each repeat,
  but finished both. Other 49 configurations were damage-free in both repeats.
  Expanded collision-free reliability is NOT established: 98/100 episodes had
  no damage, 2/100 had damage. Controller parameters have not been tuned.
- Expanded Phase 1-2 gate met. The 100-episode expanded result excludes
  the historical 60-episode initial-set evaluation. All 28 local tests pass.
- This is exposed local oracle evidence, not unseen-track generalization or a
  submission-ready policy. The user explicitly authorized Phase 3/4; not RL.
