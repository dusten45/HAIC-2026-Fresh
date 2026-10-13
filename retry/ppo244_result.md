# Fixed residual PPO pilot 244

The final actor completed only one of two DEV screens. S0 improved by 0.08 seconds, but S1 retired off_track while the frozen baseline completed. This pilot is closed without promotion.

The frozen current240 pixel controller supplied its original 16 legal features and actions. A zero-initialized linear 16→2 actor added bounded tanh pedal residuals (gas 0.03, brake 0.02), with fixed latent Gaussian standard deviation 0.2. Steering, normalization, affine head and nominal memory stayed fixed. The value network used only the same legal features. Coverage and terminal timing supplied rewards only.

The 160-second source time limit yields completion return 2−T/160 and actual DNF return p−1. Collection cuts bootstrap without a DNF bonus. Stored latent samples and old Gaussian likelihoods define PPO ratios before tanh and pedal clipping.

Controls completed in 23.70s and 25.32s. Exactly 8,192 training actions formed eight fixed 1,024-action batches; 7 actual DNFs and 8 collection cuts were distinguished. No intermediate validation or checkpoint selection occurred.

| DEV screen | Current240 baseline | Final actor | Damage |
|---|---:|---:|---:|
| S0 | 18.64s | 18.56s | 0.00 |
| S1 | 21.00s | DNF | 0.40 |

Charged 9,352 native actions in 418.0s, including controls and screens. Research balance: 6,020; final reserve: 84,000 unused. Maximum policy time including frozen worker IPC and residual calculation: 51.65ms.

Only the final actor was screened. This two-road DEV result does not establish generalization. The current champion is unchanged; HOLDOUT and SEALED remain closed. No automatic follow-up is authorized by this result. Raw observations, legal features, latent buffers, checkpoints and road identities remain private. Completed episode/optimizer records permit reuse without replay; unfinished physics episodes are not restarted.
