"""Bounded fixed-pixel paired actors; no environment or source physics import."""
import argparse
import json
import time
import traceback
from pathlib import Path
import numpy as np
from retry.path271_run import read,save
from retry.support342_stage import verify
from retry.support342_logic import birth_evidence,advance_evidence
from retry.confidence341_run import observations,label,rows
from retry.probe338_stage import stack
from retry.frozen_composite_runtime import prepare


def charge(D,kind):
    b=read(D/'call-budget.json');key='actor_act_calls' if kind=='act' else 'actor_resets';cap=b['cap' if kind=='act' else 'reset_cap'];assert b[key]<cap;b[key]+=1;save(D/'call-budget.json',b)


def run(R):
    D=R/'stage342';p=verify(R);assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));start,cpu=time.perf_counter(),time.process_time();receipts=[];preflight=[];error=None;baseline_qualified=False;losses=[]
    try:
        # Cheap source-algebra checks consume zero actor calls and zero resets.
        for case in p['untouched_cases']:
            frames,records,_=observations(case)
            for i,frame in enumerate(frames):
                births=birth_evidence(frame.astype(np.float32)/255,records[i]['tracker']['direct']);assert not any(q['low'] for q in births)
            preflight.append(dict(key=case['key'],inputs=len(frames),all_direct_predicates_false=True,no_op_proof='Initial flags empty; new flags false; original prediction/dedup/expiry only propagates/removes flags. Routing filter can never activate.',new_actor_calls=0))
        for case in p['cases']:
            frames,records,_=observations(case);expected=rows(case['expected_tracker']);previous=[]
            for i,frame in enumerate(frames):
                state=advance_evidence(expected[i]['tracker'],previous,i+1,frame.astype(np.float32)/255);previous=state['after']
            preflight.append(dict(key=case['key'],inputs=len(frames),expected_current_tracker_and_flag_algebra_verified=True,new_actor_calls=0))
        save(D/'preflight.json',dict(passed=True,cases=preflight,new_actor_calls=0,new_native_actions=0))
        for case in p['cases']:
            frames,old,gt=observations(case);expected=rows(case['expected_tracker']);baseline=[]
            z=np.load(case['pixels']);saved_obs=z['observations'][:len(frames)] if 'observations' in z.files else None
            for mode in ['baseline','candidate']:
                if case['key']!='N2_337' or mode=='candidate':assert baseline_qualified
                verify(R);F=D/case['key']/mode;F.mkdir(parents=True,mode=0o700);w=None;returned=committed=0;last_cpu=None;birth_labels={};t,cc=time.perf_counter(),time.process_time();j=None;arm_error=None
                try:
                    w=prepare(p['configs'][mode],F/'cpu',p['sandbox_path']);save(F/'ready-private.json',w.ready);charge(D,'reset');reset,_=w.call('reset',saved_obs[0] if saved_obs is not None else stack(frames,0));assert reset['state']==read(R/'stage338/cache/reset-private.json')['state'];save(F/'reset-private.json',reset)
                    j=(F/'records-private.jsonl').open('x');(F/'records-private.jsonl').chmod(0o600)
                    for i in range(len(frames)):
                        # Lightweight immutable-plan/deadline check per input;
                        # every registered input hash is checked between arms.
                        assert time.time()<__import__('datetime').datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
                        obs=saved_obs[i] if saved_obs is not None else stack(frames,i);charge(D,'act');r,_=w.call('act',obs);returned+=1;last_cpu=r['actor_cumulative_CPU_s']
                        entry=dict(index=i,response=r,commit=None);j.write(json.dumps(entry,allow_nan=False)+'\n');j.flush()
                        assert not r['python_audit_denied_events'];t_actual=r['tracker_record'];assert t_actual==expected[i]['tracker'],(case['key'],mode,i,'tracker')
                        sr=r['support_record'];re=r['routing_evidence'];assert re['tracker_preserved'] and re['full_hazards']==t_actual['after'] and len(sr['after'])==len(t_actual['after'])
                        assert [q['point'] for q in sr['births']]==t_actual['direct'];assert r['features'][11]==len(t_actual['after'])
                        for birth in sr['births']:
                            lab,identity=label(birth['point'],gt.get(i));uid=tuple(birth['uid']);birth_labels[uid]=dict(label=lab,supported_id=identity)
                            if mode=='candidate' and birth['low'] and lab=='fixture_supported':losses.append(dict(key=case['key'],step=i+1,kind='supported_direct_birth',uid=birth['uid']))
                        for evidence in re['removed_evidence']:
                            assert mode=='candidate' and evidence['low'] and evidence['raw_road_neighbors']==0
                            if birth_labels[tuple(evidence['uid'])]['label']=='fixture_supported':losses.append(dict(key=case['key'],step=i+1,kind='supported_birth_retained',uid=evidence['uid']))
                        assert not losses,'fixture-supported point withheld from routing'
                        if mode=='baseline':assert not re['removed_indices']
                        if mode=='candidate':
                            ref=baseline[i]['response'];assert t_actual==ref['tracker_record'] and sr==ref['support_record']
                            fixed=[3,8,11,12];assert [r['features'][q] for q in fixed]==[ref['features'][q] for q in fixed]
                            if not r['features'][0] and not ref['features'][0]:assert r['features'][4]==ref['features'][4]
                        if case['key']=='N2_337' and mode=='baseline':
                            assert r['action']==old[i]['returned_action'] and r['features']==old[i]['features'] and r['pixel_path']==old[i]['pixel_path'] and r['delta_audit']==old[i]['audit']
                        command=np.asarray(r['action'],np.float32);assert r['delta_audit']['action']==command.tolist();c,_=w.call('commit',command);committed+=1;last_cpu=c['actor_cumulative_CPU_s']
                        assert c['memory']==c['nominal_memory']==r['state']['previous_steer'] and np.float32(c['memory'])==command[0] and c['history'][-1]==command.tolist()
                        if case['key']=='N2_337' and mode=='baseline':assert c['state']==old[i]['policy'] and c['memory']==old[i]['nominal_memory']
                        entry['commit']=c;j.write(json.dumps(dict(index=i,commit=c),allow_nan=False)+'\n');j.flush()
                        if mode=='baseline':baseline.append(entry)
                    if case['key']=='N2_337' and mode=='baseline':baseline_qualified=True;save(D/'baseline337-qualified.json',dict(passed=True,inputs=233,all_outputs_tracker_full_state_nominal_memory_exact=True))
                except BaseException as e:
                    arm_error=type(e).__name__+': '+str(e);raise
                finally:
                    if j:j.close()
                    reaping=w.close() if w else None
                    receipt=dict(key=case['key'],mode=mode,returned_act_calls=returned,committed_actions=committed,actor_CPU_s=last_cpu,wall_s=time.perf_counter()-t,runner_CPU_s=time.process_time()-cc,reaping=reaping,technical_error=arm_error)
                    save(F/'receipt.json',receipt);receipts.append(receipt)
                print(json.dumps(receipt),flush=True)
                verify(R)
        budget=read(D/'call-budget.json');assert budget['actor_act_calls']==2630 and budget['actor_resets']==10 and sum(q['returned_act_calls'] for q in receipts)==2630
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),budget=read(D/'call-budget.json'),supported_losses=losses))
    budget=read(D/'call-budget.json');out=dict(passed=not error,technical_error=error,baseline337_qualified=baseline_qualified,receipts=receipts,charged_actor_calls=budget['actor_act_calls'],charged_actor_resets=budget['actor_resets'],supported_losses=losses,new_native_actions=0,new_environment_resets=0,new_learning_fits=0,new_source_physics_ticks=0,parameter_sweeps=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s_known=sum(q['actor_CPU_s'] or 0 for q in receipts),all_actor_CPU_receipts_available=all(q['actor_CPU_s'] is not None for q in receipts))
    save(D/'run-result.json',out);print(json.dumps({k:v for k,v in out.items() if k!='receipts'}),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);run(a.parse_args().private_root)
