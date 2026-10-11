# Fixed extra-pixel route margin (stage123)

**Passed the selected failure DEV; eligible for another DEV gate only.** The candidate completed in **49.680s with damage 0**, where frozen 116 crashed. Champion 116 and its rollbacks remain current; protected HOLDOUT details and SEALED stayed closed.

Cached precontact diagnosis found matching obstacle radius but sampled center errors of 0.306–0.616m. At action 164, the route's observed planning margin was +0.021m while the ground-truth margin was −0.329m. These margins use the existing 2.6m planner envelope plus obstacle radius, not exact vehicle fixtures. At 170, even the observed target chord lacked that clearance: localization and route/target tracking both remain possible contributors.

The preregistered change added exactly one horizontal input pixel, **1/1.3608 = 0.734861846m**, to connected-route obstacle exclusion. One source expression changed; 13 other archive members stayed byte-identical. Perception, tracking, target selection and control laws were preserved. Ground truth was used only for cached diagnosis. There was no threshold sweep or stage 122 bypass-side persistence.

| Same selected DEV | Cached 116 | Candidate 123 |
|---|---:|---:|
| Outcome | Crash | Completed |
| Lap | — | 49.680s |
| Damage | 1.0 | 0.0 |
| First damage action | 177 | None |
| Actions | 181 | 622 |

The first action difference occurred at 72; the preceding 71 actions, input frames through that decision and recorded state prefix matched exactly. This is a whole-episode routing-margin result, not identification of a sole cause near 164. A single selected failure cannot establish general reliability or justify champion adoption. The next useful gate is a fixed-candidate DEV regression check; none was started automatically.

Cost: **622/2000 registered native actions** (user ceiling 3000), **25.807s wall**, 21.582s evaluator CPU and 4.305s actor CPU. Baseline reruns and extra saved-policy/model calls: 0. Record streams matched and the actor was reaped. Native total 599181; research remaining 14819; reserve 84000 untouched. Seeds, archives and full records remain private. Official-server execution remains unverified.
