"""Two bounded replay actors; packaging differences and diagnostic differences separate."""
import datetime
import json
from pathlib import Path
import sys
import time
import traceback
import numpy as np
from retry.path271_run import read,save
from retry.package349_stage import verify
from retry.probe338_stage import stack
from retry.frozen_composite_runtime import prepare,validate_response


def rows(path):return [json.loads(x) for x in path.read_text().splitlines()]


def projection(state):return {k:v for k,v in state.items() if k!='agent_pickle_sha256'}


def cached(path):
    out={}
    for r in rows(path):out.setdefault(r['index'],{}).update(r)
    return out


def charge(D,kind):
    b=read(D/'call-budget.json');key='actor_act_calls' if kind=='act' else 'actor_resets';assert b[key]<b['cap' if kind=='act' else 'reset_cap'];b[key]+=1;save(D/'call-budget.json',b)


def run(R):
    p=verify(R);D=R/'stage349';assert not (D/'opening.json').exists();save(D/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    start,cpu=time.perf_counter(),time.process_time();receipts=[];error=None;baseline_ok=False
    try:
        for arm in p['order']:
            verify(R);mode=arm['mode'];stage=arm['input_stage'];F=D/mode;F.mkdir(mode=0o700);w=None;j=None;count=commits=0;last_cpu=None;arm_error=None;t,cc=time.perf_counter(),time.process_time()
            if mode=='candidate':assert baseline_ok
            z=np.load(R/f'stage{stage}/B/frames-actions-private.npz');frames=z['frames_uint8'];old=rows(R/f'stage{stage}/B/trace-private.jsonl');assert len(old)==233 and len(frames)==234
            generic=cached(R/f'stage342/N2_{stage}/candidate/records-private.jsonl')
            try:
                w=prepare(p['configs'][mode],F/'cpu',p['sandbox_path']);save(F/'ready-private.json',w.ready);save(F/'configuration-ready.json',w.configuration_ready_receipt)
                for path in w.ready['actual_code_paths'].values():assert Path(path).resolve().is_relative_to((F/'cpu/package').resolve())
                obs=stack(frames,0);assert obs.dtype==np.float32 and obs.shape==(4,84,84) and all(np.array_equal(obs[0],q) for q in obs)
                charge(D,'reset');reset,_=w.call('reset',obs);validate_response(reset,p['configs'][mode],obs,'reset');expected=read(R/'stage337/cache/reset-private.json')['state']
                if mode=='baseline':assert reset['state']==expected and reset['packaged_support_state'] is None
                else:assert projection(reset['state'])==projection(expected) and reset['packaged_support_state']==[] and reset['packaged_support_step']==0 and reset['support_record'] is None
                save(F/'reset-private.json',reset)
                j=(F/'records-private.jsonl').open('x');(F/'records-private.jsonl').chmod(0o600)
                for i in range(233):
                    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
                    obs=stack(frames,i);charge(D,'act');r,_=w.call('act',obs);count+=1;last_cpu=r['actor_cumulative_CPU_s'];command=validate_response(r,p['configs'][mode],obs,'act')
                    j.write(json.dumps(dict(index=i,response=r),allow_nan=False)+'\n');j.flush()
                    assert r['tracker_record']==old[i]['tracker'],(mode,i+1,'tracker')
                    if mode=='baseline':
                        for key,refkey in [('action','returned_action'),('features','features'),('pixel_path','pixel_path'),('delta_audit','audit')]:assert r[key]==old[i][refkey],(mode,i+1,key)
                        assert not r['routing_evidence']['removed_indices']
                    else:
                        ref=generic[i]['response']
                        for key in ['action','features','pixel_path','delta_audit','tracker_record','support_record']:assert r[key]==ref[key],(mode,i+1,'generic342',key)
                        for key in ['full_hazards','routing_hazards','removed_indices','removed_evidence']:assert r['routing_evidence'][key]==ref['routing_evidence'][key],(mode,i+1,key)
                        assert r['packaged_support_state']==r['support_record']['after'] and r['packaged_support_step']==i+1
                    assert command.tolist()==r['action'];c,_=w.call('commit',command);commits+=1;last_cpu=c['actor_cumulative_CPU_s'];j.write(json.dumps(dict(index=i,commit=c),allow_nan=False)+'\n');j.flush()
                    assert not c['python_audit_denied_events'] and np.float32(c['memory'])==command[0] and c['memory']==c['nominal_memory'] and c['history'][-1]==command.tolist()
                    if mode=='baseline':assert c['state']==old[i]['policy'] and c['memory']==old[i]['nominal_memory']
                    else:assert projection(c['state'])==projection(generic[i]['commit']['state']) and c['memory']==generic[i]['commit']['memory']
                if mode=='baseline':baseline_ok=True;save(D/'baseline-qualified.json',dict(passed=True,actor_calls=233,full_saved_policy_state_exact=True,action_features_path_tracker_audit_exact=True))
            except BaseException as e:arm_error=type(e).__name__+': '+str(e);raise
            finally:
                if j:j.close()
                reaping=w.close() if w else None
                receipt=dict(mode=mode,input_stage=stage,returned_act_calls=count,committed_actions=commits,actor_CPU_s=last_cpu,wall_s=time.perf_counter()-t,runner_CPU_s=time.process_time()-cc,reaping=reaping,technical_error=arm_error);save(F/'receipt.json',receipt);receipts.append(receipt)
                print(json.dumps(receipt),flush=True)
            verify(R)
        b=read(D/'call-budget.json');assert b['actor_act_calls']==466 and b['actor_resets']==2
    except BaseException as e:
        error=type(e).__name__+': '+str(e);save(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),budget=read(D/'call-budget.json')))
    out=dict(passed=error is None,technical_error=error,baseline_qualified=baseline_ok,receipts=receipts,budget=read(D/'call-budget.json'),new_native_actions=0,new_environment_resets=0,new_learning_fits=0,new_thresholds=0,new_tuning=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s_known=sum(r['actor_CPU_s'] or 0 for r in receipts))
    save(D/'run-result.json',out);print(json.dumps(out),flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
