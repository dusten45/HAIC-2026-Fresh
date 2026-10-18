"""Read-only source finishes, precharges, current-state commands and certificates."""
import json,hashlib,math,time
from pathlib import Path
import numpy as np
from retry.governor525b_control import path_for,backup
from retry.drive519_control import project,nominal,steering
from retry.plan513_model import load_root
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response525-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/governor525b_contract.json').read_text());m=json.loads((G/'retry/governor525b_model_result.json').read_text());r=json.loads((G/'retry/governor525b_native_result.json').read_text());original=json.loads((G/'retry/governor525_model_result.json').read_text());assert not original['native_pair_eligible'] and m['native_pair_eligible']
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    admission=json.loads((D/'native-admission-private.json').read_text());assert admission['contract_sha256']==hashlib.sha256((G/'retry/governor525b_contract.json').read_bytes()).hexdigest();assert admission['model_result_sha256']==hashlib.sha256((G/'retry/governor525b_model_result.json').read_bytes()).hexdigest()
    charges=sorted(D.glob('charge-*.json'));assert len(charges)==r['counts']['actions']
    for i,p in enumerate(charges,1):
        z=json.loads(p.read_text());assert p.name==f'charge-{i:03d}.json' and z['attempted_actual_actions']==i and z['research_remaining']==24641-i and z['reserve_used']==0
    raw=[json.loads(p.read_text()) for p in sorted(D.glob('raw-*.json'))];assert len(raw)==r['counts']['raw_attempts']==r['counts']['raw_completed'];assert all(not z['errors'] for z in raw)
    resets=sum(z['phase']=='reset' for z in raw);active=sum(z['phase']=='action' for z in raw);assert resets==102 and resets+active==len(raw)
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());arms=json.loads((D/'native-full-records-private.json').read_text());commands=certificates=0;prefix=[];terminal=[]
    # Partition raw rows by reset event/arm action counts; eachreset exactly51.
    offset=0
    for arm in arms:
        variant=arm['budget'];path=path_for(static,variant);low=path_for(static,'baseline');progress=project(static['root']['center'],path)['s'];sameprefix=[];history_clipped=history_samples=0;start=offset+51;arm_raw=sum(z['raw_ticks'] for z in arm['rows']);rows=raw[start:start+arm_raw];offset=start+arm_raw;by_action={}
        for row in rows:by_action.setdefault(row['action'],[]).append(row)
        for record in arm['rows']:
            i=record['index'];data=json.loads((D/f'action-{variant}-{i:03d}.json').read_text());state=data['before_root_without_roads'];state['roads']=static['root']['roads'];root=load_root(state);mode=record['governor_mode'];detail=data['governor_detail']
            if i<=24:expected=np.array([steering(root,path,progress),.32,0.],np.float32)
            elif variant=='baseline' or mode=='HIGH':expected=nominal(root,path,progress)
            else:assert mode=='BACKUP';expected=backup(root,path,low,progress)
            assert np.array_equal(expected,np.asarray(record['action'],np.float32));commands+=1
            if variant=='governor' and i>24:
                report=detail['reports'][-1];assert report['ok'] and report['peak']<=1.06 and report['samples']==history_samples+192 and report['model_ticks']==48 and report['clipped']/report['samples']<=.10
                if mode=='BACKUP':assert len(detail['reports'])==2 and not detail['reports'][0]['ok']
                certificates+=1
            current=by_action[i];assert len(current)==record['raw_ticks']
            if i>24:
                history_samples+=sum(len(z['forces']) for z in current);history_clipped+=sum(w['ratio']>1 for z in current for w in z['forces'])
            after=data['after_root_without_roads'];progress=project(after['center'],path,progress)['s']
            if i<=24:sameprefix.append(dict(action=record['action'],obs_sha256=record['obs_sha256']))
            if record['raw_ticks']<4:terminal.append(dict(variant=variant,index=i,actual_raw_ticks=record['raw_ticks']))
        prefix.append(sameprefix)
        assert arm['official_finish'] and arm['stop']=='OFFICIAL_FINISH' and arm['visited_tiles']==arm['tile_count']
        assert history_clipped==arm['force_groups']['running']['clipped'] and history_samples==arm['force_groups']['running']['samples']
    assert offset==len(raw) and prefix[0]==prefix[1] and len(prefix[0])==24 and commands==len(charges)
    assert r['both_actual_official_finishes'] and r['practical_effect_gate'] and r['official_finish_gain_s']>=.5
    force_error=max(z['forecast_error']['max_force_ratio_error'] for z in raw if z['forecast_error'] is not None);oracle=max((z['force_oracle_vector_error_N'] or 0) for z in raw);impulse=max((z['COM_impulse_error_m_s'] or 0) for z in raw)
    out=dict(status='ACTUAL_PAIR_AND_CERTIFICATES_VERIFIED',all_source_input_admission_pins_verified=True,original525failure_preserved=True,precharge_count=len(charges),own_state_commands_verified=commands,certified_governor_tracking_actions=certificates,certificate_history_sample_counts_verified=True,paired24action_observation_prefix_exact=True,actual_official_finish_gain_s=r['official_finish_gain_s'],baseline_official_finish_s=r['arms'][0]['official_finish_episode_s'],governor_official_finish_s=r['arms'][1]['official_finish_episode_s'],reset_raw_ticks=resets,action_raw_ticks=active,total_native_raw_ticks=len(raw),all_raw_errors=0,terminal_partial_holds=terminal,source_force_captures=sum(len(z['forces']) for z in raw),max_corrected_one_hold_force_ratio_error=force_error,max_source_force_oracle_vector_error_N=oracle,max_source_COM_impulse_error_m_s=impulse,new_posthoc_integrator_ticks=0,new_posthoc_force_evaluations=0,research_remaining=24641-len(charges),reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,scope='SameknownDEV oneactualpair; certificatescheckedfromsavedreports andcurrentstatecommandswithoutre-runninggovernor. No independentDEV/pixel/11sclaim. Model525bexecutionboundaryrevisionisexplicit,old525/522/523failuresretained.')
    assert out['CPU_s']<30 and out['wall_s']<45
    with (G/'retry/governor525_verification.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
