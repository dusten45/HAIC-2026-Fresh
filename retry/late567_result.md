# 567 late-section study

The saved 565 trajectory was restored at global raw 528, the checkpoint immediately before hold 133, selected by the preregistered first-hold-bracketing-s=800 rule. Its 80-raw replay matched every saved state and force record. The replay cost 80 source ticks, 320 force evaluations, 80 geometry checks and 1.03 CPU seconds.

The next preregistered step was a fresh float32 finite-difference calibration at this late checkpoint. Seven columns completed. Column 7 reached a raw-level rejection before the model tick: that raw incurred four force evaluations but no tick or geometry check. The source driver’s pre-tick rejection paths are force peak and cumulative clipping history. The failed raw itself was not durably saved, so the record cannot identify which of those two exact gates fired. This is a calibration failure under the frozen stop rule. No retry, altered direction, fixed calibration perturbation, candidate, or feedback continuation was run.

Total accounted work, including the already completed baseline replay, was 1,224 ticks, 4,900 force evaluations, 1,224 geometry checks, 14.50 CPU seconds and 14.50 wall seconds. It used only DEV source simulation. Native actions, resets, HOLDOUT, SEALED, paid compute and reserve use were zero. No candidate was promoted and no whole-source improvement is claimed. The official tracker score remains the saved incumbent result; no new finish score was established.

The exact baseline and costs are in `late567_baseline_result.json` and `late567_cost.json`; the preregistered bounds and stop rule are in `late567_contract.json`. The private checkpoint and saved trajectory remain outside the repository. The continuation script now refuses a second run after the recorded calibration failure.
