"""Aggregate frozen549 evidence without physics or protected data queries."""
import collections,datetime,hashlib,json,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response549-private')

def run():
 cpu=time.process_time();wall=time.perf_counter();read=lambda p:json.loads(p.read_text());pilot=read(G/'retry/retime549_pilot_result.json');design=read(G/'retry/retime549_design_result.json');audit=read(G/'retry/retime549_audit.json');assert audit['passed'];cases=[];actions=[]
 for case in pilot['cases']:
  data=read(D/(case['label']+'-private.json'));high=collections.Counter();alltrials=collections.Counter();finals=0
  for command in data['commands']:
   detail=command['detail']
   for report in detail.get('reports',[]):
    if report['mode']=='HIGH' and not report['ok']:high[report['reason']]+=1
    if report['mode']=='FINAL':finals+=1
   for trial in detail.get('trials',[]):alltrials[trial['reason']]+=1
  actions.append(data['commands']);cases.append(dict(label=case['label'],high_rejections=dict(high),trial_reasons=dict(alltrials),fresh_FINAL_certificates=finals,**{k:case[k] for k in ['stop','pass_safety','raw_ticks','actions','first_failure','crossing','terminal','min_margin_m','max_body_speed_m_s','max_reference_overspeed_m_s','max_path_error_m','max_cumulative_clipping_fraction','force_groups']}))
 first=None
 if len(actions)==2:
  for a,b in zip(*actions):
   if a.get('action')!=b.get('action'):first=dict(index=a['index'],baseline_mode=a['detail']['mode'],candidate_mode=b['detail']['mode'],both_have_action='action' in a and 'action' in b);break
 out=dict(status='PILOT_PASSED' if pilot['passed'] else 'STOPPED_AT_PREREGISTERED_PILOT_GATE',registered_deadline_utc='2026-10-20T10:01:55+00:00',actual_baseline541_s=13.66,candidate_actual_measured=False,whole_lap_candidate_measured=False,pilot=pilot,design=design,cases=cases,first_action_difference=first,exposure=audit['whole_lap_saved541_exposure'],research_remaining=22758,reserve=84000,reserve_used=0,new_seeds=0,protected_queries=0,deep_research_lines=1 if pilot['passed'] else 0,public_raw_data=False,science_CPU_s=design['CPU_s']+pilot['CPU_s'],science_wall_s=design['wall_s']+pilot['wall_s'],aggregate_worker_CPU_s=time.process_time()-cpu,aggregate_worker_wall_s=time.perf_counter()-wall)
 with (G/'retry/retime549_summary.json').open('x') as f:json.dump(out,f,indent=2)
 print(json.dumps({k:out[k] for k in ['status','first_action_difference','science_CPU_s','science_wall_s','research_remaining']}))
if __name__=='__main__':run()
