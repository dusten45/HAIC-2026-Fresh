"""Read-only raw/charge/own-state verification and first-force-failure diagnosis."""
import hashlib,json,math,time
from pathlib import Path
import numpy as np
from retry.capacity522_control import path_for
from retry.drive519_control import project,nominal,steering
from retry.plan513_model import load_root
from retry.brake502_response import wheel_response
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response522-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/capacity522_contract.json').read_text());r=json.loads((G/'retry/capacity522_native_result.json').read_text());m=json.loads((G/'retry/capacity522_model_result.json').read_text());u=json.loads((G/'retry/capacity522_units.json').read_text())
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    adm=json.loads((D/'native-admission-private.json').read_text());assert adm['model_result_sha256']==hashlib.sha256((G/'retry/capacity522_model_result.json').read_bytes()).hexdigest()
    charges=sorted(D.glob('charge-*.json'));assert len(charges)==r['counts']['actions']
    for i,p in enumerate(charges,1):
        z=json.loads(p.read_text());assert p.name==f'charge-{i:03d}.json' and z['attempted_actual_actions']==i and z['research_remaining']==24938-i and z['reserve_used']==0
    raw=[json.loads(p.read_text()) for p in sorted(D.glob('raw-*.json'))];assert len(raw)==r['counts']['raw_completed']==r['counts']['raw_attempts']
    assert sum(z['phase']=='reset' for z in raw)==102
    assert sum(z['phase']=='action' for z in raw)==4*len(charges)
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());all_commands=0;prefix=[]
    arms=json.loads((D/'native-full-records-private.json').read_text())
    for arm in arms:
        variant=arm['budget'];path=path_for(static,variant);progress=project(static['root']['center'],path)['s'];ownprefix=[]
        for record in arm['rows']:
            i=record['index'];data=json.loads((D/f'action-{variant}-{i:03d}.json').read_text());state=data['before_root_without_roads'];state['roads']=static['root']['roads'];root=load_root(state)
            expected=np.array([steering(root,path,progress),.32,0.],np.float32) if i<=24 else nominal(root,path,progress)
            assert np.array_equal(expected,np.asarray(record['action'],np.float32));all_commands+=1
            after=data['after_root_without_roads'];progress=project(after['center'],path,progress)['s']
            if i<=24:ownprefix.append(dict(action=record['action'],obs_sha256=record['obs_sha256']))
        prefix.append(ownprefix)
    assert all_commands==297 and prefix[0]==prefix[1] and len(prefix[0])==24
    bad=[(i+1,z) for i,z in enumerate(raw) if z['errors']];assert bad and all(z['errors']==['DYNAMICS_GUARD'] for _,z in bad)
    first_i,first=bad[0];assert first['action']==41
    fraction=r['arms'][1]['force_groups']['running']['clipped']/r['arms'][1]['force_groups']['running']['samples'];assert fraction<.10
    assert max(z['ratio'] for z in first['forces'])>1.25
    assert r['arms'][0]['official_finish'] and not r['arms'][1]['official_finish'] and r['official_finish_gain_s'] is None
    cold=json.loads((D/'cold-capacity-model-private.json').read_text());modelrow=next(z for z in cold['trace'] if z['index']==41 and z['raw']==2);prior=cold['trace'][cold['trace'].index(modelrow)-1]['root_without_roads']
    actualstate=dict(planar=first['before_planar']);actualstate['planar']['linear']=first['before']
    compared=[];force_evals=0
    for label,state in [('actual',actualstate),('cold_model_same_hold',prior)]:
        p=state['planar'];linear=p['linear'];action=json.loads((D/'action-capacity-041.json').read_text())['record']['action'] if label=='actual' else modelrow['action'];rows=[]
        from retry.brake502_response import Wheel
        for i,x in enumerate(linear['wheels']):
            w=Wheel(**dict(x,offset=tuple(x['offset'])));gas=w.gas+min(.1,float(action[1])-w.gas) if i>=2 else w.gas
            after,force,detail=wheel_response(w,linear['velocity'],gas,float(action[2]),linear['engine_multiplier']);force_evals+=1
            forward=(-math.sin(w.heading),math.cos(w.heading));side=(forward[1],-forward[0]);vel=[linear['velocity'][j]+w.offset[j] for j in range(2)];vf=sum(forward[j]*vel[j] for j in range(2));vs=sum(side[j]*vel[j] for j in range(2));long=82*(detail['omega_braked']*.54-vf);lat=-82*vs
            rows.append(dict(wheel=i,raw_longitudinal_force_N=long,raw_lateral_force_N=lat,raw_ratio=math.hypot(long,lat)/w.friction,postclip_vector=force))
        compared.append(dict(label=label,wheels=rows,postclip_net_force_acceleration_m_s2=math.hypot(*(sum(z['postclip_vector'][j] for z in rows) for j in range(2)))/linear['mass']))
    assert force_evals==8
    # Detailed wheel comparisons stay private. Public fields are first-failure diagnostics.
    with (D/'first-force-failure-private.json').open('x') as f:json.dump(compared,f,indent=2)
    (D/'first-force-failure-private.json').chmod(0o600)
    front=compared[0]['wheels'][1];model=compared[1]['wheels'][1]
    out=dict(status='NATIVE_SAFETY_FAILURE_NO_CANDIDATE_LAP_CLAIM',source_input_and_admission_hashes_verified=True,all_own_state_commands_verified=all_commands,paired24action_observation_prefix_exact=True,contiguous_precharges=len(charges),native_resets=2,reset_raw_ticks=102,action_raw_ticks=1188,total_native_raw_ticks=1290,closed_worlds=r['counts']['closed'],baseline_official_finish_s=r['arms'][0]['official_finish_episode_s'],candidate_official_finish=False,candidate_stopped_after_hold=41,first_violation=dict(global_raw_index=first_i,episode_s=first['time']-1.02,raw_in_hold=2,predicate='RUNNING_FORCE_PEAK',raw_combined_force_ratio=front['raw_ratio'],threshold=1.25,raw_longitudinal_force_N=front['raw_longitudinal_force_N'],raw_lateral_force_N=front['raw_lateral_force_N'],raw_force_magnitude_N=400*front['raw_ratio'],cold_model_same_hold_ratio=model['raw_ratio'],postclip_net_force_acceleration_m_s2=compared[0]['postclip_net_force_acceleration_m_s2'],candidate_budget_m_s2=u['candidate_lateral_budget_m_s2'],failed_raw_rows=3,extra_raw_ticks_completing_already_issued_hold=2,extra_wrapper_calls_after_first_failure=0),running_clip_fraction=fraction,only_failure_class='DYNAMICS_GUARD forcepeak; not prediction/sourceoracle/COM/road/path/overspeed/damage/collision',diagnostic_force_evaluations=8,diagnostic_model_integrator_ticks=0,interpretation='Aggregate70%capacity does not constrain individual-wheel demand. At first violation net postclip COM force norm/m151.49<153.38 while one frontwheel raw demand505.46N>400N. Predominantly lateral demand499.65N, longitudinal76.43N. Cold closedloop model underpredicts thatwheel ratio1.168vs1.264 despite small onehold kinematic errors. Comparison is between differing closedloop states at samehold, not an isolated causal ablation or proof of one solver defect. No threshold change, continuation, or candidate native finish estimate.',research_remaining=24641,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    assert out['CPU_s']<10 and out['wall_s']<15
    with (G/'retry/capacity522_verification.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
