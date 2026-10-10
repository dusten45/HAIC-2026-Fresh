# Frozen serial paired verification

`serial_paired_holdout.py` runs each predeclared condition as baseline followed by candidate, with one active simulator. Both packages, source hashes, initial observations, road geometry and physical obstacle positions are checked. The participant receives only the four-frame pixel observation through the existing aggregate-only worker.

Before execution, the private contract fixes registration and identity exclusions, condition order, action and time limits, stopping rules and the decision criterion. Completion flags are inspected only to enforce the predeclared stop: the first valid baseline completion lost by the candidate prevents all remaining launches. Missing or censored endpoints stay inconclusive. Conditions are never replaced or retried.

A single final aggregate distinguishes new completion, lost completion, common completion, common DNF and unexecuted conditions. Equal completion counts require at least two common completions. Promotion-review evidence requires both a negative median paired lap difference and a mean lap ratio below one. Each difference, the worst positive delay and common-DNF progress remain visible in the private report. Damage is a separate warning. There is no extra percentage threshold.

Only endpoint statistics, cost measurements and rolling reproduction hashes are saved. No video, trajectory rows or action arrays are exported. Completion gate checks during execution are separate from the single final aggregate look. Protected registration data and per-condition outcomes remain private.

The global action limit is authoritative even when the sum of native episode bounds is larger; an exhausted limit censors the affected evaluation. The absolute experiment deadline prevents further steps. This verification can support promotion review, while a fresh independent execution environment, official runtime enforcement parity and candidate-specific fault/reaping qualification remain separate G4 requirements. SEALED is the closed final G5 gate.

The fresh paired verification preserved all baseline completions and met both preregistered lap criteria, supporting promotion review. One condition was slightly slower. There was no candidate damage warning. This small sample does not establish broad completion reliability; the formal champion and the closed SEALED pool remain preserved.
