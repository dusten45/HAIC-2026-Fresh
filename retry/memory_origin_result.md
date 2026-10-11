# Stage130: coordinate connection fixed, driving unchanged

**Keep 116; stop advancement.** The optical-memory coordinate mismatch was
corrected in one pixel-only candidate. Its memory changed on both selected DEV,
but its complete action and observation streams were exactly equal to 128.
The original 116 clean completion is still lost.

Saved inputs showed that current detections enter memory unchanged at age zero;
there was no stale pre-correction center or double motion applied to a fresh
detection. The direct mismatch was in prediction: 128 centers use the physical
origin `(41.542, 62.4475)`, while the optical tracker projected them into pixels
and back through `(42, 63)`.

The candidate changes only both origins of that affine roundtrip. All other 13
archive members, flow estimation/validity, fallback motion, age/merge rules,
radius, margin, path and control remain unchanged. Translation alone cancels
the origin difference; rotation/scale can produce a difference.

609 saved tracker calls exactly reproduced the recorded states. The 128 prefixes
contained 212 accepted affine estimates. Across the examined affine predictions,
the one-step coordinate effect had median 0.0105m and maximum 0.0312m; these are
prediction differences, not GT-error improvements. Two candidate tracker checks
included an actual retained output change at the first applicable saved input.
GT appeared only in research labels and reconstruction of the saved 129 oracle
trace. The native candidate received official pixels only.

The separate 129 failure window explains the limit: after an exact current-center
update, detection disappeared and retained error grew through **0.269, 0.799,
0.898, 1.077, 1.272m** over ages 1–5. Every step used the unchanged fallback,
holding x fixed and subtracting old-HUD speed × 0.08 from y. The optical-origin
repair does not address that larger drift. No second cause was modified.

| Fixed DEV role | 128 and 130 endpoint | Memory-changed inputs | Route/target/action changes |
| --- | --- | ---: | ---: |
| Rescued by 128 | Complete, 606 actions, 48.460s, damage 0.2 | 117 | 0 |
| Lost by 128 | Crash, 423 actions, damage 1.0 | 72 | 0 |

Both action and observation sequence hashes matched their cached 128 runs.
The intervention was active in memory but did not change driving behavior.
This is no rescue of the observed completion loss and no qualification for
other roads. No retry, threshold tuning or successor experiment was launched.

Cost: **1029/4000 native actions**, 43.115s wall, 36.144s evaluator CPU and 7.078s
actor CPU. Saved work used 609 original and 2 candidate tracker calls, with zero
full-policy, detector, raster or native calls. Baselines were reused. Source and
reset checks passed; both endpoints were uncensored and both actors were reaped.
Cumulative native 608556; research 13444; reserve 84000 untouched. Champion 116,
prior artifacts, official main/Participants and backups are preserved. HOLDOUT
details and SEALED stayed closed; private traces and archives remain private.
No paid resources or extension; authorization ends 2026-10-16T10:01:55Z.

Recipe: [memory_origin_candidate.py](memory_origin_candidate.py).
Exact aggregate results: [memory_origin_result.json](memory_origin_result.json).
