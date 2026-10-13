# 264: Same profile through240 nominal/head/scales — integration family closed

A clear nominal-goal contrast is possible. The frozen263 pixel speed profile now selects one240 nominal target;240's original longitudinal machinery remains active. Both roads recover completion relative to263, but both are slower than240. O0 also gains damage. Reject and close this integration family without a gain sweep.

| DEV road | Cached240 | Cached263 final-pedal law | Nominal-goal264 | Delta vs240 |
|---|---|---|---|---:|
| O0 |23.66s,damage0 |41.52s,damage0.6 |25.78s,damage0.2 |+2.12s |
| N0 |23.62s,damage0.2 |crash174,damage1 |24.66s,damage0 |+1.04s |

264 completes2/2, mean25.22s versus240 mean23.64s(**+1.58s**). O0 is15.74s faster than263; N0 completes instead of failing. O0's sole contact is122; N0 has none. Every264 action has a profile, so no fallback is used.

## One goal decision; unchanged downstream control

Original240 computes its speed target in the nominal agent for feature6 and recomputes the same formula inside `SpeedController.action_target`. The builder adds one selector at the nominal agent's target-speed decision. Its selected value is explicitly passed to the controller, avoiding two inconsistent goal decisions. The controller's original steering,0.08 gas/0.04 brake P calculation, pedal0..0.5 clip and nominal state updates remain unchanged.

All16 features are then derived from this same candidate call. Feature6 contains the selected profile goal;14/15 contain the nominal gas/brake generated from that goal. Curvature, route target and all other feature definitions remain240. No original-policy feature vector is mixed with candidate pedals. The frozen affine mean/std/weights, residual±0.5 clip, exact global scales1.412502928638687/0.8138581028883641 and final0..1 clip remain byte-identical; root240 composition is unchanged. New pedals never feed nominal memory.

The263 profile function's AST and constants are exact: same wheelbase-chord curvature on the unchanged ordered pixel path, cap45, near/normal lateral8/24, four forward/back passes, current HUD-feedback initial speed, and last observed curvature at a nonzero tail. No boundary, curvature coefficient, profile gain or path is changed.263's physical final-pedal law/feedforward is intentionally removed as the comparison factor; no new feedforward, actuator equation or ratio is substituted.

The profile's chosen first speed is at most current feedback speed. Consequently every active264 nominal gas is **zero**; positive throttle comes from the existing residual head. This property was noted before actual execution and left intact. It is a limitation of using a current-speed-anchored profile entry as a P target, not a reason to silently choose a different future sample or add gain/feedforward.

The new goals change73.4%/68.9% of O0/N0 target decisions relative to the original goal formula on the candidate observations. Median feedback proxies are46.25m/s; median selected goals35.84/37.32m/s. The head sees shifted goal/nominal features and was not retrained. Its residuals do not hit±0.5 in these runs, but absence of clipping does not establish in-distribution inputs. The final mean gas is0.474/0.478 despite zero nominal gas. Thus retaining240 machinery also retains its learned response to the new goal; it does not make final pedals an exact physical implementation of the profile.

## Identity, consistency and legal boundary

Sixteen paired cached observations with the **original240 target supplied through the new plumbing** reproduce complete action,16 features and nominal state bit for bit. Sixteen profile-mode pairs preserve steering/state; only feature indices6/14/15 change. A synthetic absent-road observation reproduces complete240 fallback action, features and state. Static archive/import checks and same-host native/Python pixel sandbox pass. Runtime sees grayscale reset/act observations only; no GT road/pose/index, future259 plan or external training data.

Every actual264 pedal output is independently reconstructed bit for bit from its own stored features, original affine parameters, exact scales and original clipping stages. This is offline numerical verification, not fitting, feature mixing or another simulator rollout. Original root, head, scale, perception and route members remain byte-identical; the two source edits only expose and forward the selected goal. Frozen hashes, actor-origin and actor-reaping checks pass.

## What the contrast establishes

Keeping240 longitudinal processing restores both completions and much of263's lost speed. This supports a contribution from263's final-pedal-law replacement and its interaction with the profile. It does not provide an additive causal split of all lost time: changed control changes pixels, tracked obstacles, speed proxies and ensuing profiles. A shared profile implementation is not an identical profile trajectory.

The target-only integration still fails the preregistered time/damage gate. The unchanged head is responding to changed inputs; no claim is made that the raw profile alone caused every delay or collision. Stop this speed-profile integration family without changing sample location, gains, cap, ratio, boundary or head. Champion240 remains selected; no pixel-planning impossibility or future-map causal claim follows.

## Cost and preservation

**632 native**(323+309),2524 raw step ticks +102 reset ticks;26.84s execution wall time. No prefix replay or new native baseline.240/263 full results are reused.632 actual profiles,16 offline profiles,50 offline actor calls and632 offline head-reconstruction rows; positive-time model physics queries0, new fitting0.

Planning median/p95/max0.553/0.939/14.756ms for O0 and0.559/0.880/3.430ms for N0; total0.395s. Full agent compute median/max5.97/47.10ms and6.04/21.30ms; maximum IPC49.62/23.37ms, within the local deadline.

Cumulative823254; research remaining746; reserve84000 untouched. Champion, main, Participants, backups, HOLDOUT and SEALED are preserved. Candidate/identity ZIPs, complete features and traces, hashes and receipts remain private. Public artifacts contain the small integration builder/selector and aggregate results.
