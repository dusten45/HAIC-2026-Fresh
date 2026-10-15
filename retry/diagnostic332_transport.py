"""Posthoc rigid transport of saved hazard using measured poses, diagnostic only.

No fit, actor call, simulator world, or hypothetical physics step. GT-based
transport never enters a participant policy or the proposed direct-only probe.
"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
from retry.path271_run import read,save
from retry.diagnostic332_run import world,local


def run(R):
    D=R/'stage332';start,cpu=time.perf_counter(),time.process_time();details=[]
    for label in ['A','B']:
        replay=read(D/label/'saved-pixel-replay-private.json');g=read(D/'geometry-private.json')['actual_precontact_geometries'][label];rows=[json.loads(s) for s in (R/'stage331'/label/'trace-private.jsonl').read_text().splitlines()]
        before=replay[64]['response'];after=replay[65]['response'];old=next(h for h in before['state']['hazards'] if h[3]==0);retained=next(h for h in after['state']['hazards'] if h[3]==1);current=after['direct_obstacles'][0]
        actual_old_pose=rows[64]['pre_physical']['hull'];actual_new_pose=rows[65]['pre_physical']['hull'];transported=local(world(old[:2],actual_old_pose),actual_new_pose)
        gt=np.array(g[1]['obstacles'][0]['GT_body_center']);old_gt=np.array(g[0]['obstacles'][0]['GT_body_center'])
        gap=np.linalg.norm(np.array(retained[:2])-current[:2]);assert gap>2. # unchanged source dedup rule, not a new threshold
        details.append(dict(arm=label,boundary_from=64,boundary_to=65,old_age0_hazard=old,retained_age1_hazard=retained,direct=current,measured_pose_transported_center=transported.tolist(),
            old_detection_GT_error_m=float(np.linalg.norm(np.array(old[:2])-old_gt)),retained_GT_error_m=float(np.linalg.norm(np.array(retained[:2])-gt)),measured_pose_transport_GT_error_m=float(np.linalg.norm(transported-gt)),
            retained_minus_measured_transport_m=float(np.linalg.norm(np.array(retained[:2])-transported)),retained_to_current_detection_distance_m=float(gap),
            exact_HUD_forward_only_fallback_signature=bool(retained[0]==old[0] and retained[1]==old[1]-after['pixel_state'][0]*.08)))
    out=dict(details=details,static_rigid_transforms=2,new_fits=0,native_actions=0,new_actor_calls=0,source_physics_rollout_ticks=0,wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu,
        scope='Counterfactual measured ego-pose transport of an already observed hazard. It shows a local transport discrepancy; it does not recover unrecorded optical-flow acceptance flags, prove global tracker failure, or predict physical contact.')
    save(D/'rigid-transport-private.json',out);print(json.dumps({k:out[k] for k in ['static_rigid_transforms','wall_s','CPU_s']},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);run(p.parse_args().private_root)
