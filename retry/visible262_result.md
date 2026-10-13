# 262: Local target/reference validity diagnosis — guard rejected

The N0 action97–103 observation is complete. Coordinate, arc-length and speed/acceleration arithmetic are internally consistent. A retained target moves behind the hull as tracking alignment deteriorates. A single validity guard was tested once on both roads; it loses both completions and is rejected. No threshold, deceleration rate, learning or hyperparameter search was added.

## Exact prefix diagnosis

Replay saved N0 stages260/261 controls to103 once each,206 charged actions. Controller recomputation matches every stored action bit for bit; speeds, damage and visited tiles match. Existing261 late receipts are reused. Only14 selected pre-action rows and four small plan receipts were newly retained privately.

| Trace | Plan creation | Target along hull forward | Target along velocity | Arc / goal / length | Feedforward + feedback → command acceleration |
|---|---:|---:|---:|---:|---:|
| 260 action100 | 100 | +6.02m | −1.81m | 0.00 /12.92 /24.59m | 34.04 +0.00 →34.04m/s² |
| 261 action100 | 97 | +5.15m | +9.95m | 6.66 /19.58 /31.53m | −2.39 +5.46 →3.07m/s² |
| 261 action101 | 97 | +0.16m | +5.98m | 8.68 /21.64 /31.53m | −2.39 +5.05 →2.66m/s² |
| 261 action102 | 97 | −3.46m | +1.16m |10.01 /22.96 /31.53m | −2.39 +4.96 →2.57m/s² |
| 261 action103 | 103 | +8.53m |+11.13m |0.00 /13.25 /18.78m |0.00 −22.59 →−22.59m/s² |

The cached97 path retains its world coordinates and arc origin. Its projected arc advances monotonically0→0.97→4.15→6.66→8.68→10.01m during97–102. The target remains within that path, so this episode is not a tail-extrapolation or stale arc-origin error. A newly accepted103 plan legitimately resets arc to0; speed and acceleration use that new plan together.

Speed interpolation uses the squared-speed endpoints of the same closest segment; feedforward uses their difference divided by2*segment length. At261 action102 desired speed47.47m/s is below the local curvature cap57.83m/s, actual speed magnitude44.16m/s, so the recorded positive feedback follows the implemented formula. No mixed plan arrays, units, coordinate transform or arithmetic bug is demonstrated.

The physical alignment assumption is weak: plan-tangent dot velocity-direction falls0.706 at100→0.309 at102. At102 velocity is approximately13.65m/s along the path despite44.16m/s magnitude. Hull and velocity also differ (dot0.928). A model that treats the scalar speed as reference-path speed assumes tracking alignment; changing it to a projected velocity would change the model/control problem, not repair a proven arithmetic bug. No such change was made.

This separates261's earlier failure from its late reversal example: at100 its direction memory makes the new forward chain unavailable, retaining97 instead of260's newly accepted reverse-direction path. Its target rotates behind the hull by102 while the reference continues requesting acceleration, then103 introduces a much lower speed reference30.43m/s at actual45.49m/s. Those observations establish a closed-loop tracking/reference failure, not an isolated first cause or a general future-information effect.

## Single diagnostic change

Starting from261, if the selected target has nonpositive displacement along the hull's forward vector, invalidate that plan and invoke the exact existing no-plan action(previous steering,gas0,brake0.1) until a scheduled replan succeeds. The geometric boundary is0; there is no new tuned threshold or braking rate. Provider, direction memory, solver, constraints, speed model, gains, replanning cadence and nonzero tail stay fixed. No global map or259 future plan is loaded.

This tests a forward-reference validity policy. A target behind the hull is observed; it alone does not prove a coordinate or physics-model code bug. The guard cannot be described as a successful bug fix.

## Actual paired outcome

| DEV road | Cached240 | Cached259 global GT | Cached260 local | Cached261 | Guard262 |
|---|---:|---:|---|---|---|
| O0 |23.66s |22.52s |26.06s complete |26.06s complete |off_track469,damage0,302/326 tiles |
| N0 |23.62s |21.74s |crash313 |crash130 |off_track170,damage0,82/325 tiles |

O0 first changes at60, with expiry actions60/140/368/380. N0 first changes at71 and expires only at71. Thus both branch before the diagnostic97–103 interval; this actual test does not isolate the action102 intervention.

O0 last gains a tile at368, N0 at69. Their terminal speeds are approximately zero. No-plan fallback is used101/100 actions; late O0 receives seven road segments but cannot produce a connected valid plan, whereas late N0 receives zero. The source `off_track` retirement reflects no new progress, not proof of geometric departure from all road wheels. The existing fallback stops the vehicle without recovering a valid path. Removing collisions while losing completion is not an improvement. The preregistered two-completion gate fails; stop with no variant search.

The next minimal observation, if separately requested, is the first invalidation-to-replan transition(O0 58–64;N0 67–76): selected target direction, actual velocity/tangent, segment connectivity and feasibility, and whether stopping preserves any observable reconnectable geometry. It should precede another pedal or validity change. No extra run was performed here.

## Cost and preservation

206 diagnostic-prefix +639 candidate = **845 native**,3380 raw step ticks +204 reset ticks,44.03s combined execution wall time. Geometry objectives1550 diagnostic +3575 candidate; zero positive-time model physics queries. Candidate inference median/max replanning48.55/122.39ms on O0 and32.91/57.25ms on N0.

Cumulative821928; research remaining2072; reserved84000 untouched. Both candidate roads ran once to source terminal. Full240/259/260/261 results were reused. No new scenario collection, fitting, champion adoption, HOLDOUT or SEALED. Frozen contracts, hashes, full geometry/target traces and replay receipts are private; public artifacts contain code, aggregate results and selected scalar evidence. Main, Participants, champion240 and existing backups remain preserved. No10s bound or pixel impossibility claim follows.
