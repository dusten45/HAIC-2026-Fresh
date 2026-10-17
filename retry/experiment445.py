"""445: only H2 query-value-view correction; frozen444 remains failed."""
from retry.experiment444 import *
from retry.query445 import bind_model_query

def checkpoint(directory, phase, **facts):
    save(directory/'progress-private.json',dict(stage=445,phase=phase,pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**facts))

class Experiment445(Experiment):
    def guardian_parent(self, label):
        p = self.new(self.state, self.memory, self.actual, label)
        choices = []
        try:
            for k in range(14):
                before = copy.deepcopy(p.ctrl.memory())
                nominal = p.ctrl.act(p.m)
                ph,mh,rh = fingerprint(snapshot(p.m)), fingerprint(p.ctrl.memory()), rnghash()
                query = bind_model_query(p, self.actual, before, nominal, self.fixed, '445_MODEL_QUERY')
                save_receipt(self.d/(label+f'_decision{k+1}-query-root-private.json'), dict(context=asdict(query.context),value_view_only=True,actual_root_digest=self.actual_stamp,actual_execution_allowed=False,actual_DONE_allowed=False))
                selected = None
                for recipe in ['nominal','neutralbrake']:
                    pair = []
                    for rep in range(2):
                        c = query.spawn(self, p, self.actual,
                                     label+f'_decision{k+1}_{recipe}{rep+1}', recipe)
                        try:
                            c.initial13('B_shadow')
                            if (fingerprint(snapshot(p.m)),fingerprint(p.ctrl.memory()),rnghash()) != (ph,mh,rh):
                                raise TechnicalStop('B_parent_query_mutated')
                            query.validate(p, self.actual)
                            pair.append(dict(signature=c.signature(), valid=c.initial_ok and c.initial_safe and c.initial_progress,
                                             first=copy.deepcopy(c.rows[0])))
                        finally:
                            self.close(c)
                    if pair[0]['signature'] != pair[1]['signature']:
                        raise TechnicalStop('B_shadow_repeat')
                    if pair[0]['valid']:
                        selected = pair[0]['first']
                        choices.append(recipe)
                        break
                if selected is None:
                    raise PhysicalStop('B_both_guardians_infeasible')
                # B is a model parent with conditional actions, not nominal C
                # planner continuation. Its observed generic H13 is diagnostic.
                old_progress, old_goal = p.ledger.progress_m, p.ledger.goal_m
                parent_before = snapshot(p.m)
                p.one('B_parent', first_override=selected['command'],
                      prepared_nominal=nominal, prepared_before=before)
                check = compare_frames(p.rows[-1],selected)
                if not check['passed'] or check['wheel']['clipped_flag_mismatches']:
                    raise TechnicalStop('B_own_parent_vs_selected_first')
                own = p.rows[-1]
                if own['memory_before'] != selected['memory_before'] or own['memory_after'] != selected['memory_after']:
                    raise TechnicalStop('B_first_nominal_memory_exact')
                if p.ledger.age_actions != selected['model_age'] or p.ledger.last_clock_tick != round(selected['predicted']['time']*50):
                    raise TechnicalStop('B_first_discrete_ledger')
                from retry.geometry439 import Projection439, Interval
                geometry = Projection439(self.fixed['line'], sum(self.fixed['free_profile']['ds']), .1)
                h0, h1 = own['raw_hull'][0], selected['raw_hull'][0]
                pose = lambda h:dict(pos=h['origin_position'],vel=h['COM_linear_velocity'])
                post = lambda r:dict(pos=r['predicted']['position'],vel=r['predicted']['velocity'])
                transition = geometry.transition(pose(h0),post(own),pose(h1),post(selected),before['C']['phase'],own['memory_after']['C']['phase'])
                bound = geometry.progress_interval(Interval.point(old_progress),transition)
                if not(bound.contains(p.ledger.progress_m) and bound.contains(selected['model_progress'])) or ((p.ledger.progress_m>=old_goal)!=(selected['model_progress']>=old_goal)):
                    raise TechnicalStop('B_model_ledger_geometry_or_goal_side')
                if p.status != 'ACTIVE':
                    raise PhysicalStop('B_parent_'+p.status)
                self.assert_actual()
                checkpoint(self.d,'B_DECISION_COMPLETE',label=label,decision=k+1,ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])
            return dict(signature=p.signature(), choices=choices, actions=len(p.rows),safe=True)
        finally:
            self.close(p)


    def qualify(self):
        super().qualify()
        checkpoint(self.d,'QUALIFICATION_PASSED',ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])


def prepare(root):
    g=Path(__file__).resolve().parents[1]
    d=root/'stage445'
    assert not d.exists();d.mkdir(mode=0o700)
    old=read(root/'stage444/H2/plan.json');v=read(root/'project-effective-budget-v464.json')
    deadline=read(root/'research-deadline-current.json')['deadline_utc']
    assert deadline==v['authorization_end_utc']=='2026-10-20T10:01:55Z'
    assert(v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27516,84000,0)
    assert read(root/'stage444/H2/result.json')['status']=='TECHNICAL_STOP'
    files={Path(x):h for x,h in old['sources'].items()}
    for f in list(g.glob('retry/*445*.py'))+[root/'project-effective-budget-v464.json',root/'stage444/H2/result.json',root/'stage444/H2/stop-private.json']:
        files[f]=sha(f)
    semantic=dict(old['semantic_sources'])
    semantic.update({str(f):h for f,h in files.items() if str(f).startswith(str(g)) and f.suffix=='.py'})
    p=dict(old,stage=445,authorization='Explicit445 H2once after value-view-only correction; H1extensiondesignonly; no retry',sources={str(f):h for f,h in files.items()},semantic_sources=semantic,
           correction='capture_context/model_ledger_view/ctx.ledger for model child root, immutable actual digest separately bound; no ForecastLedger.digest added',deadline_utc=deadline)
    assert p['worst_planned_ticks']==6164<=p['caps']['ticks']==6656
    assert p['worst_planned_worlds']==119<=p['caps']['worlds']==128
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    checkpoint(d,'PLAN_FROZEN',ticks=0,worlds=0)
    print('445 H2 only frozen6164ticks119worlds within6656/128; H1notrerun')


def run445(root):
    d=root/'stage445';p=read(d/'plan.json')
    assert not(d/'opening.json').exists() and read(d/'static-result.json')['passed']
    assert sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()
    for group in [p['sources'],p['protected']]:
        for f,h in group.items():assert sha(f)==h,f
    save(d/'opening.json',dict(pid=os.getpid(),at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    meter=Meter444(d);ex=None;outcome={};error=None
    def timeout(*args):raise ResourceStop('registered_model_time_signal')
    previous={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]}
    signal.setitimer(signal.ITIMER_PROF,max(.001,240-time.process_time()))
    signal.setitimer(signal.ITIMER_REAL,max(.001,480-(time.perf_counter()-WORKER_START)))
    checkpoint(d,'QUALIFICATION_STARTED',ticks=0,worlds=0)
    try:
        ex=Experiment445(root,d,meter);ex.qualify();outcome=ex.h2()
    except PhysicalStop as e:outcome=dict(status='PHYSICAL_REFUTATION',reason=str(e),promotion=False)
    except BaseException as e:
        error=type(e).__name__+': '+str(e);outcome=dict(status='TECHNICAL_STOP',error=error)
        save(d/'stop-private.json',dict(error=error,traceback=traceback.format_exc()))
    finally:
        if ex:
            for c in ex.children:
                if not c.closed:
                    try:ex.close(c)
                    except BaseException:pass
        meter.closeall();meter.persist()
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        for s,h in previous.items():signal.signal(s,h)
    q=dict(stage=445,hypothesis='H2',**outcome,budget=read(d/'budget.json'),qualification=None if ex is None else ex.qualification,
           arms=[] if ex is None else ex.arm_summaries,actual_actions_resets_learning_new_seed_SEALED=0,plan_sha256=sha(d/'plan.json'))
    save(d/'result.json',q);checkpoint(d,'HYPOTHESIS_CLOSED',status=q['status'],error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'])
    print(json.dumps(dict(stage=445,status=q['status'],error=error,ticks=meter.b['ticks'],worlds=meter.b['worlds'])))

if __name__=='__main__':
    root=Path(sys.argv[2]);prepare(root) if sys.argv[1]=='prepare' else run445(root)
