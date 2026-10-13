# 265: Fixed258 GT free-line pace stress

All four preregistered stress episodes complete without damage, collision or path error above3m. Both higher paces improve on the reused258 results. The original approximate envelope therefore had conservative headroom; it was not an attained physical optimum. The stressed targets themselves remain unattained, and are not certified feasible profiles.

| DEV road | Reused pace1.0 | Pace1.25 | Pace1.5 |
|---|---:|---:|---:|
| O0 |21.86s |20.66s(−1.20s) |19.70s(−2.16s) |
| N0 |22.12s |19.92s(−2.20s) |20.20s(−1.92s) |

All damage0; all326/325 tiles visited. Actual DNF0, censored0, unexecuted0.1.25 mean20.29s versus original21.99s(−1.70s);1.5 mean19.95s(−2.04s). N0's1.5 is0.28s slower than1.25, so increasing the target does not monotonically improve actual time. No extra factor or successful-road selection was run.

## Constraint origin and frozen comparison

Source values: engine40000 per rear wheel(80000 total), wheel inertia1.6, radius0.54, road friction limit400 per wheel, dt0.02, brake reduces wheel omega by15*b each physics tick, upward gas slew0.1, joint steering bounds±0.4, wheelbase3.24, and Box2D body-shape mass7.30192.

Planning/controller assumptions: rolling effective mass29.24979, no-slip power proxy80000/(v+2.7), rear traction use0.8 giving35.01888m/s², brake use0.3 giving91.16873m/s², total lateral use0.4 giving87.64818m/s², numeric profile cap100m/s, four fixed forward/backward passes, ideal path tracking and the fixed pursuit/feedforward/feedback law. The0.8/0.3/0.4 utilization fractions are chosen model allowances, not measured maximum physics limits. Tire friction is a coupled longitudinal/lateral vector constraint; the model reduces it to scalar envelopes.

The exact existing258 free geometry, including its recorded O0 pre-execution feasibility correction, speed profile and model were reused. No geometry solve, repair, road conversion or model fitting occurred. Each pace multiplies the original spatial speed array **after** the same standing-start/lap-wrap choice; there is no new100 clamp on the stressed targets. The same global cursor, pure-pursuit parameters, action bounds,35.01888/91.16873 command acceleration clamps and1.5 feedback gain remain. Squared-speed feedforward changes with the scaled profile; this tests spatial speed targets and their braking law, not240 global gas scale.

Scaled targets violate the original approximate acceleration and braking envelopes: O0 has206/69 such segments at1.25 and209/72 at1.5(out of326); N0 has225/77 and225/78(out of325). Maximum implied lateral demand136.95/197.21m/s² exceeds the original87.65. These are stress references, not physical feasible solutions. Actual completion verifies achieved vehicle motion, not exact tracking of those references.

## Speed, tracking and tire saturation

| Road/pace | Actual/target median speed | Median actual/target ratio | Max path error | Front/rear clipped wheel-ticks | First clipping action |
|---|---:|---:|---:|---:|---:|
| O0/1.25 |53.67/64.41m/s |0.816 |2.06m |1.94%/1.84% |165 |
| N0/1.25 |57.44/67.79m/s |0.837 |2.03m |1.55%/1.15% |129 |
| O0/1.5 |56.18/77.89m/s |0.710 |2.24m |5.94%/6.75% |82 |
| N0/1.5 |56.55/81.36m/s |0.684 |2.50m |2.57%/0.69% |29 |

Mean actual-minus-target errors−11.90/−10.89/−23.27/−25.05m/s, in table order. Sampled target maxima125/116.97/150/140.42m/s versus actual maxima100.00001/94.46/100.00001/94.04m/s. Requested acceleration is clipped by the unchanged controller on87.3%/90.0%/88.3%/90.9% of actions. All first brake actions are23. Profile multiplication changes demands, but does not force the actuator or vehicle to deliver them.

The3m event threshold was fixed before execution and did not act as a veto. No first large-error or first-collision event exists in any run. Read-only Python source-local tracing observes raw tire-vector magnitude versus the live friction limit, aggregated per action; no forces, controls or body state are modified. Traced wheel samples equal four per actual physics tick. All sampled wheels remain on road, so the clipping fractions are road fractions; no grass or damage-grip confound is present. Clipping is observed transient saturation, not proof of universal friction-limited pace or failed tracking.

## Additional numerical ceiling

The installed Box2D2.3.5 exports max translation2m per solver step. At the source dt0.02 this gives a numerical100m/s velocity clamp. A separate one-body, one-tick probe confirms initial500m/s becomes100m/s and advances2m. It uses zero challenge wrapper actions and changes no challenge world or solver settings. The upstream design explicitly rescales velocity for oversized translations; see [Box2D island integration](https://raw.githubusercontent.com/erincatto/box2d/v2.3.1/Box2D/Box2D/Dynamics/b2Island.cpp) and [translation settings](https://raw.githubusercontent.com/erincatto/box2d/v2.3.1/Box2D/Box2D/Common/b2Settings.h).

Thus the planner's numeric100 cap coincides with an actual solver stepping ceiling here. This is distinct from engine/friction physics and from the conservative lateral/accel model. It explains why targets125/150 cannot be literally attained on the O0 straight. It does not make the achieved laps optimal, isolate every source of target lag, or establish10s impossibility for other paths/controllers. No such bound is claimed.

## Cost and preservation

Authorized research-only increment4000 is recorded once: B908000→912000, start cumulative823254, research4746, reserve84000. Actual task cost **1009 native**(259+250+247+253), below2500 cap;4025 physics step ticks +204 reset ticks;50.77s execution wall time including the tire observer. One separate solver microprobe tick is recorded offline; new car-model queries/geometry solves/fits0. Completed pace1.0 episodes are reused without native replay.

Cumulative824263; research remaining3737; reserve84000 unused. No legal model promotion, champion change, HOLDOUT, SEALED, paid resource or automatic factor sweep. This remains a privileged whole-map258 diagnostic, never a pixel participant. Main, Participants, user changes and backups are preserved. Frozen maps/profiles, detailed traces and receipts remain private; public artifacts contain small diagnostic code and aggregate evidence.
