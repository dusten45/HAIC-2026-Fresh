"""Separate single current B decision after exact recorded MODEL prefix replay."""
from retry.composition451 import *
from retry.segment451 import Parent451,Segment451,forbidden_nominal451
from retry.receipt421_io import receipt_digest

class Parent452(Parent451):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self._replay452=False;self.stream.tail_record=forbidden_nominal451
    def one(self,*args,**kwargs):
        if self.segment451 is None:require(self._replay452 and len(self.rows)<48,'452_ONLY_REGISTERED_MODEL_SOURCE_REPLAY')
        return super().one(*args,**kwargs)
    def replay_source_one(self,frame):
        require(self.segment451 is None and len(self.rows)<48,'452_REPLAY48_CAP')
        self._replay452=True
        try:self.one('452_RECORDED_MODEL_SOURCE_REPLAY',first_override=frame['command'])
        finally:self._replay452=False
        require(self.status=='ACTIVE' and self.rows[-1]==frame,'452_RECORDED_MODEL_SOURCE_FRAME_NOT_EXACT')
    def begin_current_one(self,actual,d):
        require(self.segment451 is None and len(self.rows)==48 and self.status=='ACTIVE','452_CURRENT_ONE_BEGIN')
        save_receipt(d/(self.label+'-recorded-model-prefix48-private.json'),dict(rows=self.rows,snapshot=snapshot(self.m),memory=self.ctrl.memory(),ledger=asdict(self.ledger),immutable_native_ledger=asdict(actual),scope='FIXED451_MODEL_SOURCE_REPLAY_NOT_NATIVE_FACT_NOT_NEW_POLICY_SELECTION'))
        self.segment451=Segment451(self,self.m,self.stream,actual,actual.digest(),48,fingerprint(self.rows),self.ledger.last_clock_tick,self.m.native_ticks)
        self.segment451.validate(self,actual)
    def guarded_one(self,*args,**kwargs):
        require(self.segment451 is not None and len(self.rows)==48,'452_SECOND_NEW_CURRENT_DECISION_FORBIDDEN')
        return super().guarded_one(*args,**kwargs)
    def evidence(self,*args,**kwargs):return forbidden_nominal451()
    def continue_tail(self,*args,**kwargs):return forbidden_nominal451()
    def dump(self,d):
        super().dump(d)
        from retry.loss389_analyze import read,save
        path=d/(self.label+'-private.json');value=read(path)
        value.pop('nominal_prefix_actions',None);value.pop('guarded_actions',None)
        value.update(policy='RECORDED451_MODEL_SOURCE48_THEN_ONE_NEW_CURRENT_B',recorded_model_prefix_actions=min(48,len(self.rows)),new_current_actions=max(0,len(self.rows)-48),nominal_only_ranking_forbidden=True,native_facts_produced=0)
        save(path,value)


def checkpoint452(d,phase,**facts):
    save(d/'progress-private.json',dict(stage=452,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**facts))


class Study452(Study451):
    def __init__(self,root,meter):
        super().__init__(root,meter);self.data=load_root449(root,'fullgas');self.actual=self.data['ledger'];self.source=read(root/'stage451/fullgas1-private.json')
        require(len(self.source['rows'])==48 and self.source['guarded_actions']==14,'452_SOURCE48_FIXED')
        self.policy_digest=fingerprint(dict(policy='452_SINGLE_CURRENT_B_SAME_451_RULE',sources=self.p['semantic_sources']))
    def replay_parent(self,label):
        data=self.data;self.meter.capture_inputs(data['state'],data['memory'],self.actual,label+'_inputs',gate='452_NATIVE448_ROOT_RECORDED_MODEL451_SOURCE_REPLAY')
        c=Parent452(self.meter,copy.deepcopy(data['state']),copy.deepcopy(data['memory']),self.actual,self.fixed,self.pace,label,world_tag=label);self.children.append(c)
        for frame in self.source['rows']:c.replay_source_one(frame)
        require(snapshot(c.m)==self.source['final_state'] and c.ctrl.memory()==self.source['controller_memory'] and asdict(c.ledger)==self.source['model_ledger'],'452_SOURCE_END_STATE_MEMORY_LEDGER_NOT_EXACT')
        c.begin_current_one(self.actual,self.d)
        checkpoint452(self.d,'MODEL_SOURCE48_REPLAYED',label=label,ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])
        return c
    def run_one(self):
        restore_root_rng449(self.data);actual_digest=self.actual.digest()
        held=self.replay_parent('candidate_held');held_before=copy.deepcopy(held.ctrl.memory());held_nominal=held.ctrl.act(held.m)
        held_query=bind_model_query(held,self.actual,held_before,held_nominal,self.fixed,self.policy_digest)
        ph,mh,rh=fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash();pair=[]
        for rep in [1,2]:
            parent=self.replay_parent('candidate'+str(rep))
            try:
                before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m)
                query,selected,record=select451(self,parent,before,nominal,parent.label+'_one')
                report=parent.guarded_one(query,self.actual,selected,nominal,before,'452_SINGLE_NEW_SELECTED_PARENT')
                require(len(parent.rows)==49,'452_EXACT_ONE_NEW_PARENT_STEP')
                require((fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())==(ph,mh,rh),'452_HELD_CHANGED')
                require(self.actual.digest()==actual_digest,'452_NATIVE_LEDGER_CHANGED')
                pair.append(dict(signature=parent.signature(),selected=selected,context_digest=query.context_digest,record=record,report=report))
                save(self.d/(parent.label+'-new-decision-private.json'),dict(record=record,report=report,selected_recipe=selected['recipe']))
            finally:parent.dump(self.d);parent.close()
        require(pair[0]==pair[1],'452_REQUIRED_REPEAT_NOT_EXACT')
        held_query.validate(held,self.actual);require(held_query.context_digest==pair[0]['context_digest'],'452_HELD_CURRENT_CONTEXT_NOT_IDENTICAL')
        held_report=held.guarded_one(held_query,self.actual,pair[0]['selected'],held_nominal,held_before,'452_HELD_NEW_SELECTED_FIRST')
        require(len(held.rows)==49 and rnghash()==rh and self.actual.digest()==actual_digest,'452_HELD_SCOPE_OR_NATIVE_RNG_CHANGED')
        save(self.d/'held-first-private.json',dict(passed=True,report=held_report,context_digest=held_query.context_digest,required_context_digest=pair[0]['context_digest']))
        held.dump(self.d);held.close()
        recipe=pair[0]['selected']['recipe']
        return dict(outcome='NOMINAL_SAFE_RECOVERY_IN_NEW_SINGLE_DECISION' if recipe=='nominal' else 'NEUTRAL_RESELECTED_RECOVERY_NOT_WITNESSED',selected_recipe=recipe,new_parent_actions_each=1,source_model_replay_actions_each=48,required_repeat_exact=True,held_first_passed=True,source_replay_exact=True,nominal_only_ranking_forbidden=True,current_record=pair[0]['record'],original451_status_preserved='CENSORED_NO_RECOVERY14',original451_uncensored=False,common_exit_gain=None,whole_policy_or_native_lap_qualified=False)


def prepare452(root):
    g=Path(__file__).resolve().parents[1];d=root/'stage452';assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage451/plan.json');v=read(root/'project-effective-budget-v471.json');proposal=read(g/'retry/next451_design.json')
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27436,84000,0)
    result=read(root/'stage451/result.json');assert result['status']=='B_COMPOSITION_SCOPE_COMPLETED' and result['branches']['fullgas']['status']=='CENSORED_NO_RECOVERY14'
    assert read(root/'stage451/closure-checks-private.json')['candidate_B15_not_executed']
    assert proposal['cost']['planned_ticks']==1004 and proposal['cost']['planned_worlds']==11
    deadline=read(root/'research-deadline-current.json')['deadline_utc'];assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    files={Path(f):h for f,h in old['sources'].items()}
    for f in list(g.glob('retry/*452*.py'))+[g/'retry/next451_design.json',g/'retry/composition451_result.json',root/'project-effective-budget-v471.json',root/'stage451/publication-private.json',root/'stage451/result.json',root/'stage451/closure-checks-private.json',root/'stage451/fullgas1-private.json',root/'stage451/fullgas2-private.json']:
        files[f]=sha(f)
    for f in (root/'stage451').glob('fullgas*-prefix-source-private.json'):files[f]=sha(f)
    semantic=dict(old['semantic_sources']);semantic.update({str(f):h for f,h in files.items() if str(f).startswith(str(g)) and f.suffix=='.py'})
    p=dict(stage=452,deadline_utc=deadline,fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],sources={str(f):h for f,h in files.items()},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],caps=dict(ticks=1024,worlds=16,CPU_s=90,wall_s=150),worst_planned_ticks=1004,worst_worlds=11,recorded_model_source_actions=48,new_current_decisions_each=1,authorization='Explicit452 candidate-only reconstructed single current B decision; immutable451 censor. No second new decision/native/full lap.',reuse='Frozen450/451 baseline source/current-view/segment/held/physics qualifications retained by hashes; exactly replay451 MODEL tape on3 new worlds fromnative448. No new native fact or policy selection in source replay. Fresh typed B query for exactly one decision withrequired2+held1.',stop='First prefix/source/restore/authority/ledger/memory/RNG/repeat/fidelity/technical/selected-parent safety/progress/resource/deadline error stopsall, no retry/root/policy/H13/scope/tolerance changes. Registered rejected nonselected alternatives as451.',outcome='Nominal-safe recovery or neutral reselection in this new scope only. Original451 staysCENSORED_NO_RECOVERY14. No second new decision/no common-exit gain/lap/pixel claim.',new_actual_actions_resets_learning_seed_HOLDOUT_SEALED_reserve_paid=0)
    for f,h in files.items():assert sha(f)==h,f
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');checkpoint452(d,'PLAN_FROZEN',ticks=0,worlds=0)
    print('452 frozen1004ticks11worlds; hard1024/16 CPU90/wall150; one new decision actual0')


def run452(root):
    d=root/'stage452';p=read(d/'plan.json');assert not(d/'opening.json').exists() and read(d/'static-result.json')['passed']
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256']
    for group in [p['sources'],p['protected'],p['original408_preserve']]:
        for f,h in group.items():assert sha(f)==h,f
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()));meter=Meter444(d);study=None;result={};status='STARTED';error=None
    def timeout(*args):raise ResourceStop('452_CPU90_wall150')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    signal.setitimer(signal.ITIMER_PROF,max(.001,90-time.process_time()));signal.setitimer(signal.ITIMER_REAL,max(.001,150-(time.perf_counter()-WORKER_START)))
    try:study=Study452(root,meter);result=study.run_one();status='SINGLE_CURRENT_DECISION_SCOPE_COMPLETED'
    except BaseException as e:status='STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        if study:
            for c in study.children:
                if not c.closed:
                    try:c.dump(d);c.close()
                    except BaseException as e:save(d/(c.label+'-cleanup-stop-private.json'),dict(error=type(e).__name__+': '+str(e)))
        meter.closeall();meter.persist()
        for s,h in handlers.items():signal.signal(s,h)
    out=dict(stage=452,status=status,error=error,result=result,budget=read(d/'budget.json'),plan_sha256=sha(d/'plan.json'),original451_censor_preserved=True,new_actual_actions_resets_learning_seed_HOLDOUT_SEALED_reserve_paid=0)
    save(d/'result.json',out);checkpoint452(d,'CLOSED',status=status,error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds']);print(json.dumps(dict(stage=452,status=status,error=error,outcome=result.get('outcome'),ticks=meter.b['ticks'],worlds=meter.b['worlds'])))

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare452(root) if sys.argv[1]=='prepare' else run452(root)
