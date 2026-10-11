# Stage132: motion tail reduced; micro-tracker line closed

**Keep 116. No native run; close this micro-tracking line.** One legal candidate
improves estimated movement but fails the preregistered risk-tail gate and has
no controller effect in the selected failure window.

The saved-input interval is correctly 0.080s. Previous image corresponds to the
previous action's input pose, rather than its output pose. Pixel axes have
scales 1.3608 and −1.701: a pixel-space similarity cannot exactly represent body
yaw. Endpoint speed also omits interval integration, lateral movement and yaw.

Four fixed stored contrasts change tracker movement only: 131, true current
scalar speed, true interval translation, and exact interval translation/yaw.
Current centers/radii, observations and the same controller remain fixed.
The two actual 131 windows reproduce tracker, route, target and action exactly.
The separate oracle-seeded fallback window is a research history, not a native
131 run. No diagnostic rollout or extra detection/raster was needed.

In the failed DEV's six retained inputs, maximum error is **5.604m**, unchanged
by true endpoint speed; translation gives **0.893m**, exact SE2 **0.314m**.
Exact SE2 changes one near predicate/action. This interval follows first
contact, so it does not show contact prevention or a rescued native outcome.
The fixed fallback window's 0.792m error falls to numerical zero under exact
motion, establishing the omitted movement contribution in that history.

The sole legal candidate fits the existing LK correspondences in isotropic
body coordinates and converts the result back to pixel affine. Features,
LMEDS, validity guard, 131 fallback, current detector, radius, age/association,
margin, route and pedal/controller source remain fixed; 13 other archive
members are byte-preserved. No GT reaches candidate movement or control.

| Fixed risk window | 131 maximum error | Legal candidate maximum | Tail gate |
| --- | ---: | ---: | --- |
| Actual failure | 5.604m | 2.528m | Fail |
| Actual rescue | 0.594m | 0.294m | Pass |
| Known fallback residual | 0.792m | 0.792m | Fail |

The limit is **0.735m** (one horizontal pixel) in every risk window. Improved
mean cannot override this tail. Failure memory changes at six inputs but
route, target, near and action stay identical. Rescue has six saved action
differences; that is not a new native result. The fallback remains unchanged.
No native, dense replacement, threshold tuning or second candidate followed.

Cost: **0/4000 new native actions**; completed saved work used 124 diagnostic
and 31 legal tracker calls, 130 route/controller calls each (1.258s measured
analysis wall, 1.240s CPU). Two aborted saved identity-bookkeeping attempts
required correction; their helper-call counts are bounded rather than exact.
All four interpreter attempts used 3.291s wall including startup. Full-policy,
new detector/ridge, model and raster calls were zero. Cumulative native 609586;
research **12414**, reserve **84000** untouched. HOLDOUT details/SEALED stay
closed and private data/archives stay private. No paid resource or extension.

The next separate question with greater information value is whether the
existing pre-contact controller target yields a feasible collision-free hull
and wheel footprint. Diagnose existing scenes with source and radii/margin
fixed. No successor experiment or global-margin retuning was launched.

Recipe: [metric_motion_candidate.py](metric_motion_candidate.py).
Aggregate evidence and cost: [metric_motion_result.json](metric_motion_result.json).
