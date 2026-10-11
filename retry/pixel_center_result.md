# Stage128: pixel center correction fails the completion gate

**Keep 116; stop advancement of this candidate.** The one source-derived pixel
center calculation passed its fixed saved-error gate and rescued the selected
failed DEV. It also lost a previously clean completion. The preregistered rule
rejects any completion loss. Runtime validation passed; advancement failed.

Only the existing obstacle center inverse changed, from origin `(42, 63)` to
`(41.542, 62.4475)`. The native 1000×800 camera origin `(500, 200)`, vertical flip
to `(500, 599)`, and pixel-center mapping `(raw + .5) * scale - .5` give these
constants. The existing scales 1.3608 and 1.701 remain. No constants were fitted
to DEV coordinates. Detector support, count, order, radius, path, tracker, route
and control remain unchanged; the other 13 archive members are byte-identical.
The candidate receives only official pixels, with no GT or identity assets.

The saved cohort was fixed before measuring candidate error: both original DEV
trajectories, 203 detected frames, 219 detections, and 176 uniquely matched current
visible centers. The 43 unmatched detections have no reliable GT error labels.
Brightness weighting moved the same component centroid by at most 0.01055 pixel,
far below the source-derived origin displacement `(0.458, 0.5525)` pixels.
169/176 centroids were already fractional. Residual raster/mask error remains;
the formula does not establish exact raster kernel phase.

| Matched cohort | n | Mean error, m | p95 error, m | Maximum error, m |
| --- | ---: | ---: | ---: | ---: |
| Selected failed DEV | 46 | 0.519 → 0.176 | 0.716 → 0.328 | 0.749 → 0.354 |
| Previously clean DEV | 130 | 0.487 → 0.140 | 0.667 → 0.299 | 0.775 → 0.405 |
| Pooled | 176 | 0.495 → 0.150 | 0.682 → 0.311 | 0.775 → 0.405 |

Both roads and the pool passed the predeclared mean/median improvement and
p95/maximum/one-pixel-tail nonincrease gate. Four individual rows worsened;
the largest increase was 0.1742m. One-pixel exceedances fell from 3 to 0. GT was
used only for research labels. Two isolated saved-pixel reset/act checks passed.

| Fixed DEV role | Cached 116 | Pixel candidate |
| --- | --- | --- |
| Selected failure | Crash, 181 actions, damage 1.0 | Complete, 606 actions, 48.460s, damage 0.2 |
| Previously clean completion | Complete, 548 actions, 43.820s, damage 0 | Crash, 423 actions, damage 1.0 |

New completions 1, lost completions 1, common completions 0. No common-completion
lap comparison exists. Both native runs reached normal uncensored endpoints,
matched the recorded reset identities, and reaped their actors. The cause of
the regression remains unresolved: saved current-center error does not measure
unmatched detections, new states or retained-track/path coordinate consistency.
Path and tracker origins still use 42/63. There was no retuning or retry.

Cost: **1029/4000 native actions**, 45.988s wall including records, 38.759s
evaluator CPU and 7.343s actor CPU; no baseline rerun. Saved work used 203 pure
detector calls, 203 label contexts, 182 label raster passes, and 2 policy reset/act
calls, with no native actions or full-scene render. A dependency preflight
failure occurred before any calls and was repaired using the frozen archive.
After a connection alert, the same environment and completed report were
confirmed; no duplicate run or environment move occurred.

Cumulative native 606979; research 15021; reserve 84000 untouched. Champion 116,
original 126/127 artifacts, official main/Participants and backups are preserved.
Protected HOLDOUT details and SEALED stayed closed. Private frames, labels,
seeds and archives remain private. No successor experiment was launched.
Authorization ends 2026-10-16T10:01:55Z, with no paid resources or extension.

Exact aggregate metrics: [pixel_center_result.json](pixel_center_result.json).
Reproducible candidate recipe: [pixel_center_candidate.py](pixel_center_candidate.py).
