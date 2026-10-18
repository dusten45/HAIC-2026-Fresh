"""Saved541 audit only; launch and tracking criteria are explicitly separate."""
import hashlib,json,signal,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter()
 def cap(*a):raise RuntimeError('STATIC_AUDIT_CAP')
 signal.signal(signal.SIGPROF,cap);signal.setitimer(signal.ITIMER_PROF,60);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_REAL,90)
 G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response541-private');read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();c=read(G/'retry/joint541_contract.json');assert all(sha(G/p)==h for p,h in c['source_sha256'].items());assert all(sha(p)==h for p,h in c['private_inputs_sha256'].items());assert (D/'frozen-paths-private.json').read_bytes()==Path('/workspace/haic-response539-private/frozen-paths-private.json').read_bytes()
 phases={};certs={'launch':0,'tracking':0};failed=False
 def certificate(d):
  f=next(z for z in d['reports'] if z['mode']=='FINAL');assert d['final_recertified'] and f['ok'] and f['min_footprint_margin_m']>=.5
  if d['mode']=='SOURCE_LAUNCH':assert f['launch_peak']<=2.499 and f['tracking_peak']<=1.0590000000000002 and f['launch_samples']==384 and f['launch_clipped']/384<=.15 and f['max_body_speed_m_s']<100;certs['launch']+=1
  else:assert f['peak']<=1.0590000000000002;certs['tracking']+=1
 for phase in ('pilot','cold','carry'):
  p=G/f'retry/joint541_{phase}_result.json'
  if not p.exists():assert not (D/f'{phase}-STARTED.json').exists();continue
  assert not failed;r=read(p);phases[phase]=r;failed=not r['passed'];cp=read(D/f'{phase}-latest-cost-private.json');assert cp['model_ticks']==r['model_integrator_ticks'] and cp['cost']==r['planner_cost'];lim=c['phase_caps'][phase];assert r['model_integrator_ticks']<=lim['model_ticks'] and r['explicit_force_evaluations']<=lim['force'] and r['planner_cost']['geometry_checks']<=lim['geometry']
  for case in r['cases']:
   saved=read(D/(case['label']+'-private.json'));assert saved['summary']==case
   if case['pass_safety']:assert case['max_cumulative_clipping_fraction']<=.1 and case['max_body_speed_m_s']<100 and case['force_groups']['launch']['peak']<=2.5 and case['force_groups']['launch']['clipped']/max(1,case['force_groups']['launch']['samples'])<=.15
   for q in saved['commands']:
    if q['detail'].get('final_recertified'):certificate(q['detail'])
 charges=sorted(D.glob('charge-*.json'),key=lambda p:int(p.stem.split('-')[-1]));native=None;p=G/'retry/joint541_native_result.json'
 if p.exists():
  native=read(p);assert all(r['passed'] for r in phases.values()) and phases['carry']['passed'];assert native['counts']['actions']==len(charges)<=1000 and native['counts']['worlds']==native['counts']['closed']<=2 and native['counts']['resets']<=2;assert native['research_remaining']==23107-len(charges);assert read(D/'native-exit-counters-private.json')['counts']==native['counts']
  for i,p in enumerate(charges,1):q=read(p);assert q['attempted_actual_actions']==i and q['research_remaining']==23107-i
  for p in D.glob('action-candidate-*.json'):
   q=read(p);assert not q['record']['flags'];certificate(q['governor_detail'])
  assert len(read(D/'launch-prefix-baseline-private.json'))==len(read(D/'launch-prefix-candidate-private.json'))==24
 else:assert not charges and not (D/'NATIVE_STARTED.json').exists()
 ticks=sum(r['model_integrator_ticks'] for r in phases.values())+(native['native_model_integrator_ticks'] if native else 0);forces=sum(r['explicit_force_evaluations'] for r in phases.values())+(native['native_explicit_force_evaluations'] if native else 0);assert ticks<=545000 and forces<=2650000
 out=dict(status='SAVED_RECORD_AUDIT_PASS',phase_results={k:r['passed'] for k,r in phases.items()},source_private_pins=True,unchanged539cap90_and537tracking=True,fresh_certificates=certs,model_integrator_ticks=ticks,explicit_force_evaluations=forces,native_actions=len(charges),research_remaining=23107-len(charges),reserve=84000,reserve_used=0,new_model_ticks=0,new_native_actions=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 with (G/'retry/joint541_audit.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out))
if __name__=='__main__':run()
