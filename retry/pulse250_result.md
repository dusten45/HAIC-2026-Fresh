# Six actual closed-loop pulse confirmations250

Six249selections were tested as independentepisodes. **6/6 official completions**, 0 actual DNFs, 0 censored, 0 unexecuted. 6/6 reproduced the predicted one-native-action frontier gain. No teacher/model fit or champion change occurred.

Each episode reset only at its original registered initial condition, followed exact240 to its selected snapshot and applied only the fixed249pulse-channel values for3actions. Steering, the opposite pedal and nominal memory were calculated from currentpixels240 throughout; after3actions, every channel returned to240. Stored prefix controls/scalars and fullsnapshot boundary matched without any separate validation replay or snapshot restore. Baseline lengths predicted1776native actions for6episodes within5912available; every prefix action was charged.

| Road / snapshot | Pulse | Frontier delta(actions) | Baseline lap | Actual lap | Paired official delta | Damage |
|---|---|---:|---:|---:|---:|---:|
| O0 /168 | brake_lower | -1 | 23.66s | 23.52s | -0.14s | 0.00 |
| O0 /220 | brake_lower | -1 | 23.66s | 23.54s | -0.12s | 0.00 |
| O0 /272 | brake_lower | -1 | 23.66s | 23.66s | +0.00s | 0.00 |
| N0 /13 | brake_lower | -1 | 23.62s | 23.18s | -0.44s | 0.00 |
| N0 /117 | gas_upper | -1 | 23.62s | 23.16s | -0.46s | 0.00 |
| N0 /168 | gas_upper | -1 | 23.62s | 23.50s | -0.12s | 0.20 |

Common-completion mean paired lap delta:-0.21333333333333335s across6episodes. Frontier results: 6faster, 0ties, 0slower, 0unreached. Official finaltimes: 5faster, 1ties, 0slower amongcompleted. The80ms frontier metric is one4-physics-tick native action, not a measured substep advantage. Reaching the frontier did not stopexecution. Snapshot samples on the same road are paired diagnostics, not independent unseen generalization roads.

Actual steering often differed from the old frozensequence afterpulse-induced state changes, as intended. Pulsevalues themselves remained the249fixed selection; currentnominal reachability departures, if any, are reported separately inJSON. These pulse confirmations do not prove a universal teacher-label defect, identify an optimal policy, or authorize fitting/combining pulses.

Total cost:1,760native actions = prefix952 + pulse18 + continuation790, wall81.8s. No modelticks orfits. Researchremaining:4,152; finalreserve84,000unused. Champion240, main, Participants, backups and officialHOLDOUT/SEALED preserved. Raw trajectories, controls and roadidentities remainprivate; completedrollouts persisted and never repeated.
