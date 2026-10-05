# Joint Local Path and Speed Distillation

Read COMMON.md first. User authorization 2026-10-05T09:21:49Z creates this
independent implementation/training/evaluation line. Preserve champion ZIP,
frozen repaired V7, local_plan/, and its single-point/frozen-v14 experiment.
No official submission or confirmed-model replacement is authorized.

## Closure Decision

**CLOSED / NOT_PROMOTED.** The 2026-10-05T14:05:57Z authorization publishes only
the reporting code, regression test, and closure documentation. It does not
reopen training, change the candidate, or authorize a competition submission.

- **Conditional timing evidence:** on exactly nine shared finished road settings
  spanning three geometries, champion/actual-plan-tracker means are18.646667/
  15.311111s (paired difference-3.335556s). This is privileged-plan diagnostic
  evidence, not learned-student speed or superiority over all15 attempts. Local
  Track4 laps14.76/15.00/15.70s remain4.26/4.50/5.20s above the explicit10.5s goal.
- **Learned-candidate failure:** final student0/15 episodes and0/15 roads on
  three geometries; champion13/15 and matched actual-plan tracker10/15. CPU
  compatibility and low training error do not overturn the rejection.
- **Checked connection segment:** saved six-point teacher plan -> diagnostic
  normalized target -> model output -> tracker input/action, on ID1/32 PRE0-49.
  Recorded coordinates, time, masks, and point/speed pairing align. PRE38 meets
  the declared opposite-correction criterion; it is not a proven first unsafe
  causal action. No reproducible correction to this connection was identified.
- **Unverified upstream segment:** the original dense selected path/profile was
  not saved, so dense-to-six-point resampling was not independently reconstructed
  in the closure check. No whole-exporter proof, hidden-information-gap cause,
  or multimodal-averaging cause is claimed.

Weights, generated runs, secrets, driving/training implementations, and other
research lines are outside this reporting-only commit. Existing local artifacts
remain under ignored runs/ and are referenced below rather than committed.

## Contract

- Student inputs: official pixels, short causal observation history, and its
  actually issued actions only. Predictor outputs paired local geometry/speed;
  explicit tracking uses pixel-derived motion estimates by default.
- New code lives in joint_plan/. Environment files and frozen teachers remain
  unchanged. Privilege is confined to label export and named diagnostics.
- V7 is controller_for('v7',190)(base). Extract CURRENT actually selected path
  and corresponding speed profile at the PRE-observation state. Sample cumulative
  path distances [0,3,6,10,16,24] in simulator length units. Columns are
  (forward,right,speed), relative to current hull pose; path origin and branch
  provenance must be recorded. Never invert motor commands into targets.
- Unsupported/stale emergency targets and unrelated predicted trajectories are
  masked and counted, not substituted. A persistent teacher observes every
  executed PRE-state; command-dependent memory must reflect issued actions.
- Normalization scales are (24,24,80). Eight causal images and preceding issued
  action3 history are the initial one-configuration supervised model inputs.
- Frozen official conditions: no domain randomization, physical obstacles,
  skip4/warmup50/stack4, external2000/raw8200 limits, complete true episodes.

## Stages and Roads

1. Minimal exporter and pixel-state tracker; pilot TRAIN IDs1-3 x101-102 only.
   Reuse existing data/replay where aligned plans can be recovered. No initial
   bulk collection. Check early CPU save/load/inference.
2. Genuine current V7-plan-assisted FULL episodes with intended tracker and
   pixel state. True-state diagnostics are separate. Fix repeatable interface,
   tracking or estimation failures; all-development-road success is NOT required
   before fitting. Retain all failures and branch masks.
3. Train one small model on pilot data first. Expand only on declared TRAIN
   IDs1-5 x11-30 if needed; reserve geometry28-30 for offline checks if expanded.
   Prioritize valid labels around learner failures on TRAIN roads, not development
   evaluation labels. Preserve negative candidates and configuration identity.
4. Compare teacher-plan tracker, learned-plan tracker and exact champion on
   DEV IDs1-5 x31-33:15 configurations/three geometries. These are exposed.
   Keep tracker/state estimator identical between the two plan arms. Report
   complete finishes, finished lap times, collision/off-track/stall failures.
5. Only for a promising frozen candidate, predeclare previously unused geometry
   after checking exposure. Never open protected seeds34-35/38-40 or private roads.
6. Package candidate separately and measure CPU cold initialization/reset/act,
   current-executable peak memory, save/reload parity and official compatibility.
   Deadline:2026-10-06T23:59:59+09:00. No official submission/confirmation.

## Interpretation

Visible prefixes may encode hidden-map anticipation; cropping is not a solution.
Inspect relevant pilot failures/labels and revise supervision if implicated,
not model scale or global Q/cost learning. Training loss is not driving success.
Track4 18.4s/rank6 remains user-reported, not a matched benchmark.

## Execution History

- Implemented exporter, issued-command teacher adapter, pixel-state tracker,
  250242-parameter CNN/action-history predictor, trainer, runner and packaging.
- `runs/joint_plan_champion_dev_v1`:13/15 finishes,15 roads/three geometries;
  mean finished lap18.515s, two collision episodes. This is newly measured under
  matched local conditions, not the user's Track4 report.
- `runs/joint_plan_pilot_export_v1`: deterministic replay of existing six TRAIN
  episodes finishes6/6 (two geometries);1141 transitions,1116 supported plan rows.
  All replay images/endpoints match; no new large corpus was collected.
- Initial pixel-state plan tracker finishes2/2 pilot episodes, but ID1/101 has
  four contacts. Bounded pre-contact analysis found redundant sparse-curvature
  speed clipping and an accelerating-anchor braking guard. Corrected these two
  profile semantics only; frozen oracle/champion/single-point line unchanged.
- `runs/joint_plan_student_pilot_v1`: fixed5000 updates/137.64s, TRAIN waypoint
  error0.3484 length units and speed error0.8203; NO holdout claim. Its completed
  DEV15 endpoint is0/15; the subsequent checkpoints below preserve chronology.
- `runs/joint_plan_cpu_smoke_v1`: UNTRAINED interface-only CPU smoke,300 calls,
  cold1.517s, act p95 2.547ms, current-executable VmHWM236512KiB; reload equal.
  This is not the final trained package measurement or a driving result.
- Tracker v2 removes two proven profile-interface distortions. ID1/101 improves
  from20.26s/four contacts to16.84s/zero; ID2/102 regresses to off-track/stall.
  Preserve both results; the fix is not uniformly successful.
- Tracker v3 uses newest-only HUD with unchanged coefficients. On all
  six TRAIN replay roads, high-deceleration MAE improves4.281->2.211; restricting
  true speed<=80 gives3.841->1.187. A separate read-only replay diagnostic
  (`runs/joint_plan_hud_diagnostic_v1.json`) confirms the80 measurement clip is
  artificial: allowing estimates to100 reduces all1141-PRE MAE3.883->1.126 and
  p9514.955->2.390. ONLY estimator range changes to100; planned speed cap stays80.
  No coefficients were fitted and this is not a driving result.
- First student failed on seen TRAIN roads before emergency masks, with valid
  corrective plans disagreeing in lateral direction. Timing/scale/history checks
  reproduce saved predictions. Six actual student TRAIN episodes now contribute
  only valid last60-action windows before first collision/departure/stop; failed
  episodes stay failed in records. Same model/optimizer/seed fits20000 updates;
  changed data AND budget mean this is not an isolated data-only ablation.
- Matched v2 tracker endpoint: actual teacher plans13/15 finishes/three geometries,
  finished mean15.209s; first learned model0/15. Corrective fit also0/15 with v3
  tracker, despite TRAIN point error0.1358. These remain negative student results.
- Final bounded data test: replay the ALREADY recorded full-V7100-road MAIN
  corpus (`runs/local_plan_main_v1`, IDs1-5 x11-30) for actual paired plans; retain
  28-30 for exposed offline checks only. Add one further12-road actual-student
  corrective cohort, including existing failing TRAIN roads and14-19. Do not
  change model size/heads/loss or open a new algorithm. One final fixed20000 fit
  will retain corrective sampling priority rather than dilute rare corrections.
  If no meaningful full-episode improvement, package/report the negative result
  rather than launch more architecture/loss sweeps or spend untouched geometries.

## Final Outcome

- NOT_PROMOTED. `runs/joint_plan_comparison_final_v1.json` compares complete
  episodes on15 exposed roads/three geometries with identical reset digests:
  champion13/15 (finished mean18.515s), actual-plan tracker v3 10/15 (15.334s),
  final learned-plan tracker0/15. Student has15 collision episodes:9 collision
  retirements and6 off-track retirements;4 also show sustained stopping.
- `runs/joint_plan_student_final_v1`: one250242-parameter configuration,seed0,
  fixed20000 updates/549.33s. TRAIN91 roads/19 geometries,109 recorded episodes
  (91 successful base plus18 failed corrective),16863 base+762 corrective rows;
  64+64 samples perbatch. Exposed offline checks:15 roads/seeds28-30,not fitted.
- Teacher data replays106/106 complete episodes across106 roads/22 geometries;
  these are demonstration replay counts, not student finishes. TRAIN point MAE
  0.3925 and exposed offline MAE0.4482 do not establish driving success.
- Latest HUD estimation improved numeric accuracy but teacher-plan finishes
  regressed13->10; retain that negative result. A bounded SAME-PRE cap95 probe
  on regressed ID3/31 changed zero actions: provided speeds were below80. No
  further cap tuning or controller change was adopted. Teacher-plan references
  remain privileged diagnostic inputs and include unsupported-branch fallback.
- `runs/joint_plan_candidate_v1.zip` is a research-only packaged candidate,
  NOT a replacement recommendation. SHA2562150ec2d93a23af523aac0c67749609cf65fbd23d64fe5f242445701f6fa3edd.
  Final CPU report: `runs/joint_plan_candidate_cpu_v1.json`; Python3.11/Torch2.1CPU,
  cold1.891s,resetmax0.374ms,300acts p953.820ms/max7.047ms. Current-executable
  VmHWM236940KiB afteracts;238156KiB including save/reload comparison. Reloaded
  weights/actions/plans/history agree. Local limits pass,not official certification.
- The earlier v1 true-speed-only diagnostic is separately retained at
  `runs/joint_plan_tracker_true_speed_v1`:0/1 on TRAIN ID1/101. It is not a
  complete privileged-state replacement or a matched final-v3 comparison.
- 139 focused tests pass; only expected Torch TypedStorage deprecation warning.
  No unseen-geometry evaluation was justified. Protected roads,champion,frozen
  V7,environment and the single-point/v14 experiment remain untouched. No
  official submission or confirmation was performed. Research execution did not
  commit or push; the later reporting-only publication is authorized above.
- Final bounded diagnosis inspects only DEV ID1/31 PRE49-63 and ID1/32 PRE35-49.
  Valid lateral correction is missed before the final pre-contact emergency
  masks. At ID1/32 PRE44, teacher right coordinates at s10/16/24 are
  [0.99,1.94,2.89], student[-0.60,-0.91,-1.07]; nearby speed predictions remain
  close to labels. A visible road-interior obstacle approach then intersects
  the predicted path and ends in contact. Later emergency braking is also
  missing. These are observed planning/closed-loop errors, not evidence that
  hidden-map ambiguity or multimodal averaging has been causally established.

## Bounded Closure Follow-Up

User direction2026-10-05T12:28Z retains NOT_PROMOTED. Existing artifacts only;
one driving-code correction is permitted only for a specific reproducible defect.
No more epochs, model expansion, new algorithms, or repeated CPU benchmarks.

- `runs/joint_plan_followup_timing_v1.json`: champion and final-v3 actual-plan
  tracker jointly finish9/15 road settings (three geometries), with matching
  resets. On EXACTLY those9, means18.646667/15.311111s; mean paired change
  -3.335556s, all9faster, range-4.06..-2.42s. Not overall superiority or a
  learned-student result; do not compare their different complete finish sets.
- Target ID4 is reported separately for seeds31/32/33: champion17.94/19.06/18.96s,
  plan-tracker14.76/15.00/15.70s, paired changes-3.18/-4.06/-3.26s. Relative to an
  explicit10.5s goal these still need4.26/4.50/5.20s reductions (28.86/30/33.12%).
  The user's official Track4/18.4s report has no geometry seed; these local cases
  cannot be asserted identical to that official target road.
- `runs/joint_plan_followup_linkage_v1.json` inspects ONLY final DEV ID1/32
  PRE0-49. Numerical prediction residual exists at0. First fully valid opposite
  tracker-steering decision with |teacher-plan steer|>=.02 is PRE38/simulator t4.06
  (3.04s after the post-warmup start):
  actual-plan+.0249773, predicted-plan/issued-.00659858. Earlier smaller opposite
  corrections exist; this threshold is not proof of the first unsafe causal act.
- At s16/PRE38, sampled teacher right=1.01218, diagnostic normalized target=.042174,
  raw model=-.012260, decoded/tracker-input right=-.29425. Allsix masks valid;
  same pixels/actual command history and identical pedals. Saved plans/targets,
  PRE pose/time, masks, and paired speed semantics align. Model replay differs
  at most3.815e-5 physical units; saved-plan tracker reproduces actions exactly.
  DEV diagnostic targets were never fitted. The original dense selected path
  was not saved, so dense-to-six-point resampling cannot be independently redone
  from these artifacts alone. No upstream correctness beyond that is claimed.
- No reproducible wiring correction identified. No inference/training changes,
  simulator runs, new fits or CPU benchmarks performed in this follow-up.
  Candidate CLOSED/NOT_PROMOTED; champion and other research lines preserved.
