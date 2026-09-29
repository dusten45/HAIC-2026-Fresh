# Environment Contract (Phase 1)

Inspected 2026-09-29. Official Participants `main` was
`dfb7a2de2178825ca5c5ce20bab01ba67052ba31`, matching the local starting revision.
Environment version: `variables-6`. Source files below are unmodified.

## Source Authority

1. Current competition website:
   <https://scholarships-hardwood-headers-influenced.trycloudflare.com/>.
   The fetched public application bundle agrees that finishers rank first by
   lap time, then non-finishers by progress; failed evaluations are excluded.
   Its best-record leaderboard is distinct from a team's confirmed model.
   Static UI is not live server settings and does not specify simulator internals.
2. Current official template: <https://github.com/2026-HAIC/Participants>.
   README fetched and source revision checked on the date above. No conflict
   relevant to this local experiment was found. No submission/confirmation made.
3. Actual local code and execution. Results and commands are in `EXPERIMENTS.md`.

## Policy Interface Versus Privileged State

| Item | Contract |
| --- | --- |
| Policy observation | `(4,84,84)` grayscale `float32` in `[0,1]` |
| Raw observation | `(96,96,3)` RGB `uint8` |
| Preprocessing | resize, RGB-to-gray, divide by 255 |
| Frame stack | repeat final warmup image at reset; append final image of each action |
| Action | `[steer, gas, brake]`, bounds `[-1,1]`, `[0,1]`, `[0,1]` |
| Default control interval | 4 raw ticks at 50 Hz = 0.08 simulation seconds |
| Reset | `reset(seed=seed, options={"track_id": track_id})` |
| Exposed policy state | images only, no direct pose/velocity/geometry |
| Local privileged state | `env.unwrapped.car.hull`, wheels, `track`, obstacles, tile visits, finish tracker |

References: `env_wrapper.py:7-27,41-77`; `core/vendor/car_racing.py:201-211,459-596`.
Raw steps always render observations, including headless runs. The diagnostic
runner does not remove image rendering or alter physics.

Raw reset internally performs one tick; wrapper warmup adds 50 no-op ticks.
Normal post-reset `t` is 1.02 seconds. Use actual reset time as timing origin.
Warmup already changes tile visits and raw reward but does not appear in rollout
reward totals. Reset `info` is `{}` rather than enriched wrapper step information.

The official local runner validates/clips actions; direct `env.step` does not
provide equivalent full validation. Its ten consecutive invalid-action rule and
5-second action timeout are runner rules, not simulator termination. README
also specifies CPU Linux/Python 3.11, import/init 10 s, reset 5 s, memory 1,024 MB.
The privileged oracle intentionally is not a submission-compatible `Agent`.

## Coordinates and Actuators

For hull angle `theta`, forward is `(-sin(theta), cos(theta))` and right is
`(cos(theta), sin(theta))`. Local +Y is forward. Conventional world heading is
`theta + pi/2`. Dot waypoint displacement against forward/right for bearing.
Velocity can similarly be decomposed into longitudinal and lateral components.

Positive action steering turns right: raw physics calls `car.steer(-action[0])`.
The target is in joint radians, not an action scaled to maximum steering.
Front-wheel joints have physical limits +/-0.4 rad. Their response is rate
limited; damage reduces response speed. Wheelbase is `(80+82)*0.02 = 3.24` units,
with rear axle 1.64 units behind the hull reference. Gas drives rear wheels and
increases at most 0.1 per raw tick. Brake >=0.9 locks wheels; smaller brake values
reduce wheel angular speed. Source: `core/vendor/car_dynamics.py:17-25,90-193`;
`core/vendor/car_racing.py:542-558`.

## Track Representation

`track[i] = (alpha,beta,x,y)` is a cyclic ordered sequence. `alpha` is a generation
polar angle, not driving heading. `beta` defines the road cross-section normal;
forward is approximately `(-sin(beta),cos(beta))`. Use actual adjacent-point
differences for geometric tangents. Tile i joins point i-1 to point i.

Nominal waypoint spacing is 3.5 units, but measure the closing segment rather
than assuming uniform spacing. `TRACK_WIDTH = 40/6` is road **half-width**.
The oracle projects pose onto line segments, records signed lateral displacement
(positive left of forward tangent), and uses accumulated metric arc length for
lookahead and cyclic interpolation. Nearest-segment projection is not unique
tile progress; nearby sections could cause index jumps and must be diagnosed.
Road boundaries and decorative curbs are not physical walls.

References: `core/vendor/car_racing.py:57-66,276-456,523-533`.

## Declared Conditions

The initial experiment used IDs 1-4 x seeds 1-5. The user expanded the declared
scope to IDs 1-5 x seeds 1-10 on 2026-09-29, all exposed for development. With default
`domain_randomize=False`, seed determines road geometry; ID additionally changes
obstacle placement. The expanded set is **50 geometry/obstacle configurations,
10 base geometry seeds**, not 50 independent base geometries. The original set
contained 20 configurations / five geometries. No holdout claim is made.

Each has six physical circular obstacles of radius 1.2. Placement excludes the
first 10% and last 5% of waypoints, with at least 20 indices between obstacles.
Offsets span +/-4 from the centerline, so centerline pursuit can hit obstacles.
Grass friction is 0.6. Omitting track ID removes obstacles and is NOT an equivalent
test. Enabling domain randomization consumes RNG before track generation and
can change geometry even with the same seed. Full geometry and obstacle specs
are recorded in each run's metadata.

References: `core/track_variables.py:9-18,36-71,95-148`;
`core/vendor/car_racing.py:465-522`.

## Reward, Finish, and Failure

- First visit to a tile: `+1000/N`; each raw action tick: `-0.1`.
- Progress: unique visited tiles divided by N, not ordered lap completion.
- Qualification: visit at least 95% of tiles. This alone is NOT a finish.
- Finish: leave start area, qualify before entering the gate from behind, cross
  center in the forward direction within the lateral gate, then clear its front
  boundary. Finish time is the center-crossing physics tick, not confirmation.
- Success sets `truncated=True`; use `finish_time_s is not None` / `finished`.
- Wrapper off-track: 101 consecutive negative *summed action rewards*. Stopping
  on the road, revisiting tiles or insufficient progress can trigger this; it is
  not a geometric boundary test. At skip 4 this is about 8.08 seconds.
- Playfield exit: `abs(x)` or `abs(y) > 2000/6`, raw termination and reward -100.
- Collision: raw contact flags OR-reduced across frame skip; damage increases
  0.2 once per collision-positive wrapper action, retiring at 1.0. Grip/engine/
  steering response degrade. The obstacle contact latch is not reference-counted
  across fixtures; do not interpret wrapper flags as exact distinct impacts.
- Default runner cap: 2,000 actions, about 160 simulated seconds after reset.
  Official local runner also wraps a raw TimeLimit of `2000*4+200`. Its outer
  action cap can stop without either environment done flag. Record separately.

References: `core/vendor/car_racing.py:94-137,560-596`;
`core/finish_line.py:41-95`; `env_wrapper.py:58-110`; `damage.py:3-40`;
`core/obstacle_contacts.py:34-43`; `local_runner.py:62-72,94-129`.

Lap time is `round((finish_time_s-post_reset_t)*1000)` milliseconds. Reward and
diagnostic errors are internal proxies, not ranking scores. Typical *observed*
episode lengths depend on controller and are reported with full episodes in
`EXPERIMENTS.md`, rather than inferred from a Gymnasium default episode limit.

## Verification Boundaries

Original tests: 15 passed, server parity test skipped (server absent). No server
repository content was read. Subsequent commands select local test files to
avoid importing the optional sibling-repository parity probe. These unit tests
alone do not establish real steering or finishing behavior; actual diagnostic
and oracle episodes provide that evidence. No original environment file is
instrumented, monkeypatched, or changed.
