# Renderer-visible road diagnostic

This evaluator compares a frozen, privileged full current-camera road mask (A)
with a renderer-visible mask (B). It is an evaluation diagnostic, not a pixel
submission or evidence that a pixel estimator can produce the mask.

A uses physical road sensor quadrilaterals and the already frozen camera and
raster convention. `visible_road_occlusion.py` computes O from the native drawing
order: interleaved road paint and curbs, opaque 16-gon obstacles, four wheels and
wheel stripes followed by hull fixtures, vertical flip, and HUD polygons. Later
road paint clears earlier curb ownership. Wheel stripes remain opaque regardless
of their gray color. State-pixel rendering disables skid particles. HUD bars can
extend above the bottom slab; reward text lies within that slab.

The provenance stencil is rendered at the native resolution, smooth-scaled to
96 pixels, resized to 84 pixels, and binarized at coverage >= 128. B is exactly
`A & ~O`; partial cells use this fixed binning. No RGB black-pixel heuristic or
additional hole filling is used. B false cells conflate occluded and nonroad
cells. Existing road postprocessing, including its morphological close, remains
fixed and can refill an input hole. Removing an input cell therefore does not
alone establish that the planner cannot recover that area.

The original four pixel planes and all policy modules remain unchanged. The
worker receives only the fifth current-camera binary mask, with no pose, ordered
track, future geometry, or obstacle truth. Original speed estimation, obstacle
detection, tracker memory, routing after the road threshold, steering and
throttle/brake coefficients stay fixed. The mask can affect both target path and
target speed. The archived baseline is cloned without changing archive members;
the existing reversible road-threshold boundary belongs to the evaluator.

Before any new native episode, saved scenes are compared with independently
invoked original renderer functions using source-defined opaque provenance.
This checks projection, native raster types, layering, flip, HUD and the fixed
84-pixel boundary. It does not claim bit-for-bit replay of the original RGB
observation when a saved scene lacks wheel phase. Reconstructed saved poses use
Box2D transforms and actual fixture vertices; phase variation is checked on the
saved scenes. A retained full-road mask receipt also matches exactly.

`visible_road_diagnostic.py` accepts a private, precommitted plan with exactly two
specified DEV cases, in a fixed order. A results are reused only after artifact,
source, full initial pixel stack, recorded pose/wheel state, road geometry and
physical obstacle checks. Each B case gets one native episode. Native DNF
continues to the next case; technical or budget censoring stops without retry
and is reported separately. The shared cap is 4,000 wrapper actions, with no
reserve borrowing. Two full native horizons can exceed that cap, so the second
case may be resource-censored. Mask construction is timed separately from actor
IPC and included in the overall wall limit. Action, raw step and reset costs are
reported separately.

No training, coefficient search, protected evaluation, candidate promotion or
automatic experiment extension is part of this comparison. If both B cases
complete, the two selected rescues survive removal of occluded GT road under the
fixed processing. If a B case fails, that loss concerns this representation and
postprocessing; it does not disprove every pixel estimator. Mixed results are
reported by case. Completion alone does not establish safety or generalization.

Private seeds, traces, budgets, artifacts and result receipts stay outside this
repository. The baseline, official participant files and main branch are
preserved.
