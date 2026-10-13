# 270: On-policy pixel scalar pace distillation — rejected0/8

One affine scalar model is fitted to240 inputs and frozen GT target labels. All eight actual evaluations fail, including five fit roads, unlabeled N2 and two unfit247 screens. No technical error or budget censoring occurs. Do not narrow the clamp, change gain or refit after these results; champion240 remains unchanged.

| Case/cohort | Reused240 completion time | Candidate source retirement/action | Damage |
|---|---:|---|---:|
| O0 fit |23.66s |off_track147 |0.2 |
| O2 fit |20.98s |crash141 |1.0 |
| N0 fit |23.62s |off_track134 |0 |
| N1 fit |17.08s |off_track131 |0.8 |
| N2 no valid teacher labels |21.56s |off_track155 |0.2 |
| N3 fit |18.76s |off_track325 |0.2 |
| S0 unfit screen247 |22.02s |off_track173 |0.4 |
| S1 unfit screen247 |19.22s |off_track151 |0.6 |

Cohorts: fit0/5 complete,N2 0/1,screens0/2; actual DNF8,censored0. `off_track` is official no-progress retirement, not necessarily geometric departure from all road wheels. All runs finish below their650-action budget allocation, so allocation does not cause any reported failure.

## Labels and one fixed fit

Reuse the five existing240 trajectory caches O0/O2/N0/N1/N3, with actual240 pixels and original16 image-derived features. No teacher-run pixels enter training. No new baseline materialization or teacher rollout occurs. N2 is excluded from labels because269's fixed solver did not provide a feasible path; it receives no fabricated target and remains mandatory in evaluation.

The materialization `actual[i]` is **post-action**, whereas pixels/features[i] are pre-action. Use snapshot1 for the first state and actual[i−1] afterward. Current240 pose is mapped onto the frozen oracle path using its same forward cursor/segment projection. Query the fixed268 speed profile with squared-speed interpolation and the existing lap-wrap branch. Pose/index are label-generation data only.

Label is `log(teacher_target/240_nominal_target)`. Absent/nonpositive denominators and nonpositive teacher targets are explicitly excluded. Initial standing-start samples are excluded on all five roads: the teacher entry target is zero and its separate acceleration feedforward cannot be encoded by a scalar P goal. No artificial floor/target is created. Runtime uses validated240 on its initial valid action and on absent/zero goals.

Valid counts295/262/295/213/234, total**1299**; five standing-start exclusions, no other exclusion in these five caches. Fit one17-coefficient affine scalar ridge,lambda1,unpenalized bias, exact frozen231 TRAIN mean/std. Each road has equal total weightN/5; normalization is not refitted. Weighted training log RMSE0.203. Final log pace is restricted **only** to TRAIN min/max−1.8756/2.4477, ratios0.1533–11.5611. This absolute-target ratio is much wider than the small relative condition correction268/1.5; no extra cap is retrospectively substituted.

## Geometry and label limits

The inputs match240's on-policy distribution, but the expert route/steering do not. Projection distance median2.40m,p954.70m,max8.22m. Median absolute-curvature-magnitude mismatch0.00729/m,p950.04561/m. Student curvature is its pursuit command geometry, while teacher curvature is the fixed GT path's three-point geometry; their meanings differ. Teacher sign is converted to the student's right-turn convention for reporting.

O0 examples:

| Action | Student nominal goal | Teacher goal | Student pursuit curvature | Teacher path curvature | Projection distance |
|---|---:|---:|---:|---:|---:|
|13 |45.00m/s |57.60m/s |0 |−0.00043/m |0.90m |
|65 |45.00m/s |150.29m/s |0 |+0.00063/m |2.58m |
|117 |19.64m/s |65.42m/s |+0.06224/m |−0.00223/m |2.94m |

Thus predicting a teacher speed does not establish a reachable speed under the student's current steering/recovery geometry. Whole-map future braking information can also exceed current observation support. These limits remain in the labels; they are not hidden by inventing a new target or filtering failed student runs.

## One prediction, one goal change, original downstream flow

Use264's explicit nominal-goal override plumbing. First compute the **original240 nominal16 features** with a controller dry-run that does not update memory. Predict log pace once from those original features; multiply the original nominal goal. Then make one actual nominal-controller call, updating steering memory once, and derive candidate16 features from its new goal/own nominal pedals. The unchanged affine head, exact global scales, residual/action clips then apply. No recursive inference or mixing teacher features into actions.

The original cap45 constructs the base goal/label denominator before multiplication. Corrected goals can exceed45; no extra post-pace target cap is added. Original0.08/0.04 P calculations and0.5 nominal-pedal clips, head±0.5 and final0..1 clips remain. Source steering, path extraction, hazard tracker and nominal memory rules stay240. Fallback returns its validated behavior, not cached future actions.

Forty cached baseline/identity/candidate triples verify full identity action/features/memory and match cached240 original features exactly. Candidate steering/memory match on the same observations; only final feature6/14/15 change, and pace is computed at most once. Synthetic absent-road fallback matches240. Every actual pedal is reconstructed bit for bit through the old head/scales/clips; every active scalar is reconstructed from its logged original features. Pipeline consistency passes despite performance failure.

The participant runs in the existing clean native/Python read sandbox, oneCPU/thread, grayscale-only reset/act IPC. No GT state, mapping, road ID, teacher labels or simulator imports enter action generation. Package/loaded-module hashes, limits and actor reaping pass. This is same-host research boundary verification, not new remote official qualification.

## Actual behavior and interpretation

Median active pace is4.20/1.86/2.02/1.52/4.94/3.01/6.93/2.33 in table order. Several cases hit TRAIN's11.56 upper ratio; no narrower clamp is chosen after failure. Corrected-goal/head inputs and then closed-loop observations can depart strongly from the frozen head's original capped-goal training distribution. Missing-target fallback becomes common after tracking loss.

On-policy input alignment is verified; it does not make off-policy teacher goals compatible with the student path. Geometry mismatch, unobservable future context, head distribution shift and changed closed-loop data are plausible failure contributors, not an isolated single-cause proof. A small imitation training loss cannot certify safe/fast control. This one absolute-goal distillation pilot provides no pixel-planning impossibility result.

Keep240. Any separately requested future trial should first repair label compatibility with the student's steering/observable geometry rather than silently shrinking the clamp or increasing model complexity. No alternate label, gain, feature grid, encoder, model selection or post-failure run is executed here.

## Cost and preservation

New **1357 native** over8 episodes, baseline materialization0;5428 actual raw step ticks +408reset ticks. Cached240 baseline results reused. Evaluation59.37s, episode wall59.21s, actor CPU8.42s. Label construction4.287s, one ridge fit0.000515s;122 offline preflight actor calls.667 active scalar predictions: median0.041ms,p950.129ms,max1.583ms. Full per-case agent/IPC timings are retained; local action deadline passes.

Model physics queries0,new geometry solves0,new paid resources0. Cumulative832144; research remaining3856; reserve84000 untouched; B920000. N2/screen coverage gaps and all failures retained. Champion, main, Participants, backups, HOLDOUT and SEALED unchanged. Learned model/ZIP, labels, full observations/trajectories and receipts remain private; public artifacts contain small code and aggregate evidence.
