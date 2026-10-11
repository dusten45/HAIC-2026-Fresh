A fixed HUD speed-bar decoder used only for pedal feedback passed one registered two-condition DEV contrast. Both policies completed both conditions with zero observed damage. Mean lap time changed from **58.710 s to 52.210 s**; median paired change was **−6.500 s** and mean paired time ratio **0.890379**. This is a descriptive result on reused DEV conditions. The current Stage 113 champion and both rollback archives remain unchanged; promotion was excluded by the contract.

The diagnostic used only four existing current-champion DEV recordings from Stages 113 and 115: 2,622 actions and 209.60 s of finish-clipped driving time. The global 40 m/s cap bound the target for 28.51% of this time; the pursuit-curvature target bound it for 71.49%. The existing near-hazard rule actually lowered the target for 28.80 s. These are target-constraint occupancies, not a decomposition of lost lap time or support for raising the global cap.

Selected paths were never empty or shorter than the requested lookahead. Their minimum length was 17.288 m against a maximum 14 m lookahead, with no endpoint-truncated targets. Front steering-joint command error had a post-step 95 th percentile near 3.09e−7 rad, which does not support persistent steering-servo lag. The hull's distance five actions later from the earlier selected path had a 95 th percentile of 0.969 m. That path and the observed pixel ridge are not the true road centerline; synthetic origin connectors also limit the geometric interpretation.

The old HUD reader had finish-weighted mean absolute speed error 2.445 m/s; the source decoder reduced this saved-observation error to 0.620 m/s. Its bias was negative in the first progress quarter and positive in the second on every recorded road. Progress alignment used first-visited-tile fraction within each road, not route arclength or identical physical states. A constant speed offset was therefore rejected. Fixed-target arithmetic found 26.80 s of braking when true speed would instead call for gas and 19.10 s of the converse. Neither duration measures recoverable lap time.

The old ROI's outer column varied while the speed-bar core pattern stayed identical. Official renderer geometry provided a fixed 18-byte core signature at rows 74:83, columns 11:13. The published 65 templates follow the 1000×800 indicator,96×96 pygame smoothscale and 84×84 OpenCV grayscale pipeline. Exact matches return 2.5 m/s bin midpoints, with a special zero signature; unmatched inputs use the old estimate. There was no fitted coefficient or alternate-ROI search. All 2,622 existing observations matched, and each error stayed within 1.25 m/s. Structural score-font overlap is plausible from source coordinates; an exact reward-glyph counterfactual was not rendered.

Only gas/brake feedback uses the new decoder. The old HUD value still drives tracking, the near predicate, lookahead, selected path/target and steering. Pedal gains, curvature handling and the 40 m/s cap remain fixed. Later closed-loop trajectories and steering can still differ. The builder patches two existing source members and adds one decoder module; the other eleven members remain byte-identical.

Before native execution, the read-only observer reproduced 2,622 saved actions exactly. The plain candidate then matched the analytically expected action on all 2,622 saved observations, including unchanged steering; 2,146 pedal actions changed. Six mocked gate scenarios exercised DNF/censor continuation and technical/readiness/order/qualification stops. These checks used no new environment steps. The observer is for the old champion; candidate qualification and native execution use the clean pixel worker.

The frozen contract allowed only two candidate runs, in the original order of two Stage 115 baselines, at most 2,000 actions each and 4,000 total. Baseline archive, configuration, environment, road/obstacle geometry, initial physical state and pixels were checked before candidate action. Source/runtime hashes, a one-use claim, resource/deadline checks and a charge ledger guarded execution. Normal DNF/censor would continue the second condition; a technical failure would stop without a retry, replacement condition or parameter change. Completion was evaluated before common-completion time. Damage was reported separately, without a safety claim or damage veto.

| Registered comparison | Aggregate result |
| --- | --- |
| Completion, baseline / candidate |2/2 /2/2|
| Lost completion / censor / inconclusive |0 /0 /0|
| Mean actual lap, baseline / candidate |58.710 s /52.210 s|
| Median paired lap change |−6.500 s|
| Range of paired lap changes |−7.820 to −5.180 s|
| Mean candidate/baseline lap ratio |0.890379|
| Observed damage sum, baseline / candidate |0 /0|

Independent saved-record review confirmed identical pixels, prior actions and physical state through the first action branch in each condition. Steering remained identical at that branch and the pedal change matched the new scalar feedback formula. One branch increased gas and the other decreased it. All 1,307 new candidate observations matched the frozen templates, with no fallback; per-run speed MAE was 0.624–0.629 m/s. The clean worker did not record every internal target/memory value, so no full-run same-input intervention rate is inferred. The two baseline runs were reused, and official-server/fresh-machine parity remains unverified.

| Measured work | Calls | Wall seconds | Actor CPU seconds | Evaluator CPU seconds |
| --- | ---: | ---: | ---: | ---: |
| Stage 115 native |2,961 wrapper steps|118.257|18.520|98.867|
| Stage 115 saved-policy inference |4,740 policy calls|32.556|25.669|unreported here|
| Stage 116 native |1,307 wrapper steps|51.571|8.077|43.622|
| Stage 116 saved-policy inference |5,244 policy calls|41.344|31.172|10.712|

Stage 116 native used 5,223 raw 20 ms step ticks and 102 reset ticks; reset ticks are reported separately from the wrapper-action allocation. The native wall includes record writing. Its nested environment-step timer was 39.358 s and reset timer 0.691 s, already within the native span. Saved-policy inference used eight cold starts/eight resets and zero native environment calls. Its observer and candidate phases took 21.403 s and 19.941 s. Source analysis and 65 synthetic HUD raster calls have separate private timers. These phase timers are not a complete measure of project elapsed time.

The previous one-for-one subtraction of 4,740 offline calls from the native balance is corrected. Stage 115's 7,701 mixed calls are not a native-cost unit, and its 7,007 mixed-unit remaining figure is superseded. The reconciled pre-experiment native balance was 11,747. After this experiment the ledger is **587,560 native used +10,440 research remaining +84,000 reserved =682,000**. No reserve or B increase was used, and prior ledger snapshots remain preserved.

Historical offline metadata supports a lower bound of 34,600 saved-policy calls,273.978 s of reported work spans and 127.752 actor CPU seconds. Historical native wall metadata covers 236,385 actions across 47 disjoint execution groups, totaling 9,456.681 s of reported execution spans; 351,175 native actions remain outside that wall coverage. These sums include distinct timer scopes, including parallel-worker sums and batch elapsed spans, and are not whole-project elapsed time. Missing historical wall/CPU or raw-tick measurements are unknown, not zero. The initial 293,383 native actions remain an accepted historical aggregate rather than a new raw-step audit.

Existing B is an operating allocation based on available resources and measured throughput, not a daily wall quota or a physical capacity guarantee. Recent conservative serial throughput was 25.039 native actions/s; the remaining research allocation represents about 417 s of serial native work and the reserve about 3,355 s under that conditional rate. Development, analysis, offline inference and downtime must be budgeted separately. The designated cloud snapshot had a four-core CPU quota,16 GiB memory and about 29.76 GB free disk. The authorization ends **2026-10-16 T 10:01:55 Z** without automatic extension; authorized hours do not guarantee compute uptime.

The earlier near-only curvature restoration remains slower on its two DEV conditions with zero damage in both arms. That evidence does not establish absence of a safety benefit elsewhere. This result also does not establish broad safety, a sole lap-time bottleneck, global-cap headroom, or performance on unseen conditions. Protected HOLDOUT details and SEALED data stayed closed. The next question is whether this frozen pedal decoder retains its completion and time benefit on new DEV conditions, before any broader gate or promotion.

The source builder, fixed templates, observer and guarded runner are published with [aggregate machine-readable results](hud_feedback_dev_result.json). Private plans, seeds, case identities, full records and candidate archives remain outside the repository. Reproduction requires the matching baseline archive and authorized private inputs in the recorded runtime:

```sh
python -m retry.build_hud_feedback --source BASELINE.zip --templates retry/hud_bar_templates.json --destination CANDIDATE.zip
python -m retry.hud_feedback_dev --plan PRIVATE_PLAN.json
```

The runner requires a frozen plan with matching source/runtime hashes and readiness receipts; the aggregate result is not an executable plan. Exact template matching is tied to the recorded raster/dependency pipeline and falls back on unmatched inputs.
