# Frozen curvature-term holdout comparison

The baseline is the original hazard-scheduled pixel controller with global cap40.
The candidate removes only the additive curvature denominator term, retaining
the same perception, tracking, steering, hazard schedule and pedal gains. Both
exact archives were frozen after the earlier two-road development comparison.

Each archive reproduced its saved development actions, a warm-reset prefix and
a second cold-process prefix. All 1,287 replay actions matched. These were fresh
processes on the same host; fresh-machine and official-server parity remain
unverified. Policy inputs were limited to reset/act and the official pixel stack.

Four fresh road geometries and obstacle lineages were registered using identity
metadata and exclusions from previous use. Each pair shared its environment seed
and initial geometry, obstacles, state and observation hashes. Arm order alternated.
The evaluator retained endpoints, costs and rolling hashes, with one aggregate
inspection after the batch. It saved no holdout frames or failure trajectories.

The registered comparison keeps missing, censored and invalid endpoints separate
from normal driving failures. Any lost baseline completion prevents adoption.
Without a loss, new completions take precedence. Otherwise at least two common
completions, negative median paired lap change and mean paired lap ratio below
one pass. No minimum percentage or requirement that every road become faster was
added. Normal failures and action-cap censoring preserve the registered remaining
case order; technical failures stop without retry.

The candidate passed: both policies completed all four roads. Three laps improved
and one slowed by 40 ms. Median paired change was -2,870 ms and mean paired ratio
was 0.94917. Total damage was 0.2 for each policy, with one pair increasing by 0.2
and another decreasing by 0.2. The largest episode p95 action latency increased
from 10.71 to 12.42 ms; maximum action latency decreased from 52.61 to 47.09 ms.
These are descriptive warnings and historical timing samples, separate from rank.

The exact qualified candidate becomes the local research champion after the
independent result and artifact review. Both previous archives and manifests are
preserved. This supports transfer beyond the two development roads but does not
show uniform improvement, lower damage everywhere or a failure probability of zero.
Private road identities, artifacts and document material remain outside the repo.

The next development question is whether retaining the old denominator only near
hazards preserves the time gain. No additional experiment or sealed opening is
authorized by this report.

The [public aggregate](curvature_offset_holdout_result.json) includes measured
costs. `export_frozen_comparison.py` produces it using explicit fields and scalar
validation, omitting private identifiers and ordered per-road records.
