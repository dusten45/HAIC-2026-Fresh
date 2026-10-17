"""Approved216-tick worst archival extension. No actual env or H1 prefix rerun."""
from retry.experiment444 import *
import hashlib
import pickle
import random
from retry.archive446 import ArchivalChild446,validate_archive,ArchiveGateError
from retry.pilot420_backend import model_ledger_view
from retry.planner419_model_ledger import ForecastLedger
from retry.receipt421_io import receipt_digest


def checkpoint(directory,phase,**facts):
    save(directory/'progress-private.json',dict(stage=446,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**facts))


def restore_rng(payload):
    value=payload['RNG'];blob=value['global_pickle']
    if hashlib.sha256(blob).hexdigest()!=value['digest']:
        raise ArchiveGateError('archived_RNG_digest')
    py,numpy=pickle.loads(blob)
    random.setstate(py);np.random.set_state(numpy)


def new_child(meter,data,label):
    ledger=ForecastLedger(**data['model_ledger'])
    view=model_ledger_view(ledger)
    meter.capture_inputs(data['final_state'],data['controller_memory'],view,label+'_inputs',gate='ARCHIVAL_RESTORE_MODEL_ONLY_NOT_NATIVE_QUALIFICATION')
    c=ArchivalChild446(meter,copy.deepcopy(data['final_state']),copy.deepcopy(data['controller_memory']),view,
                       read(Path(meter.p['fixed_plan'])),np.asarray(read(meter.p['pace_path'])['frozen268']),label,
                       world_tag=label,full_ledger=data['model_ledger'])
    if c.ctrl.memory()!=data['controller_memory'] or asdict(c.ledger)!=data['model_ledger']:
        raise ArchiveGateError('restored_memory_or_full_forecast_ledger')
    if c.m.t!=data['final_state']['physical']['actual_time'] or c.m.elapsed_raw_steps!=data['final_state']['elapsed_raw_steps']:
        raise ArchiveGateError('restored_time_or_elapsed')
    # Initial body/tile/progress/finish exact gates are enforced by Meter433.
    return c


def close_child(c,d):
    c.dump(d);c.close()


def prepare(root):
    g=Path(__file__).resolve().parents[1];d=root/'stage446'
    assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage445/plan.json');v=read(root/'project-effective-budget-v465.json')
    deadline=read(root/'research-deadline-current.json')['deadline_utc']
    assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27516,84000,0)
    files={Path(f):h for f,h in old['sources'].items()}
    files.update({f:sha(f) for f in g.glob('retry/*446*.py')})
    for f in [g/'retry/extension445_design.json',root/'project-effective-budget-v465.json']:
        files[f]=sha(f)
    archives={}
    for recipe in ['nominal','fullgas']:
        archive=root/f'stage444/H1/{recipe}1-private.json'
        first=read(root/f'stage444/H1/{recipe}1-observer-private.json')
        final=root/'stage444/H1'/(first['link']['child_id']+'-observer-final-private.json')
        files[archive]=sha(archive);files[final]=sha(final)
        archives[recipe]=dict(archive=str(archive),final_observer=str(final))
    rows=[json.loads(s) for s in (root/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()]
    actual=root_ledger(rows[22]);root_progress=actual.progress_m
    ends=[read(Path(x['archive']))['model_ledger']['progress_m']-root_progress for x in archives.values()]
    assert 30*(int(max(ends)//30)+1)==60
    semantic=dict(old['semantic_sources'])
    semantic.update({str(f):h for f,h in files.items() if str(f).startswith(str(g)) and f.suffix=='.py'})
    p=dict(stage=446,deadline_utc=deadline,sources={str(f):h for f,h in files.items()},semantic_sources=semantic,
           protected=old['protected'],original408_preserve=old['original408_preserve'],fixed_plan=old['fixed_plan'],
           pace_path=str(root/'stage404/profiles-private.json'),archives=archives,original_actual_root_digest=actual.digest(),
           original_root_progress_m=root_progress,original_actual_root_ledger=asdict(actual),common_exit_relative_m=60.,
           caps=dict(ticks=256,worlds=8,CPU_s=60,wall_s=120),max_extra_actions=13,
           worst_planned_ticks=4*13*4+2*4,worst_worlds=6,
           new_actual_reset_training_seed_SEALED_reserve_paid=0,
           scope='New archival restores, not same live world or actual qualification; own nominal only, no prefix rerun/secondpulse/B witness.',
           stop='First technical/source/restore/geometry/RNG/repeat/safety/progress/cost failure stopsall, no repair/retry. Missing60m within13 is censored; no horizon/boundary/tolerance change.')
    assert p['worst_planned_ticks']==216<=256
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    checkpoint(d,'PLAN_FROZEN',ticks=0,worlds=0)
    print('446 archival model-only216ticks6worlds; hard256/8; +60m, maxextra13')


def run446(root):
    d=root/'stage446';p=read(d/'plan.json')
    assert not(d/'opening.json').exists() and read(d/'static-result.json')['passed']
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
    for group in [p['sources'],p['protected']]:
        for f,h in group.items():assert sha(f)==h,f
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    meter=Meter444(d);children=[];results={};error=None;status='STARTED'
    def timeout(*args):raise ResourceStop('446_registered_time_cap')
    previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    signal.setitimer(signal.ITIMER_PROF,max(.001,60-time.process_time()))
    signal.setitimer(signal.ITIMER_REAL,max(.001,120-(time.perf_counter()-WORKER_START)))
    try:
        for recipe in ['nominal','fullgas']:
            data=read(Path(p['archives'][recipe]['archive']));final=load_receipt(Path(p['archives'][recipe]['final_observer']))
            ledger=validate_archive(data,p['original_actual_root_digest'])
            assert ledger.actual_root_goal_m==p['original_actual_root_ledger']['goal_m']
            assert asdict(ledger)==final['ledger'] and data['controller_memory']==final['memory'] and data['final_state']==final['snapshot']
            restore_rng(final)
            held=new_child(meter,data,recipe+'_held');children.append(held)
            before=copy.deepcopy(held.ctrl.memory());nominal=held.ctrl.act(held.m)
            ph,mh,rh=fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash()
            pair=[]
            for rep in range(2):
                c=new_child(meter,data,recipe+'_extension'+str(rep+1));children.append(c)
                hit=dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None,interpolated=False)
                try:
                    for k in range(13):
                        c.one('extension_'+recipe)
                        if c.status!='ACTIVE':raise PhysicalStop(recipe+'_extension_'+c.status)
                        if (fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())!=(ph,mh,rh):
                            raise TechnicalStop('held_parent_or_RNG_changed_during_extension')
                        hit=arrival(c.rows,np.asarray(read(Path(p['fixed_plan']))['line']),ledger.progress_m,p['original_root_progress_m']+60.)
                        if hit['reached']:break
                    sig=c.signature()
                    pair.append(dict(signature=sig,actions=len(c.rows),hit=hit,rows=copy.deepcopy(c.rows),model_ledger=asdict(c.ledger)))
                finally:close_child(c,d)
            if pair[0]['signature']!=pair[1]['signature'] or pair[0]['hit']!=pair[1]['hit']:
                raise TechnicalStop('archival_extension_independent_repeat')
            held.one('held_first_'+recipe,prepared_nominal=nominal,prepared_before=before)
            check=compare_frames(held.rows[0],pair[0]['rows'][0])
            if not check['passed'] or check['wheel']['clipped_flag_mismatches']:
                raise TechnicalStop('restored_held_first_transition')
            if held.rows[0]['memory_before']!=pair[0]['rows'][0]['memory_before'] or held.rows[0]['memory_after']!=pair[0]['rows'][0]['memory_after']:
                raise TechnicalStop('restored_nominal_memory_first')
            close_child(held,d)
            hit=pair[0]['hit'];cumulative=None
            if hit['reached']:cumulative=[(52+tick)/50 for tick in hit['rawtick_bracket']]
            results[recipe]=dict(status='COMMON_EXIT_REACHED' if hit['reached'] else 'CENSORED_13_ADDITIONAL_ACTIONS',
                                 actions_each=pair[0]['actions'],hit=hit,cumulative_from_original_root_s=cumulative,
                                 independent_repeat_exact=True,held_first_passed=True,
                                 actual_physics_qualified=False,same_original_live_world=False,
                                 archived_prefix_ticks_not_recharged=52)
            save(d/'branch-results.json',results)
            checkpoint(d,'BRANCH_CLOSED',recipe=recipe,status=results[recipe]['status'],ticks=meter.b['ticks'],worlds=meter.b['worlds'])
        status='ARCHIVAL_EXTENSION_COMPLETED'
    except PhysicalStop as e:status='PHYSICAL_STOP';error=str(e)
    except BaseException as e:
        status='TECHNICAL_STOP';error=type(e).__name__+': '+str(e)
        save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        for c in children:
            if not c.closed:
                try:close_child(c,d)
                except BaseException:pass
        meter.closeall();meter.persist()
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for s,h in previous.items():signal.signal(s,h)
    gain=None
    if len(results)==2 and all(x['hit']['reached'] for x in results.values()):
        a=results['nominal']['cumulative_from_original_root_s'];b=results['fullgas']['cumulative_from_original_root_s']
        gain=[a[0]-b[1],a[1]-b[0]]
    result=dict(stage=446,status=status,error=error,branches=results,gain60_bracket_s=gain,budget=read(d/'budget.json'),
                actual_actions_resets_learning_seed_SEALED_reserve_paid=0,
                original_live_continuation=False,actual_qualification=False,plan_sha256=sha(d/'plan.json'))
    save(d/'result.json',result);checkpoint(d,'CLOSED',status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'])
    print(json.dumps(dict(stage=446,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],gain=gain)))


if __name__=='__main__':
    root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run446(root)
