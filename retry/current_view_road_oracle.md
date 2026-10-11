# Current-view road diagnostic

Run `python -m retry.current_view_road_oracle --plan PRIVATE_PLAN_JSON` with a
frozen private plan. This is a privileged input diagnostic, with no submission
candidate, teacher training, parameter search or protected-split evaluation.
The archived baseline and the default policy remain unchanged.

`road_mask_boundary.py` replaces only the first road-threshold array statement
in the connected routing problem and its ridge extractor. Both consume the
same current-screen mask. Every subsequent crop, morphology, distance transform,
clearance, connectivity, path search, target and controller statement stays
unchanged. Original grayscale images still enter speed estimation, obstacle
detection, optical flow and tracker updates. The external worker adds one mask
plane beside the original four pixel planes; pose, road sequence, seed and true
obstacle coordinates never enter the worker.

The evaluator projects physical road sensor quadrilaterals using the current
hull position and heading and the native camera's zoom and translation. Only
polygons intersecting the current viewport are rasterized onto an independent
canvas, using the native polygon operations, vertical flip, 96-pixel smoothscale
and the wrapper's 84-pixel resize. A fixed half-occupancy threshold yields the
binary mask. Curbs are excluded. The mask includes road inside the viewport
that cars, obstacles or display overlays would obscure: that is the explicit
information relaxation. It carries no road identity, order, offscreen geometry
or future route. A separate canvas also avoids the native draw helper's use of
the environment's own render surface.

Before native episodes, feed the original threshold mask through the adapter
and require exact action bytes and tracker/controller/cap state on saved pixel
history. Check the worker protocol and original call counts separately. Verify
world/body/camera coordinates, physical width, rotation and viewport bounds on
saved scenes. This qualifies a boundary intervention without assuming that the
oracle raster and visible RGB threshold are identical representations.

The plan fixes two known DEV failures and a normal completion control. Reuse
baseline results only after checking the archived policy, environment and
saved initial identity. Candidate resets must match the initial four-frame
observation, all saved initial state fields and road/obstacle geometry before
policy reset or action. Report native completion or DNF, unique-tile progress,
failure reason, damage and control regression; resource censoring remains
separate. A rescued failure supports a contribution from the road representation
under this intervention. A remaining failure supports investigating the frozen
downstream components or other inputs. Neither outcome establishes a unique
cause or the value of every possible perception improvement.

In the checked diagnosis, both known failures completed with the privileged
road mask. The normal completion control also completed, with a shorter lap and
unchanged damage. One rescued episode accumulated more damage over its longer
completed route, so completion rescue is not proof that the remaining safety
problem is solved. These selected cases support asking whether pixel-accessible
road-mask or occlusion handling can reproduce the rescue. They contradict a
claim that this current-view road-input intervention offers no completion
benefit on those same failures; they do not establish a population result.

Charge all native wrapper actions and record post-reset and reset raw ticks
separately. Mask generation is timed separately from the worker's IPC latency
and remains part of the episode and overall wall budgets. Saved-pixel adapter
checks make policy calls but do not reset or step a simulator. Retain bounded
event and endpoint windows privately for reproduction and timing checks.
