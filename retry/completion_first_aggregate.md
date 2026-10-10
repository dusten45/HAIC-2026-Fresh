# Completion-first paired aggregation

`completion_first_aggregate.summarize(pairs, expected_case_ids)` summarizes an
already fixed cohort without executing an agent or simulator. Each pair has a
`case`, `baseline`, and `candidate`. Records contain `completed`,
`terminal_observed`, `censored`, `lap_ms`, `unique_tiles`, `total_tiles`,
`damage`, and `retire_reason`.

The official completion flag determines completion. Visiting every tile is
not an additional finish requirement. Only observed, uncensored endpoints
enter the new-completion, lost-completion, common-DNF, and common-completion
categories. A missing candidate is unexecuted. Censored, nonterminal, or
invalid records remain inconclusive. Duplicate and unexpected case IDs are
rejected, and the output follows the supplied case order.

Lap deltas and ratios use common completions only. Common-DNF tile vectors
remain visible separately. Total damage includes its observed-record count
and an exposure qualification, since episode durations and termination types
may differ. The utility supplies descriptive evidence and no policy-selection
threshold or winner.

The preceding distance-cap candidate remains kept with its completion gain
and lap cost. A historical lap-cost benchmark is descriptive and is not a
stopping criterion or a substitute for the official completion-first
objective. The subsequent authorized scope expansion used that exact frozen
candidate on the remaining development cases in order, with a stop at the
first loss of a previous completion. Prior baselines and candidate outcomes
were reused without new simulation charges; no policy, threshold, or speed
estimator was tuned.

Across the joined development cohort, every previous completion was
preserved and an additional completion was recovered. Every common
completion was slower, while observed damage was no greater on those cases.
One common DNF remained with only a small progress change. This is a
completion gain with a time tradeoff on a reused development cohort; it does
not establish broad dominance, transfer performance, or champion promotion.
No holdout or sealed evaluation followed. Exact case vectors, raw inputs,
private manifests, and budget evidence remain outside the public repository.

The focused tests cover all four normal categories, stable ordering,
descriptive time and damage metrics, and separation of missing, censored, and
nonterminal results from DNF. They also reject duplicate or unexpected IDs.
