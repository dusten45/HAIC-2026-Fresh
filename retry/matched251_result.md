# One matched-steering affine correction pilot251

**Candidate0/8 complete versus current2408/8.** Fourcrash and fouroff_track actual DNFs; nocensoring or unexecutedroads. The candidate is rejected without promotion/refitting/reselection. No commoncompletedtime comparison is defined. Localpulse benefits from250 didnotgeneralize through this continuouslyapplied affine correction; this doesnotprove a universal teacher-label defect or ARS/RL limitation.

Sixexact240on-policy trajectories were materialized once because existingrecords didnotprovide completepixels/actions/fullquery-boundary states together. Everythirdaction starting1 was queried if12future240 actions remained. The unchanged249fourcandidates, matchedsteering, first3onepedal intervention, baselinecontiguousfrontier firstpassage, baselinepriority ties and196baselineaccuracylimits were retained. No model/objective redesign occurred.

Teacher labels:527. Baseline selections:193 (36.62%). Statuscounts:{'intervention_selected': 334, 'baseline_tie': 169, 'tail_baseline': 23, 'incomparable_baseline': 1}. One technicallyinvalid modelbaseline query kept itsbaseline target;23future-short tailqueries also keptbaseline. 503/504 fullhorizon baselinecontinuations passed existingchecks. The label is onlythe selectedfirstaction pedals, not anentireplan orGTinput.

The finalaction saturation inverse projected to the validpre-scale interval nearestcurrent240, retaining exact0targets forbaseline queries. Mainpredicted pre-scale delta ranges were gas≈0…+0.369, brake-0.235…0. Float32intermediate rounding left opposite-channel effects at most≈3.5e−8 in changedqueries, not large saturatedpushes. One16→2affine ridge(lambda1,unpenalizedbias, sixroads equalmass, totalweight527) used fixedoriginalTRAINnormalization; existinghead coefficients/scales/nominalmemory were bytepreserved. Runtime adds correction to originalrawresidual beforeclip±0.5 and thenuses originalnominal/actionclip/global-scale sequence. No futureactions, snapshots, teacher orGTaccess in theparticipant.

| Road | Baseline lap | Candidate | Damage | Native |
|---|---:|---|---:|---:|
| O0 | 23.66s | off_track | 0.20 | 174 |
| O2 | 20.98s | crash | 1.00 | 44 |
| N0 | 23.62s | off_track | 0.20 | 163 |
| N1 | 17.08s | crash | 1.00 | 34 |
| N2 | 21.56s | crash | 1.00 | 59 |
| N3 | 18.76s | crash | 1.00 | 200 |
| S0 | 22.02s | off_track | 0.20 | 235 |
| S1 | 19.22s | off_track | 0.00 | 179 |

Cost:2,662 actualactions = collection1574 + evaluation1088. Separately2013 source-model queries and96,612 physics ticks,39.91s(modeltime included in collection). Collection142.9s, onefit0.011s, evaluation49.8s. FullAgent median4.34ms/p9510.65ms; IPCmax42.13ms.

B904,000 reflects the explicit6,000researchgrant, notborrowed reserve. Researchbalance7,490; final84,000reserve unused. Existing247DEV screens were reused for fixedcandidateevaluation, with no independentHOLDOUT claim. Current240champion, main, Participants, backups and officialHOLDOUT/SEALED preserved. Rawpixels, state, labels, model androadidentities remainprivate. No follow-upcollection/fit/policychange.
