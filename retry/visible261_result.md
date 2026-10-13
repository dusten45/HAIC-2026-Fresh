# 261: Observed local-route direction memory — rejected

One recovery was frozen and tested once per DEV road. O0 is unchanged; N0 crashes earlier. No further tuning, ratio search, new scenario collection, fitting, champion change, HOLDOUT, SEALED or reserve use.

| DEV road | Cached240 | Cached259 global GT | Cached260 local GT | Direction-memory261 |
|---|---:|---:|---|---|
| O0 | 23.66s | 22.52s | 26.06s, damage0 | 26.06s, damage0; all326 controls identical |
| N0 | 23.62s | 21.74s | Crash action313,144/325 tiles | Crash action130,99/325 tiles |

## Minimal pre-failure diagnosis

Saved260 records did not include complete local geometry or plan endpoints. Exact saved controls were therefore replayed once to O0 action184 and N0 action308, before N0's first collision309. Those492 actions were charged. Every replayed step matched recorded speed exactly and matched damage/visited tiles. There were15 selected O0 and14 selected N0 geometry/plan receipts, retained privately. Full baseline results were reused, not re-evaluated.

O0's visible plan shortened from24.9m at49 to11.1m at52, with speed reference65.2→37.6m/s. At55 a new plan violated constraints, at58 the accepted plan changed steering by+0.561, and at61 only two road segments were supplied so no new plan existed. Later unavailable/invalid plans repeat. This demonstrates local truncation, constraint rejection and abrupt replanning, without establishing their individual lap-time effects.

N0's late accepted plans also shorten (28.9m at268→14.3m at271), followed by a constraint rejection274 and steering change+0.506 at277. At292, the newly selected centerline reverses **four exact segments** previously selected at277. The implementation chooses the closest segment's direction anew using instantaneous hull heading. After the hull turns, this can reverse an already observed route. No global road IDs or259 path were needed to establish the reversal. At295/298 there are zero supplied segments; at304/307 a new chain is unavailable and old plans remain. None of the selected receipts establishes that the vehicle has passed the retained endpoint along its tangent; simple endpoint overrun is not established as the cause.

No coordinate transform or segment-order bug was demonstrated. The confirmed discontinuity is loss of previously chosen travel direction. It occurs after substantial tracking drift and need not be the first cause of failure.

## Single recovery

Remember only the directed endpoints of previously observed and connected local center segments. For a known closest segment, orient it by this memory; for an unknown segment, keep260's hull-heading rule. Stop a chain if it conflicts with remembered direction. New paths still contain only current visible segments. Visibility filtering, closest-segment selection, six-variable solver, geometry constraints, speed model, controller, three-action replanning, nonzero unknown-tail boundary and old-plan fallback remain fixed.

On saved late N0 geometry, the fixed rule supplies a feasible forward plan at289 where260 had none. At292 it rejects a backward chain instead of using it. This offline gate uses the original observed geometry, with no global reference path and no physics rollouts.

This differs from retaining an H12 action/rollout prefix:261 stores segment direction only. It loads, freezes and extends no H12 control sequence. Path, speed reference and control are recomputed from current visible geometry every three actions; old feasible-plan retention is the unchanged260 fallback.

## Actual result and limit

O0's entire326-control sequence matches260 bit for bit. N0 matches through99; at100 the direction-consistent chain is unavailable, so it retains the earlier plan. Steering at100 changes from−0.233 to+0.371 and gas0.581→0.052. First collision126 is followed by repeated collisions to130. Replanning and fallback together can still produce unsafe recovery. The candidate fails the preregistered completion gate and is rejected.

This shows that preserving observed direction alone does not repair the controller. It does not show that reversing direction was safe, identify the first underlying drift cause, or isolate the effect of unseen future terrain. Global/local differences remain confounded; no10s bound or pixel impossibility claim is made.

Before another experiment, the smallest useful observation is at N0 actions97–103: signed body/velocity direction, chosen remembered edge direction, retained-plan age and target point, and speed feedforward/feedback terms. Existing261 receipts identify the first divergence but do not retain all these quantities. No extra observation run was performed.

## Cost and preservation

492 diagnostic-prefix actions +456 candidate actions = **948 native**,3791 raw step ticks +204 reset ticks;50.36s combined execution wall time. Geometry objectives:3625 diagnostic,3525 candidate,450 offline gates, zero positive-time model physics queries. One offline receipt script hit a reporting TypeError; correcting its reporting did not change the candidate or repeat any native run. Candidate replanning median/max was46.94/71.98ms on O0 and47.09/90.57ms on N0.

Cumulative821083; research remaining2917; reserved84000 untouched. Frozen contracts, hashes, replay checks, raw observations/plan receipts and accounting remain private. Public code uses a stage-directory CLI for diagnosis; the private executed-source copy records the original identical diagnostic body. Current champion240, main, Participants, existing archives and user changes remain preserved.
