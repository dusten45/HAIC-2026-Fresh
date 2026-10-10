# Saved-state action diagnostics

`action_mode_diagnostics.py` compares a student's executed action with a teacher label for the **same saved observation and actual action history**. Different policies' action numbers do not identify the same state.

The utility reports steering, gas and brake errors in their actual units, distinguishes substantial steering opposition from small crossings near zero, and counts contiguous event runs using recorded action numbers and timestamps. Gas and brake independently define four valid modes: coast, gas only, brake only and both. Simultaneous gas and brake output is not classified as inherently wrong.

Freeze event thresholds and window definitions before comparing results. Report a fixed progressing window together with the window preceding the recorded failure onset. Keep first-contact timing separate when a long disagreement run crosses damage onset. This is a descriptive diagnostic and does not establish that the teacher's action would prevent failure.

A fixed saved-trace audit found larger action disagreement near failure, but no shared, sustained steering-direction or ordered pedal-mode pattern across initializations under its predefined criterion. The current representation and direct action regression experiment was closed. This conclusion does not establish a single failure cause or rule out other representations or training methods. No new environment actions, training, or further collection were performed. Raw observations, labels, policy traces and detailed research results remain private.

Validation:

```sh
python -m unittest retry.test_action_mode_diagnostics -v
```

The tests cover steering deadbands, small pedal-mode boundary changes, valid simultaneous pedal output, action gaps and duration calculated from actual timestamps.
