# Limited distance-cap comparison

`ChampionDistanceCapMixin` adds one fixed longitudinal target limit to an inherited pixel policy. It retains the original perception, tracked hazards, HUD speed estimate, route, target lookahead, lateral schedule, steering computation and steering memory. The inherited controller executes once; when the cap binds, gas and brake are recalculated with its original feedback speed and gains. Missing route targets retain the original fallback. Future routes and steering can change as the changed pedals alter the closed-loop trajectory.

Activation uses tracked hazards with positive forward coordinate and center distance within `clip(4 + .35 * pixel_speed, 6, 14) + 2.6 + radius`. Radial buffered clearance is `max(0, hypot(x, y) - radius - 2.6)`. The minimum hazard cap is `min(28, max(4, sqrt(10 * clearance)))`, and the effective target is the lower of that cap and the inherited curvature target. The intervention releases when no eligible hazard remains or the cap no longer lowers the target. These constants are fixed; no sweep is performed. Radial clearance and the creep floor are heuristics, not measured stopping distance or safety guarantees.

The same distance law was previously rejected in a policy using ROI bar-speed feedback because a preserved completion became substantially slower. That earlier comparison remains valid and its rejection stands. The limited comparison here keeps the original champion's HUD feedback, without the ROI correction or lookup table. This tests a different feedback context, not a new distance mechanism, and uses different selected DEV roads.

Before the new environment runs, saved observations from two champion failures were replayed to reconstruct legal tracked obstacle positions and align risk, target speed, pedals and diagnostic physical speed before first contact. Risk was observed early enough for the fixed cap to change pre-contact actions. The original policy was already braking; the post-contact high speed target was excluded from the causal premise. Physical speed remained evaluator-only. The prior baseline runs were reused and charged no new environment actions.

The one candidate was frozen before physics. Both failure cases and one previously completed control were selected in advance and evaluated to official endpoints. A lost control completion would stop unlaunched cases. One selected failure recovered completion, the other remained a DNF with little additional unique progress, and the control retained completion and zero damage while becoming materially slower. The control also exceeded the earlier descriptive time-cost benchmark. Completion and DNF unique progress were primary; fewer contacts alone did not define success.

The result is a limited DEV completion recovery with a time tradeoff. It does not identify late braking as the unique cause of the original contact, establish broad transfer, overturn the earlier rejection, or promote the candidate to champion. No candidate expansion, threshold search, training, HOLDOUT or SEALED evaluation followed. Raw cases, observations, truth, package archives and detailed numeric results remain private.

Validation:

```sh
python -m unittest retry.test_champion_distance_cap -v
```

The tests cover front-hazard eligibility, the fixed envelope and release, unchanged steering and original steering-memory precision, pedal changes only when the cap binds, and unchanged missing-target fallback. Runtime guards checked the original shared package members, frozen sources, actual road/obstacle hashes, and initial physical state and observation equality with the reused baseline.
