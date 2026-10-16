"""Aggregate completed394 prefix forks; no native/model/actor calls."""
import datetime,json,time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha

def run(root):
    d=root/'stage394';assert not(d/'analysis.json').exists();p=read(d/'plan.json');b=read(d/'budget.json');assert b['active_cases']==[];cases=[];all_results=[];start,cpu=time.perf_counter(),time.process_time()
    for key in ['N1','O0']:
        case=read(d/(key+'-case-result.json'));arms=[]
        for arm in p['jobs'][key]['arms']:
            f=d/(key+'-'+arm)
            if not(f/'result.json').exists():continue
            r=read(f/'result.json');all_results.append(r)
            if r['status']!='REGISTERED_ONE_ACTION_DONE':arms.append(dict(arm=arm,result=r));continue
            z=read(f/'fork-private.json');before=z['pre'];post=z['post'];angle=before['angle'];fwd=np.array([-np.sin(angle),np.cos(angle)]);lat=np.array([np.cos(angle),np.sin(angle)]);samples=z['raw_tire_samples'];request=z['command'];rear=[x for x in samples if x['wheel']>=2]
            def group(indices):
                q=[x for x in samples if x['wheel'] in indices]
                return dict(samples=len(q),clipped_fraction=sum(x['clipped'] for x in q)/len(q),max_raw_force_ratio=max(x['force_ratio'] for x in q),max_abs_lateral_slip_m_s=max(abs(x['lateral_slip_m_s']) for x in q),max_abs_longitudinal_slip_m_s=max(abs(x['longitudinal_slip_m_s']) for x in q),grass_fraction=sum(x['grass'] for x in q)/len(q))
            gas_by_tick=[[x['gas'] for x in rear if x['raw_tick']==t] for t in range(1,5)];brake_by_tick=[[x['brake'] for x in samples if x['raw_tick']==t] for t in range(1,5)]
            a=dict(arm=arm,result=r,requested_steering_rad=request[0],requested_gas=request[1],requested_brake=request[2],pre_speed_m_s=before['speed'],post_speed_m_s=post['speed'],pre_forward_velocity_m_s=float(np.asarray(before['vel'])@fwd),post_forward_velocity_m_s=float(np.asarray(post['vel'])@fwd),post_lateral_velocity_m_s=float(np.asarray(post['vel'])@lat),pre_yaw_rate_rad_s=before['yaw'],post_yaw_rate_rad_s=post['yaw'],pre_rear_gas=before['wheel_gas'][2:4],rear_gas_each_rawtick=gas_by_tick,brake_each_rawtick=brake_by_tick,maximum_positive_gas_request_lag=max(max(request[1]-x['gas'],0) for x in rear),all_rear_gas_equal_request_from_first_tick=all(x['gas']==request[1] for x in rear),front=group([0,1]),rear=group([2,3]),collision=z['collision'],damage=z['damage'],post_wheel_road_contacts=post['road_contacts'],response=read(f/'response.json'))
            arms.append(a)
        cases.append(dict(case=key,arms=arms,case_error=case['case_error'],unexecuted=case['unexecuted'],wholeworker_CPU_s=case['wholeworker_CPU_s']))
    assert sum(r['native'] for r in all_results)==b['actions'];assert len(all_results)==5 and b['actions']==985 and b['resets']==5
    receipt_end=max((d/(k+'-case-result.json')).stat().st_mtime for k in ['N1','O0']);cost=dict(new_wrapper_actions=b['actions'],new_environment_resets=b['resets'],raw_step_ticks=sum(r['raw_ticks'] for r in all_results),raw_reset_ticks=sum(r['reset_ticks'] for r in all_results),runner_episode_CPU_s=sum(r['runner_CPU_s'] for r in all_results),wholeworker_CPU_receipts_s=sum(c['wholeworker_CPU_s'] for c in cases),sum_episode_wall_s=sum(r['wall_s'] for r in all_results),receipt_wall_span_s=receipt_end-b['started_epoch'],receipt_wall_basis='Hostfilemtimeoflastcasereceipt minus sharedtime.time start; notallgit/reportwall',unconfirmed_charged_native=sum(r['unconfirmed_charged_native'] for r in all_results),matched_original_rows=sum(r['matched_original_rows'] for r in all_results),new_actor_calls=0,new_model_integration_ticks=0,new_learning_fits=0,new_paid_resources=0)
    report=dict(stage=394,cases=cases,cost=cost,N1_local_gate_passed=next(a['response']['N1_local_response_passed'] for c in cases if c['case']=='N1' for a in c['arms'] if a['arm']=='C'),all_changed_arms_pass_local_safety_gate=all(a['response']['safe_local_registered_gate'] for c in cases for a in c['arms'] if a['arm']!='O'),safety_stop_exists=(d/'SafetyStop.json').exists(),analysis_CPU_s=time.process_time()-cpu,analysis_wall_s=time.perf_counter()-start,analysis_new_native=0,analysis_new_model=0,scope='Only3changedoneactionresponses vs2originalcontrols; no lap/sustainedrecovery/nextcurvebraking/wholepolicy orpopulationclaim')
    save(d/'analysis.json',report);print(json.dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':run(Path(__import__('sys').argv[1]))
