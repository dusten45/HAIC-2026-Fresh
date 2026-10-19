"""One source candidate from the preserved H1raw160 checkpoint to fixed s400."""
import time
CPU=time.process_time()
import datetime,importlib.util,json,math,os,signal,subprocess,traceback
from collections import Counter
from pathlib import Path
import numpy as np
import retry.pairs607 as prev
import retry.corner608_core as core
from retry.clip561_core import atomic_write
old=prev.old;base=prev.base;G=prev.G;D=Path('/workspace/haic-response608-private')
CAPS=dict(model_attempted=100000,model_completed=100000,external_force=400000,internal_force=400000,total_force=800000,geometry=300000)
REPLAY=dict(model_attempted=1174,model_completed=1174,external_force=4696,internal_force=4696,total_force=9392,geometry=7200)

class Study(prev.Study):
    def __init__(self):
        self.task=old.d.rd(D/'TASK_STARTED-private.json')
        if (D/'PROCESS_STARTED-private.json').exists():raise RuntimeError('608_NO_RETRY')
        atomic_write(D/'PROCESS_STARTED-private.json',dict(pid=os.getpid(),utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
        static=old.d.rd(base.old.INPUTS['static']);old.prior.Meter.__init__(self,static,{})
        self.index=self.source_index;self.edge=self.source_edges;self.paths=old.d.rd(base.old.INPUTS['candidate_paths'])
        self.geometry_context=base.old.tracking.geometry_context(self.static,300000)
        self.applied_journal=old.Journal(D/'applied-journal-private.jsonl')
        self.context=None;self.state=None;self.label='preparation';self.saved=[]
        self.orig_geometry_margin=old.compiled_geometry.full.road_margin;self.original_distance=old.compiled_geometry.distance
        self.original_plain_road=old.compiled_geometry.original.margin
        self.result=dict(study=608,status='PREPARATION',original_choose_calls=0,joint_batches=0,zero_residual_decisions=0,
                         shifted_selections=0,base_fallbacks=0,fresh_pair_FINAL=0,first607_exact=False,replay=None)
        self.rows=[];self.commands=[];self.decisions=[];self.failure=None
    def times(self):return dict(CPU_s=time.process_time()-CPU+10.,wall_s=time.time()-self.task['start_epoch'])
    def guard(self,*a):
        t=self.times()
        if t['CPU_s']>=2940 or t['wall_s']>=4380 or t['wall_s']<0:raise old.BudgetStop('608_CLEANUP_RESERVE')
        if datetime.datetime.now(datetime.timezone.utc)>=base.DEADLINE:raise old.BudgetStop('DEADLINE')
    def capacity(self,req):
        self.guard()
        for k,n in req.items():
            if k in CAPS and self.counts[k]+n>CAPS[k]:raise old.BudgetStop('608_'+k)
    def initial(self):raise RuntimeError('608_INITIAL_NOT_AUTHORIZED_EXCEPT_CONDITIONAL_SAVED_REPLAY')
    def prefix96(self):raise RuntimeError('608_PREFIX_RUN_FORBIDDEN')
    def restore_cp(self,cp):
        root=old.d.load_root(dict(cp['root'],roads=self.static['root']['roads']));old.immutable(root)
        state=dict(root=root,progress=cp['progress'],tracker=old.d.FinishLineTracker(**cp['tracker']),visited=set(cp['visited']),
                   launch=list(cp['launch']),tracking=list(cp['tracking']),elapsed=cp['elapsed'],global_raw=cp['global_raw'])
        assert old.digest(self.checkpoint(state))==old.digest(cp)
        return state
    def reserve_decision(self,joint):
        raw=3892 if joint else 1540;geo=15600 if joint else 6200
        req=dict(model_attempted=raw+1174,model_completed=raw+1174,external_force=4*(raw+1174),
                 internal_force=4*(raw+1174),total_force=8*(raw+1174),geometry=geo+7200)
        self.capacity(req);t=self.times()
        if t['CPU_s']+60+120+60>=3000 or t['wall_s']+90+180+120>=4500:raise old.BudgetStop('608_NEXT_DECISION_REPLAY_TIME')
        self.applied_journal.append('DECISION_RESERVE',hold=self.hold,requests=req,CPU_s=60,wall_s=90,replay_CPU_s=120,replay_wall_s=180,time=t)
    def reserve_remaining(self,n):
        raw=(n+1)*48+4+1174;geo=(n+1)*190+64+7200
        self.capacity(dict(model_attempted=raw,model_completed=raw,external_force=4*raw,internal_force=4*raw,total_force=8*raw,geometry=geo))
        self.applied_journal.append('PAIR_REMAINDER_RESERVE',hold=self.hold,pairs_remaining=n,model=raw,geometry=geo)
    def flush(self,label,hold=None,detail=None):
        name=label if hold is None else f'{label}-{hold:03d}'
        atomic_write(D/(name+'-telemetry-private.json'),dict(events=old.prior.materialize(self.journal.rows),
            wheel_results=old.prior.materialize(self.raw_kernels),detail=detail,cost=dict(self.counts),time=self.times()))
        self.journal.rows.clear();self.raw_kernels.clear();self.trial_summaries.clear()
    def original(self):
        self.result['original_choose_calls']+=1;before=self.counts.copy()
        a,report=old.Study.choose(self,self.hold)
        if a is None:return None,report,None
        if self.hold==41:
            assert a.tobytes()==self.base_action.tobytes() and old.digest(report)==old.digest(self.packet['stored_hold41_detail']['original_FINAL'])
            work={k:self.counts[k]-before[k] for k in self.expected_work};assert work==self.expected_work
            ev=[e for e in old.prior.materialize(self.journal.rows) if e.get('mode')=='incumbent_forecast']
            assert old.digest(prev.strip_label(ev))==old.digest(prev.strip_label(self.expected_events))
            assert old.digest(old.prior.materialize(self.raw_kernels))==old.digest(self.expected_wheels)
            self.result['first_original607_exact']=True
        frames=prev.final_frames(old.prior.materialize(self.journal.rows),old.prior.materialize(self.raw_kernels))
        return a,report,frames
    def modify(self,a):return old.Study.residual_action(self,a,self.coeff)
    def joint(self,a,modified,meta):
        pairs,grid=core.make_pairs(a,modified)
        if self.hold==41:
            assert core.signature(pairs)==self.expected_signature,'607_FIRST_GRID_DEFINITION_CHANGED'
        self.end_context();self.flush('original',self.hold)
        self.begin_context();self.result['joint_batches']+=1
        self.joint_certify=base.old.tracking.certifier(self.state['root'],self.paths['candidate'],self.paths['backup'],self.state['progress'],
            self.model,self.planner,self.geometry_context,180000,tuple(self.state['tracking']))
        records=[]
        def record(q):
            records.append(dict(index=q['index'],row=q['row'],rows=q['rows'],u=q['u'],action_bits=q['action'].tobytes().hex(),report=q['report']))
        selected,final,entries,branch=core.batch(a,modified,self.certify,self.reserve_remaining,record)
        atomic_write(D/f'pairs-{self.hold:03d}-private.json',records)
        if self.hold==41:
            assert len(records)==len(self.expected_pairs)
            assert all(old.digest(q['report'])==old.digest(e['report']) for q,e in zip(records,self.expected_pairs))
            assert selected.tobytes().hex()==self.expected_pairs[self.result607['selected']['index']]['action_bits']
        self.result['fresh_pair_FINAL']+=1
        self.result['shifted_selections' if branch=='shifted' else 'base_fallbacks']+=1
        frames=prev.final_frames(old.prior.materialize(self.journal.rows),old.prior.materialize(self.raw_kernels))
        return selected,final,frames,entries,branch
    def run_candidate(self):
        self.label='candidate';self.state=old.clone(self.start);old.isolated(self.state,[self.start]);self.gates=old.Crossing(self)
        self.hold=41;self.reserve_decision(True)
        # Check the dynamic formula/grid with the STORED base command before
        # the first new chooser/tick. Two new map queries are charged.
        modified,meta=self.modify(self.base_action)
        assert modified.tobytes()==self.modified.tobytes(),'608_FIRST_RESIDUAL_FORMULA_DIFFERS607'
        assert core.signature(core.make_pairs(self.base_action,modified)[0])==self.expected_signature
        self.result['first_grid_preflight_model0']=self.counts['model_attempted']==0
        for h in range(41,295):
            self.hold=h
            if 50+self.state['global_raw']>=1224:raise old.BudgetStop('ORIGINAL_TIME_LIMIT_WITHOUT_ENDPOINT')
            self.reserve_decision(80.<self.state['progress']<220.);self.begin_context();detail=None;hold=[]
            try:
                a,final,frames,entries,branch=core.dispatch(self.original,self.modify,self.joint)
                if branch=='zero_residual_original_FINAL':self.result['zero_residual_decisions']+=1
                assert final.get('ok',True) and a.dtype==np.float32
                self.commands.append(dict(index=h,action=a.tolist()))
                detail=dict(hold=h,branch=branch,grid_pairs=len(entries),shifted_feasible=sum('shifted' in q['rows'] and q['report']['ok'] for q in entries),
                            physical_checkpoint_before=old.digest(self.checkpoint(self.state)),action_bits=a.tobytes().hex(),final=final)
                for k in range(1,5):
                    row,why=old.Study.raw(self,a,h,k);self.rows.append(row);hold.append(row)
                    if why:self.failure=dict(hold=h,raw=k,reason=why,global_raw_before=row['global_raw_before']);return 'APPLIED_STRICT_FAILURE'
                    frame=frames[k-1]
                    f=[dict(wheel=i,ratio=frame['verdict']['ratios'][i],clipped=bool(frame['external'][i][2]['clipped']),vector=frame['external'][i][1]) for i in range(4)]
                    assert old.digest(row['root_without_roads'])==old.digest(frame['after']['root']) and old.digest(row['forces'])==old.digest(f)
                    assert row['proposed_history']==frame['verdict']['prefix_history'] and row['margin']==frame['geometry']['footprint']
                    self.gates.add(row)
                    if self.state['tracker'].finish_time_s is not None:raise RuntimeError('UNEXPECTED_FULL_LAP_BEFORE_s400')
                self.gates.finish_hold(hold)
                if h==41:
                    assert old.digest(hold)==old.digest(self.expected_first_rows['rows'])
                    assert old.digest(self.checkpoint(self.state))==old.digest(self.expected_first_rows['checkpoint'])
                    self.result['first607_exact']=True
                self.decisions.append(dict(hold=h,branch=branch,pairs=len(entries),global_raw=self.state['global_raw']))
            finally:
                self.active_trial=None;self.pending=None;self.end_context();self.flush('decision',h,detail)
                atomic_write(D/'candidate-latest-private.json',dict(checkpoint=self.checkpoint(self.state),cost=dict(self.counts),time=self.times()),True)
            if self.gates.passed('400'):return 'SAFE_s400_WHOLE_HOLD'
        raise old.BudgetStop('ENDPOINT_NOT_REACHED_AT_ORIGINAL_LIMIT')
    def replay_initial(self):
        self.capacity(REPLAY);t=self.times()
        if t['CPU_s']+120+60>=3000 or t['wall_s']+180+120>=4500:raise old.BudgetStop('REPLAY_AND_CLEANUP_TIME')
        self.label='replay';self.state=self.restore_cp(self.initial_cp);g=old.Crossing(self);expected=self.prefix_rows+self.rows
        atomic_write(D/'REPLAY_STARTED-private.json',dict(expected_raw=len(expected),initial_checkpoint_sha256=old.digest(self.initial_cp),requests=REPLAY))
        replay=[]
        for j in range(0,len(expected),4):
            hh=expected[j:j+4];h=hh[0]['index'];self.begin_context()
            try:
                for e in hh:
                    r,why=old.Study.raw(self,np.asarray(e['action'],np.float32),h,e['raw']);assert why is None
                    assert old.digest(r)==old.digest(e),'INITIAL_TAPE_REPLAY_ROW_MISMATCH';replay.append(r);g.add(r)
                g.finish_hold(replay[-len(hh):])
            finally:self.end_context();self.flush('replay',h)
        assert old.digest(g.hits)==old.digest(self.gates.hits) and old.digest(self.checkpoint(self.state))==old.digest(self.candidate_cp)
        self.result['replay']=dict(exact=True,raw=len(replay),all_states_history_visited_tracker_clock_planes_exact=True)
        atomic_write(D/'independent-initial-replay-private.json',dict(rows=replay,checkpoint=self.checkpoint(self.state),crossings=g.hits))
    def prepare(self):
        c603=old.d.rd(G/'retry/scalar603_contract.json');r603=old.d.rd(G/'retry/scalar603_result.json')
        for p,h in c603['compiler_runtime_sha256'].items():assert base.sha(Path(p))==h
        self.packet=old.d.rd(Path('/workspace/haic-response606-private/proposed-input-private.json'));analysis=old.d.rd(G/'retry/forensic606_analysis.json')
        assert base.sha(Path('/workspace/haic-response606-private/proposed-input-private.json'))==analysis['proposed_private_input_sha256']
        self.start=self.restore_cp(self.packet['checkpoint']);assert self.start['global_raw']==160
        self.start_hash=old.digest(self.checkpoint(self.start));self.state=old.clone(self.start)
        r605=old.d.rd(Path('/workspace/haic-response605-private/as-executed-result-private.json'));c605=old.d.rd(G/'retry/residual605_contract.json')
        assert base.sha(Path('/workspace/haic-response605-private/as-executed-result-private.json'))==self.packet['source605_sha256']
        for k,p in [('static',base.old.INPUTS['static']),('paths',base.old.INPUTS['candidate_paths'])]:assert base.sha(p)==c605['input_sha256'][k]
        p605=Path('/workspace/haic-response605-private')
        def get(name):assert base.sha(p605/name)==r605['private_sha256'][name];return old.d.rd(p605/name)
        h1=get('H1-result-private.json');assert old.digest(h1['checkpoint'])==self.start_hash
        self.coeff=dict(c605['family'])['H1'];self.planes=get('fixed-planes-private.json')
        self.baseline_s400=r605['candidates'][0]['crossings']['400']['time_s'];assert self.baseline_s400==6.054387012453384
        self.prefix_rows=[]
        for line in (p605/'applied-journal-private.jsonl').read_text().splitlines():
            q=json.loads(line)
            if q['kind']=='APPLIED_RESULT' and q['label']=='prefix':self.prefix_rows.append(q['row'])
        assert base.sha(p605/'applied-journal-private.jsonl')==r605['private_sha256']['applied-journal-private.jsonl']
        self.prefix_rows += [q for q in h1['rows'] if q.get('global_raw_after',9999)<=160]
        assert len(self.prefix_rows)==160 and all(not r['pre_failure'] and not r['post_failure'] for r in self.prefix_rows)
        assert old.digest(self.prefix_rows[-1]['root_without_roads'])==old.digest(self.packet['checkpoint']['root'])
        r597=old.d.rd(G/'retry/cold597_result.json');initial=Path('/workspace/haic-response597-private/initial-checkpoint-private.json')
        assert base.sha(initial)==r597['private_sha256'][initial.name];self.initial_cp=old.d.rd(initial)
        self.result607=old.d.rd(G/'retry/pairs607_result.json');p607=Path('/workspace/haic-response607-private')
        def get607(name):assert base.sha(p607/name)==self.result607['private_sha256'][name];return old.d.rd(p607/name)
        self.expected_pairs=get607('all-pairs-private.json');self.expected_signature=[(q['row'],q['u'],q['action_bits']) for q in self.expected_pairs]
        self.expected_first_rows=get607('shifted-apply-rows-private.json')
        zz=get607('zero-telemetry-private.json');self.expected_events=[q for q in zz['events'] if q.get('mode')=='incumbent_forecast']
        self.expected_wheels=zz['wheel_results'][:-32];self.expected_work=self.result607['zero_work_delta']
        self.base_action=np.frombuffer(bytes.fromhex(self.packet['stored_hold41_detail']['incumbent_bits']),np.float32).copy()
        self.modified=np.frombuffer(bytes.fromhex(self.packet['stored_hold41_detail']['action_bits']),np.float32).copy()
        assert core.signature(core.make_pairs(self.base_action,self.modified)[0])==self.expected_signature
        binary=Path(c603['command'][-1]);assert base.sha(binary)==r603['binary_sha256']
        spec=importlib.util.spec_from_file_location('_scalar603',binary);ext=importlib.util.module_from_spec(spec);spec.loader.exec_module(ext)
        env=ext.environment();assert env.pop('original_math_hypot') is math.hypot and env['rounding_mode']==env['FE_TONEAREST']
        def forbidden(*a,**kw):raise RuntimeError('608_NATIVE_FORBIDDEN')
        base.old.CarRacing.__init__=base.old.CarRacing.reset=base.old.CarRacing.step=forbidden;base.old.Car.__init__=base.old.Car.step=forbidden
        import retry.plan512_control as kernel
        assert kernel.MAX_MODEL_TICKS==200000
        assert subprocess.check_output(['git','rev-parse','main'],cwd=G,text=True).strip()=='dfb7a2de2178825ca5c5ce20bab01ba67052ba31'
        assert not subprocess.check_output(['git','diff','--name-only','main','--','Participants'],cwd=G,text=True).strip()
        contract=dict(study=608,status='FROZEN_BEFORE_TESTS_AND_SOURCE',task_start=self.task,caps=CAPS,replay_reserve=REPLAY,
            time_caps=dict(CPU_s=3000,wall_s=4500,cleanup_CPU_s=60,cleanup_wall_s=120),
            source_sha256={p:base.sha(G/p) for p in ['retry/corner608.py','retry/corner608_core.py','retry/residual604_math.py','retry/residual605.py','retry/pairs607.py','retry/structure537_control.py']},
            runtime603_manifest_sha256=base.sha(G/'retry/scalar603_contract.json'),binary_sha256=base.sha(binary),
            input_packet_sha256=analysis['proposed_private_input_sha256'],checkpoint_sha256=self.start_hash,
            source605_result_sha256=base.sha(p605/'as-executed-result-private.json'),source607_result_sha256=base.sha(G/'retry/pairs607_result.json'),
            preserved_initial_checkpoint_sha256=base.sha(initial),prefix160_provenance_only_before_conditional_replay=True,
            H1_coefficients=self.coeff,spatial_windows_and_PP_formula='EXACT residual604_math.py;currentstate/progress;no tuning',
            grid='AtEACHdecision: currentoriginal537base and H1modifiedsteers;17dyadicpedals+twooriginal537brakelocklevels+CURRENTbase/modnetpedal,float32canonicalzero,dedup.21max. Rowsascendingsteer,thenpedaldescending. Ifsteerscoincide,physicallyidenticalpaircertifiedonceandbothrowmembershipsretained;no addedcandidate. FirstsignatureMUSTequal607beforeanynewchoose/tick.',
            selection='Allfixedpairscheckedbeforeselection. Shiftedfeasibleclosesttomodifiedpedal,tiehigherpedal,thenindex. Originalbaseactionmustbenewlybase-rowcertifiedsafe. Ifnoshiftedfeasible,ONLYthatnewlycertifiedbaseactionfallback. FreshFINALexactselectedpaironce;no originalFINALreuseformodifiedpair. OriginalNOaction/baseunsafe=>stop.',
            zero='SkipjointONLYrequestedoffset==0ANDpedalresidual==0;modifiedbytesmustexactoriginalbytes. Original537freshFINALvalidforsameunmodifiedaction. Everyactualfirst4rawmustmatchselectedfreshFINAL.',
            horizon='Selectedcurrentaction+11originalbackupholdsisadmissionwitness,NOTfuturejoint/residualpolicyguarantee.',
            endpoint='Readsame605fixedold551s200/300/400worldplanes;firsteligibleforwardCOMchordcross+wholeholdsafe.200/300diagnosticonly,noprogressprune. Baseline400time6.054387012453384onoriginalclock. Stopfirstsafe400hold;no wholelap/native.',
            replay='ONLYs400strictsafeANDcontinuousgain>0:ONEindependentcommandreplayfromPRESERVED597initialcheckpoint,usingstored605prefix1..96+H1safe97..160+thissuffix. Compareallfullrows/root/history/visited/tracker/clock/checkpoint/planes. No selector inreplay. Otherwiseno replay.',
            reservations='RollingworstNEXTjoint3892models/15600geometry orzero1540/6200,PLUSentire1174model/7200geometryreplayandcleanup. Maxgrid48+freshFINAL1,original32cert,48raw/cert. Worstgeometrycoversalllogicalqueries+everyoriginalPythonhelpercomparison+planes/residualpacks. Atleast18consecutiveworstjointdecisions(h41..58)fitbutwhole400notguaranteed. Ifnextreservefails,endcurrentcandidateasCOST_CENSORED,no extrapolation/capraise.',
            helper='Pinned603segmentkernel with exact originalPython fullmargin comparison at EVERYnew601memo miss. Allnewcomparisons/project/target/worldplanepacks charged. Freshcontextperoriginal/gridphase, sourcegatesunchanged1.059/.10/.50/path3/reference4.85/body100/projectionoriginal.',
            errors='Firsttechnical/IO/integrity/domain error stopsALL,no retry. Firstactualstrictviolation stopscandidate;no otherpolicy. Budget/time=>uncompletedendpoint/replaycensored. No native/world/reset/seed/carry/HOLDOUT/SEALED.',
            research_remaining=22211,reserve=84000,reserve_used=0)
        atomic_write(G/'retry/corner608_contract.json',contract)
        atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=base.sha(G/'retry/corner608_contract.json'),time=self.times()))
        def restore_stub():assert old.digest(self.checkpoint(self.restore_cp(self.packet['checkpoint'])))==self.start_hash
        def clones():
            a=old.clone(self.start);b=old.clone(self.start);old.isolated(a,[b,self.start]);a['tracking'][0]+=1
            assert b['tracking']==self.start['tracking']
        def reserve_stub():
            f=Study.__new__(Study);f.guard=lambda:None;f.counts=Counter();f.hold=41;f.times=lambda:dict(CPU_s=0,wall_s=0)
            f.applied_journal=type('J',(),{'append':lambda *a,**k:None})();f.reserve_decision(True)
            f.counts['geometry']=CAPS['geometry']
            try:f.reserve_decision(True)
            except old.BudgetStop:pass
            else:raise AssertionError('RESERVATION_MISSING')
        tests=core.pure_checks(restore_stub,clones,reserve_stub);atomic_write(G/'retry/corner608_tests.json',tests)
        self.install_meters();old.compiled_geometry.distance=ext.distance
    def run(self):
        error=None;status='PREPARATION'
        def timer(*a):raise old.BudgetStop('608_TIMER')
        signal.signal(signal.SIGPROF,timer);signal.signal(signal.SIGALRM,timer)
        signal.setitimer(signal.ITIMER_PROF,max(.01,2940-self.times()['CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,4380-self.times()['wall_s']))
        try:
            self.prepare();status=self.run_candidate();self.candidate_cp=self.checkpoint(self.state)
            if status=='SAFE_s400_WHOLE_HOLD':
                gain=self.baseline_s400-self.gates.hits['400']['time_s'];self.result['s400_gain_s']=gain
                if gain>0:self.replay_initial();status='SAFE_EARLIER_s400_INITIAL_TAPE_REPLAY_EXACT'
        except core.PolicyStop as exc:status='INCUMBENT_OR_BASE_POLICY_STOP';self.failure=dict(reason=str(exc),hold=self.hold)
        except old.BudgetStop as exc:status='COST_CENSORED';error=type(exc).__name__+':'+str(exc)
        except BaseException as exc:
            status='TECHNICAL_STOP_NO_RETRY';error=type(exc).__name__+':'+str(exc)
            atomic_write(D/'error-private.json',dict(error=error,traceback=traceback.format_exc(),time=self.times()))
        finally:
            self.end_context();self.restore();old.compiled_geometry.distance=self.original_distance;old.compiled_geometry.full.road_margin=self.orig_geometry_margin
            if self.journal.rows:self.flush('partial')
            checkpoint=self.checkpoint(self.state) if self.state else None
            atomic_write(D/'candidate-private.json',dict(rows=self.rows,commands=self.commands,checkpoint=getattr(self,'candidate_cp',checkpoint),decisions=self.decisions,crossings=self.gates.hits if hasattr(self,'gates') else {}))
            self.applied_journal.append('STUDY_END',status=status,error=error,cost=dict(self.counts),time=self.times());self.applied_journal.close()
            self.result.update(status=status,error=error,failure=self.failure,cost=dict(self.counts),time=self.times(),decisions=self.decisions,
                applied_candidate_raw=len(self.rows),global_raw=checkpoint['global_raw'] if checkpoint else None,
                crossings=self.gates.hits if hasattr(self,'gates') else {},model_counter=self.model[0],kernel_hardcap=200000,
                native=0,worlds=0,resets=0,actions=0,new_seed=0,carry=0,HOLDOUT=0,SEALED=0,FD=0,solver=0,
                native_incumbent_s=13.22,whole_lap_claim=False,native_admission=False,research_remaining=22211,reserve=84000,reserve_used=0,
                private_sha256={p.name:base.sha(p) for p in D.glob('*.json*')})
            atomic_write(G/'retry/corner608_result.json',self.result);atomic_write(D/'CLOSED-private.json',dict(time=self.times(),result_sha256=base.sha(G/'retry/corner608_result.json')))
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(self.result,indent=2))
if __name__=='__main__':Study().run()
