"""One same-live-child H1 study; no archival restore at H13, no actual API."""
from retry.experiment444 import *
import hashlib
import pickle
import random
from retry.live447 import check_historical_h13,LiveH13447


def checkpoint(d,phase,**facts):
    save(d/'progress-private.json',dict(stage=447,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**facts))


class Study447(Experiment):
    def __init__(self,root,d,meter):
        super().__init__(root,d,meter)
        proof=load_receipt(Path(self.p['original_inputs']['nominal']))
        other=load_receipt(Path(self.p['original_inputs']['fullgas']))
        if any(proof[k]!=other[k] for k in ['state','memory','ledger','RNG_digest']):
            raise TechnicalStop('original_branch_roots_differ')
        self.state=proof['state'];self.memory=proof['memory']
        if asdict(self.actual)!=proof['ledger']:
            raise TechnicalStop('original_actual_root_ledger_mismatch')
        blob=proof['global_RNG_pickle']
        if hashlib.sha256(blob).hexdigest()!=proof['RNG_digest']:
            raise TechnicalStop('original_input_RNG_digest')
        py,numpy=pickle.loads(blob);random.setstate(py);np.random.set_state(numpy)
        self.prefix_source_gates=[]

    def study(self):
        results={}
        for recipe in ['nominal','fullgas']:
            archive=read(Path(self.p['archives'][recipe]))
            held=self.new(self.state,self.memory,self.actual,recipe+'_held')
            before=copy.deepcopy(held.ctrl.memory());nominal=held.ctrl.act(held.m)
            ctx=capture_context(held.m,held.ctrl,before,nominal,self.actual,self.fixed,
                                fingerprint(self.p['sources']),{},self.actual_stamp)
            ph,mh,rh=fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash()
            pair=[]
            for rep in range(2):
                c=self.new(self.state,self.memory,self.actual,recipe+str(rep+1),recipe)
                try:
                    c.initial13('H13_'+recipe)
                    check_historical_h13(c,archive)
                    if recipe=='nominal':
                        expected=self.rows[22:35]
                        audit=replay(c.rows,expected,self.fixed)
                        if audit['certified_prefix_actions']!=13 or audit['fresh_current_first_pass']<1:
                            raise TechnicalStop('baseline_factual_H13_gate')
                        compare_first(self.actual,c.rows[0],expected[0],self.fixed)
                        self.prefix_source_gates.append(audit)
                        self.meter.qualification_passed=True
                    elif len(self.prefix_source_gates)!=2:
                        raise TechnicalStop('candidate_before_baseline_source_repeat_gate')
                    c.stream.prepare_boundary(ctx)
                    token=LiveH13447.seal(c);c.stream.start_tail();token.validate(c)
                    save_receipt(self.d/(c.label+'-same-live-H13-private.json'),dict(child_id=c.stream.child_id,H13_key=token.key,prefix_digest=token.prefix_digest,original444_H13_exact=True,actual_qualified=False))
                    hit=dict(reached=False,rawtick_bracket=None,elapsed_bracket_s=None,interpolated=False)
                    for k in range(13):
                        token.validate(c)
                        c.one('same_live_tail_'+recipe);c.tail_count=k+1
                        token.validate(c)
                        if c.status!='ACTIVE':raise PhysicalStop(recipe+'_same_live_'+c.status)
                        hit=arrival(c.rows,np.asarray(self.fixed['line']),self.actual.progress_m,self.actual.progress_m+60.)
                        if hit['reached']:break
                    if(fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())!=(ph,mh,rh):
                        raise TechnicalStop('held_parent_or_RNG_mutated')
                    pair.append(dict(signature=c.signature(),rows=copy.deepcopy(c.rows),hit=hit,tail_actions=c.tail_count))
                    save_receipt(self.d/(c.label+'-finite-live-tail-private.json'),asdict(c.stream.tail_record()))
                finally:self.close(c)
            if pair[0]['signature']!=pair[1]['signature'] or pair[0]['hit']!=pair[1]['hit']:
                raise TechnicalStop('same_live_independent_repeat')
            held.one('held_first_'+recipe,first_override=pair[0]['rows'][0]['command'],prepared_nominal=nominal,prepared_before=before)
            expected_first=pair[0]['rows'][0]
            check=compare_frames(held.rows[0],expected_first)
            if not check['passed'] or check['wheel']['clipped_flag_mismatches']:
                raise TechnicalStop('held_own_nominal_first_gate')
            self.close(held)
            results[recipe]=dict(status='EXIT60_REACHED' if pair[0]['hit']['reached'] else 'CENSORED_EXTRA13',
                                 actions_each=len(pair[0]['rows']),tail_actions_each=pair[0]['tail_actions'],
                                 crossing_from_original_root=pair[0]['hit'],historical_H13_exact=True,
                                 source_gate_passed=(recipe=='nominal'),held_first_passed=True,independent_repeat_exact=True,
                                 same_live_child_across_H13=True,actual_physics_qualified=False)
            save(self.d/'branch-results.json',results)
            checkpoint(self.d,'BRANCH_CLOSED',recipe=recipe,status=results[recipe]['status'],ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])
        return results


def prepare(root):
    g=Path(__file__).resolve().parents[1];d=root/'stage447'
    assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage446/plan.json');v=read(root/'project-effective-budget-v466.json')
    deadline=read(root/'research-deadline-current.json')['deadline_utc']
    assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27516,84000,0)
    files={Path(f):h for f,h in old['sources'].items()}
    files.update({f:sha(f) for f in g.glob('retry/*447*.py')})
    inputs={recipe:str(root/f'stage444/H1/{recipe}1_inputs-before-integration-private.json') for recipe in ['nominal','fullgas']}
    archives={recipe:str(root/f'stage444/H1/{recipe}1-private.json') for recipe in ['nominal','fullgas']}
    for f in [*(Path(x) for x in inputs.values()),*(Path(x) for x in archives.values()),g/'retry/next446_design.json',root/'project-effective-budget-v466.json']:
        files[f]=sha(f)
    semantic=dict(old['semantic_sources']);semantic.update({str(f):h for f,h in files.items() if str(f).startswith(str(g)) and f.suffix=='.py'})
    p=dict(stage=447,root_step=23,horizon=13,deadline_utc=deadline,fixed_plan=old['fixed_plan'],sources={str(f):h for f,h in files.items()},
           semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],original_inputs=inputs,archives=archives,
           caps=dict(ticks=512,worlds=8,CPU_s=90,wall_s=150),worst_planned_ticks=4*(13+13)*4+2*4,worst_worlds=6,
           actual_reset_learning_new_seed_HOLDOUT_SEALED_reserve_paid=0,
           stop='First technical/source/historicalH13/fidelity/safety/ledger/RNG/repeat failure stopsall; no retry/retune. Missing60m inextra13=>censor, no boundary/horizon change.')
    assert p['worst_planned_ticks']==424<=512
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');checkpoint(d,'PLAN_FROZEN',ticks=0,worlds=0)
    print('447 same-live study frozen424ticks6worlds; hard512/8; baseline before candidate')


def run447(root):
    d=root/'stage447';p=read(d/'plan.json');assert not(d/'opening.json').exists() and read(d/'static-result.json')['passed']
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
    for group in [p['sources'],p['protected']]:
        for f,h in group.items():assert sha(f)==h,f
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    meter=Meter444(d);ex=None;results={};status='STARTED';error=None
    def timeout(*args):raise ResourceStop('447_time_cap')
    previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    signal.setitimer(signal.ITIMER_PROF,max(.001,90-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,150-(time.perf_counter()-WORKER_START)))
    try:ex=Study447(root,d,meter);results=ex.study();status='SAME_LIVE_STUDY_COMPLETED'
    except PhysicalStop as e:status='PHYSICAL_STOP';error=str(e)
    except BaseException as e:
        status='TECHNICAL_STOP';error=type(e).__name__+': '+str(e)
        save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        if ex:
            for c in ex.children:
                if not c.closed:
                    try:ex.close(c)
                    except BaseException:pass
        meter.closeall();meter.persist();signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for s,h in previous.items():signal.signal(s,h)
    if not results and(d/'branch-results.json').exists():results=read(d/'branch-results.json')
    gain=None
    if len(results)==2 and all(v['crossing_from_original_root']['reached'] for v in results.values()):
        a=results['nominal']['crossing_from_original_root']['elapsed_bracket_s'];b=results['fullgas']['crossing_from_original_root']['elapsed_bracket_s'];gain=[a[0]-b[1],a[1]-b[0]]
    out=dict(stage=447,status=status,error=error,branches=results,gain60_bracket_s=gain,budget=read(d/'budget.json'),
             source_gates=[] if ex is None else ex.prefix_source_gates,
             actual_actions_resets_learning_new_seed_SEALED_reserve_paid=0,plan_sha256=sha(d/'plan.json'))
    save(d/'result.json',out);checkpoint(d,'CLOSED',status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'])
    print(json.dumps(dict(stage=447,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],gain=gain)))


if __name__=='__main__':
    root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run447(root)
