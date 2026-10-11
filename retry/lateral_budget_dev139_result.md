# Stage139: normal lateral8 preserves two134 DEV completions and improves time

**Keep the exact lateral8 candidate for the next remaining DEV comparison;
retain champion134 and rollback116.** This is a small one-parameter comparison
under the section5.4 / P7 instruction. Only `agent.py` changes normal lateral
acceleration from7 to8m/s². The other13 archive members are copied byte for byte;
near-obstacle5, cap40, routing, perception, HUD, tracking and steering source
remain fixed. Both baseline endpoints are reused from138, with exact matching
reset observation/state/road/obstacle signatures before the candidate acts.

| Anonymous DEV | Cached134 time / damage | Fixed8 time / damage | Lap delta |
| --- | ---: | ---: | ---: |
| Contact-bearing A | 52.700s / 0.6 | 51.140s / 0.2 | −1.560s |
| Clean high-curvature B | 48.940s / 0.0 | 46.840s / 0.0 | −2.100s |

Both completions survive, with common lap sum reduced by3.660s, median paired
delta−1.830s and mean lap ratio0.963744. Damage is a separate diagnostic;
no damage or minimum-percent veto is added. These are newly measured results
for134; earlier91–93 policy comparisons are not used as validation.

Actual-call source arithmetic verifies normal8 and near5 on all1226 actions.
On the same recorded candidate inputs, target speed exceeds the normal7
counterfactual in642 rows and pedals differ in624 rows. Near5 changes are zero,
target-law error is zero, and actual float32 pedals exactly match the source.
The first changed action in each episode has identical input, path, HUD,
tracking and steering. Subsequent trajectories can differ. No policy replay
or extra model/environment call is made. No target=None rows occur; those rows
would be excluded from curvature-intervention counts.

The observer initially rejected8 because its readiness assertion expected7.
That pre-native attempt used0 wrapper actions and0 reset ticks. Its records
remain intact; only the observer's expected constant was manually corrected.
The completed comparison uses1226/4000 new native actions,52.920s wall,
43.425s evaluator CPU and9.687s actor CPU. The failed startup adds0.367s measured
wall; its actor startup CPU was unmeasured. Raw step ticks4902 and reset ticks102
are recorded separately. Cumulative native621842, research remaining16158,
final reserve84000 unused; budget remains722000.

After the connection alert, access to this same cloud and the saved report was
confirmed. Both workers were reaped and absent, with no live139 worker. The
completed evaluations are reused without duplicate execution or environment
switching. The next choice is the unchanged8 candidate on the remaining two138
DEV against cached134. That comparison is not started or reserved here.

HOLDOUT case details and SEALED stay closed; current134 and116 rollback remain
unchanged. Private conditions, frames, traces, plans and source documents stay
private. Official-server behavior is unverified. The56.54s prior constraint
exposure is not converted into recoverable time or a forecast.

[Aggregate evidence](lateral_budget_dev139_result.json) and
[fixed candidate construction](lateral_budget_candidate.py) provide the
result and reproducible one-parameter change.
