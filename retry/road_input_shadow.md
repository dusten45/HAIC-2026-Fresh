# Same-state road-input shadow diagnostics

These tools compare the original pixel road input with a privileged,
renderer-visible GT road mask while executing only the original fixed actions.
They support diagnosis and reusable private evidence, not submission or promotion.

`road_input_shadow_worker.py` constructs two independent archived Agent instances.
Functions and controller closures remain attached to their own instance. Before
an actual action, all noncallable data state is copied to the shadow, preserving
array dtypes, float64 steering state, ordered hazard tuples and nested state.
The original pixel tracker/detector runs exactly once. Its updated image, hazards
and route obstacle inputs are copied to the shadow tracker so the shadow consumes
no additional optical-flow or OpenCV random state. Both arms use the original
pixels for speed and other perception. Only the two existing road-threshold
arrays are switched for the GT arm. The actual poststate hash is checked after
the shadow calculation; shadow actions never enter the environment.

Each arm temporarily observes the original ridge, routing problem, route and
target functions, restoring hooks and both road-boundary functions afterward.
A no-op mode substitutes the original pixel mask and requires identical actions,
post-memory and intermediate arrays. A saved-action prefix must also reproduce
the original pixel actions byte for byte. The archive itself is never edited.
The shadow is a downstream comparison with shared actual tracker outputs, not a
second independent tracker trajectory.

`road_input_shadow_capture.py` uses a private prospective plan and shared action
ledger. In recorded mode it checks each generated original-policy action against
the stored float32 action before executing that stored action. Initial pixels,
recorded state, road and obstacle hashes, and available before/after observations
and state are checked. The first mismatch stops capture and withholds the
same-state qualification. Native costs, resets and shadow calls are distinct.
Selected windows retain original four-plane uint8 observations, raw/cropped/
closed road masks, distances, allowed masks, component labels, actual actions,
pre-memory and exact timing. Compact metadata is retained for the replay prefix;
unneeded full-prefix image streams are not produced.

An unavailable original action stream remains a data limitation. An optional
frozen-policy reconstruction needs a separately resolved prospective scope and
a recorded whole-stream action commitment. The commitment is checked after the
complete prefix; directly compared old observations must be limited to the
actually retained old windows. A hash cannot recreate missing pixels.

`saved_road_input_reconstruction.py` can recover selected diagnostic masks from
saved poses and source-defined geometry without an environment or physics step.
It accepts reconstruction only when both full-road and visible-road masks match
already recorded SHA receipts exactly. Missing wheel phase is handled with a
fixed small proxy list and exact mask matching. This establishes the diagnostic
input, not replay of the original RGB observation.

`road_input_shadow_analysis.py` reads saved captures only. It separates false
and missing road relative to the visible-GT reference, the control ROI, boundary,
occlusion vicinity, HUD, components and downstream choices. Region tags overlap
and must not be summed as mutually exclusive causes. Undefined routing labels
are distinct from an empty component result. The captured closed road is derived
as `distance > 0`, matching the original binary distance-transform input.

Raw road thresholds are `image > 0.32` and `image < 0.47`; the image is already
resized grayscale. The original pipeline then crops rows 61 onward, applies a
7x7 close, computes distance and hazard exclusions, selects a connected route,
and chooses a speed-dependent target and smoothed action. Resampled mixed edge
pixels can fall outside the intensity band while a geometrical half-coverage
mask retains the cell. A mask difference can disappear at any downstream stage.
HUD differences below the crop cannot automatically explain routing changes.
A one-step shadow on the original trajectory does not show the accumulated
closed-loop effect, rescue, safety or a unique failure cause. Mask IoU alone is
not a causal criterion. All observations, seeds, numeric outcomes, plots, budgets
and proposal receipts stay in the private research area.
