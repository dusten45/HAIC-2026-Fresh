# Frozen road-mask intervention

The worker applies a frozen pixel-derived road mask at the existing ridge and
routing threshold boundaries. It loads the unchanged champion archive and keeps
the original obstacle detector, tracker, speed estimator, controller parameters
and action pipeline. No distance limiter or curve wrapper is installed.

Qualify the new boundary using saved DEV observations before native evaluation:
the original-threshold control must reproduce archived champion actions, full
input observation hashes must match, and detector/tracker inputs must remain
equal between controls. Record the first path, target and action differences.
Different outputs alone do not establish that either target is incorrect.

Resolve case names against the seed registry and exact road/obstacle identities.
Similar labels from different stages are not interchangeable. Reuse a historical
baseline only with its actual archive, environment, protocol, initial observation
and saved reproduction evidence. Do not repeat a valid baseline native run.

`mask_only_dev.py` executes two separately preregistered DEV questions: failure
improvement and preservation of an existing success. Both use the same frozen
candidate. A normal first failure does not suppress the second condition.
Technical invalidity stops further execution; a nonterminal resource cap is
reported separately. Neither two DEV results nor shadow replay qualifies a
candidate for promotion or proves final submission equivalence.

Passive evaluator records add no policy, model or simulator calls. The separate
`record-receipt.json` reports their actual frame/trace counts; the reused endpoint
function's own zero recording counters describe only its internal recorder.
Plans, model weights, seeds, observations, traces and results remain private.
