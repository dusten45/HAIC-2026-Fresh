"""Audit saved feedback/window/terminal/cost evidence; no new physics calls."""
import collections,hashlib,json,math,time
from pathlib import Path
import numpy as np
from retry.plan513_model import load_root
from retry.lap518_control import steering
from retry.velocity543_control import steering_velocity

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response543-private');read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=read(G/'retry/velocity543_contract.json');r=read(G/'retry/velocity543_pilot_result.json');assert all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items());cp=read(D/'pilot-latest-cost-private.json');assert cp['model_ticks']==r['model_integrator_ticks'] and cp['cost']==r['planner_cost'];lim=c['phase_caps']['pilot'];assert r['model_integrator_ticks']<=lim['model_ticks'] and r['explicit_force_evaluations']<=lim['force'] and r['planner_cost']['geometry_checks']<=lim['geometry'] and r['CPU_s']<=lim['CPU_s'] and r['wall_s']<=lim['wall_s'];assert not r['passed'] and len(r['records'])==1 and r['records'][0]['terminal_nonworsening'] and not r['records'][0]['effect_pass'];assert len(r['cases'])==2 and all(z['pass_safety'] for z in r['cases'])
 ctl=(G/'retry/velocity543_control.py').read_text();a=ctl.index('def steering_velocity(');b=ctl.index('def geometry_context(',a);canonical=(ctl[:a]+ctl[b:]).replace('from retry.drive519_control import nominal as legacy_nominal,project,force_rows,reference\nfrom retry.lap518_control import point_at','from retry.drive519_control import nominal,project,force_rows,reference').replace('from retry.preview527_control import backup as legacy_backup,forecast','from retry.preview527_control import backup,forecast');assert canonical==(G/'retry/structure537_control.py').read_text()
 static=read(Path('/workspace/haic-response515-private/collected-map-state-private.json'));data=read(D/'pilot-roots-private.json')[0];path=read(D/'frozen-paths-private.json')['candidate'];metrics={};certs=0
 for case in r['cases']:
  saved=read(D/(case['label']+'-private.json'));assert saved['summary']==case and len(saved['commands'])==32 and len(saved['trace'])==128;root=load_root(dict(data['root'],roads=static['root']['roads']));trace=saved['trace'];clipping=collections.Counter();candidate=case['label'].endswith('-candidate')
  for j,cmd in enumerate(saved['commands']):
   progress=trace[j*4-1]['progress'] if j else None
   if progress is None:
    from retry.frozen534_projection import initial_progress
    progress=initial_progress(root,path,data['completed'])
   func=steering_velocity if candidate and j<16 else steering;expected=np.float32(func(root,path,progress));assert np.float32(cmd['action'][0]).tobytes()==expected.tobytes();detail=cmd['detail'];f=next(z for z in detail['reports'] if z['mode']=='FINAL');assert detail['final_recertified'] and f['ok'] and f['peak']<=1.0590000000000002 and f['min_footprint_margin_m']>=.5;certs+=1
   for k in range(4):
    row=trace[j*4+k]
    for z in row['forces']:
     if not z['clipped']:continue
     w=root.planar.linear.wheels[z['wheel']];h=w.heading;v=z['vector'];forward=(-math.sin(h),math.cos(h));long=sum(v[t]*forward[t] for t in range(2));lat=forward[1]*v[0]-forward[0]*v[1];clipping[('front' if z['wheel']<2 else 'rear')+('/lateral' if lat*lat>long*long else '/longitudinal')]+=1
    root=load_root(dict(row['root_without_roads'],roads=static['root']['roads']))
  metrics[case['label']]=dict(clipped_wheel_decomposition=dict(clipping),min_intervention_margin_m=min(x['margin'] for x in trace[:64]),min_return_to_original_margin_m=min(x['margin'] for x in trace[64:]),max_running_clipping=case['max_cumulative_clipping_fraction'],terminal_path_error_m=r['records'][0]['terminal_candidate' if candidate else 'terminal_baseline']['path_error_m'])
 assert not list(D.glob('risk_16holds_before_minimum_margin*')) and not (D/'cold-STARTED.json').exists() and not (D/'carry-STARTED.json').exists() and not (D/'NATIVE_STARTED.json').exists() and not list(D.glob('charge-*.json'));assert r['native_actions']==r['native_resets']==0 and r['research_remaining']==22758
 out=dict(status='SAVED543_AUDIT_PASS',source_private_pins=True,original537pedal_and_certifier_unchanged_after_canonical_wrapper_removal=True,feedback_command_recomputations=64,fresh_FINAL_certificates=certs,primary_safe=True,sustained_effect_gate_pass=False,terminal_state_gate_pass=True,secondary_risk_not_run=True,cold_carry_native_not_run=True,phase_metrics=metrics,model_integrator_ticks=r['model_integrator_ticks'],explicit_force_evaluations=r['explicit_force_evaluations'],geometry_checks=r['planner_cost']['geometry_checks'],experiment_CPU_s=r['CPU_s'],experiment_wall_s=r['wall_s'],research_remaining=22758,reserve=84000,reserve_used=0,new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/velocity543_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
