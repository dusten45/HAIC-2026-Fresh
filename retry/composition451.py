"""Approved finite H1+B composition, no native or full-lap execution."""
from retry.continuation450 import *
from retry.segment451 import Parent451
from retry.guard451 import select451
from retry.query445 import bind_model_query
from retry.paired417_common import SourceC


def checkpoint451(d,phase,**facts):
    save(d/'progress-private.json',dict(stage=451,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**facts))


class PrefixCensored451(RuntimeError):pass

class Study451:
    def __init__(self,root,meter):
        self.root=root;self.d=meter.d;self.meter=meter;self.p=meter.p;self.fixed=read(Path(self.p['fixed_plan']));self.pace=np.asarray(read(self.p['pace_path'])['frozen268']);self.children=[];self.actual=None
        self.factual=[json.loads(s) for s in (root/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()]
        self.policy_digest=fingerprint(dict(policy='451_FIXED_H13_NOMINAL_THEN_NEUTRAL_FIRST_INTERVENTION',sources=self.p['semantic_sources']))
    def new(self,state,memory,ledger,label,recipe='nominal',guardian=False):
        require(guardian,'451_SHADOW_FACTORY_REQUIRES_GUARDIAN_CHANNEL')
        self.meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='451_CURRENT_MODEL_VALUE_VIEW_SHADOW_ONLY')
        c=GuardianChild(self.meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,self.fixed,self.pace,label,recipe=recipe,world_tag=label);self.children.append(c);return c
    def prefix(self,data,arm,label):
        self.meter.capture_inputs(data['state'],data['memory'],data['ledger'],label+'_inputs',gate='451_OBSERVED_NATIVE448_ROOT_MODEL_PARENT')
        c=Parent451(self.meter,copy.deepcopy(data['state']),copy.deepcopy(data['memory']),data['ledger'],self.fixed,self.pace,label,recipe='nominal',world_tag=label);self.children.append(c)
        initial=fingerprint(snapshot(c.m));memory=fingerprint(c.ctrl.memory());rh=rnghash()
        before=copy.deepcopy(c.ctrl.memory());temp=SourceC(self.fixed,self.pace,copy.deepcopy(before));nominal=temp.act(c.m)
        ctx=capture_context(c.m,temp,before,nominal,self.actual,self.fixed,self.policy_digest,{},self.actual.digest());ctx.validate()
        require(ctx.gate()=='QUERY_CURRENT' and (fingerprint(snapshot(c.m)),fingerprint(c.ctrl.memory()),rnghash())==(initial,memory,rh),'451_PREFIX_CONTEXT_MUTATION')
        c.initial13('451_prefix_initial13_'+arm)
        require(c.status=='ACTIVE' and c.initial_ok and c.initial_safe and c.initial_progress,'451_PREFIX_INITIAL13_SAFETY')
        first_audit=full_audit=None
        if arm=='nominal':
            first_audit=replay(c.rows,self.factual[42:55],self.fixed)
            require(first_audit['certified_prefix_actions']==13 and first_audit['fresh_current_first_pass']>=1,'451_PREFIX_INITIAL_SOURCE_G1')
            compare_first(self.actual,c.rows[0],self.factual[42],self.fixed);self.meter.qualification_passed=True
        require(self.meter.qualification_passed,'451_PREFIX_BEFORE_BASELINE_SOURCE')
        hit,token=continue450(c,ctx,np.asarray(self.fixed['line']),data['original']['progress_m']+270.,64)
        if not hit['reached']:raise PrefixCensored451('451_PREFIX270_CENSORED_NO_GUARDED_SEGMENT')
        original=read(self.root/'stage450'/(arm+'1-private.json'))
        require(c.rows==original['rows'] and snapshot(c.m)==original['final_state'] and c.ctrl.memory()==original['controller_memory'] and asdict(c.ledger)==original['model_ledger'],'451_PREFIX450_NOT_EXACT')
        if arm=='nominal':
            full_audit=replay(c.rows,self.factual[42:42+len(c.rows)],self.fixed)
            require(full_audit['certified_prefix_actions']==len(c.rows),'451_PREFIX_FULL_SOURCE')
        require(self.actual.digest()==data['ledger'].digest() and rnghash()==rh,'451_PREFIX_NATIVE_ROOT_OR_RNG_CHANGED')
        save(self.d/(label+'-prefix-source-private.json'),dict(initial13=first_audit,finite_continuation=full_audit,prefix450_exact=True,H13_key=token.key,actions=len(c.rows),native_root_ledger=asdict(self.actual),hit=hit))
        c.begin_guarded(self.actual,self.d)
        checkpoint451(self.d,'PREFIX270_SEALED',arm=arm,label=label,ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'],prefix_actions=len(c.rows))
        return c
    def probe(self,parent,arm):
        choices=[];records=[];first=None;first_context=None;first_neutral=None;recovery=None
        for k in range(1,15):
            before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m)
            label=parent.label+'_B'+str(k);query,selected,record=select451(self,parent,before,nominal,label)
            if first is None:first=copy.deepcopy(selected);first_context=query.context_digest
            report=parent.guarded_one(query,self.actual,selected,nominal,before,'451_selected_B_parent_'+arm)
            choices.append(selected['recipe'])
            if selected['recipe']=='neutralbrake' and first_neutral is None:first_neutral=k
            elif selected['recipe']=='nominal' and first_neutral is not None:recovery=k
            record.update(decision=k,first_neutral=first_neutral,recovery=recovery,own_parent_verification=report,parent_clock=parent.ledger.last_clock_tick,parent_progress_m=parent.ledger.progress_m,nominal_only_ranking_forbidden=True)
            records.append(record);save(self.d/(parent.label+'-B-decisions-private.json'),records)
            checkpoint451(self.d,'B_PARENT_TRANSITION_VERIFIED',arm=arm,label=parent.label,decision=k,recipe=selected['recipe'],first_neutral=first_neutral,recovery=recovery,ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])
            print(json.dumps(dict(stage=451,arm=arm,parent=parent.label,decision=k,recipe=selected['recipe'],first_neutral=first_neutral,recovery=recovery,ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])),flush=True)
            if recovery is not None:break
        status='FIRST_INTERVENTION_RECOVERY_WITNESSED' if recovery is not None else ('CENSORED_NO_TRIGGER14' if first_neutral is None else 'CENSORED_NO_RECOVERY14')
        return dict(status=status,signature=parent.signature(),choices=choices,first=first,first_context_digest=first_context,first_neutral=first_neutral,recovery=recovery,B_actions=len(choices),reports=records)
    def run(self):
        results={};original=None
        for arm in ['nominal','fullgas']:
            require(arm=='nominal' or results['nominal']['baseline_source_passed'],'451_CANDIDATE_BEFORE_BASELINE_SOURCE')
            data=load_root449(self.root,arm);restore_root_rng449(data);self.actual=data['ledger'];actual_digest=self.actual.digest()
            if original is None:original=data['original']
            else:require(original==data['original'],'451_DIFFERENT_ORIGINAL_NATIVE_ROOT')
            held=self.prefix(data,arm,arm+'_held')
            held_before=copy.deepcopy(held.ctrl.memory());held_nominal=held.ctrl.act(held.m)
            held_query=bind_model_query(held,self.actual,held_before,held_nominal,self.fixed,self.policy_digest)
            held_pose,held_memory,held_rng=fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash();pair=[]
            for rep in [1,2]:
                parent=self.prefix(data,arm,arm+str(rep))
                try:
                    value=self.probe(parent,arm);pair.append(value)
                    require((fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())==(held_pose,held_memory,held_rng),'451_HELD_MUTATED_DURING_GUARDED_PARENTS')
                    require(self.actual.digest()==actual_digest,'451_NATIVE_LEDGER_MUTATED')
                finally:parent.dump(self.d);parent.close()
            require(pair[0]==pair[1],'451_GUARDED_PARENT_INDEPENDENT_REPEAT')
            held_query.validate(held,self.actual)
            require(held_query.context_digest==pair[0]['first_context_digest'],'451_HELD_FIRST_CURRENT_CONTEXT_NOT_IDENTICAL')
            held_report=held.guarded_one(held_query,self.actual,pair[0]['first'],held_nominal,held_before,'451_held_selected_first_'+arm)
            save(self.d/(arm+'-held-first-private.json'),dict(passed=True,report=held_report,context_digest=held_query.context_digest,required_first_context_digest=pair[0]['first_context_digest'],RNG_unchanged=rnghash()==held_rng))
            require(rnghash()==held_rng and self.actual.digest()==actual_digest,'451_HELD_FINAL_NATIVE_LEDGER_RNG')
            held.dump(self.d);held.close()
            results[arm]=dict(status=pair[0]['status'],prefix_actions=held.segment451.prefix_actions,B_actions_each=pair[0]['B_actions'],choices=pair[0]['choices'],first_neutral_decision=pair[0]['first_neutral'],recovery_decision=pair[0]['recovery'],baseline_source_passed=arm=='nominal',independent_repeat_exact=True,held_first_passed=True,same_live_parent_prefix_to_B=True,nominal_only_tail_ranking_disabled=True,actual_native_DONE_allowed=False,common_exit_timing_rank=False)
            save(self.d/'branch-results.json',results);checkpoint451(self.d,'BRANCH_CLOSED',arm=arm,status=results[arm]['status'],ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])
        return results


def prepare451(root):
    g=Path(__file__).resolve().parents[1];d=root/'stage451';assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage450/plan.json');v=read(root/'project-effective-budget-v470.json');nextp=read(g/'retry/next450_design.json')
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27436,84000,0)
    assert read(root/'stage450/result.json')['status']=='MODEL270_COMPARISON_COMPLETED'
    assert nextp['planned_ticks']==13416 and nextp['planned_worlds']==230
    deadline=read(root/'research-deadline-current.json')['deadline_utc'];assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    files={Path(f):h for f,h in old['sources'].items()}
    for f in list(g.glob('retry/*451*.py'))+[g/'retry/next450_design.json',g/'retry/continuation450_result.json',root/'project-effective-budget-v470.json',root/'stage450/publication-private.json',root/'stage450/nominal1-private.json',root/'stage450/fullgas1-private.json',g/'retry/query445.py',g/'retry/experiment445.py']:
        files[f]=sha(f)
    semantic=dict(old['semantic_sources']);semantic.update({str(f):h for f,h in files.items() if str(f).startswith(str(g)) and f.suffix=='.py'})
    p=dict(stage=451,deadline_utc=deadline,fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],sources={str(f):h for f,h in files.items()},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],caps=dict(ticks=14336,worlds=256,CPU_s=420,wall_s=600),worst_planned_ticks=13416,worst_worlds=230,prefix_cap_each=64,guarded_cap_each=14,shadow_H=13,authorization='Explicit451 finite model-only H1+B first intervention/recovery, original native448 roots and live replay270prefix. No actual/full lap.',fixed_policy='Nominal H13 required/repeat first. Only registered observed physical or progress ineligibility permits neutral H13 required/repeat. Selected parent first vs fresh shadow fidelity and exact current memory/ledger/clock checks. End first neutral+one later nominal-safe transition or14actions.',alternative_rejection='Only path_error_over3m,damage_increase,collision_or_obstacle,road_loss_or_grass first observed shadow stop or exact predicted_progress_deadline. Reverse/unknown/technical/domain/authority/fidelity/repeat errors stop all. No unsafe selected parent permitted.',segment='Seal nominal270 prefix; same live parent thereafter guarded. Forbid nominal-only TailRecord/Completion/evidence ranking after B starts. Immutable native GoalLedger and actual DONE rights separate from ForecastLedger and model GoalLedger value view.',censor='No trigger or recovery within14 stays censored. Prefix no270 within64=>no B, preserve censor. No scope/policy/root/horizon/tolerance change or retry.',stop='First unexpected source/restore/ledger/memory/RNG/repeat/fidelity/technical/resource/deadline error or selected parent safety/progress failure stopsall, preserves facts and cost. Expected rejected nonselected alternatives are not selected-parent failures.',promotion='Finite model composition only; no common-exit timing rank or wholelap/native/11s/pixel/generalization claim. No-trigger is not blanket fallback coverage. Branch terminal equality not required.',new_actual_actions_resets_learning_seed_HOLDOUT_SEALED_reserve_paid=0)
    for f,h in files.items():assert sha(f)==h,f
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');checkpoint451(d,'PLAN_FROZEN',ticks=0,worlds=0)
    print('451 frozen13416ticks230worlds; hard14336/256 CPU420/wall600; actual0')


def run451(root):
    d=root/'stage451';p=read(d/'plan.json');assert not(d/'opening.json').exists() and read(d/'static-result.json')['passed']
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256']
    for group in [p['sources'],p['protected'],p['original408_preserve']]:
        for f,h in group.items():assert sha(f)==h,f
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    meter=Meter444(d);study=None;results={};status='STARTED';error=None
    def timeout(*args):raise ResourceStop('451_CPU420_wall600')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    signal.setitimer(signal.ITIMER_PROF,max(.001,420-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,600-(time.perf_counter()-WORKER_START)))
    try:study=Study451(root,meter);results=study.run();status='B_COMPOSITION_SCOPE_COMPLETED'
    except BaseException as e:
        status='PREFIX_CENSORED' if isinstance(e,PrefixCensored451) else 'STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        if study:
            for c in study.children:
                if not c.closed:
                    try:c.dump(d);c.close()
                    except BaseException as e:save(d/(c.label+'-cleanup-stop-private.json'),dict(error=type(e).__name__+': '+str(e)))
        meter.closeall();meter.persist()
        for s,h in handlers.items():signal.signal(s,h)
    if not results and(d/'branch-results.json').exists():results=read(d/'branch-results.json')
    out=dict(stage=451,status=status,error=error,branches=results,both_first_intervention_recovery_witnessed=len(results)==2 and all(x['status']=='FIRST_INTERVENTION_RECOVERY_WITNESSED' for x in results.values()),budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),new_actual_actions_resets_learning_seed_HOLDOUT_SEALED_reserve_paid=0,common_exit_gain_or_wholelap_claim=False)
    save(d/'result.json',out);checkpoint451(d,'CLOSED',status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds']);print(json.dumps(dict(stage=451,status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'],both_recovered=out['both_first_intervention_recovery_witnessed'])))

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare451(root) if sys.argv[1]=='prepare' else run451(root)
