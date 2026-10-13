# One two-frame road perception pilot253

**Bothroads completed but bothslowed; meanpaired delta+0.25s.** Abandon the fixedfusion hypothesis under the preregistered rule. Current240 remainschampion. No mixture-ratio/motion/phase/affine sweep or follow-upexperiment occurred.

The selectedbottleneck was singleframe road-raster quantization feedingroute planning. A deterministic similarity transform wasestimated from twoactualobservedframes usingexistingtracker-style corners/LK motion settings, then previouspixels werealigned and equallyblended onlyforroad routing. CurrentHUD, carregion andcurrentobstacle detections werepreserved. The originalcontroller, lookahead, steeringformula, frozen16featurehead andexact240scales werebytepreserved. NoGT, futureframes orteacherinputs enter thispixel-onlycandidate.

Relevantprior DEV evidence was reviewed:171uses warpedpath direction onlywithina route-score tie, and184injects GTego-motion intoexistingobstacletracks. Thispilot changes roadperception input itself rather thanretainingpath direction, supplyingmotiontruth, changingsteering gain oraddingHUDinputs. The userclosed251/252affinefamily wasnot resumed.

Before nativeexecution, old201F0/O0 andnew241F0/N0 werefixedwith theexistingexact240initialconditions andofficialfinishdefinition. Expectedbaselinecost592, cap1000. Completionloss ornonnegative equalroadmeanpairedtime abandons thehypothesis; capcensoring/technicalerror remainunknown, anddamage isdiagnostic only.

| DEV | Current240 | Roadfusion | Paired delta | Damage base→candidate | Maskchanged actions |
|---|---:|---:|---:|---|---:|
| O0 | 23.66s | 24.10s | +0.44s | 0.00→0.20 | 204 |
| N0 | 23.62s | 23.68s | +0.06s | 0.20→0.20 | 181 |

Theperception operation activated on434actions andalteredroadthreshold pixels on385actions, so thiswas notan identitycomparison. No claim ismade thatalignment removesallnoise or thattemporalperception generallyfails. Thefixedwhole-policy effectfailed its timecriterion onthese twoknownDEV roads.

Cost599native actions/29.2s, fullAgentmedian6.67ms/p9513.55ms, IPCmax34.28ms. NoactualDNF, censor, unexecutedroad ortechnicalerror. Researchbalance5,045;84,000reserve unused. Noadditional researchgrant isjustified bythisresult. Recommendkeeping240 andnot tuningthisfusionfamily; anothernativepilot shouldfirsthave directbottleneck evidence in existingon-policycache. Main, Participants, backups andofficialHOLDOUT/SEALED unchanged. Rawroad identities/caches remainprivate.
