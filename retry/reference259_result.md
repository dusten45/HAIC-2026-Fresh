# Feasibleminimum-displacement reference259

Bothreference GToracles completedwithoutsolverinfeasibility. Free258was0.66s faster onO0 but0.38s slower onN0: meanfreegain0.14s isnot a consistentgeometry-optimization benefit. Theminimum-displacement referenceitself beat240 by1.14/1.88s, mean1.51s; commonGTspeedplanning/tracking/foresight remainsconfounded.

Referencegeometry minimizedonlyroad-arclength-weighted squaredcenterline displacement. No curvature/laptime term was added; curvaturewasonlythe unchangedsteeringbound constraint. Same16periodicBspline, obstacle-awayinitialization, road/vehicle/obstacleconstraints,6coordinatepasses andnumericaltolerances as258. Bothsolveswerefeasiblewithoutprojection; noactual240trajectory wasmixedintoplans. Geometrywas frozen before applyingthe unchanged258speedprofile/follower. Boundedfeasibility isnot globaloptimality.

| Road | 240actual | Free258model /actual | Fixedreference model /actual | Free−reference | Reference damage |
|---|---:|---|---|---:|---:|
| O0 | 23.66s | 21.692s /21.86s | 21.916s /22.52s | -0.66s | 0.00 |
| N0 | 23.62s | 21.395s /22.12s | 21.457s /21.74s | +0.38s | 0.00 |

Modelpredictedfree fasteronbothroads, butactualranking reverses onN0, exposing approximateprofile/trackingeffects. Plannedgeometry, modeltime andactualscore areseparate; no10slimit orpixel-legality conclusion. Bothcontexts arethe sameknownDEV O0/N0, not independentgeneralization. Samecontroller removes controllerimplementation differences, but varyinggeometry also changes generatedspeedprofile andactualtrackingstates; commonwhole-map GTinformation gain stillrequires itsown ablation.

Smallestusefultransfer step: restrictplanning tocurrent-camera-visible route length whilefreezingonefeasiblereference/model/follower, then substitutea pixel-reconstructedlocalroute under thesame visibility. Firstmeasure theforesight gap instead ofassuming globalGTmap availability ortrainingfromthetimeoptimizedline. No suchfollow-upwasexecuted.

Cost554newnative for2referenceepisodes; completed258freeoracles reused. Actualepisodewall18.71s; solver388geometryobjectives/0.205s plus2speedprofiles; exactmodelphysicsticks0. Researchbalance4,504,84,000reserveunused,B908,000unchanged. Current240/main/Participants/backups andofficialHOLDOUT/SEALED preserved. GTmaps/plans/trajectories remainprivate. No fit, promotion orautomaticfollow-up.
