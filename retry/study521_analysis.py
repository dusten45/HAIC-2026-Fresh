"""Finite read-only source force explanation of thirteen saved520 holds."""
import hashlib,json,math,time
from pathlib import Path
from retry.plan513_model import load_root
from retry.brake502_response import wheel_response,POWER,INERTIA,RADIUS
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response521-private')

def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/study521_contract.json').read_text())
    for n,h in c['analysis_source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    data=json.loads(Path('/workspace/haic-response520-private/cold-response-model-private.json').read_text());wanted={x['action_index']:x for x in json.loads(Path('/workspace/haic-response520-private/unreachable-holds-private.json').read_text())};static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());before=static['root'];prior_action=None;records=[];active=None;evals=0;oracle_error=0.
    for row in data['trace']:
        if row['raw']==1:
            active=None
            if row['index'] in wanted:
                x=wanted[row['index']];state=dict(before);state['roads']=static['root']['roads'];root=load_root(state);speed=math.hypot(*root.planar.linear.velocity)
                active=dict(action_index=row['index'],desired_acceleration=x['desired_acceleration'],target_deficit=x['target_deficit'],speed_start=speed,engine_multiplier=root.planar.linear.engine_multiplier,prior_brake=prior_action[2],rear_gas_start=[w.gas for w in root.planar.linear.wheels[2:]],rear_omega_start=[w.omega for w in root.planar.linear.wheels[2:]],ticks=[]);records.append(active)
        if active:
            state=dict(before);state['roads']=static['root']['roads'];root=load_root(state);velocity=root.planar.linear.velocity;speed=math.hypot(*velocity);unit=tuple(v/speed for v in velocity);forces=[];wheels=[]
            for i,w in enumerate(root.planar.linear.wheels):
                gas=w.gas+min(.1,1.-w.gas) if i>=2 else w.gas
                after,force,extra=wheel_response(w,velocity,gas,0.,root.planar.linear.engine_multiplier);evals+=1;forces.append(force)
                oracle_error=max(oracle_error,math.dist(force,row['forces'][i]['vector']))
                forward=(-math.sin(w.heading),math.cos(w.heading));vf=sum(forward[j]*(velocity[j]+w.offset[j]) for j in range(2))
                wheels.append(dict(rear=i>=2,gas=gas,omega=w.omega,engine_delta_omega=.02*POWER*root.planar.linear.engine_multiplier*gas/INERTIA/(abs(w.omega)+5.),pre_engine_longitudinal_slip=w.omega*RADIUS-vf,post_engine_longitudinal_slip=extra['omega_braked']*RADIUS-vf,longitudinal_force=extra['longitudinal_force'],lateral_force=extra['lateral_force'],friction=w.friction,clipped=extra['clipped']))
            acceleration=sum(sum(f[j]*unit[j] for j in range(2)) for f in forces)/root.planar.linear.mass
            active['ticks'].append(dict(projected_source_acceleration=acceleration,wheels=wheels))
            active['speed_end']=math.hypot(*row['root_without_roads']['planar']['linear']['velocity'])
        before=row['root_without_roads'];prior_action=row['action']
    assert len(records)==13 and all(len(z['ticks'])==4 for z in records) and oracle_error<1e-8
    low=[z for z in records if max(z['rear_gas_start'])<.4];high=[z for z in records if min(z['rear_gas_start'])>.95]
    def group(rows):
        return dict(holds=len(rows),preceded_by_brake=sum(z['prior_brake']>0 for z in rows),mean_desired_acceleration=sum(z['desired_acceleration'] for z in rows)/len(rows),mean_realized_four_tick_acceleration=sum((z['speed_end']-z['speed_start'])/.08 for z in rows)/len(rows),mean_target_deficit=sum(z['target_deficit'] for z in rows)/len(rows),mean_first_tick_rear_gas=sum(sum(w['gas'] for w in z['ticks'][0]['wheels'][2:])/2 for z in rows)/len(rows),mean_final_tick_rear_gas=sum(sum(w['gas'] for w in z['ticks'][-1]['wheels'][2:])/2 for z in rows)/len(rows),mean_first_tick_rear_pre_engine_slip=sum(sum(w['pre_engine_longitudinal_slip'] for w in z['ticks'][0]['wheels'][2:])/2 for z in rows)/len(rows),mean_projected_source_acceleration=sum(sum(t['projected_source_acceleration'] for t in z['ticks'])/4 for z in rows)/len(rows))
    allw=[w for z in records for t in z['ticks'] for w in t['wheels']]
    out=dict(holds=13,raw_ticks=52,source_force_evaluations=evals,model_integrator_ticks=0,native_actions=0,native_resets=0,oracle_vector_error_max_N=oracle_error,engine_multipliers=sorted(set(z['engine_multiplier'] for z in records)),low_gas_start=group(low),near_full_gas_start=group(high),clipped_wheel_samples=sum(w['clipped'] for w in allw),time_in_affected_holds_s=1.04,share_of_520_model_finish_time=1.04/20.22,observed_whole_model_effect_s=.16,large_time_gain_established=False,decision='Proceed with one path-only spline smoothing hypothesis. 1.04s temporal occupancy is not recoverable time or an effect upper bound; satisfying short-term goals is not itself a faster-lap objective.',source_mechanism='Source first ramps rear gas by0.1, then omega gains dt*40000*engine*g/(1.6*(abs(omega)+5)); longitudinal force82*(omega_after*.54-v_forward), combined-friction clipped, then tyre impulse subtracts wheel omega. Low gas and prior braking suppress immediate drive; three near-full-gas states show ramp alone is insufficient explanation. Healthyengine/no clipping do not imply instantaneous target feasibility.',CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    assert out['CPU_s']<30 and out['wall_s']<45
    with (D/'source-hold-explanations-private.json').open('x') as f:json.dump(records,f,indent=2)
    (D/'source-hold-explanations-private.json').chmod(0o600)
    with (G/'retry/study521_analysis.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
