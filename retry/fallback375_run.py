"""Sequential immutable374 runs, posthoc gate before each next reset."""
import datetime,json,time,sys
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.fallback375_stage import verify
from retry.fallback375_episode import run as episode
from retry.fallback334_math import advance
from retry.confidence341_run import label
from retry.pair343_close import describe

def audit_case(R,key):
 D=R/'stage375'/key;r=read(D/'B/result.json');b=read(D/'native-budget.json');data=[json.loads(s) for s in (D/'B/trace-private.jsonl').read_text().splitlines()];z=np.load(D/'B/frames-actions-private.npz')
 valid=not r['technical_error'] and r['comparison_valid'];counts=dict(known_supported_direct_contexts=0,known_birth_supported_retained_contexts=0,supported_direct_losses=0,supported_retained_losses=0,missing_birth_GT_direct=0,missing_birth_GT_retained=0,unresolved_births=0);fallback_intervals=accepted_intervals=transported_fallback_points=0;maxerr=0.;nodes=[]
 if valid:
  assert read(D/'reset-qualification.json')['passed'] and r['native_actions']==b['actions']==len(data)==len(z['actions'])==b['actor_act_calls']==b['actor_commit_calls']<=2000 and len(z['frames_uint8'])==len(data)+1 and b['resets']==b['actor_resets']==1
  assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50 and r['raw_reset_ticks']==51 and r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'];assert all(not x['terminated'] and not x['truncated'] for x in data[:-1])
  for i,x in enumerate(data):
   t=x['tracker'];assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks'];reconstructed,lineage,transported=advance(t['before'],t['direct'],t['affine'],t['previous_yaw'],t['current_yaw'],t['current_speed'],True)
   a=np.asarray(reconstructed).reshape(-1,4);v=np.asarray(t['after']).reshape(-1,4);assert a.shape==v.shape;err=float(np.max(np.abs(a-v))) if a.size else 0.;maxerr=max(maxerr,err);assert err<=1e-12
   if t['before'] and t['affine'] is None:fallback_intervals+=1;transported_fallback_points+=len(t['before'])
   if t['affine'] is not None:accepted_intervals+=1
   e=x['routing_evidence'];assert not e['removed_indices'] and e['full_hazards']==t['after'] and [list(h[:3]) for h in t['after']]==[list(h) for h in e['routing_hazards']]
   newnodes=[]
   for j,parent in enumerate(lineage):
    if parent>=0:node=nodes[parent]
    else:
     lab,idx=label(t['direct'][-parent-1],x['pre_physical']);node=dict(birth_label=lab,fixture_index=idx)
     if lab=='unresolved':counts['unresolved_births']+=1
    newnodes.append(node);age=t['after'][j][3]
    if node['birth_label']=='fixture_supported':counts['known_supported_direct_contexts' if age==0 else 'known_birth_supported_retained_contexts']+=1
    if node['birth_label']=='missing_GT':counts['missing_birth_GT_direct' if age==0 else 'missing_birth_GT_retained']+=1
   nodes=newnodes
  if r['completed']:assert not r['actual_DNF'] and not r['censored'] and r['stop_reason']=='official_finish' and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
  if r['protocol_stop']:assert b['actions']==2000 and r['censored'] and not r['actual_DNF']
 support=dict(audited=bool(valid),passed=bool(valid),**counts,all_tracked_hazards_passed_to_routing=bool(valid),tracking_reconstruction_max_error=maxerr,fallback_intervals_with_retained_points=fallback_intervals,fallback_point_transports=transported_fallback_points,accepted_optical_intervals=accepted_intervals,scope='Posthocbirthcirclelabels,notsemantic/occlusiontruth. No birthfilter/historyexists:allhazardsretainedinrouting. No positive_historytransferscomputed/not365. Unknownbirthsnotfalse-positiveGT.')
 assert valid
 save(D/'support-gate.json',support);save(D/'outcome-summary.json',describe(data,r));return support

def run(R):
 D=R/'stage375';p=verify(R,True);assert not (D/'batch-opening.json').exists();save(D/'batch-opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_sha256=sha(Path(__file__))));status=dict(stage=375,attempted=[],evaluated=[],stop_reason=None,all17_evaluated=False);wall,cpu=time.perf_counter(),time.process_time()
 try:
  for key in p['order']:
   verify(R,True);assert 34000-read(D/'native-budget.json')['actions']>=2000
   F=D/key;assert not F.exists();F.mkdir(mode=0o700);save(F/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=2000,reset_cap=1));status['attempted'].append(key);save(D/'batch-status.json',status)
   episode(R,key);r=read(F/'B/result.json')
   if r['technical_error']:raise RuntimeError(r['technical_error'])
   gate=audit_case(R,key);status['evaluated'].append(key);save(D/'batch-status.json',status);print(json.dumps(dict(stage=375,condition=key,actions=r['native_actions'],completed=r['completed'],lap_ms=r['lap_ms'],actual_DNF=r['actual_DNF'],support_gate=gate['passed'])),flush=True)
   if not gate['passed']:status['stop_reason']='supported_point_loss';break
   if not r['completed'] and not r['actual_DNF'] and not r['protocol_stop']:status['stop_reason']='other_official_truncation';break
  else:status['all17_evaluated']=True;status['stop_reason']='all17_evaluated'
 except BaseException as e:
  status['stop_reason']='technical_or_integrity_error';status['technical_error']=type(e).__name__+': '+str(e);save(D/'batch-error-private.json',dict(error=status['technical_error'],traceback=__import__('traceback').format_exc()))
 status.update(wall_s=time.perf_counter()-wall,runner_CPU_s=time.process_time()-cpu,budget=read(D/'native-budget.json'),unmeasured=[k for k in p['order'] if k not in status['attempted']]);save(D/'batch-status.json',status);print(json.dumps(status),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
