"""Recover exact594 certificate input from stored records; no physics/native."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import hashlib,json,datetime
from dataclasses import asdict
from pathlib import Path
import retry.handoff562_model as d
from retry.durable568 import digest
from retry.clip561_core import atomic_write
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response595-private')
INPUTS=dict(rejection=Path('/workspace/haic-response594-private/certificate-rejected-candidate-040-private.json'),candidate=Path('/workspace/haic-response594-private/arm-candidate-private.json'),nativejournal=Path('/workspace/haic-response594-private/journal-private.jsonl'),oldcontract=G/'retry/cold594_contract.json',oldresult=G/'retry/cold594_result.json',oldaudit=G/'retry/cold594_audit.json',oldreview=G/'retry/cold594_rejection_review.json',tape=Path('/workspace/haic-response577-private/final-independent-tape-private.json'),static=Path('/workspace/haic-response515-private/collected-map-state-private.json'),paths=Path('/workspace/haic-response551-private/frozen-paths-private.json'),ledger=Path('/workspace/haic-response519-private/model-ledger-private.json'))
def short(r):return dict(planar=asdict(r.planar),center=r.center,current_contacts=r.current_contacts,floor=r.floor,skin=r.skin)
def run():
 D.mkdir(mode=0o700,exist_ok=False);atomic_write(D/'PREP_STARTED-private.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
 try:
  x=d.rd(INPUTS['rejection']);saved=d.rd(INPUTS['candidate']);c=d.rd(INPUTS['oldcontract']);r=d.rd(INPUTS['oldresult']);a=d.rd(INPUTS['oldaudit']);last=saved['raw_records'][-1];detail=x['detail'];nativechecks=dict(old_result_status=r['status']=='CANDIDATE_CERTIFICATE_REJECTED',all_old_pins=all(d.sha(Path(p) if Path(p).is_absolute() else G/p)==h for p,h in {**c['implementation_sha256'],**c['dependency_sha256']}.items()),old_input_pins=True,journal_pin=d.sha(INPUTS['nativejournal'])==a['input_sha256']['private_journal'],rejection_pin=d.sha(INPUTS['rejection'])==d.rd(INPUTS['oldreview'])['private_rejection_sha256'],root_hash=digest(x['root'])==detail['actual_start_sha256'],tracker_hash=digest(x['tracker'])==detail['actual_tracker_sha256'],visited_hash=digest(sorted(x['visited']))==detail['actual_visited_sha256'],last_index=last['phase']=='action' and last['action']==39 and len([q for q in saved['raw_records'] if q['phase']=='action'])==156,last_clock=last['time']==x['clock'],last_tracker=last['official_tracker']==x['tracker'],last_root_components=last['position']==x['root']['center'] and last['velocity']==x['root']['planar']['linear']['velocity'] and last['angle']==x['root']['planar']['angle'] and last['yaw']==x['root']['planar']['yaw'] and last['after_contacts']==x['root']['current_contacts'],visited_full=len(x['visited'])==len(set(x['visited']))==last['visited_tiles'],history=x['groups']=={g:[q['clipped'],q['samples']] for g,q in saved['summary']['force_groups'].items()},immutable_roads_proven_by_pinned_initial_identity=saved['summary']['initial_identity'] and all(q['effects']==[1.,1.,1.] and not q['errors'] for q in saved['raw_records']),expected_old48=detail['model_ticks']==48 and detail['certified_command_indices']==list(range(40,52)))
  for k in ['tape','static']:
   nativechecks['old_input_pins']&=d.sha(INPUTS[k])==c['input_sha256'][k]
  nativechecks['old_input_pins']&=d.sha(INPUTS['paths'])==c['input_sha256']['candidate_paths'] and d.sha(INPUTS['ledger'])==c['input_sha256']['ledger']
  if not all(nativechecks.values()):raise ValueError('MISSING_OR_MISMATCH_CHECKPOINT:'+str([k for k,v in nativechecks.items() if not v]))
  static=d.rd(INPUTS['static']);path=d.rd(INPUTS['paths'])['candidate'];root=d.load_root(dict(x['root'],roads=static['root']['roads']));nativechecks['roundtrip_root_exact']=digest(short(root))==detail['actual_start_sha256'];progress=last['station'];q=d.project(root.center,path,progress);nativechecks['stored_progress_exact']=q['s']==progress and q['distance']==last['path_error']
  expected=[];active=False
  for line in INPUTS['nativejournal'].open():
   event=json.loads(line)
   if event['kind']=='HOLD_RESERVE' and event['label']=='candidate' and event['next_hold']==40:active=True
   if active and event.get('label')=='candidate' and event['kind'] in ['BEFORE_MODEL_FORCE','MODEL_FORCE_VERDICT','BEFORE_MODEL_TICK','AFTER_MODEL_TICK']:expected.append(event)
  nativechecks['expected_model_events']=len(expected)==192 and all(sum(q['kind']==k for q in expected)==48 for k in ['BEFORE_MODEL_FORCE','MODEL_FORCE_VERDICT','BEFORE_MODEL_TICK','AFTER_MODEL_TICK'])
  if not all(nativechecks.values()):raise ValueError('MISSING_MODEL_PREFIX_OR_PROGRESS')
  checkpoint=dict(root=x['root'],roads_input_sha256=d.sha(INPUTS['static']),progress=progress,groups=x['groups'],tracker=x['tracker'],visited=x['visited'],clock=x['clock'],global_raw=156,next_hold=40)
  atomic_write(D/'checkpoint-private.json',checkpoint);atomic_write(D/'expected-model-events-private.json',expected)
  out=dict(study=595,status='EXACT_STORED_CERTIFICATE_CHECKPOINT_AVAILABLE',checks=nativechecks,checkpoint_sha256=d.sha(D/'checkpoint-private.json'),expected_events_sha256=d.sha(D/'expected-model-events-private.json'),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},geometry_used=1,path_projection_queries=1,new_source_ticks=0,new_force_calls=0,new_native_calls=0,checkpoint_scope='Exactsource-modelinputto594certifier,notnativeBox2Dsolvercheckpoint. root/tracker/visited/history/clockdirectlystored;progressfromlastnative raw156 station;immutable roadsfrompinnedstaticinput establishedby594initialfullidentity andunchangedmaterials. No estimatedstateornewnativeprefix.',CPU_s=time.process_time()-CPU,wall_s=time.perf_counter()-WALL)
 except BaseException as exc:
  out=dict(study=595,status='CHECKPOINT_BLOCKED_SOURCE0',error=type(exc).__name__+':'+str(exc),new_source_ticks=0,new_native_calls=0,CPU_s=time.process_time()-CPU,wall_s=time.perf_counter()-WALL)
 atomic_write(G/'retry/cause595_checkpoint_gate.json',out);print(json.dumps(out,indent=2));return out
if __name__=='__main__':run()
