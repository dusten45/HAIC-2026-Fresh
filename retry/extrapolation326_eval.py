"""Frozen HUD dynamics on actual cached interventions, with no new fit or simulation."""
import argparse
import datetime
import hashlib
import importlib.util
import json
import time
from pathlib import Path

import numpy as np

from retry.dynamics325_fit import motor_baseline,plain
from retry.hud248_features import decode
from retry.path271_run import read,save,sha


def error_metrics(error,weights,mask):
    e=error[mask];w=weights[mask]
    if not len(e):return dict(rows=0)
    w=w/w.sum();result=dict(rows=len(e),RMSE=np.sqrt(w@(e*e)),MAE=w@abs(e),bias=w@e,max_abs=abs(e).max(0))
    for name,p in [('p95_abs',.95),('p99_abs',.99)]:
        result[name]=[]
        for k in range(3):
            order=np.argsort(abs(e[:,k]),kind='stable');idx=min(np.searchsorted(np.cumsum(w[order]),p),len(order)-1)
            result[name].append(float(abs(e[order[idx],k])))
    return plain(result)


def predict(paths,x):
    predictions=[]
    for path in paths:
        m=np.load(path);predictions.append(x[:,:3]+np.c_[(x-m['mean'])/m['scale'],np.ones(len(x))]@m['beta'])
    return np.mean(predictions,axis=0)


def run(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage326';p=read(D/'plan.json')
    assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    assert not (D/'opening.json').exists()
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00'))
    save(D/'code-receipt.json',dict(script_sha256=sha(Path(__file__))))
    save(D/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    start,cpu=time.perf_counter(),time.process_time();training=np.load(R/'stage325/heldout-predictions-private.npz')
    spec=importlib.util.spec_from_file_location('frozen_speed_decoder326',R/'stage306/zero-replay/O0/package/retry/hud_feedback.py');decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
    data={};provenance=[]
    for case in p['cases']:
        assert time.perf_counter()-start<p['max_wall_s'];F=Path(case['path']);z=np.load(F/case['pixel_file']);result=read(F/'result.json')
        if case['stage']==291:
            pixels=(z['pixels'].astype(np.float64)/255).astype(np.float32)
            rows=[json.loads(s) for s in (F/case['trace_file']).read_text().splitlines()]
            actions=np.array([r['action'] for r in rows],np.float32);posttimes=np.array([r['time_s'] for r in rows]);pretimes=np.r_[0.,posttimes[:-1]]
            damage=np.array([r['damage'] for r in rows]);updates=damage>np.r_[0.,damage[:-1]]
            contacts=np.full(len(rows),-1,int);features=z['features'][:,:16]
        else:
            pixels=z['observations'];rows=read(F/case['trace_file']);actions=z['actions'];features=z['features']
            posttimes=np.array([r['truth']['time'] for r in rows]);pretimes=np.r_[result['reset_ticks']/50,posttimes[:-1]]
            contacts=np.array([int(r['collision']) for r in rows]);damage=np.array([r['truth']['damage'] for r in rows]);updates=damage>np.r_[0.,damage[:-1]]
            assert np.array_equal(actions,np.array([r['executed'] for r in rows],np.float32))
        n=len(pixels);assert len(actions)==len(rows)==n and len(features)==n
        assert np.array_equal(pixels[1:,:3],pixels[:-1,1:])
        assert hashlib.sha256(pixels[0].tobytes()).hexdigest()==case['initial_sha']
        assert abs(posttimes[:-1]-pretimes[:-1]-.08).max()<1e-9
        state=[];fallback=0
        for image,f in zip(pixels[:,-1],features):
            speed=decoder.decode_feedback_speed(image,float(f[3]));hud=decode(image)
            state.append([speed,hud[5],hud[4]])
            signature=np.rint(image[74:83,11:13]*255).astype(np.uint8).tobytes();fallback+=signature not in decoder.TEMPLATES
        state=np.array(state);assert np.isfinite(state).all();x=np.c_[state[:-1],actions[:-1]]
        pred=dict(persistence=state[:-1],residual_ridge=predict(case['model_paths'],x),motor_kinematic=motor_baseline(state[:-1],actions[:-1]))
        fit_rows=training['roads']!=case['road'] if case['road'] in p['models'] else np.ones(len(training['x']),bool)
        low=training['x'][fit_rows,3:].min(0);high=training['x'][fit_rows,3:].max(0);outside=(actions[:-1]<low)|(actions[:-1]>high)
        key=case['road']+'_'+case['arm'];data[key]=dict(case=case,x=x,state=state,pred=pred,target=state[1:],contact=contacts[:-1],damage_update=updates[:-1],initial_pixels=pixels[0].copy(),actions=actions,
                                                    result=result,weights=np.ones(n-1)/(n-1))
        provenance.append(dict(road=case['road'],arm=case['arm'],stage=case['stage'],model_mode=case['mode'],rows=n,eligible_transitions=n-1,missing_last_endpoint=1,
                               terminal_completed=result.get('completed'),actual_DNF=result.get('actual_DNF'),prefix_censored=result.get('censored'),
                               direct_contact_transitions=int(sum(contacts[:-1]==1)),direct_noncontact_transitions=int(sum(contacts[:-1]==0)),unknown_contact_transitions=int(sum(contacts[:-1]<0)),
                               damage_update_transitions=int(sum(updates[:-1])),speed_fallback_frames=int(fallback),maximum_interval_error_s=float(abs(posttimes[:-1]-pretimes[:-1]-.08).max()),
                               outside_training_marginal_action_range=int(sum(outside.any(1))),outside_by_channel=outside.sum(0),observed_action_min=actions[:-1].min(0),observed_action_max=actions[:-1].max(0)))
        print(json.dumps(plain(provenance[-1])),flush=True)
    aggregate={};pertrajectory={}
    for label,selected in [('primary_O0_O2',[v for v in data.values() if v['case']['road']!='S1']),('secondary_S1',[v for v in data.values() if v['case']['road']=='S1'])]:
        allroads=set(v['case']['road'] for v in selected);weights=[];contacts=[];updates=[];errors={arm:[] for arm in ['persistence','residual_ridge','motor_kinematic']}
        for v in selected:
            road=v['case']['road'];count=sum(z['case']['road']==road for z in selected)
            weights.extend(v['weights']/len(allroads)/count);contacts.extend(v['contact']);updates.extend(v['damage_update'])
            key=road+'_'+v['case']['arm'];pertrajectory[key]={a:error_metrics(pred-v['target'],v['weights'],np.ones(len(pred),bool)) for a,pred in v['pred'].items()}
            for arm in errors:errors[arm].extend(v['pred'][arm]-v['target'])
        contacts=np.array(contacts);updates=np.array(updates);weights=np.array(weights)
        masks=dict(all=np.ones(len(weights),bool),direct_contact=contacts==1,direct_noncontact=contacts==0,unknown_contact=contacts<0,
                   damage_update_proxy=updates,no_damage_update_proxy=~updates)
        aggregate[label]={name:{arm:error_metrics(np.array(e),weights,mask) for arm,e in errors.items()} for name,mask in masks.items()}
    pairs=[]
    for road,base_arm,intervention_arms in [('O0','baseline240',['frozen290']),('O2','baseline240',['frozen290']),('S1','saved_baseline',['gas_restored','brake_restored','saved_residual'])]:
        base=data[road+'_'+base_arm]
        for arm in intervention_arms:
            candidate=data[road+'_'+arm];assert np.array_equal(base['initial_pixels'],candidate['initial_pixels']) and np.array_equal(base['state'][0],candidate['state'][0])
            observed=candidate['target'][0]-base['target'][0]
            predictions={a:candidate['pred'][a][0]-base['pred'][a][0] for a in base['pred']}
            pairs.append(dict(road=road,baseline=base_arm,intervention=arm,action_step=1,action_difference=candidate['actions'][0]-base['actions'][0],
                              full_pre_pixels_exact=True,previous_actions=0,observed_response=observed,
                              predicted_response=predictions,response_error={a:v-observed for a,v in predictions.items()},
                              response_sign_match={a:np.sign(v)==np.sign(observed) for a,v in predictions.items()},
                              direct_contact_baseline=int(base['contact'][0]),direct_contact_intervention=int(candidate['contact'][0]),
                              damage_update_baseline=bool(base['damage_update'][0]),damage_update_intervention=bool(candidate['damage_update'][0])))
    save(D/'pairs-private.json',plain(pairs))
    for key,v in data.items():
        q=D/(key+'-predictions-private.npz');np.savez(q,x=v['x'],actual_next=v['target'],**v['pred']);q.chmod(0o600)
    premise={group:bool(np.all(np.array(metrics['all']['residual_ridge']['RMSE'])<np.array(metrics['all']['persistence']['RMSE']))) for group,metrics in aggregate.items()}
    pair_summary={arm:dict(MAE=np.mean([abs(row['response_error'][arm]) for row in pairs],axis=0),RMSE=np.sqrt(np.mean([row['response_error'][arm]**2 for row in pairs],axis=0)),
                           sign_correct_by_channel=np.sum([row['response_sign_match'][arm] for row in pairs],axis=0),pairs=len(pairs)) for arm in ['persistence','residual_ridge','motor_kinematic']}
    for q,h in p['input_hashes'].items():assert sha(q)==h,q
    budget=read(R/'project-effective-budget-v331.json');assert budget['research_remaining']==395
    cost=dict(stage=326,new_wrapper_actions=0,new_native=0,new_source_physics_ticks=0,new_fits=0,new_actor_calls=0,new_PPO=0,new_paid_resources=0,
              analysis_wall_s=time.perf_counter()-start,analysis_CPU_s=time.process_time()-cpu,research_remaining=395,final_reserved_actions=84000,
              actual_cumulative_wrapper_actions=budget['actual_cumulative_wrapper_actions'],B_operating_cap=budget['B_operating_cap'])
    public=dict(stage=326,model_rule=p['model_rule'],state_recipe=p['state_recipe'],sampling=p['samples'],paired_scope=p['paired'],
                latest319_322_pixel_missing_runs=sum(a['runs'] for a in p['availability']),latest319_322_pixel_available_runs=0,
                earlier_pixel_trajectories_found=16,selected_pixel_trajectories=8,unselected291_newroad_trajectories=8,
                available_transitions=sum(r['eligible_transitions'] for r in provenance),missing_last_endpoints=8,provenance=provenance,
                state_names=read(R/'stage325/plan.json')['state_names'],absolute_errors=aggregate,per_trajectory_errors=pertrajectory,
                paired_action_responses=pairs,paired_response_summary=pair_summary,all_three_RMSE_vs_persistence=premise,cost=cost,
                large_brake_pulse_validated=False,full_fit_exists=False,model_parameters_changed=False,
                decision='No MPC/controller expansion: gas0/brakefloor.5 raw pulse endpoints missing; limited reset steering/pedal response comparisons and absolute trajectory errors do not certify off-policy planning.',
                limitations=['Selection determined by rawpixel availability and matching325road geometry, not absolute modelerrors; earlierN0/N1/N2/N3 pixels unselected tokeepprimaryexistingLOROmodels andonefixedsecondarypedalfactorial.',
                             'Five pairedfirstactions atreset only, notindependent highspeedcontact trials; later equalHUD orstep doesnotmatchphysicalprestate.',
                             'S1 secondary sixmodelmean usesoverlappingtrainingfolds, notsixindependent predictions or afittedfullmodel.',
                             '291 directcollisionflag absent, damageupdates reportedasproxy andcontactunknown; originalDNFs andcensoredprefixes retained.',
                             'No syntheticpixels, cross-trajectory post-state substitution, GTtraining, counterfactual simulation or missingvalue interpolation.'],
                champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False)
    public=plain(public);assert cost['analysis_wall_s']<p['max_wall_s']
    save(D/'summary-private.json',public);save(G/'retry/extrapolation326_result.json',public);save(D/'cost.json',cost)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==326 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(plain(dict(absolute={g:m['all'] for g,m in aggregate.items()},paired=pair_summary,premise=premise,cost=cost))),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True)
    run(parser.parse_args().private_root.resolve())
