# Frozen student's low- and high-stratum DEV preservation checks

The unchanged grayscale road-keep student preserved completion without damage on
both selected DEV strata. Both common completion times were slower than the
original v2 policy's historical runs. Together with the two earlier other-geometry
checks, these results justify designing wider paired evaluation, while leaving
the champion unchanged.

| Known DEV stratum | Original v2, historical | Frozen student, new | Common completion delta |
|---|---|---|---|
| Low | 62.360 s, 270/270, damage 0 | **64.680 s, 270/270, damage 0** | +2.320 s |
| High | 79.960 s, 315/315, damage 0 | **80.560 s, 315/315, damage 0** | +0.600 s |

Each condition was executed once, in the prospectively fixed order low then high.
The user selected different strata among known baseline successes before these
two student outcomes were available. This is a conditional DEV preservation
check, not a random sample or independent HOLDOUT. No new roads or replacements
were drawn, and no student performance filtering selected these cases.

## Contract and data qualification

All 21 historical source guards matched the current files, including the native
evaluator, wrapper, damage logic, car physics and pixel protocol. The original v2
archive and all inherited policy module hashes matched. The actual historical
ledger recorded 780 actions for the low case and 1,000 for the high case, with
the complete outcomes shown above. Historical baseline runs were reused; no
baseline was rerun or described as a new validation.

Private scene, initial-state, physical-obstacle and geometry receipts matched.
Both road geometries differ from the student's training/validation geometry and
from each other. All training cache guards were verified. After execution, all
1,817 pre-action inputs were compared with the 833 training and 40 retained
validation observations: **zero exact four-plane or latest-frame duplicates**.
This is an exact duplication audit, not a statistical independence claim.

The model, features, original brightness thresholds, controller and postprocessing
were frozen. The runtime recorder, native evaluator and isolated worker were
unchanged from the preceding two-case check. The worker receives official
`float32(4,84,84)` grayscale only, with no RGB, GT, environment state, seed, action
index, world coordinates or trajectory lookup. The raw mask remains
`P47 & frozen_student_keep`; inherited cropping and morphology follow it.
No learning, teacher-mask queries or diagnostic renderer calls occurred.

The native environment's 8,200-raw-tick horizon was retained. Each case had a
2,000-wrapper-action resource ceiling, with a shared ceiling of 4,000, inside the
4,245 available research actions. A resource endpoint would have been labelled
censored. Both episodes reached native completion, so neither was shortened for
comparison. Ordinary policy failure would still allow the second case; only
implementation/input qualification issues or hard resource boundaries could
leave it unexecuted.

## Saved evidence and cost

All **1,817 actions, 1,819 frames and 1,819 masks** passed observation/action/mask
hash alignment, action-to-worker-response, binary-subset, component-call,
state-continuity and native endpoint checks. Added raw mask cells were **zero**.
Both runs had no contacts, registered progress-stagnation events or fallback
calls. Immutable deployed assets matched their sources and both workers were
reaped. Full traces and reconstructible observations remain private.

The new general `road_keep_saved_records.py` verifier reads JSON and NumPy
records without importing policies or simulators. Its regression check on the
preceding two saved episodes matched their verified actions, masks, deletion
fractions and contacts. A private analysis launch initially missed the repository
import path; running the unchanged analysis from the repository corrected it.
This required no new episode, policy call, model prediction or budget retry.

| Measurement | Low | High |
|---|---:|---:|
| Wrapper actions | 809 | 1,008 |
| Native step ticks, excluding reset | 3,236 | 4,030 |
| Episode wall time | 30.300 s | 41.278 s |
| Median student inference | 1.361 ms | 1.364 ms |
| Maximum student inference | 5.550 ms | 5.739 ms |
| Maximum action including IPC | 48.171 ms | 24.358 ms |
| Peak worker RSS | 63.11 MiB | 95.25 MiB |

The preceding check measured 62.893 seconds for 1,619 actions with this same
recorder and worker. Before execution, linear extrapolation predicted **155.388
seconds** for the 4,000-action ceiling, or 69.148 seconds at the historical
baseline's 1,780-action count. A 25% execution contingency and separate delivery
and verification time were included in a 15-minute work estimate.

The new episodes totaled **71.578 seconds**. Scaling the prior measurement to
the actual 1,817 actions predicts 70.585 seconds, so measured cost was **1.41%
higher**. The simulator-plus-recording interval was 1.213 seconds higher, while
actor CPU was approximately unchanged. Geometry and scheduling costs were not
separately benchmarked. Saved-record verification took 2.132 seconds and the
earlier verifier regression check took 0.900 seconds.

The operating cap remains **630,000**. Cumulative use is **543,572**, research
remaining **2,428**, and final reserve **84,000**, with no reserve use or budget
increase. No additional paid or off-cloud compute was used.

## Wider paired evaluation judgment

Across four selected other geometries, the frozen student completed all four;
the original historical baseline completed three and crashed on one. The training
geometry success is recorded separately. The three common completions were all
slower for the student: the earlier control by **1.500 seconds**, and the new
low/high cases by **2.320/0.600 seconds**. The recovered crash case also retained
damage 0.2. These regressions remain part of the evidence.

The earlier control's slowdown has no confirmed section-level cause: its original
full observation/action trace was not saved. Feature/deletion statistics cannot
establish that cause, and teacher imitation error on new states remains unmeasured.
The new deletion fractions were 2.682% and 2.873%; aggregate feature-mean shifts
were at most 0.248 and 0.377 training-frame standard deviations, descriptively.

The completion and input-boundary evidence is sufficient to design broader paired
tests of completion preservation, damage and common completion time. It is not
evidence for champion promotion or speed superiority. Future paired action costs
must fit the remaining research budget before execution; no broader run or
automatic budget increase occurred here. HOLDOUT and SEALED were unused, original
competition training eligibility remains unverified, and the project continues.
Learned weights, raw observations, private case identities and provenance were
not published.
