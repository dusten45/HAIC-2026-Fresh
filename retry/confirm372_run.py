"""Original AB/BA paired confirmation; posthoc support gate stops remaining runs."""
import datetime,json,time
from pathlib import Path
import sys
import numpy as np
from retry.path271_run import read,save,sha
from retry.confirm372_stage import verify
from retry.confirm372_episode import run as episode
from retry.confidence341_run import label
from retry.history365_logic import advance_evidence
from retry.lineage339_audit import track
from retry.episode367_stage import legacy_support
from retry.package349_run import projection
from retry.pair343_close import describe

def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]
def uid(tag):return tuple(map(int,tag.split(':')))
def audit_case(R,key,p):
 D=R/'stage372'/key;r=read(D/'B/result.json');data=rows(D/'B/trace-private.jsonl');b=read(D/'B/native-budget.json');z=np.load(D/'B/frames-actions-private.npz');used=b['actions'];assert r['technical_error'] is None and r['comparison_valid'] and read(D/'B/reset-qualification.json')['passed']
 assert used==r['native_actions']==len(data)==len(z['actions'])==b['actor_act_calls']==b['actor_commit_calls']<=b['total_cap']<=2000 and len(z['frames_uint8'])==used+1 and b['resets']==b['actor_resets']==1
 assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50 and r['raw_reset_ticks']==51;assert all(not x['terminated'] and not x['truncated'] for x in data[:-1]) and r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent']
 if r['completed']:assert not r['actual_DNF'] and not r['censored'] and r['stop_reason']=='official_finish' and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
 if r['protocol_stop']:assert used==b['total_cap'] and r['censored'] and not r['completed'] and not r['actual_DNF']
 lineage=track(data);prev=[];nodes={};direct=retained=missingd=missingr=0;losses=[];low=[];held=[];preserved=[];edges=[]
 for i,x in enumerate(data):
  assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks'];sr=advance_evidence(x['tracker'],prev,i+1,z['frames_uint8'][i].astype(np.float32)/255);assert sr==x['support_record'];prev=sr['after']
  for item in sr['births']:
   ident=tuple(item['uid']);lab,idx=label(item['point'],x['pre_physical']);parents=[a for a in lineage['records'][i]['associations'] if uid(a['new_tag'])==ident];parent=nodes.get(uid(parents[0]['old_tag'])) if len(parents)==1 else None;inherit=bool(parent and parent['positive']);own=item['raw_road_neighbors']>0;assert item['positive_history']==bool(own or inherit);origins=[dict(label=lab,fixture_index=idx)] if own else parent['origins'] if inherit else [];nodes[ident]=dict(label=lab,fixture_index=idx,positive=item['positive_history'],origins=origins)
   if item['low']:low.append(dict(action=i+1,uid=item['uid'],positive_history=item['positive_history'],raw_road_neighbors=item['raw_road_neighbors'],area_pixels=item['component_area'],posthoc_label=lab))
   if inherit:edges.append(dict(action=i+1,uid=item['uid'],parent_uid=list(uid(parents[0]['old_tag'])),low_birth=item['low'],ambiguous=lab!='fixture_supported' or any(o['label']!='fixture_supported' for o in parent['origins']),confirmed_distinct_supported_fixture_transfer=bool(lab=='fixture_supported' and any(o['label']=='fixture_supported' and o['fixture_index']!=idx for o in parent['origins']))))
  e=x['routing_evidence'];wanted=[j for j,(h,item) in enumerate(zip(x['tracker']['after'],sr['after'])) if item['low'] and h[3]>0 and not item['positive_history']];assert e['removed_indices']==wanted and e['full_hazards']==x['tracker']['after'] and x['features'][11]==len(e['full_hazards'])
  for j,(h,item) in enumerate(zip(x['tracker']['after'],sr['after'])):
   lab=nodes[tuple(item['uid'])]['label'];excluded=j in wanted
   if lab=='fixture_supported':
    if h[3]==0:direct+=1
    else:retained+=1
    if excluded:losses.append(dict(action=i+1,uid=item['uid'],age=h[3],kind='direct' if h[3]==0 else 'retained'))
   if lab=='missing_GT':
    if h[3]==0:missingd+=1
    else:missingr+=1
   if h[3]==0:assert not excluded
   if excluded:held.append(dict(action=i+1,uid=item['uid'],age=h[3]))
   if item['low'] and h[3]>0 and item['positive_history']:preserved.append(dict(action=i+1,uid=item['uid'],age=h[3],posthoc_label=lab))
 wrong_low=[e for e in edges if e['low_birth'] and e['confirmed_distinct_supported_fixture_transfer']]
 gate=dict(passed=not losses and not wrong_low,confirmed_wrong_low_transfers=wrong_low,technical_error=None,known_supported_direct_contexts=direct,known_birth_supported_retained_contexts=retained,supported_direct_losses=sum(x['kind']=='direct' for x in losses),supported_retained_losses=sum(x['kind']=='retained' for x in losses),losses=losses,missing_birth_GT_direct=missingd,missing_birth_GT_retained=missingr,low_births=low,retained_exclusions=held,preserved_low_retained=preserved,all_positive_transfer_edges=len(edges),ambiguous_transfer_edges=sum(e['ambiguous'] for e in edges),confirmed_distinct_supported_fixture_transfers=sum(e['confirmed_distinct_supported_fixture_transfer'] for e in edges),ambiguous_low_birth_edges=sum(e['ambiguous'] and e['low_birth'] for e in edges),prior62_ambiguities_and_missing_GT_still_unresolved=True,scope='Thisactualconditionposthocbirthcirclelabels;noGTtoactor,notsemanticorocclusiontruth.')
 save(D/'positive-transfer-edges-private.json',edges);save(D/'support-gate.json',gate);save(D/'outcome-summary.json',describe(data,r));return gate

def audit_arm(R,key,arm):
 F=R/'stage372'/key/arm;r=read(F/'result.json');data=rows(F/'trace-private.jsonl');b=read(F/'native-budget.json');z=np.load(F/'frames-actions-private.npz');assert r['technical_error'] is None and r['comparison_valid'] and read(F/'reset-qualification.json')['passed']
 assert r['native_actions']==len(data)==len(z['actions'])==b['actions']==b['actor_act_calls']==b['actor_commit_calls']<=2000 and len(z['frames_uint8'])==len(data)+1 and b['resets']==b['actor_resets']==1
 assert sum(x['raw_ticks'] for x in data)==r['raw_step_ticks']==r['raw_counter_at_stop']-50 and r['raw_reset_ticks']==51 and r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'];assert all(not x['terminated'] and not x['truncated'] for x in data[:-1])
 for x in data:assert x['executed']==x['returned_action'] and x['nominal_memory']==x['policy']['previous_steer'] and np.float32(x['nominal_memory'])==np.float32(x['executed'][0]) and len(x['raw_observations'])==x['raw_ticks']
 if r['completed']:assert not r['actual_DNF'] and not r['censored'] and r['stop_reason']=='official_finish' and r['lap_ms']==round((r['finish']['finish_time_s']-r['postreset_start_time'])*1000)
 if r['protocol_stop']:assert b['actions']==2000 and r['censored'] and not r['actual_DNF']
 save(F/'outcome-summary.json',describe(data,r));save(F/'saved-evidence-check.json',dict(passed=True,own_pixels_full_controls_normal_memory=True,raw_ticks_and_frames_accounted=True,process_reaped=True))
 if arm=='B':return audit_case(R,key,verify(R))
 return dict(passed=True,scope='296doesnotuselowroutingfilter;legality/integrityonly,candidatesupportgateappliesto365.')

def audit_pair(R,key):
 F=R/'stage372'/key
 for n in ['initial-scene-private.json','initial-RNG-private.json']:
  assert read(F/'A'/n)==read(F/'B'/n),n
 a=read(F/'A/reset-qualification.json');b=read(F/'B/reset-qualification.json')
 for n in ['geometry_sha256','physical_obstacles_sha256','initial_observation_sha256']:assert a[n]==b[n]
 save(F/'paired-initial-check.json',dict(passed=True,same_registered_case=True,initial_pixels_geometry_obstacles_physics_accessible_RNG_exact=True,GT_comparison_posthoc_only=True,hidden_solver_and_opencv_internal_RNG_not_directly_measured=True))

def append_query(D,value):
 with (D/'query-ledger-private.jsonl').open('a') as f:f.write(json.dumps(value,allow_nan=False)+'\n')

def run(R):
 D=R/'stage372';p=verify(R,True);binding=read(D/'cases-frozen-private.json');assert (D/'release-private.json').exists() and not (D/'batch-opening.json').exists();save(D/'batch-opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),runner_sha256=sha(Path(__file__))));status=dict(stage=372,attempted=[],evaluated=[],paired_evaluated=[],stop_reason=None,all24_evaluated=False);wall,cpu=time.perf_counter(),time.process_time()
 try:
  stop=False
  for key in binding['order']:
   F=D/key;assert not F.exists();F.mkdir(mode=0o700)
   for arm in binding['cases'][key]['arm_order']:
    verify(R,True);glob=read(D/'native-budget.json');assert 48000-glob['actions']>=2000
    A=F/arm;A.mkdir(mode=0o700);save(A/'native-budget.json',dict(actions=0,actor_act_calls=0,actor_commit_calls=0,resets=0,actor_resets=0,total_cap=2000,reset_cap=1));tag=key+'/'+arm;status['attempted'].append(tag);save(D/'batch-status.json',status)
    append_query(D,dict(event='claim',case=key,arm=arm,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),archive_sha256=p['configs'][arm]['archive_sha256'],plan_sha256=sha(D/'plan.json'),case_binding_sha256=sha(D/'cases-frozen-private.json')))
    episode(R,key,arm);r=read(A/'result.json');append_query(D,dict(event='durable_result',case=key,arm=arm,result_sha256=sha(A/'result.json'),actions=r['native_actions'],technical_error=r['technical_error']))
    gate=audit_arm(R,key,arm);status['evaluated'].append(tag);save(D/'batch-status.json',status);print(json.dumps(dict(stage=372,condition=key,arm=arm,actions=r['native_actions'],completed=r['completed'],lap_ms=r['lap_ms'],actual_DNF=r['actual_DNF'],gate=gate['passed'])),flush=True)
    if not gate['passed']:status['stop_reason']='supported_point_loss' if gate.get('losses') else 'confirmed_wrong_low_positive_transfer';stop=True;break
    if not r['completed'] and not r['actual_DNF'] and not r['protocol_stop']:status['stop_reason']='other_official_truncation';stop=True;break
   if stop:break
   audit_pair(R,key);status['paired_evaluated'].append(key);save(D/'batch-status.json',status)
  else:status['all24_evaluated']=True;status['stop_reason']='all24_evaluated'
 except BaseException as e:
  status['stop_reason']='technical_or_integrity_error';status['technical_error']=type(e).__name__+': '+str(e);save(D/'batch-error-private.json',dict(error=status['technical_error'],traceback=__import__('traceback').format_exc()))
 planned=[k+'/'+a for k in binding['order'] for a in binding['cases'][k]['arm_order']];status.update(wall_s=time.perf_counter()-wall,runner_CPU_s=time.process_time()-cpu,budget=read(D/'native-budget.json'),unmeasured=[k for k in planned if k not in status['attempted']]);save(D/'batch-status.json',status);print(json.dumps(status),flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
