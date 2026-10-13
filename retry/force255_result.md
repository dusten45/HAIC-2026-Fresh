# Current240 wheel-force source diagnosis255

Highspeedbaseline has opposingfront/rear longitudinal tireforces, mostlywithoutfrictionclipping in these samples. **Thisis notproof of wastedperformance or a physicalspeedlimit.** Two supplementary pairedreduction shadows reducedopposition while approximatelypreserving3-action baselineacceleration; one actualshortpulse confirmation is justified, not a newglobalpedal policy.

18snapshots werefrozen beforemodel execution: two highspeedlowcurvature/braking quantilepositions and onecurved medianposition per6TRAINroads. Eachused the samefullactualsnapshot and3actualsteeringcommands; baseline,brake0 orgas0 changed onlyonepedal. Pythonline tracing read unchangedCar.step locals before/afterfrictionclipping. Two additional12-action baselinechecks were bit-identicalwith/withouttracing and matchedexistingactualendpoint/discreteprogress limits. No newnative ortrainingmaterial occurred.

| Diagnosticgroup | Frontforward N | Rearforward N | Netforward N | Opposition N | Δspeed brake0 | Δspeed gas0 |
|---|---:|---:|---:|---:|---:|---:|
| low_curvature_braking | -346.2 | 376.5 | 30.3 | 669.0 | +4.79m/s | -6.04m/s |
| curve | -357.7 | 358.5 | 0.8 | 640.3 | +4.95m/s | -5.89m/s |

Raw/appliedlongitudinal andlateral forces, wheelomega andsurface-minus-forward-speed slip were recorded separately. Forceclipping couples thetwo wheel-axis components. Mosthighspeedbaseline samples had noclip; onlyonecurve samplefront group clipped25%ofits wheel-tick records. Thisdoesnot generalize theearlierlaunch boundaryclamp. One-channel removal changes acceleration; itdoesnot establish betterlap time. Dualneutral0/0 onthe same twoquietstates reducedopposition but ended0.62/1.81m/s belowbaseline, largelyholdingentrance speed rather thanbaselineacceleration.

Source order is gasactuator update(upward+.1/tick maximum), engineomega increment, brakeomega reduction, slipforce evaluation, vectorfriction clip, omegaroadreaction feedback andBox2Dsolve. Brake15*b israd/s per20ms tick, not15N; wheelradius0.54m andinertia1.6 areused. Projectedbodyforward forces are not axleforce magnitudes or measuredhullaccelerations.

The finalsinglecontrast used existinglegalfeedbackspeed v toderive K=0.06*(v/0.54+5), then d=min(brake,gas/K), gasnew=gas−K*d andbrakenew=brake−d. Fourbrakedwheels versus tworearengineupdates sets thissource ratio. Itapproximatelypreserves aggregateunclippedomega input and differs from236normalized-magnitude winnerexclusion. No coefficientwas fit. Snapshot-only v wasfixedthrough3actions; a runtimehypothesis would readcurrentpixels eachaction.

| Quietstate | Oppositionbaseline→paired | Netforwardbaseline→paired | PairedΔspeed |
|---|---:|---:|---:|
| O0/67 | 649.7→179.2N | 18.8→25.5N | +0.221m/s |
| N0/82 | 676.7→226.6N | 54.9→57.8N | +0.096m/s |

Nextoneexperiment: independentlyreplay these2knownprefixes, apply thefixed pairedreduction for3actions usingcurrentlegal v, then closed-loop240 toofficialfinish. Expected~592native within5,045available. This remains unexecuted. Actualrolling/slip andclipping, gasramp history, curve/hazard states andfuturesteering remainuncertain; fixedshadowsteering isnot claimed equal toclosedloopsteering. No universal gas/brake removal orphysics maxspeed conclusion.

Cost:native0; model62queries/888physics ticks, modelwall1.21s(mainread/tracing phase6.10s). Budget814,955+5,045+84,000=904,000unchanged. Champion240, officialHOLDOUT/SEALED, main, Participants andbackups preserved. Rawforces/fullstates/controls private. Noactualcandidate, fit, new dataset orautomaticfollow-up.
