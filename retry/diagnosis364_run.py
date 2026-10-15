"""Reproduce63inputs; four fixed-input original/restore-full clone comparisons."""
from pathlib import Path
import sys,time,json
import numpy as np
from retry.path271_run import read,save
from retry.diagnosis364_stage import verify
from retry.package349_run import projection
from retry.probe338_stage import stack
from retry.frozen_composite_runtime import prepare,validate_response

def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]
def charge(D,key,n=1):
    p=read(D/'plan.json');b=read(D/'call-budget.json');caps=dict(actor_act_calls=63,actor_commit_calls=63,pixel_resets=1,probes=4,clone_act_calls=8,routing_entries=8,target_entries=8);assert b[key]+n<=caps[key];b[key]+=n;save(D/'call-budget.json',b)
def run(R):
    D=R/'stage364';p=verify(R,True);assert not (D/'opening.json').exists();save(D/'opening.json',dict(saved_only=True));rr=rows(R/'stage363/T29510/B/trace-private.jsonl');frames=np.load(R/'stage363/T29510/B/frames-actions-private.npz')['frames_uint8'];w=j=None;cpu=time.process_time();wall=time.perf_counter();error=None;actor_cpu=0;probes=[]
    try:
        w=prepare(p['config'],D/'cpu',p['sandbox_path']);save(D/'ready-private.json',w.ready);charge(D,'pixel_resets');r,_=w.call('reset',stack(frames,0));validate_response(r,p['config'],stack(frames,0),'reset');j=(D/'records-private.jsonl').open('x');(D/'records-private.jsonl').chmod(0o600)
        for i in range(63):
            verify(R);obs=stack(frames,i);charge(D,'actor_act_calls');r,_=w.call('act',obs);actor_cpu=r['actor_cumulative_CPU_s'];action=validate_response(r,p['config'],obs,'act');x=rr[i]
            for k,key in [('action','returned_action'),('features','features'),('pixel_path','pixel_path'),('delta_audit','audit'),('tracker_record','tracker'),('support_record','support_record'),('routing_evidence','routing_evidence')]:assert r[k]==x[key],(i+1,k)
            assert projection(r['state'])==projection(x['actor_state']);j.write(json.dumps(dict(step=i+1,response=r))+'\n');j.flush()
            if i+1 in p['target_steps']:
                charge(D,'probes');charge(D,'clone_act_calls',2);charge(D,'routing_entries',2);charge(D,'target_entries',2);probe,_=w.call('restore_probe',obs);actor_cpu=probe['actor_cumulative_CPU_s'];assert probe['state_preserved'] and probe['state']==r['state'];v=probe['variants'];a,b=v['original'],v['restored']
                assert a['action']==r['action'] and a['features']==r['features'] and a['path']==r['pixel_path'] and a['delta_audit']==r['delta_audit']
                assert a['routing_evidence']==r['routing_evidence'] and b['routing_evidence']['removed_indices']==[] and a['routing_evidence']['removed_indices']==[0]
                assert a['features'][3]==b['features'][3] and a['features'][7:9]==b['features'][7:9] and a['features'][11:13]==b['features'][11:13]
                assert np.isfinite(b['action']).all();probes.append(dict(step=i+1,probe=probe));j.write(json.dumps(dict(step=i+1,probe=probe))+'\n');j.flush()
            charge(D,'actor_commit_calls');c,_=w.call('commit',action);actor_cpu=c['actor_cumulative_CPU_s'];assert projection(c['state'])==projection(x['policy']) and c['memory']==x['nominal_memory'] and not c['python_audit_denied_events'];j.write(json.dumps(dict(step=i+1,commit=c))+'\n');j.flush()
        verify(R,True);save(D/'probes-private.json',probes)
    except BaseException as e:error=type(e).__name__+': '+str(e);save(D/'failure-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
    finally:
        if j:j.close()
        reaping=w.close() if w else None
    save(D/'run-result.json',dict(passed=error is None,error=error,calls=read(D/'call-budget.json'),wall_s=time.perf_counter()-wall,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=actor_cpu,reaping=reaping,new_native_actions=0));print('364 clonecheck',error or 'passed',flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
