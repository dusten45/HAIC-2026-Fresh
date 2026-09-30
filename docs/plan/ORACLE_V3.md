# Oracle-v3 High-Speed Teacher

## Authorization and Scope

The 2026-09-30 user request authorizes a separate privileged oracle-v3 teacher
improvement experiment aiming at the reported leaderboard-leading lap times.
Read [COMMON.md](COMMON.md) first. Preserve oracle-v1/v2, supplied environment,
and submission Agent. No BC/RL training, submission, or model confirmation is
authorized by this task; other research plans retain their independent status.

## Roads, Timing, and Targets

All three configurations below are exposed development/evaluation roads, not
holdouts. Use unchanged physical obstacles, domain_randomize=False, frame skip 4,
50 no-op warmup ticks, raw TimeLimit 8200, and outer cap 2000 actions. Lap time is
round((finish_time_s - actual_post_reset_t) * 1000), not wall-clock runtime.

| Track | Geometry seed | Measured v2 pace (s) | User-reported team best (s) | User-reported leader best (s) |
| --- | --- | --- | --- | --- |
| 1 | 516237 | 46.200 | 18.520 | 11.940 |
| 2 | 644062 | 60.780 | 21.700 | 15.500 |
| 3 | 1007 | 54.440 | 20.300 | 13.920 |

V2 baseline: 3/3 complete episodes on 3/3 roads, one episode per road, no
collision/damage. Artifacts: runs/v2_pace_mock_t1_s516237_20260930,
runs/v2_pace_mock_t2_s644062_20260930, runs/v2_pace_mock_t3_s1007_20260930.
Leaderboard records are targets, not independently verified local matched
comparisons. The three seed mappings remain user-provided: public APIs do not
disclose deployed seeds or the environment revision attached to each record.

## Stages and Gates

1. Diagnose the v2 speed ceiling, acceleration/braking and steering behavior;
   verify timing conventions against accessible official sources. Measure rather
   than assume physical limits. Keep simulator instrumentation external.
2. Implement independent oracle/v3_controller.py and oracle/v3_runner.py. Change
   an evidenced control mechanism at a time, retaining source snapshots and full
   traces for complete episodes, including negative results.
3. Run matched full episodes on the three roads. Diagnose first divergence or
   collision before another targeted change; no blind parameter sweep. Favor
   complete-episode reliability over a single fast or damaged run.
4. Repeat a promising candidate on all three roads before calling it selected
   for these roads. Report finishes with episode/road denominators, damage,
   simulation laps and source fingerprints. Leader-level status requires actual
   completed local laps at or below all three targets, not extrapolation.

The first checkpoint need not reach the leader target. If it does not, record
the measured gap and an evidence-backed next experiment. Generalization outside
these exposed three roads and student imitability remain untested until a
separate gate; v3 never implicitly replaces the BC teacher.

## Current Checkpoint

**Frozen by user request at 2026-09-30 05:35 UTC.** Keep `V3Controller`,
`v3_runner` and their `responsive` defaults byte-unchanged. The previously
planned next mechanism below is now assigned to the separately authorized
[ORACLE_V4.md](ORACLE_V4.md), not an update to this teacher. No commit/tag or
official model confirmation is implied by this research freeze.

Frozen execution hashes, matching `runs/v3_selected_designated_repeat`:

- oracle/v3_controller.py: dd4f008e4279933209079eb220badab21d84fe404466387ca4fd027f76efea03
- oracle/v3_runner.py: 1f156e4c722de73e91ccae6bc4527e1f49cd18058744398ec9a363197cc76018
- oracle/v2_controller.py: 9e884d73980318894120105003a90524e889a32f67729616325a5caa32d40e3a
- oracle/oracle_controller.py: a447aa7559a9f2fdddfc65202c739dd1228dd607b8cc40aa9b8f9bb82a28d839

2026-09-30: first improvement checkpoint complete. `V3Controller` and its runner
default to `responsive`, selected only for these three exposed roads. The target
gate is **not met**; no generalization or submission-policy claim is made.

### Verified Timing and Physical Diagnosis

The official website's public `/api/ranking?trackId=1`, `=2`, and `=3` responses
at approximately 01:10:44 UTC verify leader times 11.940/15.500/13.920 seconds,
with 150/194/174 actions. The leader's per-track records use different
submissions (35 on tracks 1/2, 32 on track 3), not necessarily one model.
Official Participants main is `dfb7a2de2178825ca5c5ce20bab01ba67052ba31`,
environment `variables-6`; checked local physics, wrapper and finish code match
its Git blobs. Official README and local runner agree on the timing formula.
The approximately fourfold v2 gap is real in action counts too, not a units fix.

Sources: [official website](https://scholarships-hardwood-headers-influenced.trycloudflare.com/),
[track 1 ranking](https://scholarships-hardwood-headers-influenced.trycloudflare.com/api/ranking?trackId=1),
[track 2 ranking](https://scholarships-hardwood-headers-influenced.trycloudflare.com/api/ranking?trackId=2),
[track 3 ranking](https://scholarships-hardwood-headers-influenced.trycloudflare.com/api/ranking?trackId=3),
[official README](https://github.com/2026-HAIC/Participants/blob/dfb7a2de2178825ca5c5ce20bab01ba67052ba31/README.md).
If our team is team 4 (matching user-provided track 2/3 records), its current
public track-1 best is 17.140 rather than the supplied 18.520. This does not
change the leader targets; team identity was not inferred as a verified fact.

V2 reference lengths are 980.288/1182.808/1088.546 simulation length units;
leader targets require average reference speeds 82.101/76.310/78.200 units/s.
V2 explicitly caps speed at 30, lateral acceleration at 8, and braking at 5.
Installed Box2D maxTranslation=2 at 50 FPS implies a roughly 100-unit/s
per-body translational ceiling. Wheel bodies may reach it before the hull in
corners. Tire force limits imply an optimistic total lateral bound 219.12 and
steady rear-axle bound about 210.98 units/s^2, not safe operating guarantees.

Nominal straight rolling effective mass is 29.2498, including wheel spin
inertia; sustained full-gas acceleration is approximately
min(43.7736, 80000 / ((speed + 2.7) * 29.2498)). Non-locking brake deceleration
is about 303.8958 * brake action, corroborated by the saved v2 traces. These
are approximate actuator conversions, not a coupled tire/vehicle model.
Analytical engine-limited fixed-v2-path estimates at independent lateral/brake
limits 210.98 are 12.180/15.758/14.093s. They omit combined tire force,
throttle ramp, sampling and tracking transients: neither measured laps nor an
impossibility proof. A better line/control mechanism may still improve them.

### Matched Experiments

Each exploratory row is one full episode on each of the three roads. All use
the same v2 integrated reference line, obstacles, physics and timing. The v3
runner saves paired roads rather than their Cartesian product, full traces,
configurations, termination flags and execution source snapshots.

| Stage | Mechanism | Finishes / episodes / roads | Laps t1/t2/t3 (s) |
| --- | --- | --- | --- |
| envelope | cap 95, lateral 80, brake 60; full-loop braking envelope, one-action reaction margin; v2 feedback/steer | 3/3/3 | 17.000 / 22.500 / 20.040 |
| drive | same envelope, physical acceleration-to-gas/brake conversion | 3/3/3 | 16.620 / 21.920 / 19.560 |
| grip | lateral 160, brake 120; same path/steer/actuator policy | 3/3/3 | 13.680 / 17.920 / 15.940 |
| responsive | same grip envelope; remove lookahead slew bottleneck | 3/3/3 | 13.680 / 17.920 / 15.940 |
| limit, rejected | same responsive controller; lateral 190 | 1/3/3 | failed / failed / 15.440 |
| steer_limit, not selected | limit stage plus commanded-curvature speed constraint at lateral 160 | 3/3/3 | 13.820 / 17.940 / 16.020 |

Artifacts: `runs/v3_<stage>_designated_first` for all six rows. All completed
exploratory episodes have zero collision/damage. Failed episodes also remain
saved; `limit` retires off_track at actions 139/203 on tracks 1/2. Do not rank
its survivor-only mean above reliable stages. Exploratory totals: 16/18
finishes on three repeatedly exposed roads, not 18 independent roads.

Envelope-stage mean desired-minus-actual speed is 13.35/13.76/13.10 units/s.
Physical actuator conversion improves laps, but substantial target-tracking
gaps remain at high grip; this is not yet acceleration-feedforward planning.
Responsive preview changes no rounded lap time versus grip, but reduces
track-2/3 maximum reference error from 2.689/2.053 to 1.944/1.563 units
(27.7%/23.9%). Track-1 maximum error changes 1.371 -> 1.379. All wheels remain
on-road at recorded boundaries for these successful exploratory stages.

Rejected limit stage: track 1 first lateral velocity magnitude >5 occurs at
action 28 (arc83.96, speed73.26, right_velocity7.13), before reference error
exceeds 4 at action31 and partial wheel departure at action32. Track 2's first
partial wheel departure at70 temporarily recovers; lateral velocity magnitude
exceeds5 at76 (arc371.52, speed73.30, right_velocity-5.64), before error>4 at80.
Last newly visited tiles are at38/102, followed by the wrapper's 101-negative-
reward-action retirement rule. Tire saturation plus corrective yaw oscillation
is a hypothesis consistent with these traces, not an isolated causal proof.
Commanded-curvature limiting restores 3/3 finishes but is slower and does not
improve aggregate tracking versus responsive; preserve it as a negative tradeoff.

### Fixed-Source Repetition

After fixing defaults, `runs/v3_selected_designated_repeat` contains **6/6 full
episodes finished on 3/3 roads**, two runs per road, zero collision/damage.
Each road's two full JSONL traces are byte-identical. All recorded source
hashes match final executable files; actual geometry, obstacles and reference
points match the v2 baseline on every road. The earlier responsive exploratory
run has the same behavior but a different source version; it is not added to
the final-source 6-episode denominator.

| Track / seed | Selected v3 (s), both repeats | Reduction vs v2 | Gap vs leader target |
| --- | --- | --- | --- |
| 1 / 516237 | 13.680 | 70.390% | +1.740s / +14.573% |
| 2 / 644062 | 17.920 | 70.517% | +2.420s / +15.613% |
| 3 / 1007 | 15.940 | 70.720% | +2.020s / +14.511% |

Reproduce with a fresh output path:

```bash
python -m oracle.v3_runner --stage responsive --repeats 2 --output runs/v3_reproduction
python -m oracle.v3_runner --stage limit --road 1 516237 --output runs/v3_failure_reproduction
python -m pytest -q tests/test_v3_controller.py tests/test_v3_runner.py tests/test_v2_controller.py tests/test_oracle_controller.py tests/test_local_contract.py
```

Validation: 39 tests and 15 subtests pass. V1/official environment/Agent/runner
are unchanged against oracle-v1; v2 controller/runner are unchanged against
the task's HEAD. No commit, push, official submission, model confirmation, BC
training or image trajectory collection occurred.

### Next Gate

Do not just raise the lateral cap again. The next bounded experiment should
retain the selected line and envelope, add tire-budget-aware forward engine /
backward braking reachability and acceleration feedforward, and compare all
three full episodes. Then diagnose slip/entry steering transients before any
steering feedforward or lap-time-aware path optimization. These mechanisms
remain **planned, not implemented or evaluated** at this checkpoint. Repetition
on these deterministic exposed roads establishes repeatability only, not unseen
road robustness or student imitability. The v3 target gate remains open.
