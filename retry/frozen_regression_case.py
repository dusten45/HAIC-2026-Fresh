"""Frozen champion, official endpoints, diagnostic truth outside isolated actor."""
import argparse, datetime, fcntl, hashlib, json, math, resource, sys, time, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
import numpy as np
from retry.diagnose import Budget, BudgetStop, make_env
from retry.evaluate import check_window, observation_contract, percentiles
from retry.process_probe import Participant, valid_action
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
array_digest=lambda x:hashlib.sha256(np.asarray(x,dtype='<f8').tobytes()).hexdigest()
p=argparse.ArgumentParser(); p.add_argument('--plan',type=Path,required=True); p.add_argument('--case',required=True); args=p.parse_args(); D=args.plan.resolve().parent
assert args.plan.name == 'plan.json'
plan=json.loads((D/'plan.json').read_text()); case=next(c for c in plan['cases'] if c['id']==args.case)
role=args.case; out=D/'runs'/role; out.mkdir(parents=True,exist_ok=False)
env=child=None; rows=[]; frames=[]; actions=[]; latencies=[]; used=raw_ticks=reset_ticks=0
started=time.perf_counter(); result={}; reason=error=None; ended=truncated=False

def charged():
 with (D/'budget.json').open() as h:
  fcntl.flock(h,fcntl.LOCK_SH); return json.load(h)['stages'].get(role,0)
def truth():
 raw=env.unwrapped; hull=raw.car.hull
 return {'position':list(hull.position),'speed_m_s':math.hypot(*hull.linearVelocity),
         'angle':float(hull.angle),'time':raw.t,'unique_tiles':raw.tile_visited_count,
         'damage':env.damage.damage,'off_track_counter':env.off_track_counter}
def stop(kind,detail):
 try:
  with (D/'stop.json').open('x') as h:json.dump({'kind':kind,'detail':detail,'case':role},h)
 except FileExistsError:pass
try:
 check_window(plan); assert not (D/'stop.json').exists()
 assert digest(D/'plan.json')==(D/'plan.sha256').read_text().split()[0]
 assert digest(Path(case['baseline_result_path']))==case['baseline_result_sha256']
 for name,want in plan['execution_source_sha256'].items():assert digest(Path(name))==want,name
 config=plan['candidate']; assert digest(Path(config['archive_path']))==config['archive_sha256']
 for name,want in config['members_sha256'].items():assert digest(Path(config['package_path'])/name)==want,name
 budget=Budget(D/'plan.json',role)
 child=Participant(ROOT/'.venv/bin/python',command_override=[str(ROOT/'.venv/bin/python'),plan['worker_path'],config['package_path']])
 check_window(plan); env=make_env(); t=time.perf_counter(); obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']}); reset_wall=time.perf_counter()-t
 initial=truth(); assert initial==case['baseline_initial_truth']; assert hashlib.sha256(obs.tobytes()).hexdigest()==case['baseline_initial_observation_sha256']; reset_ticks=round(env.unwrapped.t*50); assert reset_ticks==51
 geometry_sha=array_digest(env.unwrapped.track); assert geometry_sha==case['road_geometry_sha256']
 obstacle_sha=array_digest([[*map(float,o.position),float(o.fixtures[0].shape.radius)] for o in env.unwrapped.obstacles]); assert obstacle_sha==case['expected_physical_obstacles_sha256']
 observation_contract(obs); assert all(np.array_equal(obs[0],x) for x in obs[1:])
 _,actor_reset_wall=child.call('reset',obs); frames.append(np.rint(obs[-1]*255).astype(np.uint8))
 (out/'started.json').write_text(json.dumps({'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'plan_sha256':digest(D/'plan.json'),'initial':initial,'geometry_sha256':geometry_sha,'obstacles_sha256':obstacle_sha,'initial_observation_sha256':hashlib.sha256(obs.tobytes()).hexdigest()},indent=2)+'\n')
 with (out/'trace.jsonl').open('w') as h:
  for step in range(1,plan['max_steps']+1):
   check_window(plan)
   if (D/'stop.json').exists():reason='shared_stop_censored';break
   before=truth(); response,act_wall=child.call('act',obs)
   assert valid_action(response); action=np.asarray(response['action'],dtype=np.float32)
   assert np.all(action>=[-1,0,0]) and np.all(action<=[1,1,1])
   assert set(['speed_estimate','hazard_near','centerline_points','path_points','route_target_missing'])<=set(response['policy'])
   previous=obs; t=time.perf_counter()
   obs,reward,ended,truncated,info=budget.step(env,action); sim_wall=time.perf_counter()-t; used=step
   after=truth(); ticks=round((after['time']-before['time'])*50); raw_ticks+=ticks
   assert 1<=ticks<=4 and (ticks==4 or ended or truncated)
   observation_contract(obs); assert np.array_equal(obs[:3],previous[1:])
   row={'step':step,'before_time':before['time'],'after_time':after['time'],'action':action.tolist(),'policy':response['policy'],'cap':response['cap_diagnostic'],'tracked_obstacles':response['tracked_obstacles'],'memory':response['memory'],
        'truth_before':before,'truth_after':after,'unique_tiles':after['unique_tiles'],'total_tiles':len(env.unwrapped.track),'progress':info['progress'],'collision':bool(info['collision']),
        'terminated':bool(ended),'truncated':bool(truncated),'retire_reason':info['retire_reason'],'raw_ticks':ticks,
        'act_wall_s':act_wall,'sim_step_wall_s':sim_wall,'rss_mib':response['rss_mib'],'actor_cumulative_CPU_s':response['actor_cumulative_CPU_s'],
        'observation_sha256_after':hashlib.sha256(obs.tobytes()).hexdigest()}
   h.write(json.dumps(row)+'\n');h.flush();rows.append(row);actions.append(action);frames.append(np.rint(obs[-1]*255).astype(np.uint8));latencies.append(act_wall)
   if ended or truncated:reason=info['retire_reason'];break
  else:reason='unexpected_no_official_endpoint_at_native_bound_censored'
 finish=env.unwrapped.finish_time_s; completed=finish is not None; terminal=bool(ended or truncated); assert not completed or terminal
 assert charged()==used
 result={'case':role,'scope':'FROZEN_POLICY_REUSED_BASELINE_REGRESSION','completed':completed,'terminal_observed':terminal,'censored':not terminal,'evaluation_endpoint_observed':terminal,
         'lap_ms':round((finish-1.02)*1000) if completed else None,'finish_time_s':finish,'progress':env._calculate_progress(),
         'unique_tiles':env.unwrapped.tile_visited_count,'total_tiles':len(env.unwrapped.track),'damage':env.damage.damage,
         'steps':used,'charged_wrapper_actions':charged(),'raw_step_ticks':raw_ticks,'raw_reset_ticks':reset_ticks,'retire_reason':reason,
         'frozen_archive_sha256':config['archive_sha256'],'geometry_sha256':geometry_sha,'obstacles_sha256':obstacle_sha,
         'policy_module_boundary':child.ready,'oracle_inputs_to_policy':False,'policy_differs_from_baseline':True,'policy_changed_this_stage':False,
         'reset_wall_s':reset_wall,'actor_reset_wall_s':actor_reset_wall,'wall_s':time.perf_counter()-started,
         'sum_sim_step_wall_s':sum(r['sim_step_wall_s'] for r in rows),'act_including_ipc':percentiles(latencies),
         'actor_cumulative_CPU_s':max((r['actor_cumulative_CPU_s'] for r in rows),default=0),
         'harness_CPU_s':resource.getrusage(resource.RUSAGE_SELF).ru_utime+resource.getrusage(resource.RUSAGE_SELF).ru_stime,
         'child_peak_RSS_mib':max((r['rss_mib'] for r in rows),default=0),'harness_peak_RSS_mib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,
         'collision_wrapper_calls':sum(r['collision'] for r in rows),'max_off_track_counter':max((r['truth_after']['off_track_counter'] for r in rows),default=0)}
except Exception as exc:
 error=repr(exc);stop('INCONCLUSIVE_TECHNICAL_OR_BUDGET',error)
 result={'case':role,'error':error,'traceback':traceback.format_exc(),'completed':False,'terminal_observed':False,'censored':True,
         'steps':used,'charged_wrapper_actions':charged(),'raw_step_ticks':raw_ticks,'raw_reset_ticks':reset_ticks,'wall_s':time.perf_counter()-started,'no_automatic_retry':True}
finally:
 if frames:np.savez_compressed(out/'pixels-actions.npz',frames=np.asarray(frames),actions=np.asarray(actions,dtype=np.float32))
 (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 if child:child.close()
 if env:env.close()
print(json.dumps(result,ensure_ascii=False),flush=True)
if error:sys.exit(1)
