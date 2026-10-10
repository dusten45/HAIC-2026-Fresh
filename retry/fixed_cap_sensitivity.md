# Fixed distance-cap sensitivity

Run `python -m retry.fixed_cap_sensitivity --plan PRIVATE_PLAN_JSON` with a
previously frozen plan. The coordinator reuses the charged native episode
evaluator and its isolated pixel-only worker. The plan and raw evidence belong
outside the public repository.

The candidate builder verifies an archived baseline and changes exactly one
literal in a separate archive: `sqrt(10 * d)` becomes `sqrt(11 * d)`. This is a
1.10 multiplier on the heuristic deceleration coefficient and a `sqrt(1.10)`
multiplier on the uncapped speed bound. The inherited minimum target, existing
floor and ceiling can mask its effect. This heuristic does not establish a
measured physical braking guarantee. Every other policy source stays identical;
the changed action can still alter subsequent observations and steering.

Reuse saved baseline results only after checking archive members, environment
sources and settings, road and physical-obstacle geometry, and recorded initial
observations and state. Before each candidate policy reset or action, compare
the actual full initial pixel stack and the available recorded state fields.
This checks the saved state coverage; it does not claim that every hidden
simulator variable was recorded. No additional baseline episodes are run.

Execute four preselected DEV conditions in their frozen order, starting with a
previously rescued completion. Stop at the first native DNF that loses a saved
completion and mark the remaining conditions unexecuted. Technical and resource
limits are censored separately. Apply the strict negative mean and median
candidate-minus-baseline lap-time rule only if all four completions survive.
Charge every new wrapper action and account for reset and post-reset raw ticks
separately, including shortened final wrappers at native completion. Preserve
the baseline archive and default policy throughout.

The checked sensitivity preserved the first completion, worsened the next lap,
and then lost a completion with added damage. The candidate was retired at that
native failure; the last condition was not executed. The four-condition mean
and median gate was not evaluated. No second coefficient, protected split,
promotion, or baseline replacement follows from this result.
