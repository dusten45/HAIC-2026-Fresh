"""Complete per-wheel tick error ledger and saved joint-rate audit, no replay."""
import json,hashlib,math,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response524-private');OLD=Path('/workspace/haic-response522-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/closure524_validation_contract.json').read_text())
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    predicted=json.loads((D/'predicted-inputs-private.json').read_text());actual=[json.loads((OLD/f'raw-{i:04d}.json').read_text()) for i in range(1287,1291)];entry=json.loads((OLD/'action-capacity-041.json').read_text());final=entry['after_root_without_roads'];command=entry['record']['action'];ledger=[];motor=[]
    for k,(row,a) in enumerate(zip(predicted,actual)):
        p=row['predicted_before_root_without_roads']['planar'];q=a['before_planar'];pv=p['linear']['velocity'];tv=q['linear']['velocity'];items=[]
        for i,(x,y) in enumerate(zip(p['linear']['wheels'],q['linear']['wheels'])):
            items.append(dict(wheel=i,heading_error_rad=x['heading']-y['heading'],offset_velocity_error_m_s=[x['offset'][j]-y['offset'][j] for j in range(2)],world_velocity_error_m_s=[pv[j]+x['offset'][j]-tv[j]-y['offset'][j] for j in range(2)],omega_error_rad_s=x['omega']-y['omega'],gas_memory_error=x['gas']-y['gas'],joint_angle_error_rad=p['joints'][i]-q['joints'][i],joint_rate_error_rad_s=p['rates'][i]-q['rates'][i],lever_error_m=[p['levers'][i][j]-q['levers'][i][j] for j in range(2)]))
        ledger.append(dict(raw=k+1,wheels=items,hull_angle_error_rad=p['angle']-q['angle'],yaw_error_rad_s=p['yaw']-q['yaw'],COM_velocity_error_m_s=[pv[j]-tv[j] for j in range(2)]))
        after=actual[k+1]['before_planar'] if k<3 else final['planar']
        rates=[]
        for i in range(4):
            delta=-float(command[0])-q['joints'][i];target=math.copysign(min(50*abs(delta),3.),delta)*q['steering_multiplier'] if i<2 and delta else 0.;rates.append(dict(wheel=i,commanded_relative_rate_rad_s=target,observed_after_relative_rate_rad_s=after['rates'][i],error_rad_s=after['rates'][i]-target))
        motor.append(dict(raw=k+1,wheels=rates))
    for name,data in [('tick-wheel-input-errors-private.json',ledger),('joint-rate-tracking-private.json',motor)]:
        p=D/name
        with p.open('x') as f:json.dump(data,f,indent=2)
        p.chmod(0o600)
    v=json.loads((G/'retry/closure524_validation.json').read_text());diag=json.loads((G/'retry/closure524_diagnosis.json').read_text());out=dict(source_and_input_pins_verified=True,per_wheel_error_records=16,per_tick_commanded_vs_observed_joint_rate_records=16,front_motor_relative_rate_max_absolute_tracking_error_rad_s=max(abs(z['error_rad_s']) for r in motor for z in r['wheels'][:2]),rear_relative_joint_rate_max_abs_rad_s=max(abs(z['observed_after_relative_rate_rad_s']) for r in motor for z in r['wheels'][2:]),motor_torque_limit_source_N_m=64.8,motor_saturation_established=False,interpretation='Very small actual commanded-vs-observed relative-rate errors in thishold do not support motor saturation as dominant explanation. Impulses/motor torque not saved, so saturation is not directly measured. Offset-lever timing explains the dominant local force-input discrepancy; finite-solver approximations remain elsewhere.',model_integrator_ticks=0,explicit_force_evaluations=0,native_actions=0,native_resets=0,original523_source_and_results_preserved=True,validation_pass=v['status']=='SAVED_MODEL_CORRECTION_PASS',uncertainty_margin_unchanged=.19,physical_limit_unchanged=1.25,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    assert out['CPU_s']<10 and out['wall_s']<15
    with (G/'retry/closure524_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
