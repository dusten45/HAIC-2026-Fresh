# One-hop pixel support falsification

The single legal cue admits an expanded-band pixel only when it directly touches
the original raw road mask in one of four directions. `road_supported_recovery`
uses current pixels only: `P47 | ((P52 & ~P47) & neighbor4(P47))`. New pixels never
become expansion seeds, and neither GT nor material ownership enters the cue.
Original crop, closing, distance, hazard exclusion, route and controller remain
unchanged in the isolated same-state shadow.

Evaluation distinguishes full road A, source material coverage O, and visible
road B. Saved full/visible masks and the complete binary occlusion mask must
match existing native SHA receipts. Material ownership comes from saved poses
and source-defined geometry without an environment reset or physics step.
Partial material coverage is uncertain even below the binary half-coverage
cutoff. The clear nonroad subset excludes material coverage, a fixed one-pixel
road-boundary neighborhood and HUD. Binary reference nonroad and that stricter
subset are reported separately. A material-covered road is not relabeled as
known nonroad. Source material tags may overlap.

Across 218 saved decisions, the upper-bound expansion added 2,235 cells marked
false by visible GT: 1,070 HUD, 148 material/paint uncertainty and 1,017 boundary
mixtures. In the control ROI, the 412 added false cell occurrences were 57
material uncertainty and 355 boundary mixtures; clear nonroad examples were
zero. The 61 newly reachable visible-reference-false cell occurrences all
overlapped curb paint coverage, with no car/obstacle-owned examples. They do not
establish a newly dangerous physical connection. The preceding expansion's
registered failure remains unchanged.

The one-hop cue retained all 3,248 recovered visible-road cell occurrences:
control-ROI missing road fell from 3,645 to 397. It retained the same 355 false
boundary mixtures and reduced material false occurrences from 57 to 39. Clear
nonroad errors and new clear-nonroad reach were zero, but there are no positive
clear-nonroad examples to establish discrimination. Newly reachable
visible-reference-false paint cells fell from 61 to 44; broader material-uncertain
reach remained at 57 cell occurrences. Average reference-target error improved,
while four decisions materially worsened. The cue therefore failed its frozen
admission conditions and produced no candidate for a native run.

This closes the exact tested brightness expansion plus one-hop support cue.
It does not reject every pixel or memory-based distinction, establish physical
safety, or turn one-step shadows into a candidate trajectory. Same support values
occur for recovered road and boundary/material mixtures; support alone is an
insufficient representation here. Threshold sweeps, fitting, new native runs and
protected evaluation were absent. General code and these aggregate results may
be public; original documents, images, masks, scene geometry, archives, detailed
traces and personal receipts remain private.
