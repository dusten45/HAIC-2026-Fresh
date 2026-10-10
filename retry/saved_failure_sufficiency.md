# Saved failure sufficiency gate

The saved three-policy failure comparison stopped at the first data gate. Vehicle position, heading and timing were recorded, and road/obstacle/initial-observation identities matched. The selected route was recorded only as a point count, together with one controller target. Those fields do not specify the full chosen path. The original policy record also retained obstacle counts and a digest without the obstacle coordinates used by the decision.

The missing evidence is the selected route polyline, its coordinate frame and decision-time association with the vehicle pose, and the obstacle coordinates actually available to the original route decision. A tracked obstacle estimate and a physical obstacle geometry remain distinct. Frozen vehicle geometry can supply width; that does not recover an absent route.

No progress/direction alignment, contact-versus-error ordering, stagnation or repeated-motion inference followed. No policy replay, geometry reconstruction, simulator action, learning or automatic fix was performed. Neither route failure nor controller failure is identified, and this case is not generalized to other failures. Geometric clearance with vehicle width and dynamic tracking feasibility remain separate unanswered questions.

`saved_failure_sufficiency.py` records field coverage and stops on missing route coordinates. Coordinates alone would still require a reference-frame and route-input review. Private input records and coverage vectors stay outside the repository. Existing provisional baselines, the formal champion and protected splits remain preserved.
