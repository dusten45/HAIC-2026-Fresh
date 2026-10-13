# One deterministic parameter-probe pilot 247

The update completed6/6 roads but averaged21.300s versus20.943s for current240, so the baseline was selected. The fresh screens therefore evaluated the same baseline policy, with duplicate arms reused. No champion change or follow-up occurred.

Eight fixed episode policies used four Gaussian parameter directions with exact ± symmetry. Every probe was scaled to latent RMS0.2 on road-balanced saved current240 legal features from the four new241 training roads; the old201 roads had no suitable feature cache. The existing16-feature input normalization and frozen240 steering, affine head and nominal memory remained fixed. No per-action noise, retraining, radius/rate sweep or additional direction occurred.

The one ARS-style update used six-road mean official terminal returns: complete2−T/160, actual DNF p−1. Paired differences were divided by the population standard deviation of eight policy means, multiplied by positive probe matrices, averaged over four directions and capped at baseline-feature latent RMS0.2. Zero standard deviation or zero sum gives the exact baseline. Incomplete returns forbid an update. Actual DNFs do not prune remaining roads; budget censoring and unexecuted roads remain unknown.

| Policy | Complete | Actual DNF | Censored / unexecuted | Mean official time if6/6 | Native |
|---|---:|---:|---:|---:|---:|
| baseline | 6/6 | 0 | 0 / 0 | 20.943s | 0 |
| probe0 | 5/6 | 1 | 0 / 0 | — | 1375 |
| probe1 | 4/6 | 2 | 0 / 0 | — | 1222 |
| probe2 | 4/6 | 2 | 0 / 0 | — | 1494 |
| probe3 | 2/6 | 4 | 0 / 0 | — | 1157 |
| probe4 | 4/6 | 2 | 0 / 0 | — | 1349 |
| probe5 | 3/6 | 3 | 0 / 0 | — | 1519 |
| probe6 | 5/6 | 1 | 0 / 0 | — | 1400 |
| probe7 | 4/6 | 2 | 0 / 0 | — | 1291 |
| update | 6/6 | 0 | 0 / 0 | 21.300s | 1601 |

Selection: **baseline**, using official completion count first and equal-road mean time among6/6 policies. Baseline results reused six exact current240 runs. ParameterL2 and fixed order break exact time ties. Selection was frozen before either fresh DEV screen opened.

| Fresh DEV | A:240 | B:winner |
|---|---|---|
| S0 | 22.02s | 22.02s |
| S1 | 19.22s | 19.22s |

Fresh identities were fixed before the parameter draw and excluded all prior registered roads, including diagnostic S1. Paired A/B then B/A used identical reset observations; exactly identical policies reused the first result. Screen results did not change selection, draw new directions or automatically change the champion.

PPO244 previously had22 completed training episodes,7 actual DNFs and8 collection cuts, followed by1/2 completed DEV screens. Its action-noise training and earlier screen cohort differ from this pilot, so these counts are not a controlled proof of method superiority.

Cost: 12,925 native actions in553.8s, including all failed/censored episodes and screens. Maximum policy latency including base IPC and residual calculation:67.09ms. Research remaining:8,125; final reserve84,000 unused; operating cap898,000. Champion240 and official HOLDOUT/SEALED remain unchanged. Raw legal features, models, commands and road identities remain private. No follow-up experiment was started.
