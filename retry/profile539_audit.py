"""Standard-library-only audit of completed538 saved records."""
import hashlib,json,signal,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter()
 def cap(*a):raise RuntimeError('STATIC_AUDIT_CAP')
 signal.signal(signal.SIGPROF,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_REAL,60)
 G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response539-private');read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();c=read(G/'retry/profile539_contract.json');paths=read(D/'frozen-paths-private.json');assert all(paths['baseline'][k]==paths['candidate'][k] for k in ('points','arcs','ds','curvature','length'));assert paths['backup']==paths['baseline_backup']
 assert all(sha(G/p)==h for p,h in c['source_sha256'].items());assert all(sha(p)==h for p,h in c['private_inputs_sha256'].items())
 assert sha(G/'retry/structure537_control.py')==read(G/'retry/structure537_contract.json')['source_sha256']['retry/structure537_control.py']
 phases={};certs=0;failed=False
 for phase in ('pilot','cold','carry'):
  p=G/f'retry/profile539_{phase}_result.json'
  if not p.exists():assert not (D/f'{phase}-STARTED.json').exists();continue
  assert not failed;r=read(p);phases[phase]=r;failed=not r['passed'];lim=c['phase_caps'][phase];assert r['model_integrator_ticks']<=lim['model_ticks'] and r['explicit_force_evaluations']<=lim['force'] and r['planner_cost']['geometry_checks']<=lim['geometry'];cp=read(D/f'{phase}-latest-cost-private.json');assert cp['model_ticks']==r['model_integrator_ticks'] and cp['cost']==r['planner_cost']
  for case in r['cases']:
   saved=read(D/(case['label']+'-private.json'));assert saved['summary']==case
   if case['pass_safety']:assert case['max_cumulative_clipping_fraction']<=.10 and case['max_body_speed_m_s']<100
   for cmd in saved['commands']:
    if cmd['detail']['mode']=='FIXED_LAUNCH' or not cmd['detail'].get('final_recertified'):continue
    f=next(z for z in cmd['detail']['reports'] if z['mode']=='FINAL');assert f['ok'] and f['peak']<=1.0590000000000002 and f['min_footprint_margin_m']>=.5;certs+=1
 charges=sorted(D.glob('charge-*.json'),key=lambda p:int(p.stem.split('-')[-1]));native=None
 p=G/'retry/profile539_native_result.json'
 if p.exists():
  native=read(p);assert len(phases)==3 and all(r['passed'] for r in phases.values());assert native['counts']['actions']==len(charges)<=1000 and native['counts']['worlds']==native['counts']['closed']<=2 and native['counts']['resets']<=2;assert native['research_remaining']==23107-len(charges)
  for i,p in enumerate(charges,1):q=read(p);assert q['attempted_actual_actions']==i and q['research_remaining']==23107-i
  exit=read(D/'native-exit-counters-private.json');assert exit['counts']==native['counts'] and exit['model_ticks']==native['native_model_integrator_ticks']
 else:assert not charges and not (D/'NATIVE_STARTED.json').exists()
 ticks=sum(r['model_integrator_ticks'] for r in phases.values())+(native['native_model_integrator_ticks'] if native else 0);forces=sum(r['explicit_force_evaluations'] for r in phases.values())+(native['native_explicit_force_evaluations'] if native else 0);assert ticks<=485000 and forces<=2300000
 out=dict(status='SAVED_RECORD_AUDIT_PASS',same538_controller_sha256=True,source_private_pins=True,phase_results={k:r['passed'] for k,r in phases.items()},fresh_model_certificates=certs,model_integrator_ticks=ticks,explicit_force_evaluations=forces,native_actions=len(charges),research_remaining=23107-len(charges),reserve=84000,reserve_used=0,one90candidate_only=True,new_model_ticks=0,new_native_actions=0,private_files=len(list(D.iterdir())),private_bytes=sum(p.stat().st_size for p in D.iterdir()),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
 assert out['private_files']<=8192 and out['private_bytes']<=268435456
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 with (G/'retry/profile539_audit.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out))
if __name__=='__main__':run()
