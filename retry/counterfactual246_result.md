# S1 brake residual counterfactual 246

Restoring only the brake channel to frozen240 commands recovered official completion: **21.12s**, 265 actions, damage0.4, all297 tiles. Final244 gas residual remained active on the same legal features; steering, normalization, affine head and nominal memory stayed fixed. No retraining, likelihood/reward recheck, parameter search or historical control rerun occurred.

| Policy | Observed outcome | Damage |
|---|---|---:|
| Frozen240 historical | Official complete21.00s /263actions | 0.2 |
| Both residuals244 historical | Official off_track313, stopped237/297tiles | 0.4 |
| Brake only245, gas restored | Stopped237tiles at235-action censored prefix; official terminal unknown | 0.6 |
| Gas only246, brake restored | Official complete21.12s /265actions | 0.4 |

The gas-only run first differed from240 in pixels at6, route forward/curvature at30/30, and steering at30. Contacts at[182, 208] did not stop tile progress: the last new tile was at262, maximum no-new-tile streak3, and no speed below1m/s or persistent reverse motion occurred. Brake commands matched the frozen controller exactly; nominal steering memory differed from prior float32 steering by at most1.4e-08 due to rounding.

The contrast implicates the brake channel in the original S1 failure: brake removal recovers completion, whereas gas removal did not prevent the earlier local stopping pattern. It does not isolate a universal wrong brake formula; tiny pedal changes can change route perception and subsequent steering through pixel/physics feedback. The brake-only245 prefix remains censored and must not be called an official DNF. S1 has been reused for diagnosis and has no independent evaluation status. This result is not evidence against residual RL generally, and does not promote a new champion.

Next research should inspect brake residual sensitivity around precontact legal-feature and route changes before any additional RL, then test a specifically scoped brake constraint/ablation with fresh DEV evidence. No further experiment was started.

Cost: 265 charged native actions (cap600), 11.84s. Research remaining5,050; final reserve84,000 unused. Current champion240, all official HOLDOUT and SEALED remain unchanged. Raw pixels/features/actions/physics and road identities stay private.
