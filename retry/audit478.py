"""478 saved-only hold/late-error analysis. No actor/world/physics imports."""
import datetime,json,math,shutil,sys,time
from pathlib import Path
from retry.audit474_traces import NoPhysics
from retry.audit475_forces import read,sha,put,G
MIB=1024**2

def prepare(root):
 d=Path('/tmp/haic-retry-stage478-private');assert not d.exists() and not(root/'stage478').exists();old=read(root/'stage477-revision1/plan.json');paths=[root/'stage477-revision1'/n for n in ['whole_AllocationP4-private.json','whole_AllocationP4-observer-private.json','whole_Projected4Reference-private.json','whole_Projected4Reference-observer-private.json','plan.json','budget.json','integrated-qualification.json']];paths.extend((root/'stage477-revision1').glob('allocation-*.json'));paths.extend([Path(old['fixed_plan']),Path(old['projection_path']),G/'retry/audit478.py',G/'retry/signed417_executor.py',G/'retry/scalar392_audit.py',G/'retry/pace269_run.py',G/'retry/live477.py',G/'retry/allocator476.py',root/'project-effective-budget-v476.json',root/'stage441/authorization-correction-private.json',root/'stage477-retention-manifest-private.json'])
 ledger=read(root/'project-effective-budget-v476.json');assert (ledger['research_remaining'],ledger['final_reserved_actions'],ledger['final_reserve_used'])==(26175,84000,0)
 free={s:shutil.disk_usage(s).free for s in ['/tmp','/workspace']};assert free['/tmp']>=(16+32+512)*MIB and free['/workspace']>=576*MIB
 p=dict(stage=478,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='SAVED_ONLY_SOURCE_AND_TRACE_ANALYSIS_ONE_FUTURE_CONTRACT',sources={str(f):sha(f) for f in sorted(set(paths))},protected=old['protected'],original408_preserve=old['original408_preserve'],anchors=dict(success=[47],late=[69,70,71,72,73,74],contexts=[45,46,48,64,65,66,67,68]),CPU_cap_s=60,wall_cap_s=120,raw_hard_bytes=16*MIB,reserve_each_bytes=512*MIB,free_bytes=free,new_physics=0,new_native=0,new_world=0,new_reset=0,new_actor=0,new_search=0,deadline_utc='2026-10-20T10:01:55Z',extension_sha256=sha(root/'stage441/authorization-correction-private.json'),stop='missing source/state/hash/schema/numeric inconsistency stops; do not infer absent full state or simulate; no retuning. Existing scalar source reproduced but not newworldqualified',future_designs_max=2,new_archive=False,workspace_new_raw_copies=0)
 d.mkdir(mode=0o700);(root/'stage478').symlink_to(d,target_is_directory=True);put(d/'plan.json',p);put(root/'stage478-plan-durable-private.json',p);print(sha(d/'plan.json'))

def run(root):
 guard=NoPhysics();sys.meta_path.insert(0,guard)
 import numpy as np
 from retry.signed417_executor import canonical_projection
 from retry.scalar392_audit import pedals
 d=root/'stage478';p=read(d/'plan.json');cpu=time.process_time();wall=time.perf_counter()
 for group in ['sources','protected','original408_preserve']:
  for f,h in p[group].items():assert sha(f)==h,f
 src=root/'stage477-revision1';fixed=read(read(src/'plan.json')['fixed_plan']);line=fixed['line'];nodes=read(read(src/'plan.json')['projection_path'])['projected_nodes'];ds=fixed['free_profile']['ds'];arcs=[0.]
 for length in ds:arcs.append(arcs[-1]+length)
 rows={a:read(src/('whole_'+a+'-private.json'))['rows'] for a in ['AllocationP4','Projected4Reference']};posts={a:read(src/('whole_'+a+'-observer-private.json'))['posts'] for a in rows};proofs={q['action']:q for q in (read(f) for f in src.glob('allocation-proof-*.json')) if q['label']=='whole_AllocationP4'};inputs={q['action']:q for q in (read(f) for f in src.glob('allocation-input-*.json')) if q['label']=='whole_AllocationP4'}
 def wrap(a):return (a+math.pi)%(2*math.pi)-math.pi
 def body(h):
  q=canonical_projection(line,h['origin_position'],h['COM_linear_velocity'],'FIRST_LAP');j=q['index'];edge=np.asarray(line[(j+1)%len(line)])-line[j];theta=math.atan2(edge[1],edge[0]);v=math.hypot(*h['COM_linear_velocity']);course=math.atan2(h['COM_linear_velocity'][1],h['COM_linear_velocity'][0]);r=math.sqrt((1-q['u'])*nodes[j]**2+q['u']*nodes[j+1]**2);f=(nodes[j+1]**2-nodes[j]**2)/(2*ds[j]);raw=f*q['sigma']/r+1.5*(r-v)
  return dict(time=h['time'],arc=q['arc'],path_error_m=q['path_error_m'],speed=v,sigma=q['sigma'],heading_error=wrap(h['angle']+math.pi/2-theta),course_error=wrap(course-theta),sideslip_angle=wrap(course-(h['angle']+math.pi/2)),yaw=h['yaw'],target_speed=r,reference_f=f,raw_scalar_accel=raw,clamped_scalar_accel=pedals(raw,v,fixed['model'])['command_accel'],preview_distance=max(6.,min(25.,3.24+.22*v)),v_minus_r=v-r)
 def wheelgroup(ts,ids):
  group=[t for t in ts if t['wheel'] in ids];out={}
  for key in ['omega','gas','brake','lateral_slip_m_s','longitudinal_slip_m_s','raw_long_N','raw_lat_N','joint_angle']:
   out[key]=[t[key] for t in group]
  out.update(max_lat_only_ratio=max(abs(t['raw_lat_N'])/t['friction_limit'] for t in group),max_long_only_ratio=max(abs(t['raw_long_N'])/t['friction_limit'] for t in group),max_combined_ratio=max(t['force_ratio'] for t in group),clip_retention_min=min(1/max(1,t['force_ratio']) for t in group),mean_lat_force_after_clip=sum(t['raw_lat_N']/max(1,t['force_ratio']) for t in group)/2,mean_long_force_after_clip=sum(t['raw_long_N']/max(1,t['force_ratio']) for t in group)/2)
  return out
 allrows=[];exactnominal=0
 for wi,row in enumerate(rows['AllocationP4'],1):
  start=body(row['raw_hull'][0]);post=posts['AllocationP4'][4*(wi-1):4*wi];end=post[-1];endh=dict(time=end['time'],origin_position=end['position'],COM_linear_velocity=end['velocity'],angle=row['predicted']['angle'],yaw=row['predicted']['angular_velocity']);endbody=body(endh);computed=np.asarray([pedals(start['raw_scalar_accel'],start['speed'],fixed['model'])[k] for k in ['gas','brake']],np.float32).tolist();nominal=inputs[wi]['nominal'][1:];same=computed==nominal;exactnominal+=same
  ticks=[]
  for k,h in enumerate(row['raw_hull'],1):
   ts=[t for t in row['tires'] if t['raw_tick']==k];q=body(h);g={name:wheelgroup(ts,ids) for name,ids in [('front',(0,1)),('rear',(2,3))]};ticks.append(dict(raw=k,pre=q,post_path_error_m=canonical_projection(line,post[k-1]['position'],post[k-1]['velocity'],'FIRST_LAP')['path_error_m'],guard_path_error_m=post[k-1]['path_error_m'],axles=g,M=max(0.,max(t['force_ratio']-1 for t in ts))))
  z=dict(action=wi,selected=wi in p['anchors']['success']+p['anchors']['late'],start=start,end=endbody,nominal=inputs[wi]['nominal'],command=row['command'],changed=proofs[wi]['changed'],nominal_scalar_pedals_reproduced=same,objective_q0=proofs[wi]['proof']['objective_q0'],objective_first=proofs[wi]['proof']['objective'],M_hold=max(t['M'] for t in ticks),M_raw=[t['M'] for t in ticks],path_guard_max=max(t['guard_path_error_m'] for t in ticks),speed_delta=endbody['speed']-start['speed'],observed_speed_change_per_s=(endbody['speed']-start['speed'])/.08,safety=row['safety'],wheel_before=inputs[wi]['current_wheels'],ticks=ticks,steering_target_joint=-row['command'][0],max_joint_target_error=max(abs(t['joint_angle']+row['command'][0]) for t in row['tires'] if t['wheel']<2))
  allrows.append(z)
 # Point raw acceleration recomputation may differ at sub-ulp due source expression
 # ordering; actual float32 nominal identity is reported, never silently forced.
 summary=[]
 for z in allrows:
  if z['action'] not in p['anchors']['success']+p['anchors']['late']+p['anchors']['contexts']:continue
  q={k:v for k,v in z.items() if k not in ['ticks','wheel_before']};q['first_axles']=z['ticks'][0]['axles'];q['last_axles']=z['ticks'][-1]['axles'];q['first_lateral_alone_above']=any(a['max_lat_only_ratio']>1 for a in q['first_axles'].values());summary.append(q)
 selected=[z for z in allrows if z['selected']];late=[z for z in selected if z['action']>=69];before=context=[z for z in allrows if 64<=z['action']<=68];out=dict(stage=478,status='SAVED_HOLD_ANALYSIS_COMPLETE_NO_INTEGRATION',plan_sha256=sha(d/'plan.json'),actions_analyzed=len(allrows),scalar_nominal_exact_float32=exactnominal,selected=summary,conclusions=dict(all7_changed_pedals_were_gas=True if all(z['changed'] and z['nominal'][1]>0 and z['nominal'][2]==0 for z in selected) else False,brake_reduction_in_selected=any(z['command'][2]<z['nominal'][2] for z in selected),late_hold_M_exceeds_first=sum(z['M_hold']>z['objective_first'] for z in late),late_first_lateral_alone_above=sum(any(a['max_lat_only_ratio']>1 for a in z['ticks'][0]['axles'].values()) for z in late),late_first_path_over3=sum(z['start']['path_error_m']>3 for z in late),late_first_yaw_range=[min(z['start']['yaw'] for z in late),max(z['start']['yaw'] for z in late)],intervening_nominal_brake_actions=[z['action'] for z in before if z['nominal'][2]>0],hold80ms_constant=True,firstraw_certificate_is_not_horizon_certificate=True),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,new_physics=0,new_native=0,new_world=0,new_reset=0,new_actor=0,new_search=0,import_guard_attempts=guard.attempts,deadline_utc=p['deadline_utc'])
 for group in ['sources','protected','original408_preserve']:
  for f,h in p[group].items():assert sha(f)==h,f
 put(d/'rows-private.json',allrows);put(d/'result.json',out);put(G/'retry/audit478_result.json',out);print(json.dumps({k:v for k,v in out.items() if k!='selected'}))
if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
