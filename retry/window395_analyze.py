"""Postprocess four bounded native windows; no new native/model/actor calls."""
import time
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save

def run(root):
    d=root/'stage395';assert not(d/'analysis.json').exists();p=read(d/'plan.json');b=read(d/'budget.json');assert not b['active_cases'];start,cpu=time.perf_counter(),time.process_time();cases=[];results=[];workers=[]
    for key in ['N1','O0']:
        cr=read(d/(key+'-case-result.json'));workers.append(cr);arms=[];windows={}
        for arm in ['O','C']:
            f=d/(key+'-'+arm)
            if not(f/'result.json').exists():continue
            r=read(f/'result.json');results.append(r);w=read(f/'window-private.json');windows[arm]=w
            if not w:arms.append(dict(arm=arm,result=r));continue
            samples=[s for z in w for s in z['raw_tire_samples']]
            def group(which):
                q=[s for s in samples if s['wheel'] in which];return dict(samples=len(q),clipped_wheel_ticks=sum(s['clipped'] for s in q),clipped_fraction=sum(s['clipped'] for s in q)/len(q),max_force_ratio=max(s['force_ratio'] for s in q),max_abs_lateral_slip_m_s=max(abs(s['lateral_slip_m_s']) for s in q),max_abs_longitudinal_slip_m_s=max(abs(s['longitudinal_slip_m_s']) for s in q))
            pre=w[0]['pre'];post=w[-1]['post'];a=dict(arm=arm,result=r,start_speed_m_s=pre['speed'],end_speed_m_s=post['speed'],min_speed_m_s=min(z[phase]['speed'] for z in w for phase in ['pre','post']),max_speed_m_s=max(z[phase]['speed'] for z in w for phase in ['pre','post']),max_abs_yaw_rate_rad_s=max(abs(z[phase]['yaw']) for z in w for phase in ['pre','post']),max_abs_body_lateral_velocity_m_s=max(abs(z[phase]['body_lateral_v']) for z in w for phase in ['pre_spatial','post_spatial']),max_abs_steer_rad=max(abs(z['command'][0]) for z in w),max_original_cursor_path_error_m=max(z['original_cursor_path_error_m'] for z in w),gas_positive_actions=sum(z['command'][1]>0 for z in w),brake_positive_actions=sum(z['command'][2]>0 for z in w),maximum_gas=max(z['command'][1] for z in w),maximum_brake=max(z['command'][2] for z in w),front=group([0,1]),rear=group([2,3]),max_positive_gas_request_lag=max(max(z['command'][1]-s['gas'],0) for z in w for s in z['raw_tire_samples'] if s['wheel']>=2),gas_lag_wheel_ticks=sum(z['command'][1]>s['gas'] for z in w for s in z['raw_tire_samples'] if s['wheel']>=2),max_positive_brake_request_lag=max(max(z['command'][2]-s['brake'],0) for z in w for s in z['raw_tire_samples']),collisions=sum(z['collision'] for z in w),max_damage=max(z['damage'] for z in w),road_loss_actions=sum(not all(n>0 for n in z[phase]['road_contacts']) for z in w for phase in ['pre','post']),meaningful_reverse_actions=sum(z[phase]['sigma']<-.1 or z[phase]['body_forward_v']<-.1 for z in w for phase in ['pre_spatial','post_spatial']),progress_by_window_action_m=[z['progress_since_fork_m'] for z in w],requested_brake_by_window_action=[z['command'][2] for z in w],requested_gas_by_window_action=[z['command'][1] for z in w],own_steering_by_window_action=[z['command'][0] for z in w]);arms.append(a)
        full=len(arms)==2 and all(a['result']['status']=='REGISTERED_12_ACTION_WINDOW_DONE' and a['result']['window_actions']==12 for a in arms);gain=arms[1]['result']['final_progress_m']-arms[0]['result']['final_progress_m'] if full else None;safe=full and all(a['result']['max_actual_path_error_m']<=3 and a['collisions']==0 and a['max_damage']==0 and a['road_loss_actions']==0 and a['meaningful_reverse_actions']==0 for a in arms)
        steering_changed=sum(x['command'][0]!=y['command'][0] for x,y in zip(windows.get('O',[]),windows.get('C',[])))
        cases.append(dict(case=key,arms=arms,full_registered_windows=full,final_C_minus_O_progress_m=gain,information_gate_passed=bool(safe and gain>=1),registered_safety_passed=bool(safe),own_state_steering_different_actions=steering_changed,case_error=cr['case_error'],unexecuted=cr['unexecuted']))
    assert sum(r['native'] for r in results)==b['actions'];end=max((d/(k+'-case-result.json')).stat().st_mtime for k in ['N1','O0'])
    cost=dict(new_wrapper_actions=b['actions'],new_environment_resets=b['resets'],raw_step_ticks=sum(r['raw_ticks'] for r in results),raw_reset_ticks=sum(r['reset_ticks'] for r in results),runner_episode_CPU_s=sum(r['runner_CPU_s'] for r in results),wholeworker_CPU_receipts_s=sum(w['wholeworker_CPU_s'] for w in workers),sum_episode_wall_s=sum(r['wall_s'] for r in results),receipt_wall_span_s=end-b['started_epoch'],unconfirmed_charged_native=sum(r['unconfirmed_charged_native'] for r in results),matched_original_actual_rows=sum(r['matched_original_rows'] for r in results),new_actor_calls=0,new_model_integration_ticks=0,new_learning_fits=0,new_paid_resources=0)
    report=dict(stage=395,cases=cases,cost=cost,all_information_gates_passed=all(c['information_gate_passed'] for c in cases),SafetyStop_exists=(d/'SafetyStop.json').exists(),analysis_CPU_s=time.process_time()-cpu,analysis_wall_s=time.perf_counter()-start,analysis_native=0,analysis_model=0,scope='Two knownTRAIN .96s ownstate windows;progress/safetygate only,no full-lap/generalization/296promotion')
    save(d/'analysis.json',report);print(__import__('json').dumps(report,ensure_ascii=False),flush=True)
if __name__=='__main__':run(Path(__import__('sys').argv[1]))
