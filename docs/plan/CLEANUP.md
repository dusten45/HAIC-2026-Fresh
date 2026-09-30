# Research Tooling Cleanup

## Scope

The 2026-09-30 user request authorizes all six structural cleanup findings:
shared experiment contracts, restart lifecycle, report semantics, explicit
baseline/diagnostic settings, independent recording helpers, and artifact indexing.
This is tooling maintenance, not permission to tune controllers, train policies,
inspect protected roads, submit, commit, or confirm a model.

Preserve the supplied environment, frozen oracle-v1 controller/runner, submission
Agent, historical checkpoints, failed experiments, and existing run paths.
BC and oracle-v2 research status stays in their own plans. New source fingerprints
must not retroactively certify old runs or transfer old performance to new code.

## Validation Gate

Use one targeted unit-test pass for changed BC/v2/recording/indexing contracts.
No new complete-episode experiments or repeated broad environment verification.

## Status

All six cleanup items implemented. BC contracts, execution fingerprints, restart
state, plain defaults and explicit diagnostic options are separated; v2 stage
configuration, artifact identity checks, execution groups and metric definitions
are explicit. New BC/v2 outputs retain recoverable source snapshots via independent
recording helpers. `docs/RUNS.json` indexes 110 existing directories, including
partial runs and negative variants, without moving or deleting their artifacts.

Validation: one focused mocked/pure unit pass, **39 tests passed in 2.054 seconds**;
`git diff --check` passed. Frozen v1 controller/runner, supplied environment and
Agent remain byte-unchanged from `oracle-v1`. No research training, simulator
rollouts, protected-road evaluation, submission, commit or model confirmation ran.
No new-code driving-performance claim is established by this maintenance pass.
