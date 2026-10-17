"""440 once-only known-condition actual pair through native authority."""
import copy,json,random,time,traceback
from pathlib import Path
from dataclasses import asdict
import numpy as np
from retry.paired417_common import ActualC,Trace
from retry.loss389_replay import sensor
from retry.fork394_run import complete_state
from retry.executor397 import canonical_projection
from retry.planner419 import GoalLedger
from retry.native440 import Native440
from retry.routing440 import ObservedHistory440
from retry.paired440_query import Query440
from retry.step440 import suffix_step
from retry.ledger439 import require
from retry.receipt421_io import save_receipt
from retry.loss389_analyze import read,save

def actual_pairs(root,meter,fixed,pace):
 from retry.diagnose import make_env
 d=root/'stage440';p=read(d/'plan.json');prefix=[json.loads(t) for t in (root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()][:118];source_prefix=read(root/'stage417/source-prefix-private.json');results=[];meter.begin_actual()
 try:
  for arm,cap in [('C0',80),('P',100)]:
   folder=d/('actual_'+arm);folder.mkdir(mode=0o700);env=obs=ctrl=native=history=trace=None;error=None;status='STARTED';stage='reset';planner=prefix_checks=0;queries=[];comparisons=[];native_before=meter.nb['actions'];model_before=meter.b['ticks'];world_before=meter.b['worlds'];cpu=time.process_time();wall=time.perf_counter();mc0,mw0=meter.modeltime();start_time=None;lap_ms=official=None;query=Query440(root,meter,fixed,pace)
   try:
    random.seed(394);np.random.seed(394);env=make_env();meter.charge('reset',arm);obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});ctrl=ActualC(env,fixed,pace);initial=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',initial);require(initial==read(root/'stage423/actual_C0/initial-private.json'),'ACTUAL_INITIAL_FULL_STATE_RNG_PIXELS');start_time=float(env.unwrapped.t);pre=sensor(env);progress=canonical_projection(fixed['line'],pre['pos'],pre['vel'],ctrl.phase())['arc'];ledger=GoalLedger.start(progress,round(pre['time']*50));native=Native440(env,ctrl,ledger,fixed,charge_native=lambda:meter.charge('action',arm),obs=obs,directory=folder,arm=arm);trace=Trace(lambda:env.unwrapped.t)
    for step in range(1,119+cap):
     meter.guard();stage='prefix' if step<=118 else 'suffix'
     if step==119:history=ObservedHistory440(native,fixed,meter.plan_sha,arm)
     native.prepare_step(step);before=copy.deepcopy(ctrl.memory());nominal=ctrl.act(env);native.bind_nominal(nominal)
     if step<=118:
      reference=prefix[step-1];require(native.prepared['pre']==reference['pre'] and before==reference['memory_before'] and nominal.tolist()==reference['nominal'],'ACTUAL_PREFIX_PRE_NOMINAL_MEMORY');native.dispatch(np.asarray(reference['command'],np.float32),trace);native.commit_native_observation();native.verify_prefix(reference,source_prefix[step-1]);prefix_checks+=1
     else:
      if step==119:
       fork=complete_state(env,native.obs,dict(before=before,after=ctrl.memory(),nominal=nominal.tolist()));save(folder/'fork-private.json',fork);require(fork==read(root/'stage423/actual_C0/fork-private.json'),'ACTUAL_PRE119_FULL_ROOT_STATE_MEMORY_CLOCK_RNG')
       if arm=='P':require(fork==read(d/'actual_C0/fork-private.json'),'FRESH_PAIR_C0_P_ROOT')
      frame,record,pending=query.query(history,before,nominal,arm,step-118,planner);queries.append(record);planner+=int(record['planner_used']);row,fact,verification=suffix_step(native,history,frame,trace,pending);comparisons.append(dict(step=step,progress_interval_width_m=verification['comparison']['progress_interval'][1]-verification['comparison']['progress_interval'][0],progress_model_minus_actual_m=verification['comparison']['progress_difference_m'],clipping_mismatches=verification['comparison']['fidelity']['wheel']['clipped_flag_mismatches'],fidelity=verification['comparison']['fidelity']));print(json.dumps(dict(stage=440,arm=arm,suffix=step-118,planner=record['planner_used'],recipe=record['selected_recipe'],actual_actions=meter.nb['actions'],model_ticks=meter.b['ticks'],worlds=meter.b['worlds'])),flush=True)
     if native.ledger.done:
      require(step>118 and native.last_verification['passed'] and not native.halted,'NATIVE_DONE_AND_VERIFICATION_REQUIRED');ctrl.done(env);official=float(env.unwrapped.finish_time_s);lap_ms=round((official-start_time)*1000);status='COMPLETED_SAFE_OFFICIAL';break
     if native.rows[-1]['ended'] or native.rows[-1]['truncated']:raise RuntimeError('ACTUAL_NONFINISH_TERMINAL')
    else:status='ACTUAL_ACTION_CAP_CENSORED'
   except BaseException as e:
    error=type(e).__name__+': '+str(e);status='CENSORED_STOP'
    if native:native.halted=True;native.failure=error
    save(folder/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc(),actual_facts_retained=True,next_dispatch_forbidden=True))
   finally:
    if trace:trace.disable()
    if native:native.close_log()
    if history:save_receipt(folder/'native-routing-history-private.json',dict(root=history.root,initial=asdict(history.initial),values=asdict(history.values),posts=history.posts,actions=history.actions,verified=history.verified,source='OBSERVED_NATIVE_VALUES_ONLY_NO_ACTUAL_AUTHORITY'))
    if env:
     try:save(folder/'final-private.json',complete_state(env,native.obs if native else obs,ctrl.memory() if ctrl else {}))
     finally:env.close()
   rows=[] if native is None else native.rows;ts=[t for r in rows for t in r['raw_tire_samples']];suffix=rows[118:];finish=next((r for r in suffix if r['completed']),None);event_bracket=None
   if finish:
    ticks=round((finish['finish_time_s']-suffix[0]['pre']['time'])*50);event_bracket=[ticks-1,ticks]
   mc,mw=meter.modeltime();rr=dict(arm=arm,status=status,error=error,prefix_exact_rows=prefix_checks,suffix_rows=len(suffix),native_actions=meter.nb['actions']-native_before,confirmed_actual_facts=len(rows),unconfirmed_actual_facts=meter.nb['actions']-native_before-len(rows),successful_native_dispatch_records=len(list(folder.glob('*-after-native-private.json'))),reset_ticks=round(start_time*50) if start_time is not None else 0,raw_step_ticks=sum(r['raw_ticks'] for r in rows),planner_decisions=planner,guardian_decisions=len(queries)-planner,verified_suffix_transitions=len(comparisons),actual_facts_retained_after_failure=True,authority_halted=False if native is None else native.halted,awaiting_verification=False if native is None else native.awaiting_verification,actual_ledger=None if native is None else asdict(native.ledger),completed=status=='COMPLETED_SAFE_OFFICIAL',official_event_time_s=None if finish is None else finish['finish_time_s'],native_official_finish_observed=finish is not None,native_lap_ms_from_fact=None if finish is None else round((finish['finish_time_s']-start_time)*1000),confirmation_time_s=None if finish is None else finish['post']['time'],lap_ms=lap_ms,suffix_event_rawtick_bracket=event_bracket,pending_routes=sum(r['route']=='REGISTERED_PENDING_GUARDIAN_ONLY' for r in queries),damage=rows[-1]['damage'] if rows else None,max_post_path_error_m=max((r['post_projection']['path_error_m'] for r in rows),default=None),max_force_ratio=max((t['force_ratio'] for t in ts),default=None),clipped_wheel_samples=sum(t['clipped'] for t in ts),wheel_samples=len(ts),suffix_max_force_ratio=max((t['force_ratio'] for r in suffix for t in r['raw_tire_samples']),default=None),max_progress_comparison_width_m=max((x['progress_interval_width_m'] for x in comparisons),default=None),max_abs_progress_model_actual_m=max((abs(x['progress_model_minus_actual_m']) for x in comparisons),default=None),model_ticks=meter.b['ticks']-model_before,model_worlds=meter.b['worlds']-world_before,exclusive_actual_CPU_s=time.process_time()-cpu-(mc-mc0),exclusive_actual_wall_s=time.perf_counter()-wall-(mw-mw0),new_state_qualification='Only observed and verified actual first transitions, not unobserved forecast tail/high-force/generalization.')
   save(folder/'first-transition-checks.json',comparisons);save(folder/'result.json',rr);results.append(rr);save(d/'actual-results.json',results);print(json.dumps(dict(stage=440,arm=arm,status=status,error=error,actions=rr['native_actions'],lap_ms=lap_ms)),flush=True)
   if status!='COMPLETED_SAFE_OFFICIAL':break
 finally:meter.end_actual();save(d/'actual-results.json',results);save(d/'query-records-private.json',meter.queries)
 return results
