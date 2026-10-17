"""Approved model-only continuation to original-root+90m; actual calls absent."""
from retry.experiment444 import *
from retry.root449 import load_root449,restore_root_rng449
from retry.query448 import finite_guard448
from retry.receipt421_io import receipt_digest
from retry.ledger439 import require


def checkpoint449(d,phase,**facts):
    save(d/'progress-private.json',dict(stage=449,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**facts))


def new449(meter,data,fixed,pace,label):
    meter.capture_inputs(data['state'],data['memory'],data['ledger'],label+'_inputs',gate='449_OBSERVED_NATIVE_WRAPPER_END_RESTORED_MODEL_ONLY')
    c=Child(meter,copy.deepcopy(data['state']),copy.deepcopy(data['memory']),data['ledger'],fixed,pace,label,recipe='nominal',world_tag=label)
    require(c.ctrl.memory()==data['memory'] and c.m.t==data['full']['physical']['actual_time'],'449_ROOT_MEMORY_OR_CLOCK')
    require(c.ledger.actual_root_digest==data['ledger'].digest(),'449_ROOT_LEDGER_BINDING')
    return c


def prepare(root):
    g=Path(__file__).resolve().parents[1];d=root/'stage449';assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage448/plan.json');v=read(root/'project-effective-budget-v468.json');deadline=read(root/'research-deadline-current.json')['deadline_utc']
    assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27436,84000,0)
    assert read(root/'stage448/result.json')['status']=='NATIVE_EXIT60_PAIR_COMPLETED'
    files={Path(f):h for f,h in old['sources'].items()}
    for f in list(g.glob('retry/*449*.py'))+[g/'retry/next448_design.json',g/'retry/transfer448_result.json',root/'project-effective-budget-v468.json',root/'stage448/result.json',root/'stage448/publication-private.json',root/'stage442/actual_C0/C0_step43-before-native-private.json']:
        files[f]=sha(f)
    for arm in ['nominal','fullgas']:
        for f in (root/'stage448'/('actual_'+arm)).glob('*'):
            if f.is_file():files[f]=sha(f)
        data=load_root449(root,arm)
        f=root/'stage448'/(arm+'_current'+str(data['source_native_step']-22)+'_copy1_inputs-before-integration-private.json');files[f]=sha(f)
    semantic=dict(old['semantic_sources']);semantic.update({str(f):h for f,h in files.items() if str(f).startswith(str(g)) and f.suffix=='.py'})
    p=dict(stage=449,deadline_utc=deadline,fixed_plan=old['fixed_plan'],pace_path=str(root/'stage404/profiles-private.json'),sources={str(f):h for f,h in files.items()},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],caps=dict(ticks=256,worlds=8,CPU_s=60,wall_s=120),worst_planned_ticks=216,worst_worlds=6,max_actions_each=13,common_exit_from_original_root_m=90.,new_actual_actions_resets_learning_seed_HOLDOUT_SEALED_reserve_paid=0,authorization='Explicit449 only: native448 observed wrapper-end roots, own nominal max13, independent2+held1 perbranch, baseline factual442 first; no longer continuation/full lap.',stop='First source/fidelity/restore/ledger/memory/RNG/repeat/safety/progress/technical/resource/deadline error stopsall; no retry/retune. No90m within13=>censor, no horizon/exit/pulse change.',promotion='Both90m model crossings and all source gates needed for local model contrast only. Native90m/hidden warm-start equivalence/wholelap/pixel/generalization not established. Preserve overlap/small/negative/censor.',clock='Observed native whole wrapper clock delta80/64 ticks plus new model raw crossing bracket; do not add uncertain60m bracket or duplicate wrapper remainder.',source='Baseline native448 end equals factual442 pre43 full root; baseline finite forecast reused as factual calibration and contrast. First transition fresh-current exact and future replay439 distinct. Candidate own-native observed root only; future model not actual-qualified.')
    for f,h in files.items():assert sha(f)==h,f
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');checkpoint449(d,'PLAN_FROZEN',ticks=0,worlds=0)
    print('449 frozen216ticks6worlds; hard256/8 CPU60/wall120; actual0')


def study449(root,meter,children):
    d=meter.d;p=meter.p;fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);results={}
    actual442=[json.loads(s) for s in (root/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()]
    original=None
    for arm in ['nominal','fullgas']:
        require(arm=='nominal' or (results['nominal']['factual_source_passed'] and results['nominal']['held_first_passed']),'449_CANDIDATE_BEFORE_BASELINE')
        data=load_root449(root,arm);restore_root_rng449(data)
        if original is None:original=data['original']
        else:require(original==data['original'],'449_DIFFERENT_ORIGINAL_ROOT')
        held=new449(meter,data,fixed,pace,arm+'_held');children.append(held)
        before=copy.deepcopy(held.ctrl.memory());nominal=held.ctrl.act(held.m)
        ph,mh,rh=fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash();native_digest=data['ledger'].digest();pair=[];audits=[]
        for rep in [1,2]:
            c=new449(meter,data,fixed,pace,arm+str(rep));children.append(c)
            try:
                hit=finite_guard448(c,'449_own_nominal_'+arm,np.asarray(fixed['line']),original['progress_m']+90.)
                require((fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())==(ph,mh,rh),'449_HELD_PARENT_OR_RNG_CHANGED')
                require(data['ledger'].digest()==native_digest,'449_NATIVE_LEDGER_CHANGED')
                if arm=='nominal':
                    expected=actual442[42:42+len(c.rows)];audit=replay(c.rows,expected,fixed)
                    require(audit['certified_prefix_actions']==len(c.rows) and audit['fresh_current_first_pass']>=1,'449_BASELINE_FACTUAL442_SOURCE_G1')
                    compare_first(data['ledger'],c.rows[0],expected[0],fixed);audits.append(audit)
                pair.append(dict(signature=c.signature(),first=copy.deepcopy(c.rows[0]),rows=copy.deepcopy(c.rows),hit=hit))
            finally:c.dump(d);c.close()
        require(pair[0]==pair[1],'449_INDEPENDENT_REPEAT')
        held.one('449_held_first_'+arm,prepared_nominal=nominal,prepared_before=before)
        proof=compare_frames(held.rows[0],pair[0]['first'])
        require(proof['passed'] and not proof['wheel']['clipped_flag_mismatches'],'449_HELD_FIRST_PHYSICS')
        require(all(held.rows[0][k]==pair[0]['first'][k] for k in ['command','memory_before','memory_after']),'449_HELD_FIRST_MEMORY_OR_COMMAND')
        held.dump(d);held.close();require(rnghash()==rh and data['ledger'].digest()==native_digest,'449_FINAL_RNG_OR_NATIVE_LEDGER')
        hit=pair[0]['hit'];cumulative=None
        if hit['reached']:cumulative=[(data['native_prefix_ticks']+tick)/50 for tick in hit['rawtick_bracket']]
        results[arm]=dict(status='MODEL_EXIT90_REACHED' if hit['reached'] else 'CENSORED_EXTRA13',actions_each=len(pair[0]['rows']),model_tail_crossing=hit,observed_native_wrapper_delta_ticks=data['native_prefix_ticks'],cumulative_from_original_root_s=cumulative,held_first_passed=True,independent_repeat_exact=True,factual_source_passed=arm=='nominal',future_candidate_actual_qualified=False,same_native_live_solver=False)
        save(d/(arm+'-source-proof-private.json'),dict(native_root_full_digest=fingerprint(data['full']),native_ledger=asdict(data['ledger']),original=original,source_audits=audits,held_first=proof,global_RNG_verified_against_native_hashes=True))
        save(d/'branch-results.json',results);meter.qualification_passed=True
        checkpoint449(d,'BRANCH_CLOSED',arm=arm,status=results[arm]['status'],ticks=meter.b['ticks'],worlds=meter.b['worlds'])
    return results


def run449(root):
    d=root/'stage449';p=read(d/'plan.json');assert not(d/'opening.json').exists() and read(d/'static-result.json')['passed']
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256']
    for group in [p['sources'],p['protected'],p['original408_preserve']]:
        for f,h in group.items():assert sha(f)==h,f
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    meter=Meter444(d);children=[];results={};error=None;status='STARTED'
    def timeout(*args):raise ResourceStop('449_CPU60_wall120')
    previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    signal.setitimer(signal.ITIMER_PROF,max(.001,60-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,120-(time.perf_counter()-WORKER_START)))
    try:results=study449(root,meter,children);status='MODEL90_COMPARISON_COMPLETED'
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
    q=dict(stage=449,status=status,error=error,branches=results,gain90_bracket_s=gain,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),new_actual_actions_resets_learning_seed_HOLDOUT_SEALED_reserve_paid=0)
    save(d/'result.json',q);checkpoint449(d,'CLOSED',status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds']);print(json.dumps(dict(stage=449,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],gain=gain)))

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run449(root)
