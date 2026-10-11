# A single curvature-term probe on the current pixel policy

The baseline is the original hazard-scheduled policy with global speed ceiling
40. Its two existing DEV completions and saved inputs are reused by exact archive
identity. The earlier learned-mask composite is a different policy.

The candidate changes only the active speed-target denominator from
`abs(curvature) + 0.003` to `max(abs(curvature), 1e-6)`. The purpose of the original
additive term is unknown. This tests the cost of that regularization, with a
larger relative target change at low curvature. It differs from raising the
global ceiling or multiplying the lateral acceleration coefficient uniformly.

Route selection, target coordinates, perception, tracking, steering, ceiling,
hazard scheduling and pedal feedback gains remain fixed. Requested speed and
pedals can change near hazards as well as elsewhere. Retaining the safe lateral
coefficient does not establish unchanged safety.

Saved-record analysis distinguishes curvature-limited targets from ceiling
limits and unsaturated acceleration. HUD measurement error also affects pedal
direction, so time spent braking cannot all be attributed to slow acceleration.
An inverse-target-speed diagnostic ranks this probe; it is neither a physical
bound on recoverable time nor a prediction of lap improvement.

Before driving, archive checks and replay verify the exact baseline actions,
unchanged steering on identical full pixel stacks, legal candidate actions and
an actual intervention. The same isolated worker receives only reset/act and
pixels. Existing supervisor evidence is reused only for unchanged components.

One frozen candidate runs once on each of the two known DEV roads, at most
2,000 actions each and 4,000 total. The baseline is not driven again. Each new
reset must match the baseline state and observation hashes. A technical failure
stops the batch without retry; normal driving failure or action-cap censoring
does not suppress the second condition. The research budget covers both runs
and leaves the final reserve untouched.

Incomplete or censored comparisons do not pass. Completion loss rejects the
candidate. With both completions preserved, a negative median paired lap change
and mean paired lap ratio below one support only a separate future gate. There
is no minimum percentage gain. Damage, collisions and worse tail latency remain
separate warnings. No result in this two-road DEV probe automatically replaces
the current champion or opens a protected split.

Private identities, plans, archives, full records and document excerpts remain
outside the repository. Same-host reproduction does not establish fresh-machine
or official-server equivalence.
