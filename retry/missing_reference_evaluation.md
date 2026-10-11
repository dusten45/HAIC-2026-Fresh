# Missing DEV reference evaluation

`single_frozen_dev.py` fills one explicitly authorized, missing DEV reference
using an unchanged, previously qualified champion configuration. It reuses the
pixel worker and endpoint evaluator from the frozen comparison harness.

Before publishing a plan, audit registered DEV metadata and linked endpoint
records. Preserve the distinction between an official champion, a provisional
baseline, and a composite candidate whose external assets affect its behavior.
A source commit alone need not identify a complete fixed-parameter ZIP.

The private plan binds the inventory, qualification, archive and configuration,
source/runtime hashes, existing reset receipt, budget, and finite time window.
The readiness gate permits one claim. The runner allows one champion episode,
capped at 2,000 actions, with no retry or replacement. It compares road geometry,
physical obstacles, recorded reset state, and the full four-frame observation
before calling the actor. This does not prove equality of unrecorded solver state.

The optional DEV recorder copies observations, actions, and evaluator-side
physical states after the original environment calls. It adds no policy, model,
renderer, reset, or step calls and sends no privileged state to the actor.
Recorded observation and action streams are checked against the endpoint
evaluator's rolling hashes. Private plans, traces, models and results stay outside
the public repository.

`PASS` means a valid observed endpoint, including a normal driving failure.
A technical failure or nonterminal action cap is inconclusive. Compare completion
first; compare lap time only for common completions, and report damage separately.
One DEV result does not establish generalization or isolate the effects of several
changed components. This evaluator does not establish final submission equivalence.
