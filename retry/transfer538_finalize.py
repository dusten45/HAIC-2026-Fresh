"""Summarize saved538 actual records, without model or environment imports."""
import datetime,hashlib,json,signal,time
from pathlib import Path

def run():
 cpu=time.process_time();wall=time.perf_counter()
 def cap(*a):raise RuntimeError('FINAL_SAVED_RECORD_CAP')
 signal.signal(signal.SIGPROF,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_REAL,60)
 G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response538-private');read=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();n=read(G/'retry/transfer538_native_result.json');reg=read(G/'retry/transfer538_native_registration.json');audit=read(G/'retry/transfer538_audit.json');x=read(D/'native-exit-counters-private.json');gate=read(G/'retry/transfer538_gate_result.json')
 assert n['practical_effect_gate'];assert sha(G/'retry/transfer538_native.py')==reg['native_source_sha256'];assert sha(G/'retry/structure537_control.py')==reg['same537_policy_sha256'];assert sha(G/'retry/transfer538_audit.py')==read(G/'retry/transfer538_audit_registration.json')['source_sha256']
 assert read(D/'launch-prefix-baseline-private.json')==read(D/'launch-prefix-candidate-private.json')
 assert x['explicit_force_evaluations']==n['native_explicit_force_evaluations'];assert x['counts']==n['counts'] and x['model_ticks']==n['native_model_integrator_ticks']
 live=[];raw=sorted(D.glob('raw-*.json'));assert len(raw)==n['counts']['raw_completed']==n['counts']['raw_attempts'];start=read(D/'close-baseline-private.json')['counts']['raw_completed']+51
 for p in raw:
  r=read(p);assert not r['errors']
  if int(p.stem.split('-')[-1])>start and r['phase']=='action' and r['action']>24:live.append(r)
 clips=samples=0;peak=0.
 for r in live:samples+=4;clips+=sum(f['ratio']>1 for f in r['forces']);peak=max(peak,clips/samples)
 assert peak<=.1;certs=0
 for p in D.glob('action-candidate-*.json'):
  r=read(p);assert not r['record']['flags']
  if r['record']['index']<=24:continue
  d=r['governor_detail'];assert d['final_recertified'];f=next(f for f in d['reports'] if f['mode']=='FINAL');assert f['ok'] and f['peak']<=1.0590000000000002 and f['min_footprint_margin_m']>=.5;certs+=1
 for arm in read(D/'native-full-records-private.json'):assert all(not r['flags'] for r in arm['rows'])
 s=dict(status='ACTUAL_14_22_S_EXISTING_DEV_PAIR_PASS',actual_baseline_s=n['arms'][0]['official_finish_episode_s'],actual_candidate_s=n['arms'][1]['official_finish_episode_s'],actual_gain_s=n['official_finish_gain_s'],actual_best_s=14.22,old537_failure_preserved=True,same537_policy_sha256=reg['same537_policy_sha256'],reused_root25_independent_evidence=False,new_pilot_pass=True,cold_model_s=14.22,carry_model_s=14.70,native_counts=n['counts'],actual_guard_flags_empty=True,fresh_native_candidate_certificates=certs,candidate_max_cumulative_clipping_fraction=peak,candidate_final_running_clipping=[clips,samples],pair_launch_prefix_exact=True,model_integrator_ticks=n['all_model_integrator_ticks'],integrator_wheel_force_calls=4*n['all_model_integrator_ticks'],explicit_force_evaluations=n['all_model_wheel_force_evaluations'],forecast_geometry_checks=n['all_geometry_checks'],preflight_CPU_s=gate['CPU_s'],native_CPU_through_exit_s=x['CPU_s'],core_measured_CPU_s=gate['CPU_s']+x['CPU_s'],core_measured_wall_s=gate['wall_s']+x['wall_s'],preparation_CPU_s=read(G/'retry/transfer538_preparation.json')['CPU_s'],accounting_CPU_s=read(G/'retry/transfer538_accounting.json')['CPU_s'],audit_CPU_s=audit['CPU_s'],final_saved_record_CPU_s=time.process_time()-cpu,cost_scope='Registered preflight/native plus separately measured preparation/accounting/audit/final checks. Imports, interactive editing/monitoring and Git overhead are not an exact measured total.',research_remaining=n['research_remaining'],reserve=84000,reserve_used=0,new_seeds=0,protected_queries=0,remaining_gap_to_11_99_s=2.23,scope='One existing DEV, privileged full-state research controller; same path/reference/launch/steering, but candidate also exploits allowed reference band. No pure tracking-loss attribution, pixel submission, generalization or 11-second claim.',deadline_KST='2026-10-20 19:01:55')
 signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
 with (G/'retry/transfer538_summary.json').open('x') as f:json.dump(s,f,indent=2)
 ledger=dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),stage=538,research_start=23474,actual_actions=n['counts']['actions'],research_remaining=n['research_remaining'],reserve=84000,reserve_used=0,native_result_sha256=sha(G/'retry/transfer538_native_result.json'),prior537_result_preserved=True)
 with (D/'current-ledger-private.json').open('x') as f:json.dump(ledger,f,indent=2)
 progress=read(G/'retry/transfer538_progress.json');progress['prior_in_progress_charge']=progress.pop('last_charge');progress['scope']='Completed538pairaggregate; prior_in_progress_charge retains original snapshot, final_counts are final.';progress.update(status='ACTUAL_PAIR_COMPLETED_PASS',completed_utc=ledger['recorded_utc'],actual_candidate_finish_s=14.22,actual_gain_s=n['official_finish_gain_s'],final_counts=n['counts'],research_remaining=n['research_remaining']);(G/'retry/transfer538_progress.json').write_text(json.dumps(progress,indent=2)+'\n')
 print(json.dumps(s,indent=2))
if __name__=='__main__':run()
