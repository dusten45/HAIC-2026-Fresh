# Stage135: route selection alone on the actual116 champion

**Keep 116.** Frozen 135 and cached 116 both complete 3/4 DEV. There is no new
completion or common-completion time gain. This closes the route-only check.

134 was not 116 plus routing alone: its detector and tracker also differed.
135 copies exactly 134's `connected_agent.py` and `schedule_agent.py` onto the
actual 116 archive. The other twelve members, including detector, tracker,
controller and fixed-HUD pedal feedback, are byte-identical to 116. No 128–132
perception changes or parameter adjustment enter 135.

The same stored candidate pool and controller state feed zero/one-weight
scorers. Both compute the steering connection term. On 42 inputs, zero weight
reconstructs every 116 action; weight one changes one action. This controls
stored computation, without claiming identical historical native CPU.

The known pair has no completion loss relative to 116. 135's 43.820s completion
is 1.220s faster than 134, while 134 completes the other 135 DNF. This passes the
pre-registered **complementarity** continuation gate. It is not a promotion.
The same 135 then runs the remaining two DEV; no baseline is rerun.

| DEV reference | Cached 116 time / damage | Frozen 135 time / damage |
| --- | --- | --- |
| Known clean | 43.820s / 0.0 | Exact same actions and observations |
| Known failure | DNF, 104/300 tiles / 1.0 | DNF, 104/300 tiles / 1.0 |
| Remaining A | 46.100s / 0.6 | 46.140s / 0.4 |
| Remaining B | 45.300s / 0.8 | Exact same actions and observations |

No new or lost completion. Among the three common completions, median lap
delta is 0ms and mean time ratio is 1.000289. Damage decreases by 0.2 on one
common completed case and is a separate diagnostic, never an automatic veto.

| Known DEV | A: 116 | P: 131 perception | R: 135 route | P+R: 134 |
| --- | --- | --- | --- | --- |
| Clean | Complete 43.820s | DNF | Complete 43.820s | Complete 45.040s |
| Failure | DNF | Complete 48.500s | DNF | Complete 48.500s |

P bundles multiple detector/tracker edits. R rescues the P-context failure,
but R alone does not rescue 116's failure; P alone already completes that case.
This selected-pair component comparison shows context dependence. It does not
establish universal component necessity or steering lag as the sole cause.

135 selects one alternate at input 164 on the known failure and one at 388 on
remaining A. Both first differences have the same pixel input and controller
state as 116. Subsequent trajectories differ. The known failure retires after
180 actions versus 116's 181, with the same tile progress. Precontact steering
metrics remain auxiliary to the native completion/time outcomes.

Cost: **1872/6000 new native actions**, zero baseline reruns, extra calls or
retries. Two phases take 81.624s wall including records, 66.827s evaluator CPU
and 14.940s actor CPU. Four actors are reaped; no extra observer inference.
Research remaining **9371**, final reserve **84000** untouched. 116 is frozen;
HOLDOUT details and SEALED stay closed. Archives, frames, traces, geometry and
private plans stay private. No further native experiment is launched here.

A useful next question is whether the unchanged combined 134 retains its known
completion advantage on remaining DEV versus cached 116; that is unexecuted.

[Reproducible builder](champion_connection_candidate.py) copies two frozen
members without environment or policy execution. Building again reproduced
the exact 135 ZIP hash. [Aggregate evidence](champion_connection_result.json)
records outcomes, source boundaries, gates, costs and provenance.
