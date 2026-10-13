# Smallwhole-lap racing-line/speed oracle258

**FreeGToracle completedbothroads: O0 21.86s versus24023.66s, N0 22.12s versus23.62s, bothdamage0.** Mean gain1.65s. Strictfixedcenterlines intersectactualobstacles, so theirwhole-lap problems aregeometricallyinfeasible: stoppingpartialplans actuallyterminatedoff_track. Thiscomparison cannotcleanlyseparate curvatureoptimization fromnecessaryobstacle avoidance orspeedplanning. No10-second feasibility/impossibility orlegalpixelperformance claim.

Same-source map/state wasreused fromexact240old201F0/new241F0; noHOLDOUT terrain orperformance wasused. The oracle sees fulllapgeometry/obstacles/livepose/livevelocity. A16-variable periodiccubic-spline lateralpath hasstart/finishcentretaper, roadwidth/vehiclefootprint margins, obstacleclearance andsteeringcurvature constraints. Oneobstacle-away initialization andfixed6coordinate passes used194objectiveevaluations perroad. Firstevaluation4.58/3.82ms predicted~0.8s boundedsolvecost; actualsolver0.80/0.86s. Feasible isnot a global/localoptimality certificate.

Whole-lapcurvature sets speedlimits; forward/backward acceleration passes use sourceengine power, gas/brake order, wheelinertia/rollingeffective mass andfriction approximations. Lateral/accel utilization andnumeric100m/scap werefixed beforeexecution, notphysicslimits ordamagevetoes. Bothreferences use thesamepurepursuit/standing-start speedfeedforward tracker. Actualsource environment retains itsfinish qualification>=95%, forwardstart crossing, obstacles, carsolver andofficialretire semantics.

| Road | 240 actual | Strictcenter actual | Free modelprediction | Free actual | Mean/p95 trackingerror | Free damage |
|---|---:|---|---:|---:|---|---:|
| O0 | 23.66s | off_track (blockedcenter) | 21.692s | 21.86s | 0.719/1.740m | 0.00 |
| N0 | 23.62s | off_track (blockedcenter) | 21.395s | 22.12s | 0.622/1.695m | 0.00 |

O0initialfree result missedits0.25m obstaclemargin by0.384mm. BeforeanyO0freeactualrun, a boundedminimum-norm geometricprojection changedcoefficients by atmost0.628mm, madeclearancepositive, andleft model/speed/follower fixed. It used35geometryevaluations/0.016s. Originalplan/receipt werepreserved; completedcenter/N0 runs werereused, neverreplayed. Thiswas numericalconstraintrecovery, not a newhyperparameterfamily oroutcome-driven candidate selection.

Maxfreecurvature0.128/0.117m⁻¹ exceedsfixedcenter0.088m⁻¹ becauseobstacle detours affectcurvature; no claimfreepath universallyreducescurvature relativetoinfeasiblerigidcenter. Freeactualmaxspeeds99.42/91.79m/s areobservedpeak speeds, notsafe/global limits. Trackingerror max2.01/2.26m exposes approximation/tracking uncertainty despitebothactualzero-contact finishes.

Nextcleancomparison shouldfreeze anobstacle-feasiblecentrebasedreference includingmandatorydetours, then varycurvature representation withthesamespeed/tracker. Pixels wouldrequirea separateglobal-map/foresight transfer problem. No newmodel/headtraining orautomaticfollow-up.

Cost891native = center340 + free551, rawstep3561/reset204ticks. Actualepisodewall30.38s; solver1.66s/388objectives plus35geometryrepaircalls. Approximateprofilecalls areseparatefromexactphysics: positivemodelphysicsticks0, four0-time mass-read initializations(includingpreflight). Researchbalance5,058;84,000reserveunused, B908,000 reflects explicit4,000researchgrant. Champion240, main, Participants, backups andofficialHOLDOUT/SEALED unchanged. GTmaps/plans/rawtrajectory/state private.
