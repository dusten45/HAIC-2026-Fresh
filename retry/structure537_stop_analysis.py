"""Saved-record diagnosis only. Never imports a simulator or controller."""
import hashlib,json,signal,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter()
 def cap(*a):raise RuntimeError('STATIC_CAP')
 signal.signal(signal.SIGPROF,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_REAL,60)
 G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response537-private');read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();c=read(G/'retry/structure537_contract.json');r=read(G/'retry/structure537_pilot_result.json')
 assert all(sha(G/p)==h for p,h in c['source_sha256'].items());assert all(sha(p)==h for p,h in c['private_inputs_sha256'].items())
 assert not r['passed'] and len(r['cases'])==2 and all(x['pass_safety'] for x in r['cases'])
 assert all(not (D/(p+'-STARTED.json')).exists() for p in ('cold','carry')) and not (D/'NATIVE_STARTED.json').exists()
 a=read(D/'ceiling-deficit-candidate-private.json');b=read(D/'ceiling-deficit-baseline-private.json');gas_deltas=[max(abs(x['gas']-y['gas']) for x,y in zip(ra['root_without_roads']['planar']['linear']['wheels'],rb['root_without_roads']['planar']['linear']['wheels'])) for ra,rb in zip(a['trace'][:4],b['trace'][:4])]
 certs=0
 for item in (a,b):
  for q in item['commands']:
   d=q['detail'];assert d['final_recertified'];f=next(x for x in d['reports'] if x['mode']=='FINAL');assert f['ok'] and f['peak']<=1.0590000000000002 and f['min_footprint_margin_m']>=.5;certs+=1
 checkpoint=read(D/'pilot-latest-cost-private.json');assert checkpoint['model_ticks']==r['model_integrator_ticks'] and checkpoint['cost']==r['planner_cost']
 out=dict(status='PILOT_IMMEDIATE_EFFECT_GATE_FAIL_SAFETY_PASS_STOPPED',pair=r['pairs'][0],first_hold_identical_rear_gas_raw_ticks=[i+1 for i,z in enumerate(gas_deltas) if z==0.],first_hold_max_rear_gas_difference=max(gas_deltas),interpretation='Source gas rise is limited to .1 per raw tick; first-hold immediate-effect criterion is poorly aligned with delayed engine response. This is a limitation of the registered mechanism test, not a refutation of the observed 24-hold gain. Original criterion/failure retained: no rescue or further model/native admission.',fresh_certificates=certs,source_private_pins_pass=True,checkpoint_counts_pass=True,model_ticks=r['model_integrator_ticks'],explicit_force_evaluations=r['explicit_force_evaluations'],research_remaining=23474,reserve=84000,reserve_used=0,new_model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 with (G/'retry/structure537_stop_analysis.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
