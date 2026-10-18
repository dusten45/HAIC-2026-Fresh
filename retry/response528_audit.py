"""Read-only search certification and remaining profile occupancy audit."""
import json,math,hashlib,time
from pathlib import Path
import numpy as np
from retry.drive519_control import reference,drive,nominal
from retry.plan513_model import load_root
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response528-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/response528_contract.json').read_text())
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    x=json.loads((D/'cold-candidate-model-private.json').read_text());old=json.loads(Path('/workspace/haic-response527-private/cold-candidate-model-private.json').read_text());static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());path=json.loads((D/'frozen-paths-private.json').read_text())['candidate'];commands={z['index']:z for z in x['commands']};numeric=[z for z in x['commands'] if z['detail']['mode']!='HIGH' and z['index']>24];limits={k:dict(time_s=0.,mean_speed_sum=0.,force_sum=0.,wheel_samples=0) for k in ('launch','source_forward','backward80','top80','curvature_transition')};before=static['root'];s0=0.;nonmonotone=0;maxcalls=0;float32actions=0
    for z in x['trace']:
        a=commands[z['index']]['action'];r=z['root_without_roads'];v=math.hypot(*before['planar']['linear']['velocity']);s=(s0+z['progress'])/2;target,ff=reference(s,path);u=s%path['length'];i=next((i for i in range(len(path['ds'])) if path['arcs'][i+1]>=u),len(path['ds'])-1);kind='launch' if z['index']<=24 else 'source_forward' if abs(ff-drive(path['launch_squared'][i]))<1e-7 else 'backward80' if abs(ff+80)<1e-7 else 'top80' if abs(target-80)<1e-6 and abs(ff)<1e-8 else 'curvature_transition';row=limits[kind];row['time_s']+=.02;row['mean_speed_sum']+=v*.02;row['force_sum']+=sum(w['ratio'] for w in z['forces']);row['wheel_samples']+=4
        if z['raw']==1:
            state=dict(before);state['roads']=static['root']['roads'];root=load_root(state);high=nominal(root,path,s0);assert np.float32(a[0]).tobytes()==high[0].tobytes();assert not(a[1]>0 and a[2]>0) and all(float(np.float32(q))==q for q in a);float32actions+=1
        before=r;s0=z['progress']
    for z in numeric:
        d=z['detail'];final=d['reports'][-1];assert d['final_recertified'] and final['ok'] and final['model_ticks']==48 and final['peak']<=1.06 and final['max_reference_overspeed']<=4.85;assert d['numerical_calls']<=32
        assert any(t['ok'] for t in d['trials']);assert all(float(np.float32(t['u']))==t['u'] for t in d['trials']);nonmonotone+=d.get('coarse_nonmonotone',False);maxcalls=max(maxcalls,d['numerical_calls'])
    for row in limits.values():row['mean_speed_m_s']=row.pop('mean_speed_sum')/row['time_s'] if row['time_s'] else None;row['mean_force_ratio']=row.pop('force_sum')/row['wheel_samples'] if row['wheel_samples'] else None
    assert abs(sum(z['time_s'] for z in limits.values())-18)<1e-8
    out=dict(source_input_pins_verified=True,float32_mutually_exclusive_pedal_actions_verified=float32actions,steering_unchanged_for_current_state=True,numerical_selected_commands_final_fresh_certificates_verified=len(numeric),max_certification_calls_per_intervention=maxcalls,nonmonotone_coarse_cases=nonmonotone,nonmonotone_not_observed_is_not_monotonicity_proof=True,cold_model_528_finish_s=x['summary']['model_finish_episode_s'],cold_model_527_finish_s=old['summary']['model_finish_episode_s'],incremental_model_gain_vs527_s=old['summary']['model_finish_episode_s']-x['summary']['model_finish_episode_s'],profile_time_partition=limits,reference_path_length_m=path['length'],mean_speed_needed_for_11_5s_on_reference_length_m_s=path['length']/11.5,source_scalar_reference_clock_s=sum(2*d/(math.sqrt(path['launch_squared'][i])+math.sqrt(path['launch_squared'][i+1])) for i,d in enumerate(path['ds'])),clock_not_feasible_or_optimal_lower_bound=True,decision='Stoprepeatpedaldosefineadjustments:sharedstateimprovementaddsjust.10swholemodelvs527, .40vs525below.50gate. Nextstructuralquestionisfixedtop80 orpathlength/curvature; knownreference995m needs86.6m/saveragefor11.5s evenbeforelaunchcost. Currentreferenceoccupancyisnotcausalorarecoverablegainupperbound. No newcap/pathcandidateexecuted.',new_model_integrator_ticks=0,new_force_evaluations=0,native_actions=0,native_resets=0,research_remaining=24155,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    assert out['CPU_s']<60 and out['wall_s']<90
    with (G/'retry/response528_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
