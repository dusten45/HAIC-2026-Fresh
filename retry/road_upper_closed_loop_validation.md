# Frozen upper-bound candidate: closed-loop DEV result

The road brightness upper bound change from `0.47` to `0.52` did not improve
completion or unique-tile progress on one previously observed DEV failure.
The candidate is closed for this test; it was not promoted and no independent
condition was run.

| Evaluator outcome | Original v2, historical | Frozen upper-only candidate, new |
| --- | ---: | ---: |
| Completion | False | False |
| Lap time | Unavailable | Unavailable |
| Native endpoint | `off_track` DNF | `off_track` DNF |
| Unique tiles / total | 97 / 279 | 97 / 279 |
| Progress | 34.767025% | 34.767025% |
| Damage | 0.2 | 0.2 |
| Wrapper actions | 306 | 307 |
| Collision-marked wrapper actions | 1 | 1 |
| First collision-marked action | 213 | 213 |

The historical baseline retained its complete action and pixel stream and an
observed native terminal. Its 28 execution-source hashes still matched. An
earlier full reproduction matched all 306 actions and 307 four-plane observation
hashes. The new run checked identical reset pixels, recorded body and wheel
state, road geometry, and physical obstacle geometry. It used the same seed and
condition in a private plan. This supports a paired local comparison; it does
not establish performance on an independent condition or an official server.

The fixed archive changed only the upper threshold in two road extraction
functions. Its lower threshold, controller, speed logic, memory, and other
members remained unchanged. A fresh, isolated CPU worker loaded all 14 policy
modules with matching member hashes. Its requests contained only the operation
and the four pixel planes. Observers made no extra policy calls or simulation
steps.

The first action difference was at action 24 on identical input pixels:
steering changed from approximately `-0.0089623` to `0`, with the same throttle.
The first differing subsequent input observation was at action 25. The
candidate then followed its own actual trajectory through its native endpoint;
the historical actions were not forced onto it. Matching contact indices and
damage do not establish an identical physical collision mechanism after that
divergence. One additional action before retirement is not improved progress.

The prospective plan allowed one candidate episode, at most 2,000 actions,
and at most 3,836 new actions overall. A ceiling without a native terminal would
have been reported as resource censored. Completion and lap time took priority;
for two native DNF results, unique-tile progress determined benefit. Damage,
contacts, and perception remained diagnostics. No improvement closes this
candidate on the tested condition. Improvement would only have authorized
designing an independent validation, without executing or promoting it.

Actual new cost was 307 wrapper actions, 1,228 raw step ticks, and 51 reset ticks.
The native episode took 11.385 seconds; measured wrapper-step wall time was
8.364 seconds, including observer recording, and actor CPU time was 1.906 seconds.
Maximum action latency including IPC was 14.381 milliseconds and peak actor
RSS was 63.668 MiB. The worker was reaped. All 307 actions and 308 grayscale
frames, reconstructing the four-plane stacks, passed receipt checks.
Research allowance remaining is 3,529 actions; the 84,000-action final reserve
was untouched.

The earlier offline gate failure and the separate adjacency-recovery rejection
remain recorded. This authorized native test adds evidence that the original
upper-only change did not rescue this DEV failure. It does not invalidate all
road-perception improvements or prove the curb-mask discrepancy caused a
physical hazard. HOLDOUT, SEALED, the champion, original sources, Participants,
and prior backups remained untouched. Raw data and private review records are
kept outside the public repository.

`retry/paired_closed_loop.py` provides the general harness. No rerun or automatic
extension is scheduled. Any future experiment needs a separate prospective
decision and remaining-budget check.
