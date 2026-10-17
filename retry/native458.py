"""Exactly one known-DEV whole native pair through existing fact-first authority."""
import copy,json,random,time,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.paired417_common import ActualC,Trace
from retry.fork394_run import complete_state
from retry.executor397 import canonical_projection
from retry.loss389_replay import sensor
from retry.planner419 import GoalLedger
from retry.native442 import Native442
from retry.routing442 import ObservedHistory442
from retry.query458 import Query458
from retry.step442 import suffix_step
from retry.ledger439 import require
from retry.canonical438 import require_equal
from retry.receipt421_io import save_receipt,load_receipt
from retry.loss389_analyze import read,save


def actual458(root,meter,fixed,pace):
    from retry.diagnose import make_env
    d=meter.d;p=meter.p;reference=[json.loads(s) for s in (root/'stage453/actual_candidate/trace-private.jsonl').read_text().splitlines()]
    source_prefix=read(root/'stage417/source-prefix-private.json');root_proof=load_receipt(root/'stage453/actual_candidate/candidate_step113-before-native-private.json')['full_pre_before_nominal'];results=[]
    meter.begin_actual();meter.checkpoint('NATIVE_PAIR_STARTED')
    try:
        for arm in ['C0','P']:
            require(arm=='C0' or results[0]['completed'],'458_CANDIDATE_AFTER_BASELINE_NATIVE_COMPLETION')
            folder=d/('actual_'+arm);folder.mkdir(mode=0o700);env=ctrl=native=history=trace=None;obs=None;error=None;status='STARTED';stage='reset';start=None;planner=0;lap_ms=None;official=None;prefix_checks=0;queries=[];checks=[]
            a0=meter.nb['actions'];t0=meter.b['ticks'];w0=meter.b['worlds'];cpu=time.process_time();wall=time.perf_counter();mc0,mw0=meter.modeltime()
            try:
                random.seed(394);np.random.seed(394);env=make_env();meter.charge('reset',arm)
                obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']});ctrl=ActualC(env,fixed,pace)
                initial=complete_state(env,obs,dict(index=0,laststeer=0.));save(folder/'initial-private.json',initial)
                require_equal(initial,read(root/'stage453/actual_candidate/initial-private.json'),folder,'458_initial')
                start=float(env.unwrapped.t);pre=sensor(env);progress=canonical_projection(fixed['line'],pre['pos'],pre['vel'],ctrl.phase())['arc']
                native=Native442(env,ctrl,GoalLedger.start(progress,round(pre['time']*50)),fixed,charge_native=lambda:meter.charge('action',arm),obs=obs,directory=folder,arm=arm);trace=Trace(lambda:env.unwrapped.t);query=Query458(root,meter,fixed,pace)
                for step in range(1,213):
                    meter.guard();stage='fixed_observed_prefix' if step<=112 else 'fresh_current_policy'
                    if step==113:
                        fork=complete_state(env,native.obs,ctrl.memory());save(folder/'root-before-nominal-private.json',fork)
                        require_equal(fork,root_proof,folder,'458_pre113_original_root')
                        if arm=='P':require_equal(fork,read(d/'actual_C0/root-before-nominal-private.json'),folder,'458_pair_root')
                        history=ObservedHistory442(native,fixed,meter.plan_sha,arm)
                        save_receipt(folder/'458-native-authorization-private.json',dict(scope='EXPLICIT458_FIXED112_THEN_C0_GUARDIAN_P_FIRST8_419_NATIVE_PAIR',native_root_ledger=asdict(native.ledger),root_dispatch=112,policy='same453candidate112prefix_C0guardian_Pfirst8eligible419_then_sameguardian_native_finish',legacy442_snapshot_label_not_an_authorization=True))
                    native.prepare_step(step);before=copy.deepcopy(ctrl.memory());nominal=ctrl.act(env);native.bind_nominal(nominal)
                    if step<=112:
                        expected=reference[step-1]
                        require(native.prepared['pre']==expected['pre'] and before==expected['memory_before'] and nominal.tolist()==expected['nominal'],'458_OBSERVED_PREFIX_PRE_NOMINAL_MEMORY')
                        native.dispatch(np.asarray(expected['command'],np.float32),trace);native.commit_native_observation();source_frame=source_prefix[step-1] if step<=22 else load_receipt(root/('stage453/candidate_decision'+str(step-22)+'-before-actual-dispatch-private.json'))['selected_first']
                        native.verify_prefix(expected,source_frame);prefix_checks+=1
                    else:
                        frame,record,pending=query.query(history,before,nominal,arm,step-112,planner);queries.append(record);planner+=int(record['planner_used'])
                        row,fact,verification=suffix_step(native,history,frame,trace,pending);checks.append(dict(step=step,planned=record['planner_used'],recipe=record['selected_recipe'],passed=verification['overall_verification_success'],comparison=verification['comparison']))
                        print(json.dumps(dict(stage=458,arm=arm,native_step=step,planner_used=planner,planned=record['planner_used'],recipe=record['selected_recipe'],actual_actions=meter.nb['actions'],model_ticks=meter.b['ticks'],worlds=meter.b['worlds'])),flush=True)
                    meter.checkpoint('NATIVE_TRANSITION_VERIFIED',arm=arm,native_step=step,prefix_verified=prefix_checks,suffix_verified=len(checks),planner_used=planner)
                    if native.ledger.done:
                        require(step>112 and native.last_verification['passed'] and not native.halted,'458_OWN_NATIVE_DONE_AND_VERIFIED_FIRST_REQUIRED')
                        ctrl.done(env);official=float(env.unwrapped.finish_time_s);lap_ms=round((official-start)*1000);status='COMPLETED_SAFE_OFFICIAL';break
                    require(not native.rows[-1]['ended'] and not native.rows[-1]['truncated'],'458_NONFINISH_TERMINAL')
                else:status='CENSORED_NATIVE212_SUFFIX100'
            except BaseException as e:
                error=type(e).__name__+': '+str(e);status='STOP'
                if native:native.halted=True;native.failure=error
                save(folder/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc(),native_facts_retained=True,next_dispatch_forbidden=True))
            finally:
                if trace:trace.disable()
                if native:native.close_log()
                if history:save_receipt(folder/'native-routing-history-private.json',dict(root=history.root,initial=asdict(history.initial),values=asdict(history.values),posts=history.posts,actions=history.actions,verified=history.verified,source='OBSERVED_NATIVE_ONLY_NO_MODEL_AUTHORITY'))
                if env:
                    try:save(folder/'final-private.json',complete_state(env,native.obs if native else obs,ctrl.memory() if ctrl else {}))
                    finally:env.close()
            rows=[] if native is None else native.rows;ts=[t for r in rows for t in r['raw_tire_samples']];mc,mw=meter.modeltime();completed=status=='COMPLETED_SAFE_OFFICIAL'
            rr=dict(arm=arm,status=status,error=error,completed=completed,lap_ms=lap_ms,official_event_time_s=official,native_official_finish_observed=completed,reset_complete_time_s=start,confirmation_time_s=rows[-1]['post']['time'] if completed else None,prefix_exact_rows=prefix_checks,suffix_rows=max(0,len(rows)-112),verified_suffix_transitions=len(checks),native_actions=meter.nb['actions']-a0,confirmed_native_facts=len(rows),unconfirmed_native_actions=meter.nb['actions']-a0-len(rows),successful_native_dispatch_records=len(list(folder.glob('*-after-native-private.json'))),reset_ticks=round(start*50) if start is not None else None,raw_action_ticks=sum(r['raw_ticks'] for r in rows),planner_decisions=planner,guardian_decisions=len(queries)-planner,selected_fullgas_count=sum(q['selected_recipe']=='fullgas' for q in queries),guardian_neutral_count=sum(q['selected_recipe']=='neutralbrake' and not q['planner_used'] for q in queries),planner_neutral_count=sum(q['selected_recipe']=='neutralbrake' and q['planner_used'] for q in queries),pending_queries=sum(q['route']=='REGISTERED_PENDING_GUARDIAN_ONLY' for q in queries),authority_halted=native.halted if native else None,awaiting_verification=native.awaiting_verification if native else None,actual_ledger=asdict(native.ledger) if native else None,actual_facts_retained_after_failure=True,model_ticks=meter.b['ticks']-t0,model_worlds=meter.b['worlds']-w0,actual_exclusive_CPU_s=time.process_time()-cpu-(mc-mc0),actual_exclusive_wall_s=time.perf_counter()-wall-(mw-mw0),fresh_current_query_count=len(queries),damage=rows[-1]['damage'] if rows else None,max_post_path_error_m=max((r['post_projection']['path_error_m'] for r in rows),default=None),max_force_ratio=max((t['force_ratio'] for t in ts),default=None),clipped_wheel_samples=sum(t['clipped'] for t in ts),wheel_samples=len(ts),max_progress_comparison_width_m=max((x['comparison']['progress_interval'][1]-x['comparison']['progress_interval'][0] for x in checks),default=None),max_abs_progress_model_actual_m=max((abs(x['comparison']['progress_difference_m']) for x in checks),default=None),clipping_mismatches=sum(x['comparison']['fidelity']['wheel']['clipped_flag_mismatches'] for x in checks),target11_99_achieved=completed and lap_ms<=11990)
            save(folder/'first-transition-checks-private.json',checks);save(folder/'result.json',rr);results.append(rr);save(d/'actual-results.json',results)
            meter.checkpoint('ARM_COMPLETE' if completed else 'ARM_CENSORED_STOP',arm=arm,native_step=len(rows),status=status,error=error)
            print(json.dumps(dict(stage=458,arm=arm,status=status,error=error,native_actions=rr['native_actions'],lap_ms=lap_ms)),flush=True)
            if not completed:break
    finally:meter.end_actual();save(d/'actual-results.json',results);save(d/'query-records-private.json',meter.queries)
    return results
