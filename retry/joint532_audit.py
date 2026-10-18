"""Read-only endpoint fidelity and explicit longitudinal residual audit."""
import hashlib,json,time
from pathlib import Path
import numpy as np
from retry.joint532_problem import Problem,Q
from retry.line530_control import rebuild,choose
from retry.response528_control import choose as old_choose
from retry.drive519_control import drive
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response532-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/joint532_contract.json').read_text());design=json.loads((G/'retry/joint532_design.json').read_text());static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());history=json.loads(Path('/workspace/haic-response531-private/design-history-private.json').read_text());solution=json.loads((D/'design-solution-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());problem=Problem(static,history['restored_points']);x=np.array(solution['x']);state,q,w=problem.state(x);q=q*Q;w=w*Q;ds=state['ds'];constraints=problem.constraints(x);p=rebuild(problem.points(x),static);speedp=np.sqrt(np.maximum(q,0));speedw=np.sqrt(np.maximum(w,0));regenp=np.sqrt(p['periodic_squared']);regenw=np.sqrt(p['launch_squared']);excessp=float(max(0.,max(speedp-regenp)));excessw=float(max(0.,max(speedw-regenw)))
    def longitudinal(cur,next):
        delta=(next-cur)/(2*ds);forward=np.array([drive(max(0.,a)) for a in cur]);return dict(max_forward_accel_excess_m_s2=float(max(0.,max(delta-forward))),max_backward80_excess_m_s2=float(max(0.,max(-delta-80))),min_speed_m_s=float(np.sqrt(max(0.,min(cur)))))
    sourcepins=all(hashlib.sha256((G/z).read_bytes()).hexdigest()==h for z,h in c['source_sha256'].items());privatepins=all(hashlib.sha256(Path(z).read_bytes()).hexdigest()==h for z,h in c['private_inputs_sha256'].items());assert sourcepins and privatepins and choose is old_choose
    assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==design['frozen_paths_sha256'];assert paths['baseline']==json.loads(Path('/workspace/haic-response528-private/frozen-paths-private.json').read_text())['candidate']
    out=dict(source_pins_verified=sourcepins,private_input_pins_verified=privatepins,controller_function_identity=True,max_profile_rebuild_error=max(float(np.max(abs(np.array(paths['candidate'][key])-np.array(p[key])))) for key in ('points','ds','curvature','arcs','periodic_squared','launch_squared')),max_normalized_violation=max(0.,-float(constraints.min())),periodic_longitudinal=longitudinal(q,np.roll(q,-1)),launch_longitudinal=longitudinal(w[:-1],w[1:]),periodic_design_speed_excess_m_s=excessp,launch_design_speed_excess_m_s=excessw,design_speed_conservative_or_equal=max(excessp,excessw)<=.001,design_clock_s=design['design_speed_clock_s'],regenerated_clock_s=design['regenerated528_profile_clock_s'],clock_difference_design_minus_regenerated_s=design['design_speed_clock_s']-design['regenerated528_profile_clock_s'],model_started=(D/'MODEL_STARTED.json').exists(),native_started=(D/'NATIVE_STARTED.json').exists(),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,model_ticks=0,force_evaluations=0,native_actions=0,scope='Read-only explicitlongitudinal/profilefidelitycheck,notactualphysics/noactual528claim. Designqneverdeployed;regeneratedprofilealonegate.')
    with (G/'retry/joint532_audit.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
