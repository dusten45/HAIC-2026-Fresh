"""Saved-only endpoint-domain correction and matched-space brake-debt audit."""
import json,math,sys
from pathlib import Path
from retry.loss389_analyze import read,sha
from retry.signed417_executor import canonical_projection

def put(path,value):
 with path.open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')

def run(root):
 g=Path(__file__).resolve().parents[1];d=root/'stage469-revision1';p=read(d/'plan.json');public_path=g/'retry/compare470_result.json';result=read(public_path)
 # Preserve initial saved analysis before correcting its post-finish query.
 put(root/'stage469-revision1-initial-analysis-private.json',result)
 fixed=read(p['fixed_plan']);profile=read(p['projection_path']);ds=fixed['free_profile']['ds'];arcs=[0.]
 for length in ds:arcs.append(arcs[-1]+length)
 B=fixed['model']['brake_accel'];L=arcs[-1];matched={}
 for arm,value in result['details'].items():
  stream=read(d/('whole_'+arm+'-observer-private.json'));child=read(d/('whole_'+arm+'-private.json'));first=child['rows'][0]['raw_hull'][0]
  old=canonical_projection(fixed['line'],first['origin_position'],first['COM_linear_velocity'],'FIRST_LAP')['arc'];progress=0.;picked=None
  for post in stream['posts']:
   q=canonical_projection(fixed['line'],post['position'],post['velocity'],post['phase']);after=progress+(q['arc']-old+L/2)%L-L/2
   if progress<180<=after:picked=(post,q);break
   progress,old=after,q['arc']
  if picked:
   post,q=picked;speed=math.hypot(*post['velocity']);debts={}
   for label,nodes in [('common_original',profile['original_nodes']),('own',profile['projected_nodes'] if arm.startswith('Projected') else profile['original_nodes'])]:
    lower=[(s-q['arc'],n) for s,n in zip(arcs,nodes) if s>q['arc'] and n<speed]
    debts[label]=dict(lower_nodes=len(lower),max_required_deceleration_over_B=max(((speed*speed-n*n)/(2*s)/B for s,n in lower),default=None),minimum_distance_margin_m=min((s-(speed*speed-n*n)/(2*B) for s,n in lower),default=None),exact_physical_feasibility=False)
   matched[arm]=dict(boundary_m=180,raw_tick=post['raw_clock']-stream['link']['model_ledger']['last_clock_tick'],speed_m_s=speed,path_error_m=post['path_error_m'],brake_debt_proxy=debts,scope='first raw post crossing+180m; different states, not a causal isolation')
  if value['own_model_finish']:
   assert child['final_state']['finish_tracker']['finish_time_s'] is not None and child['model_ledger']['done']
   value['endpoint_reference_m_s']=None
   value['endpoint_brake_debt_proxy']=None
   value['endpoint_reference_debt_domain']='NOT_APPLICABLE_AFTER_OWN_MODEL_FINISH; geometric wrap must not create a next-lap braking target'
 result['matched_180m_saved_diagnostics']=matched
 result['terminal_domain_audit']='post-DONE reference/debt queries removed; initial analysis retained privately; raw/model/control unchanged'
 audit=dict(stage=470,post_finish_reference_debt_not_applicable=True,matched_180m=matched,model_ticks_added=0,worlds_added=0,raw_control_unchanged=True,prior_analysis_sha256=sha(root/'stage469-revision1-initial-analysis-private.json'))
 put(root/'stage469-revision1-terminal-domain-audit-private.json',audit)
 put(g/'retry/compare470_terminal_audit.json',audit)
 # Aggregate metadata revision only; the original raw saved-closure is intact.
 public_path.write_text(json.dumps(result,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 print(json.dumps(audit,ensure_ascii=False))

if __name__=='__main__':run(Path(sys.argv[1]))
