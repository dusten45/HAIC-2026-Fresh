# S1 gas residual counterfactual 245

Removing only the learned gas residual did not prevent the local collision and progress stop. This excludes gas residual as a necessary sole explanation for this stopping pattern; it does not establish a unique brake cause or reject residual RL generally. No new training or search occurred.

S1 was a DEV screen in stages243/244 and is now diagnostic data. It has no independent evaluation status. Original244 retained actual commands, 16 pixel-derived features and progress/speed/terminal records; full images and richer physical observations were regenerated through charged, exact command/feature/physics prefix replay.

The first residual command differed at action1 (gas +0.000948, brake +0.00000592). Regenerated pixels first differed at5, legal features at25, and steering at30. Original244 lost its target at212, collided and slowed from46.5 to4.1m/s, then stayed at237/297 tiles until off_track at313. Its large late pedal/steering differences from the baseline were feedback effects; its own residual amplitudes remained small. Nominal steering memory matched prior steering within float32 rounding. Two brief negative hull-longitudinal samples during collision were not sustained reverse travel.

| 235-action prefix | Collision actions | End tiles | End speed | Damage | Target missing |
|---|---|---:|---:|---:|---|
| saved_residual | [212, 220] | 237 | 0.19m/s | 0.40 | [212] |
| saved_baseline | [208] | 267 | 53.24m/s | 0.20 | [] |
| gas_restored | [213, 214, 221] | 237 | 0.26m/s | 0.60 | [] |

The original and baseline replay each matched235 saved commands; original legal features and both saved physical traces matched. The gas-cancelled arm retained the learned brake residual on its own legal observations and stopped without target loss. All three prefixes ended at the fixed235-action boundary, so their outcomes are censored, not newly asserted official DNFs. The earlier baseline official run completed in21.00s.

Dense mean reward fluctuated across the eight training batches rather than improving monotonically. Final two-screen mean terminal return was lower than the baseline; S1 failed return was−0.202 versus baseline completion return1.86875. Existing data provide no reward/completion reversal. Likelihood and reward integrity checks were not repeated.

Charged705 native actions, including both prefix controls. Research balance is5,315, and the84,000 final reserve is untouched. Raw images, features, commands, physical state and road identities remain private. Champion240 and all official HOLDOUT/SEALED remain unchanged. The most useful next technical contrast, before more RL, is symmetric brake-only cancellation with the same prefix controls; it was not executed here.
