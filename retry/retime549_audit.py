"""Read-only audit of549 frozen inputs, profile invariants and one source pilot."""
import datetime,hashlib,json,math,subprocess,time
from pathlib import Path
from retry.corner515_model import margin
from retry.plan513_model import load_root
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response549-private')

def finite(value):
 if isinstance(value,float):return math.isfinite(value)
 if isinstance(value,dict):return all(finite(x) for x in value.values())
 if isinstance(value,list):return all(finite(x) for x in value)
 return True

def run():
 cpu=time.process_time();wall=time.perf_counter();read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=read(G/'retry/retime549_model_contract.json');design=read(G/'retry/retime549_design_result.json');result=read(G/'retry/retime549_pilot_result.json');paths=read(D/'frozen-paths-private.json');old=read(Path('/workspace/haic-response541-private/frozen-paths-private.json'));force=read(D/'curvature-force-design-private.json');probe=read(D/'probe-private.json');saved=read(Path('/workspace/haic-response549-input-private/saved541-candidate-rows-private.json'));checks={}
 checks['source_pins']=all(sha(G/p)==h for p,h in c['source_sha256'].items());checks['private_input_pins']=all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items());checks['baseline541_exact']=paths['baseline']==old['candidate'];checks['backup_exact']=paths['backup']==paths['baseline_backup']==old['backup'];mutable={'periodic_squared','launch_squared','periodic_pass_rounds'};checks['geometry_and_cap_metadata_unchanged']=all(paths['candidate'][k]==paths['baseline'][k] for k in paths['baseline'] if k not in mutable);checks['cap90']=max(paths['candidate']['periodic_squared']+paths['candidate']['launch_squared'])<=8100+1e-8
 peak=0.;mass=force['body_mass'];weights=force['axle_load_fractions'];q=force['periodic_q'];launch=force['launch_q'];ds=paths['candidate']['ds'];K=force['segment_curvature']
 for values in (q+[q[0]],launch):
  for i,d in enumerate(ds):
   acc=(values[i+1]-values[i])/(2*d);qmax=max(values[i:i+2]);lat=[mass*weights[j//2]*qmax*K[i]/2 for j in range(4)];long=[mass*max(acc,0)/2 if j>=2 else 0 for j in range(4)] if acc>=0 else [mass*abs(acc)/4]*4;peak=max(peak,max(math.hypot(x,y)/400 for x,y in zip(lat,long)))
 checks['steady_design_force']=peak<=.9990000001;checks['design_gate']=design['passed'] and design['scalar_clock_difference_s']>0 and design['selected_window_scalar_proxy_s']>=.02
 near=[r for r in saved if r['action']>24 and r['speed']-r['reference_speed']>=4];noncap=[r for r in near if r['reference_speed']<89.999];low=lambda rows:[r for r in rows if max(z['ratio'] for z in r['forces'])<.7];exposure=dict(near_reference_s=.02*len(near),near_reference_low_force_s=.02*len(low(near)),near_reference_noncap_s=.02*len(noncap),near_reference_noncap_low_force_s=.02*len(low(noncap)))
 static=read(Path('/workspace/haic-response515-private/collected-map-state-private.json'));initial_root=load_root(dict(probe['root'],roads=static['root']['roads']));initial_gap=margin(initial_root,static['roads'],bounds(static['roads']),static['boundary'],boundary_index(static['boundary']),static['obstacles'])
 cases=[]
 for case in result['cases']:
  saved_case=read(D/(case['label']+'-private.json'));trace=saved_case['trace'];commands=saved_case['commands'];checks[case['label']+'_summary_exact']=case==saved_case['summary'];checks[case['label']+'_raw_count']=len(trace)==case['raw_ticks'];checks[case['label']+'_finite']=finite(trace) and finite(case);checks[case['label']+'_float32_action_domain']=all(len(a['action'])==3 and abs(a['action'][0])<=.40000001 and 0<=a['action'][1]<=1 and 0<=a['action'][2]<=1 and not(a['action'][1]>0 and a['action'][2]>0) for a in commands if 'action' in a);clips,samples=probe['history'];maxclip=clips/samples;peak_force=0.;min_margin=initial_gap;maxover=0.;maxpath=0
  for r in trace:
   clips+=sum(z['clipped'] for z in r['forces']);samples+=4;maxclip=max(maxclip,clips/samples);peak_force=max(peak_force,max(z['ratio'] for z in r['forces']));min_margin=min(min_margin,r['margin']);maxover=max(maxover,math.hypot(*r['root_without_roads']['planar']['linear']['velocity'])-r['target']);maxpath=max(maxpath,r['path_error'])
  physical=bool(trace and min_margin>=.5251524480367317 and peak_force<=1.059 and maxclip<=.1 and maxover<=4.85 and maxpath<=3 and case['max_body_speed_m_s']<100)
  checks[case['label']+'_metrics']=abs(min_margin-case['min_margin_m'])<1e-12 and abs(maxclip-case['max_cumulative_clipping_fraction'])<1e-12
  cross=case['crossing'];checks[case['label']+'_crossing_bracket']=cross is None or (cross['lower_s']<=cross['time_s']<=cross['upper_s'] and abs(cross['upper_s']-cross['lower_s']-.02)<1e-12)
  if case['pass_safety']:checks[case['label']+'_safe_pass_consistent']=physical and case['continuation12_complete'] and cross is not None
  cases.append(dict(label=case['label'],physical_safe_from_trace=physical,pass_safety=case['pass_safety'],min_margin_m=min_margin,peak_force=peak_force,max_cumulative_clipping=maxclip,max_reference_overspeed=maxover,max_path_error=maxpath,crossing=cross,first_failure=case['first_failure'],commands=len(commands),raw_ticks=len(trace)))
 lim=c['phase_caps']['pilot'];checks['pilot_caps']=result['model_integrator_ticks']<=lim['model_ticks'] and result['explicit_force_evaluations']<=lim['force'] and result['planner_cost']['geometry_checks']<=lim['geometry'] and result['CPU_s']<=lim['CPU_s'] and result['wall_s']<=lim['wall_s'];checks['no_native']=result['native_actions']==result['native_resets']==0;checks['main_preserved']=subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
 if not result['passed']:checks['failed_pilot_stops_deeper']=not any((D/(phase+'-STARTED.json')).exists() for phase in ['cold','carry','native'])
 out=dict(passed=all(checks.values()),checks=checks,design_force_ratio_independent=peak,whole_lap_saved541_exposure=exposure,cases=cases,actual_gain_measured=False,model_pilot_passed=result['passed'],research_remaining=22758,reserve=84000,reserve_used=0,new_seeds=0,protected_queries=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,checked_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 with (G/'retry/retime549_audit.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2));assert out['passed']
if __name__=='__main__':run()
