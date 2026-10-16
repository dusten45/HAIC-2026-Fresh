"""One-use12-action stored-control qualification; no wrapper, actor, fit or sweep."""
import datetime, hashlib, json, signal, sys, time, traceback
from pathlib import Path
import numpy as np
from retry.loss389_analyze import read, save, sha
G=Path(__file__).resolve().parent.parent

def prepare(root):
    d=root/'stage391';assert not d.exists();d.mkdir(mode=0o700)
    prior=root/'project-effective-budget-v410.json';b=read(prior);assert b['research_remaining']==34139 and b['final_reserved_actions']==84000 and b['final_reserve_used']==0
    caps=read(root/'stage390/B-capture/captures-private.json');actual=[json.loads(s) for s in (root/'stage389/replay/N1/trace-private.jsonl').read_text().splitlines()]
    p390=read(root/'stage390/plan.json');assert read(root/'stage390/B-model-gate.json')['passed'];assert p390['B_states']==[dict(step=64,phase='straight'),dict(step=94,phase='corner')]
    for selected in p390['B_states']:
        step=selected['step'];c=caps[str(step)];row=actual[step-1];assert c['action']==row['action'] and c['actual_post']==row['post'];assert c['snapshot']['hull']['position']==row['pre']['pos'] and c['snapshot']['hull']['velocity']==row['pre']['vel'] and c['snapshot']['actual_time']==row['pre']['time'];assert len(actual[step-1:step+11])==12
    sources=[Path(__file__),G/'retry/source_vehicle_transition.py',G/'retry/loss389_analyze.py',G/'damage.py',prior,root/'research-deadline-current.json',root/'stage390/plan.json',root/'stage390/B-model-gate.json',root/'stage390/B-capture/captures-private.json',root/'stage389/replay/N1/trace-private.jsonl']+list((G/'core').rglob('*.py'))
    p=dict(stage=391,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55+00:00',states=p390['B_states'],state_order=[64,94],actions_per_state=12,action_ranges_inclusive=[[64,75],[94,105]],control_source='Unchanged296 stored actualactions389 N1; snapshot390 pre64/pre94; firstcommand is alreadyqualified390command followed by11commands. No inference/futureteachercommands.',model='Unmodified SourceVehicleTransition; one reconstructedworld perstate, no intermediate reset/correction; no restored solverwarmstarts',limits=p390['B_model_limits'],gate='Eachrow speedabs/yawrateabs/positionL2<=390limits; initialbody/tiles/progress exact; collision,damage,wheel-roadcontact count mustmatchactual. unique_tiles/offtrackcounter/angle loggeddiagnostics,notnewgate.',stop='Firstgatethreshold/discrete mismatch stops thatstate andrecords its firstmismatch; otherfrozenstate remainsindependentandexecutes. Anytechnicalsource/budget/deadline/CPUfailure stopsall remaining; no retry/replacement/thresholdchange. Nooptimization onpass.',native_wrapper_cap=0,actor_call_cap=0,model_tick_cap=96,CPU_cap_s=60,research_remaining=34139,final_reserved_actions=84000,final_reserve_used=0,source_hashes={str(f):sha(f) for f in sources},protected_hashes={str(f):sha(f) for f in [root/'current-champion.json',root/'stage296/champion-manifest.json',root/'protected-query-ledger-v1.json']},provenance='Parentrelayedexplicitresume391; parentoriginalplan/methodfullread11:08-11:09; consumerdirectfullreadnotclaimed',forbidden='Newnative/reset/actor/learning/gainsweep/372failuredetail/HOLDOUT/DEV/SEALED/paidresource/filetransfer')
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');(d/'plan.sha256').chmod(0o600);print(json.dumps(dict(registered=True,plan_sha256=sha(d/'plan.json'),actions=p['action_ranges_inclusive'],model_tick_cap=96,native_cap=0)),flush=True)

def run(root):
    from retry.source_vehicle_transition import SourceVehicleTransition
    import Box2D
    d=root/'stage391';p=read(d/'plan.json');assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip();assert not(d/'opening.json').exists()
    for f,h in {**p['source_hashes'],**p['protected_hashes']}.items():assert sha(f)==h,f
    save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),native_wrapper_cap=0,actor_cap=0))
    caps=read(root/'stage390/B-capture/captures-private.json');actual=[json.loads(s) for s in (root/'stage389/replay/N1/trace-private.jsonl').read_text().splitlines()];records=[];raw=[];ticks=0;reserved=0;worlds=0;error=None;active=None;status='RUNNING'
    start,cpu=time.perf_counter(),time.process_time()
    def guard():
        assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(p['deadline_utc'])
        assert time.process_time()-cpu<60,'CPU cap'
    def timeout(signum,frame):raise TimeoutError('391 CPU60s cap')
    previous=signal.signal(signal.SIGPROF,timeout);signal.setitimer(signal.ITIMER_PROF,60)
    try:
        for sel in p['states']:
            guard();step=sel['step'];model=None;rows=[];first=None;technical=None
            try:
                worlds+=1;model=SourceVehicleTransition(caps[str(step)]['snapshot']);active=model
                initial=dict(bodies=model.initial_bodies_exact,tiles=model.initial_tiles_exact,progress=model.initial_progress_exact)
                if not all(initial.values()):first=dict(relative_action=0,actual_step=step,reason='initialization_mismatch',initialization=initial)
                else:
                    for offset in range(12):
                        guard();assert reserved+4<=96;reserved+=4;truth=actual[step-1+offset];action=np.asarray(truth['action'],np.float32);before=model.native_ticks
                        try:q=model.step(action)
                        finally:ticks+=model.native_ticks-before
                        assert model.native_ticks-before==4
                        post=truth['post'];errors=dict(speed_m_s=abs(q['speed_m_s']-post['speed']),yaw_rate_rad_s=abs(q['angular_velocity']-post['yaw']),position_m=float(np.linalg.norm(np.asarray(q['position'])-post['pos'])))
                        discrete=dict(collision=q['collision']==truth['collision'],damage=q['damage']==truth['damage'],wheel_road_contacts=q['wheel_road_contacts']==sum(n>0 for n in post['road_contacts']))
                        failures=[k for k,v in errors.items() if v>p['limits'][k]]+[k for k,v in discrete.items() if not v]
                        diagnostics=dict(visited_match=q['unique_tiles']==post['visited'],offtrackcounter_match=q['off_track_counter']==post['off_track_counter'],angle_abs_error_rad=abs(float(np.arctan2(np.sin(q['angle']-post['angle']),np.cos(q['angle']-post['angle'])))))
                        r=dict(relative_action=offset+1,actual_step=step+offset,elapsed_model_s=(offset+1)*.08,errors=errors,discrete_matches=discrete,diagnostics=diagnostics,passed=not failures)
                        rows.append(r);raw.append(dict(state_step=step,actual_step=step+offset,action=action.tolist(),predicted=q,actual_post=post))
                        save(d/'progress.json',dict(source_physics_ticks=ticks,reserved_tick_cap=reserved,states_finished=len(records),active_state=step,rows_completed=len(rows)))
                        if failures:first=dict(r,failed_fields=failures);break
                records.append(dict(state_step=step,phase=sel['phase'],initialization=initial,rows_completed=len(rows),passed=first is None and len(rows)==12,first_mismatch=first,rows=rows,max_errors={k:max((r['errors'][k] for r in rows),default=0.) for k in p['limits']},model_ticks=model.native_ticks))
            finally:
                if model:model.close()
                active=None
        status='PASSED' if len(records)==2 and all(r['passed'] for r in records) else 'GATE_FAILED'
    except BaseException as e:
        error=type(e).__name__+': '+str(e);status='TECHNICAL_STOP';save(d/'error-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.signal(signal.SIGPROF,previous)
        if active:active.close()
    save(d/'raw-comparisons-private.json',raw)
    result=dict(stage=391,status=status,technical_error=error,states=records,unexecuted_state_steps=[s for s in p['state_order'] if s not in [r['state_step'] for r in records]],new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_learning_fits=0,source_model_world_initializations=worlds,source_model_zero_time_contact_setups=worlds,source_physics_ticks=ticks,reserved_ticks=reserved,unconfirmed_reserved_ticks=reserved-ticks,model_tick_cap=96,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,CPU_cap_s=60,new_paid_resources=0,python_version=sys.version.split()[0],numpy_version=np.__version__,Box2D_version=Box2D.__version__,source_hashes_rechecked=all(sha(f)==h for f,h in p['source_hashes'].items()),protected_hashes_rechecked=all(sha(f)==h for f,h in p['protected_hashes'].items()),scope='KnownTRAIN storedcontrols;12step fidelity only,notcounterfactual ranking/optimization/generalization/officialtiming qualification')
    save(d/'result.json',result);print(json.dumps(result,ensure_ascii=False),flush=True)
if __name__=='__main__':
    root=Path(sys.argv[1]).resolve()
    if sys.argv[2]=='prepare':prepare(root)
    elif sys.argv[2]=='run':run(root)
    else:raise ValueError(sys.argv[2])
