# 267: Actual-simulator optimization of eight spatial pace knots

The fixed small search finds only a marginal O0 improvement, and the frozen profile loses time on N0. Do not treat this road-specific schedule as a transferable improvement. No further generation, pace sweep or N0 retuning is run.

| Evaluation | Constant1.5 reused | Selected spatial profile | Difference |
|---|---:|---:|---:|
| O0 training best |19.70s |19.66s |−0.04s |
| N0 single transfer |20.20s |22.20s |+2.00s |

Both selected runs complete with damage0. The40ms training gain is small and not a robustness or optimality certificate. The N0 result was unavailable to the search and did not change the selection.

## Preregistered one-method search

Reuse exact258 free paths/base speed profiles and the original controller, including its positive35.01888 acceleration clamp, negative91.16873 bound, steering/cursor/lookahead/smoothing and action limits.266's unclamped controller is not used. Same simulator physics, initial seeds/observations, rendering, qualification and official finish semantics remain.

Optimize only **eight positive pace knots** at normalized cumulative path fractions0,1/8,…,7/8. Bounds1.0–2.0. A periodic monotone cubic Hermite interpolator in log pace uses fixed harmonic-mean slopes; it is C1, passes through the knots and stays within their bounds. The original speed array is multiplied by the interpolated pace at each fixed path node. The same squared-speed feedforward and speed feedback process that array; no control gain, geometry or extra speed law is fitted. This is a stress reference, not a feasibility proof.

Single CEM: NumPy default_rng/PCG64 seed267, three generations, population4. Each population has one cached best incumbent plus three new independent log-Gaussian samples. Initial meanlog1.5,std0.15; samples are clipped to log bounds. The two fastest completed candidates form the elite; update diagonal mean/population std(ddof0), with fixed std floor0.05. Only completed candidates enter the update; failure, censor and unexecuted statuses remain separate. Damage is diagnostic and never a cutoff. Stable earliest registration breaks exact time ties. The final candidate is the best actually evaluated O0 profile, not an unevaluated CEM mean.

The constant1.5 point starts the search with the exact265 result. A special constant-array case preserves its speed/lap-wrap arrays bit for bit; both-road numerical identity is checked offline. Completed incumbents are reused exactly, never rerun. No new global scalar gain sweep occurs: the nine new candidates vary eight spatial knots independently.

Before simulation, task cap8000 was split into training6000 and final transfer2000. Budget cuts would be censored and source retirements actual DNF; neither damage nor a tracking threshold ends a candidate early. In this run no budget cut or unexecuted candidate occurs.

## Actual O0 training results

| Generation | New complete /actual DNF /censored | Fastest new completion | Best including cached incumbent |
|---|---:|---:|---:|
|0 |3/0/0 |19.92s |19.70s |
|1 |2/1/0 |20.56s |19.70s |
|2 |3/0/0 |19.66s |19.66s |

Nine distinct new O0 simulator episodes: **8 complete,1 actual DNF,0 censored**. The failure `g1_p3` retires `off_track` at442 actions,186/326 tiles,damage0; it is not rejected by an arbitrary damage cutoff. All other new training runs also have damage0. The three cached incumbent entries in the populations are not counted as three new episodes or independent baseline measurements.

Completed new times by generation:20.34/19.92/20.24s;20.56/20.70s;20.62/20.70/19.66s. Winner `g2_p3` completes in246 actions with all326 tiles. Its tracking mean/p95/max is0.687/1.729/3.461m; the first>3m event is the final action246. This event is retained as a diagnostic, not retrospectively used to remove a valid official completion.

Selected knot range1.1461–1.6338, slowest knot at75% normalized arc, fastest at62.5%. Actual desired speeds do not scale lap time directly: changed spatial gradients alter braking/acceleration requests and closed-loop path tracking, and source/control limits still apply. The full knot vector and generation registrations remain private with a frozen selection SHA.

## Frozen N0 transfer and recommendation

The selected parameters were written and hashed before opening the N0 run. N0 uses those same knots on its own normalized fixed-route arc; there is no alignment to O0 curve locations, search update or selection based on N0. The one actual transfer completes in278 actions,325/325 tiles,damage0,22.20s. Its tracking mean/p95/max0.687/1.657/2.383m; no>3m event or contact. It is2.00s slower than cached constant1.5, and0.08s slower than original258 pace1.0(22.12s).

Training recommendation: the40ms gain does not justify expanding this tiny one-road phase optimizer as though it found robust headroom. Transfer recommendation: normalized arc positions do not align equivalent curves/traction demands across roads; the observed negative transfer is consistent with route-specific fitting. This search cannot certify that better spatial profiles do not exist, but it provides no transferable win.

Retain constant1.5 as a GT diagnostic comparator; do not adopt or select a new N0-based ratio. If further research is separately scoped, curvature/available-traction-conditioned parameters and independent DEV training/transfer gates are more informative than blindly adding phase-knot generations. No such follow-up, fresh road or HOLDOUT is opened here. This is whole-lap GT research, not pixel-only performance or a10s/optimality result.

## Native cost and preservation

Authorized research-only increment8000 recorded once: B912000→920000, starting cumulative824805, research11195, reserve84000. Actual **2758 native** =2480 O0 training +278 N0 transfer, below8000 task cap;11023 actual raw step ticks +510 reset ticks. Every fitness query runs the real simulator with rendering retained and is charged native, not hidden as model cost. No SourceVehicleTransition query/model physics tick or geometry solve occurs.

Total execution88.99s, actual episode wall88.76s, process CPU88.88s. Three CEM parameter updates; no new affine/neural training. All registrations, official outcomes, failed/censored statuses, selection hashes and transfer timing remain available privately. Constant1.5 full results are reused.

Cumulative827563; research remaining8437; final reserve84000 untouched. Champion240, main, Participants, backups, HOLDOUT and SEALED are preserved. Public artifacts contain small interpolation/search code and aggregate results; raw global maps, full candidate parameters/trajectories and personal records stay private.
