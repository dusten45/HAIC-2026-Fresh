"""Sequential13 episodes; posthoc support/technical gate before next reset."""
import datetime
import json
from pathlib import Path
import sys
import time
import numpy as np
from retry.path271_run import read,save,sha
from retry.evaluation363_stage import verify
from retry.evaluation363_episode import run as episode
from retry.confidence341_run import label
from retry.pair343_close import describe

def rows(path):return [json.loads(x) for x in Path(path).read_text().splitlines()]

def audit_case(R,key):
    D=R/'stage363'/key;r=read(D/'B/result.json');data=rows(D/'B/trace-private.jsonl');b=read(D/'native-budget.json');z=np.load(D/'B/frames-actions-private.npz');used=b['actions']
    assert r['technical_error'] is None and r['comparison_valid'] and read(D/'reset-qualification.json')['passed']
    assert used==r['native_actions']==len(data)==len(z['actions'])==b['actor_act_calls']==b['actor_commit_calls']<=2000 and len(z['frames_uint8'])==used+1 and b['resets']==b['actor_resets']==1
    assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50 and r['raw_reset_ticks']==51
    assert all(not x['terminated'] and not x['truncated'] for x in data[:-1]) and r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
    if r['completed']:assert not r['actual_DNF'] and not r['censored'] and r['stop_reason']=='official_finish' and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
    if r['protocol_stop']:assert used==2000 and r['censored'] and not r['actual_DNF'] and not r['completed']
    births={};direct=retained=missing_direct=missing_retained=0;losses=[];low=[];protected=[];held=[]
    for x in data:
        assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks']
        e=x['routing_evidence'];assert e['full_hazards']==x['tracker']['after'] and x['features'][11]==len(e['full_hazards']) and e['removed_indices']==[j for j,(h,item) in enumerate(zip(x['tracker']['after'],x['support_record']['after'])) if item['low'] and h[3]>0]
        for item in x['support_record']['births']:
            lab,idx=label(item['point'],x['pre_physical']);births[tuple(item['uid'])]=dict(label=lab,fixture_index=idx)
            if item['low']:low.append(dict(action=x['step'],uid=item['uid'],area_pixels=item['component_area'],label=lab))
        for j,(h,item) in enumerate(zip(x['tracker']['after'],x['support_record']['after'])):
            lab=births[tuple(item['uid'])]['label'];age=h[3];excluded=j in e['removed_indices']
            if lab=='fixture_supported':
                if age==0:direct+=1
                else:retained+=1
                if excluded:losses.append(dict(action=x['step'],uid=item['uid'],age=age,kind='direct' if age==0 else 'birth_supported_retained'))
            if lab=='missing_GT':
                if age==0:missing_direct+=1
                else:missing_retained+=1
            if age==0:assert not excluded
            if item['low'] and age==0:protected.append(x['step'])
            if excluded:held.append(dict(action=x['step'],uid=item['uid'],age=age))
    gate=dict(passed=not losses,technical_error=None,known_supported_direct_contexts=direct,known_birth_supported_retained_contexts=retained,supported_direct_losses=sum(x['kind']=='direct' for x in losses),supported_retained_losses=sum(x['kind']=='birth_supported_retained' for x in losses),losses=losses,missing_birth_GT_direct=missing_direct,missing_birth_GT_retained=missing_retained,low_births=low,protected_current_direct_actions=protected,retained_exclusions=held,own_controls_memory_verified=True,scope='Postepisodebirthcirclecorrespondenceonly; notsemanticmaterialorocclusiontruth. GTnotactorinput; directandbirthsupportedretained countedseparately.')
    save(D/'support-gate.json',gate);save(D/'outcome-summary.json',describe(data,r));return gate

def run(R):
    D=R/'stage363';p=verify(R,True);assert not (D/'batch-opening.json').exists();save(D/'batch-opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_sha256=sha(Path(__file__))))
    status=dict(stage=363,attempted=[],evaluated=[],stop_reason=None,all13_finished=False);start=time.perf_counter();cpu=time.process_time()
    try:
        for key in p['order']:
            verify(R,True);F=D/key;assert not F.exists();F.mkdir(mode=0o700);save(F/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=2000,reset_cap=1));status['attempted'].append(key);save(D/'batch-status.json',status)
            episode(R,key);gate=audit_case(R,key);status['evaluated'].append(key);save(D/'batch-status.json',status)
            rr=read(F/'B/result.json');print(json.dumps(dict(stage=363,condition=key,actions=rr['native_actions'],completed=rr['completed'],lap_ms=rr['lap_ms'],actual_DNF=rr['actual_DNF'],support_gate=gate['passed'],support_losses=len(gate['losses']))),flush=True)
            if not gate['passed']:status['stop_reason']='supported_point_loss';break
            if not rr['completed'] and not rr['actual_DNF'] and not rr['protocol_stop']:status['stop_reason']='other_official_truncation';break
        else:status['all13_finished']=True;status['stop_reason']='all13_evaluated'
    except BaseException as exc:
        status['stop_reason']='technical_or_integrity_error';status['technical_error']=type(exc).__name__+': '+str(exc);save(D/'batch-error-private.json',dict(error=status['technical_error'],traceback=__import__('traceback').format_exc(),budget=read(D/'native-budget.json')))
    status.update(wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,budget=read(D/'native-budget.json'));save(D/'batch-status.json',status);print(json.dumps(status),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
