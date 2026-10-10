# Aggregate-only frozen paired evaluation

`python -m retry.aggregate_only_episode --plan PRIVATE_JSON --case FIXED_CASE
--arm FROZEN_ARM` runs one predeclared episode. The private plan fixes source
hashes, policy archive and member hashes, case identities, official native
endpoint limits, the authorization window, and a shared action budget.

Each policy runs in a separate resource-limited worker receiving only the
operation and the current full pixel observation. The worker calls the
unchanged policy's reset or act method once per request. It exports actions
and process cost counters, with no diagnostic hooks or simulator imports.

The evaluator checks matching initial observation, state, road, and obstacle
hashes across the two arms. Every action is charged before the simulator
step. Official finish time determines completion and lap time; a resource
stop before an official endpoint remains censored. A tile count does not
override an official completion flag.

Private outputs contain endpoint metrics, official finish/termination
scalars, cost counters, and rolling action/observation hashes. No images,
per-step action arrays, trajectories, or failure videos are saved. Rolling
hashes permit a later identity check but cannot reconstruct observations.
Parallel elapsed wall time is separate from summed episode times, and
process RSS maxima are not a combined simultaneous memory peak.

The fresh holdout evaluation registered a small new cohort under existing
seed, road, and obstacle-lineage exclusion rules before any performance was
observed. Previously exhausted pools were preserved. No predeclared
difficulty distribution was available, so there was no difficulty, length,
performance, or visual filter. Frozen original and candidate policies were
evaluated once per arm and case, with fixed case order and bounded
concurrency. The outcome contract prioritizes new and lost completions,
reports common-DNF and common-completion evidence, and keeps lap and damage
costs descriptive. There is no new post-outcome timing threshold, automatic
retuning, or champion promotion. Sealed data remain unopened.

The frozen candidate recovered completions on the newly registered geometry
cohort without losing an original-policy completion. Common completions took
longer, while their observed damage decreased. The predeclared decision is
to keep this as promising evidence from a small sample, with the time cost
reported alongside the completion gain. It is not an automatic promotion or
a reliable estimate of completion probability across the wider domain.
The evaluation ended after the fixed paired runs and one aggregate look;
no individual failure visualization, trajectory inspection, or retuning
followed. Private case identities and exact metric evidence remain outside
the public repository.
