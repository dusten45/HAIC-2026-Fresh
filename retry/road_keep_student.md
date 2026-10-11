# A small grayscale keep classifier recovered completion on the known DEV condition

One fixed student learned the useful teacher keep/delete convention from an
already saved trajectory. Its native execution received only the official
`float32 (4, 84, 84)` grayscale observation and completed the condition. It used
no runtime RGB, environment object, GT, seed, action index, world coordinates,
or saved-trajectory lookup.

| Local evaluator outcome | Original v2, historical | Deletion teacher, historical | Frozen student, new |
| --- | ---: | ---: | ---: |
| Completion | False | True | True |
| Lap time | Unavailable | 66,580 ms | 66,480 ms |
| Unique tiles / total | 97 / 279 | 279 / 279 | 279 / 279 |
| Damage | 0.2 | 0.8 | 0.8 |
| Collision-marked actions | 1 | 4 | 4 |
| Wrapper actions | 306 | 833 | 832 |
| Endpoint | Native `off_track` DNF | Native completion | Native completion |

Completion uses the native finish timestamp. The original DNF has no comparable
lap time. The 100 ms student/teacher difference is descriptive for these single
runs and does not establish a speed advantage. Damage 0.8 remains.

The learner, features, sampling, class weights, and checks were fixed before
fitting. The installed OpenCV decision tree was used instead of adding an
unavailable dependency. There was one fit, no model selection or retuning:
maximum depth 5, at most 32 leaves, minimum sample count 64, no cross-validation,
surrogates, or pruning. Delete samples had weight 4 and keep samples weight 1.
The fitted model has 45 nodes and 23 leaves and occupies 8,762 bytes.

The 21 fixed features describe current-frame grayscale intensity, local 3×3
and 7×7 means, standard deviations and contrasts, gradients, Laplacian, eight
neighbor contrasts, and the local fraction of the existing pixel road mask.
The fitted tree uses 11 of those features, including neighborhood, contrast,
and edge information. The original road brightness thresholds were unchanged;
there was no brightness-threshold sweep.

Training used all 833 pre-action observations from the saved teacher trajectory,
with up to 256 deterministically selected original-road cells per frame:
213,248 samples, including 5,997 teacher-delete labels. The other saved
trajectory supplied 42 aligned observations. Two observations duplicated the
training trajectory exactly, including their effective latest-frame input;
they were excluded, leaving 40 validation observations. No adjacent-frame random
split, new training rollout, or synthetic replacement for missing data was used.
Both trajectories share the same geometry, so this is not independent-geometry
generalization evidence. The validation frames are correlated observations.

Validation measured agreement with the teacher convention, not absolute physical
road truth. The confusion counts were 1,280 correctly deleted, seven missed
deletions, two incorrectly deleted teacher-keep cells, and 50,624 correctly kept.
Delete precision was 99.844%, delete recall 99.456%, keep recall 99.996%, and
balanced accuracy 99.726%. None of the 40 output masks was unchanged or empty.
There was no requirement that every frame proxy improve. The teacher labels can
include curb, occlusion, and raster-boundary effects; supervised private research
was authorized, while competition training eligibility remains unverified.

The frozen actor loaded a read-only learned model and feature implementation.
Its sole request observation had four grayscale planes. It computed
`C = P & predicted_keep` internally and substituted `C` at the same two raw-mask
sites as the teacher. Cropping, 7×7 closing, routing, obstacle handling, speed
estimation, and controller laws remained fixed. No raw road pixels were added;
the inherited closing operation can refill deletion holes.

All 832 actions, 833 grayscale frames reconstructing the four-plane observations,
and 833 mask calls including reset were retained privately. Independent checks
verified hashes, alignment, subset masks, single component calls, model identity,
read-only assets, and one observed native endpoint. The wire check used one
policy reset and one action without an environment. The native run made no new
teacher or GT-mask-renderer calls.

The first action change from original v2 was at action 24 on identical pixels,
with the next input differing. Relative to the teacher, the student first chose
a different action at action 29 on identical input, and the next input diverged.
It therefore completed its own closed-loop trajectory. The raw deletion rate was
2.758%, compared with 2.767% for student predictions on the training trajectory
and 2.470% on the validation trajectory. The largest aggregate feature-mean
shift was 0.187 training-frame standard deviations. These descriptive values
do not measure teacher-label error on new states; no new GT labels were queried.

Pure fitting took 1.470 s CPU/wall time; cache preparation, fitting, and offline
validation together took 3.744 s and peaked at 244.797 MiB. The one native episode
took 29.857 s, charged 832 wrapper actions, and advanced 3,326 raw step ticks plus
51 reset ticks. Actor CPU was 6.050 s and peak RSS 63.691 MiB. Maximum action
latency including IPC and student inference was 22.848 ms; student-only inference
was 1.334 ms median and 6.328 ms maximum. Workers were reaped.

Research allowance remaining is 1,864 actions; the 84,000-action final reserve
was untouched. The champion, previous failed hypotheses, original files,
Participants, and backups were preserved. HOLDOUT and SEALED were not opened.
The learned model, raw data, and private records are not published here.

Next question, not executed: does this frozen student preserve completion
relative to original v2 on geometry absent from training and validation?

General code: `road_keep_student.py`, `road_keep_student_train.py`,
`road_keep_student_worker.py`, and `road_keep_student_probe.py`. The run requires
the private frozen model and plan; no automatic rerun or extension is scheduled.
