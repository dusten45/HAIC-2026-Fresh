"""Read saved542 falsification and source pins; no simulator/model imports."""
import hashlib,json,math,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response542-private');read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=read(G/'retry/diagnosis542_contract.json');r=read(G/'retry/diagnosis542_pilot_result.json');cp=read(D/'pilot-latest-cost-private.json');assert all(sha(G/p)==h for p,h in c['source_sha256'].items()) and all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items());assert cp['model_ticks']==r['model_integrator_ticks'] and cp['cost']==r['planner_cost'];lim=c['phase_caps']['pilot'];assert r['model_integrator_ticks']<=lim['model_ticks'] and r['explicit_force_evaluations']<=lim['force'] and r['planner_cost']['geometry_checks']<=lim['geometry'] and r['CPU_s']<=lim['CPU_s'] and r['wall_s']<=lim['wall_s'];assert not r['passed'] and not r['learning_gate'] and not r['promotion_eligible'] and r['full12hold_alternative_safe_witness'];certificates=0
 for case in r['cases']:
  saved=read(D/(case['label']+'-private.json'));assert saved['summary']==case and case['pass_safety'] and case['raw_ticks']==64 and case['max_body_speed_m_s']<100 and case['max_cumulative_clipping_fraction']<=.1 and case['min_margin_m']>=.5 and case['max_reference_overspeed_m_s']<=4.85 and case['force_groups']['running']['peak']<=1.0590000000000002
  for cmd in saved['commands']:
   detail=cmd['detail']
   if detail['mode']=='OFFLINE_HIGH_WITNESS_FIRST':assert cmd['index']==156 and cmd['action'][1:]==[1.,0.] and not detail['promotion_admissible'];continue
   f=next(z for z in detail['reports'] if z['mode']=='FINAL');assert detail['final_recertified'] and f['ok'] and f['peak']<=1.0590000000000002 and f['min_footprint_margin_m']>=.5;certificates+=1
 a=read(D/'root156-baseline-private.json');b=read(D/'root156-high-then-original-policy-private.json');w=read(D/'alternative-12hold-witness-private.json');assert w['commands']==b['commands'][:12] and w['trace']==b['trace'][:48];trajectory=[]
 for n in (4,8,16,32,48,64):
  x=b['trace'][n-1];y=a['trace'][n-1];trajectory.append(dict(raw_ticks=n,progress_gain_m=x['progress']-y['progress'],speed_gain_m_s=math.hypot(*x['root_without_roads']['planar']['linear']['velocity'])-math.hypot(*y['root_without_roads']['planar']['linear']['velocity'])))
 assert trajectory[-1]['progress_gain_m']==r['window_progress_gain_m'] and trajectory[-1]['speed_gain_m_s']==r['window_end_speed_gain_m_s']
 assert not list(D.glob('charge-*.json')) and not (D/'NATIVE_STARTED.json').exists() and not (D/'cold-STARTED.json').exists() and not (D/'carry-STARTED.json').exists();assert r['research_remaining']==22758 and r['native_actions']==0
 out=dict(status='SAVED542_AUDIT_PASS',source_private_pins=True,finite_witness_exists=True,local_effect_gate_pass=False,promotion_eligible=False,fresh_original_high_rejection_raw=17,fresh_original_policy_certificates=certificates,paired_trajectory=trajectory,first_pedal_commands=dict(baseline=[q['action'][1:] for q in a['commands'][:2]],candidate=[q['action'][1:] for q in b['commands'][:2]]),model_integrator_ticks=r['model_integrator_ticks'],explicit_force_evaluations=r['explicit_force_evaluations'],geometry_checks=r['planner_cost']['geometry_checks'],experiment_CPU_s=r['CPU_s'],experiment_wall_s=r['wall_s'],research_remaining=22758,reserve=84000,reserve_used=0,new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 with (G/'retry/diagnosis542_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
