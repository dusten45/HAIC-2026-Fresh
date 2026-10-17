"""Read-only whole saved actual/model audit; no constructors or integration."""
import copy,json,math
from dataclasses import asdict
from pathlib import Path
from retry.loss389_analyze import read,save
from retry.receipt421_io import load_receipt
from retry.planner419 import GoalLedger,H
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
from retry.geometry439 import Projection439,Interval,Telescope439
from retry.ledger439 import compare_first,row_candidate,geometry_transition,compare_ledgers,advance_source
from retry.paired417_common import shapecheck
from retry.canonical438 import compare

def rows(path):return [json.loads(t) for t in path.read_text().splitlines()]
def root_ledger(row):return GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-(row['step']-1)),round(row['pre']['time']*50))
def error(e):return type(e).__name__+': '+str(e)
def replay(frames,actual,fixed,*,prefix=False):
 projection=Projection439(fixed['line'],sum(fixed['free_profile']['ds']),.1);old=root_ledger(actual[0]);model=ForecastLedger.fork(old);progress_i=Interval.point(old.progress_m);goal_i=Interval.point(old.goal_m);result=[];first_stop=None;memory_fields={};geom_branches={};telescope=Telescope439(projection)
 for i,(original,row) in enumerate(zip(frames,actual),1):
  f=copy.deepcopy(original);record=dict(relative_action=i,actual_step=row['step'],physical=None,geometry=None,ledger=None,current_first=None,model_memory_recorded=not prefix)
  z=shapecheck(f,row);record['physical']=bool(z['passed'] and z['wheel']['clipped_flag_mismatches']==0)
  if prefix:f.update(memory_before=row['memory_before'],memory_after=row['nominal_memory_after'])
  else:
   for group,source,target in [('before',f['memory_before'],row['memory_before']),('after',f['memory_after'],row['nominal_memory_after'])]:
    for d in compare(source,target)['diffs']:
     key=group+d['path'];memory_fields[key]=memory_fields.get(key,0)+1
  actual_next,observed=row_candidate(old,row,fixed['line'],projection.L)
  try:
   t=geometry_transition(projection,f,row);record['geometry']='SUPPORTED';record['branches']=[t['before']['branch'],t['after']['branch']]
   for branch in record['branches']:geom_branches[branch]=geom_branches.get(branch,0)+1
   predicted=projection.progress(model.progress_m,t,'model')
   if not prefix and predicted!=f['model_progress']:raise ValueError('MODEL_PROGRESS_ARITHMETIC_NOT_REPRODUCED')
  except Exception as e:
   record['geometry']=error(e);t=None
   # Inspect all stored rows even after a conservative stop, without granting
   # qualification to the tail. Use original source coordinates for accounting.
   from retry.executor397 import canonical_projection
   pre=canonical_projection(projection.line,f['raw_hull'][0]['origin_position'],f['raw_hull'][0]['COM_linear_velocity'],row['memory_before']['C']['phase']);post=canonical_projection(projection.line,f['predicted']['position'],f['predicted']['velocity'],row['nominal_memory_after']['C']['phase']);predicted=advance_source(model.progress_m,post['arc'],pre['arc'],projection.L)
  model_hit=bool(predicted>=model.goal_m or f['predicted']['finished']);next_model=model.advance_prediction(ModelPrediction(predicted,model.last_clock_tick+f['predicted']['raw_ticks'],f['predicted']['finished']))
  try:
   if t is None or progress_i is None:raise ValueError('NO_CONTINUOUS_PREFIX_CERTIFICATE')
   bound=telescope.advance(old.progress_m,model.progress_m,actual_next.progress_m,next_model.progress_m,t);certificate,goal_i=compare_ledgers(old,actual_next,model,next_model,observed['goal_hit'],model_hit,bound,goal_i);progress_i=bound;record['ledger']='PASS';record['continuous_bound_width_m']=bound.hi-bound.lo
  except Exception as e:record['ledger']=error(e);progress_i=None
  if not prefix:
   try:_,cert=compare_first(old,f,row,fixed);record['current_first']='PASS'
   except Exception as e:record['current_first']=error(e)
  else:record['current_first']='MODEL_MEMORY_AND_ROOT_LEDGER_NOT_RECORDED_IN_PREFIX'
  record['numeric_goal_side_equal']=(actual_next.progress_m>=old.goal_m)==(next_model.progress_m>=model.goal_m);record['discrete_equal']=record['numeric_goal_side_equal'] and all(getattr(actual_next,k)==getattr(next_model,k) for k in ['age_actions','last_clock_tick','deadline_missed','done']) and observed['goal_hit']==model_hit
  if first_stop is None and (not record['physical'] or record['geometry']!='SUPPORTED' or record['ledger']!='PASS'):first_stop=i
  result.append(record);old=actual_next;model=next_model
 return dict(rows=len(result),physical_pass=sum(x['physical'] for x in result),geometry_supported=sum(x['geometry']=='SUPPORTED' for x in result),geometry_stop_actions=[dict(action=x['relative_action'],reason=x['geometry']) for x in result if x['geometry']!='SUPPORTED'],ledger_pass=sum(x['ledger']=='PASS' for x in result),discrete_equal=sum(x['discrete_equal'] for x in result),certified_prefix_actions=len(result) if first_stop is None else first_stop-1,first_conservative_stop=first_stop,fresh_current_first_pass=sum(x['current_first']=='PASS' for x in result),memory_exact_mismatch_fields=memory_fields,geometry_branch_counts=geom_branches,continuous_bound_max_width_m=max((x.get('continuous_bound_width_m',0) for x in result),default=0),scope='Stored replay inspection; no actual authority. Prefix memory/ledger are reconstructed diagnostics, not authenticated archived model fields.' if prefix else 'Full trajectory replay and fresh-current eligibility are distinct; after first stop no tail qualification.',records=result)

def run(root,directory):
 fixed=read(Path(read(root/'stage438/plan.json')['fixed_plan']));prefix=read(root/'stage417/source-prefix-private.json');datasets={}
 for name,stage in [('C0',423),('P',427)]:
  actual=rows(root/('stage'+str(stage))/('actual_'+name)/'trace-private.jsonl');frames=read(root/'stage438'/('qualification_'+name+'_1-private.json'))['rows'];datasets[name]=dict(prefix=replay(prefix,actual[:118],fixed,prefix=True),suffix=replay(frames,actual[118:],fixed))
 fresh=[];actual=rows(root/'stage427/actual_P/trace-private.jsonl')
 for n in range(12):
  for rep in [1,2]:
   frame=read(root/'stage438'/('qualification_restore'+str(n+1)+'_'+str(rep)+'-private.json'))['rows'][0];row=actual[118+n]
   try:c,proof=compare_first(root_ledger(row),frame,row,fixed);out=dict(passed=True,continuous_width_m=proof['progress_interval'][1]-proof['progress_interval'][0],actual_candidate_progress_matches_native=c.progress_m==row['progress_after'])
   except Exception as e:out=dict(passed=False,error=error(e))
   fresh.append(dict(actual_decision=n+1,independent_repeat=rep,**out))
 packet=load_receipt(root/'stage438/C0_decision1-before-actual-dispatch-private.json');row=rows(root/'stage438/actual_C0/trace-private.jsonl')[-1]
 try:c,proof=compare_first(GoalLedger(**packet['context']['ledger']),packet['selected_first'],row,fixed);prior438=dict(new_static_pass=True,actual_candidate_matches_native=c.progress_m==row['progress_after'],model_progress_not_committed=c.progress_m!=packet['selected_first']['model_progress'],proof=proof)
 except Exception as e:prior438=dict(new_static_pass=False,error=error(e))
 from retry.fixture438 import stored_env,adapter_values
 from types import SimpleNamespace
 import numpy as np
 full=read(root/'stage437/actual_C0/final-private.json');env=stored_env(full);_,_,left,right=adapter_values(env,np.zeros((4,84,84),np.float32),SimpleNamespace(memory=lambda:copy.deepcopy(full['controller'])));adapter=dict(stored437_full_adapter_canonical_pass=compare(left,right)['equal'],original437_recertified=False)
 q=dict(datasets=datasets,fresh_actual_restore_first_transitions=fresh,stored438_ledger_new_contract=prior438,adapter=adapter,first_transition_field_audit=[dict(field='progress/goal model vs actual',rule='Outward interval from unchanged0.1m endpoint bounds and original expression; exact discrete goal hit/age/clock/deadline/DONE.',conflict_resolved=True),dict(field='actual progress/goal claimed telemetry',rule='Exact own observed geometry derivation. Never use model value as actual.',conflict_resolved=True),dict(field='memory index/laststeer/C fields',rule='Exact at identical copied current inputs before physics. Accumulated future replay memory drift does not qualify as fresh current.',full_replay_continuous_drift_not_waived=True),dict(field='restore pre position/COM velocity/angle/yaw/time',rule='Exact current copy prerequisite for nominal-memory equality; physical future body tolerance remains unchanged.'),dict(field='body/wheel/raw hull/COM metadata/grass/contact/collision/phase/clipping/raw count/finish',rule='Existing fidelity and exact discrete checks retained; physical speed comparison is registered magnitude, not a newly invented post-velocity exact check.'),dict(field='adapter state/memory/RNG/actual event',rule='Exact canonical same-observation comparison; native official tracker/ticket authority only, no model DONE.')],new_model_ticks=0,new_actual_actions=0,new_worlds=0,new_learning_HOLDOUT_SEALED_reserve_paid=0)
 save(directory/'audit-private.json',q);return q
