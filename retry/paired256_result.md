# Four actualsource-ratio paired pulses256

**4/4completed**; noactualDNF, censor orunexecutedepisode. Finalofficialtime improvedat2curvestates butslowedat2quietstates; meanpaired delta**-0.015s**. Thisis tiny/mixedevidence fromtwoalreadyknownTRAINroads, notindependentperformanceconfirmation. Nochampionchange orfitting occurred.

The exact255ratio wasfrozen: K=0.06*(max(0,existinglegalfeature4speed)/0.54+5), d=min(current240brake,current240gas/K); gasnew=gas−K*d, brakenew=brake−d. Onlycurrentpixel-derived240outputs/speed areused. No wheelomega/force/GT entersaction selection. Threepairedactions arefollowedbyall-channelclosed-loop240; steering/nominalmemory remain originaleveryaction.

QuietstatesO0/67,N0/82 werefixed255cases. CurverepresentativesO0/160,N0/163 werealreadyregistered255median-curvature-bin samples, notselectedfrom256outcomes. Everyindependentepisode resetatitsoriginalinitialcondition, replayedexact240prefix andmatchedstoredfullsnapshotbeforepulse. Noactualsnapshotrestore orbaselinevalidationrerun.

| State | 3-action speed delta | Contiguous/visited delta | Baseline lap | Actual lap | Paired delta | Damage |
|---|---:|---|---:|---:|---:|---:|
| O0/67 low_curvature_braking | +0.221m/s | 0/0 | 23.66s | 23.68s | +0.02s | 0.00 |
| N0/82 low_curvature_braking | +0.096m/s | 0/0 | 23.62s | 23.78s | +0.16s | 0.20 |
| O0/160 curve | -0.088m/s | 0/0 | 23.66s | 23.52s | -0.14s | 0.00 |
| N0/163 curve | +0.137m/s | 0/0 | 23.62s | 23.52s | -0.10s | 0.20 |

The legalproxyK stayedatits snapshotvalue throughoutallfour3-actionpulses. The twoquietpulses exactlymatched255paired pedalcommands. Forcurves, the reference is a hypothetical255stylefixedbaseline sequence, not anoriginal255paired forecast: currentpixelpedals differed by upto0.08534onO0/160 and0.00000870onN0/163. These differences were recorded without overridingcurrentpixels withGT. Realquietstate speedchanges matchedthe source predictions closely. Thisdoesnotmakeforecasts equal toclosedloopsteering orguarantee laterlap gains: bothquietpulse laps sloweddespitehigherlocalspeed, whileonecurve pulse slowedlocallyyetimprovedfinishtime. Friction/forceopposition reduction isnot intrinsicallyspeed orlap gain.

A subsequent singlecontinuousapplication pilotofthe samefrozenlaw maytesttransfer; no gain orpromotion ispromised. Baseline-lengthcost for6TRAIN+2existingDEV wouldbe~2091native within3861remaining, withbudgetcensoring explicit. No furtherexperiment wasstartedhere.

Cost1,184native = prefix468 + pulse12 + continuation704, 58.3s. Newmodelticks/fits0. Researchbalance3,861;84,000reserveunused. Champion240/main/Participants/backups andofficialHOLDOUT/SEALED preserved. Rawstates/controls/roadidentities private; completedruns retainedwithoutreplay.
