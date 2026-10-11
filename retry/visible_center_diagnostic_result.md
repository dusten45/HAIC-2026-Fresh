# Visible obstacle center diagnostic (stage126)

**Keep champion116. The intervention was inactive, so the center-error hypothesis remains unresolved.** The preregistered privileged diagnostic used the exact116 archive on the known failed DEV condition, with its cached baseline and a one-episode,2000-action ceiling. It was never a submission candidate. The global+1pixel margin variant is terminated; its archive is preserved.

The hook could replace only the centers of existing detections whose current visible ownership matched uniquely. It preserved detection count/order/radii, original path and tracker/controller source. Every component pixel needed ownership>=128, with at least one255; overlapping or unsupported matches stayed unchanged. Hidden layers were omitted. Seven pure helper checks and one saved-action packet check passed, but these checks did not establish live matching coverage.

| Recorded outcome | Result |
|---|---:|
| Existing detections / actions containing detections | 51 / 47 |
| Centers replaced / new detections | **0 / 0** |
| Insufficient visible support / unmatched | 46 / 5 |
| Ambiguous matches / component alignment mismatches | 0 / 0 |
| Endpoint, baseline and diagnostic | Crash at action181; damage1.0;104/300tiles |
| First damage, both | Action177 |

All181 actions and the complete observation stream have the same hashes as cached116. Insufficient-support decisions occurred at actions66–76 and138–172; unmatched detections occurred at23,143,147,162,164. Receipts do not distinguish failure of the>=128 condition from failure of the255 witness condition. No rerasterization or threshold adjustment followed the result.

The preregistered zero-replacement gate determines the conclusion: this result cannot reject a center-error explanation or establish a path/tracking cause. Before another native center diagnostic, validate the ownership/support matching against stored DEV evidence. No follow-up experiment was launched.

Cost: **181/2000 native actions,8.574s wall**,7.090s evaluator CPU and1.500s actor CPU;724 raw step ticks and51 reset ticks. The181 oracle-context calls took0.293s within that wall time and used62 label raster passes, with zero extra environment render/reset/step calls. There was one extra component extraction per action. The separate saved packet check used one policy reset and one action, no physics or model calls. Frozen source/module checks and initial reset hashes matched; the actor was reaped.

Native total605331; research remaining16669; reserve84000 untouched. Champion116 and rollbacks remain unchanged. Protected HOLDOUT details and SEALED stayed closed; seeds, private records and archives remain private. Authorization ends2026-10-16T10:01:55Z, with no extension or paid resources. Runtime execution passed; causal intervention coverage did not.
