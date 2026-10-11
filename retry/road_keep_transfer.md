# Frozen grayscale student on two other DEV geometries

The fixed road-keep student completed both selected DEV conditions on geometries
absent from its training and validation caches. The transfer condition previously
ended in a crash for the original policy. The preservation control still completed
without damage, but took 1.50 seconds longer than the original policy's historical
run. These two selected, already known DEV conditions do not justify promotion.

| Condition | Original v2, historical | GT diagnostic, historical | Frozen student, new |
|---|---|---|---|
| Transfer | Crash, 140/312 tiles, damage 1.0 | Visible GT: 77.280 s, 312/312, damage 0 | **69.820 s, 312/312, damage 0.2** |
| Preservation control | 58.060 s, 271/271, damage 0 | Full-road GT: 56.200 s, 271/271, damage 0 | **59.560 s, 271/271, damage 0** |

The earlier full-road GT result on the transfer condition was 77.020 seconds with
zero damage. Full-road and visible GT are different privileged interventions.
The student also previously completed its training geometry in 66.480 seconds
with damage 0.8; that result is separate from the two new geometry checks.
All original and GT outcomes above are reused historical comparisons, not new
baseline validations. No baseline or GT episode was rerun.

## Frozen candidate and prospective gates

The model, feature implementation, two original brightness thresholds, controller,
obstacle tracking, speed estimation and mask postprocessing were unchanged.
The model and deployed assets remained read-only, and all inherited package
module hashes matched their frozen archive. No fitting or tuning occurred.
The worker receives only official `float32(4,84,84)` grayscale observations.
The same learned tree predicts keep/delete for existing raw road-mask cells;
the intervention remains `P47 & predicted_keep` before inherited postprocessing.
RGB, GT, environment state, seed, action index, world coordinates and trajectory
lookups are absent from the worker input.

Before execution, private provenance and geometry hashes confirmed that both
conditions differ from the training geometry and from each other. The conditions
are selected known DEV cases, not independent HOLDOUT evidence. The order was
fixed as transfer then preservation. Each received a ceiling of 2,000 wrapper
actions, with a shared ceiling of 4,000. The native environment's horizon was
unchanged; reaching a resource ceiling would be reported as censored. Both runs
actually reached native completion, so neither comparison is shortened.

Model/source/initial-state/geometry qualification failures would stop the remaining
execution without a repaired retry. Ordinary native failure would still allow the
second frozen candidate episode. No champion promotion, HOLDOUT/SEALED calls,
automatic extension or reserve borrowing was permitted.

## Records and behavior

The new recorder preserves every action, reconstructible four-plane observation,
mask and receipt. It uses the existing native evaluator and unchanged isolated
student worker. Historical initial observation/state, geometry and physical
obstacle receipts matched. Historical full action streams are unavailable, so
this check does not claim a full baseline reproduction or an exact first action
divergence against the old runs.

All **1,619 actions, 1,621 frames and 1,621 masks** passed saved-record alignment,
hash, binary-mask and component-call checks. Every raw student mask was a subset
of its original mask: **zero added cells**. There were no extra policy calls,
teacher-mask calls or diagnostic renderer calls. Both workers were reaped.

The transfer run's sole contact occurred at action **376**, at 139 visited tiles,
raising damage to 0.2. Its complete pre/post event window was saved, and it went
on to finish. The control had no contacts. Neither run triggered the registered
25-action progress-stagnation event or the fallback controller.

Deletion fractions on original road-mask cells were **2.881%** and **2.643%**,
compared with 2.767% for student predictions on its training trajectory. The
largest aggregate mean-feature shifts were 0.302 and 0.311 training-frame standard
deviations. Local shifts were larger: the transfer contact window reached 1.293.
These are descriptive distribution measurements, not teacher imitation error.
Aligned teacher labels on the new visited states were not collected. Both runs
completed, while residual contact and control slowdown remain unresolved.

## Measured cost and budget

The operating budget was explicitly increased before execution from 626,000 to
630,000 actions. With cumulative use of 540,136 and the 84,000-action final reserve
unchanged, available research actions became 5,864. The prior 832-action student
run took 29.857 seconds; linear extrapolation gave 143.54 seconds for the full
4,000-action ceiling. A 25% recording contingency and separate verification and
delivery time were included in a 15-minute overall work estimate.

| Measurement | Transfer | Preservation control |
|---|---:|---:|
| Wrapper actions | 874 | 745 |
| Native step ticks, excluding reset | 3,493 | 2,980 |
| Episode wall time | 33.030 s | 29.863 s |
| Median student inference | 1.359 ms | 1.407 ms |
| Maximum student inference | 8.944 ms | 32.904 ms |
| Maximum action including IPC | 21.829 ms | 47.574 ms |
| Peak worker RSS | 57.11 MiB | 102.25 MiB |

Native execution totaled **62.893 seconds**. At the actual 1,619-action count,
the prior measurement predicted 58.099 seconds: actual cost was 8.25% higher.
The measured simulator-plus-recording interval accounts for approximately 4.10
seconds of the 4.79-second increase; actor CPU increased by approximately 0.46
seconds. Geometry, scheduling and recorder differences were not separately
benchmarked. The lower total than the full-ceiling estimate is explained by
native completion after fewer actions. Saved-record verification took 1.32 seconds.

Cumulative use is now **541,755**, research remaining **4,245**, and final reserve
**84,000**, with none of that reserve used. No additional paid or off-cloud compute
was used. Learned weights, raw observations, traces, private case identities and
provenance remain private; this document contains aggregate results only.

## Interpretation

The student transferred completion to one other geometry where the original
policy had crashed, and preserved completion on another. It does not uniformly
dominate the historical comparisons: transfer damage exceeds the GT diagnostics,
and the preservation control is slower than v2. Training eligibility under the
original competition rules is still unverified, and the champion is unchanged.
The next focused question is where the preservation control's 1.50-second loss
arises in its route and speed behavior. No follow-up experiment was run here.
