"""Frozen predictions and budget closure for twelve matched one-step endpoints."""
import argparse
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

from retry.dynamics325_fit import motor_baseline,plain
from retry.hud248_features import decode
from retry.intervention327_collect import command,digest,verify
from retry.path271_run import read,save,sha


def estimate(paths,x):
    out=[]
    for path in paths:
        model=np.load(path);out.append(x[:3]+np.r_[(x-model['mean'])/model['scale'],1.]@model['beta'])
    return np.mean(out,axis=0)


def summary(errors):
    e=np.array(errors)
    if not len(e):return dict(samples=0)
    return plain(dict(samples=len(e),MAE=abs(e).mean(0),RMSE=np.sqrt((e*e).mean(0)),bias=e.mean(0),max_abs=abs(e).max(0)))


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage327';p=verify(D)
    o=read(D/'outcome-private.json');results=o['results'];assert not (D/'cost.json').exists()
    assert o['all_planned'] and len(results)==12
    assert all(r['reached_endpoint'] and not r['technical_error'] for r in results),'Missing endpoint: do not invent pair or rerun; report actualcost separately.'
    assert sha(G/'retry/intervention327_collect.py')==read(D/'opening.json')['code_sha256']
    start,cpu=time.perf_counter(),time.process_time()
    spec=importlib.util.spec_from_file_location('frozen_speed_decoder327',R/'stage306/zero-replay/O0/package/retry/hud_feedback.py');decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    training=np.load(R/'stage325/heldout-predictions-private.npz');allrows=[];pairs=[];private={};input_checks=[]
    for r in results:
        assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
        road,arm=r['road'],r['arm'];F=D/'runs'/(road+'_'+arm);z=np.load(F/'raw-pixels-actions-private.npz');boundary=read(F/'boundary-private.json');post=read(F/'post-private.json')
        observations=z['observations'];assert observations.shape==(66,4,84,84) and z['actions'].shape==(65,3)
        assert np.array_equal(observations[1:,:3],observations[:-1,1:]);assert np.array_equal(z['actions'][:64],z['base_actions'][:64])
        assert abs(z['actual_times'][65]-z['actual_times'][64]-.08)<1e-9
        assert digest(observations[64].tobytes())==boundary['pre_pixel_sha256'] and digest(observations[65].tobytes())==post['pixel_sha256']
        action=z['actions'][64];base=z['base_actions'][64];assert np.array_equal(action,command(base,arm))
        state=[];fallback=[]
        for image,f in [(observations[64,-1],boundary['features']),(observations[65,-1],post['features'])]:
            speed=decoder.decode_feedback_speed(image,f[3]);hud=decode(image);state.append(np.array([speed,hud[5],hud[4]]))
            signature=np.rint(image[74:83,11:13]*255).astype(np.uint8).tobytes();fallback.append(signature not in decoder.TEMPLATES)
        s0,s1=state;x=np.r_[s0,action]
        model_paths=[p['models'][road]] if road in p['models'] else list(p['models'].values())
        predictions=dict(persistence=s0,residual_ridge=estimate(model_paths,x),motor_kinematic=motor_baseline(s0[None,:],action[None,:])[0])
        fit_rows=training['roads']!=road if road in p['models'] else np.ones(len(training['x']),bool)
        low=training['x'][fit_rows,3:].min(0);high=training['x'][fit_rows,3:].max(0)
        requested=float(base[0])+(.08 if arm=='steer_plus' else -.08 if arm=='steer_minus' else 0.)
        row=dict(road=road,arm=arm,action_step=65,model_mode='same_road_excluded325' if road in p['models'] else 'fixed_sixmodel_mean_secondary',
                 actual_action=action,baseline_action=base,action_difference=action-base,steering_requested=requested,
                 steering_clipped=bool(arm.startswith('steer') and (requested<-.4 or requested>.4)),
                 current_HUD=s0,actual_next_HUD=s1,predicted_next_HUD=predictions,next_errors={a:v-s1 for a,v in predictions.items()},
                 collision=post['collision'],collision_flag_present=post['collision_flag_present'],official_terminal=r['official_terminal'],
                 protocol_stop=r['protocol_stop'],outside_TRAIN_marginal_action_by_channel=(action<low)|(action>high),
                 frozen_speed_fallback_pre_post=fallback,interval_s=float(z['actual_times'][65]-z['actual_times'][64]))
        allrows.append(row);private[road+'_'+arm]=dict(row=row,boundary=boundary,zpath=str(F/'raw-pixels-actions-private.npz'))
    for road in p['roads']:
        base=private[road+'_baseline'];basepixels=np.load(base['zpath'])['observations']
        for arm in p['arms'][1:]:
            chosen=private[road+'_'+arm];pixels=np.load(chosen['zpath'])['observations']
            assert np.array_equal(basepixels[:65],pixels[:65])
            for key in ['prefix_sha256','pre_pixel_sha256','state_before','state_after_baseline_act','features','base_action','actual_time']:
                assert base['boundary'][key]==chosen['boundary'][key]
            first,second=base['row'],chosen['row'];observed=second['actual_next_HUD']-first['actual_next_HUD']
            pred={a:second['predicted_next_HUD'][a]-first['predicted_next_HUD'][a] for a in first['predicted_next_HUD']}
            pairs.append(dict(road=road,arm=arm,observed_response=observed,predicted_response=pred,response_errors={a:v-observed for a,v in pred.items()},
                              sign_match={a:np.sign(v)==np.sign(observed) for a,v in pred.items()},baseline_collision=first['collision'],intervention_collision=second['collision'],
                              steering_clipped=second['steering_clipped'],action_difference=second['action_difference'],pre_pixels_prefix_and_policy_exact=True))
        input_checks.append(dict(road=road,paired_arms=4,raw_prefix_observations_equal=65,prefix_action_count=64,
                                 full_policy_object_hash_and_controller_tracker_history_exact=True,base_action65_exact=True))
    metrics={}
    for label,roads in [('primary_O0_O2',['O0','O2']),('secondary_N0',['N0'])]:
        selected=[r for r in allrows if r['road'] in roads];pp=[r for r in pairs if r['road'] in roads]
        observed=np.array([r['observed_response'] for r in pp]);models=['persistence','residual_ridge','motor_kinematic']
        absolute={a:summary([r['next_errors'][a] for r in selected]) for a in models}
        response={a:summary([r['response_errors'][a] for r in pp]) for a in models}
        signs={a:dict(correct=[int(sum(r['sign_match'][a][j] for r in pp if r['observed_response'][j]!=0)) for j in range(3)],
                      observed_nonzero_denominators=np.sum(observed!=0,axis=0).tolist(),observed_zero_denominators=np.sum(observed==0,axis=0).tolist()) for a in models}
        response_better=all(np.all(np.array(response['residual_ridge']['MAE'])<np.array(response[a]['MAE'])) for a in ['persistence','motor_kinematic'])
        contact_metrics={}
        for state in [False,True]:
            rr=[r for r in selected if r['collision'] is state]
            contact_metrics['contact' if state else 'no_contact']={a:summary([r['next_errors'][a] for r in rr]) for a in models}
        metrics[label]=dict(absolute_next_errors=absolute,baseline_relative_response_errors=response,nonzero_response_signs=signs,
                            contact_absolute_errors=contact_metrics,all_three_response_MAE_better_than_both_baselines=bool(response_better))
    b=read(D/'budget.json');assert b['actions']==sum(r['native_actions'] for r in results)==780
    prior=R/'project-effective-budget-v332.json';v=read(prior);assert v['research_remaining']==780
    cost=dict(stage=327,new_wrapper_actions=b['actions'],native_cap=780,new_native_runs=12,raw_step_ticks=sum(r['raw_step_ticks'] for r in results),raw_reset_ticks=sum(r['raw_reset_ticks'] for r in results),
              actual_simulated_interval_per_run_s=5.2,collection_wall_s=o['wall_s'],runner_CPU_s=sum(r['runner_CPU_s'] for r in results),actor_CPU_s=sum(r['actor_CPU_s'] for r in results),
              analysis_wall_s=time.perf_counter()-start,analysis_CPU_s=time.process_time()-cpu,new_source_physics_ticks=0,new_fits=0,new_PPO=0,new_paid_resources=0,
              additional_research=385,actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],research_remaining=v['research_remaining']-b['actions'],
              final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=v['B_operating_cap'])
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    public=dict(stage=327,index_resolution=p['index_resolution'],prefix_actions=64,action_step=65,model_rule=p['model_rule'],intervention=p['intervention'],gate=p['gate'],
                state_names=read(R/'stage325/plan.json')['state_names'],preflight=read(D/'preflight.json'),pairing_verification=input_checks,
                endpoint_rows=allrows,paired_responses=pairs,metrics=metrics,cost=cost,official_terminal_endpoints=sum(r['official_terminal'] for r in results),
                successful_protocol_stops=sum(r['protocol_stop'] for r in results),technical_errors=0,missing_endpoints=0,
                decision='Keep diagnostic evidence only; no MPC/controller/full-episode validation or promotion regardless of one-step response results.',
                limitations=['Three knownTRAIN states atfixed64prefix,12ownnativeprefixes,not12independentprestates.',
                             'HUDquantization canhidephysicalresponses;exactzeroresponse isnotphysicalzero;contactsampletiny.',
                             'N0hasno325LOROmodel;fixedsixfoldmean isseparatesecondaryzero-fitdefinition.',
                             'Oneactionprotocolend isnotDNF,notfull-lap performance;noglobalcollisionorplanningguarantee.'],
                champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False)
    save(D/'analysis-summary-private.json',plain(public));save(G/'retry/intervention327_result.json',plain(public));save(D/'cost.json',cost)
    v.update(version=333,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),
             actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=0,stage327_new_wrapper_actions=780)
    assert not (R/'project-effective-budget-v333.json').exists();save(R/'project-effective-budget-v333.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==327 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(plain(dict(metrics=metrics,cost=cost,pairs=pairs))),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True)
    close(parser.parse_args().private_root.resolve())
