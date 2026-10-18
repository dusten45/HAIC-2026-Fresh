"""Bounded verification repair only: no FD, LP, proposal or optimization retry."""
import datetime,json,math,time,traceback
from dataclasses import replace
from pathlib import Path
import numpy as np
import retry.period556_model as engine
from retry.transcribe559_model import canonical,vector

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response560-private');engine.D=D
rd,sha,save,short=engine.rd,engine.sha,engine.save,engine.short
def run():
 prior=rd(G/'retry/sequential560_result.json');assert prior['recovery_error']=='RuntimeError:RECOVERY_WORK_CAP' and prior['accepted_count']==0 and prior['cost']['recovery']['model_ticks']==132
 baseline=rd(D/'baseline-private.json');segment=rd(D/'segment-private.json');original=rd(G/'retry/sequential560_contract.json');static=rd(Path('/workspace/haic-response515-private/collected-map-state-private.json'));path=rd(Path('/workspace/haic-response551-private/frozen-paths-private.json'))['candidate']
 c=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Repair final verification bookkeeping cap: last132raw replay was computed but lost before postprocessing. Repeat ONLY same unchanged baseline incumbent132raw, compare every state/force on the fly, save trace on every exit. NO new direction/LP/proposal or accepted-step change. Original and first recovery failures retained.',caps=dict(additional_model_ticks=132,additional_explicit_wheel_forces=528,additional_geometry_checks=133,CPU_s=10,wall_s=20),parent_contract_sha256=sha(G/'retry/sequential560_contract.json'),first_recovery_contract_sha256=sha(G/'retry/sequential560_recovery_contract.json'),first_recovery_result_sha256=sha(G/'retry/sequential560_result.json'),source_sha256={p:sha(G/p) for p in ['retry/sequential560_finalize.py','retry/period556_model.py','retry/closure524_control.py','retry/plan512_control.py','retry/brake504_planar.py','retry/brake502_response.py','retry/speed516_control.py']})
 save(G/'retry/sequential560_finalization_contract.json',c);save(D/'finalization-STARTED.json',dict(contract_sha256=sha(G/'retry/sequential560_finalization_contract.json')))
 cpu,wall=time.process_time(),time.perf_counter();root=engine.load_root(dict(segment['initial'],roads=static['root']['roads']));index=engine.bounds(root.roads);edge=engine.boundary_index(static['boundary']);counter=[0];force_calls=geo=0;rows=[];history=segment['history'].copy();maxforce=maxbody=maxclip=maxpath=0.;maxover=-1e10;minimum=1e10;exact=True;safe=True;error=None
 def timeguard():
  if time.process_time()-cpu>=10 or time.perf_counter()-wall>=20:raise RuntimeError('FINALIZATION_TIME_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(original['deadline_utc']):raise RuntimeError('DEADLINE')
 def measure(state):
  nonlocal geo,minimum,maxpath,maxover,safe
  timeguard()
  if geo>=133:raise RuntimeError('FINALIZATION_GEOMETRY_CAP')
  gap=engine.margin(state,static['roads'],index,static['boundary'],edge,static['obstacles']);geo+=1
  from retry.drive519_control import project,reference
  q=project(state.center,path);s=q['s']%path['length'];over=math.hypot(*state.planar.linear.velocity)-reference(s,path)[0];minimum=min(minimum,gap);maxpath=max(maxpath,q['distance']);maxover=max(maxover,over);safe &=gap>=.5 and q['distance']<=3 and over<=4.85
  return dict(margin=gap,patherror=q['distance'],original551_overspeed=over)
 initial=short(root)
 try:
  initial_geometry=measure(root)
  for action in [np.array(a,np.float32) for a in segment['commands']]:
   root=replace(root,planar=replace(root.planar,steer=-float(action[0])))
   for _ in range(4):
    timeguard()
    if counter[0]>=132 or force_calls+4>528:raise RuntimeError('FINALIZATION_INTEGRATION_CAP')
    fs=engine.force_rows(root,action);force_calls+=4;root=engine.tick(root,float(action[1]),float(action[2]),index,counter);geometry=measure(root)
    body=max(math.hypot(*engine.hull_pose(root)[1]),*(math.hypot(*(root.planar.linear.velocity[j]+w.offset[j] for j in range(2))) for w in root.planar.linear.wheels));maxbody=max(maxbody,body);maxforce=max(maxforce,max(f['ratio'] for f in fs));history[0]+=sum(f['clipped'] for f in fs);history[1]+=4;maxclip=max(maxclip,history[0]/history[1]);safe &=maxforce<=1.059 and body<100 and maxclip<=.1
    expected=baseline['rows'][counter[0]-1];same=canonical(short(root))==expected['root_without_roads'] and canonical(fs)==expected['forces'];exact &=same;rows.append(dict(raw=counter[0],root_without_roads=short(root),forces=fs,geometry=geometry,body=body,exact_baseline_match=same))
  assert counter[0]==132 and exact and safe
 except BaseException as e:error=type(e).__name__+':'+str(e)
 finally:
  rec=dict(model_ticks=counter[0],explicit_wheel_force_evaluations=force_calls,geometry_checks=geo,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
  save(D/'final-repaired-private.json',dict(error=error,initial_root_without_roads=initial,rows=rows,terminal_root_without_roads=short(root),exact=bool(exact),safe=bool(safe),cost=rec))
 summary=dict(completed=error is None,scientific_stop_reason='THREE_REJECTED_TRIALS',exact_feasible_initialization=True,accepted_count=0,direction_count=1,trials=prior['trials'],final_incumbent='baseline',final_fresh_replay_exact=bool(error is None and exact),final_feasible=bool(error is None and safe),baseline_times_s=prior['baseline_times_s'],final_times_s=prior['baseline_times_s'] if error is None else None,cumulative_gain_ms=[0.,0.] if error is None else None,final_raw_brackets=[g['raw_bracket'] for g in baseline['crossings']],final_fullstate_gate_differences='exactly zero versus baseline because every raw state/force matched',final_stats=dict(min_margin=minimum,max_path=maxpath,max_reference_overspeed=maxover,max_force=maxforce,max_clip_fraction=maxclip,max_body=maxbody,final_clip_history=history),errors_preserved=['main NumPy int64 JSON serialization failure','first recovery integration cap incorrectly applied to postprocessing'],finalization_error=error,cost=dict(model_ticks=prior['cost']['model_ticks']+counter[0],explicit_wheel_force_evaluations=prior['cost']['explicit_wheel_force_evaluations']+force_calls,internal_wheel_force_evaluations=4*(prior['cost']['model_ticks']+counter[0]),geometry_checks=prior['cost']['geometry_checks']+geo,body_checks=prior['cost']['body_checks']+counter[0],main_model_ticks=5940,first_recovery=prior['cost']['recovery'],finalization=rec,main_measured_CPU_s=None,aggregate_measured_CPU_s=None,main_registration_to_failure_file_wall_estimate_s=prior['cost']['main_registration_to_failure_file_wall_estimate_s'],aggregate_CPU600_independently_verified=False),new_native_actions=0,new_resets=0,new_worlds=0,new_seeds=0,HOLDOUT_queries=0,SEALED_queries=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_baseline_s=13.66,no_lap_gain_observation=True)
 save(G/'retry/sequential560_summary.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':run()
