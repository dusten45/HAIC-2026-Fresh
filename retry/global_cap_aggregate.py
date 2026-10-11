"""Audit one cap40 DEV outcome against a qualified historical cap28 stream.

Saved observations/actions/masks and current-input arithmetic only. Every
native outcome remains reported if verification fails; no simulator or model.
"""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import time

import numpy as np

from retry.global_cap_cached import cap_shadow
from retry.gentle_curve_patch import gate
from retry.road_keep_saved_records import verify_records


def audit(directory, case_id, cap):
    directory=Path(directory)
    result=json.loads((directory/case_id/'result.json').read_text())
    assert result==json.loads((directory/case_id/'student-result.json').read_text())
    verified=verify_records(directory,case_id)
    rows=[json.loads(line) for line in (directory/(case_id+'-trace.jsonl')).read_text().splitlines()]
    assert rows and len(rows)==result['charged_wrapper_actions']==verified['actions']
    finish=rows[-1]['info']['finish_time_s'] if result['completed'] else rows[-1]['truth_after']['time']
    dt=np.asarray([max(0.,min(r['truth_after']['time'],finish)-r['truth_before']['time']) for r in rows])
    if result['completed']:assert abs(dt.sum()-result['official_lap_ms']/1000)<1e-8
    labels=[]; shadows=[]; targets=[]; subtypes=Counter(); fallback=0.
    with np.load(directory/(case_id+'-pixels-actions.npz'),allow_pickle=False) as saved:
        frames=saved['frames'].copy()
    for index,(row,seconds) in enumerate(zip(rows,dt)):
        response=row['policy_response'];t=response['route_telemetry'];c=response['cap_diagnostic'];d=response['curve_diagnostic']
        action=np.asarray(row['action'],np.float32)
        integral=float((frames[index].astype(np.float32)/255)[74:83,9:14].sum())
        speed=max(0.,11.4142485314592*integral-6.545558315185489)
        assert speed==t['speed_estimate']
        if t['actual_fallback_called']:
            assert d is None and t['fallback_far_x'] is None
            assert np.array_equal(action,np.asarray([response['previous_steer_after'],0,.25],np.float32))
            labels.append('fallback');shadows.append(None);targets.append(math.nan);fallback+=seconds
            continue
        hazards=t['memory_hazards_after_tracker'];lookahead=float(np.clip(4+.35*speed,6,14))
        near=any(y>0 and np.hypot(x,y)<=lookahead+2.6+radius for x,y,radius,_age in hazards)
        eligible=[list(h[:3]) for h in hazards if h[3]==0 and h[1]>0 and np.hypot(h[0],h[1])<=lookahead+2.6+h[2]]
        clearances=[max(0.,float(np.hypot(x,y))-radius-2.6) for x,y,radius in eligible]
        assert eligible==c['eligible_hazards'] and clearances==c['radial_clearances']
        assert c['cap_input_scope']=='age_zero'
        x,y=t['controller_target'];k=2*x/max(x*x+y*y,1e-6)
        steer=.8*float(np.clip(np.arctan(3.24*k),-.4,.4))+.2*t['previous_steer_before']
        assert steer==response['previous_steer_after']==d['existing_smoothed_steer']
        assert d['coefficient']==7 and d['near']==near and d['gate']==gate(k,steer,near)
        assert k==d['curvature']
        curve=math.sqrt((5 if near else 7)/(abs(k)+.003))
        distance=min((max(4.,math.sqrt(10*q)) for q in clearances),default=math.inf)
        target=min(cap,curve,distance)
        assert abs(c['inherited_target']-min(cap,curve))<1e-10
        assert abs(c['distance_cap']-min(cap,distance))<1e-10
        assert abs(target-c['effective_target'])<1e-10
        assert d['baseline_final_target']==d['applied_final_target']==c['effective_target']
        predicted=np.asarray([steer,np.clip(.08*(target-speed),0,.5),np.clip(.04*(speed-target),0,.5)],np.float32)
        assert np.array_equal(predicted,action) and np.array_equal(action,np.asarray(d['baseline_action'],np.float32))
        assert d['target_delta']==0 and d['steering_unchanged']
        limits={f'global{cap}':float(cap),'curvature':curve,'age0distance':distance}
        active=[name for name,value in limits.items() if abs(value-target)<1e-10]
        label='+'.join(active);labels.append(label)
        if 'curvature' in active:subtypes['safe5' if near else 'fast7']+=seconds
        shadow=cap_shadow(curve,distance,speed)
        assert abs(shadow['new' if cap==40 else 'old']-target)<1e-10
        shadows.append(shadow);targets.append(target)
    dwell=Counter();transitions=Counter();segments=[]
    for index,(label,seconds) in enumerate(zip(labels,dt)):
        if not seconds:continue
        row=rows[index];dwell[label]+=seconds
        if not segments or label!=segments[-1]['limit']:
            if segments:transitions[segments[-1]['limit']+' -> '+label]+=1
            segments.append({'limit':label,'start_step':row['step'],'end_step':row['step'],
                'start_lap_s':row['truth_before']['time']-rows[0]['truth_before']['time'],
                'end_lap_s':row['truth_before']['time']+seconds-rows[0]['truth_before']['time'],
                'seconds':float(seconds),'progress_before':row['truth_before']['unique_tiles'],
                'progress_after':row['truth_after']['unique_tiles']})
        else:
            segment=segments[-1];segment.update(end_step=row['step'],end_lap_s=row['truth_before']['time']+seconds-rows[0]['truth_before']['time'],
                seconds=segment['seconds']+seconds,progress_after=row['truth_after']['unique_tiles'])
    assert abs(sum(dwell.values())-dt.sum())<1e-8
    exposure=Counter();delta_sum=throttle_sum=brake_sum=0.;delta_max=0.;throttle_max=brake_reduction=0.;groups=Counter()
    for shadow,seconds in zip(shadows,dt):
        if shadow is None:continue
        groups[shadow['group']]+=seconds
        if shadow['delta']>1e-10:
            exposure['target_raised_s']+=seconds
            delta_sum+=shadow['delta']*seconds;delta_max=max(delta_max,shadow['delta'])
            throttle_sum+=shadow['pedal_delta'][0]*seconds;brake_sum+=shadow['pedal_delta'][1]*seconds
            throttle_max=max(throttle_max,shadow['pedal_delta'][0]);brake_reduction=max(brake_reduction,-shadow['pedal_delta'][1])
            exposure['pedal_changed_s' if shadow['changed'] else 'raised_but_pedals_same_s']+=seconds
            if not shadow['changed']:
                exposure['throttle_saturated_both_s' if shadow['old_pedals'][0]==.5 else 'other_equal_s']+=seconds
    raised=exposure['target_raised_s']
    exposure.update(target_delta_max_m_s=delta_max,throttle_delta_max=throttle_max,brake_reduction_max=brake_reduction)
    for key,value in [('target_delta_mean_raised_m_s',delta_sum),('throttle_delta_mean_raised',throttle_sum),('brake_delta_mean_raised',brake_sum)]:
        exposure[key]=value/raised if raised else None
    actions=np.asarray([r['action'] for r in rows]);fraction=dt/np.asarray([r['truth_after']['time']-r['truth_before']['time'] for r in rows])
    actual=np.asarray([r['truth_before']['speed_m_s']+(r['truth_after']['speed_m_s']-r['truth_before']['speed_m_s'])*f/2 for r,f in zip(rows,fraction)])
    target_arr=np.asarray(targets);valid=~np.isnan(target_arr)
    metrics={'elapsed_s':float(dt.sum()),'sampled_chord_m':sum(math.dist(r['truth_before']['position'],r['truth_after']['position'])*f for r,f in zip(rows,fraction)),
        'actual_speed_mean_m_s':float(np.dot(actual,dt)/dt.sum()),
        'target_speed_mean_nonfallback_m_s':float(np.dot(target_arr[valid],dt[valid])/dt[valid].sum()) if dt[valid].sum() else None,
        'throttle_mean':float(np.dot(actions[:,1],dt)/dt.sum()),'brake_mean':float(np.dot(actions[:,2],dt)/dt.sum()),
        'brake_on_s':float(dt[actions[:,2]>0].sum()),'throttle_saturated_s':float(dt[actions[:,1]==.5].sum()),'fallback_s':float(fallback)}
    return {'verification_pass':True,'record_verification':verified,'fixed_formula_float32_actions_exact':True,
        'metrics':metrics,'actual_binding_dwell_s':dict(dwell),'actual_curvature_subtype_dwell_s':dict(subtypes),
        'binding_transition_counts':dict(transitions),'binding_segments':segments,
        'own_input_global28_vs40':{**dict(exposure),'constraint_groups_s':dict(groups),'not_causal_lap_savings':True}},rows


def analyze(directory):
    directory=Path(directory);plan=json.loads((directory/'plan.json').read_text());historical=plan['historical_baseline']
    baseline_directory=Path(historical['directory']);candidate_id=plan['cases'][0]['id']
    results=[];traces=[];errors=[]
    for source,case_id,cap in [(baseline_directory,historical['case_id'],28),(directory,candidate_id,40)]:
        native=json.loads((source/case_id/'result.json').read_text())
        item={key:native.get(key) for key in ('status','completed','official_lap_ms','damage','unique_tiles','total_tiles','charged_wrapper_actions',
            'successful_wrapper_steps','raw_step_ticks','raw_reset_ticks','wall_s','sum_sim_step_wall_s','actor_CPU_s','peak_actor_RSS_MiB','max_act_including_IPC_ms','failure_type','error')}
        item.update(global_cap=cap,historical_only=cap==28,new_episode_count=int(cap==40),verification_pass=False)
        try:
            metrics,rows=audit(source,case_id,cap);item.update(metrics);traces.append(rows)
        except Exception as error:
            item['verification_error']=type(error).__name__+': '+str(error);errors.append(item['verification_error']);traces.append(None)
        results.append(item)
    baseline,candidate=results
    initial_same=False
    try:
        before=json.loads((baseline_directory/historical['case_id']/'started.json').read_text())
        after=json.loads((directory/candidate_id/'started.json').read_text())
        initial_same=all(before[key]==after[key] for key in ('initial','initial_observation_sha256','geometry_sha256','obstacles_sha256'))
    except Exception as error:
        errors.append('initial_receipts: '+type(error).__name__+': '+str(error))
    ledger=json.loads((directory/'budget.json').read_text())
    budget_pass=ledger['actions']==candidate['charged_wrapper_actions'] and ledger['actions']<=2000 and ledger['stages']=={candidate_id:ledger['actions']}
    preflight=json.loads((directory/'preflight.json').read_text())
    qualified=preflight['historical_baseline_comparable'] and preflight['cached_baseline_reproduction_pass']
    verified=not errors and initial_same and budget_pass and qualified
    common=verified and baseline['completed'] and candidate['completed']
    pair={'historical_baseline_reused':True,'baseline_episode_rerun':False,'same_initial_receipts':initial_same,
        'both_records_verified':verified,'both_completed_verified':bool(common),
        'common_completed_lap_delta_ms':candidate['official_lap_ms']-baseline['official_lap_ms'] if common else None,
        'native_completion_lost_verified':verified and baseline['completed'] and candidate['status']=='DNF',
        'damage_delta':candidate['damage']-baseline['damage'] if verified else None,'damage_separate_warning':True}
    if all(t is not None for t in traces):
        first=next((i for i,(b,c) in enumerate(zip(*traces)) if b['action']!=c['action']),None)
        if first is not None:
            b,c=traces[0][first],traces[1][first]
            assert all(x['action']==y['action'] and x['observation_sha256_before']==y['observation_sha256_before'] and x['truth_before']==y['truth_before'] for x,y in zip(traces[0][:first],traces[1][:first]))
            pair['first_action_difference']={'step':first+1,'same_pre_observation':b['observation_sha256_before']==c['observation_sha256_before'],
                'same_pre_truth':b['truth_before']==c['truth_before'],'baseline_action':b['action'],'candidate_action':c['action'],
                'target28':b['policy_response']['curve_diagnostic']['applied_final_target'],
                'target40':c['policy_response']['curve_diagnostic']['applied_final_target']}
    return {'stage':95,'results':results,'pair':pair,'verification_errors':errors,'all_required_evidence_verified':bool(verified),
        'new_wrapper_actions':ledger['actions'],'budget_ledger_pass':budget_pass,'new_environment_episodes':1,'baseline_episode_rerun':False,
        'champion_promotion':False,'HOLDOUT_details_or_SEALED_opened':False,'analysis_environment_policy_model_renderer_calls':0,
        'interpretation':'Historical qualified baseline and one new known DEV candidate; no repeatability or transfer claim. Own-input shadows are immediate controls, not causal lap decomposition.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',required=True,type=Path)
    directory=parser.parse_args().directory;start=time.perf_counter();report=analyze(directory);report['analysis_wall_s']=time.perf_counter()-start
    (directory/'comparison.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'new_actions':report['new_wrapper_actions'],'pair':report['pair'],'verification_errors':report['verification_errors']}))


if __name__=='__main__':main()
