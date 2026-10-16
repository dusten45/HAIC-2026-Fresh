"""Aggregate registered390 measurements only; no env, actor or model calls."""
import datetime,json,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha

def intervals(mask,dt):
    out=[];start=None
    for i,flag in enumerate(list(mask)+[False]):
        if flag and start is None:start=i
        if not flag and start is not None:out.append(dict(first_step=start+1,last_step=i,duration_s=float(sum(dt[start:i]))));start=None
    return out

def A_case(root,key):
    d=root/'stage390';rows=read(d/('A-'+key)/'trace-private.json');result=read(d/('A-'+key)/'result.json');line=np.array(read(d/('A-'+key)/'fixed-geometry-private.json')['line']);N=len(line)
    dt=np.array([r['post']['time']-r['pre']['time'] for r in rows]);pretime=np.array([r['pre']['time'] for r in rows]);t0=pretime[0]
    if result['completed']:dt=np.minimum(dt,np.maximum(0,t0+result['lap_ms']/1000-pretime))
    c=[r['control'] for r in rows];speed=np.array([r['pre']['speed'] for r in rows]);q=np.array([r['target_speed_m_s'] for r in c]);cursor=np.array([r['cursor_fraction'] for r in c]);near=np.unwrap(np.array([r['nearest_fraction'] for r in c])/N*2*np.pi)*N/(2*np.pi);near+=round((cursor[0]-near[0])/N)*N;gap=cursor-near
    roadloss=np.array([any(n==0 for n in r['pre']['road_contacts']) for r in rows]);err=np.array([r['cursor_path_error_m'] for r in c]);safe=np.logical_and.accumulate(~(roadloss|(err>3)))
    gapruns=intervals((abs(gap)>2)&safe,dt);progressgate=any(r['last_step']-r['first_step']+1>=3 for r in gapruns)
    constraints=np.array([r['positive_accel_clamped'] or r['negative_accel_clamped'] or r['action'][2]>0 for r in c]);lagruns=intervals((q-speed>10)&constraints,dt);speedgate=any(r['duration_s']>=1-1e-8 for r in lagruns)
    unwrapped_arc=np.unwrap(np.array([r['nearest_arc_m'] for r in c])/sum(np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1))*2*np.pi)*sum(np.linalg.norm(np.roll(line,-1,axis=0)-line,axis=1))/(2*np.pi)
    pos=np.array([r['pre']['pos'] for r in rows]);postpos=np.array([r['post']['pos'] for r in rows]);vel=np.array([r['pre']['vel'] for r in rows]);ang=np.array([r['pre']['angle'] for r in rows]);fwd=np.sum(vel*np.c_[-np.sin(ang),np.cos(ang)],axis=1)
    def secs(mask):return float(sum(dt[np.asarray(mask)]))
    def first(mask):return int(np.flatnonzero(mask)[0]+1) if any(mask) else None
    visited=np.array([r['pre']['visited'] for r in rows]);lastnew=max([i for i,r in enumerate(rows) if r['post']['visited']>r['pre']['visited']],default=-1)
    windows=[]
    for lo,hi in [(1,64),(65,128),(129,len(rows))]:
        if lo>len(rows):continue
        z=rows[lo-1:hi];w=dt[lo-1:hi];windows.append(dict(first_step=lo,last_step=min(hi,len(rows)),time_s=float(sum(w)),mean_speed_m_s=float(np.average(speed[lo-1:hi],weights=w)),mean_target_m_s=float(np.average(q[lo-1:hi],weights=w)),visited_pre=int(z[0]['pre']['visited']),visited_post=int(z[-1]['post']['visited']),max_cursor_gap_segments=float(max(abs(gap[lo-1:hi]))),max_cursor_path_error_m=max(r['control']['cursor_path_error_m'] for r in z),wheel_contact_loss_s=secs(np.array([lo<=i+1<=hi for i in range(len(rows))])&roadloss)))
    return dict(case=key,result=result,time_s=float(sum(dt)),distance_observed_chord_m=float(np.linalg.norm(postpos-pos,axis=1).sum()),distance_scope='Actual wrapper endpoints, terminal chord includes post-finish portion, no exact continuous distance',mean_speed_m_s=float(np.average(speed,weights=dt)),mean_target_m_s=float(np.average(q,weights=dt)),lag_over10_s=secs(q-speed>10),lag_with_constraint_s=secs((q-speed>10)&constraints),longest_lag_with_constraint_s=max((r['duration_s'] for r in lagruns),default=0),brake_below_target_s=secs((speed<q)&np.array([r['action'][2]>0 for r in c])),positive_accel_clamped_s=secs([r['positive_accel_clamped'] for r in c]),negative_accel_clamped_s=secs([r['negative_accel_clamped'] for r in c]),gas_at1_s=secs([r['action'][1]>=.999999 for r in c]),wheel_gas_slew_present_s=secs([r['post']['wheel_gas'][2]+1e-6<r['control']['action'][1] or r['post']['wheel_gas'][3]+1e-6<r['control']['action'][1] for r in rows]),rear_unclipped_positive_clamp_gasbelow1_s=secs([r['control']['positive_accel_clamped'] and r['control']['action'][1]<.999999 and r['tire']['rear']['clipped_fraction']==0 for r in rows]),rear_clipping_action_s=secs([r['tire']['rear']['clipped_fraction']>0 for r in rows]),first_wheel_road_loss_step=first(roadloss),first_patherror_over3_step=first(err>3),first_negative_body_forward_step=first(fwd<-.1),negative_body_forward_s=secs(fwd<-.1),max_abs_cursor_gap_segments=float(max(abs(gap))),first_cursor_gap_over2_step=first(abs(gap)>2),cursor_gap_over2_runs_before_departure=gapruns,nearest_arc_net_m=float(unwrapped_arc[-1]-unwrapped_arc[0]),last_new_tile_step=lastnew+1,after_last_new_tile_s=float(sum(dt[lastnew+1:])),final_visited=rows[-1]['post']['visited'],total_reference_nodes=N,final_offtrackcounter=rows[-1]['post']['off_track_counter'],max_offtrackcounter=max(r['post']['off_track_counter'] for r in rows),windows=windows,registered_gates=dict(progress_state=progressgate,speed_execution=bool(not progressgate and speedgate)),gate_scope='Nearest planned polyline spatial projection can be ambiguous; no force-limit optimum or causal seconds claim')

def B(root):
    d=root/'stage390';p=read(d/'plan.json');base=read(d/'B-capture/trace-private.json');model=read(d/'B-model-gate.json');pred=read(d/'B-model-predictions-private.json');records=[]
    for state in p['B_states']:
        step=state['step'];original=base[step-1];pre=original['pre'];ang=pre['angle'];forward=np.array([-np.sin(ang),np.cos(ang)]);lateral=np.array([np.cos(ang),np.sin(ang)])
        arms=[]
        for arm in p['B_arms']:
            if arm=='original':r=original;q=next(x['predicted'] for x in model['records'] if x['step']==step)
            else:
                f=d/('B-'+str(step)+'-'+arm)
                if not (f/'result.json').exists():continue
                result=read(f/'result.json')
                if result['technical_error']:continue
                r=read(f/'trace-private.json')[-1];q=next(x['predicted'] for x in pred if x['step']==step and x['arm']==arm)
            post=r['post'];dv=np.array(post['vel'])-original['post']['vel'];dp=np.array(post['pos'])-original['post']['pos'];dy=post['yaw']-original['post']['yaw'];safe=(not r['collision'] and r['damage']==original['damage'] and all(n>0 for n in post['road_contacts']) and all(a>=b for a,b in zip(post['road_contacts'],original['post']['road_contacts'])))
            arms.append(dict(arm=arm,action=r['command'],end_speed_m_s=post['speed'],end_forward_velocity_m_s=float(np.array(post['vel'])@forward),delta_forward_velocity_m_s=float(dv@forward),delta_lateral_velocity_m_s=float(dv@lateral),delta_yaw_rate_rad_s=dy,delta_lateral_position_m=float(dp@lateral),collision=r['collision'],damage=r['damage'],wheel_road_contact_count=sum(n>0 for n in post['road_contacts']),new_contact_or_loss=not safe,tire=r['tire'],predicted_end_forward_velocity_m_s=float(np.array(q['velocity'])@forward),prediction_speed_error_m_s=abs(q['speed_m_s']-post['speed']),prediction_yaw_error_rad_s=abs(q['angular_velocity']-post['yaw']),prediction_position_error_m=float(np.linalg.norm(np.array(q['position'])-post['pos'])),local_headroom_gate=bool(arm!='original' and safe and dv@forward>=.5 and abs(dy)<=.05)))
        arank=[a['arm'] for a in sorted(arms,key=lambda x:x['end_forward_velocity_m_s'],reverse=True)];prank=[a['arm'] for a in sorted(arms,key=lambda x:x['predicted_end_forward_velocity_m_s'],reverse=True)];records.append(dict(step=step,phase=state['phase'],arms=arms,actual_forward_ranking=arank,predicted_forward_ranking=prank,ranking_exact=arank==prank))
    return dict(model_gate={k:v for k,v in model.items() if k!='records'},model_original_errors=[dict(step=x['step'],phase=x['phase'],errors=x['errors'],initialization=x['initialization'],discrete=x['discrete'],passed=x['passed']) for x in model['records']],states=records,local_headroom_passed=any(a['local_headroom_gate'] for r in records for a in r['arms']),scope='2selectedstates,4rawticks;original measuredinB0,changedarms onlyafterbothmodelgates;candidate ranking diagnostic notMPC orwholelapclaim')

def run(root):
    d=root/'stage390';assert not(d/'analysis.json').exists();start,cpu=time.perf_counter(),time.process_time();a=[A_case(root,k) for k in ['O0','N1']];b=B(root);x=dict(stage=390,A=a,B=b,cost=read(d/'budget.json'),analysis_CPU_s=time.process_time()-cpu,analysis_wall_s=time.perf_counter()-start,new_native_this_analysis=0,new_model_this_analysis=0)
    save(d/'analysis.json',x);print(json.dumps(x,ensure_ascii=False),flush=True)
if __name__=='__main__':run(Path(__import__('sys').argv[1]))
