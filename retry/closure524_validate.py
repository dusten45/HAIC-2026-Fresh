"""One structural model correction on frozen failure/normal/turn saved holds."""
import hashlib,json,math,time
from dataclasses import replace,asdict
from pathlib import Path
from retry.plan513_model import load_root
from retry.plan512_control import tick as original_tick
from retry.closure524_control import tick as corrected_tick
from retry.speed516_control import force_rows
from retry.brake508_corridor import bounds
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response524-private');OLD=Path('/workspace/haic-response522-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();counter=[0];force_evals=0;c=json.loads((G/'retry/closure524_validation_contract.json').read_text());diag=json.loads((G/'retry/closure524_diagnosis.json').read_text());assert diag['predeclared_lever_clock_hypothesis_admitted']
    if (D/'VALIDATION_STARTED.json').exists():raise RuntimeError('NO_CORRECTION_RETRY')
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    with (D/'VALIDATION_STARTED.json').open('x') as f:json.dump(dict(contract_sha256=hashlib.sha256((G/'retry/closure524_validation_contract.json').read_bytes()).hexdigest()),f)
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());selection=[dict(label='failure',action_index=41,checkpoint=str(OLD/'action-capacity-041.json'),raw_files=[str(OLD/f'raw-{i:04d}.json') for i in range(1287,1291)])]+json.loads((D/'validation-selection-private.json').read_text());results=[]
    def stats(v):return dict(RMSE=math.sqrt(sum(z*z for z in v)/len(v)),max_abs=max(map(abs,v)))
    for case in selection:
        entry=json.loads(Path(case['checkpoint']).read_text());state=entry['before_root_without_roads'];state['roads']=static['root']['roads'];initial=load_root(state);command=entry['record']['action'];actual=[json.loads(Path(p).read_text()) for p in case['raw_files']];index=bounds(initial.roads)
        for arm,step in [('original',original_tick),('corrected',corrected_tick)]:
            if case['label']=='failure' and arm=='original':
                previous=json.loads((G/'retry/force523_calibration.json').read_text());results.append(dict(label='failure',action_index=41,arm=arm,force_ratio=diag['force_input_replacement_stats']['predicted']['force_ratio'],postclip_vector_error_N=diag['force_input_replacement_stats']['predicted']['postclip_vector_error_N'],kinematic_errors=previous['kinematic_errors'],max_predicted_ratio=1.178769383780067,reused_model_ticks_not_new=4));continue
            root=replace(initial,planar=replace(initial.planar,steer=-float(command[0])));ratio=[];vector=[];rows=[];peak=0.;kine={k:0. for k in ('position_m','speed_m_s','angle_rad','yaw_rad_s')};inputerr={k:0. for k in ('wheel_heading_rad','wheel_offset_velocity_m_s','wheel_world_velocity_m_s','omega_rad_s','joint_angle_rad','joint_rate_rad_s')}
            for k in range(4):
                truth=actual[k]['before_planar'];tw=truth['linear']['wheels'];pv=root.planar.linear.velocity;tv=truth['linear']['velocity']
                inputerr['wheel_heading_rad']=max(inputerr['wheel_heading_rad'],max(abs(w.heading-x['heading']) for w,x in zip(root.planar.linear.wheels,tw)));inputerr['wheel_offset_velocity_m_s']=max(inputerr['wheel_offset_velocity_m_s'],max(math.dist(w.offset,x['offset']) for w,x in zip(root.planar.linear.wheels,tw)));inputerr['wheel_world_velocity_m_s']=max(inputerr['wheel_world_velocity_m_s'],max(math.dist([pv[j]+w.offset[j] for j in range(2)],[tv[j]+x['offset'][j] for j in range(2)]) for w,x in zip(root.planar.linear.wheels,tw)));inputerr['omega_rad_s']=max(inputerr['omega_rad_s'],max(abs(w.omega-x['omega']) for w,x in zip(root.planar.linear.wheels,tw)));inputerr['joint_angle_rad']=max(inputerr['joint_angle_rad'],max(abs(a-b) for a,b in zip(root.planar.joints,truth['joints'])));inputerr['joint_rate_rad_s']=max(inputerr['joint_rate_rad_s'],max(abs(a-b) for a,b in zip(root.planar.rates,truth['rates'])))
                force=force_rows(root,command);force_evals+=4;peak=max(peak,max(z['ratio'] for z in force))
                for i,z in enumerate(force):ratio.append(z['ratio']-actual[k]['forces'][i]['ratio']);vector.append(math.dist(z['vector'],actual[k]['forces'][i]['vector']))
                root=step(root,float(command[1]),float(command[2]),index,counter)
                err=dict(position_m=math.dist(root.center,actual[k]['position']),speed_m_s=abs(math.hypot(*root.planar.linear.velocity)-actual[k]['speed']),angle_rad=abs(root.planar.angle-actual[k]['angle']),yaw_rad_s=abs(root.planar.yaw-actual[k]['yaw']))
                for name,v in err.items():kine[name]=max(kine[name],v)
                state=asdict(root);state.pop('roads');rows.append(dict(raw=k+1,forces=force,after_root_without_roads=state))
            item=dict(label=case['label'],action_index=case['action_index'],arm=arm,force_ratio=stats(ratio),postclip_vector_error_N=stats(vector),kinematic_errors=kine,max_force_input_errors=inputerr,max_predicted_ratio=peak,reused_model_ticks_not_new=0);results.append(item)
            with (D/f"validation-{case['label']}-{arm}-private.json").open('x') as f:json.dump(dict(summary=item,trace=rows),f,indent=2)
            (D/f"validation-{case['label']}-{arm}-private.json").chmod(0o600)
    pairs={label:{z['arm']:z for z in results if z['label']==label} for label in ('failure','normal','turn')};old=pairs['failure']['original'];new=pairs['failure']['corrected']
    failure_pass=new['force_ratio']['RMSE']<=.5*old['force_ratio']['RMSE'] and new['force_ratio']['max_abs']<=min(.05,.5*old['force_ratio']['max_abs']) and new['max_predicted_ratio']>1.25
    aggregate=lambda arm:math.sqrt(sum(pairs[label][arm]['force_ratio']['RMSE']**2 for label in ('normal','turn'))/2)
    other_pass=aggregate('corrected')<=.75*aggregate('original') and all(pairs[label]['corrected']['force_ratio']['max_abs']<=min(.05,pairs[label]['original']['force_ratio']['max_abs']+.01) for label in ('normal','turn'))
    kine_pass=all(all(z['kinematic_errors'][k]<=limit for k,limit in [('position_m',.10),('speed_m_s',.15),('angle_rad',.02),('yaw_rad_s',.05)]) for z in results if z['arm']=='corrected')
    out=dict(status='SAVED_MODEL_CORRECTION_PASS' if failure_pass and other_pass and kine_pass else 'SAVED_MODEL_CORRECTION_REJECTED',failure_force_gate=failure_pass,separate_holds_force_gate=other_pass,kinematic_gate=kine_pass,arms=results,separate_holds_aggregate_force_ratio_RMSE=dict(original=aggregate('original'),corrected=aggregate('corrected')),new_model_integrator_ticks=counter[0],reused_diagnostic_ticks_not_new=4,source_wheel_force_evaluations_in_integrator=4*counter[0],additional_explicit_force_evaluations=force_evals,uncertainty_margin_unchanged=.19,physical_force_limit_unchanged=1.25,native_actions=0,native_resets=0,research_remaining=24641,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,scope='ThreeexistingDEVholds,saved-onlymodelaccuracyvalidation. Failurecaseisexpectedtoaccuratelypredictunsafephysicalratio>1.25,nottohideit. Finitejoint/motor/solverapproximationsremain; no globalerrorbound/nativeeligibility/full-lapgainclaim. Actualfuturelabelsneverpolicyinput.')
    assert counter[0]==20 and force_evals==80 and out['CPU_s']<60 and out['wall_s']<90
    with (G/'retry/closure524_validation.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
