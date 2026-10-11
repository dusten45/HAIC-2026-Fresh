# Stage131: fallback speed drift reduced, completion loss remains

**Keep 116; stop advancement.** One candidate replaces legacy-HUD speed with
the existing fixed-HUD decoder only in fallback memory displacement. Optical
tracking, x, the 0.08s interval, lifetime/association, margin, route and control
source are preserved. The other 13 archive members are byte-identical to 130.
The native candidate receives official pixels only.

The fixed five-step saved window starts from a shared age-zero center in a
research oracle trace. Every step uses fallback. Actual sequential tracker
functions reproduce the original state exactly; x/radius/age/count and branch
stay fixed. All five errors improve: mean **0.863→0.448m**, maximum
**1.272→0.792m**, above-one-horizontal-pixel count **4→1**. This passed the
preregistered saved gate. GT supplies research labels and that common starting
history; it is absent from the native candidate.

Speed RMSE against the current physical speed falls **2.410→0.789m/s**. The
observed interval is 0.080s, but the car rotates by −0.239rad and x remains
fixed. Endpoint speed sampling, acceleration/quantization and omitted rotation
leave residual error. The intervention establishes a speed contribution to
saved drift; it does not identify a unique crash cause.

| Frozen DEV role | Cached 130 | Candidate 131 |
| --- | --- | --- |
| Rescued by 128 | Complete, 606 actions, 48.460s, damage 0.2 | Complete, 607 actions, 48.500s, damage 0.2 |
| Lost by 128 | Crash, 423 actions, damage 1.0 | Crash, 423 actions, damage 1.0 |

The failed DEV has 23 changed memory inputs but exactly the same full action and
observation streams as 130. The completed DEV changes behavior, finishes 40ms
slower, and its first contact precedes both memory and action divergence. Later
perception/route differences follow the changed trajectory. No completion is
rescued versus 130; the original 116 clean completion remains lost. The
advancement gate fails. No retry, tuning or successor experiment was launched.

Cost: **1030/4000 native actions**, 46.370s wall, 38.904s evaluator CPU and
7.625s actor CPU; raw step/reset ticks 4118/102. Saved work used 5 original and
5 candidate tracker calls, 10 decoder calls, and zero full-policy, new detector,
raster or native calls (0.235s wall). Cached baselines were reused. Runtime/reset
checks passed; both endpoints were uncensored and actors were reaped.
Cumulative native **609586**; research **12414**; reserve **84000** untouched.
116 and prior artifacts remain fixed. HOLDOUT details and SEALED stayed closed;
private data and archives remain private. No paid resources or extension;
authorization ends 2026-10-16T10:01:55Z.

Recipe: [tracker_feedback_candidate.py](tracker_feedback_candidate.py).
Aggregate results: [tracker_feedback_result.json](tracker_feedback_result.json).
