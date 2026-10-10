# Frozen-policy fresh DEV distribution

`python -m retry.fresh_dev_distribution --plan PRIVATE_PLAN_JSON` runs one
episode per prospectively registered condition in its fixed order. The plan,
candidate archive, split, budget ledger and all resulting data live outside the
repository. This runner does not change the participant package or configuration.

Before observing performance, register new road seeds, road geometry identities,
obstacle identities and random-generator ancestry against the existing split
identity inventory. Keep all first valid identity-disjoint roads. Geometry-only
stratification and label assignment must be frozen before a policy or environment
episode starts. A label selects obstacle randomness, not a road template.

The evaluator reuses the official environment and isolated full-route pixel
worker. Only operation and the complete four-frame pixel stack enter the worker.
The observer returns original detector, tracker, routing and controller results
after exactly one original call. Privileged geometry and vehicle state remain in
the evaluator. Newly measured observation hashes have no saved reference against
which to assert equality.

The first contact saves a rolling window before the collision flag. The first
progress-stagnation marker requires the configured consecutive wrappers with no
new unique tiles. Its onset and detection time are distinct; the rolling buffer
retains the requested pre-onset history and short post-detection context. Missing
prehistory or a terminal that cuts the post-window short is explicitly marked.
Existing raw calls provide contact intervals without advancing extra simulation.
A final bounded window is supplemental and never replaces the earliest signs.
No episode-wide pixels, video or trajectory are retained by this runner.

`COMPLETE` requires an official finish and native endpoint. `DNF` requires native
termination or exhaustion of the native raw-step horizon. An action, wall-time,
worker, identity or other technical boundary before a native endpoint is
`RESOURCE_CENSORED`; the remaining conditions become `UNEXECUTED`. Per-condition
records retain native flags, official lap/progress, actual charged actions and
successful steps separately. The native TimeLimit counts the 50 warmup calls;
the internal raw reset call is an additional simulator tick outside that counter.
Thus an otherwise uninterrupted 8,200-call limit allows 8,150 post-reset raw calls,
with two raw calls in the last of 2,038 wrapper actions. A shorter research ceiling
must never be reported as an official timeout DNF.

There are no retries, replacement conditions, policy variants or outcome-driven
order changes. Every child is reaped, and resource measurements include telemetry
and IPC. A recurring precursor across different new roads can motivate one future
question. This descriptive DEV sample does not establish a champion improvement,
an independent HOLDOUT result, sealed qualification or official-server parity.

The local pilot illustrates two interpretation limits. No new tile for a short
window can coexist with substantial vehicle movement and a later finish, so that
marker alone does not identify a failure. A contact can also follow a route whose
sampled grid segments satisfy the policy's radial obstacle margin while its
origin connector does not. This is a policy-model discrepancy, not a measured
vehicle-footprint clearance. The same discrepancy also occurs on roads that finish
without contact, so rejection alone does not identify a failure. A signal observed
only just before contact still needs an action-feasibility gate before proposing a
preventive intervention. The pilot leaves the frozen policy unchanged.
