# 269: Frozen268 transfer on four remaining DEV roads

The candidate completes all three roads for which the fixed258 recipe produces a feasible path. Constant1.5 completes only one of those three. N2 has a solver coverage failure, so two requested runs are unexecuted rather than counted as driving DNF. Coefficients are never changed or reselected.

| DEV road | Cached pixel240 | Same-path constant1.5 GT | Frozen268 GT candidate |
|---|---|---|---|
| O2(old201 F2) |20.98s,damage0.2 |off_track260,damage0 |**18.52s,damage0** |
| N1(new241 F1) |17.08s,damage0 |off_track259,damage0 |**14.78s,damage0** |
| N2(new241 F2) |21.56s,damage0 |Unexecuted:solver infeasible |Unexecuted:solver infeasible |
| N3(new241 F3) |18.76s,damage0.2 |17.66s,damage0 |**15.94s,damage0** |

Within the feasible-road paired comparison: candidate3/3 complete versus baseline1/3; N3's common-completion gain1.72s. Candidate times versus pixel240 improve2.46/2.30/2.82s, but that comparison additionally changes global map/path/controller information and is not a legal pixel gain attributable solely to the speed expression. Original240 completes N2; the teacher cannot supply this fixed-recipe route there.

## Fixed geometry and solver outcomes

Use existing TRAIN/DEV registrations and initial snapshots only, no new HOLDOUT. Each road is solved once with unchanged258 representation/objective/constraints:16 periodic B-spline offsets, original obstacle-away initialization, six coordinate passes2/2/1/1/0.4/0.4, approximate lap-time objective plus fixed constraint/roughness terms and original source-based model constants. No side search, new knot count, road-specific tuning or speed-coefficient search.

| Road | Static geometry status | Minimum expanded-obstacle clearance | Max absolute curvature |
|---|---|---:|---:|
| O2 |Feasible directly |+2.876mm |0.128603/m |
| N1 |Feasible directly |+0.020mm |0.123345/m |
| N2 |Infeasible |−0.9108m |0.131372/m |
| N3 |Feasible after fixed numerical projection |+0.100mm |0.115028/m |

The steering bound is tan(0.4)/3.24≈0.130492/m. N2 exceeds that bound and has substantial obstacle-clearance violation. The fixed search finding no feasible output is not a proof that the road has no feasible route; representation, search and conservative vehicle/obstacle margins may limit it. Both N2 arms are skipped before any reset/action. They are not actual DNF or censoring.

The predeclared existing258 numerical projection is used only for a residual within1mm when steering is already feasible. N3 needs35 geometric evaluations and max coefficient change0.191mm; constraints/radii/controller remain unchanged. Its reported raw solver violation precedes this projection. The frozen projected path is identical in both arms. No projection is attempted on the large N2 failure.

All valid pairs bind identical plan hashes and the exact268 coefficient file/algorithm. Zero coefficients reproduce constant1.5; candidate coefficients are reused unchanged. Arm order was fixed before solving:O2 B/C,N1 C/B,N2 B/C,N3 C/B. Initial image and full source track hashes match registrations. Static path feasibility is not a dynamic tracking guarantee.

## Tracking and baseline stalls

| Road | Baseline mean/p95/max error | Candidate mean/p95/max error |
|---|---:|---:|
| O2 |0.543/1.480/1.969m |0.690/1.707/2.466m |
| N1 |0.509/1.582/2.109m |0.639/1.666/1.832m |
| N3 |0.631/1.603/3.417m |0.625/1.615/1.927m |

Candidate has no>3m event or collision on any of the three roads. Baseline N3's>3m event is its final action221; it still qualifies for official completion. Baseline failures have low path error because they stop for much of the episode: O2 ends at nearly0m/s, target52.37m/s,gas0/brake0.3,error0.441m,193/289 tiles; N1 nearly0m/s,target72.75,gas0/brake0.3,error0.411m,187/238 tiles.

The `off_track` retirement follows no new progress, not evidence that path error exceeded a large geometric threshold. Persistent braking below a positive target is consistent with the original spatial feedforward/feedback interaction. Feedforward terms were not separately recorded in these lightweight runs, so no stronger complete causal claim is made. Some candidate gains may avoid GT follower/profile stalls rather than express extra physical vehicle speed headroom. Do not distill those full pedal commands blindly.

This differs from260's current-visibility connection/fallback failures:269 supplies a full global map and fixed whole-lap path. N2 fails before control in the geometry solver; O2/N1 baseline failures occur in actual following. The current result gives five successfully driven teacher roads when combined withO0/N0, **not six-road teacher coverage**.

## Smallest next pixel learning experiment — recommended only

First distill **one local relative pace correction**, `pace268/1.5−1`, rather than global route, absolute GT target speed or full pedals. It is small, conditioned on local curve/drive/brake demands and does not carry a road-position identifier. GT pose/index can query labels offline but must never become student inputs.

Use already cached240 on-policy pixels/derived curvature, route extent, hazard and HUD features; retain only labels whose meaningful geometry support is visible/recently observed. Do not force a student to predict a whole-map unseen-future bottleneck. One fixed scalar linear/ridge fit is enough for a first pilot; freeze it without gain/ratio sweeps.

Apply the predicted correction at the existing nominal goal-selection hook, retain the original cap, and recompute candidate nominal pedals/features consistently before the unchanged affine head/scales. Keep240 route extraction, steering, nominal memory and absent-route fallback. A zero correction must reproduce240 action/features/memory exactly. This differs from263's wholesale physical-pedal replacement and264's current-speed-anchored profile goal that forced nominal gas0.

Then use a minimal actual DEV gate with N2 mandatory before deeper work, even though N2 has no valid teacher-path labels. This checks the coverage bias instead of silently excluding the teacher's hard case. The GT comparison contains path/foresight and feedforward interactions absent in the pixel controller, so GT lap gains cannot be promised to transfer. No dataset fit or pixel experiment is performed in269.

## Cost and preservation

Requested8 episode slots: **6 actually executed,2 solver-blocked**. Actual DNF2,censored0,technical errors0. New **1357 native**(260+232+185+259+200+221), below4500 cap;5425 actual raw step ticks +306 reset ticks. Native episode wall46.68s,evaluation46.96s.

Separately,4 geometric solves,776 objective calls,3.143s solver wall(5.198s whole preparation including existing snapshot reads),35 numerical-projection geometry evaluations. Positive-time model physics queries0,new car-model initialization0,new speed/model fit0. Coefficients and geometry remain frozen through both arms; no candidate reselection.

Cumulative830787; research remaining5213; reserve84000 untouched; B920000. Champion240, main, Participants, backups, HOLDOUT and SEALED preserved. Full maps/plans, registration identities, raw traces and parameter files remain private. Public artifacts contain small diagnostic code and aggregate results; this remains a whole-map GT oracle, not a pixel participant.
