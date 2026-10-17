"""Saved whole-parent470 audit. No physics integration or native environment."""
import json,math,re,sys,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.signed417_executor import canonical_projection

ARMS=['OriginalReferenceCommonPulse','Projected4ReferenceCommonPulse']
def clean(error):return None if error is None else re.sub(r'/(?:workspace|tmp)/[^\s\'\"]+','[private-path]',str(error))

def run(root):
 c,w=time.process_time(),time.perf_counter();d=root/'stage469-revision1';g=Path(__file__).resolve().parents[1]
 p=read(d/'plan.json');result=read(d/'result.json');progress=read(d/'progress-private.json');budget=result['budget'];model=budget['model']
 assert progress['phase']=='CLOSED' and sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
 for group in ['sources','protected','original408_preserve']:
  for filename,h in p[group].items():assert sha(filename)==h,filename
 assert sha(p['ledger_path'])==p['ledger_sha256']
 assert 0<=model['ticks']<=model['reserved_ticks']<=2018<=2048 and model['worlds']<=43
 assert budget['actual']['actions']==budget['actual']['resets']==0
 assert budget['wholeworker_CPU_s']<180 and budget['whole_execution_wall_s']<300
 streams={x['link']['label']:x for x in (read(f) for f in d.glob('*-observer-private.json'))}
 assert len(streams)==model['worlds']==model['confirmed_worlds']
 assert sum(len(x['posts']) for x in streams.values())==model['ticks']
 fixed=read(p['fixed_plan']);data=read(p['projection_path']);assert sha(p['projection_path'])==p['projection_sha256']
 nodes=data['original_nodes'];projected=data['projected_nodes'];ds=fixed['free_profile']['ds'];arc_nodes=[0.]
 for length in ds:arc_nodes.append(arc_nodes[-1]+length)
 L=arc_nodes[-1];B=fixed['model']['brake_accel']
 whole=result.get('whole_result');policies=[] if not whole else whole['policies']
 if not policies and (d/'whole_policy-results.json').exists():policies=read(d/'whole_policy-results.json')
 details={}
 for policy in policies:
  arm=policy['arm'];assert arm in ARMS and arm not in details
  child=read(policy['rows_private_path']);rows=child['rows'];stream=streams[policy['label']];posts=stream['posts'];initial=stream['link']['model_ledger']
  assert len(rows)==policy['parent_actions']<=70 and len(posts)==policy['raw_ticks']<=280
  assert len(posts)==sum(row['predicted']['raw_ticks'] for row in rows)
  assert policy['whole_arm_runs']==1 and policy['whole_arm_repeated'] is False
  assert child['initial_actions']==child['tail_actions']==0
  crossings={};failure=None;prior_arc=None;distance=0.;previous_tick=0
  if rows:
   first=rows[0]['raw_hull'][0];prior_arc=canonical_projection(fixed['line'],first['origin_position'],first['COM_linear_velocity'],'FIRST_LAP')['arc']
   assert rows[0]['command'][1:]==[1.,0.]
  for post in posts:
   q=canonical_projection(fixed['line'],post['position'],post['velocity'],post['phase']);distance_after=distance+(q['arc']-prior_arc+L/2)%L-L/2
   tick=post['raw_clock']-initial['last_clock_tick'];assert tick==previous_tick+1
   reasons=[]
   if post['path_error_m']>3:reasons.append('path_error_over3m')
   if post['damage']>0:reasons.append('damage_increase')
   if post['collision']:reasons.append('collision_or_obstacle')
   if post['grass'] or post['wheel_road_contacts']<4:reasons.append('road_loss_or_grass')
   if reasons and failure is None:failure=dict(raw_tick=tick,elapsed_s=tick/50,reasons=reasons,progress_from_root_m=distance_after)
   for boundary in range(60,math.floor(max(0,distance_after)/60)*60+1,60):
    if str(boundary) not in crossings and distance<boundary<=distance_after:
     crossings[str(boundary)]=dict(bracket_s=[previous_tick/50,tick/50],safe_through_crossing=failure is None)
   distance,prior_arc,previous_tick=distance_after,q['arc'],tick
  endpoint=rows[-1] if rows else None;vel=None if endpoint is None else endpoint['predicted']['velocity'];v=None if vel is None else math.hypot(*vel)
  debt={};reference={}
  if endpoint:
   q=canonical_projection(fixed['line'],endpoint['predicted']['position'],vel,endpoint['memory_after']['C']['phase']);j,u=q['index'],q['u']
   for label,vector in [('common_original',nodes),('own',projected if arm==ARMS[1] else nodes)]:
    reference[label]=math.sqrt((1-u)*vector[j]**2+u*vector[j+1]**2)
    lower=[(s-q['arc'],n) for s,n in zip(arc_nodes,vector) if s>q['arc'] and n<v]
    debt[label]=dict(lower_nodes=len(lower),max_required_deceleration_over_B=max(((v*v-n*n)/(2*s)/B for s,n in lower),default=None),minimum_distance_margin_m=min((s-(v*v-n*n)/(2*B) for s,n in lower),default=None),exact_physical_feasibility=False)
  tires=[t for row in rows for t in row['tires']]
  assert len(tires)==4*len(posts)
  if policy['own_model_finish']:
   tracker=child['final_state']['finish_tracker'];assert child['model_ledger']['done'] and tracker['finish_time_s']==policy['official_event_time_s'] and tracker['qualified_time_s'] is not None and failure is None
   assert policy['status']=='FINISHED' and policy['finish_ticks']['lo']<policy['finish_ticks']['hi']
  first_action_failure=next((dict(action=i+1,raw_end_tick=sum(z['predicted']['raw_ticks'] for z in rows[:i+1]),reasons=row['safety']) for i,row in enumerate(rows) if row['safety']),None)
  details[arm]=dict(status=policy['status'],error=clean(policy['error']),actions=len(rows),raw_ticks=len(posts),elapsed_s=len(posts)/50,
   own_model_finish=policy['own_model_finish'],remaining_finish_bracket_s=policy['remaining_model_finish_s'],official_event_time_s=policy['official_event_time_s'],confirmation_time_s=policy['confirmation_time_s'],
   whole_arm_runs=1,whole_arm_repeated=False,qualification_prefix13_exact=policy.get('prefix_match13'),
   common_boundary_crossings=crossings,first_raw_physical_failure=failure,first_action_safety_failure=first_action_failure,
   endpoint_progress_delta_m=distance,endpoint_speed_m_s=v,endpoint_reference_m_s=reference,endpoint_brake_debt_proxy=debt,
   endpoint_phase=child['controller_memory']['C']['phase'],endpoint_ledger_done=child['model_ledger']['done'],
   endpoint_tracker=child['final_state']['finish_tracker'],max_path_error_m=max((x['path_error_m'] for x in posts),default=None),
   max_force_ratio=max((x['force_ratio'] for x in tires),default=None),clipped_wheel_samples=sum(bool(x['clipped']) for x in tires),wheel_samples=len(tires),
   mean_abs_lateral_slip_m_s=None if not tires else sum(abs(x['lateral_slip_m_s']) for x in tires)/len(tires),
   brake_actions=sum(x['command'][2]>0 for x in rows),actual_finish_witness=False)
 both=len(details)==2 and all(x['own_model_finish'] for x in details.values());gain=None;common={}
 if len(details)==2:
  a,b=(details[k] for k in ARMS)
  for boundary in sorted(set(a['common_boundary_crossings'])&set(b['common_boundary_crossings']),key=int):
   ca=a['common_boundary_crossings'][boundary];cb=b['common_boundary_crossings'][boundary]
   common[boundary]=dict(Original_bracket_s=ca['bracket_s'],P4_bracket_s=cb['bracket_s'],Original_minus_P4_s=[ca['bracket_s'][0]-cb['bracket_s'][1],ca['bracket_s'][1]-cb['bracket_s'][0]],both_safe=ca['safe_through_crossing'] and cb['safe_through_crossing'])
  if both:
   a,b=a['remaining_finish_bracket_s'],b['remaining_finish_bracket_s'];gain=[a[0]-b[1],a[1]-b[0]]
 public=dict(stage=470,revision='469-revision1',status=result['status'],error=clean(result['error']),details=details,
  both_safe_own_model_finishes=both,remaining_finish_gain_bracket_s=gain,full_window_model_gain_criterion_passed=bool(both and gain[0]>0),common_boundaries=common,
  prior60m_gain_added=False,actual_promotion=False,whole_arm_repetition_claimed=False,actual_finish_witness=False,
  source_root_qualification_passed=bool((result.get('root_qualification') or {}).get('passed')),
  cost=dict(ticks=model['ticks'],reserved_ticks=model['reserved_ticks'],worlds=model['worlds'],CPU_s=budget['wholeworker_CPU_s'],wall_s=budget['whole_execution_wall_s']),
  static=read(d/p.get('static_result_name','static-result.json')),preflight_counts=result.get('preflight_counts'),storage_forecast=p['storage_forecast'],storage_free_at_start=p['storage_start_free_bytes'],
  protected18_and_ledger475_unchanged=True,new_actual_actions=0,new_resets=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,
  deadline_utc=p['deadline_utc'],plan_sha256=sha(d/'plan.json'),raw_archive_storage='/tmp on this executor only; not assumed shared or durable',workspace_raw_archive_copies=0,
  reproduction_limit='Workspace retains code, full private plan/input material, hashes/manifest and conditions. If /tmp is lost, exact new raw/archive cannot be reverified; hashes do not reconstruct raw.',
  saved_audit_CPU_s=time.process_time()-c,saved_audit_wall_s=time.perf_counter()-w)
 save(d/'saved-closure-private.json',public);save(g/'retry/compare470_result.json',public)
 print(json.dumps(public,ensure_ascii=False));return public

if __name__=='__main__':run(Path(sys.argv[1]))
