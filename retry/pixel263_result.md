# 263: Existing240 pixel path with local longitudinal speed profile — rejected

A legal pixel-only pilot preserves current240's path extraction, ordering, obstacle tracker, route target, steering and nominal memory. It replaces final pedals on active paths with one fixed local profile/control law. O0 becomes slower and damaged; N0 loses completion. The performance gate fails and no variant is run.

| DEV road | Cached240 | Pixel profile263 | Official result |
|---|---|---|---|
| O0 |23.66s,damage0 |41.52s,damage0.6 |Complete,326/326 tiles; +17.86s |
| N0 |23.62s,damage0.2 |—,damage1 |Crash action174,120/325 tiles |

O0 contacts occur181–183; N0 contacts170–174. All694 actions have active plans; missing-path fallback never occurs. These failures therefore do not reproduce260–262's GT route-reconnection/fallback problem.

## Frozen method and composition

The wrapper observes the exact existing240 `connected_route` result and tracked obstacles without modifying either or adding a vision call. The original ordered body-coordinate path is unchanged. Curvature is differentiated using chords at±3.24m along that same polyline, reusing wheelbase scale to avoid differentiating individual pixel grid corners; this does not resmooth or reroute the geometry. All original240 archive dependencies remain byte-identical, including the nominal source, learned head and global scales. The original root is preserved in the candidate archive.

The profile uses existing240 speed cap45 and hazard-selected lateral budget24/8. Original obstacles already determine route clearance and that hazard mode; no additional GT obstacle test is introduced. Four forward/backward passes reuse259's source-derived numerical effective-mass, engine, traction and braking approximations. Initial speed is current240's image/HUD feedback proxy. The unknown visible tail holds the adjacent observed curvature and its nonzero cap; no stop is imposed. Observed minimum terminal caps/profile speeds are4.32m/s on O0 and4.47m/s on N0.

Longitudinal control uses259's first-segment squared-speed feedforward plus fixed1.5 speed feedback and its inverse actuator approximations. The **sole output composition point is after the original head and global scales**: replace both final pedals, retaining nominal steering exactly. On active paths, the old residual/scales are computed for the frozen baseline audit but are bypassed for returned pedals. Adding them onto the physical-profile pedals would mix two goal-dependent laws and could cancel the new target. Sole post-composition replacement is the fixed minimal comparable alternative used here; no blend/ratio is searched.

This tests profile plus actuator law together. It does not isolate the speed-profile contribution from removal of the learned/rescaled pedal law. Keeping the frozen head after a changed nominal target would also create a feature/target-distribution mismatch, rather than a clean no-cost preservation of240 calibration. That alternative was not executed.

If the current target is absent/nonforward, path is missing, or the profile input is invalid, return the complete validated240 action. No past GT path, pose, tile index, future plan, training record or learned new fallback is loaded. A synthetic no-road pixel observation confirms complete fallback action and nominal state match240 exactly; actual runs need no fallback.

## Boundary and verification

The archive runs in the existing native read sandbox plus Python audit hooks, clean extracted package, sanitized environment and oneCPU/thread. Only official float32 grayscale reset/act observations reach the participant. Simulator modules and outside file reads are blocked; ready/response receipts show no denied events or simulator imports. This is same-host research verification, not new remote official-runner qualification.

Sixteen paired cached pixel observations show bit-exact steering, original features and nominal state against240, with zero native actions. Each pixel pipeline is called once; output pedal changes are not fed into nominal memory. Later trajectories, and therefore their pixels and steering values, can differ physically. Package/static import checks, frozen hashes, fallback check and actor reaping pass. No training or new road collection occurs.

Repository search found no identical current240 pixel-path forward/backward profile pilot. Prior `oracle_teacher`/`spatial_speed_probe` and258–259 use privileged global paths;260–262 use live GT local geometry and different tracking/fallback.263 uses none of those runtime references and changes no pixel path connection.

## Cost and interpretation

New **694 native**(520+174),2773 raw step ticks +102 reset ticks;32.91s execution wall time. The cached240 full results are reused, not replayed. There are694 actual pixel profiles and16 offline profiles;34 offline actor calls include16 matched pairs and one matched absent-route pair. Positive-time simulator model queries0.

Planner median/p95/max cost: O0 **0.591/1.283/9.130ms**, N0 **0.596/1.034/1.730ms**. Total planning0.488s. Full agent compute median/p95/max6.617/14.100/26.951ms and6.240/11.118/16.052ms. IPC max29.58/19.02ms, well within the local action deadline.

Candidate HUD-feedback medians23.75/26.25m/s and target medians21.25/26.25m/s are lower than the high-speed240 operating regime. On these candidate observations, planner gas is on average0.427/0.417 lower than the unchanged240 counterfactual output; this is a same-observation action comparison, not a native baseline trajectory or a causal lap-time decomposition. Low cost and legal inputs are verified, but this curvature estimator, short visible horizon, pixel proxies and physical actuator approximation do not reproduce learned240 performance. No claim of pixel-planning impossibility,10s limit or future-map causality follows. Stop without gain, ratio, cap or head changes.

Cumulative822622; research remaining1378; reserve84000 untouched. Champion240, main, Participants, backups, HOLDOUT and SEALED remain preserved. Candidate ZIP, raw pixel-derived traces, frozen plans and receipts are private; public artifacts contain small code and aggregate outcomes.
