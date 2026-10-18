"""One actual-root hold and eight fixed local perturbations; calibration only."""
import datetime,hashlib,json,math,time,signal
from dataclasses import replace
from pathlib import Path
from retry.plan513_model import load_root
from retry.plan512_control import tick
from retry.brake508_corridor import bounds
from retry.speed516_control import force_rows
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response523-private');OLD=Path('/workspace/haic-response522-private')


def perturb(root,family,sign):
    p=root.planar;wheels=list(p.linear.wheels)
    if family=='heading':
        joints=list(p.joints)
        for i in (0,1):wheels[i]=replace(wheels[i],heading=wheels[i].heading+sign*.002);joints[i]+=sign*.002
        p=replace(p,joints=tuple(joints))
    elif family=='offset':
        for i in (0,1):
            w=wheels[i];side=(math.cos(w.heading),math.sin(w.heading));wheels[i]=replace(w,offset=tuple(w.offset[j]+sign*.10*side[j] for j in range(2)))
    elif family=='yaw':
        delta=sign*.03;p=replace(p,yaw=p.yaw+delta,angular_momentum=p.angular_momentum+p.inertia*delta)
        for i,(w,r) in enumerate(zip(wheels,p.levers)):wheels[i]=replace(w,offset=(w.offset[0]-delta*r[1],w.offset[1]+delta*r[0]))
    elif family=='spin_slip':wheels=[replace(w,omega=w.omega+sign*.10/.54) for w in wheels]
    else:raise ValueError('UNKNOWN_PERTURBATION')
    return replace(root,planar=replace(p,linear=replace(p.linear,wheels=tuple(wheels))))


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/force523_calibration_contract.json').read_text());counter=[0];force_evals=0
    if (D/'CALIBRATION_STARTED.json').exists():raise RuntimeError('NO_CALIBRATION_RETRY')
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(c['deadline_utc'])
    signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(RuntimeError('CALIBRATION_CPU_CAP')));signal.setitimer(signal.ITIMER_PROF,30)
    signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(RuntimeError('CALIBRATION_WALL_CAP')));signal.setitimer(signal.ITIMER_REAL,45)
    with (D/'CALIBRATION_STARTED.json').open('x') as f:json.dump(dict(contract_sha256=hashlib.sha256((G/'retry/force523_calibration_contract.json').read_bytes()).hexdigest()),f)
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());entry=json.loads((OLD/'action-capacity-041.json').read_text());state=entry['before_root_without_roads'];state['roads']=static['root']['roads'];initial=load_root(state);command=entry['record']['action'];index=bounds(initial.roads)
    actual=[json.loads((OLD/f'raw-{i:04d}.json').read_text()) for i in range(1287,1291)];assert all(z['action']==41 and z['phase']=='action' for z in actual)
    cases=[('conditioned',initial)]+[(f'{family}_{sign:+d}',perturb(initial,family,sign)) for family in ('heading','offset','yaw','spin_slip') for sign in (-1,1)];saved=[];summaries=[]
    for name,root in cases:
        root=replace(root,planar=replace(root.planar,steer=-float(command[0])));rows=[]
        for k in range(4):
            force=force_rows(root,command);force_evals+=4;root=tick(root,float(command[1]),float(command[2]),index,counter)
            rows.append(dict(forces=force,position=root.center,speed=math.hypot(*root.planar.linear.velocity),angle=root.planar.angle,yaw=root.planar.yaw))
        ratios=[[w['ratio'] for w in z['forces']] for z in rows];summaries.append(dict(case=name,maximum_raw_ratio=max(v for z in ratios for v in z)));saved.append(dict(case=name,rows=rows))
    base=saved[0]['rows'];signed=[actual[k]['forces'][i]['ratio']-base[k]['forces'][i]['ratio'] for k in range(4) for i in range(4)]
    error=max(map(abs,signed));under=max(0.,max(signed));sensitivity=max(abs(z['rows'][k]['forces'][i]['ratio']-base[k]['forces'][i]['ratio']) for z in saved[1:] for k in range(4) for i in range(4))
    margin=math.ceil((error+sensitivity+.05)*100)/100;threshold=1.25-margin
    cold=json.loads((OLD/'cold-capacity-model-private.json').read_text());oldrows=[z for z in cold['trace'] if z['index']==41]
    cold_error=max(abs(actual[k]['forces'][i]['ratio']-oldrows[k]['forces'][i]['ratio']) for k in range(4) for i in range(4))
    kine=dict(position_m=max(math.dist(base[k]['position'],actual[k]['position']) for k in range(4)),speed_m_s=max(abs(base[k]['speed']-actual[k]['speed']) for k in range(4)),angle_rad=max(abs(base[k]['angle']-actual[k]['angle']) for k in range(4)),yaw_rad_s=max(abs(base[k]['yaw']-actual[k]['yaw']) for k in range(4)))
    out=dict(status='CALIBRATION_ONLY_NO_NATIVE',actual_root_same_command=True,actual_future_used_as_comparison_labels_only=True,conditioned_max_absolute_force_ratio_error=error,conditioned_max_underprediction=under,cold_different_initial_history_max_absolute_ratio_error=cold_error,local_sensitivity_max_ratio_change=sensitivity,calibrated_empirical_force_margin=margin,proposed_prediction_admission_ratio=threshold,margin_formula='ceil100(max_abs_conditioned_ratio_error + max_fixed_local_sensitivity +0.05)/100; not universal uncertainty bound',cases=summaries,kinematic_errors=kine,model_integrator_ticks=counter[0],source_wheel_force_evaluations_in_integrator=4*counter[0],additional_explicit_force_evaluations=force_evals,native_actions=0,native_resets=0,research_remaining=24641,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,scope='One historical failing hold; fullclosedloop vs conditioned difference helps separate accumulated history from singlehold error but does not identify a unique solver defect or validate unseen regimes.')
    assert counter[0]==36 and force_evals==144
    with (D/'calibration-traces-private.json').open('x') as f:json.dump(saved,f,indent=2)
    (D/'calibration-traces-private.json').chmod(0o600)
    with (G/'retry/force523_calibration.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
