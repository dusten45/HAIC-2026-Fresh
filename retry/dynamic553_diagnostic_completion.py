"""Complete failed553 analysis from recovered state, exact19 old trials only."""
import datetime,hashlib,json,math,time
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
 cpu=time.process_time();wall=time.perf_counter();rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prior=rd(G/'retry/dynamic553_diagnostic_result.json');err=rd(D/'diagnostic-error-private.json');entry=rd(D/'entry-private.json');data=rd(D/'fixed-segment-candidate-private.json');inner=data['commands'][0]['detail']['backup']['inner'];assert prior['model_ticks']==28 and len(err['trace'])==28;plan=rd(G/'retry/dynamic553_diagnostic_contract.json');c=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='First diagnostic had incorrect algebra assertion all19 failfirstraw; prefix reconstruction succeeded28ticks with allstored endvel matches. Reuse exactsaved recoveredstate, replay ONLY original19failed4tickqueries to identify failuretick/components. No prefix replay, no newcontrols or planner/candidate retry.',same_total_caps=plan['caps'],precharge=prior,source_sha256=sha(Path(__file__)),input_sha256={str(p):sha(p) for p in [G/'retry/dynamic553_diagnostic_contract.json',G/'retry/dynamic553_diagnostic_result.json',D/'diagnostic-error-private.json',D/'fixed-segment-candidate-private.json']})
 with (G/'retry/dynamic553_diagnostic_completion_contract.json').open('x') as f:json.dump(c,f,indent=2)
 with (D/'diagnostic-completion-STARTED.json').open('x') as f:json.dump(dict(contract_sha256=sha(G/'retry/dynamic553_diagnostic_completion_contract.json')),f)
 counter=[prior['model_ticks']];cost=prior['cost'].copy();caps=plan['caps'];static=rd(Path('/workspace/haic-response515-private/collected-map-state-private.json'));path=rd(D/'frozen-paths-private.json')['candidate'];root=load_root(dict(err['trace'][-1]['root_without_roads'],roads=static['root']['roads']));s=err['trace'][-1]['progress'];history=entry['history'].copy()
 for row in err['trace']:history[0]+=sum(z['clipped'] for z in row['forces']);history[1]+=4
 index=bounds(root.roads);edge=boundary_index(static['boundary']);speed=math.hypot(*root.planar.linear.velocity);purelat=[]
 for w in root.planar.linear.wheels:
  side=(math.cos(w.heading),math.sin(w.heading));v=[root.planar.linear.velocity[t]+w.offset[t] for t in range(2)];purelat.append(abs(82*sum(side[t]*v[t] for t in range(2)))/w.friction)
 def guard():
  if counter[0]>=caps['model_ticks'] or cost['force_evaluations']>=caps['force_evaluations'] or cost['geometry_checks']>=caps['geometry_checks'] or prior['CPU_s']+time.process_time()-cpu>=caps['CPU_s'] or prior['wall_s']+time.perf_counter()-wall>=caps['wall_s']:raise RuntimeError('COMBINED_DIAGNOSTIC_CAP')
  if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat('2026-10-20T10:01:55+00:00'):raise RuntimeError('DEADLINE')
 results=[];priv=[]
 for oldtrial in inner[-1]['trials']:
  u=oldtrial['u'];a=np.array([steering(root,path,s),max(0.,u),max(0.,-u)],np.float32);state=replace(root,planar=replace(root.planar,steer=-float(a[0])));progress=s;h=history.copy();before_saved=[];failure=None
  for raw in range(4):
   guard();fs=force_rows(state,a);cost['force_evaluations']+=4;peak=max(z['ratio'] for z in fs);h[0]+=sum(z['clipped'] for z in fs);h[1]+=4;lat=[]
   for w in state.planar.linear.wheels:
    side=(math.cos(w.heading),math.sin(w.heading));v=[state.planar.linear.velocity[t]+w.offset[t] for t in range(2)];lat.append(abs(82*sum(side[t]*v[t] for t in range(2)))/w.friction)
   if peak>1.059 or h[0]/h[1]>.1:
    failure=dict(u=u,reason='FORCE' if peak>1.059 else 'CLIP',raw=raw+1,peak_force_ratio=peak,pure_lateral_ratio_max=max(lat),limiting_wheel=max(range(4),key=lambda i:fs[i]['ratio']),speed=math.hypot(*state.planar.linear.velocity));saved=asdict(state);saved.pop('roads');priv.append(dict(failure=failure,before_failure_root_without_roads=saved,force_rows=fs,lateral_lower_bounds=lat));break
   state=tick(state,float(a[1]),float(a[2]),index,counter);q=project(state.center,path,progress);progress=q['s'];cost['geometry_checks']+=1;gap=margin(state,static['roads'],index,static['boundary'],edge,static['obstacles']);body=max(math.hypot(*hull_pose(state)[1]),*(math.hypot(*(state.planar.linear.velocity[t]+w.offset[t] for t in range(2))) for w in state.planar.linear.wheels));assert gap>=.5 and body<100
  assert failure is not None and failure['reason']==oldtrial['reason'];results.append(failure)
 matched=[]
 for step in inner[:-1]:
  good=[z for z in step['trials'] if z['ok']];best=min(good,key=lambda z:(abs(z['end_speed']-entry['target_speed']),-z['end_speed'],-z['u']));matched.append(best['end_speed'])
 checks=dict(prefix28not_replayed=True,all19_original_queries_reproduce=True,no_policy_retry=not rd(G/'retry/dynamic553_pilot_result.json')['passed'],same_root_speed=abs(speed-matched[-1])<1e-12,global_caps=counter[0]<=100 and cost['force_evaluations']<=1000 and cost['geometry_checks']<=100)
 with (D/'completed-force-diagnosis-private.json').open('x') as f:json.dump(dict(recovered_root_without_roads=err['trace'][-1]['root_without_roads'],recovered_progress=s,recovered_history=history,trial_failures=priv),f,indent=2)
 (D/'completed-force-diagnosis-private.json').chmod(0o600);out=dict(passed=all(checks.values()),checks=checks,recovered_future_speed_m_s=speed,goal_speed_m_s=entry['target_speed'],goal_error_m_s=speed-entry['target_speed'],recovered_future_yaw_rad_s=root.planar.yaw,recovered_goal_hold_number=8,pure_lateral_ratio_lower_bounds_before_hold=purelat,first_raw_all_pedals_impossible_proved=max(purelat)>1.059,failure_raw_counts={str(k):sum(z['raw']==k for z in results) for k in range(1,5)},failures_with_lateral_alone_over_limit=sum(z['pure_lateral_ratio_max']>1.059 for z in results),source_failed_queries=len(results),not_a_continuous_control_impossibility_proof=True,model_ticks=counter[0],new_completion_model_ticks=counter[0]-prior['model_ticks'],cost=cost,CPU_s=prior['CPU_s']+time.process_time()-cpu,wall_s=prior['wall_s']+time.perf_counter()-wall,new_native_actions=0,new_resets=0)
 with (G/'retry/dynamic553_diagnostic_completion_result.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2));assert out['passed']
if __name__=='__main__':run()
