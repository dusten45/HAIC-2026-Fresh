# Clean-process qualification and provisional research status

`qualify_pixel_package` extracts an unchanged policy ZIP into a new temporary
directory and replays one saved pixel episode through `clean_pixel_worker`.
The framework helpers stay outside the policy ZIP. The worker receives only
reset/act operations and full pixel observations; replay files, seeds,
environment objects, and research logs are not worker inputs.

The probe uses an independent isolated-Python CPU process, a sanitized
environment, one-core affinity, immutable package files, package module-origin
checks, and Python audit hooks for file access and environment imports. It
shares the existing cloud host, kernel, interpreter, installed dependencies,
and filesystem caches. Audit hooks are not a full OS filesystem or network
sandbox. This does not establish fresh-machine or official-server parity.

The frozen distance-cap candidate passed the local static package checks,
saved observation/action identity checks, finite output shape/range checks,
and observed cold-start, reset, act, and participant RSS limits on the chosen
existing development stream. No new simulator steps were needed. One cold
start and one stream are observed evidence; repeated cold/reset trials,
candidate-specific fault tests, and all-input resource guarantees are not
established by this probe.

The candidate is designated a provisional completion-first research baseline.
The preceding development and separate small holdout comparisons recovered
completions without observed completion loss, with roughly one-fifth longer
lap times on common completions. Their denominators remain separate, and
the small holdout sample does not establish broad completion probability.
The original champion remains preserved for rollback and speed comparison.
Its formal manifest is unchanged. Under the current application plan, G4 is
the promotion and execution-qualification gate; fresh-machine and exact
official-runtime qualifications remain unproved. G5 is the separate final
sealed confirmation and stays closed. Opening the sealed split is not a
current G4 prerequisite. Older experiment records retain their historical
gate labels. Provisional research status is not final adoption or broad
generalization. No additional holdout or sealed evaluation followed.

One next speed investigation can use already saved development data: align
the two policies' records by road progress, position, and heading, then locate
where cumulative time differences accrue relative to cap engagement,
release, and intervals without tracked hazards. Equal action indices or
equal visited-tile counts are not identical physical states. Cap-active
duration alone is not the causal share of the lap-time cost. This diagnostic
is proposed for later work; no alignment experiment or tuning was performed
in the qualification stage.
