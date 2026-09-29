# Independent Restart: Finish First

## Research Contract

Start independently from the official Participants template. Do not import code or
conclusions from previous HAIC research repositories. The immediate goal is the
simplest driving system that reliably finishes complete episodes, not reward,
speed, submission eligibility, or a particular learning algorithm.

Current scope is **Phase 1 and Phase 2 only**. No RL, neural policy, behavior
cloning, DAgger, or complex MPC. Privileged vehicle state and track geometry are
allowed for this local oracle. Do not modify `env_wrapper.py`, `damage.py`, or
`core/`. Keep instrumentation and control external to the supplied environment.

## Declared Evaluation Roads

- Track IDs: 1, 2, 3, 4.
- Geometry seeds: 1, 2, 3, 4, 5 for each track ID.
- Total: 20 explicitly exposed development/evaluation roads, not a holdout.
- Record actual reset arguments and all environment conditions per episode.
- Use matched conditions across controller comparisons; change one variable at
  a time. Repeat complete episodes to check reproducibility and disclose episode
  and distinct-road denominators separately.
- Prioritize finish count. Reward, progress, damage, speed, and diagnostics are
  internal proxies, not official ranking scores.

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
2. Evaluate an initial full episode, then the declared 20-road matrix.
3. Classify each failure (overshoot, oscillation, insufficient steering, excessive
   speed, stuck, collision, waypoint progression, reset/termination, or another
   evidenced cause). Locate the earliest trajectory departure, not just the
   terminal symptom. Label causal explanations as hypotheses until tested.
4. If needed, make a single targeted change and run matched comparisons. Preserve
   negative results. Avoid blind multi-parameter searches.
5. Aim for 90-100% complete-episode finishes over all 20 roads and verify the
   chosen controller with repeated matched full-episode evaluation. If this is
   not achieved, continue until a concrete fundamental blocker is evidenced.

Record finish/fail, progress, failure step/location/type, speed, steering,
saturation, curvature, vehicle and track-relative state, action, reward,
termination/truncation, and step/time/track identifiers. Oracle-policy action
difference is not applicable until a learned policy exists. Bulk observation
trajectory collection belongs to Phase 3 and is not started implicitly.

## Later Phases (Not Authorized Now)

- Phase 3: after reliable oracle finishes, collect successful trajectories with
  observations, actions, privileged/track-relative state and metadata.
- Phase 4: simple behavior cloning diagnostics: training fit, held-out prediction,
  closed-loop tracking, first deviation, and recovery.
- Phase 5: consider learning only in response to measured failure hypotheses.

Never represent local results as official submission performance. Obtain fresh
explicit user authorization before any official submission/model confirmation.

## Reproducibility and Checkpoints

Keep environment-contract documentation, compact experiment summaries, commands,
and failure evidence in the repository. Keep generated runs and weights out of
Git. Inspect status/diff before commits, verify author and committer are
`dusten45`, and verify authenticated GitHub identity, credential helper, actual
remote, and private origin before pushing. Never push to official upstream.
Do not include unrelated pre-existing changes without authorization.

## Current Status

- 2026-09-29: plan established before implementation. Local repository has an
  untracked pre-existing `AGENTS.md`; leave it untouched and out of task commits.
- Phase 1 in progress; controller and performance are not yet established.
