# Oracle-v4 Coupled-Grip Teacher

## Authorization and Frozen Reference

The 2026-09-30 05:35 UTC user request freezes oracle-v3 and authorizes its planned
improvements under the separate name oracle-v4. Read [COMMON.md](COMMON.md) and
the frozen [ORACLE_V3.md](ORACLE_V3.md) checkpoint. Preserve v1/v2/v3 executable
files, supplied environment, Agent, and unrelated BC work. No BC/RL training,
submission or model confirmation is authorized here. No commit/tag is implied.

V3 controller/runner and dependency hashes match the final v3 source snapshot;
their frozen hashes are recorded in ORACLE_V3.md. Baseline artifact:
`runs/v3_selected_designated_repeat`, 6/6 episodes on three exposed roads, two
identical trace repetitions each, zero collision/damage. These are not holdouts.

| Track | Geometry seed | Frozen v3 (s) | Leader target (s) |
| --- | --- | --- | --- |
| 1 | 516237 | 13.680 | 11.940 |
| 2 | 644062 | 17.920 | 15.500 |
| 3 | 1007 | 15.940 | 13.920 |

Timing/conditions remain frame skip4, 50 raw-frame warmup, physical obstacles,
domain_randomize=False, TimeLimit8200 and cap2000 actions. Lap is finish-center
simulation time minus actual post-reset time, rounded to milliseconds. Public
leader times were verified during v3; deployed seed/revision matching remains
conditional on the user-provided configurations. This is local teacher research.

## Mechanisms and Gates

1. Retain v3's integrated reference line, responsive pursuit and initial scalar
   envelope (straight95, lateral160, brake120). Implement a coupled lateral /
   longitudinal grip approximation, backward braking reachability and forward
   engine-limited acceleration. Handle standing launch without imposing an
   artificial zero-speed finish boundary. Record actual config and planned arrays.
2. Compare profile feedback alone against frozen v3 on all three full episodes.
   Then add acceleration feedforward with the same profile, path and steering,
   so its effect can be isolated. Diagnose first departures, not just retirement.
3. Keep every complete failure/negative stage and source snapshot. Any correction
   must follow observed timing/tracking/actuator evidence, not a parameter sweep.
   Do not increase scalar grip caps before understanding coupled-control results.
4. Repeat a promising v4 candidate on all three roads with fixed source before
   selecting it. Report episode and road denominators separately, collision /
   damage, matched lap deltas and repeat trace hashes. If no candidate improves
   reliability/pace, preserve v3 as preferred reference and label v4 experimental.

Initial model approximations are not measured physical feasibility guarantees.
After this longitudinal gate, steering transients or lap-time-aware path
optimization need their own evidence-backed comparison; they are not implicitly
stacked in the initial v4 implementation. No wider-road or student-transfer claim.

## Current Checkpoint

First longitudinal checkpoint complete. V3 remains frozen, including both
executable hashes. New `oracle/v4_controller.py` and `oracle/v4_runner.py`
default to `midpoint`, selected locally on these three exposed roads only.
The measured pace gain is small; leader targets remain unmet. No wider-road,
official submission or student-transfer claim is made.

### Implemented Model

V4 reuses v3's integrated reference points and responsive pursuit without
editing the inherited code. The straight/lateral/braking operating caps remain
95/160/120. At squared speed w and interval curvature K, the nominal model uses
physical rear lateral bound210.98, residual R=sqrt(max(0,1-(K*w/210.98)^2)),
acceleration min(43.7736*R,80000/(29.2498*(sqrt(w)+2.7))), and braking
min(120,210.98*R). The acceleration bound accounts for passive front-wheel spin:
rear longitudinal force per wheel is approximately9.137928*a, not M*a/4.
These are rolling/axle approximations, not measured per-wheel force guarantees.

Cyclic forward/backward sweeps enforce the sampled acceleration/braking
inequalities using maximum absolute curvature at each interval's endpoints.
Backward braking uses the corresponding analytic friction-circle root;
forward engine/traction reachability uses scalar bisection. A separate launch
profile starts from measured reset velocity and rejoins the cyclic caps; the
finish endpoint is not constrained to zero. The final-source profile satisfies
all saved-road forward/braking inequalities within1e-8 squared-speed units.

Feedforward averages planned speed change over0.08s across however many
2.5-unit nodes the action crosses. Feedback uses the current-position profile
speed, not the future feedforward endpoint. Both compared stages have the same
one-interval initial reference bootstrap, needed for feedback-only departure
from exactly zero speed. Runtime grip uses the greater of reference lateral
demand and abs(speed*yaw_rate); wheel-force transients remain approximate.

Selected midpoint keeps v3's 3+0.08v early-braking guard at action time rather
than pre-shifting the entire profile. Positive desired acceleration is converted
to gas with predicted midpoint speed v+0.04*a; braking conversion remains
unchanged. No path rewrite, steering feedforward, scalar cap increase or physics
modification was made. Launch/time/profile arrays and full traces are retained.

### Matched Full-Episode Stages

Every exploratory row below is three full episodes on the same three roads,
one per road. Each finished3/3 on3/3 roads without collision/damage; all recorded
post-action states have four wheels on-road. Source snapshots retain each
version. Artifacts: `runs/v4_<stage>_designated_first`.

| Stage | Mechanism | Track1 / track2 / track3 laps (s) | Decision |
| --- | --- | --- | --- |
| profile | coupled reachable profile, pre-buffered braking, feedback only | 14.040 / 18.480 / 16.440 | slower than v3 |
| feedforward | same buffered profile plus interval-averaged feedforward | 13.920 / 18.460 / 16.340 | improves profile stage, still slower than v3 |
| guarded | same coupled model/feedforward, v3 braking guard at runtime instead of pre-buffered profile | 13.760 / 18.060 / 16.040 | better, still slightly slower than v3 |
| midpoint | same guarded plan/control, midpoint-speed gas inverse only | 13.620 / 17.900 / 15.940 | current candidate |

The first two stages have identical saved speed/launch profiles. Feedforward
reduces target-error RMS from4.727/5.491/5.221 to1.559/1.356/1.392 units/s,
but buffered ideal profile times13.543/17.960/15.884s are already too cautious
to produce meaningful improvement over v3. Better target tracking alone is not
evidence of faster laps. Moving the guard to action time reduces measured laps
on all three roads without changing the scalar caps or introducing failures.

Guarded stage's first action on each road commands43.774 but measures29.442
units/s^2. Fourteen eligible low-speed, low-sideslip, unsaturated-gas samples per
road have mean commanded-minus-measured acceleration7.318. This motivates the
isolated midpoint inverse correction: first measured acceleration42.532 with
the same43.774 command. Laps improve by0.140/0.160/0.100s versus guarded.
Reference error RMS becomes1.729/1.820/1.838, with reference path error RMS /
max0.564/1.353,0.608/1.593,0.548/1.449 units. Tracking is not uniformly better
than every prior stage; do not present midpoint as an optimal controller.

Before final repetitions, corrected numerical bisection handling to retain an
already-feasible upper bound rather than repeatedly reducing it by rounding.
Saved earlier profiles had maximum forward residual about0.00113 squared-speed
units; final sampled constraints are satisfied. Earlier exploratory snapshots
remain unchanged. Defaults were then fixed to midpoint; the final-source
denominator below excludes all earlier experimental source versions.

### Fixed-Source Repetition and Preservation

`runs/v4_selected_designated_repeat`: **6/6 full episodes on3/3 roads**, two
per road, zero collision/damage. Repeated full traces are byte-identical on all
three roads. Recorded executable source hashes match current files. Actual
track geometry, obstacles and reference points exactly match frozen v3.

| Track / seed | V3 (s) | V4 (s), both repeats | V4 minus v3 | Leader target gap |
| --- | --- | --- | --- | --- |
| 1 / 516237 | 13.680 | 13.620 | -0.060s | +1.680s |
| 2 / 644062 | 17.920 | 17.900 | -0.020s | +2.400s |
| 3 / 1007 | 15.940 | 15.940 | unchanged | +2.020s |

Mean lap15.820s versus v3's15.846667s: reduction0.026667s (about0.168%).
This is a small deterministic matched gain, not replicated unseen-road evidence.
Exploratory total12/12 on three repeatedly exposed roads is separate from the
final-source6/6 denominator. Leader target gate is not met.

V3 controller/runner hashes and inherited v2/v1 hashes still match frozen v3's
source snapshot. V1/original environment/Agent/runner/requirements are unchanged
against oracle-v1; v2 controller/runner remain unchanged against task HEAD.
54 focused tests and35 subtests pass, including freeze hashes, paired-road
runner/timing, coupled reachability, interval-averaged feedforward, midpoint
conversion and runtime yaw budgeting. No commit/tag/push, submission,
confirmation, BC training or image dataset collection occurred.

Reproduction with fresh output paths:

```bash
python -m oracle.v4_runner --stage midpoint --repeats 2 --output runs/v4_reproduction
python -m oracle.v4_runner --stage profile --output runs/v4_profile_reproduction
python -m oracle.v4_runner --stage feedforward --output runs/v4_feedforward_reproduction
python -m pytest -q tests/test_v4_controller.py tests/test_v4_runner.py tests/test_v3_controller.py tests/test_v3_runner.py tests/test_v2_controller.py tests/test_oracle_controller.py tests/test_local_contract.py
```

### Next Gate

Do not claim the longitudinal change closes the leader gap. Retain midpoint as
the current v4 reference and frozen v3 as the comparison. Next diagnose where
projected progress rate, heading/yaw transients and throttle ramp still account
for the remaining1.68/2.40/2.02s, then isolate a steering-preview/feedforward
mechanism before any line change. Keep scalar caps fixed for that comparison.
Steering improvement and lap-time-aware line optimization remain **planned,
not implemented or evaluated** here. Any later selection needs matched complete
episodes and fixed-source repetition again; no holdout or BC-teacher replacement
is implied by this checkpoint.
