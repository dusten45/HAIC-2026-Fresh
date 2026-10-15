"""Point-preservation gate over all savedinputs; six real paired actor replays."""
import datetime
import json
from pathlib import Path
import sys
import time
import traceback
import numpy as np
from retry.path271_run import read,save
from retry.guard357_stage import verify
from retry.confidence341_run import observations,label
from retry.support342_logic import advance_evidence
from retry.package349_run import rows,cached,projection
from retry.probe338_stage import stack
from retry.frozen_composite_runtime import prepare,validate_response


def charge(D,key):
    b=read(D/'call-budget.json');cap=b['reset_cap'] if key=='actor_resets' else b['cap'];assert b.get(key,0)<cap;b[key]=b.get(key,0)+1;save(D/'call-budget.json',b)


def preflight(p):
    result=[];audits={};losses=[]
    for case in p['cases']+p['untouched_cases']:
        frames,_,gt=observations(case);expected=rows(case['expected_tracker']);assert len(frames)==len(expected)==case['count'];previous=[];labels={};checks=[]
        count=dict(key=case['key'],inputs=len(frames),supported_direct_contexts=0,supported_birth_retained_contexts=0,missing_birth_GT_direct_contexts=0,missing_birth_GT_retained_contexts=0,baseline_supported_direct_losses=0,baseline_supported_retained_losses=0,variant_supported_direct_losses=0,variant_supported_retained_losses=0,low_births=0,baseline_removed_contexts=0,variant_removed_contexts=0,actor_replay_planned=case in p['cases'])
        for i,frame in enumerate(frames):
            sr=advance_evidence(expected[i]['tracker'],previous,i+1,frame.astype(np.float32)/255);previous=sr['after']
            for birth in sr['births']:labels[tuple(birth['uid'])]=label(birth['point'],gt.get(i))[0];count['low_births']+=int(birth['low'])
            old=[j for j,e in enumerate(previous) if e['low']];new=[j for j,(h,e) in enumerate(zip(expected[i]['tracker']['after'],previous)) if e['low'] and h[3]>0]
            supported_direct=[];supported_retained=[]
            for j,(h,e) in enumerate(zip(expected[i]['tracker']['after'],previous)):
                lab=labels[tuple(e['uid'])];kind='direct' if h[3]==0 else 'retained'
                if lab=='fixture_supported':
                    count['supported_direct_contexts' if kind=='direct' else 'supported_birth_retained_contexts']+=1
                    (supported_direct if kind=='direct' else supported_retained).append(j)
                    if j in old:count['baseline_supported_'+kind+'_losses']+=1
                    if j in new:count['variant_supported_'+kind+'_losses']+=1;losses.append(dict(key=case['key'],step=i+1,uid=e['uid'],kind=kind))
                if lab=='missing_GT':count['missing_birth_GT_'+kind+'_contexts']+=1
            count['baseline_removed_contexts']+=len(old);count['variant_removed_contexts']+=len(new)
            checks.append(dict(old_removed=old,new_removed=new,supported_direct=supported_direct,supported_retained=supported_retained,uids=[e['uid'] for e in previous]))
        if case in p['untouched_cases']:assert count['low_births']==count['baseline_removed_contexts']==count['variant_removed_contexts']==0
        result.append(count);audits[case['key']]=checks
    return dict(passed=not losses,cases=result,variant_losses=losses,scope='All2792savedinputcontexts. Knownfixture support usesbirthlabel; missingbirthGT remainsunknown. Sixuntouchedcases lowflagsfalse byinduction => identicalrouting/policyinput forbothversions, sourceproofnotnewactoroutputs.'),audits


def reference(case):
    if case['reference_format']=='342':return cached(Path(case['reference']))
    out={}
    for i,r in enumerate(rows(case['reference'])):
        response=dict(action=r['returned_action'],features=r['features'],pixel_path=r['pixel_path'],delta_audit=r['audit'],tracker_record=r['tracker'],support_record=r['support_record'],routing_evidence=r['routing_evidence'],state=r['actor_state'])
        out[i]=dict(response=response,commit=dict(state=r['policy'],memory=r['nominal_memory']))
    return out


def run(R):
    D=R/'stage357';p=verify(R,True);assert not (D/'opening.json').exists();save(D/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));start,cpu=time.perf_counter(),time.process_time();receipts=[];error=None;gate_failure=None;pre=None
    try:
        pre,audits=preflight(p);save(D/'support-preflight-private.json',pre);assert pre['passed'],'variant supported-point exclusion in fullcorpuspreflight'
        for case in p['cases']:
            frames,_,_=observations(case);expected=rows(case['expected_tracker']);saved=np.load(case['pixels']);saved_obs=saved['observations'][:case['count']] if 'observations' in saved.files else None;ref=reference(case);baseline=[]
            for mode in p['order']:
                verify(R,True);F=D/case['key']/mode;F.mkdir(parents=True,mode=0o700);w=j=None;n=commits=0;last_cpu=None;arm_error=None;t,cc=time.perf_counter(),time.process_time()
                try:
                    w=prepare(p['configs'][mode],F/'cpu',p['sandbox_path']);save(F/'ready-private.json',w.ready);save(F/'configuration-ready.json',w.configuration_ready_receipt)
                    obs=saved_obs[0] if saved_obs is not None else stack(frames,0);charge(D,'actor_resets');reset,_=w.call('reset',obs);validate_response(reset,p['configs'][mode],obs,'reset');assert projection(reset['state'])==projection(read(R/'stage349/candidate/reset-private.json')['state']) and reset['packaged_support_state']==[] and reset['packaged_support_step']==0;save(F/'reset-private.json',reset)
                    j=(F/'records-private.jsonl').open('x');(F/'records-private.jsonl').chmod(0o600)
                    for i in range(case['count']):
                        verify(R);obs=saved_obs[i] if saved_obs is not None else stack(frames,i);charge(D,'actor_act_calls');r,_=w.call('act',obs);n+=1;last_cpu=r['actor_cumulative_CPU_s'];j.write(json.dumps(dict(index=i,response=r),allow_nan=False)+'\n');j.flush();command=validate_response(r,p['configs'][mode],obs,'act');check=audits[case['key']][i]
                        assert r['tracker_record']==expected[i]['tracker'] and r['packaged_support_step']==i+1 and r['packaged_support_state']==r['support_record']['after'];e=r['routing_evidence'];wanted=check['old_removed' if mode=='baseline' else 'new_removed'];assert e['removed_indices']==wanted
                        assert e['full_hazards']==r['tracker_record']['after'] and r['features'][11]==len(e['full_hazards'])
                        assert e['routing_hazards']==[h[:3] for k,h in enumerate(e['full_hazards']) if k not in wanted]
                        if mode=='variant':
                            assert not set(wanted)&set(check['supported_direct']),'supported_direct_exclusion'
                            assert not set(wanted)&set(check['supported_retained']),'supported_retained_exclusion'
                            assert all(e['full_hazards'][k][3]>0 for k in wanted)
                        if mode=='baseline':
                            old=ref[i]['response']
                            for key in ['action','features','pixel_path','delta_audit','tracker_record','support_record']:assert r[key]==old[key],(case['key'],i+1,'baseline',key)
                            assert projection(r['state'])==projection(old['state'])
                        else:
                            old=baseline[i]['response'];assert r['tracker_record']==old['tracker_record'] and r['support_record']==old['support_record']
                            for k in [3,8,11,12]:assert r['features'][k]==old['features'][k]
                            if case['key'] in ['N2_337','N2_340']:
                                for key in ['action','features','pixel_path','delta_audit']:assert r[key]==old[key],(case['key'],i+1,'requiredN2effectpreservation',key)
                                if 127<=i+1<=129:assert [check['uids'][k] for k in wanted]==[[121,0]]
                        assert r['delta_audit']['action']==command.tolist();charge(D,'actor_commit_calls');c,_=w.call('commit',command);commits+=1;last_cpu=c['actor_cumulative_CPU_s'];j.write(json.dumps(dict(index=i,commit=c),allow_nan=False)+'\n');j.flush()
                        assert not c['python_audit_denied_events'] and c['memory']==c['nominal_memory']==r['state']['previous_steer'] and np.float32(c['memory'])==command[0] and c['history'][-1]==command.tolist()
                        if mode=='baseline':assert projection(c['state'])==projection(ref[i]['commit']['state']) and c['memory']==ref[i]['commit']['memory'];baseline.append(dict(response=r,commit=c))
                        elif case['key'] in ['N2_337','N2_340']:assert c['memory']==baseline[i]['commit']['memory'] and projection(c['state'])==projection(baseline[i]['commit']['state'])
                    save(F/'qualification.json',dict(passed=True,inputs=n,mode=mode,baseline_original_records_exact=mode=='baseline',actualactorreplay=True,supported_direct_andretained_exclusions_zero=mode=='variant',N2requiredoutputsequences_preserved=mode=='variant' and case['key'].startswith('N2_')))
                except BaseException as e:arm_error=type(e).__name__+': '+str(e);raise
                finally:
                    if j:j.close()
                    reaping=w.close() if w else None;receipt=dict(key=case['key'],mode=mode,returned_act_calls=n,commits=commits,actor_CPU_s=last_cpu,wall_s=time.perf_counter()-t,runner_CPU_s=time.process_time()-cc,reaping=reaping,error=arm_error);save(F/'receipt.json',receipt);receipts.append(receipt);print(json.dumps(receipt),flush=True)
        b=read(D/'call-budget.json');assert b['actor_act_calls']==b['actor_commit_calls']==3342 and b['actor_resets']==12
    except BaseException as e:
        error=type(e).__name__+': '+str(e);gate_failure=error;save(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),budget=read(D/'call-budget.json')))
    result=dict(passed=error is None,error=error,gate_failure=gate_failure,preflight_passed=pre['passed'] if pre else False,receipts=receipts,budget=read(D/'call-budget.json'),new_native_actions=0,new_environment_resets=0,new_learning_fits=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s_known=sum(x['actor_CPU_s'] or 0 for x in receipts),all_actor_CPU_receipts_available=all(x['actor_CPU_s'] is not None for x in receipts));save(D/'run-result.json',result);print(json.dumps({k:v for k,v in result.items() if k!='receipts'}),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
