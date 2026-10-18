"""Compact read-only551 status and rejection summaries; no model/native calls."""
import collections,datetime,hashlib,json,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response551-private')
def run():
 cpu=time.process_time();wall=time.perf_counter();read=lambda p:json.loads(p.read_text());r=read(G/'retry/whole551_cold_result.json');a=read(G/'retry/whole551_audit.json');assert a['passed'];rejections={}
 for arm,p in [('baseline541',Path('/workspace/haic-response541-private/cold-candidate-private.json')),('candidate551',D/'cold-candidate-private.json')]:
  data=read(p);reasons=collections.Counter();first=collections.Counter();n=0
  for command in data['commands']:
   if command['index']<=24:continue
   n+=1;report=next((z for z in command['detail'].get('reports',[]) if z['mode']=='HIGH'),None)
   if report and not report['ok']:reasons[report['reason']]+=1;first[str(report.get('first_hold_pass'))]+=1
  rejections[arm]=dict(tracking_decisions=n,source_full_rejection_reasons=dict(reasons),rejected_first_hold_pass=dict(first),not_causal_time_attribution=True)
 out=dict(status='SAFE_WHOLE_SOURCE_COLD_440MS_BELOW_500MS_GATE',finalized_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),fixed_candidate549_sha256=read(G/'retry/whole551_contract.json')['fixed_path_sha256'],baseline541_reused_no_reintegration=True,baseline_cold_model_s=13.66,candidate_cold_source_finish_s=r['case']['model_finish_episode_s'],gain_ms=r['gain_vs541_ms'],effect_gate_ms=500,shortfall_ms=500-r['gain_vs541_ms'],safe_whole_source_finish=r['case']['pass_safety'],first_safety_failure=r['case']['first_failure'],carry_preregistered_nonworsening_vs14_46=True,carry_executed=False,carry_not_executed_reason='Cold500ms effect gate not met; no candidate carry observation.',actual_cap=0,new_actual_actions=0,new_resets=0,actual_baseline541_s=13.66,actual_candidate_measured=False,no_retroactive549_or550_pass=True,no_new_candidate_or_tuning=True,new_scientific_cost=a['total_new_scientific_cost'],rejections=rejections,research_remaining=22758,reserve=84000,reserve_used=0,new_seeds=0,protected_queries=0,deadline_utc='2026-10-20T10:01:55+00:00',summary_CPU_s=time.process_time()-cpu,summary_wall_s=time.perf_counter()-wall)
 assert not r['passed'] and not (D/'carry-STARTED.json').exists()
 with (G/'retry/whole551_summary.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps(out,indent=2))
if __name__=='__main__':run()
