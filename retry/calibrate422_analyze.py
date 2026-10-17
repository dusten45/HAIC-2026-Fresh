"""Read saved422 only: actual13 fidelity/clipping, scope, and cost aggregation."""
import copy,json,sys,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.headroom413_run import row_fidelity
from retry.receipt421_io import load_receipt,receipt_digest
from retry.preflight421 import restore_typed
from retry.planner419 import choose
from retry.pilot420_json import json_ready

def prepare(root):
 d=root/'stage422';assert not(d/'analysis-plan.json').exists();p=read(d/'plan.json');files=[Path(__file__),d/'plan.json',d/'result.json',d/'budget.json',d/'static-result.json']+[f for f in d.glob('actual_*/*') if f.is_file()]+[root/'stage421/parent_C0-private.json',root/'stage421/parent_P-private.json']
 save(d/'analysis-plan.json',dict(scope='Savedonly; noactual/modelcalls,no new selection or rule changes. Actual13notlongfinishgain.',sources={str(f):sha(f) for f in files},protected=p['protected'],original408_preserve=p['original408_preserve']));(d/'analysis-plan.sha256').write_text(sha(d/'analysis-plan.json')+'\n')

def maxima(checks):
 return dict(passed=all(z['passed'] for z in checks),body={k:max(z['body']['errors'][k] for z in checks) for k in checks[0]['body']['errors']},wheel={k:max(z['wheel']['max_errors'][k] for z in checks) for k in checks[0]['wheel']['max_errors']},raw_hull={k:max(z['hull']['max_errors'][k] for z in checks) for k in checks[0]['hull']['max_errors']},clipped_flag_mismatches=sum(z['wheel']['clipped_flag_mismatches'] for z in checks))

def run(root):
 d=root/'stage422';p=read(d/'analysis-plan.json');assert not(d/'analysis.json').exists();cpu=time.process_time();wall=time.perf_counter()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 result=read(d/'result.json');arms={};receipts=[];queries=[]
 for arm in ['C0','P']:
  folder=d/('actual_'+arm);r=read(folder/'result.json');rows=[json.loads(t) for t in (folder/'trace-private.jsonl').read_text().splitlines()];suffix=rows[118:];checks=read(folder/'fidelity-checks.json');tires=[t for row in suffix for t in row['raw_tire_samples']];prior=read(root/('stage421/parent_'+arm+'-private.json'))['rows'][:len(suffix)];priorchecks=[]
  for pred,actual in zip(prior,suffix):
   delta=float(max(abs(np.asarray(pred['command'])-actual['command'])))
   if delta>1e-6:break
   priorchecks.append(row_fidelity(pred,actual))
  for path in sorted(folder.glob('*-query-private.json')):
   q=read(path);assert q['parent_before_sha256']==q['parent_after_sha256'] and q['parent_memory_RNG_ledger_unchanged'] and not q['source_memory_committed'];queries.append(q)
  for path in sorted(folder.glob('*-receipt-private.json')):
   payload=load_receipt(path);ctx,ev=restore_typed(copy.deepcopy(payload));assert json_ready(asdict(choose(ctx,ev)))==payload['decision'];state,mem,rng=ctx.parent.fork_inputs();step=int(path.name.split('_')[-1].split('-')[0]);actual=rows[step-1];assert state['provenance']=='CURRENT_ACTUAL_PARENT';assert state['terminal_model']['physical']['hull']['position']==actual['pre']['pos'] and mem==actual['memory_before'];assert ctx.ledger.last_clock_tick==round(actual['pre']['time']*50);receipts.append(dict(step=step,canonical_digest=receipt_digest(payload),typed_selector_equal=True,current_actual_pre_and_memory_exact=True,recipe=payload['decision']['recipe'],gain_rawticks=payload['decision']['gain_rawticks'],actual_execution_allowed=payload['decision']['actual_execution_allowed']))
  first=maxima(checks['checks'][118:]);segments=maxima(checks['matching_recipe']);priorresult=None if not priorchecks else maxima(priorchecks)
  assert first['passed'] and first['clipped_flag_mismatches']==0 and segments['passed'] and segments['clipped_flag_mismatches']==0
  arms[arm]=dict(status=r['status'],prefix_exact_rows=r['prefix_exact_rows'],suffix_rows=r['suffix_rows'],actual_actions=r['native_actions'],resets=1,arrival=r['arrival'],damage=r['damage'],max_post_path_error_m=r['max_post_path_error_m'],first_selected_fidelity=first,matching_witness_comparisons=len(checks['matching_recipe']),matching_witness_fidelity=segments,witness_divergences=r['witness_divergences'],prior421_matching_prefix_rows=len(priorchecks),prior421_matching_prefix_fidelity=priorresult,selected_recipes=[x['selected'] for x in r['decisions']],first_three_match421=[x.get('same_recipe_as421') for x in r['decisions'][:3]] if arm=='P' else None,neutral_guardian_steps=r['neutral_guardian_steps'],query_count=r['query_count'],query_parent_unchanged_all=r['query_parent_unchanged_all'],max_force_ratio=max(t['force_ratio'] for t in tires),clipped_wheel_samples=sum(t['clipped'] for t in tires),total_wheel_samples=len(tires),first_clip=next((dict(step=row['step'],raw_tick=t['raw_tick'],wheel=t['wheel']) for row in suffix for t in row['raw_tire_samples'] if t['clipped']),None),actual_finish_observed=any(row['completed'] for row in suffix),terminal_metadata_nonterminal_all=all(not row['completed'] and row['finish_time_s'] is None and not row['ended'] and not row['truncated'] for row in suffix),actual_progress_deadline_passed=all(not row['safety'] for row in suffix) and not r['actual_ledger']['deadline_missed'],model_ticks=r['model_ticks_during_arm'],model_worlds=r['model_worlds_during_arm'],actual_exclusive_CPU_s=r['exclusive_actual_CPU_s'],actual_exclusive_wall_s=r['exclusive_actual_wall_s'])
 gain=None
 if all(x['arrival']['reached'] for x in arms.values()):
  a=arms['C0']['arrival']['rawtick_bracket'];b=arms['P']['arrival']['rawtick_bracket'];gain=[(a[0]-b[1])/50,(a[1]-b[0])/50]
 assert len(queries)==26 and len(receipts)==3 and all(not x['actual_execution_allowed'] for x in receipts)
 for f,h in read(d/'prior-preservation-manifest.json').items():assert sha(f)==h,f
 q=dict(stage=422,status=result['status'],arms=arms,actual_local_exit_gain_bracket_s=gain,queries=26,query_parent_memory_RNG_ledger_all_unchanged=True,actual_planner_receipts=receipts,actual13_transition_clipping_qualified=all(x['status']=='COMPLETED_SAFE_13' for x in arms.values()),long_actual_finish_gain_qualified=False,model421_finish_gain_unchanged_model_only=[.62,.66],source_memory_committed=False,first_safety_or_technical_stop=None,model_budget=result['budget']['model'],actual_budget=result['budget']['actual'],wholeworker_CPU_s=result['wholeworker_CPU_s'],execution_wall_s=result['execution_wall_s'],prior420_421_preserved=True,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'analysis.json',q);print(json.dumps(dict(status=q['status'],actual_local_exit_gain=gain,queries=26,receipts=3,actual13_qualified=q['actual13_transition_clipping_qualified'],CPU_s=q['CPU_s'])))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
