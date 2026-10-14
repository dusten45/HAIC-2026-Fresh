"""One structural endpoint expansion; saved-input gate then6/conditional12TRAIN."""
import argparse,datetime,json,time,zipfile,hashlib
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.completion297_search import metrics,diagnose

def package(p,D,label,on):
 G=Path(__file__).resolve().parent.parent;F=D/label;F.mkdir(mode=0o700)
 with zipfile.ZipFile(p['baseline296']['config']['archive_path']) as z:members={n:z.read(n) for n in z.namelist()}
 original=members['retry/connected_agent.py'];s=original.decode();needle='    candidates = route_candidates(image, obstacles)\n    path, LAST_CONNECTION_EVALUATION = choose_route(candidates, speed, previous_steer)\n';assert s.count(needle)==1
 replacement='''    global LAST_EXPANSION
    from retry.endpoints311_routes import expand, choose
    legacy = route_candidates(image, obstacles)
    if ADDITIONS_ON:
        candidates, LAST_EXPANSION = expand(image, obstacles, legacy, routing_problem)
        path, LAST_CONNECTION_EVALUATION = choose(candidates, speed, previous_steer, route_target, len(legacy))
    else:
        LAST_EXPANSION = dict(legacy_count=len(legacy), added_count=0, tree_runs=0, goal_row=None, terminal_columns=[])
        path, LAST_CONNECTION_EVALUATION = choose_route(legacy, speed, previous_steer)
'''
 s=s.replace(needle,replacement);s+='\nADDITIONS_ON = '+repr(on)+'\n';members['retry/connected_agent.py']=s.encode();members['retry/endpoints311_original.py']=original;members['retry/endpoints311_routes.py']=(G/'retry/endpoints311_routes.py').read_bytes();q=F/'policy.zip'
 with zipfile.ZipFile(q,'x',compression=zipfile.ZIP_DEFLATED) as z:
  for n,b in sorted(members.items()):item=zipfile.ZipInfo(n,date_time=(2026,10,9,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED;item.external_attr=0o100644<<16;z.writestr(item,b)
 q.chmod(0o600);cfg=dict(p['baseline296']['config'],archive_path=str(q),archive_sha256=sha(q),members_sha256={n:hashlib.sha256(b).hexdigest() for n,b in members.items()},worker_path=str(G/'retry/endpoints311_worker.py'),worker_sha256=sha(G/'retry/endpoints311_worker.py'));save(F/'candidate-config.json',cfg);return cfg

def prepare(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage311';assert not D.exists(),'Existing311:no duplicate';D.mkdir(mode=0o700);v=read(R/'project-effective-budget-v319.json');assert v['research_remaining']==5657;old=read(R/'stage299/plan.json');screen=['T2950','T2953','T2956','T2959','O0','O2'];p=dict(stage=311,deadline_utc='2026-10-16T10:01:55+00:00',baseline296=old['baseline296'],base_controller_theta=old['baseline296']['theta'],cases=old['cases'],initial_observations=old['initial_observations'],roads=old['roads'],screen=screen,extension=[r for r in old['roads'] if r not in screen],sandbox_path=old['sandbox_path'],phase_caps=dict(screen=5657,extension=5657),native_cap=5657,rule='Keepalllegacy candidates; oneextraDijkstra tree withoriginaledge1+2/d onunchangedstart/mask/cornerconditions, reconstructallotherreachablecolumns atunchangedfarthestgoalrow; existingcoef1/2/1 unchanged. Gapglobalminimum withlegacygap sharedoffset, retainlegacyrank including existing1e-9zerogap convention; exacttieslegacyfirst thenaddedcolumn.',prior_review='163existing archivedroute_candidates functions,2bodies:162 originalleft/rightloop,1continuityannotation; no allterminalcol predecessor-tree expansion.134/135samegoalcol alternatives,171tie,304anchor,310costweights;thischangescandidatecapacityonly.',preflight='Allstored306 sixroad actualobservations, offidentity action/features/memory and onchangedroute/action/latency; no native ifno actualchange.',screen_gate='Onlyfixedcandidate sixTRAINonce vs296cached5/6; greatercompletioncount orsamecountstrictlyfastercommonmean =>remaining12once. UnknownnotDNF,no retune/replacement/DEV/adoption.',stop='5657native combined,deadline,technical/censor; preserveunobserved andclose withoutreserve.');p['off_config']=package(p,D,'additions-off',False);p['on_config']=package(p,D,'additions-on',True);names=['endpoints311_stage.py','endpoints311_routes.py','endpoints311_worker.py','endpoints311_episode.py','endpoints311_jobs.py'];sources=[G/'retry'/n for n in names]+[Path(p['baseline296']['config']['archive_path']),Path(p['off_config']['archive_path']),Path(p['on_config']['archive_path']),R/'project-effective-budget-v319.json'];p['hashes']={str(q):sha(q) for q in sources};save(D/'previous-current-champion.json',read(R/'current-champion.json'));save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'budget.json',dict(actions=0,screen=0,extension=0));print('311registered savedinputgate thenfixed6/conditional12, native5657,noDEV',flush=True)
def verify(D):
 p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
 for q,h in p['hashes'].items():assert sha(q)==h,q
 return p

def preflight(R):
 from retry.frozen_composite_runtime import prepare as actor
 D=R/'stage311';p=verify(D);assert not (D/'preflight-opening.json').exists();save(D/'preflight-opening.json',dict(epoch=time.time()));records=[];totalchanged=0
 for road in p['screen']:
  F=D/'preflight'/road;F.mkdir(parents=True,mode=0o700);cache=np.load(R/'stage306/collection'/road/'observations-actions-private.npz');rows=[json.loads(s) for s in (R/'stage306/collection'/road/'trace-private.jsonl').read_text().splitlines()];workers=[];data=[];times=[[],[]];computes=[[],[]];cpu=[0.,0.]
  try:
   for i,k in enumerate(['off_config','on_config']):workers.append(actor(p[k],F/str(i),p['sandbox_path']));workers[-1].call('reset',cache['observations'][0])
   for obs,base,r in zip(cache['observations'],cache['actions'],rows):
    responses=[]
    for i,w in enumerate(workers):
     x,ms=w.call('act',obs);responses.append(x);times[i].append(ms);computes[i].append(x['act_compute_ms']);ack,_=w.call('commit',np.array(x['action'],np.float32));cpu[i]=ack['actor_cumulative_CPU_s']
    off,on=responses;assert off['action']==base.tolist() and off['features']==r['features'] and off['state']['previous_steer']==r['memory'] and not off['route_audit']['path_changed'];assert on['route_audit']['existing_rank_preserved'];change=on['action']!=off['action'];totalchanged+=change;data.append(dict(step=r['step'],action_changed=change,off_action=off['action'],on_action=on['action'],on_route_audit=on['route_audit']))
  finally:
   reaping=[w.close() for w in workers];assert all(r['process_reaped'] and r['actor_pids_absent'] for r in reaping)
  save(F/'comparisons-private.json',data);records.append(dict(road=road,actions=len(data),off_exact=True,on_action_changes=sum(x['action_changed'] for x in data),on_path_changes=sum(x['on_route_audit']['path_changed'] for x in data),added_selected_actions=sum(x['on_route_audit']['selected_added'] for x in data),candidate_count_range=[min(x['on_route_audit']['candidate_count'] for x in data),max(x['on_route_audit']['candidate_count'] for x in data)],added_count_max=max(x['on_route_audit']['added_count'] for x in data),actor_compute_ms=[dict(median=float(np.median(x)),p95=float(np.percentile(x,95)),max=float(max(x))) for x in computes],IPC_ms=[dict(median=float(np.median(x)),p95=float(np.percentile(x,95)),max=float(max(x))) for x in times],actor_CPU_s=cpu));print(json.dumps({k:records[-1][k] for k in ['road','actions','on_action_changes','on_path_changes','candidate_count_range']}),flush=True)
 save(D/'preflight-receipt.json',dict(records=records,changed_actions=totalchanged,actual_change=totalchanged>0,new_native=0,new_source_physics_ticks=0,wall_s=time.time()-read(D/'preflight-opening.json')['epoch']));print('311preflight complete; actualchange '+str(totalchanged),flush=True)

def evaluate(D,p,roads,phase):
 from retry.endpoints311_jobs import jobs
 rr=[];t=p['base_controller_theta']
 for i in range(0,len(roads),2):
  entries=[dict(folder=str(D/'evaluations'/phase/r),road=r,case=p['cases'][r],initial_observation_sha256=p['initial_observations'].get(r),config=p['on_config'],ceiling=float(45*np.exp(t[5])),steering_gain=float(np.exp(t[2]))) for r in roads[i:i+2]];out=jobs(D,p,entries,phase);rr+=out;save(D/(phase+'-partial.json'),rr)
  if len(out)<len(entries) or any(x['censored'] or x['technical_error'] for x in out):break
 return rr

def run(R):
 D=R/'stage311';p=verify(D);pre=read(D/'preflight-receipt.json');assert not (D/'opening.json').exists();save(D/'opening.json',dict(epoch=time.time()));screen=[];extension=[];gate=False;error=None
 try:
  if pre['actual_change']:
   screen=evaluate(D,p,p['screen'],'screen');assert len(screen)==6 and not any(x['censored'] or x['technical_error'] for x in screen),'Incomplete screen/no forcedgate';base=[r for r in p['baseline296']['results'] if r['road'] in p['screen']];d=diagnose(screen,base);nc=sum(r['completed'] for r in screen);gate=nc>5 or(nc==5 and d['common_mean_delta_ms'] is not None and d['common_mean_delta_ms']<0);save(D/'screen-gate.json',dict(passed=bool(gate),completions=nc,baseline_completions=5,against296=d));print(json.dumps(dict(screen_completions=nc,gate=bool(gate),against296=d)),flush=True)
   if gate:extension=evaluate(D,p,p['extension'],'extension')
 except BaseException as e:error=type(e).__name__+': '+str(e);print(error,flush=True)
 save(D/'outcome-private.json',dict(screen=screen,extension=extension,screen_gate=bool(gate),preflight_actual_change=pre['actual_change'],technical_error=error,unobserved=[r for r in p['roads'] if r not in [x['road'] for x in screen+extension]],wall_s=time.time()-read(D/'opening.json')['epoch']));print('311execution closed',flush=True)

def close(R):
 G=Path(__file__).resolve().parent.parent;D=R/'stage311';p=verify(D);o=read(D/'outcome-private.json');b=read(D/'budget.json');assert not (D/'cost.json').exists();files=list((D/'evaluations').glob('*/*/result.json'));rr=[read(q) for q in files];assert sum(r['native_actions'] for r in rr)<=b['actions']<=5657;signals=[]
 for q,r in zip(files,rr):
  assert r['reaping']['process_reaped'] and r['reaping']['actor_pids_absent'];rows=[json.loads(s) for s in (q.parent/'trace-private.jsonl').read_text().splitlines()];assert len(rows)==r['native_actions'];assert all(x['route_audit']['existing_rank_preserved'] and x['route_audit']['tree_runs']<=1 for x in rows);signals.append(dict(phase=q.parent.parent.name,road=r['road'],actions=len(rows),path_changed_actions=sum(x['route_audit']['path_changed'] for x in rows),added_selected_actions=sum(x['route_audit']['selected_added'] for x in rows),candidate_count_max=max(x['route_audit']['candidate_count'] for x in rows)))
 prior=R/'project-effective-budget-v319.json';v=read(prior);cost=dict(stage=311,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),new_wrapper_actions=b['actions'],native_cap=5657,screen_native=b['screen'],extension_native=b['extension'],new_official_runs=len(rr),new_source_physics_ticks=0,new_fits=0,new_paid_resources=0,raw_step_ticks=sum(x['raw_step_ticks'] for x in rr),raw_reset_ticks=sum(x['raw_reset_ticks'] for x in rr),runner_CPU_s=sum(x['runner_CPU_s'] for x in rr),actor_CPU_s=sum(x['actor_CPU_s'] for x in rr),total_native_wall_s=o['wall_s'],B_operating_cap=1330000,actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions']+b['actions'],research_remaining=v['research_remaining']-b['actions'],final_reserved_actions=84000,final_reserve_used=0);save(D/'cost.json',cost);v.update(version=320,prior_budget_path=str(prior),prior_budget_sha256=sha(prior),B_increment=0,cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),actual_cumulative_wrapper_actions=cost['actual_cumulative_wrapper_actions'],research_remaining=cost['research_remaining'],stage311_new_wrapper_actions=b['actions']);assert not (R/'project-effective-budget-v320.json').exists();save(R/'project-effective-budget-v320.json',v);ledger=R/'experiment-cost-lines.jsonl';assert not any(json.loads(s).get('stage')==311 for s in ledger.read_text().splitlines())
 with ledger.open('a') as f:f.write(json.dumps(cost)+'\n')
 assert sha(R/'current-champion.json')==sha(D/'previous-current-champion.json');safe=lambda x:{k:x.get(k) for k in ['road','completed','actual_DNF','censored','technical_error','lap_ms','damage','native_actions','retire_reason']};full=o['screen']+o['extension'];fully=len(full)==18 and not any(x['technical_error'] or x['censored'] for x in full);base=[r for r in p['baseline296']['results'] if r['road'] in p['screen']];pub=dict(stage=311,rule=p['rule'],prior_review=p['prior_review'],preflight=read(D/'preflight-receipt.json'),screen=[safe(r) for r in o['screen']],screen_baseline=[safe(r) for r in base],screen_gate=o['screen_gate'],screen_diagnostic=diagnose(o['screen'],base) if len(o['screen'])==6 and not any(x['technical_error'] or x['censored'] for x in o['screen']) else None,extension=[safe(r) for r in o['extension']],full18_summary=dict(**metrics(full),against296=diagnose(full,p['baseline296']['results'])) if fully else None,unobserved=o['unobserved'],signals=signals,technical_error=o['technical_error'],cost=cost,champion296_maintained=True,DEV_opened=False,HOLDOUT_opened=False,SEALED_opened=False,automatic_next_experiment=False);save(G/'retry/endpoints311_result.json',pub);print(json.dumps(dict(screen=pub['screen'],gate=pub['screen_gate'],full18_summary=pub['full18_summary'],cost=cost,technical_error=o['technical_error']),indent=2))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('phase',choices=['prepare','preflight','run','close']);a.add_argument('--private-root',type=Path,required=True);x=a.parse_args();globals()[x.phase](x.private_root.resolve())
