# 260: Current-view GT rolling local planner

This diagnostic exposes freshly observed geometry inside the actual renderer camera to a small local planner. It does not crop a preoptimized global path or speed profile. Runtime planning receives unordered visible boundary-derived segments, wholly visible obstacle circles, current GT pose and speed. No global tile IDs, finish index or future route/profile enter the planner. Previously observed feasible plans may be retained. This is privileged local GT, not a pixel-only participant.

Before native execution, the contract fixed six open cubic spline variables, two coordinate passes (1.0, 0.4), replanning every three actions, and acceptance of geometrically feasible plans only. If planning fails, retain the previous observed feasible plan; if none exists, use zero gas and 0.1 brake. The unknown tail holds the last observed curvature for speed and tangent/arc extension; there is no forced terminal stop. Source model constants and controller gains were reused without fitting.

| DEV road | Cached240 | Cached259 global feasible reference | Current-view260 | Official outcome |
|---|---:|---:|---:|---|
| O0 | 23.66s | 22.52s | 26.06s | Complete, damage0, 315/326 tiles |
| N0 | 23.62s | 21.74s | — | Crash at action313, damage1, 144/325 tiles |

O0 is 3.54s slower than259 and 2.40s slower than240. N0 first takes damage at action309; collisions repeat through313. It last gains a tile at288. Its late plans are unavailable at289,295,298,304,307, so control retains previously observed plans. These are associations, not an isolated causal test.

O0:109 replans,100 accepted,7 unavailable,2 infeasible. N0:105 replans,88 accepted,14 unavailable,3 infeasible. Median available path length is31.50m for both; minimum10.51/11.09m. Finite plan-distance mean/p95/max is2.56/6.45/14.18m and5.21/16.80/22.86m. This measure includes longitudinal distance to a forward-only endpoint and distance to a stale plan. It is not directly comparable to lateral tracking error on a full global route. Median/max actual speed is44.55/75.96m/s and40.06/97.75m/s.

The provider projects live road quadrilaterals using source zoom, rotation, translation, vertical flip and HUD exclusion. Only wholly camera-contained quads with unoccluded sampled boundaries are returned; center segments are inferred from the visible boundary. Obstacle circles must be wholly in view and unobscured by the car. This is a conservative geometric sensor: sampled continuous-boundary checks are not exact downsampled raster ownership, and no claim of pixel-equivalent perception is made. Partial visible geometry is discarded, which can shorten or disconnect the local route.

Each road was executed once to official finish/retirement. No baseline was replayed. Cost:639 wrapper actions,2555 raw step ticks plus102 reset ticks;33.64s execution wall time. There were4825 geometry objectives,193 local speed profiles,10.70s total provider/planning time, and zero positive-time model-physics queries. Replanning median/p95/max latency is47.50/62.43/71.24ms for O0 and48.91/69.70/138.40ms for N0. Full action computation p95/max is54.97/71.41ms and61.20/138.61ms. These timings are in-process GT inference, including visibility extraction, not isolated participant IPC.

No promotion, tuning, additional run, HOLDOUT, SEALED or final-reserve use. Cumulative native820135; research remaining3865; reserved84000 untouched. Champion240 and main remain unchanged. Private frozen contract, inputs, execution receipts, traces and accounting are retained separately; public artifacts contain only code and aggregate diagnostics.

The outcome changes local information, open-end assumptions, six-variable solver capacity, rolling replanning and fallback jointly. It does not isolate future visibility alone, establish a10s bound, or establish pixel-policy impossibility. The next useful review is an offline examination of local route disconnections and stale-plan control before considering any separately authorized experiment.
