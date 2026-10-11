The completely frozen Stage116 pedal-feedback candidate passed the registered completion/time comparison on two new DEV conditions, with a **damage warning**. Both policies completed both conditions. Median paired lap change was **−4.350 s**, but candidate damage increased by **0.6** in one condition. The current Stage113 champion and both rollback archives remain unchanged; this comparison did not permit promotion.

The candidate archive was reused byte-for-byte. Against the current champion, two source members differ and one fixed 65-entry decoder module is added; the other eleven members are identical. Only gas/brake feedback receives the new speed scalar. Perception/tracking, the near predicate, lookahead, path/target selection and steering retain the original speed input. The 40 m/s cap, gains, curvature treatment, ROI and exact-match/fallback rules stayed fixed. Closed-loop trajectories can differ after the pedals diverge.

Before any outcome, two conditions were registered in AB/BA order. Their seeds, road geometries, obstacle specifications, physical obstacle fingerprints and RNG lineages were distinct from the recorded exclusion metadata and each other. The registry covered 190 prior road geometries and 192 conservative seed/generator identities, plus available obstacle fingerprints and parent families. No identity collision, redraw, difficulty filter or performance ranking occurred. Historical missing obstacle fingerprints remain a coverage limit; novelty is not proof of broad difficulty coverage. Selection called only the source road/obstacle functions and used no environment, physics, policy or renderer.

Existing same-host qualification was reused after exact archive, configuration, worker, source and runtime checks. There were zero new saved-policy calls. Eight mock scenarios checked normal DNF/censor continuation, technical stops, readiness/order/lineage/configuration rejection and one-use execution. A source-bound plan fixed four runs at at most 2,000 actions each, 8,000 total. It preserved the 84,000-action reserve and allowed no retries, replacement conditions or tuning after outcomes. Actual paired reset geometry, obstacles, physical state and pixels matched before actions. Protected HOLDOUT details and SEALED data stayed closed.

| Outcome | Aggregate observation |
| --- | --- |
| Completed, baseline / candidate | 2/2 / 2/2 |
| Lost completion / censor / inconclusive | 0 / 0 / 0 |
| Mean actual lap, baseline / candidate | 50.120 s / 45.770 s |
| Median paired lap change | −4.350 s |
| Range of paired lap changes | −5.620 to −3.080 s |
| Mean candidate/baseline lap ratio | 0.914299 |
| Observed damage sum, baseline / candidate | 0 / 0.6 |

Independent saved-record review confirmed the endpoints, actual finish-clipped times, AB/BA order, stream hashes and worker cleanup. Before the first action branch in each pair, pixels, physical state and prior actions were identical; steering was also identical at that branch. All 1,146 candidate observations matched the frozen HUD table, with no fallback. Candidate speed MAE was 0.608–0.614 m/s on its own trajectories, compared with about 2.246 m/s for the old reader on those same observations. That sensor improvement is a separate measurement from completion, lap time and damage.

The damage warning consists of three consecutive wrapper records, each adding 0.2 and reporting collision. The candidate subsequently completed. These rows do not establish three independent physical crashes, and the damage mechanism has not been isolated. Targets and internal controller memory were not logged for every clean-worker call, so no full-run intervention rate or same-step cross-arm causal explanation is claimed. Damage was a diagnostic warning under the registered rule; it was not used as a new veto or as evidence of safety.

The historical comparison matters. **Stage15 already used the same core HUD region for pedal feedback alone**. Its 25-level intensity/interpolation decoder looked favorable on selected DEV; Stage16 then lost a baseline completion on fresh DEV and was rejected under its own contract. Stage101 later improved saved-observation speed-error criteria but failed its target-relative false-acceleration criterion, so the following native test was not opened. Those historical outcomes remain intact. This candidate differs in its exact 18-byte, 65-signature source-raster representation and fallback, and operates under the current cap40/removed-offset controller context. The intervention channel is shared. A bin midpoint can cross a target boundary even while absolute speed error shrinks; the two Stage116 gains and these two new DEV gains do not resolve that risk.

| Measured work | Calls | Wall seconds | Policy CPU seconds | Evaluator CPU seconds |
| --- | ---: | ---: | ---: | ---: |
| Registered native comparison | 2,400 wrapper steps | 97.568 | 14.924 | 82.850 |
| New saved-policy inference | 0 | 0 | 0 | 0 |

Native work used 9,593 raw 20 ms step ticks and 204 reset ticks, four cold starts and four policy resets. The reported wall includes record writing. Nested environment-step and reset timers were 74.583 s and 1.619 s; these are already inside the native span. Separately retained source/identity/mock/analysis blocks sum to **2.933 s of measured work spans and 3.224 CPU seconds**. Those are partial timers, some from parallel work, and exclude unmetered reading, communication, reasoning, report/git work and startup outside the timers. They are not whole-stage elapsed time. Prior qualification calls were reused without charging them again.

Preflight verified that the worst registered 8,000 native actions fit the 10,440 research balance, leaving 2,440 if fully consumed. The actual charge was 2,400. The updated allocation is **589,960 used + 8,040 research remaining + 84,000 reserved = 682,000**. B and reserve usage did not change. Offline inference is tracked in its own call, wall and CPU units rather than subtracted one-for-one from native actions.

Latest measured serial throughput is **24.598 native actions/s**. Conditional costs for future work are:

| Possible next work, not executed | Native allocation | Estimated wall |
| --- | ---: | ---: |
| Replay all existing Stage117 streams once | 0; 2,400 offline policy calls | 18.92 s |
| One new pair at its 4,000-action cap | 4,000 | 162.61 s |
| Two new pairs at their 8,000-action cap | 8,000 | 325.23 s |
| Preserved final-validation reserve | 84,000 | 56.91 min |

The replay estimate uses the measured Stage116 offline rate and excludes observer implementation, qualification and analysis. Its estimated policy/evaluator CPU costs are 14.27/4.90 s. Native estimates use the actual Stage117 rate without a parallel multiplier; they are not runtime guarantees. Another maximum 8,000-action packet would leave only 40 research actions. Any next experiment therefore needs a concrete question and its own preflight allocation; no further packet has been opened.

The designated cloud has a four-core CPU quota and 16 GiB memory. About 115.36 authorized hours remained at the post-run cost review; these hours do not guarantee compute availability. The authorization ends **2026-10-16T10:01:55Z (19:01:55 KST)** without extension. Existing-record damage diagnosis is the next question before choosing more native validation. Broad generalization, safety, official-server parity and fresh-machine parity remain unverified.

The [aggregate JSON](hud_feedback_generalization_result.json) and guarded [runner](hud_feedback_generalization.py) preserve the result and cost semantics. Seeds, condition identities, full recordings, private documents and ZIP archives remain outside the repository. The runner requires matching frozen private plan/readiness/qualification receipts; the published aggregate is not an executable plan.
