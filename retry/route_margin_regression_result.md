# Frozen route-margin regression comparison (stage124)

**All three completions were preserved, with a time cost in every case. Champion 116 remains current.** The exact stage 123 archive was evaluated on the other three DEV121 cases, reusing the original 116 endpoints. No margin adjustment followed the results.

| Completed DEV | Baseline 116 lap | Candidate lap | Time increase | Baseline damage | Candidate damage |
|---|---:|---:|---:|---:|---:|
| 0 | 46.100s | 46.540s | +0.440s | 0.6 | 0.0 |
| 1 | 43.820s | 44.580s | +0.760s | 0.0 | 0.0 |
| 2 | 45.300s | 45.740s | +0.440s | 0.8 | 0.0 |

Completion losses: **0/3**. Common-completion median lap delta: **+0.440s**; mean paired lap ratio: **1.01220039**. All three laps increased; DEV 1 damage was unchanged. Total damage was 1.4→0, a descriptive comparison with different driving exposure. The existing directional lap rule returned `KEEP_CHAMPION_MIXED_OR_NO_LAP_GAIN`.

Together with stage 123's selected failure rescue, the fixed candidate completed 4/4 of these DEV cases versus 116's 3/4. This supports a completion/time tradeoff on this selected set; it does not establish general reliability or justify adoption.

The setting remained obstacle exclusion `2.6 + radius + 1/1.3608`, adding exactly one input horizontal pixel (0.734861846m). The candidate archive and observer were identical to stage 123. The existing runner's maximum expanded from two cases/4000 actions to three/6000; per-episode limit 2000 and execution/scoring logic stayed the same. Technical failure would stop without retry; normal DNF would remain in the registered comparison. All three reset records and recorded streams matched, and all actors were reaped. Independent endpoint and receipt review passed.

Cost: **1712/6000 registered native actions**, **74.159s wall**, 62.497s evaluator CPU and 11.899s actor CPU. Baseline reruns and extra saved-policy/model calls: 0. Native total 600893; research remaining 13107; reserve 84000 untouched. Champion 116, rollbacks, protected HOLDOUT details and SEALED were preserved. No next run started. Seeds, archives and full records remain private; official-server execution remains unverified.
