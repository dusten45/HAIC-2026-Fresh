# One six-HUD-feature representation change 248

Candidate completed**5/8** versus current240**8/8**; actual DNFs3, censored0, unexecuted0. No champion change, refit or screen selection occurred. This single representation experiment does not establish a universal limitation of ARS or residual learning.

Renderer wheel bars atplaces7–10 encode0.01*omega. Actual front-joint bar at20 encodes−10*joint.angle, and yaw bar at30 encodes−0.8*angularVelocity. Runtime reads only the latest84×84 grayscale frame, using fixed source-derived bar ROIs and signed brightness extent. Six proxies were visibly present and varied in three existing TRAIN frames; all six had nonzero TRAIN variance, and steering/yaw had both signs. They are quantized display proxies, with antialiasing, adjacent wheel leakage, baseline rounding and clipping, not exact simulator states. No decoder fit or new GT calibration occurred.

Original16-input ridge was reproduced bit-for-bit in mean, std and weights. One22-input head then used the same1392old224 and473new229 labels/pixels: each population receives0.5, each road equal mass174, lambda1 and unpenalized bias. 229 action-indexed preaction observations were aligned to their sparse labels. Normalization used TRAIN only. Pedal residual clip±0.5, final action clipping and exact240 scales were preserved. Original nominal steering/memory source remained byte-identical;24/8 are lateral acceleration settings, and original lookahead is unchanged.

| Road | 240 baseline | One22-feature candidate | Paired delta | Candidate damage |
|---|---:|---:|---:|---:|
| O0 | 23.66s | 22.96s | -0.70s | 0.0 |
| O2 | 20.98s | DNF | — | 1.0 |
| N0 | 23.62s | 23.48s | -0.14s | 0.2 |
| N1 | 17.08s | DNF | — | 1.0 |
| N2 | 21.56s | DNF | — | 1.0 |
| N3 | 18.76s | 18.04s | -0.72s | 0.4 |
| S0 | 22.02s | 21.90s | -0.12s | 0.2 |
| S1 | 19.22s | 19.78s | +0.56s | 0.4 |

Common-completion mean paired delta:-0.224s over5 roads. Completion loss takes precedence; failed/censored roads are excluded from that timing statistic. These are six known training DEV roads plus the two already registered247DEV screens, not official HOLDOUT. Baselines reused exact prior results; all new initial observations matched them. Failure did not prune later evaluations.

Fit cost:0.649s; evaluation:71.9s and1,621 native actions. Full Agent computation median5.62ms, p9512.26ms, max26.72ms; IPC-inclusive maximum30.49ms. Research remaining:6,504;84,000 final reserve untouched. Raw TRAIN pixels/features/labels, fitted model, road identities and runtime caches remain private. Main, official Participants, previous backups, current champion and HOLDOUT/SEALED remain preserved.
