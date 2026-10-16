"""Immutable374qualification then296counterfactual on saved374pixels only."""
import datetime,json,time,sys
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.diagnosis376_stage import verify
from retry.probe338_stage import stack
from retry.frozen_composite_runtime import prepare,validate_response

def projection(v):return {k:x for k,x in v.items() if k!='agent_pickle_sha256'}
def run(R):
 D=R/'stage376';p=verify(R,True);assert not (D/'replay-opening.json').exists();save(D/'replay-opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_sha256=sha(Path(__file__))));actual=[json.loads(s) for s in Path(p['actual_trace']).read_text().splitlines()];z=np.load(p['frames_path']);assert len(actual)==len(z['actions'])==303 and len(z['frames_uint8'])==304;receipts=[];error=None;wall,cpu=time.perf_counter(),time.process_time()
 def charge(key):
  c=read(D/'call-counts.json');assert c[key]<(2 if key=='pixel_resets' else 606);c[key]+=1;save(D/'call-counts.json',c)
 try:
  for mode in p['order']:
   verify(R,True);F=D/mode;F.mkdir(mode=0o700);w=None;records=[];start,cpu0=time.perf_counter(),time.process_time();actorcpu=0.
   try:
    w=prepare(p['configs'][mode],F/'cpu',p['sandbox_path']);save(F/'ready-private.json',w.ready);charge('pixel_resets');before,_=w.call('reset',stack(z['frames_uint8'],0));validate_response(before,p['configs'][mode],stack(z['frames_uint8'],0),'reset');save(F/'reset-private.json',before)
    with (F/'records-private.jsonl').open('x') as log:
     (F/'records-private.jsonl').chmod(0o600)
     for i in range(303):
      verify(R);obs=stack(z['frames_uint8'],i);pre=before['state'];charge('actor_act_calls');response,_=w.call('act',obs);command=validate_response(response,p['configs'][mode],obs,'act');charge('actor_commit_calls');commit,_=w.call('commit',command);actorcpu=commit['actor_cumulative_CPU_s'];assert commit['memory']==commit['nominal_memory']==response['state']['previous_steer'] and np.float32(commit['memory'])==command[0] and commit['history'][-1]==command.tolist() and not commit['python_audit_denied_events']
      if mode=='374':
       x=actual[i];assert response['action']==x['executed'] and response['features']==x['features'] and response['pixel_path']==x['pixel_path'] and response['tracker_record']==x['tracker'] and response['routing_evidence']==x['routing_evidence'] and commit['memory']==x['nominal_memory'] and projection(response['state'])==projection(x['actor_state']) and projection(commit['state'])==projection(x['policy']),(i,'374savedreproduction')
      row=dict(step=i+1,pre_state=pre,response=response,commit=commit);log.write(json.dumps(row,allow_nan=False)+'\n');log.flush();records.append(row);before=commit
   finally:
    reap=w.close() if w else None;receipt=dict(mode=mode,actor_act_calls=len(records),actor_commit_calls=len(records),wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu0,actor_CPU_s=actorcpu,reaping=reap);save(F/'receipt.json',receipt);receipts.append(receipt)
 except BaseException as e:error=type(e).__name__+': '+str(e);save(D/'error-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
 result=dict(passed=error is None,error=error,receipts=receipts,counters=read(D/'call-counts.json'),wall_s=time.perf_counter()-wall,runner_CPU_s=time.process_time()-cpu,scope='Fixed374pixels,owncounterfactualcontrols/normalmemory;nolivesimulationorno296score.');save(D/'replay-result.json',result);print(json.dumps(result),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
