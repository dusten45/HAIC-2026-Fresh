"""Fixed+270m model-only screen, same child from H13 through first braking."""
from retry.continuation449 import *
from retry.live447 import LiveH13447


def checkpoint450(d,phase,**facts):
    save(d/'progress-private.json',dict(stage=450,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**facts))


def continue450(c,ctx,line,exit_progress,max_actions=64):
    require(c.status=='ACTIVE' and c.initial_count==13 and len(c.rows)==13 and c.initial_ok and c.initial_safe and c.initial_progress,'450_INITIAL_H13_NOT_SAFE_QUALIFIED')
    c.stream.prepare_boundary(ctx);token=LiveH13447.seal(c);c.stream.start_tail();token.validate(c)
    hit=dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None,interpolated=False)
    while len(c.rows)<max_actions:
        token.validate(c);c.one('450_live_tail_'+c.recipe);c.tail_count=len(c.rows)-13;token.validate(c)
        require(c.status=='ACTIVE' and not c.rows[-1]['safety'] and not c.ledger.deadline_missed,'450_TAIL_PHYSICAL_SAFETY_PROGRESS_OR_TERMINAL')
        hit=arrival(c.rows,line,c.root_ledger.progress_m,exit_progress)
        if hit['reached']:break
    return hit,token


def prepare450(root):
    g=Path(__file__).resolve().parents[1];d=root/'stage450';assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage449/plan.json');v=read(root/'project-effective-budget-v469.json');proposal=read(g/'retry/next449_design.json')['primary_model_comparison']
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27436,84000,0)
    assert read(root/'stage449/result.json')['status']=='MODEL90_COMPARISON_COMPLETED'
    assert proposal['exit_from_original_root_m']==270. and proposal['planned_ticks']==1032 and proposal['planned_worlds']==6
    deadline=read(root/'research-deadline-current.json')['deadline_utc'];assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    files={Path(f):h for f,h in old['sources'].items()}
    for f in list(g.glob('retry/*450*.py'))+[g/'retry/next449_design.json',g/'retry/continuation449_result.json',root/'project-effective-budget-v469.json',root/'stage449/publication-private.json',root/'stage449/nominal1-private.json',root/'stage449/fullgas1-private.json']:
        files[f]=sha(f)
    semantic=dict(old['semantic_sources']);semantic.update({str(f):h for f,h in files.items() if str(f).startswith(str(g)) and f.suffix=='.py'})
    p=dict(stage=450,deadline_utc=deadline,fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],sources={str(f):h for f,h in files.items()},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],caps=dict(ticks=1152,worlds=8,CPU_s=90,wall_s=150),worst_planned_ticks=1032,worst_worlds=6,max_total_actions_each=64,max_same_live_actions_after_H13=51,common_exit_from_original_root_m=270.,new_actual_actions_resets_learning_seed_HOLDOUT_SEALED_reserve_paid=0,authorization='Explicit450 primary_model_comparison only: original native448 wrapper-end roots, own nominal,2 independent+held1 perbranch; no full lap or B policy composition.',source='Baseline native448 end is factual442 pre43; initialH13 factual439 gate on both copies plus current-first exact, qualified same-child H13 barrier before tail. Baseline finite continuation compared to factual442 with unchanged future replay limits before candidate. No future native labels for candidate.',stop='First source/restore/ledger/memory/RNG/geometry/repeat/fidelity/physical-safety/progress/technical/resource/deadline error stopsall, no retry/retune. No270m within64=>censor. Root,exit,64cap,pulse and thresholds fixed.',clock='Original observed native wrapper delta80/64ticks + model crossing raw bracket; no uncertain60/90 bracket concat. No old96tick recharge.',promotion='Both270m crossings+gates permit this single-hypothesis bounded-model contrast. Positive/overlap/negative/censor retained. No native270,hidden native solver equivalence,wholelap,pixel or method-family conclusion. Branch terminal state equality not required.')
    for f,h in files.items():assert sha(f)==h,f
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');checkpoint450(d,'PLAN_FROZEN',ticks=0,worlds=0)
    print('450 frozen1032ticks6worlds; hard1152/8 CPU90/wall150; actual0')


def study450(root,meter,children):
    d=meter.d;p=meter.p;fixed=read(Path(p['fixed_plan']));line=np.asarray(fixed['line']);pace=np.asarray(read(p['pace_path'])['frozen268'])
    factual=[json.loads(s) for s in (root/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()];results={};original=None
    for arm in ['nominal','fullgas']:
        require(arm=='nominal' or (results['nominal']['factual_source_passed'] and results['nominal']['held_first_passed']),'450_CANDIDATE_BEFORE_BASELINE_SOURCE')
        data=load_root449(root,arm);restore_root_rng449(data)
        if original is None:original=data['original']
        else:require(original==data['original'],'450_DIFFERENT_ORIGINAL_NATIVE_ROOT')
        held=new449(meter,data,fixed,pace,arm+'_held');children.append(held)
        before=copy.deepcopy(held.ctrl.memory());nominal=held.ctrl.act(held.m)
        ctx=capture_context(held.m,held.ctrl,before,nominal,data['ledger'],fixed,fingerprint(p['semantic_sources']),{},data['ledger'].digest())
        ctx.validate();require(ctx.gate()=='QUERY_CURRENT','450_CURRENT_ROOT_CONTEXT')
        ph,mh,rh=fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash();native_digest=data['ledger'].digest();pair=[];source=[]
        for rep in [1,2]:
            c=new449(meter,data,fixed,pace,arm+str(rep));children.append(c)
            try:
                c.initial13('450_initial13_'+arm)
                require(c.status=='ACTIVE' and c.initial_ok and c.initial_safe and c.initial_progress,'450_INITIAL13_FAILURE')
                initial_audit=None
                if arm=='nominal':
                    initial_audit=replay(c.rows,factual[42:55],fixed)
                    require(initial_audit['certified_prefix_actions']==13 and initial_audit['fresh_current_first_pass']>=1,'450_BASELINE_INITIAL13_SOURCE')
                    compare_first(data['ledger'],c.rows[0],factual[42],fixed);meter.qualification_passed=True
                require(meter.qualification_passed,'450_SOURCE_BEFORE_TAIL_OR_CANDIDATE')
                hit,token=continue450(c,ctx,line,original['progress_m']+270.,p['max_total_actions_each'])
                save_receipt(d/(c.label+'-same-live-tail-private.json'),dict(child_id=c.stream.child_id,H13_key=token.key,prefix_digest=token.prefix_digest,tail=asdict(c.stream.tail_record()),actual_execution_allowed=False))
                require((fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())==(ph,mh,rh),'450_HELD_OR_RNG_MUTATED')
                require(data['ledger'].digest()==native_digest,'450_NATIVE_LEDGER_MUTATED')
                full_audit=None
                if arm=='nominal':
                    full_audit=replay(c.rows,factual[42:42+len(c.rows)],fixed)
                    require(full_audit['certified_prefix_actions']==len(c.rows),'450_BASELINE_FULL_FINITE_SOURCE')
                source.append(dict(initial13=initial_audit,finite_continuation=full_audit))
                pair.append(dict(signature=c.signature(),first=copy.deepcopy(c.rows[0]),rows=copy.deepcopy(c.rows),hit=hit,tail_actions=c.tail_count))
            finally:c.dump(d);c.close()
        require(pair[0]==pair[1],'450_INDEPENDENT_REPEAT')
        held.one('450_held_first_'+arm,prepared_nominal=nominal,prepared_before=before);proof=compare_frames(held.rows[0],pair[0]['first'])
        require(proof['passed'] and not proof['wheel']['clipped_flag_mismatches'],'450_HELD_FIRST_PHYSICAL')
        require(all(held.rows[0][k]==pair[0]['first'][k] for k in ['command','memory_before','memory_after']),'450_HELD_MEMORY_OR_COMMAND')
        held.dump(d);held.close();require(rnghash()==rh and data['ledger'].digest()==native_digest,'450_FINAL_NATIVE_LEDGER_OR_RNG')
        hit=pair[0]['hit'];cumulative=[(data['native_prefix_ticks']+tick)/50 for tick in hit['rawtick_bracket']] if hit['reached'] else None
        results[arm]=dict(status='MODEL_EXIT270_REACHED' if hit['reached'] else 'CENSORED_TOTAL64',actions_each=len(pair[0]['rows']),tail_actions_each=pair[0]['tail_actions'],initial13_same_child_continuation=True,model_tail_crossing=hit,observed_native_wrapper_delta_ticks=data['native_prefix_ticks'],cumulative_from_original_root_s=cumulative,factual_source_passed=arm=='nominal',held_first_passed=True,independent_repeat_exact=True,future_candidate_actual_qualified=False,same_native_live_solver=False)
        save(d/(arm+'-source-proof-private.json'),dict(native_root_full_digest=fingerprint(data['full']),native_ledger=asdict(data['ledger']),original=original,source_audits=source,held_first=proof,global_RNG_verified_against_native_hashes=True))
        save(d/'branch-results.json',results);checkpoint450(d,'BRANCH_CLOSED',arm=arm,status=results[arm]['status'],ticks=meter.b['ticks'],worlds=meter.b['worlds'])
        print(json.dumps(dict(stage=450,arm=arm,status=results[arm]['status'],actions=len(pair[0]['rows']),ticks=meter.b['ticks'],worlds=meter.b['worlds'],cumulative=cumulative)),flush=True)
    return results


def run450(root):
    d=root/'stage450';p=read(d/'plan.json');assert not(d/'opening.json').exists() and read(d/'static-result.json')['passed']
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256']
    for group in [p['sources'],p['protected'],p['original408_preserve']]:
        for f,h in group.items():assert sha(f)==h,f
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    meter=Meter444(d);children=[];results={};status='STARTED';error=None
    def timeout(*args):raise ResourceStop('450_CPU90_wall150')
    previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    signal.setitimer(signal.ITIMER_PROF,max(.001,90-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,150-(time.perf_counter()-WORKER_START)))
    try:results=study450(root,meter,children);status='MODEL270_COMPARISON_COMPLETED'
    except BaseException as e:
        status='STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for c in children:
            if not c.closed:
                try:c.dump(d);c.close()
                except BaseException as e:save(d/(c.label+'-cleanup-stop-private.json'),dict(error=type(e).__name__+': '+str(e)))
        meter.closeall();meter.persist()
        for s,h in previous.items():signal.signal(s,h)
    if not results and(d/'branch-results.json').exists():results=read(d/'branch-results.json')
    gain=None
    if len(results)==2 and all(x['cumulative_from_original_root_s'] is not None for x in results.values()):
        a=results['nominal']['cumulative_from_original_root_s'];b=results['fullgas']['cumulative_from_original_root_s'];gain=[a[0]-b[1],a[1]-b[0]]
    q=dict(stage=450,status=status,error=error,branches=results,gain270_bracket_s=gain,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),new_actual_actions_resets_learning_seed_HOLDOUT_SEALED_reserve_paid=0)
    save(d/'result.json',q);checkpoint450(d,'CLOSED',status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds']);print(json.dumps(dict(stage=450,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],gain=gain)))

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare450(root) if sys.argv[1]=='prepare' else run450(root)
