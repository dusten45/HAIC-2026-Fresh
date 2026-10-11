# Fixed bypass-side persistence (stage122)

**Rejected: no new completion.** Two candidate-only DEV runs reused the121 champion endpoints. Champion116 remains current; no HOLDOUT or SEALED was opened.

| Condition | Baseline116 | Candidate122 | First damage action | Damage |
|---|---|---|---:|---:|
| Previous failure | Crash181 | Crash180 | 177 → 173 | 1.0 → 1.0 |
| Completed control | 43.820s | 43.820s | None | 0 → 0 |

On the failure, first target-sign reversal moved164→167 and reversals before first damage fell4→1, but contact started0.32s earlier. First action difference was164: prior163actions and the current pixels/truth/controller/HUD/feedback/tracker numeric state matched. The target changed +0.735→−3.090m; this was a route-choice intervention, with the original steering and pedal law preserved. The completed control retained all548actions,549frames and recorded truth exactly.

The rule was fixed before results: acquire the original route's side for the nearest nearby tracked obstacle crossed by that route; retain that side while a connected route reaches the original goal; release on lost track, passed obstacle or unavailable retained-side path, then wait one action before reacquisition. Existing2m tracker association and existing near/grid/clearance constants were used without sweeping. In the critical sequence, side−1 was held160–166, released167 as disconnected, then side+1 was acquired168. Exactly3archive members changed for routing and identity metadata; the Dijkstra body and11other members stayed identical.

Target sign does not equal obstacle-relative bypass side, and precontact exposure differs. This fixed rule did not rescue the failure; the earliest initiating cause remains unidentified. No second candidate or threshold search was started.

Cost: **728/4000 native actions**, **29.843s** wall,24.840s evaluator CPU and5.085s actor CPU. Baseline reruns and extra saved-policy/model calls:0. Native total598559, research remaining15441, reserve84000 untouched. Seeds, full records and archives remain private.
