# Removing raw road-mask cells recovered completion on one DEV condition

A frozen diagnostic intersected the original raw pixel road mask `P` with the
renderer-visible ground-truth road mask `B`. It completed the previously failed
condition. Under this fixed representation and inherited processing, deleting
raw mask cells was sufficient for recovery; adding raw road cells was not
required on this condition.

| Local evaluator result | Original v2, historical | Visible GT, historical | Intersection, new |
| --- | ---: | ---: | ---: |
| Completion | False | True | True |
| Lap time | Unavailable | 68,080 ms | 66,580 ms |
| Unique tiles / total | 97 / 279 | 279 / 279 | 279 / 279 |
| Progress | 34.767025% | 100% | 100% |
| Damage | 0.2 | 0.8 | 0.8 |
| Wrapper actions | 306 | 852 | 833 |
| Collision-marked actions | 1 | 4 | 4 |
| Endpoint | Native `off_track` DNF | Native completion | Native completion |

The 1,500 ms lap difference compares the two completed historical/new GT
diagnostics. The original v2 failed and has no comparable lap time. Completion
was determined by the native `finish_time_s`, not by reaching 100% progress.
The new episode was not resource censored.

The intervention was exactly:

```python
P = ((observation[-1] > 0.32) & (observation[-1] < 0.47)).astype(np.uint8)
C = P & B
```

`C` replaced only the initial road-threshold arrays in `routing_problem` and
`ridge_path`, through the same worker and boundary used in the historical
visible-GT diagnostic. Both functions retained their row cropping, 7×7 closing,
distance transform, and subsequent routing. Closing can refill raw deletion
holes; the no-addition claim concerns the substituted raw mask. Pixel speed
estimation, obstacle detection and tracking, controller laws, and coefficients
were unchanged. Their outputs could change as the new trajectory evolved.

The evaluator generated `B` using the unchanged current-camera renderer
provenance routine. The isolated actor received the original four observation
planes plus `C`; its underlying agent received the four original planes. This
is a privileged GT diagnostic, not a legal deployment candidate. Cells excluded
by `B` may represent occluded road, curb paint, or raster-boundary mixtures as
well as nonroad. Deleted cells must not all be called physical road errors.

Comparison checks matched the original archived policy, unchanged historical
GT generator and boundary, road and obstacle geometry, reset pixels, and
recorded reset body/wheel state. Four saved observations matched the original
raw masks before the run. The historical original-v2 full reproduction was
reused, without new baseline actions. The visible-GT completion is also a
historical comparison, not a newly repeated trial.

The first action difference occurred at action 24 on identical input pixels:
steering changed from approximately `-0.0089623` to `0`, with unchanged throttle.
The next observation differed. The prospectively chosen 1 m position-separation
diagnostic first triggered after action 59, at approximately 1.201 m. These
differences precede the eventual outcome and do not identify which deleted
cells caused recovery. Four collision-marked actions and damage 0.8 remain;
completion recovery is not evidence of improved safety.

All 833 actions, 834 grayscale frames reconstructing four-plane observations,
and 834 mask inputs including reset were retained privately. Every raw mask
was recomputed from its observation, and every intersection passed exact
`C == P & B` and subset checks, with zero added raw cells. Full observation
hashes, actions, state continuity, and single component calls passed independent
review. The historical failed brightness candidate remains closed.

One native episode consumed 833 wrapper actions, 3,331 raw step ticks, and 51
reset ticks. Episode wall time was 45.892 s, including 12.658 s of GT mask
generation. Measured wrapper-step time was 25.311 s including observer work;
actor CPU time was 5.384 s. Maximum action latency including IPC was 20.150 ms,
and peak actor RSS was 63.781 MiB. Research allowance remaining is 2,696 actions;
the 84,000-action final reserve was untouched.

The prospective limits were one episode, at most 2,000 new actions, a 3,529-action
research pool, and 25 minutes overall. No training, threshold search, protected
evaluation, promotion, or further native episode was performed. This result is
sufficiency evidence for the tested condition and processing, not a population
claim or proof that the deletion rule is extractable from legal inputs.

Next question, not executed: would recovery persist if curb, occlusion, and
raster-boundary mixtures were retained and only the remaining cells deleted?

The general runner is `retry/road_deletion_diagnostic.py`. Private plans, seeds,
scenes, and original/derived arrays remain outside the public repository.
