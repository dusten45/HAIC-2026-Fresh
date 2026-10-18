"""Saved reference force accounting only: no new integrated trajectory or policy."""
import hashlib,json,math,time
from dataclasses import replace
from pathlib import Path
from retry.plan513_model import load_root
from retry.brake502_response import wheel_response,STIFFNESS,RADIUS
from retry.corner515_control import project
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response515-private')

def run():
    c=dict(purpose='Saved model reference tyre force usage; no policy variant, no new trajectory',maximum_wheel_evaluations=2000,CPU_s=20,wall_s=30,native_actions=0,native_resets=0)
    with (D/'saved-force-audit-contract.json').open('x') as f:json.dump(c,f,indent=2)
    t=time.perf_counter();cpu=time.process_time();static=json.loads((D/'collected-map-state-private.json').read_text());path=json.loads((D/'frozen-curve-reference-private.json').read_text());results=[];evaluations=0
    for label,start in [('exact_reset',static['root']),('observed_trigger_stress',json.loads(Path('/workspace/haic-response512-private/trigger-scalar-private.json').read_text())['root'])]:
        root=load_root(start);trace=json.loads((D/(label+'-reference-model-private.json')).read_text())['trace'];stats={phase:dict(ticks=0,brake_ticks=0,gas_ticks=0,clipped_wheels=0,wheel_samples=0,peak_force_ratio=0.,sum_force_ratio=0.,sum_speed=0.) for phase in ('entry','corner','exit')}
        for row in trace:
            s=project(root.center,path)['s'];phase='entry' if path['measurement_begin']<=s<path['corner_begin'] else 'corner' if path['corner_begin']<=s<path['corner_end'] else 'exit' if path['corner_end']<=s<=path['measurement_end'] else None
            if phase is not None:
                z=stats[phase];a=row['action'];z['ticks']+=1;z['brake_ticks']+=a[2]>0;z['gas_ticks']+=a[1]>0;z['sum_speed']+=math.hypot(*root.planar.linear.velocity)
                for i,w in enumerate(root.planar.linear.wheels):
                    g=w.gas+min(.1,a[1]-w.gas) if i>=2 else w.gas
                    after,force,detail=wheel_response(w,root.planar.linear.velocity,g,a[2],root.planar.linear.engine_multiplier);evaluations+=1
                    forward=(-math.sin(w.heading),math.cos(w.heading));side=(forward[1],-forward[0]);v=tuple(root.planar.linear.velocity[j]+w.offset[j] for j in range(2));vf=sum(forward[j]*v[j] for j in range(2));vs=sum(side[j]*v[j] for j in range(2))
                    ratio=math.hypot(STIFFNESS*(detail['omega_braked']*RADIUS-vf),STIFFNESS*vs)/w.friction
                    z['wheel_samples']+=1;z['clipped_wheels']+=ratio>1.;z['peak_force_ratio']=max(z['peak_force_ratio'],ratio);z['sum_force_ratio']+=ratio
            state=dict(row['root_without_roads']);state['roads']=static['root']['roads'];root=load_root(state)
        aggregate={phase:dict(sample_time_s=z['ticks']*.02,braking_s=z['brake_ticks']*.02,gas_s=z['gas_ticks']*.02,clipped_wheels=z['clipped_wheels'],wheel_samples=z['wheel_samples'],peak_force_ratio=z['peak_force_ratio'],mean_force_ratio=z['sum_force_ratio']/z['wheel_samples'] if z['wheel_samples'] else None,mean_speed_m_s=z['sum_speed']/z['ticks'] if z['ticks'] else None) for phase,z in stats.items()}
        results.append(dict(start=label,phases=aggregate))
    result=dict(reference_model_force_audit=results,wheel_force_evaluations=evaluations,new_integrated_trajectories=0,new_native_actions=0,new_native_resets=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,scope='Predicted source-order wheel force accounting on saved nominal model states, not actual native force measurements or a capacity certificate.')
    assert evaluations<=2000 and result['CPU_s']<20 and result['wall_s']<30
    with (G/'retry/corner515_force_audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':run()
