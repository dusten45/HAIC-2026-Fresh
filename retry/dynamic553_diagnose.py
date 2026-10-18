"""Reconstruct only failed planner's chosen prefix to preserve missing force state.

Not a pilot retry: exact stored chosen controls, no new policy/action search,
failed553 gate stays false. All new reconstruction ticks charged separately.
"""
import datetime,hashlib,json,math,time,traceback
from dataclasses import asdict,replace
from pathlib import Path
import numpy as np
from retry.plan513_model import load_root
from retry.drive519_control import steering,force_rows,project
from retry.closure524_control import tick
from retry.brake508_corridor import bounds
from retry.corner515_model import margin
from retry.brake510_common import boundary_index
from retry.lap518_finish import hull_pose
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response553-private')
def run():
 cpu=time.process_time();wall=time.perf_counter();rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();inputs=[D/'entry-private.json',D/'fixed-segment-candidate-private.json',D/'frozen-paths-private.json',Path('/workspace/haic-response515-private/collected-map-state-private.json')];c=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),reason='553 failed backup summary retained controls/end speeds but omitted intermediate fullstates. Reconstruct exactlythe7chosenholds once to freeze force-deadend state and explain failure. No policy change, no pilotretry, no additionalcandidate/window/goal.',caps={'model_ticks':100,'force_evaluations':1000,'geometry_checks':100,'CPU_s':10,'wall_s':15},source_sha256=sha(Path(__file__)),input_sha256={str(p):sha(p) for p in inputs},original553_failure_preserved=True,new_actual_cap=0)
 with (G/'retry/dynamic553_diagnostic_contract.json').open('x') as f:json.dump(c,f,indent=2)
 with (D/'diagnostic-STARTED.json').open('x') as f:json.dump(dict(contract_sha256=sha(G/'retry/dynamic553_diagnostic_contract.json')),f)
 counter=[0];cost=dict(force_evaluations=0,geometry_checks=0);trace=[];out={}
 def guard():
  if counter[0]>=100 or cost['force_evaluations']>=1000 or cost['geometry_checks']>=100 or time.process_time()-cpu>=10 or time.perf_counter()-wall>=15:raise RuntimeError('DIAGNOSTIC_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00'):raise RuntimeError('DEADLINE')
 try:
  e=rd(inputs[0]);data=rd(inputs[1]);p=rd(inputs[2])['candidate'];static=rd(inputs[3]);inner=data['commands'][0]['detail']['backup']['inner'];assert inner[-1]['reason']=='NO_GOAL_HOLD';root=load_root(dict(e['root'],roads=static['root']['roads']));s=e['progress'];history=e['history'].copy();index=bounds(root.roads);edge=boundary_index(static['boundary']);differences=[];controls=[]
  for step in inner[:-1]:
   good=[z for z in step['trials'] if z['ok']];best=min(good,key=lambda z:(abs(z['end_speed']-e['target_speed']),-z['end_speed'],-z['u']));u=best['u'];a=np.array([steering(root,p,s),max(0.,u),max(0.,-u)],np.float32);controls.append(a.tolist());root=replace(root,planar=replace(root.planar,steer=-float(a[0])))
   for k in range(4):
    guard();fs=force_rows(root,a);cost['force_evaluations']+=4;history[0]+=sum(z['clipped'] for z in fs);history[1]+=4;root=tick(root,float(a[1]),float(a[2]),index,counter);q=project(root.center,p,s);s=q['s'];cost['geometry_checks']+=1;gap=margin(root,static['roads'],index,static['boundary'],edge,static['obstacles']);body=max(math.hypot(*hull_pose(root)[1]),*(math.hypot(*(root.planar.linear.velocity[t]+w.offset[t] for t in range(2))) for w in root.planar.linear.wheels));assert gap>=.5 and body<100 and max(z['ratio'] for z in fs)<=1.059000000000001 and history[0]/history[1]<=.1;state=asdict(root);state.pop('roads');trace.append(dict(root_without_roads=state,progress=s,action=a.tolist(),margin=gap,forces=fs))
   error=abs(math.hypot(*root.planar.linear.velocity)-best['end_speed']);differences.append(error);assert error<1e-12
  steer=steering(root,p,s);lateral=[];target_lat=[];speed=math.hypot(*root.planar.linear.velocity)
  for w in root.planar.linear.wheels:
   side=(math.cos(w.heading),math.sin(w.heading));v=[root.planar.linear.velocity[t]+w.offset[t] for t in range(2)];lateral.append(abs(82*sum(v[t]*side[t] for t in range(2)))/w.friction);vv=[root.planar.linear.velocity[t]*e['target_speed']/speed+w.offset[t] for t in range(2)];target_lat.append(abs(82*sum(vv[t]*side[t] for t in range(2)))/w.friction)
  trials=[]
  for z in inner[-1]['trials']:
   guard();u=z['u'];a=np.array([steer,max(0.,u),max(0.,-u)],np.float32);fs=force_rows(root,a);cost['force_evaluations']+=4;trials.append(dict(u=u,peak=max(f['ratio'] for f in fs),wheel_peaks=[f['ratio'] for f in fs]));assert max(f['ratio'] for f in fs)>1.059
  state=asdict(root);state.pop('roads');private=dict(trace=trace,controls=controls,failure_root_without_roads=state,failure_progress=s,failure_history=history,algebra_trials=trials,lateral_ratio_lower_bounds=lateral,exact_target_speed_same_yaw_offset_lateral=target_lat)
  with (D/'reconstructed-planning-prefix-private.json').open('x') as f:json.dump(private,f,indent=2)
  (D/'reconstructed-planning-prefix-private.json').chmod(0o600);out=dict(passed=True,matched_saved_end_speed_max_error=max(differences),reconstructed_holds=len(controls),reconstructed_raw=counter[0],failed_future_speed_m_s=speed,goal_speed_m_s=e['target_speed'],goal_error_m_s=speed-e['target_speed'],failed_future_yaw_rad_s=root.planar.yaw,failed_future_path_fraction=s/p['length'],failure_history=history,pure_lateral_force_ratio_lower_bounds=lateral,all19_sampled_pedals_force_failed=True,continuous_signed_pedal_impossibility_at_this_fixed_state=max(lateral)>1.059,even_exact_goal_speed_same_yaw_offset_lower_bound=max(target_lat),target_speed_perturbation_is_algebra_only_not_reachable_control=True,source_lateral_before_steeringservo_independent_of_pedal=True,original_pilot_stays_failed=not rd(G/'retry/dynamic553_pilot_result.json')['passed'],no_new_closed_loop_case=True)
 except BaseException as exc:
  out=dict(passed=False,error=type(exc).__name__+':'+str(exc))
  with (D/'diagnostic-error-private.json').open('x') as f:json.dump(dict(error=out['error'],traceback=traceback.format_exc(),trace=trace,counter=counter,cost=cost),f,indent=2)
 finally:
  out.update(model_ticks=counter[0],cost=cost,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_native_actions=0,new_resets=0)
  with (G/'retry/dynamic553_diagnostic_result.json').open('x') as f:json.dump(out,f,indent=2)
  print(json.dumps(out,indent=2))
if __name__=='__main__':run()
