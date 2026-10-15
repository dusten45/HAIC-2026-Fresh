"""All-input support/propagation audit then mechanically necessary paired replays."""
import json,time,sys
from pathlib import Path
import numpy as np
from retry.path271_run import read,save
from retry.history365_stage import verify
from retry.history365_logic import advance_evidence as advance_new
from retry.support342_logic import advance_evidence as advance_old
from retry.confidence341_run import observations,label
from retry.lineage339_audit import track
from retry.package349_run import cached,projection
from retry.probe338_stage import stack
from retry.frozen_composite_runtime import prepare,validate_response

def rows(path):return [json.loads(s) for s in Path(path).read_text().splitlines()]
def uid(tag):return tuple(map(int,tag.split(':')))
def preflight(R,p):
 D=R/'stage365';summaries=[];audits={};losses=[];wrong=[];N2ok=True
 for case in p['cases']:
  frames,records,gt=observations(case);expected=rows(case['expected_tracker']);lineage=track([dict(step=i+1,tracker=x['tracker']) for i,x in enumerate(expected)]);oldprev=[];newprev=[];nodes={};checks=[];changes=[];events=[];all_edges=[];direct=retained=missingd=missingr=0;directloss=retainedloss=0;protected=[]
  for i,frame in enumerate(frames):
   t=expected[i]['tracker'];old=advance_old(t,oldprev,i+1,frame.astype(np.float32)/255);new=advance_new(t,newprev,i+1,frame.astype(np.float32)/255);oldprev=old['after'];newprev=new['after']
   if 'support_record' in expected[i]:assert old==expected[i]['support_record']
   for birth in new['births']:
    ident=tuple(birth['uid']);lab,idx=label(birth['point'],gt.get(i));parents=[a for a in lineage['records'][i]['associations'] if uid(a['new_tag'])==ident];parent=nodes.get(uid(parents[0]['old_tag'])) if len(parents)==1 else None;inherited=bool(parent and parent['positive']);own=birth['raw_road_neighbors']>0;assert birth['positive_history']==bool(own or inherited)
    origins=[dict(label=lab,fixture_index=idx,uid=list(ident))] if own else parent['origins'] if inherited else []
    node=dict(label=lab,fixture_index=idx,positive=birth['positive_history'],origins=origins);nodes[ident]=node
    if inherited:
     transfer=dict(action=i+1,uid=list(ident),parent_uid=list(uid(parents[0]['old_tag'])),same_frame_parent=uid(parents[0]['old_tag'])[0]==i+1,distance_m=parents[0]['distance_m'],low_birth=birth['low'],current_label=lab,current_fixture_index=idx,positive_origin_labels=[o['label'] for o in parent['origins']],positive_origin_fixture_ids=sorted(set(o['fixture_index'] for o in parent['origins'] if o['label']=='fixture_supported')))
     transfer['confirmed_distinct_supported_fixture_transfer']=bool(lab=='fixture_supported' and any(o['label']=='fixture_supported' and o['fixture_index']!=idx for o in parent['origins']));transfer['unresolved_or_missing_transfer']=lab!='fixture_supported' or any(o['label']!='fixture_supported' for o in parent['origins']);all_edges.append(transfer)
     if birth['low']:
      events.append(transfer)
      if transfer['confirmed_distinct_supported_fixture_transfer']:wrong.append(dict(case=case['key'],**transfer))
   oldremoved=[j for j,(h,e) in enumerate(zip(t['after'],old['after'])) if h[3]>0 and e['low']];removed=[j for j,(h,e) in enumerate(zip(t['after'],new['after'])) if h[3]>0 and e['low'] and not e['positive_history']];supported=[]
   for j,(h,e) in enumerate(zip(t['after'],new['after'])):
    n=nodes[tuple(e['uid'])];kind='direct' if h[3]==0 else 'retained'
    if n['label']=='fixture_supported':
     if kind=='direct':direct+=1
     else:retained+=1
     supported.append(j)
     if j in removed:
      if kind=='direct':directloss+=1
      else:retainedloss+=1
      losses.append(dict(case=case['key'],action=i+1,uid=e['uid'],kind=kind))
    if n['label']=='missing_GT':
     if kind=='direct':missingd+=1
     else:missingr+=1
    if j in oldremoved and j not in removed:protected.append(dict(action=i+1,uid=e['uid'],age=h[3],label=n['label']))
   if oldremoved!=removed:changes.append(i+1)
   if case['key'] in p['mandatory_actor_cases'] and 127<=i+1<=129:
    critical=[j for j,e in enumerate(new['after']) if e['uid']==[121,0]];N2ok &= len(critical)==1 and critical[0] in removed and t['after'][critical[0]][3]==i+1-121
   checks.append(dict(old_record=old,new_record=new,old_removed=oldremoved,new_removed=removed,supported=supported))
  summary=dict(key=case['key'],cohort=case['cohort'],inputs=len(frames),known_supported_direct_contexts=direct,known_birth_supported_retained_contexts=retained,missing_birth_GT_direct=missingd,missing_birth_GT_retained=missingr,supported_direct_losses=directloss,supported_retained_losses=retainedloss,routing_changed_actions=changes,newly_preserved_retained=protected,inherited_low_births=events,all_positive_transfer_edges=len(all_edges),same_frame_positive_edges=sum(x['same_frame_parent'] for x in all_edges),distinct_supported_fixture_edges=sum(x['confirmed_distinct_supported_fixture_transfer'] for x in all_edges),ambiguous_transfer_edges=sum(x['unresolved_or_missing_transfer'] for x in all_edges),actor_replay_planned=bool(changes) or case['key'] in p['mandatory_actor_cases'])
  if summary['actor_replay_planned']:assert case['baseline_reference']
  summaries.append(summary);audits[case['key']]=checks;save(D/f"{case['key']}-preflight-private.json",dict(checks=checks,positive_transfer_edges=all_edges));print('365preflight',case['key'],len(frames),'routingchanges',len(changes),'losses',directloss+retainedloss,flush=True)
 result=dict(passed=not losses and not wrong and N2ok,cases=summaries,supported_losses=losses,confirmed_wrong_low_positive_transfers=wrong,N2critical_membership_preserved=bool(N2ok),selected_actor_cases=[x['key'] for x in summaries if x['actor_replay_planned']],scope='8140savedpointcontexts; GTposthocbirthcirclelabels. Distinctsupportedfixturelow-transferfails; unresolved/missingisnotnegativegroundtruth. No newruntimeGTfeature.')
 save(D/'preflight-private.json',result);return result,audits

def reference(case):
 if case['reference_format']=='cached':return cached(Path(case['baseline_reference']))
 return {i:dict(response=dict(action=x['returned_action'],features=x['features'],pixel_path=x['pixel_path'],delta_audit=x['audit'],tracker_record=x['tracker'],support_record=x['support_record'],routing_evidence=x['routing_evidence'],state=x['actor_state']),commit=dict(state=x['policy'],memory=x['nominal_memory'])) for i,x in enumerate(rows(case['baseline_reference']))}

def charge(D,key):
 p=read(D/'plan.json');b=read(D/'call-budget.json');caps=dict(actor_act_calls=p['budget']['actor_act_cap'],actor_commit_calls=p['budget']['actor_commit_cap'],actor_resets=p['budget']['actor_reset_cap']);assert b[key]<caps[key];b[key]+=1;save(D/'call-budget.json',b)

def run(R):
 D=R/'stage365';p=verify(R,True);assert not (D/'opening.json').exists();save(D/'opening.json',dict(saved_only=True));start,cpu=time.perf_counter(),time.process_time();receipts=[];pairs=[];error=None;pre=None
 try:
  pre,audits=preflight(R,p);assert pre['passed'],'support/propagation/N2preflightgatefailed'
  for case in p['cases']:
   if case['key'] not in pre['selected_actor_cases']:continue
   frames,_,_=observations(case);z=np.load(case['pixels']);saved=z['observations'][:case['count']] if 'observations' in z.files else None;expected=rows(case['expected_tracker']);ref=reference(case);baseline=[];variant=[]
   for mode in ['baseline','variant']:
    verify(R,True);F=D/case['key']/mode;F.mkdir(parents=True,mode=0o700);w=j=None;actor_cpu=0;n=0;t,cc=time.perf_counter(),time.process_time();arm_error=None
    try:
     w=prepare(p['configs'][mode],F/'cpu',p['sandbox_path']);save(F/'ready-private.json',w.ready);obs=saved[0] if saved is not None else stack(frames,0);charge(D,'actor_resets');r,_=w.call('reset',obs);validate_response(r,p['configs'][mode],obs,'reset');assert projection(r['state'])==projection(read(R/'stage349/candidate/reset-private.json')['state']);j=(F/'records-private.jsonl').open('x');(F/'records-private.jsonl').chmod(0o600)
     for i in range(case['count']):
      verify(R);obs=saved[i] if saved is not None else stack(frames,i);charge(D,'actor_act_calls');r,_=w.call('act',obs);actor_cpu=r['actor_cumulative_CPU_s'];n+=1;command=validate_response(r,p['configs'][mode],obs,'act');check=audits[case['key']][i];sr=check['old_record' if mode=='baseline' else 'new_record'];removed=check['old_removed' if mode=='baseline' else 'new_removed']
      assert r['tracker_record']==expected[i]['tracker'] and r['support_record']==sr and r['packaged_support_state']==sr['after'] and r['routing_evidence']['removed_indices']==removed
      if mode=='variant':assert not set(removed)&set(check['supported'])
      if mode=='baseline':
       old=ref[i]['response']
       for k in ['action','features','pixel_path','delta_audit','tracker_record','support_record','routing_evidence']:assert r[k]==old[k],(case['key'],i+1,k)
       assert projection(r['state'])==projection(old['state'])
      j.write(json.dumps(dict(index=i,response=r),allow_nan=False)+'\n');j.flush();charge(D,'actor_commit_calls');c,_=w.call('commit',command);actor_cpu=c['actor_cumulative_CPU_s'];assert not c['python_audit_denied_events'] and c['memory']==c['nominal_memory']==r['state']['previous_steer'] and np.float32(c['memory'])==command[0];j.write(json.dumps(dict(index=i,commit=c),allow_nan=False)+'\n');j.flush()
      if mode=='baseline':assert c['memory']==ref[i]['commit']['memory'] and projection(c['state'])==projection(ref[i]['commit']['state']);baseline.append(dict(response=r,commit=c))
      else:
       variant.append(dict(response=r,commit=c))
       if case['key'] in p['mandatory_actor_cases']:
        for k in ['action','features','pixel_path','delta_audit']:assert r[k]==baseline[i]['response'][k],(case['key'],i+1,'N2output',k)
        assert c['memory']==baseline[i]['commit']['memory'] and projection(c['state'])==projection(baseline[i]['commit']['state'])
     save(F/'qualified.json',dict(passed=True,inputs=n))
    except BaseException as e:arm_error=type(e).__name__+': '+str(e);raise
    finally:
     if j:j.close()
     reaping=w.close() if w else None;receipt=dict(key=case['key'],mode=mode,act_calls=n,actor_CPU_s=actor_cpu,wall_s=time.perf_counter()-t,runner_CPU_s=time.process_time()-cc,error=arm_error,reaping=reaping);save(F/'receipt.json',receipt);receipts.append(receipt)
   changes={k:[] for k in ['routing','path','target','features','full_control','nominal_memory','original_state_projection']}
   for i,(a,v) in enumerate(zip(baseline,variant)):
    x,y=a['response'],v['response'];flags=dict(routing=x['routing_evidence']['removed_indices']!=y['routing_evidence']['removed_indices'],path=x['pixel_path']!=y['pixel_path'],target=x['features'][:3]!=y['features'][:3],features=x['features']!=y['features'],full_control=x['action']!=y['action'],nominal_memory=a['commit']['memory']!=v['commit']['memory'],original_state_projection=projection(a['commit']['state'])!=projection(v['commit']['state']))
    for k,f in flags.items():
     if f:changes[k].append(i+1)
   item=dict(key=case['key'],inputs=case['count'],changes=changes,baseline_historical_reproduced=True)
   if case['key'] in ['N2_337','N2_340']:
    old=cached(R/f"stage342/{case['key']}/baseline/records-private.jsonl");diffs={k:[] for k in ['path','target','full_control','steering']}
    for i,v in enumerate(variant):
     a,b=old[i]['response'],v['response'];flags=dict(path=a['pixel_path']!=b['pixel_path'],target=a['features'][:3]!=b['features'][:3],full_control=a['action']!=b['action'],steering=a['action'][0]!=b['action'][0])
     for k,f in flags.items():
      if f:diffs[k].append(i+1)
    assert diffs['path']==[127,128,129] and diffs['target']==[128,129] and diffs['full_control'][0]==127 and diffs['steering'][0]==128;item['N2_same_input_no_filter_historical_differences']=diffs
   pairs.append(item);save(D/'pairs-so-far.json',pairs);print('365pair',case['key'],changes,flush=True)
  verify(R,True)
 except BaseException as e:error=type(e).__name__+': '+str(e);save(D/'failure-private.json',dict(error=error,traceback=__import__('traceback').format_exc()))
 result=dict(passed=error is None,error=error,preflight_passed=pre['passed'] if pre else False,pairs=pairs,receipts=receipts,calls=read(D/'call-budget.json'),wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=sum(x['actor_CPU_s'] for x in receipts),new_native=0);save(D/'run-result.json',result);print('365result',error or 'passed',flush=True)
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
