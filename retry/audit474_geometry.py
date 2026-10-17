"""474 independent stored-state pursuit arithmetic, never applies a new action."""
import bisect,json,math,struct,sys,time
from pathlib import Path
from retry.audit474_traces import RUNS,Geometry,NoPhysics,read,sha,put,wrap

def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def run(root):
    root=Path(root);d=root/'stage474';assert not(d/'geometry-private.json').exists();guard=NoPhysics();sys.meta_path.insert(0,guard)
    started=time.process_time();p=read(d/'plan.json');fixed=read(read(root/'stage473/plan.json')['fixed_plan']);line=fixed['line'];ds=fixed['free_profile']['ds'];sarc=[0.]
    for length in ds:sarc.append(sarc[-1]+length)
    N=len(line);L=sarc[-1];points=[];summary={}
    for label,(rel,observer) in RUNS.items():
        raw=read(root/rel) if observer else None;rows=raw['rows'] if observer else [json.loads(s) for s in (root/rel).read_text().splitlines() if s];runpoints=[]
        for wrapper,row in enumerate(rows,1):
            h=row['raw_hull'][0];before=row['memory_before'];after=row['memory_after'] if observer else row['nominal_memory_after'];index=after['index'];pos=h['origin_position'];vel=h['COM_linear_velocity'];v=math.hypot(*vel);angle=h['angle']
            candidates=range(max(0,before['index']-2),before['index']+18);computed=max(before['index'],min(candidates,key=lambda c:(line[c%N][0]-pos[0])**2+(line[c%N][1]-pos[1])**2));i=index%N;a=line[i];b=line[(i+1)%N];edge=[b[0]-a[0],b[1]-a[1]];u=max(0.,min(1.,((pos[0]-a[0])*edge[0]+(pos[1]-a[1])*edge[1])/max(edge[0]**2+edge[1]**2,1e-9)))
            arc=sarc[i]+u*ds[i];look=max(6.,min(25.,3.24+.22*v));goal=(arc+look)%L;j=min(N-1,bisect.bisect_right(sarc,goal)-1);alpha=(goal-sarc[j])/max(ds[j],1e-9);target=[line[j][k]+alpha*(line[(j+1)%N][k]-line[j][k]) for k in [0,1]];delta=[target[k]-pos[k] for k in [0,1]];x=delta[0]*math.cos(angle)+delta[1]*math.sin(angle);y=-delta[0]*math.sin(angle)+delta[1]*math.cos(angle);distance2=delta[0]**2+delta[1]**2
            angle_raw=math.atan(2*3.24*x/max(distance2,1e-6));clipped=max(-.4,min(.4,angle_raw));filtered=.8*clipped+.2*before['laststeer'];nominal=row['command'][0] if observer else row['nominal'][0];error=abs(f32(filtered)-nominal)
            q=dict(run=label,wrapper=wrapper,physical_time=h['time'],elapsed_from_reset_s=h['time']-1.02,index_before=before['index'],index_after=index,computed_index=computed,cursor_reproduced=computed==index,control_cursor_arc=arc,preview_m=look,preview_seconds_at_boundary_speed=None if v==0 else look/v,distance_at_80ms_hold=v*.08,speed_COM=v,target_bodyright_m=x,target_bodyforward_m=y,target_chord_m=math.sqrt(distance2),pursuit_unclipped_rad=angle_raw,pursuit_clipped_rad=clipped,pursuit_clip_active=abs(angle_raw)>.4,filtered_source_rad=filtered,source_float32_error_rad=error,actual_steer=row['command'][0],nominal_steer=nominal,actual_matches_nominal=row['command'][0]==nominal,saved_state_no_filter_counterfactual_steer=f32(clipped),saved_state_no_filter_delta_rad=f32(clipped)-nominal,nominal_gas_brake=row['command'][1:],counterfactual_is_independent_stored_state_not_closed_loop=True)
            runpoints.append(q);points.append(q)
        summary[label]=dict(wrappers=len(runpoints),max_source_float32_error_rad=max(q['source_float32_error_rad'] for q in runpoints),cursor_mismatches=sum(not q['cursor_reproduced'] for q in runpoints),pursuit_clip_actions=sum(q['pursuit_clip_active'] for q in runpoints),counterfactual_steer_changed_actions=sum(q['saved_state_no_filter_delta_rad']!=0 for q in runpoints),max_abs_counterfactual_steer_delta_rad=max(abs(q['saved_state_no_filter_delta_rad']) for q in runpoints),actual_nominal_override_actions=sum(not q['actual_matches_nominal'] for q in runpoints))
    assert all(v['max_source_float32_error_rad']<1e-6 and v['cursor_mismatches']==0 for v in summary.values()),'stored arithmetic reproduction failed'
    out=dict(stage=474,analysis='INDEPENDENT_STORED_STATE_PURSUIT_ARITHMETIC',runs=summary,records=points,geometry=dict(reference_point='hull origin; speed=COM magnitude',rear_axle_local_y_m=-1.64,wheelbase_m=3.24,bodyright_sign='positive x -> positive action -> negative front joint -> right turn',lookahead='clamp(3.24+.22*speed,6,25)',hold_s=.08,filter='.8current+.2previous',counterfactual='Only remove the additional filter; every stored state is independent, new action is never propagated'),new_physics=0,new_native=0,new_actor=0,import_guard_attempts=guard.attempts,CPU_s=time.process_time()-started)
    put(d/'geometry-private.json',out);print(json.dumps({k:v for k,v in out.items() if k not in ('records',)}));return out

if __name__=='__main__':run(Path(sys.argv[1]))
