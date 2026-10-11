# Stage133: pre-contact geometry and steering diagnosis

**Keep 116; no candidate and no native run.** The frozen stop rule applies:
the evidence does not isolate one planner or follower repair.

The comparison uses 63 saved inputs: 21 ending at first contact in each of two 131
DEV runs, plus 21 around closest approach to the same obstacle in a clean 116
reference. All causal poses have zero damage and precede contact. After-poses
are used only to measure joint response in intervals without contact. Stored
target curvature and clipped/smoothed steering reconstruct exactly.

| Diagnostic window | Route prefixes with sufficient all-heading clearance | Passing-side reversals | Joint opposite command | Held command-arc overlaps |
| --- | ---: | ---: | ---: | ---: |
| Failed 131 | 12/21 | 8 | 8/21 | 1/21 |
| Completed 131 with contact | 12/21 | 2 | 1/21 | 4/21 |
| Clean 116 reference | 8/21 | 0 | 0/21 | 0/21 |

These are descriptive counts on different trajectories and approach windows,
not a matched-state causal comparison. The clean window has 11 forward-crossing
side labels; its other 10 inputs have the obstacle behind the hull.

Each clearance concerns the selected obstacle only; road edges and other
obstacles are outside this screen. Exact source hull polygons, independent
wheel poses, circle radius and 0.01m
polygon skin replace a center-only check. The conservative hull-radius bound
is 2.864m; an inconclusive bound does not prove an impossible path. The stored
polyline has no yaw or curvature continuity. Imposing its segment tangent
produces three overlaps even in the clean reference, illustrating that limit.

Two failed-run inputs have clear route bounds of **+0.173/+0.120m** while the
raw target point-circles overlap by **0.104/0.063m**. The actual smoothed steering
commands, modeled about the rear axle with the 1.64m hull offset, instead have
**+0.449/+0.308m** clearance. The raw point-circle discrepancy therefore does
not identify a follower defect. Held arcs cannot certify dynamic feasibility.

The failed route and nonzero target curvature both reverse side eight times.
Six contact-free intervals retain joint error above 0.01rad. Planning changes
and steering response are coupled; changing gain, lookahead or clearance now
would not test an isolated cause. Large post-impact errors were excluded.
Source and causal reviews independently support this diagnosis-only stop.

Cost: **0/4000 native actions**, no policy/tracker/planner/controller/model or
new detector/render calls. Successful analysis used 1.039s wall and 1.027s CPU;
four instrumented attempts including two technical aborts used 2.407s wall.
This excludes ordinary file inspection and packaging. Cumulative native 609586;
research **12414**, reserve **84000** untouched. HOLDOUT details/SEALED remain
closed; private traces, seeds, frames, geometry and archives remain private.

The next useful measurement is left/right route continuity and connection
from current steering using the **same stored state estimate, bounded steering
sequences and scoring terms**. True geometry remains a diagnostic label. No
successor experiment was launched. No larger budget is needed for that saved
comparison: recent measured throughput was 22.21 wrapper actions/s, so a later
4000-action gate would take roughly 180s at that rate, without a timing guarantee.

Reusable calculations: [precontact_feasibility.py](precontact_feasibility.py).
Aggregate evidence, limits, provenance and cost:
[precontact_feasibility_result.json](precontact_feasibility_result.json).
