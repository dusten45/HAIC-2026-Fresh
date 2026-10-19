"""Stored571-only active reference diagnosis. No source integration."""
import json,math,time
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
from retry.clip561_core import atomic_write
from retry.handoff562_model import reference
from retry.path569_design import sha

G=Path(__file__).resolve().parents[1];OLD=Path('/workspace/haic-response571-private');D=Path('/workspace/haic-response572-private');rd=lambda p:json.loads(p.read_text());SCALE=np.tile([.003,.03],34)

def top(vector,n=6,multiplier=1.):
    return [dict(hold=133+int(j)//2,control='steer' if j%2==0 else 'pedal',per_normalized_unit=float(vector[j]*multiplier)) for j in np.argsort(-abs(vector))[:n]]

def main():
    D.mkdir(mode=0o700,exist_ok=False);cpu,wall=time.process_time(),time.perf_counter();final=rd(OLD/'proposal-4-0-diagnostic-private.json');center=rd(OLD/'proposal-3-0-diagnostic-private.json');saved=rd(OLD/'linear-5-private.json');J=np.asarray(saved['linear']['J']);T=np.asarray(saved['linear']['T']);steps=np.asarray(saved['steps']);path=rd(Path('/workspace/haic-response551-private/frozen-paths-private.json'))['candidate'];rows=final['rows'];targets=sorted(rows,key=lambda r:-r['reference_overspeed'])[:3];needed={r['global_raw_after'] for r in targets};observed={}
    with open(OLD/'raw-journal-private.jsonl') as f:
        for line in f:
            r=json.loads(line)
            if r['kind']=='AFTER_TICK':
                current_label=r['context']['label'];raw=r['context']['global_raw']+1
                current_speed=math.hypot(*r['root']['planar']['linear']['velocity']) if current_label.startswith('FD-5-') and raw in needed else None
            elif r['kind']=='RAW_VERDICT' and current_label.startswith('FD-5-') and raw in needed:
                j=int(current_label.split('-')[-1]);observed[j,raw]=dict(speed=current_speed,progress=r['progress'])
    actual_dx=np.asarray(final['x'])-center['x'];global_step=float(max(abs(actual_dx/SCALE)));details=[];A=[];b=[]
    descent=-T*SCALE;descent/=np.linalg.norm(descent)
    for row in targets:
        raw=row['global_raw_after'];offset=raw-529;k=offset*10+2;n=2*(offset//4+1);gradient=J[k]*SCALE;baseline=center['rows'][offset];v0=math.hypot(*baseline['root_without_roads']['planar']['linear']['velocity']);ref0=reference(baseline['progress'],path)[0];speed=[];profile=[]
        for j in range(68):
            ev=observed[j,raw];speed.append((ev['speed']-v0)/steps[j]);profile.append((reference(ev['progress'],path)[0]-ref0)/steps[j])
        speed=np.asarray(speed)*SCALE;profile=np.asarray(profile)*SCALE;assert np.max(abs(profile-speed-gradient))<1e-7
        futurezero=bool(np.all(gradient[n:]==0));assert futurezero
        details.append(dict(raw=raw,hold=row['index'],raw_in_hold=row['raw'],reference_overspeed=row['reference_overspeed'],actual_slack=4.85-row['reference_overspeed'],causal_control_count=n,future_controls_zero_stored_derivative=futurezero,dominant_slack_sensitivities=top(gradient),dominant_speed_sensitivities=top(speed),dominant_profile_sensitivities=top(profile),speed_profile_decomposition_error_max=float(max(abs(profile-speed-gradient))),slack_rate_on_unconstrained_L2_time_descent=float(gradient@descent),slack_gradient_norm=float(np.linalg.norm(gradient)),last_accepted_global_step=global_step,last_accepted_causal_prefix_step=float(max(abs((actual_dx/SCALE)[:n])))))
        A.append(-gradient);b.append(4.85-row['reference_overspeed'])
    bounds=[]
    for j,v in enumerate(final['x']):
        lo,hi=(-float(np.float32(.4)),float(np.float32(.4))) if j%2==0 else (-1.,1.);bounds.append((max(-.05,(lo-v)/SCALE[j]),min(.05,(hi-v)/SCALE[j])))
    conditional=linprog(T*SCALE,A_ub=A,b_ub=b,bounds=bounds,method='highs');late_bounds=[(0.,0.)]*6+bounds[6:];late=linprog(T*SCALE,A_ub=A,b_ub=b,bounds=late_bounds,method='highs')
    out=dict(stage='saved-data-only diagnosis before572source',same_center_FD_available=False,stored_FD_center='571proposal3-0,one acceptedstep before finalproposal4-0',center_offset_normalized_inf=global_step,actual_active_reference=details,time_sensitivities_ms_per_normalized_unit=top(T*SCALE,12,1000.),early_control_time_sensitivities_ms=[dict(hold=133+j//2,control='steer' if j%2==0 else 'pedal',slope=float(T[j]*SCALE[j]*1000)) for j in range(6)],conditional_linear_time_response=dict(reference3_only_gain_ms=-1000*float(conditional.fun) if conditional.success else None,first3holds_fixed_reference3_only_gain_ms=-1000*float(late.fun) if late.success else None,scope='Approximate stored previous-center gradients with current final zero-order slacks. Omits force/footprint/path/rank/error margins and is NOT a source candidate or prediction of feasible gain.'),interpretation='The reference is an unchanged design condition,not a physical optimum bound. Near-zero slack identifies a potential local restriction;causal gradients and any later LPdual are conditional local information only. Fresh68FD at the exact final571point are required before optimization;no off-centerFD reuse as an exact model.',source_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,input_sha256={str(p):sha(p) for p in [OLD/'linear-5-private.json',OLD/'proposal-3-0-diagnostic-private.json',OLD/'proposal-4-0-diagnostic-private.json',OLD/'raw-journal-private.jsonl']})
    atomic_write(G/'retry/reference572_diagnosis.json',out);print(json.dumps(out,indent=2))

if __name__=='__main__':main()
