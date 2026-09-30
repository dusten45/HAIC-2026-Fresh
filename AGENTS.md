# Agent Instructions

## Mission and Rules

- Build the strongest 2026 HAIC CarRacing agent from this official Participants template. Prioritize reliable full-episode finishes before lap time; treat all design choices as provisional.
- Treat `docs/plan/COMMON.md` plus the plan for your assigned task as the research contract: `docs/plan/BC.md` for trajectory collection, learned-policy training, and BC diagnosis; `docs/plan/ORACLE_V2.md` for the separate high-speed teacher experiment; `docs/plan/ORACLE_V3.md` for the frozen leaderboard-targeted teacher checkpoint; `docs/plan/ORACLE_V4.md` for coupled-grip planning and feedforward teacher improvement; `docs/plan/CLEANUP.md` for authorized tooling maintenance only. Follow the selected plan's current phase and gates; do not skip stages without evidence, substitute a preferred algorithm, or expand the research scope on your own.
- For competition facts, prefer the current [competition website](https://scholarships-hardwood-headers-influenced.trycloudflare.com/), then the [official Participants repository](https://github.com/2026-HAIC/Participants), then local notes. Recheck official sources before submission or model confirmation; resolve conflicts before acting.
- Do not modify the supplied environment (`env_wrapper.py`, `damage.py`, `core/`) to improve performance. Keep diagnostic instrumentation external to the supplied environment; measure all reported performance in the unmodified official environment. Implement the `agent.py` contract and keep submitted inference within official CPU, time, memory, and package limits.

## Research Evidence

- Report complete-episode finish counts with their episode and road denominators. Raw reward, progress, damage, and local diagnostics are internal proxies, not official ranking scores.
- Declare training and evaluation roads by track ID, geometry seed, and relevant conditions. Treat any track/seed whose results influenced a design decision as exposed evaluation; never present it as an untouched holdout.
- Separate one-seed observations from replicated, matched comparisons. Verify claims against run artifacts, keep negative results, and label untested causal explanations as hypotheses.
- Treat official private tracks as an unseen final target, not an available holdout. A promising local result is not an official submission or a confirmed competition model.
- Obtain explicit user authorization immediately before an official submission or model confirmation.

## Working Safely

- Prioritize implementing and improving the learned driving model over exhaustive defensive checks or repeated verification. This is a research agent, not a general-purpose public service; run only checks needed to substantiate a decision and avoid redundant safeguards.
- While asynchronous data collection or training runs, do not use `sleep` to wait. Do independent useful work; if no work remains, schedule a wakeup for the next meaningful check-in and resume then.
- Keep changes and experiment records small and task-relevant. Check Git status before edits, coordinate overlapping work, and never discard another person's changes or run artifacts.
- Update only your task's plan in `docs/plan/`; do not write concurrent task checkpoints into `COMMON.md` or another task's plan. A pause, resume, or teacher selection in one plan does not change another plan's status or scope. Coordinate shared-contract changes before editing. For a new user-authorized independent task, create a separate clearly named plan in this directory and add it to this guide rather than recreating a monolithic plan.
- Before committing, inspect status and diff; exclude secrets, model weights, generated runs, and unrelated changes. Verify `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT` identify `dusten45`.
- Before authenticated Git operations, verify `gh api user --jq .login` is `dusten45` and check the actual remote and credential helper. Push only to private `origin`, never to official `upstream`.

## Repository Guide

- [`README.md`](README.md): official template setup, `Agent` contract, submission layout, and evaluation limits; retained at the root as the repository entry point.
- [`docs/plan/COMMON.md`](docs/plan/COMMON.md): shared research contract, original Phase 1-2 gates, exposed oracle evaluation roads, and frozen oracle-v1 checkpoint; read before the task-specific plan.
- [`docs/plan/BC.md`](docs/plan/BC.md): Phase 3/4 splits and gates, geometry/observability diagnosis, and BC status; update for learned-policy work only.
- [`docs/plan/ORACLE_V2.md`](docs/plan/ORACLE_V2.md): separate high-speed local teacher scope and v2 checkpoints; update for oracle-v2 work only.
- [`docs/plan/ORACLE_V3.md`](docs/plan/ORACLE_V3.md): frozen leaderboard-targeted teacher checkpoint on the three designated exposed roads.
- [`docs/plan/ORACLE_V4.md`](docs/plan/ORACLE_V4.md): separate coupled-grip planning and feedforward teacher improvement, preserving frozen v3.
- [`docs/plan/CLEANUP.md`](docs/plan/CLEANUP.md): user-authorized research-tool maintenance scope and validation gate; does not resume research experiments.
- [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md): verified observation/action/reset/termination and local environment contracts, with source references.
- [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md): diagnostic and oracle evaluation protocols, reproduction commands, artifacts, results, and limitations.
- [`docs/BC.md`](docs/BC.md): behavior cloning splits, trajectory protocol, offline and closed-loop evidence and decisions.
- [`docs/RUNS.json`](docs/RUNS.json): compact saved-run catalog; regenerate with `python -m oracle.catalog` after completed work, without opening traces or weights. Keep historical failures and existing run paths; generated data and source snapshots remain under ignored `runs/`.
- [`oracle/recording.py`](oracle/recording.py): local serialization, diagnostics, execution fingerprints, and source snapshots without simulator/CLI bootstrap; frozen v1 keeps its original helpers.
- [`oracle/`](oracle/): privileged local-only oracle runner, controller, and report utility; none is the submission `Agent`.
- [`tests/`](tests/): local interface, environment parity, and oracle-tool regression tests.
