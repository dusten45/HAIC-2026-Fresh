"""Three frozen source-only arms from the preserved original raw96 state."""
import time
CPU = time.process_time()
import datetime, importlib.util, json, math, os, signal, subprocess, traceback
from collections import Counter
from pathlib import Path
import numpy as np
import retry.corner608 as previous
import retry.early609_core as core
from retry.clip561_core import atomic_write
old = previous.old
base = previous.base
G = previous.G
D = Path('/workspace/haic-response610-private')
CAPS = dict(model_attempted=180000, model_completed=180000, external_force=720000,
            internal_force=720000, total_force=1440000, geometry=600000)
REPLAY = previous.REPLAY


class Study(previous.Study):
    def __init__(self):
        self.task = old.d.rd(D/'TASK_STARTED-private.json')
        if (D/'PROCESS_STARTED-private.json').exists(): raise RuntimeError('610_NO_RETRY')
        atomic_write(D/'PROCESS_STARTED-private.json', dict(pid=os.getpid(), utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        static = old.d.rd(base.old.INPUTS['static'])
        old.prior.Meter.__init__(self, static, {})
        self.index=self.source_index; self.edge=self.source_edges
        self.paths=old.d.rd(base.old.INPUTS['candidate_paths'])
        self.geometry_context=base.old.tracking.geometry_context(self.static,600000)
        self.applied_journal=old.Journal(D/'applied-journal-private.jsonl')
        self.context=None; self.state=None; self.label='preparation'; self.saved=[]
        self.orig_geometry_margin=old.compiled_geometry.full.road_margin
        self.original_distance=old.compiled_geometry.distance
        self.original_plain_road=old.compiled_geometry.original.margin
        self.results=[]; self.records={}; self.scoring=False; self.score_trace=[]
        self.checks={}; self.failure=None; self.arm=None; self.hold=None; self.replay=None
        self.previous609=old.d.rd(Path('/workspace/haic-response609-private/TASK_CLOSED-private.json'))

    def times(self):
        return dict(CPU_s=time.process_time()-CPU+10.+self.previous609['CPU_accounted_s'],
                    wall_s=time.time()-self.task['start_epoch']+self.task['prior_preparation_wall_s']+self.previous609['whole_task_accounted_wall_s'])

    def guard(self,*a):
        t=self.times()
        if t['CPU_s']>=5310 or t['wall_s']>=6480: raise old.BudgetStop('610_CLEANUP_RESERVE')
        if datetime.datetime.now(datetime.timezone.utc)>=base.DEADLINE: raise old.BudgetStop('DEADLINE')

    def capacity(self,req):
        self.guard()
        for k,n in req.items():
            if k in CAPS and self.counts[k]+n>CAPS[k]: raise old.BudgetStop('610_'+k)

    def reserve(self,kind,n=None):
        # Mandatory next fixed arms retain one whole call each, plus full replay.
        future = [] if self.arm=='C' else (['C'] if self.arm=='B' else ['B','C'])
        model,geo = {'fixed':(4,40),'feedback':(1540,6200),'joint':(2068,8300),'replay':(0,0)}[kind]
        if n is not None: model=(n+1)*48+4; geo=(n+1)*190+80
        model += 1174 + sum(2068 if x=='C' else 1540 for x in future)
        geo += 7200 + sum(8300 if x=='C' else 6200 for x in future)
        req=dict(model_attempted=model,model_completed=model,external_force=4*model,
                 internal_force=4*model,total_force=8*model,geometry=geo)
        self.capacity(req)
        t=self.times(); need=90 if kind=='joint' else 60
        remaining=sum(90 if x=='C' else 60 for x in future)
        if t['CPU_s']+need+remaining+120+90>=5400 or t['wall_s']+need*1.5+remaining*1.5+180+120>=6600:
            raise old.BudgetStop('610_NEXT_CALL_MANDATORY_REPLAY_CLEANUP')
        self.applied_journal.append('RESERVE',arm=self.arm,hold=self.hold,kind_call=kind,
                                    pairs_remaining=n,requests=req,future_minimum_calls=future,time=t)

    def flush(self,label,hold=None,detail=None):
        name=label if hold is None else f'{label}-{hold:03d}'
        atomic_write(D/(name+'-telemetry-private.json'),dict(events=old.prior.materialize(self.journal.rows),
            wheel_results=old.prior.materialize(self.raw_kernels),detail=detail,cost=dict(self.counts),time=self.times()))
        self.journal.rows.clear(); self.raw_kernels.clear(); self.trial_summaries.clear()

    def project(self,kind,*args):
        q=super().project(kind,*args)
        if self.scoring and kind=='tracking_forecast': self.score_trace.append(q['s'])
        return q

    def certify_scored(self,a):
        self.score_trace=[]; self.scoring=True
        try: report=previous.prev.Study.certify(self,a)
        finally: self.scoring=False
        trace=self.score_trace
        if report['ok']:
            assert len(trace)==48 and report['model_ticks']==48
            assert trace[3]-self.state['progress']==report['first_hold']['progress_gain']
            return report,trace[-1],trace[3]
        return report,None,None

    def nominal_proposal(self):
        self.add('nominal_proposals')
        return core.proposal(self.state['root'],self.paths['candidate'],self.state['progress'],base.old.tracking.nominal)

    def choose_original(self,h):
        tracking=base.old.tracking; fn=tracking.nominal; captured=[]
        def capture(*a):
            value=fn(*a); captured.append(value.copy()); return value
        tracking.nominal=capture
        try: a,report=old.Study.choose(self,h)
        finally: tracking.nominal=fn
        assert len(captured)==1
        # One charged, source-identical nominal proposal comparison per call.
        direct=self.nominal_proposal()
        assert direct.tobytes()==captured[0].tobytes(), '610_NOMINAL_SPLIT_IDENTITY'
        self.checks['nominal_direct_matches_original_calls']=True
        if self.arm=='A':
            expected=self.zero_details[h]
            assert old.digest(report)==old.digest(expected['original_FINAL'])
            assert a is not None and a.tobytes().hex()==expected['action_bits']
        frames=None if a is None else previous.prev.final_frames(old.prior.materialize(self.journal.rows),old.prior.materialize(self.raw_kernels))
        return a,report,frames

    def choose_joint(self):
        nominal=self.nominal_proposal()
        modified,meta=old.Study.residual_action(self,nominal,self.coeff)
        self.model_mode='joint_forecast'
        self.joint_certify=base.old.tracking.certifier(self.state['root'],self.paths['candidate'],self.paths['backup'],
            self.state['progress'],self.model,self.planner,self.geometry_context,180000,tuple(self.state['tracking']))
        records=[]
        def record(q):
            records.append(dict(index=q['index'],row=q['row'],rows=q['rows'],u=q['u'],
                action_bits=q['action'].tobytes().hex(),report=q['report'],end_progress=q['end_progress'],first4_progress=q['first4_progress']))
        a,final,entries=core.batch(nominal,modified,self.certify_scored,
            lambda n:self.reserve('joint',n),record)
        atomic_write(D/f'C-pairs-{self.hold:03d}-private.json',dict(nominal_bits=nominal.tobytes().hex(),
            modified_bits=modified.tobytes().hex(),meta=meta,pairs=records,selected_bits=None if a is None else a.tobytes().hex()))
        frames=None if a is None else previous.prev.final_frames(old.prior.materialize(self.journal.rows),old.prior.materialize(self.raw_kernels))
        return a,final,frames

    def run_arm(self,label):
        self.arm=self.label=label; self.state=old.clone(self.start)
        old.isolated(self.state,[self.start]+[r['state'] for r in self.records.values()])
        gates=old.Crossing(self); rows=[]; commands=[]; reason=None
        before=self.counts.copy(); begin=self.times()
        atomic_write(D/f'{label}-STARTED-private.json',dict(checkpoint_sha256=self.start_hash,time=begin))
        for h in range(25,295):
            self.hold=h; self.next_hold=h
            if 50+self.state['global_raw']>=1224: reason='ORIGINAL_HORIZON_CENSORED'; break
            kind='joint' if label=='C' else 'fixed' if label=='A' and h<=39 else 'feedback'
            try: self.reserve(kind)
            except old.BudgetStop as exc: reason='COST_CENSORED:'+str(exc); break
            self.begin_context(); detail=None; hold=[]
            try:
                if kind=='fixed': a=self.fixed[h].copy(); report=None; frames=None
                elif label=='C': a,report,frames=self.choose_joint()
                else: a,report,frames=self.choose_original(h)
                if a is None:
                    reason='NO_SAFE_PAIR' if label=='C' else 'INCUMBENT_NO_ADMISSIBLE_ACTION'
                    break
                detail=dict(action_bits=a.tobytes().hex(),final=report,kind=kind)
                commands.append(dict(index=h,action=a.tolist()))
                for k in range(1,5):
                    row,why=old.Study.raw(self,a,h,k); rows.append(row); hold.append(row)
                    if label=='A': core.require_equal(row,self.zero_rows[(h-25)*4+k-1],old.digest)
                    if why: reason='APPLIED_STRICT_'+why; break
                    if frames is not None:
                        f=frames[k-1]
                        forces=[dict(wheel=i,ratio=f['verdict']['ratios'][i],clipped=bool(f['external'][i][2]['clipped']),vector=f['external'][i][1]) for i in range(4)]
                        assert old.digest(row['root_without_roads'])==old.digest(f['after']['root'])
                        assert old.digest(row['forces'])==old.digest(forces)
                        assert row['proposed_history']==f['verdict']['prefix_history'] and row['margin']==f['geometry']['footprint']
                    gates.add(row)
                    if self.state['tracker'].finish_time_s is not None: raise RuntimeError('FULL_LAP_NOT_AUTHORIZED')
                gates.finish_hold(hold)
            except (old.CandidateDomain,base.old.DomainStop) as exc:
                bodies=[e['body'] for e in self.journal.rows if e['kind']=='AFTER_MODEL_TICK']
                if bodies and not math.isfinite(bodies[-1]): raise RuntimeError('610_NONFINITE_BODY_TECHNICAL') from exc
                reason='SCIENTIFIC_BODY_DOMAIN:'+str(exc)
            except old.BudgetStop as exc: reason='COST_CENSORED:'+str(exc)
            finally:
                self.scoring=False; self.active_trial=None; self.pending=None
                self.end_context(); self.flush(label,h,detail)
                atomic_write(D/f'{label}-latest-private.json',dict(checkpoint=self.checkpoint(self.state),cost=dict(self.counts),reason=reason,time=self.times()),True)
            if reason or gates.passed('400'): break
        safe=reason is None and gates.passed('400')
        if reason is None and not safe: reason='ENDPOINT_NOT_REACHED_CENSORED'
        cp=self.checkpoint(self.state)
        if label=='A' and reason and 'CENSORED' in reason:
            self.results.append(dict(arm=label,safe_s400=False,stop=reason,applied_raw=len(rows),global_raw=self.state['global_raw'],crossings=gates.hits,cost={k:self.counts[k]-before[k] for k in self.counts},time={k:self.times()[k]-begin[k] for k in begin}))
            raise old.BudgetStop('610_A_IDENTITY_GATE_INCOMPLETE:'+reason)
        if label=='A':
            assert safe and old.digest(cp)==old.digest(self.zero['checkpoint'])
            assert old.digest(commands)==old.digest(self.zero['commands']) and old.digest(gates.hits)==old.digest(self.zero['crossings'])
            self.checks['A_all_rows_commands_full_checkpoint_planes_exact605']=True
        summary=dict(arm=label,safe_s400=safe,stop=reason or 'SAFE_s400_WHOLE_HOLD',
            applied_raw=len(rows),global_raw=self.state['global_raw'],crossings=gates.hits,
            cost={k:self.counts[k]-before[k] for k in self.counts},
            time={k:self.times()[k]-begin[k] for k in begin})
        self.records[label]=dict(rows=rows,commands=commands,checkpoint=cp,crossings=gates.hits,state=old.clone(self.state))
        atomic_write(D/f'{label}-result-private.json',dict(summary=summary,**{k:v for k,v in self.records[label].items() if k!='state'}))
        self.results.append(summary)
        assert old.digest(self.checkpoint(self.start))==self.start_hash
        return summary

    def independent_replay(self,label):
        self.arm='C'; self.hold=0; self.reserve('replay')
        record=self.records[label]; expected=self.prefix_rows+record['rows']
        self.label='replay'; self.state=self.restore_cp(self.initial_cp); gates=old.Crossing(self); rows=[]
        atomic_write(D/'REPLAY_STARTED-private.json',dict(arm=label,raw=len(expected),requests=REPLAY))
        for j in range(0,len(expected),4):
            hh=expected[j:j+4]; self.begin_context()
            try:
                for e in hh:
                    r,why=old.Study.raw(self,np.asarray(e['action'],np.float32),e['index'],e['raw'])
                    assert why is None and old.digest(r)==old.digest(e), '610_INITIAL_REPLAY_IDENTITY'
                    rows.append(r); gates.add(r)
                gates.finish_hold(rows[-4:])
            finally: self.end_context(); self.flush('replay',hh[0]['index'])
        assert old.digest(self.checkpoint(self.state))==old.digest(record['checkpoint']) and old.digest(gates.hits)==old.digest(record['crossings'])
        self.replay=dict(arm=label,exact=True,raw=len(rows),all_states_history_visited_tracker_clock_planes_exact=True)
        atomic_write(D/'independent-initial-replay-private.json',dict(summary=self.replay,rows=rows,checkpoint=self.checkpoint(self.state),crossings=gates.hits))

    def prepare(self):
        p605=Path('/workspace/haic-response605-private')
        c605=old.d.rd(G/'retry/residual605_contract.json'); r605=old.d.rd(p605/'as-executed-result-private.json')
        assert base.sha(p605/'as-executed-result-private.json')==old.d.rd(Path('/workspace/haic-response606-private/proposed-input-private.json'))['source605_sha256']
        def get(name):
            assert base.sha(p605/name)==r605['private_sha256'][name]
            return old.d.rd(p605/name)
        cp=get('raw96-checkpoint-private.json'); self.start=self.restore_cp(cp)
        assert self.start['global_raw']==96; self.state=old.clone(self.start); self.start_hash=old.digest(cp)
        self.zero=get('zero-result-private.json'); self.zero_rows=self.zero['rows']; self.planes=get('fixed-planes-private.json')
        assert len(self.zero_rows)==208 and self.zero_rows[0]['global_raw_before']==96
        assert base.sha(p605/'applied-journal-private.jsonl')==r605['private_sha256']['applied-journal-private.jsonl']
        events=[json.loads(s) for s in (p605/'applied-journal-private.jsonl').read_text().splitlines()]
        self.prefix_rows=[e['row'] for e in events if e['kind']=='APPLIED_RESULT' and e['label']=='prefix']
        assert len(self.prefix_rows)==96 and all(not q['pre_failure'] and not q['post_failure'] for q in self.prefix_rows)
        assert self.prefix_rows[-1]['checkpoint_sha256']==self.start_hash
        for k,v in [('root_without_roads','root'),('visited','visited')]:
            assert old.digest(self.prefix_rows[-1][k])==old.digest(cp[v])
        self.zero_details={}
        for h in range(40,77):
            n=f'zero-hold-{h:03d}-private.json'
            self.zero_details[h]=get(n)['detail']
        for k,p in [('static',base.old.INPUTS['static']),('paths',base.old.INPUTS['candidate_paths'])]: assert base.sha(p)==c605['input_sha256'][k]
        c597=old.d.rd(G/'retry/cold597_contract.json'); r597=old.d.rd(G/'retry/cold597_result.json')
        assert base.sha(base.old.INPUTS['tape'])==c597['input_sha256']['tape']
        self.fixed={q['index']:np.asarray(q['action'],np.float32) for q in old.d.rd(base.old.INPUTS['tape'])['commands'] if q['index']<=39}
        initial=Path('/workspace/haic-response597-private/initial-checkpoint-private.json')
        assert base.sha(initial)==r597['private_sha256'][initial.name]; self.initial_cp=old.d.rd(initial)
        from retry.early610_preflight import validate_prefix_histories
        self.checks['phase_history_prefix96']=validate_prefix_histories(self,self.prefix_rows,cp)
        self.coeff=dict(c605['family'])['H1']
        c603=old.d.rd(G/'retry/scalar603_contract.json'); r603=old.d.rd(G/'retry/scalar603_result.json')
        for p,h in c603['compiler_runtime_sha256'].items(): assert base.sha(Path(p))==h
        binary=Path(c603['command'][-1]); assert base.sha(binary)==r603['binary_sha256']
        spec=importlib.util.spec_from_file_location('_scalar603',binary); ext=importlib.util.module_from_spec(spec); spec.loader.exec_module(ext)
        env=ext.environment(); assert env.pop('original_math_hypot') is math.hypot and env['rounding_mode']==env['FE_TONEAREST']
        tracking=base.old.tracking
        import retry.lap518_control as lap
        assert tracking.nominal is lap.nominal
        from retry.early610_preflight import run_preflight
        tests=run_preflight(self)
        atomic_write(G/'retry/early610_tests.json',tests)
        assert subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
        assert not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
        import retry.plan512_control as kernel
        assert kernel.MAX_MODEL_TICKS==200000
        def forbidden(*a,**kw): raise RuntimeError('610_NATIVE_FORBIDDEN')
        base.old.CarRacing.__init__=base.old.CarRacing.reset=base.old.CarRacing.step=forbidden
        base.old.Car.__init__=base.old.Car.step=forbidden
        files=['retry/early610.py','retry/early610_preflight.py','retry/early609_core.py','retry/corner608.py','retry/corner608_core.py','retry/residual605.py','retry/residual604_math.py','retry/structure537_control.py','retry/lap518_control.py','retry/profile601.py','retry/cold598_support.py']
        contract=dict(study=610,status='PURE_TESTS_PASSED_FROZEN_BEFORE_SOURCE',task=self.task,deadline=base.DEADLINE.isoformat(),caps=CAPS,
            time_caps=dict(CPU_s=5400,wall_s=6600,cleanup_CPU_s=90,cleanup_wall_s=120),kernel=200000,
            source_sha256={p:base.sha(G/p) for p in files},tests_sha256=base.sha(G/'retry/early610_tests.json'),
            input_sha256=dict(checkpoint96=base.sha(p605/'raw96-checkpoint-private.json'),source605=base.sha(p605/'as-executed-result-private.json'),zero=base.sha(p605/'zero-result-private.json'),prefix_journal=base.sha(p605/'applied-journal-private.jsonl'),initial=base.sha(initial),planes=base.sha(p605/'fixed-planes-private.json'),binary603=base.sha(binary),runtime603=base.sha(G/'retry/scalar603_contract.json')),
            checkpoint96_full_digest=self.start_hash,prefix96_provenance_not_newly_run=True,
            arms=dict(A='Fixed577holds25..39 then original537from40. ALLraw/fullcp/commands/reports/planes exact605zero before B or C.',B='Original537everyholdfrom25,unchangedrules.',C='Original537nominal function directly ONCE(currentroot,high,progress); NO originalchoose or admissible-base precondition. H1 modification unchanged604sixcoeff/formula/windows. Bothnominal/H1shiftedsteers paired BEFORE certification.'),
            coefficients=self.coeff,grid='EXACT608make_pairs:17dyadic[-1,1]+2brakelockfloat32+.CURRENTnominalandH1modifiednetpedal;float32canonicalzero,dedup,21pedalsmax42pairs;ascendingsteerthenpedaldescending. Ifsteersbyteidentical,physicalpairsdedupandbothrowmemberships. NominalH1clampsoriginal. ZeroresidualpreservesnominalbytesBUTcontinuesSAMEtimegridselection;no chooserfallback.',
            selection='ALLfixedpairscertified original12hold/48raw. Safehighestend48progress,thenhighestfirst4progress,thenlowestfixedindex. Progress from alreadychargedtracking_forecastprojectionreturns;no newquery. FreshFINAL once selected;scoreexactandactualfirst4root/force/history/marginexact. No-safe=>scientificarmstop. No nearestpedal/fallback/rowsteeringtuning.',
            nominal_parity='Original537 AST firstassignment calls SAME nominal function. Actual nominal_proposal/choose_joint/certify_scored/project/reserve/compare/error-handler exercised with evaluation dependencies stubbed, NO chooser or physical kernel in purepreflight. EveryA/B originalchoose interceptsnominal returnandcomparesbyteexact toseparatechargedproposal onsamefullcurrentstate;A actions/fullreports alsoexact605storedcalls. No newsteeringrule.',
            gate='Samefixed605worldplanes/originalclock. s200/s300diagnosticonly,noprune. Endpointfirsteligibles400crossandwholeholdsafe. Strict537gates unchanged1.059force/.10clip/.50footprint/4.85reference/path3/body100/projectionbounds. Next11holds originalbackupwitness,NOTfutureCpolicyproof.',
            replay='AfterALLfixedarms,earlieststrictsafeB/C withtime<A (tieBfirst):ONEcommandreplayfromsaved597initial usingstoredprefix96+winnercommands. Compareallfullrows/cp/history/visited/tracker/clock/planes. No gain=>no replay. No full-lap/native.',
            cost_derivation=dict(A_full_known_endpoint_worst=dict(holds=52,fixed_holds=15,feedback_holds=37,model=57040,geometry=230000),B_per_hold=dict(model=1540,geometry=6200),C_per_hold=dict(model=2068,geometry=8300),replay=REPLAY,
                formula='C43cert*48+4=2068;43*(49margin+48postproject+44backupnominal+49originalhelpercompare)+80=8250, use conservative8300geometry in reservation;originalnominal2+H1residual2+actualplanes included80. A/B1540model6200geometry PLUSnominalparity2geometry accounted in6200 envelope. Allreportedcounts global, originalhelperEVERYnewmiss charged.',
                entire_three_arms_not_guaranteed=True,B_worst_270holds_model=415800,C_worst_270holds_model=558360,
                reservation='Eachhold worstnextcall PLUS onefullcallforeachremainingmandatoryarm PLUSentire1174rawreplay/7200geometry PLUSCPU/wallcleanup. Pairremainingreserves worstallremaining+FINAL+actual+mandatory+replay. Currentarmcensoredwhenreservationfails;not scientificfailure. No reduction/capraise.'),
            errors='Aidentity/scientificfailure=>ALLstop;B/Cscientific=>nextfixedarm;budget=>armcensored;technical/IO/identity/nonfinite=>ALLstopNOretry.',
            preserve609=dict(code=base.sha(G/'retry/early609.py'),closeout=base.sha(G/'retry/early609_closeout.json'),failure_cost=self.previous609,recovery_scope='Fix phase history guard and implement actual-object preflight; extract unchanged arm dispatcher and technical error handler for testing. Policies/selection/limits unchanged. 609 CPU/wall INCLUDEDat610caps.'),
            preserve608=base.sha(G/'retry/corner608_closeout.json'),native_world_reset_seed_carry_HOLDOUT_SEALED=0,research_remaining=22211,reserve=84000,reserve_used=0)
        atomic_write(G/'retry/early610_contract.json',contract)
        atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=base.sha(G/'retry/early610_contract.json'),time=self.times()))
        self.install_meters(); old.compiled_geometry.distance=ext.distance

    def compare(self):
        for label in ['A','B','C']: self.run_arm(label)
        baseline=self.results[0]['crossings']['400']['time_s']
        best=[r for r in self.results[1:] if r['safe_s400'] and r['crossings']['400']['time_s']<baseline]
        if best:
            winner=min(best,key=lambda r:(r['crossings']['400']['time_s'],r['arm']))
            self.independent_replay(winner['arm']); status='FASTER_SOURCE_s400_REPLAY_EXACT'
        else: status='NO_FASTER_SAFE_ARM'
        return status

    def technical_stop(self,exc):
        error=type(exc).__name__+':'+str(exc)
        atomic_write(D/'error-private.json',dict(error=error,traceback=traceback.format_exc(),time=self.times()))
        return 'TECHNICAL_STOP_NO_RETRY',error

    def run(self):
        status='PREPARATION'; error=None
        def timer(*a): raise old.BudgetStop('610_TIMER')
        signal.signal(signal.SIGPROF,timer); signal.signal(signal.SIGALRM,timer)
        signal.setitimer(signal.ITIMER_PROF,max(.01,5310-self.times()['CPU_s']))
        signal.setitimer(signal.ITIMER_REAL,max(.01,6480-self.times()['wall_s']))
        try:
            self.prepare()
            status=self.compare()
        except old.BudgetStop as exc: status='COST_CENSORED'; error=str(exc)
        except BaseException as exc:
            status,error=self.technical_stop(exc)
        finally:
            self.end_context(); self.restore(); old.compiled_geometry.distance=self.original_distance
            if self.journal.rows: self.flush('partial')
            self.applied_journal.append('STUDY_END',status=status,error=error,cost=dict(self.counts),time=self.times()); self.applied_journal.close()
            raw=dict(study=610,status=status,error=error,arms=self.results,checks=self.checks,replay=self.replay,cost=dict(self.counts),time=self.times(),model_counter=self.model[0],kernel_hardcap=200000,
                native=0,worlds=0,resets=0,new_seed=0,carry=0,HOLDOUT=0,SEALED=0,research_remaining=22211,reserve=84000,reserve_used=0,whole_lap_claim=False,native_admission=False,
                private_sha256={p.name:base.sha(p) for p in D.glob('*.json*')})
            atomic_write(D/'as-executed-result-private.json',raw)
            public=json.loads(json.dumps(raw)); allowed={'before_raw','after_raw','fraction','time_s','hold','eligible','whole_hold_safe'}
            for r in public['arms']: r['crossings']={k:{a:b for a,b in v.items() if a in allowed} for k,v in r['crossings'].items()}
            public['as_executed_private_sha256']=base.sha(D/'as-executed-result-private.json')
            atomic_write(G/'retry/early610_result.json',public)
            atomic_write(D/'CLOSED-private.json',dict(result_sha256=base.sha(G/'retry/early610_result.json'),raw_sha256=base.sha(D/'as-executed-result-private.json'),time=self.times()))
            signal.setitimer(signal.ITIMER_PROF,0); signal.setitimer(signal.ITIMER_REAL,0)
            print(json.dumps(dict(status=status,error=error,cost=dict(self.counts),time=self.times())))


if __name__=='__main__': Study().run()
