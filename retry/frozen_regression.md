# Frozen-policy development regression

`python -m retry.frozen_regression --plan /path/to/private/plan.json`
runs only a frozen candidate against existing baseline results. The private
plan and its `plan.sha256` bind the archive, package members, execution sources,
ordered cases, saved baseline result hashes, initial full observation and
state, road geometry, physical obstacles, native endpoint and cost limits.
The ledger's start time includes preparation time. Raw observations, seeds,
case vectors and policy archives stay outside the public repository.

The case harness verifies the frozen package and sources before reset, then
checks the actual reset identity before acting. The isolated worker receives
only reset/act operations and full pixels. Evaluator truth and case metadata
are excluded from its requests. The telemetry worker preserves the same
policy calls and memory used by the preceding comparison.

The coordinator runs cases sequentially, admits work using a conservative
observed cost rate and charges every new wrapper action before simulation.
Raw step ticks and reset ticks are also recorded. A previous completion lost
at an official endpoint stops all unlaunched cases. A normal failure shared
with the baseline is reported separately; it is not a lost completion.
Budget, time or technical interruption without an official endpoint remains
inconclusive. There are no automatic retries, baseline simulations or policy
changes.

Join prior candidate results and new results only when candidate archive,
baseline archive and scene identities match for every fixed case. Use the
completion-first aggregate to retain new/lost/common completions, common
failures, unexecuted and censored records. Lap and damage changes are
descriptive; failed-case progress is distinct from completion. No minimum
percentage threshold is introduced. Development regression does not establish
holdout generalization, final adoption or official-runtime parity.

The unchanged current-detection-cap candidate preserved the provisional
baseline's completions across the full reused development cohort. Lap effects
varied: some improved, while others slowed or stayed unchanged. The existing
failed condition remained an off-track failure, with slightly fewer unique
tiles reached and lower observed damage. Failed-case progress was excluded
from completed-lap metrics. This supports completion preservation on the
selected development cohort, without resolving the remaining failure or
establishing broader performance.

The original champion, provisional completion-first baseline and preceding
development-selected records remain preserved. No policy tuning, additional
holdout or sealed evaluation followed this regression comparison.
