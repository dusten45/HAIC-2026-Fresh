# High-Speed Oracle-v2 Plan

This plan owns the separate privileged local high-speed teacher experiment.
Read [COMMON.md](COMMON.md) for the shared research contract, exposed evaluation
roads (IDs 1-5 x seeds 1-10), and frozen oracle-v1 comparison evidence.
Learned-policy work has its own [BC.md](BC.md) plan; v2 status updates do not
pause, resume, or change that work. Splitting the documents does not authorize
new experiments or a new learning phase.

Evidence and reproduction commands: [../EXPERIMENTS.md](../EXPERIMENTS.md).

## Research Scope

The 2026-09-29 user request freezes `oracle-v1` and authorizes a separate
privileged high-speed `oracle-v2` teacher experiment, with finish reliability
ahead of lap time. That request paused Phase 3/4 BC work; it did not authorize
RL, world model, offline RL, or submission. This records the original v2 request,
not a global current-status override for the independently updated BC plan.
Privileged vehicle state and track geometry remain allowed only for local
teacher generation and analysis, never as a learned policy input. Do not modify
`env_wrapper.py`, `damage.py`, or `core/`. Keep instrumentation external.
Preserve the frozen v1 controller/runner; v2 does not replace the BC teacher
implicitly.

## Checkpoints

- **2026-09-29 v2 pause checkpoint (user-requested):** separate
  `oracle/v2_controller.py` and `oracle/v2_runner.py` added; neither frozen v1
  controller nor supplied environment edited. Stage `speed` uses v1 obstacle
  path/pursuit, curvature speed limits 9-24 and no preview; matched IDs 1-5 x
  geometry seeds 1-3: **13/15 full episodes on 13/15 roads**, four damaged,
  14 collision-positive actions; successful laps mean 59.777 s, median 54.380 s,
  best 49.980 s. ID5/seed1 and ID5/seed3 crashed. Stage `braking` adds a
  forward reachable-speed envelope (5 units/s^2 nominal deceleration, 3-unit
  margin): **14/15 on 14/15 roads**, four damaged, 13 collision-positive actions;
  successful laps mean 66.591 s, median 60.970 s, best 55.820 s. ID5/seed1
  crashed. Artifacts: `runs/v2_speed_15`, `runs/v2_braking_15`; single-road
  preliminary probe `runs/v2_speed_probe` excluded from matrix denominators.
  Both stages are unsafe compared with frozen v1's historical 100/100 on 50
  roads (2 repeats), so neither is a selected teacher. The 15 roads are exposed,
  not holdouts; no racing-line/linked-corner/obstacle integration was attempted.
  Resume by inspecting first collision and braking/steering traces, then change
  only a targeted control mechanism and run matched complete episodes before
  layering additional strategies. Do not launch new runs until work resumes.
- **2026-09-29 resumed v2 checkpoint:** user resumed local teacher work.
  Curvature/braking-only failures were traced to aggressive longitudinal
  oscillation and consumed obstacle clearance. Gentle feedback produced a clean
  50/50-road baseline; independent out-in-out and forward acceleration-profile
  variants were rejected by matched lap/finish evidence. Coupled whole-loop
  curvature planning and joint local obstacle corridors were measured separately;
  an integration-range defect was fixed and its failed 3/15 result preserved.
  Default v2 is now `pace` in `oracle/v2_controller.py` / `oracle/v2_runner.py`.
  **100/100 complete episodes on all 50/50 exposed ID1-5/seed1-10 roads, 2/2
  finishes each, zero collision/damage**, versus frozen v1 100/100 with two
  damaged episodes. Mean/median/best lap 50.8052/49.570/40.840s versus v1
  85.9108/83.400/73.760s; ratio-of-means lap reduction 40.8628%, faster 50/50.
  All 50 repeated full trace pairs are byte-identical. Two source versions differ
  only in v2 defaults and removing unused initialization; **current final code
  is verified on the repeat50**, not 100 episodes under one source fingerprint.
  V1 controller/runner, supplied physics and Agent remain unchanged. No BC/RL,
  dataset collection, submission, commit or model confirmation occurred here.
  Artifacts `runs/v2_selected_first_t1` through `t5` and corresponding `repeat`
  directories; combined report in `runs/v2_selected_repeat_t1/combined_report.json`.
  Stage/behavior details and future dataset-use limits are in
  [../EXPERIMENTS.md](../EXPERIMENTS.md).
  Treat v2 as a promising local high-speed teacher alongside v1; private-track
  robustness and student imitability remain untested. No further tuning or new
  learning phase starts implicitly at this checkpoint.
