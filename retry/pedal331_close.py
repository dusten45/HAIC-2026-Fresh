"""Close the preregistered pedal-only diagnostic; export aggregates only."""
import argparse
import datetime
import json
import runpy
from pathlib import Path

import numpy as np
from retry.path271_run import read,save,sha
from retry.pedal331_run import digest,plain


def diagnostic_summary(records):
    out={}
    for label,rows in records.items():
        impact=next((r for r in rows if r['collision']),None)
        prior=[r for r in rows if impact is None or r['step']<impact['step']]
        out[label]=dict(precontact_steps=len(prior),precontact_mean_H1_speed_absolute_error=mean(abs(r['mean_next'][0]-r['actual_post_HUD_speed']) for r in prior if r['actual_post_HUD_speed'] is not None),
            first_contact_H1_supported=all(impact['support_by_model']) if impact else None,
            first_contact_predicted_goal_error=impact['predicted_H1_goal_error'] if impact else None,
            first_contact_actual_HUD_goal_error=impact['actual_H1_goal_error'] if impact else None,
            first_contact_predicted_speed=float(impact['mean_next'][0]) if impact else None,
            first_contact_actual_HUD_speed=impact['actual_post_HUD_speed'] if impact else None,
            first_contact_actual_true_speed=impact['speed_m_s'] if impact else None,
            first_contact_time_interval_s=impact['contact_interval_s'] if impact else None)
    return out


def close(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage331';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    assert not (D/'cost.json').exists()
    a=read(D/'A/result.json');b=read(D/'B/result.json');assert a['reference330_exact'];assert not a['technical_error'] and not b['technical_error']
    assert read(D/'A/boundary-private.json')==read(D/'B/boundary-private.json')
    cfg=p['config'];package=D/'A/cpu/package';models_file=package/'retry/h1_330_model.py';hud_file=package/'retry/hud_feedback.py'
    assert sha(models_file)==cfg['members_sha256']['retry/h1_330_model.py'];assert sha(hud_file)==cfg['members_sha256']['retry/hud_feedback.py']
    models=runpy.run_path(str(models_file))['MODELS'];decode=runpy.run_path(str(hud_file))['decode_feedback_speed'];records={};outcomes={}
    for label,result in [('A',a),('B',b)]:
        assert result['native_actions']==72 and result['reaping']['process_reaped'] and result['reaping']['actor_pids_absent']
        rows=[json.loads(s) for s in (D/label/'trace-private.jsonl').read_text().splitlines()];z=np.load(D/label/'raw-pixels-actions-private.npz');assert len(rows)==len(z['actions'])==72 and len(z['observations'])==73
        actual=[]
        for row in rows[64:]:
            i=row['step']-1;x=np.r_[row['pixel_state'],row['executed']];predictions=np.array([np.array(row['pixel_state'])+np.r_[(x-m['mean'])/m['scale'],1.]@m['beta'] for m in models]);prediction=predictions.mean(0)
            support=[bool(np.all(x>=m['low']) and np.all(x<=m['high'])) for m in models];post_hud=decode(z['observations'][i+1,-1],None);q=None if row['features'][0] else row['features'][6]
            record=dict(step=i+1,models_next=predictions.tolist(),mean_next=prediction.tolist(),support_by_model=support,q=q,actual_post_HUD_speed=post_hud,
                predicted_H1_goal_error=abs(float(prediction[0])-q) if q is not None else None,
                actual_H1_goal_error=abs(post_hud-q) if q is not None and post_hud is not None else None,
                actual_true_speed_goal_error=abs(row['post']['speed_m_s']-q) if q is not None else None,
                collision=row['collision'],damage=row['damage'],damage_increase=row['damage_increase'],
                contact_interval_s=row['first_contact_interval_s'],speed_m_s=row['post']['speed_m_s'],position=row['post']['position'],heading=row['post']['angle'],
                angular_velocity=row['post']['angular_velocity'],progress=row['progress'],selector_fallback=row['audit']['reason'],
                calculated_steering=row['calculated_steering'],executed_steering=row['executed_steering'],nominal_memory=row['nominal_memory'])
            assert row['executed'][0]==read_original_action(R,i)[0]
            assert row['nominal_memory']==row['policy']['previous_steer']
            if label=='B':assert row['executed'][1:]==row['calculated296'][1:]
            actual.append(record)
        records[label]=actual
        outcomes[label]=dict(native_actions=72,first_contact=result['first_contact'],contact_steps=[r['step'] for r in rows if r['collision']],damage=result['damage'],actual_DNF=result['actual_DNF'],actual_terminal=result['actual_terminal'],completed=result['completed'],protocol_stop=result['protocol_stop'],retire_reason=result['retire_reason'],
            branch_steering_overrides=sum(r['calculated_steering']!=r['executed_steering'] for r in rows[64:]),branch_supported_H1_actions=sum(all(r['support_by_model']) for r in actual),
            branch_target_missing=sum(r['q'] is None for r in actual),branch_HUD_missing=sum(r['actual_post_HUD_speed'] is None for r in actual),
            endpoint_speed_m_s=actual[-1]['speed_m_s'],endpoint_progress=actual[-1]['progress'],
            mean_predicted_H1_goal_error=mean(r['predicted_H1_goal_error'] for r in actual),mean_actual_H1_goal_error=mean(r['actual_H1_goal_error'] for r in actual),
            mean_H1_speed_absolute_error=mean(abs(r['mean_next'][0]-r['actual_post_HUD_speed']) for r in actual if r['actual_post_HUD_speed'] is not None))
    save(D/'H1-physical-comparison-private.json',plain(records))
    endpoint_position_gap=float(np.linalg.norm(np.array(records['A'][-1]['position'])-records['B'][-1]['position']));endpoint_heading_gap=abs(records['A'][-1]['heading']-records['B'][-1]['heading'])
    before=R/'project-effective-budget-v337.json';v=read(before);budget=read(D/'native-budget.json');used=a['native_actions']+b['native_actions'];assert used==budget['actions']==144<=budget['cap']<=v['research_remaining'];assert v['final_reserved_actions']==84000
    cost=dict(stage=331,new_wrapper_actions=used,native_cap=144,raw_step_ticks=a['raw_step_ticks']+b['raw_step_ticks'],raw_reset_ticks=a['raw_reset_ticks']+b['raw_reset_ticks'],
        runner_CPU_s=a['runner_CPU_s']+b['runner_CPU_s'],actor_CPU_s=a['actor_CPU_s']+b['actor_CPU_s'],native_wall_s=a['wall_s']+b['wall_s'],cache_wall_s=read(D/'cache-receipt.json')['wall_s'],
        offline_cached_policy_calls=72,new_fits=0,new_source_physics_ticks=0,new_paid_resources=0,additional_research=0,
        actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+used,research_remaining=v['research_remaining']-used,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=v['B_operating_cap'])
    save(D/'cost.json',cost);v.update(version=338,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),prior_budget_path=str(before),prior_budget_sha256=sha(before),B_increment=0,
        authorization_end_utc=p['deadline_utc'],cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage331_new_wrapper_actions=used)
    assert not (R/'project-effective-budget-v338.json').exists();save(R/'project-effective-budget-v338.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==331 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
    public=dict(stage=331,design='N2 independent reset twice; identical stored330 prefix64; stored330 steering fixed65-72; A stored330 pedals; B original296 final pedals on its actual observations, retaining calculated nominal memory.',
        reference330_A_exact=True,reference_actions=72,reference_observation_stacks=73,prebranch_observation_captured_physical_policy_tracked_RNG_exact=True,
        outcomes=outcomes,endpoint_position_gap_m=endpoint_position_gap,endpoint_heading_gap_rad=endpoint_heading_gap,cost=cost,
        limitations=['Single postselected known TRAIN branch; no generalization or full-lap result.',
            'Equal physical state means captured fields, not unexposed Box2D warm-start/broadphase/island internals. Exact independent replay and all saved pixels corroborate the boundary.',
            'Python/NumPy and environment RNG states match; OpenCV only existing seed-call stream matches. Its opaque internal RNG state has no getter and was not directly verified.',
            'Contact timing has wrapper .08-second interval resolution; collision flags are actual simulator outcomes.',
            'Unsupported H1 forecasts are extrapolation diagnostics. Missing targets have no defined goal error.'],
        champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,promotion=False)
    if b['first_contact'] is None:interpretation='B avoided contact within steps65-72. This supports a local pedal effect under the fixed stored steering; it does not establish full-policy or full-lap superiority.'
    elif b['first_contact']==a['first_contact'] and b['actual_DNF']!=a['actual_DNF']:interpretation='Both arms first contacted at the same step; crash outcome differs. Evidence supports only a local postcontact recovery effect, not contact avoidance.'
    else:interpretation='Both arms contacted. Compare first-contact timing and actual retirement without claiming unavoidability; no contact-avoidance gate passed.'
    public['interpretation']=interpretation
    public['next_high_information_hypothesis']='Proposed only: geometric tracking state inherited from prefix64 dominates initial contact, while pedal choices may affect contact speed and subsequent damage. Distinguish by an earlier matched steering-only intervention with identical pedals and explicit calculated-memory semantics; preregister budget before any run. Both failures alone do not establish this cause.'
    public['H1_contact_diagnostic']=diagnostic_summary(records)
    save(D/'summary-private.json',public);save(G/'retry/pedal331_result.json',public);print(json.dumps(public,ensure_ascii=False),flush=True)


def mean(values):
    v=[x for x in values if x is not None];return float(np.mean(v)) if v else None


def read_original_action(R,i):
    return np.load(R/'stage330/evaluation/N2/raw-pixels-actions-private.npz')['actions'][i]


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);close(p.parse_args().private_root)
