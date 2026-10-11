# Stage138: frozen134 completes four unseen DEV

**Unchanged local champion134 completes all four fresh DEV.** These conditions
are development data from this point onward. There are no normal DNFs or
technical failures. The contact in one completion remains a diagnostic risk;
four DEV successes do not establish a general failure probability.

| Anonymous DEV | Lap time | Damage | New native actions |
| --- | ---: | ---: | ---: |
| A | 52.700s | 0.6 | 659 |
| B | 48.940s | 0.0 | 612 |
| C | 38.400s | 0.0 | 481 |
| D | 43.900s | 0.0 | 550 |

All completed, so the registered diagnostic uses saved elapsed time. The
controller sets target speed to `min(40, sqrt(a / max(abs(kappa), 1e-6)))`,
where `a` is normal7 or near-obstacle5. Obstacle exposure counts only when5
tightens the target relative to normal7. Near alone does not count. A recorded
action is classified at bound or braking when its actual HUD feedback speed
is at least target minus1m/s, or its returned brake is positive. Finish-clipped
action dwell is the time weight; terminal zero-dwell rows still count as actions.

| Target constraint | Fresh DEV exposure | Fresh at bound / braking | Fresh transient | Existing DEV at bound / braking |
| --- | ---: | ---: | ---: | ---: |
| Normal pursuit curvature7 | 93.02s (50.57%) | 56.54s | 36.48s | 54.08s |
| Additional near-obstacle5 | 25.92s (14.09%) | 20.00s | 5.92s | 21.12s |
| Global cap40 | 65.00s (35.34%) | 5.76s | 59.24s | 5.66s |
| Total | 183.94s | 82.30s | 101.64s | 80.86s |

Existing134 DEV time is184.80s, with constraint exposures48.48%,15.50%,36.02%
respectively. Stored actions and observation hashes align; target-law error
is zero on every fresh row, target fields are complete, and dwell matches
recorded lap times. Existing logs are reused with no baseline or policy replay.

**Normal pursuit-curvature control is the leading bound exposure in both
sets.** Most global-cap exposure is still below target without braking. These
are exposure diagnostics, not recoverable time or a causal speed-loss estimate.
Pursuit curvature also includes lateral correction and perception effects;
it is not physical road curvature. The logs do not show whether7 is too
conservative or necessary for completion.

The proposed single change is **normal lateral-acceleration budget7→8m/s²**.
Near-obstacle5 and cap40 remain fixed as part of this one-scalar intervention.
The source-law target increase is at most6.90%; that is not a lap-time forecast.
This directly tests the largest bound exposure with a small dose, without
introducing the previously unsuccessful generic slowdown or margin expansion.

Proposed small comparison: first check target arithmetic on saved observations,
then run only the candidate on A (the contact-bearing newDEV) and B (the clean
newDEV with the greatest curvature bound/braking time). Reuse cached134 endpoints
and require identical reset signatures. Cap at4000 native actions,2000 per case.
Stop on the first lost completion, censoring or technical/reset mismatch, with
no retry, retuning or replacement. Retain for remaining DEV only if both
completions survive and their completed lap-time sum improves. Report time and
damage separately; add no damage or1-percent veto. This is a proposal: no new
candidate is implemented, tested, adopted or given a budget reservation here.

Cost: **2302/8000 new native actions**,95.112s wall including records,
78.187s evaluator CPU and17.205s actor CPU. Raw step ticks9203 and reset ticks204
are separate from the wrapper-action budget. Budget remains722000; cumulative
native620616, research remaining17384, final reserve84000 untouched. The prior
8229 is part of the historical research balance, not an additional reserve.

Champion134 remains frozen. HOLDOUT details/outcomes and SEALED stay closed.
Basic qualification and the existing observer are reused without a ZIP rebuild
or full audit stage. Private conditions, frames, traces and plans stay private.
The evidence applies to this cloud/runtime; official-server behavior remains
unverified. No next experiment, paid resource or automatic extension is started.

[Aggregate evidence](champion_fresh_dev138_result.json) records outcomes,
time-weighted constraints, cost and the one-change comparison proposal.
