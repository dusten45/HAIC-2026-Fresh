"""Capability gate for pixel closed-loop source suffixes; no continuation if unsupported."""
import argparse,time,datetime
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha

def run(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage280';assert not D.exists();D.mkdir(mode=0o700)
 anchors=dict(N0=148,N2=136)
 save(D/'plan.json',dict(stage=280,anchors=anchors,anchor_rule='Nearest stored pre-action query boundary to half of existing episode length, before runtime probe; no performance selection',scope='Capability gate only; two no-change suffixes require images, own controller state and official terminal. No macros or learning.',native_cap_if_missing_reference=1300,champion_changed=False))
 start=time.perf_counter();cpu=time.process_time()
 from retry.source_vehicle_transition import SourceVehicleTransition
 source=read(R/'stage251/plan.json');rows=[]
 for road,q in anchors.items():
  folder=R/'stage251/training'/road;m=read(folder/'materialized.json');z=np.load(folder/'cache-private.npz');snapshot=m['snapshots'][str(q)];n=m['native_actions'];ref=source['references'][road]
  assert z['observations'].shape==(n+1,4,84,84) and z['commands'].shape==(n,3) and len(m['actual'])==n
  assert np.array_equal(z['commands'],np.array(ref['actions'],np.float32)) and m['actual'][-1]['terminal']
  init=time.perf_counter();model=SourceVehicleTransition(snapshot)
  try:
   capabilities=dict(road_visit_restored=model.initial_progress_exact and model.initial_tiles_exact,body_restored=model.initial_bodies_exact,render_callable=callable(getattr(model,'render',None)) or callable(getattr(model,'_render',None)),observation_stack=hasattr(model,'stack_state'),finish_tracker=hasattr(model,'finish_tracker') or hasattr(model,'_finish_tracker'),finish_time=hasattr(model,'finish_time_s'),policy_controller_snapshot='controller' in snapshot,real_track_coordinates=any(x is not None for x in model.track))
   assert model.native_ticks==0
  finally:model.close()
  row=dict(road=road,preaction_boundary=q,prefix_actions=q-1,suffix_actions=n-q+1,existing_baseline_actions=n,existing_baseline_complete=True,existing_baseline_lap_ms=ref['lap_ms'],full_observation_action_trace=True,durable_full_controller_state=False,capabilities=capabilities,source_world_build_wall_s=time.perf_counter()-init,source_physics_ticks=0,source_zero_time_contact_initializations=1,source_suffix_executed=False,first_mismatch=None,first_mismatch_scope='Not measured: capability gate failed before continuation',official_source_terminal_reproduced=False,reference_collection_wall_s=m['wall_s'],reference_actor_CPU_s=m['base_actor_CPU_s'])
  rows.append(row)
 p=read(R/'project-effective-budget-v283.json');cost=dict(stage=280,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_wrapper_actions=0,new_source_physics_ticks=0,source_zero_time_contact_initializations=2,new_render_calls=0,new_actor_calls=0,new_suffix_rollouts=0,audit_wall_s=time.perf_counter()-start,audit_CPU_s=time.process_time()-cpu,source_world_build_wall_s=sum(r['source_world_build_wall_s'] for r in rows),B_operating_cap=p['B_operating_cap'],actual_cumulative_wrapper_actions=p['actual_cumulative_wrapper_actions'],research_remaining=p['research_remaining'],final_reserved_actions=84000,final_reserve_used=0,new_paid_resources=0)
 save(D/'cost.json',cost);private=dict(rows=rows,source_hashes={str(q):sha(q) for q in [G/'retry/source_vehicle_transition.py',G/'core/finish_line.py',G/'core/vendor/car_racing.py',G/'env_wrapper.py',G/'retry/suffix280_audit.py']},reference_hashes={str(q):sha(q) for r in anchors for q in [R/'stage251/training'/r/'cache-private.npz',R/'stage251/training'/r/'materialized.json']},cost=cost);save(D/'audit-private.json',private)
 result=dict(stage=280,status='Blocked at capability gate; no policy learning',rows=rows,cost=cost,missing=['Renderer scene assets/road polygons/colors/camera and state_pixels output','Four-frame wrapper pixel stack and matching preprocessing','Official finish tracker line geometry, previous side/position, qualification/crossing/time state','240 controller/planner/hazards/previous-image history in snapshot','Box2D warm-start impulses/contact manifold/broadphase/island history not cloned'],alternatives=['Existing real pixel240 observation/action traces support offline actor replay, not changed-trajectory counterfactual labels','Fresh official reset and charged prefix replay in the same runner can support true short intervention then actual pixel240 full continuation, as250; this audit executes none','Existing source clone remains usable for bounded supplied-control physics diagnostics, not official pixel closed-loop completion labels'],champion_changed=False,HOLDOUT_SEALED_used=False)
 (G/'retry/suffix280_result.json').write_text(__import__('json').dumps(result,indent=2,ensure_ascii=False)+'\n');print(__import__('json').dumps(result,indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--private-root',type=Path,required=True);run(a.parse_args().private_root.resolve())
