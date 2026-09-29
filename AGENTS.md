# Agent Instructions

## Mission and Rules

- Build the strongest 2026 HAIC CarRacing agent from this official Participants template. Prioritize reliable full-episode finishes before lap time; treat all design choices as provisional.
- Treat `docs/PLAN.md` as the current research contract. Follow its current phase and gates; do not skip stages without evidence, substitute a preferred algorithm, or expand the research scope on your own.
- For competition facts, prefer the current [competition website](https://scholarships-hardwood-headers-influenced.trycloudflare.com/), then the [official Participants repository](https://github.com/2026-HAIC/Participants), then local notes. Recheck official sources before submission or model confirmation; resolve conflicts before acting.
- Do not modify the supplied environment (`env_wrapper.py`, `damage.py`, `core/`) to improve performance. Keep diagnostic instrumentation external to the supplied environment; measure all reported performance in the unmodified official environment. Implement the `agent.py` contract and keep submitted inference within official CPU, time, memory, and package limits.

## Research Evidence

- Report complete-episode finish counts with their episode and road denominators. Raw reward, progress, damage, and local diagnostics are internal proxies, not official ranking scores.
- Declare training and evaluation roads by track ID, geometry seed, and relevant conditions. Treat any track/seed whose results influenced a design decision as exposed evaluation; never present it as an untouched holdout.
- Separate one-seed observations from replicated, matched comparisons. Verify claims against run artifacts, keep negative results, and label untested causal explanations as hypotheses.
- Treat official private tracks as an unseen final target, not an available holdout. A promising local result is not an official submission or a confirmed competition model.
- Obtain explicit user authorization immediately before an official submission or model confirmation.

## Working Safely

- Keep changes and experiment records small and task-relevant. Check Git status before edits, coordinate overlapping work, and never discard another person's changes or run artifacts.
- Before committing, inspect status and diff; exclude secrets, model weights, generated runs, and unrelated changes. Verify `git var GIT_AUTHOR_IDENT` and `git var GIT_COMMITTER_IDENT` identify `dusten45`.
- Before authenticated Git operations, verify `gh api user --jq .login` is `dusten45` and check the actual remote and credential helper. Push only to private `origin`, never to official `upstream`.

## Repository Guide

- [`README.md`](README.md): official template setup, `Agent` contract, submission layout, and evaluation limits; retained at the root as the repository entry point.
- [`docs/PLAN.md`](docs/PLAN.md): current research scope, phase gates, exposed-road declaration, and status checkpoint.
- [`docs/ENVIRONMENT.md`](docs/ENVIRONMENT.md): verified observation/action/reset/termination and local environment contracts, with source references.
- [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md): diagnostic and oracle evaluation protocols, reproduction commands, artifacts, results, and limitations.
- [`oracle/`](oracle/): privileged local-only oracle runner, controller, and report utility; none is the submission `Agent`.
- [`tests/`](tests/): local interface, environment parity, and oracle-tool regression tests.
