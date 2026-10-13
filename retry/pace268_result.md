# 268: Three road-common curvature/acceleration conditions

The frozen three-coefficient expression improves both O0 training and one N0 transfer by0.30s relative to constant1.5. It is promising GT diagnostic evidence, with two failed training candidates and no broad safety/optimality claim.

| Evaluation | Reused constant1.5 |268 selected |267 phase-knot selected |
|---|---:|---:|---:|
| O0 training best |19.70s |**19.40s** |19.66s |
| N0 frozen transfer |20.20s |**19.90s** |22.20s |

Selected268 completes both roads without damage, collision or>3m tracking error. Relative267: O0−0.26s,N0−2.30s. This is one known DEV transfer, not a fresh HOLDOUT or pixel result.

## Preregistered representation

Keep exact258 free paths/base profiles and the original controller, including positive35.01888/negative91.16873 acceleration bounds, steering/cursor/lookahead/smoothing and actuator clipping. No267 location knots or266 clamp release.

Three coefficients `beta_lat`, `beta_drive`, `beta_brake`, each in[−0.2,0.2], act on three local conditions:

- **Curve pressure:** approximate lateral demand `M*q²*|curvature|` divided by four-wheel road friction1600N.
- **Acceleration demand:** positive local squared-speed gradient of the curvature envelope compared with approximate available rear traction and engine acceleration. This distinguishes opening curves from steady straight/steady-radius travel.
- **Braking demand:** negative envelope gradient compared with approximate brake/remaining friction acceleration. This distinguishes entry into tighter curves from acceleration exits.

`q` is1.5 times the existing curvature cap. Drive availability uses the smaller of rear remaining force/(M+two-front-wheel rotational inertia) and80000/(q+2.7)/effective mass. Brake availability uses the smaller of the original91.17 allowance and total remaining force/M. Demand/(demand+availability) gives bounded drive/brake features. A fixed3.24m-wheelbase Gaussian smooths features using **relative cyclic arc distances only**.

Pace is `clip(1.5*exp(features @ beta),1,2)`, multiplied into the unchanged original base speed nodes. All-zero coefficients reproduce constant1.5 exactly, including the existing lap-wrap branch. No absolute progress, normalized phase, road ID or left/right label enters the expression. Cyclicly shifting geometry shifts the output with numerical error<1e−12; a nonzero diagnostic vector produces genuinely nonconstant speed ratios. The original global path cursor remains only in the unchanged follower.

Source values include400N friction per road wheel, total80000 engine power,I1.6,R0.54,dt0.02, body-shape mass and wheelbase3.24. **Assumptions** include all-road/grip1, equal lateral demand across axles, point-mass lateral force, rolling effective mass/no-slip engine proxy and original brake0.3 allowance. The remaining-force circle is an approximation, not exact telemetry or a calculation of real vehicle limits from one friction constant. `q` may exceed the numerical100m/s solver ceiling. Actual objective handles approximation error; no planned-feasibility certificate follows.

This differs from a global pace scalar: coefficients separately weight steady curves, opening/accelerating sections and tightening/braking sections. Straight regions with little condition demand remain near1.5. Still, the selected profile only spans about1.50–1.55 and mostly raises aggressiveness. Without an additional matched scalar comparison, its gain cannot be fully attributed to conditioning rather than the modest overall pace increase. No scalar grid or extra comparison was run.

## Fixed O0 search and frozen transfer

One CEM, seed268/PCG64, population4,two generations: one exact cached incumbent plus three new Gaussian coefficient vectors per generation. Initial mean0,std0.10; coefficient clipping to bounds. Two fastest completed elites update diagonal mean/population std with fixed0.03 floor. Damage is diagnostic, not a filter. Failure/censor/technical error stay distinct; earliest registration breaks exact time ties. Only O0 official completion/time selects an actually evaluated candidate; never the unevaluated mean.

Task cap5000 split training3000 plus transfer2000 before execution. Baseline constant1.5 is the zero vector and its exact265 result is reused. Six distinct new O0 runs:

| Generation | New complete /actual DNF /censored | Fastest new completion | Best including baseline |
|---|---:|---:|---:|
|0 |1/2/0 |20.22s |19.70s |
|1 |3/0/0 |19.40s |19.40s |

Actual complete4/6,DNF2,censored0,technical errors0. Failures `g0_p1`/`g0_p3` retire `off_track` at254/372 actions,184/140 tiles,damage0; no arbitrary damage cutoff removes them. Completed times20.22,19.46,20.14,19.40s. Cached population entries are not counted as independent new baseline episodes.

Winner `g1_p3` is hashed before opening N0. Its coefficients remain private and unchanged through transfer. Same expression/coefficients apply directly to N0's curvature/margin conditions; no curve-position alignment, road-specific recalibration or N0-based selection occurs. O0 tracking mean/p95/max0.731/1.694/2.097m; N0 0.683/1.724/2.269m. Active pace ranges1.5001–1.5530 and1.5001–1.5549. Actual median speeds56.90/57.39m/s still lag target medians79.88/81.39; the optimized reference is not literally achieved.

## Interpretation and next recommendation

Unlike267's marginal40ms training gain followed by2s transfer loss, this smaller common-condition expression improves both tested roads. That supports retaining it as a **frozen GT diagnostic candidate**. It does not prove that fewer degrees of freedom caused the gain:268 uses a different seed, six rather than nine new search episodes, different parameterization and a small increase above1.5.

The search's two failures show that the allowed coefficient region is not uniformly safe. Before expanding optimization, a separately requested check of the frozen candidate on other DEV conditions would be more informative than more phase knots or gain sweeps. No such run, newHOLDOUT, post-N0 update or participant promotion occurs here.

## Cost and preservation

**1867 native** =1618 O0 search +249 N0 transfer, below5000 cap.7465 actual raw step ticks +357 reset ticks. Rendering retained; every simulator fitness episode is charged native. Model physics queries0; seven numerical conditioned-profile constructions and two CEM updates are ordinary CPU computations. No new geometry solve or affine/neural training.

Execution69.44s, actual episode wall69.12s, CPU69.31s. Cumulative829430; research remaining6570; reserved84000 unused; B920000 unchanged. Champion240, main, Participants, backups, HOLDOUT and SEALED remain preserved. Raw GT maps, parameter registrations, complete traces and freeze/transfer receipts stay private; public artifacts contain small code and aggregate evidence.
