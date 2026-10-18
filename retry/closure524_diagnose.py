"""One saved-root replay and fixed force-input substitutions; no live world."""
import datetime,hashlib,json,math,time
from dataclasses import replace,asdict
from pathlib import Path
from retry.plan513_model import load_root
from retry.plan512_control import tick
from retry.brake508_corridor import bounds
from retry.speed516_control import force_rows
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response524-private');OLD=Path('/workspace/haic-response522-private')


def source_ratio(root,action,counts):
    rows=force_rows(root,action);counts[0]+=4;return rows


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/closure524_diagnostic_contract.json').read_text());counter=[0];forces=[0]
    if (D/'DIAGNOSIS_STARTED.json').exists():raise RuntimeError('NO_REPLAY_RETRY')
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(c['deadline_utc'])
    with (D/'DIAGNOSIS_STARTED.json').open('x') as f:json.dump(dict(contract_sha256=hashlib.sha256((G/'retry/closure524_diagnostic_contract.json').read_bytes()).hexdigest()),f)
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());entry=json.loads((OLD/'action-capacity-041.json').read_text());state=entry['before_root_without_roads'];state['roads']=static['root']['roads'];root=load_root(state);command=entry['record']['action'];root=replace(root,planar=replace(root.planar,steer=-float(command[0])));index=bounds(root.roads)
    actual=[json.loads((OLD/f'raw-{i:04d}.json').read_text()) for i in range(1287,1291)];names=('predicted','heading','COM_velocity','wheel_offsets','spin_gas','actual_rigid_pose','all_actual');errors={n:[] for n in names};vectors={n:[] for n in names};metrics=[];private=[];same_res=[];lag_res=[]
    def norm(v):return math.hypot(*v)
    for k,a in enumerate(actual):
        ap=a['before_planar'];state=dict(planar=ap,center=a['before_position'],roads=static['root']['roads'],current_contacts=a['used_contacts'],floor=static['root']['floor'],skin=static['root']['skin']);truth=load_root(state);pred=root;pw=pred.planar.linear.wheels;tw=truth.planar.linear.wheels;pv=pred.planar.linear.velocity;tv=truth.planar.linear.velocity
        def difference(xs,ys):return [x-y for x,y in zip(xs,ys)]
        metrics.append(dict(raw=k+1,max_wheel_heading_error_rad=max(abs(x.heading-y.heading) for x,y in zip(pw,tw)),max_wheel_offset_velocity_error_m_s=max(norm(difference(x.offset,y.offset)) for x,y in zip(pw,tw)),max_wheel_world_velocity_error_m_s=max(norm([pv[j]+x.offset[j]-tv[j]-y.offset[j] for j in range(2)]) for x,y in zip(pw,tw)),max_spin_omega_error_rad_s=max(abs(x.omega-y.omega) for x,y in zip(pw,tw)),hull_angle_error_rad=pred.planar.angle-truth.planar.angle,hull_yaw_error_rad_s=pred.planar.yaw-truth.planar.yaw,COM_velocity_error_m_s=norm(difference(pv,tv)),max_joint_angle_error_rad=max(map(abs,difference(pred.planar.joints,truth.planar.joints))),max_joint_rate_error_rad_s=max(map(abs,difference(pred.planar.rates,truth.planar.rates))),max_lever_error_m=max(norm(difference(x,y)) for x,y in zip(pred.planar.levers,truth.planar.levers))))
        for name in names:
            p=pred.planar;w=list(pw);v=pv
            if name=='heading':w=[replace(x,heading=y.heading) for x,y in zip(w,tw)]
            elif name=='COM_velocity':v=tv
            elif name=='wheel_offsets':w=[replace(x,offset=y.offset) for x,y in zip(w,tw)]
            elif name=='spin_gas':w=[replace(x,omega=y.omega,gas=y.gas) for x,y in zip(w,tw)]
            elif name=='actual_rigid_pose':w=[replace(x,heading=truth.planar.angle+q,offset=(-truth.planar.yaw*r[1],truth.planar.yaw*r[0])) for x,q,r in zip(w,truth.planar.joints,truth.planar.levers)]
            elif name=='all_actual':w=list(tw);v=tv
            q=replace(pred,planar=replace(p,linear=replace(p.linear,wheels=tuple(w),velocity=v)))
            rows=source_ratio(q,command,forces)
            for i,z in enumerate(rows):errors[name].append(z['ratio']-a['forces'][i]['ratio']);vectors[name].append(math.dist(z['vector'],a['forces'][i]['vector']))
        for i,w in enumerate(tw):
            r=truth.planar.levers[i];same=(-truth.planar.yaw*r[1],truth.planar.yaw*r[0]);same_res.append(norm(difference(w.offset,same)))
            if k:
                oldr=actual[k-1]['before_planar']['levers'][i];lag=(-truth.planar.yaw*oldr[1],truth.planar.yaw*oldr[0]);lag_res.append(norm(difference(w.offset,lag)))
        state=asdict(pred);state.pop('roads');private.append(dict(raw=k+1,predicted_before_root_without_roads=state,source_force_input_metrics=metrics[-1]));root=tick(root,float(command[1]),float(command[2]),index,counter)
    def stats(v):return dict(RMSE=math.sqrt(sum(x*x for x in v)/len(v)),max_abs=max(map(abs,v)))
    force_stats={n:dict(force_ratio=stats(errors[n]),postclip_vector_error_N=stats(vectors[n])) for n in names}
    # Matching raw2..4 for both lever-clock residual comparisons.
    same_later=same_res[4:];same_rms=stats(same_later)['RMSE'];lag_rms=stats(lag_res)['RMSE'];base=force_stats['predicted']['force_ratio']['RMSE'];offset=force_stats['wheel_offsets']['force_ratio']['RMSE']
    clear=lag_rms<=.5*same_rms and offset<=.5*base
    out=dict(status='FIXED_INPUT_DIAGNOSIS',force_input_replacement_stats=force_stats,tick_input_errors=metrics,actual_offset_residual_same_tick_lever_m_s=stats(same_later),actual_offset_residual_previous_tick_lever_m_s=stats(lag_res),predeclared_lever_clock_hypothesis_admitted=clear,admission='previouslevervelocityresidualRMSE<=50%samelever AND actualoffsetsubstitutionforceratioRMSE<=50%original; then testonepre-positionleverclosure correction. Notunique motor/solver causality.',model_integrator_ticks=counter[0],source_wheel_force_evaluations_in_integrator=4*counter[0],additional_explicit_force_evaluations=forces[0],native_actions=0,native_resets=0,research_remaining=24641,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,scope='Savedfuture substitutions calibrate input sensitivities only, not policy inputs or independent causal effects. Motor torque saturation is not inferred from joint rate discrepancy alone. Sourceforce ratios are preclip; COM usespostclip.')
    assert counter[0]==4 and forces[0]==112 and out['CPU_s']<30 and out['wall_s']<45
    with (D/'predicted-inputs-private.json').open('x') as f:json.dump(private,f,indent=2)
    (D/'predicted-inputs-private.json').chmod(0o600)
    with (G/'retry/closure524_diagnosis.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
