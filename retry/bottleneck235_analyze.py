"""Read-only DEV diagnosis of the retained232 single-head policy, no rollout.

python -m retry.bottleneck235_analyze --private-root PRIVATE_ROOT \
  --output PRIVATE_OUTPUT_DIRECTORY
Only existing DEV records and repository physics text are read. No simulator,
teacher, predictor or policy actor is imported or invoked.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time
import numpy as np


def analyze(root,output):
    start,cpu=time.perf_counter(),time.process_time();inputs={}
    def read(path):
        inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        return json.loads(path.read_text())
    champion_before=hashlib.sha256((root/'current-champion.json').read_bytes()).hexdigest()
    config=read(root/'stage232/configuration.json')
    assert champion_before=='b17aef1cee0d4d5fb35763be7cd9ec8748a6e060d79b529ca477c1efba5948bc'
    jobplan=read(root/'stage234/plan.json');baseline=jobplan['arms']['A'];assert config==baseline
    case_ids={j['road']:j['case']['id'] for j in jobplan['jobs']}
    cases={};tracks={}
    for i in range(2):
        label='F'+str(i);scene=read(root/'stage221/evaluation/runs'/(case_ids[label]+'__C')/'track-diagnostic.json')
        track=np.asarray(scene['track'],float)[:,2:4];tracks[label]=track
        length=float(np.linalg.norm(np.roll(track,-1,axis=0)-track,axis=1).sum())
        cases[label]=dict(centerline_length_m=length,centerline_assumption_mean_speed_for_10s_m_s=length/10,
            centerline_at_policy_target45_seconds=length/45,
            length_scope='Closed storedDEV centerline, not shortest legal route or required actual travel distance.')
    f0=read(root/'stage232/smoke-outcome.json');cases['F0'].update(official_lap_s=f0['endpoint']['lap_time_ms']/1000,
        raw_step_ticks=f0['raw_step_ticks'],naive_wrapper_count_seconds=f0['native_actions']*.08,
        raw_wrapper_endpoint_seconds=f0['raw_step_ticks']/50,
        finish_vs_raw_endpoint_seconds=f0['raw_step_ticks']/50-f0['endpoint']['lap_time_ms']/1000,
        detailed_policy_telemetry_available=False,actual_distance_or_speed_or_pedal_partition=None,
        missing='232F0smoke retained endpoint/timing only. No actual trajectory/speed/commands; do not substitute234changedsteering or230LOO/221GT.',
        centerline_assumption_current_mean_speed_m_s=cases['F0']['centerline_length_m']/(f0['endpoint']['lap_time_ms']/1000))
    folder=root/'stage234/runs'/(case_ids['F1']+'__A');r=read(folder/'result.json');d=read(folder/'diagnostic.json');rows=d['actual_steps'];assert r['archive_sha256']==config['archive_sha256']
    initial_record=read(root/'stage229/F1/result.json');assert initial_record['initial']==r['initial']
    # Existing first-query snapshot is used solely for the measured reset hull.
    initial_query=read(root/'stage229/F1/queries-private.json')[0];assert initial_query['action']==1
    initial=initial_query['snapshot'];assert abs(initial['actual_time']-r['raw_reset_ticks']/50)<1e-9
    initial_position=np.asarray(initial['hull']['position'],float);initial_speed=float(np.linalg.norm(initial['hull']['velocity']))
    n=len(rows);assert n==r['charged_wrapper_actions']
    ticks=np.full(n,4);ticks[-1]=r['raw_step_ticks']-4*(n-1);assert 1<=ticks[-1]<=4
    ts=np.r_[0.,np.cumsum(ticks)/50];positions=np.vstack([initial_position,[x['position'] for x in rows]])
    speeds=np.r_[initial_speed,[x['speed_m_s'] for x in rows]]
    finish_s=r['lap_ms']/1000;finish_ticks=round(finish_s*50)
    assert abs((r['finish_time_s']-r['raw_reset_ticks']/50)*50-finish_ticks)<1e-7
    keep=np.flatnonzero(ts[1:]<=finish_s+1e-10)
    count=len(keep)
    if count<n:
        f=(finish_s-ts[count])/(ts[count+1]-ts[count])
        end_position=positions[count]+f*(positions[count+1]-positions[count]);end_speed=speeds[count]+f*(speeds[count+1]-speeds[count])
        pp=np.vstack([positions[:count+1],end_position]);vv=np.r_[speeds[:count+1],end_speed];tt=np.r_[ts[:count+1],finish_s]
    else:pp,vv,tt=positions,speeds,ts
    dt=np.diff(tt);commands=np.asarray([x['command'] for x in rows[:len(dt)]],float)
    distance=np.linalg.norm(np.diff(pp,axis=0),axis=1);trapezoid=(vv[:-1]+vv[1:])/2*dt;right=vv[1:]*dt;acc=np.diff(vv)/dt
    track=tracks['F1'];segments=np.roll(track,-1,axis=0)-track;headings=np.arctan2(segments[:,1],segments[:,0]);seglen=np.linalg.norm(segments,axis=1)
    geometry_curvature=[]
    for position in pp[1:]:
        fractions=np.clip(np.sum((position-track)*segments,axis=1)/(seglen**2),0,1)
        closest=track+fractions[:,None]*segments;j=int(np.argmin(np.linalg.norm(closest-position,axis=1)))
        ids=(np.arange(j-3,j+4))%len(track);angles=np.unwrap(headings[ids]);window_distance=float(seglen[ids[:-1]].sum())
        geometry_curvature.append(abs(float(angles[-1]-angles[0]))/window_distance)
    curvature=np.asarray(geometry_curvature);speed=(vv[:-1]+vv[1:])/2
    stationary=speed<=.001;curved=curvature>=1/80;slow=speed<.9*45
    masks={'stationary':stationary,'straight_low_speed_proxy':~stationary&~curved&slow,
        'curve_low_speed_proxy':~stationary&curved&slow,'other_moving':~stationary&~slow}
    assert np.all(np.sum(list(masks.values()),axis=0)==1)
    def time_s(mask):return float(dt[mask].sum())
    def stats(values,weights=dt):
        order=np.argsort(values);v=np.asarray(values)[order];w=np.asarray(weights)[order];c=np.cumsum(w)/sum(w)
        return dict(min=float(v[0]),p10=float(v[np.searchsorted(c,.1)]),median=float(v[np.searchsorted(c,.5)]),p90=float(v[np.searchsorted(c,.9)]),p95=float(v[np.searchsorted(c,.95)]),max=float(v[-1]),time_weighted_mean=float(np.average(values,weights=weights)))
    partitions={k:dict(seconds=time_s(mask),fraction_of_official_time=time_s(mask)/finish_s,
        sampled_path_m=float(distance[mask].sum()),mean_speed_m_s=float(np.average(speed[mask],weights=dt[mask])) if mask.any() else None,
        mean_gas=float(np.average(commands[mask,1],weights=dt[mask])) if mask.any() else None,
        mean_brake=float(np.average(commands[mask,2],weights=dt[mask])) if mask.any() else None,
        decelerating_seconds=time_s(mask&(acc<0)),significant_overlap_seconds=time_s(mask&(commands[:,1]>.05)&(commands[:,2]>.05))) for k,mask in masks.items()}
    total_distance=float(distance.sum());speed_integral=float(trapezoid.sum())
    overlap=(commands[:,1]>0)&(commands[:,2]>0);significant=(commands[:,1]>.05)&(commands[:,2]>.05)
    # Noncausal constant45 reference for the same sampled path; not a bound.
    reference45=total_distance/45;excess={k:time_s(mask)-float(distance[mask].sum())/45 for k,mask in masks.items()}
    cases['F1'].update(official_lap_s=finish_s,detailed_policy_telemetry_available=True,
        recorded_wrapper_steps=n,raw_step_ticks=r['raw_step_ticks'],raw_reset_ticks=r['raw_reset_ticks'],official_finish_ticks=finish_ticks,
        naive_wrapper_count_seconds=n*.08,raw_wrapper_endpoint_seconds=ts[-1],raw_endpoint_minus_finish_s=float(ts[-1]-finish_s),
        finish_time_tick_consistency=True,weighted_partition_seconds=float(dt.sum()),
        sampled_actual_path_chord_m=total_distance,trapezoid_speed_integral_m=speed_integral,right_endpoint_speed_integral_m=float(right.sum()),
        trapezoid_minus_chord_m=speed_integral-total_distance,full_postfinish_sample_chord_m=float(np.linalg.norm(np.diff(positions,axis=0),axis=1).sum()),
        path_distance_scope='4rawtick position chords, last3rawtick interval linearly trimmed to officialcenterline tick. Approximate actualpath; no perrawtick trajectories, not exact arc length or shortestroute.',
        sampled_actual_path_required_mean_speed_for10s_m_s=total_distance/10,
        current_sampled_path_mean_speed_m_s=total_distance/finish_s,required_current_speed_factor=finish_s/10,
        speed_m_s=stats(speed),speed_distribution_scope='Timeweighted means of two recordedendpoint speeds perwrapper interval.',recorded_endpoint_speed_max_m_s=float(speeds.max()),gas=stats(commands[:,1]),brake=stats(commands[:,2]),
        positive_gas_brake_overlap_seconds=time_s(overlap),positive_overlap_fraction=time_s(overlap)/finish_s,
        both_pedals_over005_seconds=time_s(significant),both_pedals_over005_fraction=time_s(significant)/finish_s,
        classifications=dict(curve_abs_geometry_curvature_at_least=.0125,curvature_window='neareststoredGT segment, headingchange across±3segments /arc distance',low_speed_less_than=40.5,stationary_at_most=.001,causal_scope='Descriptive proxies. Straightlow speed is not proven avoidable accelerationloss; curvelow speed is not proven necessarybraking. GTgeometrydiagnosis only.'),
        time_partitions=partitions,all_curved_seconds=time_s(curved),curved_decelerating_seconds=time_s(curved&(acc<0)),all_decelerating_seconds=time_s(acc<0),
        same_sampled_path_constant45_reference_s=reference45,excess_over_reference45_s=finish_s-reference45,
        excess_reference45_by_partition_s=excess,reference_scope='Same measuredpath atconstant45,no acceleration/curvature/collision/transient; counterfactual accounting only, not physicsbound.',
        collision_steps=[x['step'] for x in rows if x['collision']],final_damage=r['damage'])
    repository=Path(__file__).resolve().parents[1]
    source_hashes={name:hashlib.sha256((repository/name).read_bytes()).hexdigest() for name in ['core/vendor/car_dynamics.py','core/vendor/car_racing.py','core/finish_line.py','env_wrapper.py','damage.py']}
    physics=dict(engine_power=40000.,wheel_moment_of_inertia=1.6,friction_limit_per_wheel_road=400.,grass_multiplier=.6,
        gas='Rearwheels only; +0.1 maxincrease perrawtick, decreases immediately. Omega drive dt*40000*engine_multiplier*gas/1.6/(abs(omega)+5). This engine expression is not a fixedspeedclamp.',
        brake='Allwheels; brake>=.9 locksomega to0, otherwise perrawtick omega subtracts min(absomega,15*brake), applied afterengine. Positivegas/brake oppose eachother, but cancellationcost notidentifiable fromcommand/speedlogs alone.',
        tire_force='Perwheel longitudinal+lateral vector capped at400*road_friction*grip; grassbaseline240*grip. Coupled friction budget, not direct velocitybound.',
        steering='Frontwheel joint angle±.4; motorspeed<=3rad/s*steering_multiplier, maxmotortorque64.8. Policy rawclip±.4 and0.8/0.2smoothing are additional control settings.',
        damage='Grip=max(.6,1-.5damage), engine/steering=max(.8,1-.25damage). F1finaldamage.6 -> grip.7, engine/steering.85.',
        rigorous_global_speed_bound_or_route_time_lower_bound_proved=False,
        conclusion='No global speedupperbound or shortestlegalpath lowerbound derived here. CenterlineL/45 is only a policy-reference calculation; empiricalmaxspeed is not physicalupperbound. No claim that10seconds is impossible.',source_sha256=source_hashes)
    recommendation=dict(one_next_falsification='If separately authorized, test one legal output-only mutual-exclusion rule: when frozenhead gas>0, set returnedbrake=0; otherwise keepbrake. Preservesteering,features,head,normandnominalmemory. ChooseknownDEV F1 withexistingbaseline, one fixedcandidate, no threshold tuning.',
        rationale='Simultaneouspedals onthecurrentactualF1trajectory can oppose wheelspin inofficialsource; quantify straightlow-speed andcurve overlap before changing capacity orpreview again. Notproof ofavoidabletime, and removingbrake mayincreasecurve/contactfailure.',
        what_would_refute='Lostofficialcompletion or commoncompletedtime notimproved under the same fixedconditions; damage remainsdiagnostic. No universalperformanceclaim or newminimumgain.',
        proposed_experiment_executed=False,new_candidate_or_model_created=False)
    result=dict(stage=235,status='READ_ONLY_CURRENT232_DEV_TIME_DIAGNOSIS',cases=cases,physics=physics,next_single_test_basis=recommendation,
        current_champion_changed=False,long_preview234_line_terminated=True,H24_line_terminated=True,
        HOLDOUT_opened=False,SEALED_opened=False,native_actions=0,model_queries=0,new_training_data=0)
    assert hashlib.sha256((root/'current-champion.json').read_bytes()).hexdigest()==champion_before
    cost=dict(stage=235,read_and_analysis_wall_s=time.perf_counter()-start,read_and_analysis_CPU_s=time.process_time()-cpu,
        native_actions=0,model_queries=0,policy_actor_calls=0,new_paid_resources=0,research_remaining=443,final_reserved_actions=84000,final_reserve_used=0,
        scope='Timed script reads/analysis. Preliminaryinteractiveinspection wall/CPU notseparatelycaptured; no fullturncost claim.')
    result['cost']=cost
    for name,data in [('analysis.json',result),('input-receipt.json',dict(input_sha256=inputs,champion_sha256=champion_before))]:
        p=output/name
        with p.open('x') as f:json.dump(data,f,indent=2,allow_nan=False);f.write('\n')
        p.chmod(0o600)
    print(json.dumps(dict(F0_centerline_m=cases['F0']['centerline_length_m'],F1=cases['F1'],cost=cost)))


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--private-root',type=Path,required=True);a.add_argument('--output',type=Path,required=True)
    p=a.parse_args();analyze(p.private_root,p.output)
