# Global target ceiling on the original champion

This experiment keeps the actual champion's pixel processing, HUD calibration,
hazard schedule, steering, routing and pedal gains. The only intervention is the
global target ceiling from 28 to 40. It adds no learned mask, distance constraint
or curvature wrapper. An earlier always-fast lateral-acceleration policy is a
different intervention and cannot supply this candidate's endpoint.

`build_global_cap.py` changes two exact literals in a supplied immutable archive:
the fixed Agent constructor argument and the legacy GeometryController ceiling.
The first reaches the active SpeedController. The legacy method is overridden
in this Agent; its change has no active effect. The unused parameter-constructor
default stays unchanged. Building with 28 is the no-op control. The private
manifest binds every archive member, worker, runtime and source hash.

`qualify_global_cap.py` replays a bounded saved pixel sequence into the original
clean isolated worker. It checks the control against saved actions and checks
that candidate steering is identical on the same inputs and history. It records
the first action difference without treating replay as performance evidence.
No simulator or model is used by this qualification.

`global_cap_dev.py` consumes a one-use, hash-bound readiness receipt. On the first
registered DEV road it runs the candidate once against a verified saved original
endpoint. On the second it runs original then candidate. Each episode has a
2,000-action ceiling; the total is at most three episodes and 6,000 actions.
The original archive and the same candidate are fixed before all results.
Normal driving failure or a censored action ceiling does not suppress the other
road. Technical invalidity, resource exhaustion or absolute expiry stops safely.

The shared passive collector accepts the arm and a shared initial-state map.
It compares saved initial state and all four observation frames before action,
then checks exact paired resets for the second road. Only the evaluator sees
truth records; actors receive the ordinary pixel reset/act interface. Saved
actions and reconstructed observation streams must match their rolling hashes.
Private recordings support the actual first-divergence check without another
policy call or simulator run.

Report completion preservation, loss and gain first. Compare numeric laps only
for common normal completions. Report damage separately; neither zero damage
nor a minimum improvement percentage is a new kill criterion. Two reused DEV
roads do not authorize promotion. Protected evaluation details stay closed.

Retrospective factorials additionally require the requested protocol match.
Different action ceilings or execution protocols must be disclosed even if all
stored endpoints occur before either ceiling. Their observed outcome pattern
does not pass a strict protocol-matched interaction gate. Never substitute a
failed episode's elapsed time or action count for a missing lap.

Seeds, models, archives, plans, trajectories, costs and results stay outside the
public repository. These same-host adapters do not establish official runner or
fresh-machine submission equivalence.
