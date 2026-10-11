# Stage134: one path-ranking intervention rescues completion

**Keep 116; retain frozen 134 for research.** The two-DEV completion gate passes,
but collisions remain. The candidate is not adopted.

One term adds the nominal steering-transition distance
`speed * abs(next_smoothed_steer - previous_command) / 3` to legacy path cost.
Both saved evaluators receive the same pixel-derived state and candidate pool:
the original path plus shortest left/right crossing alternatives on the same
graph. There is no passing-side lock. Detector, tracker, radius, 2.6m margin,
grid, goal, lookahead and speed/pedal/controller laws remain fixed.
Previous command is a legal proxy, not the measured wheel angle or a guarantee
of achievable steering time.

On 63 saved pre-contact inputs, the zero-term evaluator reproduces every
original route, target and action. The added term changes one failed-window
input; the other two windows are unchanged. Candidate paths pass the original
graph and no-corner constraints. No GT enters ranking.

| Native DEV | Cached 131 | Frozen 134 |
| --- | --- | --- |
| Failure | DNF, damage 1.0 | Complete, 45.040s, damage 0.6 |
| Rescue | Complete, 48.500s, damage 0.2 | Exact same actions/observations and outcome |

The failure run has 403 identical input/action steps. At step 404, the same
input and controller state produce the sole alternate-route selection. In
the fixed 21-input pre-contact window, passing-side/curvature reversals fall
**8→4**, opposite joint/command inputs **8→5**, maximum joint error
**0.624→0.362rad**, and clean-interval joint residuals above 0.01rad **6→1**.
After this matched intervention, trajectories differ; these mechanism counts
are descriptive. Target curvature also changes downstream pedals under the
unchanged law, so the rescue does not isolate steering lag as its sole cause.

First contact moves from input 416 to 418. Damage-bearing wrapper events fall
5→3, but are not distinct physical encounters. The rescue DEV still has its
original contact. Collision-free efficacy therefore fails. Cached 116 is clean
on the failure DEV in 43.820s: 134 is 1.220s slower and damaging there.

Cost: **1171/4000 new native actions**, no baseline rerun or retry; 49.710s wall
including records, 40.756s evaluator CPU and 9.070s actor CPU. Both actors were
reaped, with no simulator import or audit denial. Saved comparison and summary
used 2.071s wall including startup. Research remaining **11243**, reserve
**84000** untouched. Private records/archives stay private; HOLDOUT details and
SEALED remain closed. No paid resource, tuning or successor run was added.

The next useful efficacy check is this exact candidate on the remaining DEV
cases against cached 116, preserving the damage/lap regression as a risk.

Reproducible builder: [steering_connection_candidate.py](steering_connection_candidate.py).
Aggregate evidence and provenance: [steering_connection_result.json](steering_connection_result.json).
