"""Once-only fixed known-DEV native pair; native facts precede model checks."""
import copy,json,random,time,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.paired417_common import ActualC,Trace,arrival
from retry.fork394_run import complete_state
from retry.executor397 import canonical_projection
from retry.loss389_replay import sensor
from retry.planner419 import GoalLedger
from retry.native442 import Native442
from retry.routing442 import ObservedHistory442
from retry.query448 import Query448
from retry.step442 import suffix_step
from retry.ledger439 import require
from retry.canonical438 import require_equal
from retry.receipt421_io import save_receipt,load_receipt
from retry.loss389_analyze import read,save


def actual448(root,meter,fixed,pace):
    from retry.diagnose import make_env
    d=meter.d;p=meter.p;reference=[json.loads(t) for t in (root/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()]
    source_prefix=read(root/'stage417/source-prefix-private.json');root_proof=load_receipt(root/'stage442/actual_C0/C0_step23-before-native-private.json')['full_pre_before_nominal']
    results=[];meter.begin_actual();meter.checkpoint('ACTUAL_PAIR_STARTED')
    try:
        for arm in ['nominal','fullgas']:
            require(arm=='nominal' or (len(results)==1 and results[0]['status']=='NATIVE_EXIT60_VERIFIED'),'448_CANDIDATE_REQUIRES_BASELINE_NATIVE_SUCCESS')
            folder=d/('actual_'+arm);folder.mkdir(mode=0o700)
            env=ctrl=native=history=trace=None;obs=None;status='STARTED';error=None;stage='reset';queries=[];checks=[];prefix_checks=0;start=None;root_progress=None;hit=dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None,interpolated=False)
            calls0=meter.nb['actions'];ticks0=meter.b['ticks'];worlds0=meter.b['worlds'];cpu=time.process_time();wall=time.perf_counter();mc0,mw0=meter.modeltime()
            try:
                # The preserved known condition and legacy setup RNG are fixed,
                # not a new seed search or a new split opening.
                random.seed(394);np.random.seed(394);env=make_env();meter.charge('reset',arm)
                obs,_=env.reset(seed=p['case']['seed'],options={'track_id':p['case']['track_id']})
                ctrl=ActualC(env,fixed,pace);initial=complete_state(env,obs,dict(index=0,laststeer=0.))
                save(folder/'initial-private.json',initial)
                require_equal(initial,read(root/'stage442/actual_C0/initial-private.json'),folder,'448_initial')
                start=float(env.unwrapped.t);pre=sensor(env);progress=canonical_projection(fixed['line'],pre['pos'],pre['vel'],ctrl.phase())['arc']
                ledger=GoalLedger.start(progress,round(pre['time']*50))
                native=Native442(env,ctrl,ledger,fixed,charge_native=lambda:meter.charge('action',arm),obs=obs,directory=folder,arm=arm)
                trace=Trace(lambda:env.unwrapped.t);query=Query448(root,meter,fixed,pace)
                for step in range(1,49):
                    meter.guard();stage='prefix' if step<=22 else 'suffix'
                    if step==23:
                        # Root is checked before advancing controller memory.
                        fork=complete_state(env,native.obs,ctrl.memory());save(folder/'root-before-nominal-private.json',fork)
                        require_equal(fork,root_proof,folder,'448_pre23_original_root')
                        if arm=='fullgas':require_equal(fork,read(d/'actual_nominal/root-before-nominal-private.json'),folder,'448_pair_root')
                        history=ObservedHistory442(native,fixed,meter.plan_sha,arm)
                        root_progress=native.ledger.progress_m;exit_progress=root_progress+60.
                        save_receipt(folder/'448-native-authorization-private.json',dict(stage=448,scope='EXPLICIT448_FIXED_DEV_PRE23_COMMON_EXIT60',actual_root_ledger=asdict(native.ledger),root_dispatch=native.dispatcher.calls,root_progress=root_progress,exit_progress=exit_progress,legacy_snapshot_authority_label_from442_not_a_new_authorization=True))
                    native.prepare_step(step);before=copy.deepcopy(ctrl.memory());nominal=ctrl.act(env);native.bind_nominal(nominal)
                    if step<=22:
                        row=reference[step-1]
                        require(native.prepared['pre']==row['pre'] and before==row['memory_before'] and nominal.tolist()==row['nominal'],'448_EXACT_PREFIX_PRE_COMMAND_MEMORY')
                        native.dispatch(np.asarray(row['command'],np.float32),trace);native.commit_native_observation();native.verify_prefix(row,source_prefix[step-1]);prefix_checks+=1
                    else:
                        frame,record=query.query_fixed(history,before,nominal,arm,step-22,exit_progress);queries.append(record)
                        row,fact,verification=suffix_step(native,history,frame,trace)
                        require(not native.ledger.done and not row['completed'] and not row['ended'] and not row['truncated'],'448_UNEXPECTED_NATIVE_TERMINAL')
                        checks.append(dict(step=step,passed=verification['overall_verification_success'],comparison=verification['comparison']))
                        hit=arrival([a['frozen_row'] for a in history.actions],np.asarray(fixed['line']),root_progress,exit_progress)
                        print(json.dumps(dict(stage=448,arm=arm,decision=step-22,recipe=record['recipe'],guard_actions_each=record['guard_actions_each'],native_actions=meter.nb['actions'],model_ticks=meter.b['ticks'],worlds=meter.b['worlds'],exit_reached=hit['reached'])),flush=True)
                        if hit['reached']:status='NATIVE_EXIT60_VERIFIED'
                    meter.checkpoint('ACTUAL_TRANSITION_VERIFIED',arm=arm,last_completed_action=step,prefix_verified=prefix_checks,suffix_verified=len(checks))
                    if status=='NATIVE_EXIT60_VERIFIED':break
                    require(not native.rows[-1]['ended'] and not native.rows[-1]['truncated'],'448_NONFINISH_TERMINAL')
                else:status='POSTROOT26_CENSORED'
            except BaseException as e:
                error=type(e).__name__+': '+str(e);status='STOP'
                if native:native.halted=True;native.failure=error
                save(folder/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc(),native_facts_retained=True,next_dispatch_forbidden=True))
            finally:
                if trace:trace.disable()
                if native:native.close_log()
                if history:save_receipt(folder/'native-routing-history-private.json',dict(root=history.root,initial=asdict(history.initial),values=asdict(history.values),posts=history.posts,actions=history.actions,verified=history.verified,source='OBSERVED_NATIVE_ONLY_NOT_MODEL_AUTHORITY'))
                if env:
                    try:save(folder/'final-private.json',complete_state(env,native.obs if native else obs,ctrl.memory() if ctrl else {}))
                    finally:env.close()
            rows=[] if native is None else native.rows;suffix=rows[22:];mc,mw=meter.modeltime()
            rr=dict(arm=arm,status=status,error=error,prefix_exact_rows=prefix_checks,suffix_rows=len(suffix),verified_suffix_transitions=len(checks),native_actions=meter.nb['actions']-calls0,confirmed_native_facts=len(rows),unconfirmed_native_actions=meter.nb['actions']-calls0-len(rows),successful_native_dispatch_records=len(list(folder.glob('*-after-native-private.json'))),reset_ticks=round(start*50) if start is not None else None,raw_action_ticks=sum(row['raw_ticks'] for row in rows),crossing_from_original_root=hit,authority_halted=native.halted if native else None,awaiting_verification=native.awaiting_verification if native else None,actual_ledger=asdict(native.ledger) if native else None,actual_facts_retained_after_failure=True,model_ticks=meter.b['ticks']-ticks0,model_worlds=meter.b['worlds']-worlds0,actual_exclusive_CPU_s=time.process_time()-cpu-(mc-mc0),actual_exclusive_wall_s=time.perf_counter()-wall-(mw-mw0),fresh_current_query_count=len(queries),damage=rows[-1]['damage'] if rows else None,no_actual_finish_or_wholelap_claim=True)
            save(folder/'first-transition-checks-private.json',checks);save(folder/'result.json',rr);results.append(rr);save(d/'actual-results.json',results)
            meter.checkpoint('ARM_CLOSED',arm=arm,status=status,error=error,last_completed_action=len(rows))
            print(json.dumps(dict(stage=448,arm=arm,status=status,error=error,actual_actions=rr['native_actions'],crossing=hit)),flush=True)
            if status!='NATIVE_EXIT60_VERIFIED':break
    finally:
        meter.end_actual();save(d/'actual-results.json',results);save(d/'query-records-private.json',meter.queries)
    return results
