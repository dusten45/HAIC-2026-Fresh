# Frozen champion interval diagnostics

`champion_telemetry_worker.py PACKAGE` runs the package's original `Agent` in a separate process. It accepts only reset/act operations and lawful pixel observations. Read-only wrappers call the original tracker, centerline extractor, connected-route planner, target selector and controller once and return their original results. Internal steering memory retains its original precision. `--plain` disables these wrappers for verification on the same saved observations. The worker has no simulator imports.

`champion_bottleneck_profile.profile(rows, thresholds)` analyzes saved telemetry without executing a policy or environment. Freeze its thresholds before collecting observations. Rows contain `before_time`, `after_time`, monotonic after-interval `unique_tiles`, `action`, `collision`, and `policy` fields `speed_estimate`, `hazard_near`, `centerline_points`, `path_points`, and `route_target_missing`.

Default events are no new tile for 0.8 seconds, a low estimated speed during that interval, the policy's actual near-hazard predicate, steering magnitude at least 0.30, absent pixel centerline, absent route target, and recovery intervals. Recovery starts after a clear interval gains a tile following an anomaly, and a new anomaly interrupts it. Its two-second window classifies interval starts; whole observed intervals contribute duration, so discretization and floating boundary arithmetic can extend a reported run by one interval. Missing centerlines and missing route targets are separate events because planning can fail while road perception succeeds.

The profiler returns actual duration-weighted seconds, shares, continuous runs, recovery triggers, union exposure and summed exposure. Events overlap. Summed shares can exceed the union or exceed 100%; they are not a partition of lap time. A slow interval can be appropriate for avoidance, turning or recovery. These measurements do not establish unnecessary slowing, causal failure mechanisms, or optimal lap time.

A frozen champion audit on a fresh DEV cohort observed both completions and collision retirements at official endpoints. The representative failure retained a perceived centerline, a route target and a near-hazard flag through repeated contacts. This supports a single untested hypothesis: add a distance-dependent longitudinal speed limit near tracked obstacles, so a nearly straight target cannot by itself release the speed target during close approach. This hypothesis was not implemented or evaluated. The policy and parameters stayed frozen; no alternate policy, training, HOLDOUT or SEALED evaluation was performed. Private case identifiers, pixels, truth, detailed numeric results and package artifacts remain outside the repository.

Validation:

```sh
python -m unittest retry.test_champion_bottleneck_profile -v
```

The tests cover unequal interval durations, overlapping events, separate perception and planning failures, progress age, and interrupted recovery. On the representative episode, replaying all saved observations through the plain original actor matched instrumented actions, tracker/image hashes and original steering memory exactly, with no additional environment actions.
