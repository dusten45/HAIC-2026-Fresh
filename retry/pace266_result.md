# 266: Separate speed-lag mechanisms; positive acceleration clamp removal rejected

Local source evidence confirms unused possible acceleration in one aligned regime. Removing that limit globally at the fixed1.5 pace loses both completions through tire/steering coupling. The candidate is rejected; no second control formula or higher pace is run.

| DEV road | Reused265 pace1.5 | Single positive-clamp removal266 |
|---|---|---|
| O0 |19.70s complete,damage0 |off_track182,damage0;119/326 tiles |
| N0 |20.20s complete,damage0 |off_track191,damage0.4;119/325 tiles |

O0 first path error>3m at80(5.58m), first grass-wheel contact81, no collision. N0 first error82(3.88m), grass84, first collision88. Both are actual source retirements, censored0. `off_track` follows lack of progress; it is not itself a geometric wheel-contact test. Recorded grass fractions establish actual departure after the earlier tracking error.

## Distinct causes in the existing1.5 reference

Use265 trajectories directly; a diagnostic lag label is target minus actual>10m/s. This label selects observations and never controls the candidate.

| Reference | Large-lag actions | Positive35.02 clamp | Clamp +gas<1 +rear not clipped | Gas1 | Braking while below target |
|---|---:|---:|---:|---:|---:|
| O0 |207 |153 |105 |32 |47 |
| N0 |232 |166 |130 |28 |55 |

These conditions overlap and are not a partition. No baseline action commands gas and brake simultaneously. Source checks separate:

- **Controller allowance:** positive acceleration is capped at35.01888, derived from a chosen0.8 rear traction fraction. It is not a physical maximum. Many lag states leave gas below1 and the rear tire vector below saturation.
- **Engine/action ceiling:** at N0 actions165–166 gas is already1. The matched source first eight physics ticks have front axle−332.54N and rear+548.93N, no clipping. Speed rises85.64→90.39m/s over0.16s. Maximum gas plus finite source engine power/wheel response limits further acceleration there; raising a scalar request changes no action.
- **Spatial braking model:** N0 action54 has actual94.04m/s, target140.42, feedforward−160.19 and feedback+69.58m/s², giving−90.60 and brake0.298. Action167 has feedforward−205.13 plus69.80, clipped to−91.17/brake0.3. The profile is dropping ahead along the route; braking below the instantaneous target is not by itself a bug. The stressed spatial gradient exceeds the original approximate envelope. Matched brake probes apply negative forces on both axles with no tire clipping and slow strongly.
- **Coupled tire/steering limit:** source clips the combined longitudinal/lateral force vector. Unsaturated tires on a straight do not imply full engine demand remains available during turning. This becomes decisive in the actual changed controller.
- **Numerical solver ceiling:** O0 recorded actions57–64 are approximately100m/s with gas1; N0 never reaches that plateau. This is distinct from a friction or engine limit. Native C++ branch counts were not instrumented; plateau, installed settings/source and the265 one-tick probe support this interpretation.

## Matching version and source time units

Installed distribution and module are both `box2d-py2.3.5`; native extension hash is recorded. The exact [2.3.5 source release](https://pypi.org/project/box2d-py/2.3.5/#files) was downloaded as data and its published SHA-256 verified(`b37dc388…0da2207`). Only `b2Island.cpp`, `b2Settings.h` and `setup.py` were retained privately; nothing was installed or rebuilt. This matches the installed release number, not a claim of bit-identical compiled build provenance.

That release clamps oversized `dt*velocity` to max translation2m. Challenge source calls `world.Step(1/50,…)`, so dt0.02 gives the100m/s numerical ceiling. The265 installed-runtime microprobe is reused without another solver query. It is not tire/engine physics and current trajectory length divided by100 is **not** claimed as the shortest possible lap or a10s bound.

Actual `Car.step` uses engine40000 per rear wheel, omega increment proportional to dt*power*gas/(I*(abs(omega)+5)), I1.6,R0.54 and source gas rise0.1 per raw action call. Brake decreases omega by15*b **rad/s per raw20ms tick**, capped at remaining omega; brake≥0.9 locks. It is not15N or15m/s². Four raw ticks usually make one wrapper action. Positive and negative inverse pedal approximations remain unchanged in the candidate.

## Minimal source gate and single change

Existing N0 pace1.5 controls1–169 were replayed once, charging169 native. Speed/damage/tiles match265. Snapshot anchors13/54/165/167 generate four baseline/changed **3-action** source probes, same recorded steering, eight queries/96physics ticks. Baseline max speed mismatch2.30e−5m/s and discrete tile/contact/damage checks pass; omitted warm-start history remains a reconstruction limitation.

At anchor13, baseline gas0.391/0.424/0.457 leaves rear clipping0. Mean front/rear forces are−351.99/+587.55N. Removing only the positive clamp gives gas1, front/rear−453.06/+779.66N, rear clipping83.3%; end speed35.62→38.61m/s(**+2.99**), no collision and all wheels on road. Front opposing force grows with acceleration because free wheel rotational inertia must be spun up. It is not evidence of simultaneous throttle/brake waste to cancel.

The other probes are unchanged: brake54 and167 remain brake;165 is already gas1 for its two accelerating actions. This supports a local unused-acceleration opportunity, not a universally safe controller.

Freeze **one change**: replace upper acceleration clipping by `acc=max(feed+1.5*speed_error,-brake_accel)`. Retain the negative91.16873 bound, inverse pedal mappings,0..1 final actions, source gas slew/vector friction, fixed1.5 profile, exact258 geometry, global cursor, lookahead, steering limits/smoothing and GT scope. No new gain, traction ratio, torque cancellation, fallback or physics setting is added. Source saturation decides achieved force; the unbounded request is not a feasibility certificate.

## Actual failure and interpretation

Before first>3m error, rear clipping grows to37.3% on O0 and47.4% on N0; front11.2%/7.4%. On the corresponding original first79/81 actions rear clipping is0, front0/0.31%; these are elapsed-action prefixes, not matched spatial states. Before any grass-wheel contact, changed front/rear clipping is12.3%/38.1% and8.4%/48.6%. Hence the increased saturation precedes grass and damage and cannot be explained solely by reduced grass/damaged grip afterward.

At O0 action80: actual61.63,target87.05, steer0.324,gas1, all wheels still on road, error5.58m. At N0 action82: actual59.24,target83.53,steer0.262,gas1, all wheels still on road,error3.88m. Applying full power while turning spends the same tire-vector budget needed for lateral tracking. The unchanged pursuit/braking/profile combination does not retain completion under this extra longitudinal demand. Exact allocation of each force component at the first failure is not retained by the lightweight actual observer; no stronger causal attribution is claimed.

The original35.02 allowance leaves some acceleration unused locally and also contributes stability globally. Current lag includes model/controller conservatism, actuator power, anticipatory braking, tire coupling and the numerical ceiling. It is not one universal hard physical speed limit. Reject global positive-clamp removal. If further diagnosis is requested, the smallest next observation is applied longitudinal/lateral force allocation at the first steering/traction conflict before grass, rather than another unconditional gain or pace increase. No such extra run occurred.

## Cost and preservation

**542 native** =169 diagnostic prefix +373 actual candidate(182+191). Actual2168 raw step ticks +153reset ticks;25.36s combined execution wall time. Separately, eight reconstructed source queries/96model physics ticks,0.151s model wall time and eight0-time model initializations. No geometry solve, fitting or paid resource.265 completed full results are reused.

Cumulative824805; research remaining3195; reserved84000 untouched; B912000. No pixel/champion promotion, HOLDOUT, SEALED, changed source physics, extra pace or second candidate. Main, Participants, backups and user changes remain preserved. Full states, force probes, matching-release source and receipts stay private; public artifacts contain small diagnostic code and aggregate evidence.
