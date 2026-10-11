# Whole-prefix road upper-bound validation

`build_road_upper_candidate.py` creates a separate private policy archive. Only
the existing upper road threshold in `routing_problem` and `ridge_path` changes;
all other archive members and source statements remain byte-identical.

`road_band_saved_comparison.py` first qualifies saved renderer masks against
their previous full/visible mask SHA receipts. Original images come from the
retained pixel stream, not reconstructed RGB. A no-op replay must preserve saved
actions, intermediate arrays and post-memory. The subsequent comparison starts
in a fresh worker: `Agent.reset` need not clear every diagnostic field left by a
previous episode. Reusing one process can therefore violate constructor memory
even when the no-op actions themselves were exact.

The worker uses original pixels, one actual tracker/detector call and copied
tracker outputs for both arms. Before every substitution it restores the exact
actual pre-memory and verifies that the shadow cannot mutate actual post-memory.
Only the two road masks are substituted with masks computed from the candidate
pixel intensity band. The separate archived candidate uses that same band.
These outputs are one-step comparisons on the original trajectory; they do not
form an executed candidate trajectory or carry shadow memory into the next row.

The prospective whole-prefix gate measures false and missing road against the
visible-GT reference in the control ROI and before the row-61 crop. Full-frame
HUD differences are reported separately. Four-connected labels of identically
postprocessed GT allowed space identify newly joined reference component pairs;
newly start-reachable reference-false/disallowed cells are a separate proxy.
Neither metric proves physical danger. Target distances use common defined rows
with explicit missing-target counts. First path, target, inherited/effective
speed, action and controller-memory differences are distinct events.

Only reduced image error, nonincreased false positives, no added reference
connections/false reachable areas, exact replay/isolation and a control effect
before the original first damage permit one native candidate episode. Gate
failure permits no native episode. Source/protocol failures are reported and
recovered separately from candidate failures. No threshold sweep is implied.

The registered single upper-bound change `0.47 -> 0.52` failed this gate across
218 saved decisions. Control-ROI missing-cell occurrences fell from 3,645 to 397,
but false occurrences rose from 153 to 565; false positives worsened in 120 rows.
There were no new reference component pairs, while new reachable raw-false cells
appeared in 15 rows and reference-disallowed cells in 119 rows. The first action
effect occurred before original damage. These representation tradeoffs withheld
the native run: new environment resets/actions were zero. This rejects the
specified upper-bound change under the registered gate, not visible-road
information improvement generally, and establishes no unique collision cause.

Original documents, observations, seeds, masks, scene geometry, detailed row
traces, policy archives and personal research receipts remain private. This
record contains only the general protocol and aggregate failure outcome.
