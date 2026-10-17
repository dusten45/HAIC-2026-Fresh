"""Saved-only actual carry readout: original arc brackets and official crossing."""
import copy,json,sys,time
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.calibrate422_analyze import maxima
from retry.paired417_common import arrival
from retry.executor397 import canonical_projection
from retry.receipt421_io import load_receipt,receipt_digest
from retry.preflight421 import restore_typed
from retry.planner419 import choose
from retry.pilot420_json import json_ready
from retry.terminal409_contract import validate

def prepare(root):
 d=root/'stage425';assert not(d/'analysis-plan.json').exists();p=read(d/'plan.json');files=[Path(__file__),Path(__file__).with_name('calibrate422_analyze.py'),d/'plan.json',d/'result.json',d/'budget.json',d/'static-result.json']+[f for f in d.glob('actual_*/*') if f.is_file()]
 save(d/'analysis-plan.json',dict(scope='Savedonly; noactual/model/actorcalls. Officialcrossingandoriginalarcbrackets; neverimputefailed/censoredfinish.',sources={str(f):sha(f) for f in files},protected=p['protected'],original408_preserve=p['original408_preserve']));(d/'analysis-plan.sha256').write_text(sha(d/'analysis-plan.json')+'\n')

def finish_record(rows,initial_time,when,prefix_ticks):
 if when is None:return None
 clocks={initial_time:0};total=0
 for row in rows:
  for h in row['raw_hull']:clocks[h['time']]=total+h['raw_tick']-1
  total+=row['raw_ticks'];clocks[row['post']['time']]=total
 if when not in clocks:raise AssertionError('official_finish_not_observed_raw_clock')
 tick=clocks[when];return dict(lap_ms=round((when-initial_time)*1000),event_tick=tick,event_bracket_ticks=[tick-1,tick],lap_bracket_s=[(tick-1)/50,tick/50],remaining_root_event_bracket_ticks=[tick-prefix_ticks-1,tick-prefix_ticks],remaining_root_bracket_s=[(tick-prefix_ticks-1)/50,(tick-prefix_ticks)/50],confirmed_total_raw_ticks=total,final_wrapper_raw_ticks=rows[-1]['raw_ticks'],official_finish_time_s=when,confirmation_post_time_s=rows[-1]['post']['time'],raw_event_timestamp_exact=True)

def percentile(values):return dict(max_s=max(values),p95_s=float(np.percentile(values,95)),total_s=sum(values)) if values else None

def run(root):
 d=root/'stage425';p=read(d/'analysis-plan.json');assert not(d/'analysis.json').exists();cpu=time.process_time();wall=time.perf_counter()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h,f
 plan=read(d/'plan.json');result=read(d/'result.json');fixed=read(Path(plan['fixed_plan']));line=np.asarray(fixed['line']);L=sum(fixed['free_profile']['ds']);arms={};receipts=[];query_checks=[]
 for r in result['actual']:
  arm=r['arm'];folder=d/('actual_'+arm);rows=[json.loads(t) for t in (folder/'trace-private.jsonl').read_text().splitlines()];suffix=rows[118:];fidelity=read(folder/'fidelity-checks.json');first=fidelity['checks'][118:];tires=[t for row in suffix for t in row['raw_tire_samples']];whole_tires=[t for row in rows for t in row['raw_tire_samples']];latencies=[]
  for path in sorted(folder.glob('*-query-private.json')):
   q=read(path);query_checks.append(q['parent_before_sha256']==q['parent_after_sha256'] and q['parent_memory_RNG_ledger_unchanged'] and not q['source_memory_committed']);latencies.append(rows[q['step']-1]['guardian'])
  for path in sorted(folder.glob('*-receipt-private.json')):
   payload=load_receipt(path);ctx,ev=restore_typed(copy.deepcopy(payload));assert json_ready(asdict(choose(ctx,ev)))==payload['decision'];state,mem,rng=ctx.parent.fork_inputs();step=int(path.name.split('_')[-1].split('-')[0]);actual=rows[step-1];assert state['provenance']=='CURRENT_ACTUAL_PARENT' and state['terminal_model']['physical']['hull']['position']==actual['pre']['pos'] and mem==actual['memory_before'];receipts.append(dict(step=step,canonical_digest=receipt_digest(payload),typed_selector_equal=True,current_actual_parent_exact=True,recipe=payload['decision']['recipe'],gain_rawticks=payload['decision']['gain_rawticks']))
  markers={};start_arc=canonical_projection(line,suffix[0]['pre']['pos'],suffix[0]['pre']['vel'],'FIRST_LAP')['arc'] if suffix else None
  if suffix:
   for fraction in plan['arc_marker_fractions']:
    if fraction*L>start_arc:markers[str(fraction)]=arrival(suffix,line,start_arc,fraction*L)
  finish=finish_record(rows,r['start_time_s'],r['official_finish_time_s'],sum(x['raw_ticks'] for x in rows[:118])) if r['completed'] else None
  if r['completed']:assert read(folder/'final-private.json')['controller']['C']['phase']=='DONE' and finish['lap_ms']==r['lap_ms']
  clips=lambda samples:dict(max_force_ratio=max((t['force_ratio'] for t in samples),default=None),clipped_samples=sum(t['clipped'] for t in samples),wheel_samples=len(samples))
  segments=fidelity['matching_recipe'];summ=lambda z:None if not z else maxima(z)
  arms[arm]=dict(status=r['status'],error=r['error'],completed=r['completed'],actual_actions=r['native_actions'],confirmed_rows=len(rows),unconfirmed_wrapper_actions=r['unconfirmed_native'],prefix_exact_rows=r['prefix_exact_rows'],historical423_exact_rows=r['historical423_exact_rows'],initial13_full_after_state_exact=r['initial13_full_after_state_exact'],historical423_first_command_break=r['historical423_first_command_break'],historical423_alignment_until_end=r['historical423_alignment_until_end'],suffix_actions=len(suffix),initial_suffix_actions=min(13,len(suffix)),continuation_actions=max(0,len(suffix)-13),finish=finish,local_exit=r['arrival'],arc_markers=markers,damage=r['damage'],max_post_path_error_m=r['max_post_path_error_m'],max_raw_path_error_m=max((canonical_projection(line,h['origin_position'],h['origin_linear_velocity'],row['memory_before']['C']['phase'])['path_error_m'] for row in suffix for h in row['raw_hull']),default=None),clipping_whole_actual=clips(whole_tires),clipping_initial13=clips([t for row in suffix[:13] for t in row['raw_tire_samples']]),clipping_continuation=clips([t for row in suffix[13:] for t in row['raw_tire_samples']]),neutral_guardian_steps=r['neutral_guardian_steps'],first_twelve_selected=[x['selected'] for x in r['decisions'][:12]],first_twelve_match424=[x.get('same_recipe_as424') for x in r['decisions'][:12]] if arm=='P' else None,original424_first_command_break=r['original424_first_command_break'],original424_command_alignment_until_end=r['original424_command_alignment_until_end'],first_transition_checks=len(first),first_transition_fidelity=summ(first),initial13_first_transition_fidelity=summ(first[:13]),continuation_first_transition_fidelity=summ(first[13:]),matching_witness_comparisons=len(segments),matching_witness_fidelity=summ(segments),witness_divergence_count=len(r['witness_divergences']),actual_progress_deadline_passed=bool(r['actual_ledger']) and not r['actual_ledger']['deadline_missed'] and all(not row['safety'] for row in rows),raw_tick_terminal_contract_passed=all(validate(row)['passed'] for row in rows),query_count=len(latencies),query_CPU_latency=percentile([q['CPU_s'] for q in latencies]),query_wall_latency=percentile([q['wall_s'] for q in latencies]),model_ticks=r['model_ticks_during_arm'],model_worlds=r['model_worlds_during_arm'],actual_exclusive_CPU_s=r['exclusive_actual_CPU_s'],actual_exclusive_wall_s=r['exclusive_actual_wall_s'])
 differences={};official_gain=None;finish_gain=None
 if 'C0' in arms and 'P' in arms:
  a,b=arms['C0'],arms['P']
  for key in ['local_exit',*plan['arc_marker_fractions']]:
   x=a['local_exit'] if key=='local_exit' else a['arc_markers'].get(str(key));y=b['local_exit'] if key=='local_exit' else b['arc_markers'].get(str(key))
   if x and y and x['reached'] and y['reached']:
    at,bt=x['rawtick_bracket'],y['rawtick_bracket'];differences[str(key)]=[(at[0]-bt[1])/50,(at[1]-bt[0])/50]
   else:differences[str(key)]=None
  if a['finish'] and b['finish']:
   official_gain=(a['finish']['lap_ms']-b['finish']['lap_ms'])/1000;at=a['finish']['event_bracket_ticks'];bt=b['finish']['event_bracket_ticks'];finish_gain=[(at[0]-bt[1])/50,(at[1]-bt[0])/50]
 for f,h in read(d/'prior-preservation-manifest.json').items():assert sha(f)==h,f
 qualified=len(arms)==2 and arms['C0']['initial13_full_after_state_exact'] and arms['C0']['historical423_alignment_until_end'] and all(x['completed'] and x['historical423_exact_rows']>=118 and (x['historical423_first_command_break'] is None or x['historical423_first_command_break'].get('pre_state_exact',False) and x['historical423_first_command_break'].get('memory_before_exact',False)) and x['first_transition_fidelity']['passed'] and x['first_transition_fidelity']['clipped_flag_mismatches']==0 and x['actual_progress_deadline_passed'] for x in arms.values()) and all(query_checks)
 q=dict(stage=425,status=result['status'],arms=arms,actual_paired_carry_qualified=qualified,official_lap_gain_s=official_gain,actual_finish_gain_bracket_s=finish_gain,original_arc_gain_brackets_s=differences,query_count=len(query_checks),parent_memory_RNG_actual_ledger_all_unchanged=all(query_checks),actual_planner_receipts=receipts,source_memory_committed=False,pixel_or_independent_generalization_qualified=False,budget=result['budget'],wholeworker_CPU_s=result['wholeworker_CPU_s'],execution_wall_s=result['execution_wall_s'],prior420_421_422_423_424_preserved=True,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall);save(d/'analysis.json',q);print(json.dumps(dict(status=q['status'],qualified=qualified,official_lap_gain_s=official_gain,finish_bracket=finish_gain,arc_gains=differences,queries=len(query_checks),CPU_s=q['CPU_s'])))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
