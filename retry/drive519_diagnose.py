"""Saved controller saturation accounting, no integrated trajectory or policy trial."""
import json,math,time
from pathlib import Path
from retry.drive519_control import path_for
from retry.lap518_control import project,reference
from retry.plan513_model import load_root
from retry.envelope500 import REAR,BRAKE
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response519-private')

def run():
    c=dict(purpose='Explain reference clock vsphysicalmodelgap fromsavedholdcommands',CPU_s=30,wall_s=45,model_integrator_ticks=0,native_actions=0,native_resets=0,parameter_trials=0)
    with (D/'saved-saturation-contract.json').open('x') as f:json.dump(c,f,indent=2)
    t=time.perf_counter();cpu=time.process_time();static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());results=[]
    for variant,file in [('baseline',Path('/workspace/haic-response518-private/cold-100-continued-model-private.json')),('source_drive',D/'cold-source_drive-model-private.json')]:
        path=path_for(static,variant);root=load_root(static['root']);progress=project(root.center,path)['s'];trace=json.loads(file.read_text())['trace'];metrics=dict(gas_s=0.,mapped_command_at_REAR_s=0.,fullgas_s=0.,positive_feedforward_gas_s=0.,positive_ff_mapped_saturation_s=0.,positive_ff_speed_deficit_integral=0.,positive_ff_acceleration_integral=0.,positive_ff_gas_integral=0.);control=None
        for row in trace:
            if row['raw']==1:
                q=project(root.center,path,progress);v=math.hypot(*root.planar.linear.velocity);target,ff=reference(q['s'],path);sigma=sum(root.planar.linear.velocity[j]*q['tangent'][j] for j in range(2));raw=ff*sigma/max(target,1.)+2*(target-v);control=dict(ff=ff,raw=raw,deficit=target-v)
            before_speed=math.hypot(*root.planar.linear.velocity);state=dict(row['root_without_roads']);state['roads']=static['root']['roads'];root=load_root(state);progress=row['progress'];speed=math.hypot(*root.planar.linear.velocity);a=row['action']
            if row['index']<=24:continue
            metrics['gas_s']+=.02*(a[1]>0);metrics['fullgas_s']+=.02*(a[1]==1.);metrics['mapped_command_at_REAR_s']+=.02*(a[1]>0 and control['raw']>=REAR)
            if a[1]>0 and control['ff']>1e-8:
                metrics['positive_feedforward_gas_s']+=.02;metrics['positive_ff_mapped_saturation_s']+=.02*(control['raw']>=REAR);metrics['positive_ff_speed_deficit_integral']+=.02*control['deficit'];metrics['positive_ff_acceleration_integral']+=speed-before_speed;metrics['positive_ff_gas_integral']+=.02*a[1]
        T=metrics['positive_feedforward_gas_s'];metrics['positive_ff_mean_reference_deficit_m_s']=metrics.pop('positive_ff_speed_deficit_integral')/T;metrics['positive_ff_mean_realized_speed_acceleration_m_s2']=metrics.pop('positive_ff_acceleration_integral')/T;metrics['positive_ff_mean_gas']=metrics.pop('positive_ff_gas_integral')/T
        results.append(dict(variant=variant,metrics=metrics))
    result=dict(arms=results,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-t,model_integrator_ticks=0,native_actions=0,native_resets=0,interpretation='Conventionalaccel-command ceiling saturation isnot tire clipping/fullgas. Source-driveprofile usesupto35 butsamepedalmapclampsat35,leavinglessfeedbackheadroom. Savedcomparison ismechanistic evidence,notseparatecausalablation.')
    assert result['CPU_s']<30 and result['wall_s']<45
    (G/'retry/drive519_diagnosis.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':run()
