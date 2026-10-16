"""Read-only actual/source calibration aggregation after completed418; no worlds or controls."""
import datetime,json,sys,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha

def prepare(root):
 d=root/'stage418';assert not(d/'analysis-plan.json').exists();p=read(d/'plan.json');files=[Path(__file__),d/'plan.json',d/'result.json',d/'budget.json',root/'stage411/policy_C/trace-private.jsonl']
 for arm in ['A','B']:
  files +=[d/('actual_'+arm)/name for name in ['initial-private.json','fork-private.json','trace-private.jsonl','fidelity-checks.json','result.json']]+[root/('stage417/'+arm+'1-private.json')]
 q=dict(stage=418,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='All13actual/sourceclippingphaseflags,forceerrors/first119transition/allmatchingrecipe,realexitbrackets,guardianpolicyoverridesvsroundoffcommanddifferences andaccessibleparentimmutability. Do notchange417thresholdorimputefailedtime. Storedonly,no model/native.',sources={str(f):sha(f) for f in files},protected=p['protected'],original408_preserve=p['original408_preserve']);save(d/'analysis-plan.json',q);(d/'analysis-plan.sha256').write_text(sha(d/'analysis-plan.json')+'\n');print('418 analysis frozen')
def run(root):
 d=root/'stage418';p=read(d/'analysis-plan.json');assert not(d/'analysis.json').exists() and sha(d/'analysis-plan.json')==(d/'analysis-plan.sha256').read_text().strip()
 for f,h in {**p['sources'],**p['protected'],**p['original408_preserve']}.items():assert sha(f)==h
 cpu=time.process_time();wall=time.perf_counter();result=read(d/'result.json');assert result['status']=='ACTUAL_CALIBRATION_PAIRED_COMPLETED';arms={};history=[json.loads(x) for x in (root/'stage411/policy_C/trace-private.jsonl').read_text().splitlines()]
 def maxima(zs,section):
  values=[z[section]['errors' if section=='body' else 'max_errors'] for z in zs];return {k:max(z[k] for z in values) for k in values[0]}
 for arm in ['A','B']:
  folder=d/('actual_'+arm);rr=read(folder/'result.json');rows=[json.loads(x) for x in (folder/'trace-private.jsonl').read_text().splitlines()];source=read(root/('stage417/'+arm+'1-private.json'));checks=read(folder/'fidelity-checks.json');suffix=rows[118:];clipping=[];allphaseexact=True;gaserr=brakeerr=0.;guardhash=True
  for actual,forecast in zip(suffix,source['rows']):
   gu=read(folder/('guardian-'+str(actual['step'])+'-private.json'));guardhash=guardhash and gu['parent_before_sha256']==gu['parent_after_sha256'] and gu['memory_unchanged']
   at=actual['raw_tire_samples'];st=forecast['tires'];assert len(at)==len(st)==16
   for a,s in zip(at,st):
    allphaseexact=allphaseexact and(a['raw_tick'],a['wheel'])==(s['raw_tick'],s['wheel']);clipping.append(dict(step=actual['step'],raw_tick=a['raw_tick'],wheel=a['wheel'],actual=bool(a['clipped']),source=bool(s['clipped']),actual_q=a['force_ratio'],source_q=s['force_ratio']))
    for key in ['gas','brake']:
     if key in a and key in s:
      if key=='gas':gaserr=max(gaserr,abs(a[key]-s[key]))
      else:brakeerr=max(brakeerr,abs(a[key]-s[key]))
  exact_actual=all(z['post']==history[i]['post'] and z['command']==history[i]['command'] for i,z in enumerate(rows)) if arm=='A' else None
  diff=rr['original_recipe_command_differences'];checksMatch=checks['matching_recipe'];assert len(checksMatch)==13 and all(z['passed'] for z in checksMatch);clipfirst=next((dict(step=z['step'],raw_tick=z['raw_tick'],wheel=z['wheel']) for z in clipping if z['actual']),None)
  arms[arm]=dict(status=rr['status'],prefix_exact_rows=rr['prefix_exact_rows'],suffix_rows=rr['suffix_rows'],raw_phase_pairs_exact=allphaseexact,actual_clip_samples=sum(z['actual'] for z in clipping),source_clip_samples=sum(z['source'] for z in clipping),clip_flag_mismatches=sum(z['actual']!=z['source'] for z in clipping),wheel_samples=len(clipping),actual_front_clip_samples=sum(z['actual'] and z['wheel']<2 for z in clipping),actual_rear_clip_samples=sum(z['actual'] and z['wheel']>=2 for z in clipping),actual_max_force_ratio=max(z['actual_q'] for z in clipping),source_max_force_ratio=max(z['source_q'] for z in clipping),first_actual_clip=clipfirst,first_changed_or_nominal_transition=checksMatch[0],matching_recipe_rows=13,body_max_errors=maxima(checksMatch,'body'),wheel_max_errors=maxima(checksMatch,'wheel'),hull_max_errors=maxima(checksMatch,'hull'),selected_first_prediction_all_passed=all(z['passed'] for z in checks['checks'][118:]),guardian_query_count=rr['query_count'],guardian_neutral_override_steps=rr['neutral_guardian_steps'],live_parent_hashes_unchanged=guardhash,actual_source_command_binary_difference_rows=len(diff),max_command_abs_delta=max((z['max_abs_delta'] for z in diff),default=0),recipe_semantic_divergence=bool(rr['neutral_guardian_steps']),source_recipe_after_semantic_divergence_not_claimed=True,actual_arrival=rr['arrival'],cached_source_arrival=read(root/'stage417/result.json')['source_arrival'][arm],official_finish_observed=any(z['completed'] for z in rows),actual_DNF_observed=any(z['ended'] and not z['completed'] for z in rows),damage=rr['damage'],max_suffix_post_path_error_m=max(z['post_projection']['path_error_m'] for z in suffix),max_raw_and_post_path_error_m=None,historical411_A_131_commands_posts_exact=exact_actual)
  save(d/(arm+'-clipping-pairs-private.json'),clipping)
 # FullaccessibleA/BforkincludesRNG/controller/observationhash; nofullsolverhistoryclaim.
 initial=read(d/'actual_A/initial-private.json')==read(d/'actual_B/initial-private.json');fork=read(d/'actual_A/fork-private.json')==read(d/'actual_B/fork-private.json');assert initial and fork
 A=arms['A']['actual_arrival']['rawtick_bracket'];B=arms['B']['actual_arrival']['rawtick_bracket'];gain=[(A[0]-B[1])/50,(A[1]-B[0])/50];assert all(z['raw_phase_pairs_exact'] and z['clip_flag_mismatches']==0 and z['live_parent_hashes_unchanged'] for z in arms.values())
 q=dict(stage=418,status='COMPLETED_ACTUAL_CLIPPING_CALIBRATION',arms=arms,initial_full_A_B_exact=initial,fork_full_A_B_exact=fork,actual_gain_bracket_s=gain,actual_gain_rawtick_bracket=[A[0]-B[1],A[1]-B[0]],actual_source_time_brackets_exact=all(z['actual_arrival']==z['cached_source_arrival'] for z in arms.values()),prior417_promotion_judgment_unchanged=True,promotion=False,reason='Separatecalibrationconfirmedlocalmodelresponse/clipping; guaranteedgain.04stillbelow.08. Notfull-lap/policy/generalizationqualification.',new_native_model_during_analysis=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,analysis_plan_sha256=sha(d/'analysis-plan.json'));save(d/'analysis.json',q);print(json.dumps({k:v for k,v in q.items() if k!='arms'}));print(json.dumps({arm:{k:z[k] for k in ['actual_clip_samples','source_clip_samples','clip_flag_mismatches','first_actual_clip','max_command_abs_delta','max_suffix_post_path_error_m']} for arm,z in arms.items()}))
if __name__=='__main__':
 root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run(root)
