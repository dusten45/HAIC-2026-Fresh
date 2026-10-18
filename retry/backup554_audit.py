"""Read-only554 feasibility/proposal/execution/effect audit and frozen refs."""
import hashlib,json,math,subprocess,time
from pathlib import Path
from types import SimpleNamespace
from retry.backup554_control import Planner
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response554-private')
def finite(x):
 if isinstance(x,float):return math.isfinite(x)
 if isinstance(x,list):return all(finite(a) for a in x)
 if isinstance(x,dict):return all(finite(a) for a in x.values())
 return True

def run():
 cpu=time.process_time();wall=time.perf_counter();rd=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=rd(G/'retry/backup554_contract.json');r=rd(G/'retry/backup554_pilot_result.json');e=rd(D/'entry-private.json');paths=rd(D/'frozen-paths-private.json');data=rd(D/'fixed-segment-candidate-private.json');initial=rd(D/'pilot-initial551-feedback-identity-private.json');checks=dict(source_pins=all(sha(G/p)==h for p,h in c['source_sha256'].items()),input_pins=all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items()),contract_pin=rd(D/'pilot-STARTED.json')['contract_sha256']==sha(G/'retry/backup554_contract.json'),same_segment=sha(D/'entry-private.json')==rd(G/'retry/dynamic553_preparation.json')['entry_sha256'],initial_feedback_exact551=initial['exact_saved551_state_prefix'] and initial['full_feedback_recomputed'] and initial['raw_states']==28,finite=finite(data),initialization_executed=True)
 mock=SimpleNamespace(paths=paths);planner=Planner(mock,e);old=e['root'];h=e['history'].copy();minimum=float('inf');peak=over=maxold=body=patherr=0.;maxclip=h[0]/h[1];cross={};plan_checks=[];mode_counts={};records_by_index={};before_by_index={};baseline=data['summary'];rejections={};accepted=regenfailed=retainedpassed=0;curve=None
 for row in data['trace']:
  if row['raw']==1:before_by_index[row['index']]=old
  records_by_index.setdefault(row['index'],[]).append(row);v=math.hypot(*row['root_without_roads']['planar']['linear']['velocity']);minimum=min(minimum,row['margin']);peak=max(peak,max(z['ratio'] for z in row['forces']));over=max(over,v-row['target']);maxold=max(maxold,v-row['old_target']);body=max(body,row['body_speed']);patherr=max(patherr,row['path_error']);h[0]+=sum(z['clipped'] for z in row['forces']);h[1]+=4;maxclip=max(maxclip,h[0]/h[1])
  for name,gate in [('gate',e['gate']),('return',e['return_gate'])]:
   dot=lambda p:sum((p[j]-gate['point'][j])*gate['tangent'][j] for j in range(2));a,b=dot(old['center']),dot(row['root_without_roads']['center'])
   if name not in cross and a<0<=b:
    frac=-a/(b-a);n=sum(len(z) for z in records_by_index.values())-1;vel=[old['planar']['linear']['velocity'][j]+frac*(row['root_without_roads']['planar']['linear']['velocity'][j]-old['planar']['linear']['velocity'][j]) for j in range(2)];cross[name]=dict(lower_s=.02*n,upper_s=.02*(n+1),time_s=.02*(n+frac),speed=math.hypot(*vel))
  old=row['root_without_roads']
 from retry.plan513_model import load_root
 static=rd(Path('/workspace/haic-response515-private/collected-map-state-private.json'));before_history=e['history'].copy()
 for cmd in data['commands']:
  if 'action' not in cmd:continue
  d=cmd['detail'];mode=d['mode'];mode_counts[mode]=mode_counts.get(mode,0)+1;rows=records_by_index[cmd['index']]
  if 'plan_number' in d:
   p=rd(D/f'plan-pilot-{d["plan_number"]:03d}-private.json');state=before_by_index[cmd['index']];finger=hashlib.sha256(json.dumps(state,sort_keys=True).encode()).hexdigest();ok=bool(finger==p['before_sha256']==d['full_state_sha256'] and before_history==p['history'] and p['controls'][0]==cmd['action'] and p['fresh_selected_replay_identical']);ok &= json.dumps([z['root_without_roads'] for z in rows],sort_keys=True)==json.dumps([z['root_without_roads'] for z in p['states'][:len(rows)]],sort_keys=True)
   for row in rows:
    root=load_root(dict(row['root_without_roads'],roads=static['root']['roads']));ok &= abs(planner.ref(root,row['progress'],p['curve'])-row['target'])<1e-12
   if p['curve'] is not None:ok &= max(z[1] for z in p['curve'])<=8100+1e-10
   if mode=='ACCEPTED_STATEFUL_RETIMING':
    accepted+=1;end=p['states'][3];expected=planner.compressed_curve(curve,state_s if 'state_s' in locals() else e['progress'],end['progress'],end['speed']);ok &= [list(z) for z in expected]==p['curve']
   curve=p['curve'];plan_checks.append(ok)
   reg=p['regenerated'];ret=p['retained_revalidation'];pro=p['proposal'];regenfailed+=bool(reg and not reg['ok']);retainedpassed+=bool(ret and ret['ok'])
   if pro and not pro['ok']:rejections[pro['reason']]=rejections.get(pro['reason'],0)+1
  for row in rows:before_history[0]+=sum(z['clipped'] for z in row['forces']);before_history[1]+=4
  state_s=rows[-1]['progress']
 checks['all_committed_refs_and_plan_states']=all(plan_checks) and bool(plan_checks);checks['all_raw_bounds']=minimum>=.5 and peak<=1.059 and over<=4.85 and body<100 and patherr<=3 and maxclip<=.1;checks['raw_counts']=len(data['trace'])==r['case']['raw_ticks'];checks['reported_metrics']=all(abs(a-b)<1e-12 for a,b in [(minimum,r['case']['min_margin_m']),(maxclip,r['case']['max_cumulative_clipping_fraction']),(peak,r['case']['force_groups']['running']['peak'])]);checks['crossing_replay']=all(name in cross and all(abs(z[k]-cross[name][k])<1e-12 for k in ['lower_s','upper_s','time_s','speed']) for name,z in r['case']['crossings'].items());gains={};speedok={}
 for name,key in [('gate','baseline_gate'),('return','baseline_return')]:
  if name in cross:gains[name]=e[key]['lower_s']-cross[name]['upper_s'];speedok[name]=cross[name]['speed']>=e[key]['speed']-.15
 future=rd(D/'pilot-fresh-return-witness-private.json') if (D/'pilot-fresh-return-witness-private.json').exists() else None;futurepass=bool(future and future['action_exists']);checks['effect_gate_recomputed']=r['passed']==bool(len(gains)==2 and all(v>=.02-1e-12 for v in gains.values()) and all(speedok.values()) and futurepass and checks['all_raw_bounds']);lim=c['phase_caps']['pilot'];checks['caps']=r['model_integrator_ticks']<=lim['model_ticks'] and r['explicit_force_evaluations']<=lim['force'] and r['planner_cost']['geometry_checks']<=lim['geometry'] and r['CPU_s']<=lim['CPU_s'] and r['wall_s']<=lim['wall_s'];checks['all_model_body_checked']=r['planner_cost']['model_body_checks']==r['model_integrator_ticks'] and r['planner_cost']['max_all_model_body_speed_m_s']<100;checks['actual0']=r['native_actions']==r['native_resets']==0;checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31';checks['old553_failure_preserved']=not rd(G/'retry/dynamic553_pilot_result.json')['passed']
 if not r['passed']:checks['no_deeper_execution']=not any((D/(p+'-STARTED.json')).exists() for p in ['cold','carry','native'])
 out=dict(passed=all(checks.values()),checks=checks,crossings=cross,conservative_gain_s=gains,speed_pass=speedok,accepted_retiming_actions=accepted,regenerated_feedback_failures=regenfailed,successful_retained_revalidations=retainedpassed,proposal_rejections=rejections,mode_counts=mode_counts,max_overspeed_original551_reference=maxold,max_overspeed_committed_reference=over,new_model_ticks_in_audit=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/backup554_audit.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2));assert out['passed']
if __name__=='__main__':run()
