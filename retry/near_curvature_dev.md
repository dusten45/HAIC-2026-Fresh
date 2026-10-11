The near-only curvature restoration completed a frozen, two-condition paired DEV probe. Both policies completed both conditions with zero damage. The candidate was slower in both: median paired lap increase **920 ms**, mean candidate/baseline lap ratio **1.016692**. The current cap40 policy and both rollback artifacts remain unchanged; this experiment did not permit promotion.

The baseline has no additive curvature offset. The single candidate restores the original `+0.003` denominator term only when the existing `near` predicate is true. Perception, tracking, target selection, steering, the predicate and its thresholds, speed cap, lateral acceleration, pedal gains and fallback behavior are unchanged. The archive builder changes two linked source members and checks byte equality of all other members.

Before drawing new conditions, four plain/observed configurations passed 4,740 saved DEV action calls. The observer returned exactly the same actions as the corresponding plain worker, baseline actions reproduced the saved sequence, and fixed-input steering and recorded tracking memory matched between policies. The saved DEV inputs showed pedal changes on 11.19%–12.54% of actions. Those replays established exposure and observer qualification, rather than native performance.

Two fresh DEV conditions were then registered against the available prior identity metadata, with paired AB/BA order and one execution per arm. Registration fixed a ceiling of 2,000 native actions per episode, 8,000 total native actions and 4,740 replay calls. Initial pixels, recorded state, geometry and obstacle identities matched within each pair. Normal DNF or declared censoring would continue collection; technical failure would stop without automatic retry. Cases and thresholds were not replaced or tuned after outcomes. Damage was a separate diagnostic. No incomplete-run time was treated as a completed lap.

| Endpoint | Baseline | Near-only restoration |
| --- | ---: | ---: |
| Completed conditions | 2/2 | 2/2 |
| Total damage | 0 | 0 |
| Collision-flagged actions | 0 | 0 |
| Conditions faster than baseline | — | 0/2 |
| Conditions slower than baseline | — | 2/2 |

The read-only observer computes both pedal formulas using each arm's own observed target, speed and actual steering. It calls the underlying policy and target controller once, without a shadow policy or model call. Candidate pedals differed from their nominal analytical shadow on **202/1,492 actions (13.54%)**, spanning **16.16 simulated seconds**. Per-condition fractions were 12.93%–14.07%, so neither triggered the preregistered below-1% low-exposure flag. That flag describes measurement sensitivity; it is not a safety or promotion threshold. At both first native divergences, the observed input, recorded controller/tracker memory and steering matched, and the restored term increased braking. Later trajectories were not matched by action index to infer intervention dose or decompose lap-time causation. Dwell measurements use the final crossing time, including correction for delayed finish confirmation.

| Measured cost | Value |
| --- | ---: |
| Native episodes / wrapper actions | 4 / 2,961 |
| Raw simulation ticks, step / reset | 11,838 / 204 |
| Native wall time including record writes | 118.257 s |
| Native actor / evaluator CPU | 18.520 / 98.867 s |
| Maximum observed action latency including IPC | 48.850 ms |
| Maximum actor RSS | 48,082,944 bytes |
| Qualification replay calls / wall time | 4,740 / 32.556 s |
| Native plus replay action calls | 7,701 |

The observer overhead is included in these measurements. Workers were reaped, with no automatic retries or additional paid resources. The native-action ledger has 11,747 research actions remaining and the 84,000-action reserve is untouched. Counting this experiment's replay calls one-for-one as an additional conservative charge leaves 7,007. Unused capacity does not start another experiment automatically.

These two conditions show a time cost with active intervention and no observed damage reduction. Since baseline damage was already zero, they have limited sensitivity to a safety benefit. This is a small DEV result on the same host, with no claim of generalization, safety, fresh-machine or official-server equivalence. Protected HOLDOUT details and SEALED remained closed. Seeds, road identities, full trajectories, archives and private source material stay outside the public repository. The machine-readable aggregate is [near_curvature_dev_result.json](near_curvature_dev_result.json).
