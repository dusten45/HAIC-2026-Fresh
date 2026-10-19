"""Single unchanged537 return path, with every forecast and FINAL accounted."""
import time
START_CPU=time.process_time();START_WALL=time.perf_counter()
import sys,math,json,datetime,signal,traceback,copy
from pathlib import Path
from collections import Counter
import numpy as np
from retry.clip561_core import atomic_write,plain
from retry.durable568 import Journal,digest,inspect
import retry.beam579_model as b
from retry.beam579_math import immutable
from retry.return583_math import plane_observation,bracket_comparison,cache_accounting

d=b.d;policy=b.base.policy;G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response583-private');CONTRACT=G/'retry/return583_contract.json'
INPUTS={**b.INPUTS,'verified581':Path('/workspace/haic-response581-private/verified-tape-private.json'),'planes579':G/'retry/beam579_contract.json','blocked582':G/'retry/return582_contract.json'}
CAPS=dict(attempted_raw=65000,completed_model_ticks=65000,external_force=260000,internal_force=260000,total_force=520000,geometry_checks=66000,CPU_s=1800,wall_s=2400)
STAGES={'preparation':dict(CPU_s=15,wall_s=25),'prefix':dict(attempted_raw=132,CPU_s=8,wall_s=12),'continuation':dict(CPU_s=1700,wall_s=2250),'verification':dict(attempted_raw=292,CPU_s=12,wall_s=18),'audit':dict(CPU_s=15,wall_s=25)}


def register():
    tests=d.rd(G/'retry/return583_tests.json');assert tests['passed']
    c=dict(study=583,status='FROZEN_BEFORE_SOURCE',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',parent_commit='5fdf453c4a5a703168c93776e7229fc6a067ab5a',question='Can the actual581escape state return through unchanged551/537feedback to fixeds300? s200observationonly;no100/80msgain gate.',scope='Freshinitial132raw581exactprefix,onefeedbackpathfromhold34upto40fullholds/160actualraw. Stopafterfirsts300crossingwholeholdsafe,firstactualsafetyfailure,no-safe-action,depthorcost/technicalstop. Onlys300safe->oneinitialexactcommandreplay<=292raw. No factualsuffix/pose transplant,otherlaw,parent,whole/native.',caps=CAPS,stage_caps=STAGES,actual_limits={'prefix_raw':132,'continuation_holds':40,'continuation_raw':160,'independent_replays':1,'replay_raw':292},static_worst_work={'attempted_raw':62024,'geometry_checks':63304,'external_force':248096,'internal_force':248096},selector='Originalstructure537_control.choose/certifierandpreview527.backupunchanged. HORIZON12,freshFINAL,31samplecache+FINAL<=32certifications. max_ticksargument65000isbudget-only;sourcekernelMAX200000unchanged. Instrumentationdelegatesoriginalfunctionsandreportswithoutmodification.',instrumentation='Patchpolicyforce_rows,tick,marginandcertifierfactorywithdelegatingwrappers. OrdinaryforecastinvalidreportsremainFalseandcontinueoriginalcandidate/cachelogic. Actualstrict1.059remainsoriginal;forecastusesexactpolicy.ADMISSIONfloat. Strongreflinear->historylineageperchooser;freshFINALreturnsseedhistory,notpreviouscandidatecounts. Forecastsneverupdateactualtracker/visited/history/clocks.',reservation='Beforeeverychooserreserve1536forecast+4actual+292replayattempts/external/internalforce,1568forecastgeometry+4actual+292replaygeometry,plus12CPU/18wallreplayand15CPU/25wallaudit. Checkallcaps/deadlineinsideforce/tick/geometry/certificationloops. Reservationsdo not consume actual counts.',safety='Unchangedsourceforce/clipping/reference/footprint/path/body/projection/action/finish/timepredicates. Body/domain/integrity/IOhardstop;ordinaryforecastforce/clip/geometry/referencefailurestotheoriginalcertifier. No-safe-actionrecordedseparately. Time/work/reservation=>budget-censored,not scientificfailure.',planes=d.rd(INPUTS['planes579'])['gates']['planes'],crossing='Useunchanged579crossing:fixedworldplane,firstforwardcrossing,±10progress/pathcorridor3. Completecrossingholdstrictsafe. Velocityvectorinterpolationthen norm. yaw/joint/omegainterpolateddiagnostics;integerhistorybefore/afterraw,marginreportedafterraw. Integergaininterval[baselinebefore-candidateafter,baselineafter-candidatebefore],noperformancegate.',verification='Replayexactrecordedcommandsincludingprefix132fromoriginalsourceinitialstate;nochooser/lawreselection. Compareallfullrows,finalroot/visited/tracker/history/clockcheckpointbycontentsandbothplaneobservations.',cost_categories='Separateprefix/forecast/actual/replayattempts,completedticks,external/internalactualwheelcalls,currentgeometry/geometrychecks,certifications/cachemiss/hits/FINAL,preparationandaudit. Legacycostdiagnosticnotdoublecharged.',preparation_prior_charge={'CPU_s':tests['CPU_s']+1,'wall_s':tests['wall_s']+1,'meaning':'Measuredsource0testsallattempts+conservative1sregistration/hash/write;runtimeimports/preparationalsoincluded.'},tests=tests,input_sha256={k:d.sha(p) for k,p in INPUTS.items()},initial_visited_sha256=digest(d.rd(INPUTS['ledger'])['initial_visited']),dependency_file_sha256=b.manifest(),implementation_sha256={str(p.relative_to(G)):d.sha(p) for p in [Path(__file__),G/'retry/return583_math.py',G/'tests/test_return583.py']},native_actions=0,HOLDOUT=0,SEALED=0,new_FD=0,new_optimizer=0,new_learning=0,research_remaining=22758,reserve=84000,reserve_used=0,actual_incumbent_s=13.66,source_incumbent_s=13.20,paid_compute=0,privacy='Technicalcode/aggregatesonly;rawstates,commands,journal,privatemanuscriptremainprivate. Preserve582blocked/581successandalloldresults/main/Participants/userchanges/backups. Noautomaticfollowup.')
    atomic_write(CONTRACT,c);print(json.dumps(dict(registered=True,dependency_files=len(c['dependency_file_sha256']),source_ticks=0)))


class Phase(b.Phase):
    def __init__(self,s,name):
        super().__init__(s,name);self.cost.update(forecast_calls=0,forecast_ticks=0,geometry_checks=0);self.histories={};self.last_forecast_history=None;self.current_certificate=0
    def seed(self,state):
        linear=state['root'].planar.linear;self.histories={id(linear):(linear,state['tracking'].copy())};self.seed_history=state['tracking'].copy();self.seed_raw=state['global_raw'];self.last_forecast_history=self.seed_history.copy()
    def force(self,root,action):
        self.s.validate_action(action);key=id(root.planar.linear)
        if key not in self.histories or self.histories[key][0] is not root.planar.linear:raise RuntimeError('FORECAST_HISTORY_LINEAGE')
        history=self.histories[key][1];offset=(history[1]-self.seed_history[1])//4
        result=self.evaluate(root,action,history,dict(mode='forecast',chooser=self.s.choice_index,certificate=self.current_certificate,forecast_raw_offset=offset,global_raw=self.seed_raw+offset),policy.ADMISSION,.1,True)
        self.last_forecast_history=result['history'].copy();return result['forces']
    def tick(self,root,gas,brake,index,counter):
        if counter is not self.counter:raise RuntimeError('MODEL_COUNTER_ALIAS')
        pending=self.pending
        if self.s.mode=='forecast' and (pending is None or pending['gate']):raise RuntimeError('FORECAST_TICK_AFTER_REJECTION')
        after=super().tick(root,gas,brake,index,counter)
        if self.s.mode=='forecast':
            linear=after.planar.linear;self.histories[id(linear)]=(linear,pending['history'].copy())
        return after
    def geometry(self,root):
        self.cost['geometry_checks']+=1
        return self.s.geometry(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles'])


class Study:
    raw=b.base.Study.raw
    phase_times=b.Study.phase_times;switch=b.Study.switch;wheel_call=b.Study.wheel_call
    def __init__(self):
        self.contract=d.rd(CONTRACT);self.prior=self.contract['preparation_prior_charge'];self.bucket='preparation';self.mode='preparation';self.stage_start_cpu=START_CPU;self.stage_start_wall=START_WALL;self.phases={'preparation':dict(CPU_s=self.prior['CPU_s'],wall_s=self.prior['wall_s'])};self.counts=Counter();self.stage_counts={};self.mode_counts={};self.journal=None;self.choice_index=0;self.choice_calls=[];self.choice_summaries=[];self.rows=[];self.commands=[];self.hits={};self.last_state=None;self.result={};self.actual_raw=0;self.active_phase=None
        D.mkdir(mode=0o700,exist_ok=False);self.journal=Journal(D/'raw-journal-private.jsonl');self.guard()
        for k,h in self.contract['input_sha256'].items():
            if d.sha(INPUTS[k])!=h:raise RuntimeError('INPUT_HASH:'+k)
        self.validate_closure()
        for f,h in self.contract['implementation_sha256'].items():
            if d.sha(G/f)!=h:raise RuntimeError('IMPLEMENTATION_HASH:'+f)
        self.tape,self.static,self.paths,self.ledger,self.verified=[d.rd(INPUTS[k]) for k in ['tape','static','paths','ledger','verified581']]
        if digest(self.ledger['initial_visited'])!=self.contract['initial_visited_sha256']:raise RuntimeError('INITIAL_VISITED_HASH')
        self.prefix={q['index']:np.asarray(q['action'],np.float32) for q in self.verified['commands']};assert sorted(self.prefix)==list(range(1,34)) and len(self.verified['rows'])==132
        self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.orig_external=b.wheel.wheel_response;self.orig_internal=b.planar.wheel_response;self.orig_tick=policy.tick;self.orig_force=policy.force_rows;self.orig_margin=policy.margin;self.orig_factory=policy.certifier;self.original_choose=policy.choose
        self.baseline_planes={}
        for plane in self.contract['planes']:
            for row in self.tape['rows']:
                if row['index']<=24 or abs(row['progress']-plane['station_m'])>10:continue
                obs=plane_observation(row,plane)
                if obs and obs['eligible']:obs['crossing_hold_safe']=True;self.baseline_planes[str(int(plane['station_m']))]=obs;break
        assert sorted(self.baseline_planes)==['200','300']
        atomic_write(D/'STARTED.json',dict(contract_sha256=d.sha(CONTRACT),source_ticks=0,initial_inputs=self.contract['input_sha256']))
    def count(self,key,n):
        self.counts[key]+=n;self.stage_counts.setdefault(self.bucket,Counter())[key]+=n;self.mode_counts.setdefault(self.mode,Counter())[key]+=n
    def elapsed(self):return dict(CPU_s=time.process_time()-START_CPU+self.prior['CPU_s'],wall_s=time.perf_counter()-START_WALL+self.prior['wall_s'])
    def cost(self):return dict(total=dict(self.counts,**self.elapsed()),phases={k:dict(self.stage_counts.get(k,{}),**v) for k,v in self.phase_times().items()},modes={k:dict(v) for k,v in self.mode_counts.items()},external_force=self.counts['external_force'],internal_force=self.counts['internal_force'],total_force=self.counts['external_force']+self.counts['internal_force'])
    def guard(self,attempts=0,external=0,internal=0,geometry=0):
        c=self.counts
        for key,add in [('attempted_raw',attempts),('completed_model_ticks',0),('external_force',external),('internal_force',internal),('geometry_checks',geometry)]:
            if c[key]+add>CAPS[key]:raise b.BudgetStop('AGGREGATE_'+key)
        if c['external_force']+c['internal_force']+external+internal>CAPS['total_force']:raise b.BudgetStop('AGGREGATE_total_force')
        times=self.elapsed();phase=self.phase_times()[self.bucket];limit=STAGES[self.bucket]
        for key in ['CPU_s','wall_s']:
            reserve=(27 if key=='CPU_s' else 43) if self.bucket=='continuation' else 0
            if times[key]+reserve>=CAPS[key] or phase[key]>=limit[key]:raise b.BudgetStop('TIME_'+self.bucket+'_'+key)
        if 'attempted_raw' in limit and self.stage_counts.get(self.bucket,{}).get('attempted_raw',0)+attempts>limit['attempted_raw']:raise b.BudgetStop('PHASE_WORK_'+self.bucket)
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc'].replace('Z','+00:00')):raise b.BudgetStop('DEADLINE')
    def reserve(self,attempts,geometry,cpu,wall):
        self.guard()
        for key,extra in [('attempted_raw',attempts),('completed_model_ticks',attempts),('external_force',4*attempts),('internal_force',4*attempts),('geometry_checks',geometry)]:
            if self.counts[key]+extra>CAPS[key]:raise b.BudgetStop('RESERVE_'+key)
        if self.counts['external_force']+self.counts['internal_force']+8*attempts>CAPS['total_force']:raise b.BudgetStop('RESERVE_total_force')
        e=self.elapsed()
        if e['CPU_s']+cpu>1800 or e['wall_s']+wall>2400:raise b.BudgetStop('RESERVE_TIME')
    @staticmethod
    def validate_action(a):
        if not np.all(np.isfinite(a)) or abs(float(a[0]))>float(np.float32(.4)) or any(not 0<=float(v)<=1 for v in a[1:]) or a[1]*a[2]!=0:raise RuntimeError('CONTROL_DOMAIN')
    def geometry(self,root,*args):
        self.guard(geometry=1);self.count('geometry_checks',1);context=dict(mode=self.mode,chooser=self.choice_index,certificate=self.active_phase.current_certificate if self.mode=='forecast' else None,state_id=digest(d.short(root)))
        event=self.journal.append('BEFORE_GEOMETRY',**context);value=self.orig_margin(root,*args);self.journal.append('GEOMETRY_VERDICT',input_event=event,margin=value,**context);self.guard();return value
    def factory(self,*args,**kwargs):
        original=self.orig_factory(*args,**kwargs);phase=self.active_phase
        def certify(action):
            self.guard();caller_frame=sys._getframe(1);caller=caller_frame.f_code
            role='FINAL' if caller is self.original_choose.__code__ else 'SAMPLE'
            if role=='SAMPLE' and not (caller.co_name=='evaluate' and caller.co_filename==self.original_choose.__code__.co_filename):raise RuntimeError('CERTIFIER_CALLER')
            phase.current_certificate+=1;phase.last_forecast_history=phase.seed_history.copy();entry=dict(id=phase.current_certificate,role=role,report=None);self.choice_calls.append(entry)
            if role=='FINAL':entry['evaluate_requests']=1+len(caller_frame.f_locals.get('points',[]))+caller_frame.f_locals.get('refinements',0)
            self.journal.append('CERTIFICATION_STARTED',chooser=self.choice_index,certificate=entry['id'],role=role,action=action.tolist(),seed_history=phase.seed_history)
            report=original(action);self.guard()
            if [report['clipped'],report['samples']]!=phase.last_forecast_history:raise RuntimeError('CERTIFICATION_HISTORY_IDENTITY')
            entry['report']=report;self.count('certifications',1);self.count('fresh_FINAL' if role=='FINAL' else 'sample_cache_misses',1);self.journal.append('CERTIFICATION_FINISHED',chooser=self.choice_index,certificate=entry['id'],role=role,report=report);return report
        return certify
    def hold(self,state,action,index,phase,prefix=False,observe=False):
        self.validate_action(action);assert state['global_raw']==4*(index-1);rows=[];first_failure=None
        for k in range(1,5):
            row,reason=self.raw(state,action,index,k,phase);rows.append(row);self.guard()
            if prefix:
                if reason or d.canonical(row)!=self.verified['rows'][row['global_raw_before']]:raise RuntimeError('581_PREFIX_ROW_IDENTITY')
            if reason:first_failure=reason;break
            if observe:
                for plane in self.contract['planes']:
                    key=str(int(plane['station_m']))
                    if key not in self.hits:
                        hit=plane_observation(row,plane)
                        if hit:self.hits[key]=dict(hit,crossing_hold=index)
        if observe:
            for h in self.hits.values():
                if h['crossing_hold']==index:h['crossing_hold_safe']=first_failure is None and len(rows)==4
        return rows,first_failure
    def run(self):
        status=None;error=None;replay=None;state=None;failure=None;cert_failure_counts=Counter();continuation_phase=None
        b.wheel.wheel_response=lambda *a,**k:self.wheel_call('external_force',self.orig_external,*a,**k);b.planar.wheel_response=lambda *a,**k:self.wheel_call('internal_force',self.orig_internal,*a,**k)
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(b.BudgetStop('CPU_SIGNAL')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(b.BudgetStop('WALL_SIGNAL')));signal.setitimer(signal.ITIMER_PROF,max(.01,1800-self.elapsed()['CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,2400-self.elapsed()['wall_s']))
        try:
            self.reserve(62024,63304,1735,2305);self.switch('prefix');self.mode='prefix';phase=Phase(self,'prefix');self.active_phase=phase;state=d.Study.initial(self);immutable(state['root']);self.last_state=state
            for i in range(1,34):
                rr,_=self.hold(state,self.prefix[i],i,phase,prefix=True);self.rows+=rr;self.commands.append(dict(index=i,action=self.prefix[i].tolist()))
            cp=d.Study.checkpoint(self,state)
            if d.canonical(cp)!=self.verified['checkpoint']:raise RuntimeError('581_FULL_CHECKPOINT_IDENTITY')
            self.result['prefix']=dict(raw=132,all_full_rows_and_checkpoint_exact=True,checkpoint_sha256=digest(cp));atomic_write(D/'prefix-checkpoint-private.json',cp)
            self.switch('continuation');continuation_phase=Phase(self,'continuation');self.active_phase=continuation_phase
            for index in range(34,74):
                self.reserve(1536+4+292,1568+4+292,27,43);self.choice_index+=1;self.choice_calls=[];self.mode='forecast';continuation_phase.seed(state);before=digest(d.Study.checkpoint(self,state));costbefore=self.cost();policy.tick=continuation_phase.tick;policy.force_rows=continuation_phase.force;policy.margin=self.geometry;policy.certifier=self.factory
                self.journal.append('CHOOSER_STARTED',index=index,chooser=self.choice_index,actual_checkpoint=before,reserved_attempted_raw=1832,reserved_geometry=1864,actual_history=state['tracking'],cost=costbefore)
                try:
                    geometry=policy.geometry_context(self.static,66000);action,detail=self.original_choose(state['root'],self.paths['candidate'],self.paths['backup'],state['progress'],continuation_phase.counter,continuation_phase.cost,65000,history=tuple(state['tracking']),geometry=geometry)
                finally:policy.tick=self.orig_tick;policy.force_rows=self.orig_force;policy.margin=self.orig_margin;policy.certifier=self.orig_factory
                self.guard()
                if digest(d.Study.checkpoint(self,state))!=before:raise RuntimeError('FORECAST_MUTATED_ACTUAL_CHECKPOINT')
                cache=cache_accounting(detail,self.choice_calls)
                if cache['actual_certification_calls']>32:raise RuntimeError('CERTIFICATION_CAP_IDENTITY')
                self.counts['cache_hits']+=cache['cache_hits'];self.stage_counts.setdefault(self.bucket,Counter())['cache_hits']+=cache['cache_hits'];self.mode_counts.setdefault('forecast',Counter())['cache_hits']+=cache['cache_hits']
                for report in self.choice_calls:
                    if not report['report']['ok']:cert_failure_counts[report['report']['reason']]+=1
                choice=dict(index=index,chooser=self.choice_index,selected_mode=detail['mode'],cache=cache,legacy_cost=dict(continuation_phase.cost),source_cost_after=self.cost(),no_safe_action=action is None)
                self.choice_summaries.append(choice);self.journal.append('CHOOSER_FINISHED',**choice);atomic_write(D/f'choice-{index:03d}-private.json',dict(action=action.tolist() if action is not None else None,detail=detail,certifications=self.choice_calls,checkpoint=d.Study.checkpoint(self,state),cost=self.cost()))
                continuation_phase.histories.clear()
                if action is None:status='NO_SAFE_ACTION';failure=dict(index=index,reason='NO_ADMISSIBLE_ACTION');break
                if not detail.get('final_recertified') or not any(c['role']=='FINAL' and c['report']['ok'] for c in self.choice_calls):raise RuntimeError('FRESH_FINAL_IDENTITY')
                self.mode='actual';self.commands.append(dict(index=index,action=action.tolist()));rr,reason=self.hold(state,action,index,continuation_phase,observe=True);self.rows+=rr;self.actual_raw+=len(rr)
                atomic_write(D/'continuation-latest-private.json',dict(index=index,rows=rr,commands=self.commands,checkpoint=d.Study.checkpoint(self,state),hits=self.hits,cost=self.cost()),True)
                if reason:status='ACTUAL_SAFETY_FAILURE';failure=dict(index=index,raw=rr[-1]['raw'],attempted_global_raw=rr[-1]['global_raw_before']+1,reason=reason);break
                if '300' in self.hits:
                    status='SAFE_RETURN_TO_S300' if self.hits['300']['eligible'] and self.hits['300']['crossing_hold_safe'] else 'S300_CROSSING_OUTSIDE_WINDOW';break
            if status is None:status='DEPTH_LIMIT40'
            if status=='SAFE_RETURN_TO_S300':
                self.reserve(292,292,27,43);self.switch('verification');self.mode='replay';phase=Phase(self,'verification');self.active_phase=phase;again=d.Study.initial(self);immutable(again['root']);actual=[];replay_hits={}
                for command in self.commands:
                    rr,reason=self.hold(again,np.asarray(command['action'],np.float32),command['index'],phase);actual+=rr
                    if reason:raise RuntimeError('INDEPENDENT_REPLAY_REJECTION:'+reason)
                    for r in rr:
                        for plane in self.contract['planes']:
                            key=str(int(plane['station_m']))
                            if key not in replay_hits and command['index']>=34:
                                hit=plane_observation(r,plane)
                                if hit:replay_hits[key]=hit
                exact=len(actual)==len(self.rows) and len(actual)<=292 and d.canonical(actual)==d.canonical(self.rows);checkpoint=d.canonical(d.Study.checkpoint(self,again))==d.canonical(d.Study.checkpoint(self,state))
                if not exact or not checkpoint:raise RuntimeError('INDEPENDENT_REPLAY_IDENTITY')
                for key,hit in self.hits.items():
                    expected={k:v for k,v in hit.items() if k not in ['crossing_hold','crossing_hold_safe']};expected['crossing_hold_safe']=False
                    if replay_hits[key]!=expected:raise RuntimeError('INDEPENDENT_PLANE_IDENTITY')
                replay=dict(raw=len(actual),all_full_rows_exact=True,full_checkpoint_contents_exact=True,plane_observations_exact=True,chooser_reselection=False);atomic_write(D/'verified-tape-private.json',dict(rows=actual,commands=self.commands,checkpoint=d.Study.checkpoint(self,again),hits=replay_hits));status='SAFE_RETURN_TO_S300_EXACT_REPLAY'
        except BaseException as exc:
            error=type(exc).__name__+':'+str(exc);status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE';atomic_write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),partial_certifications=self.choice_calls,cost=self.cost()),True)
        finally:
            atomic_write(G/'retry/return583_cost.json',self.cost(),True);policy.tick=self.orig_tick;policy.force_rows=self.orig_force;policy.margin=self.orig_margin;policy.certifier=self.orig_factory;b.wheel.wheel_response=self.orig_external;b.planar.wheel_response=self.orig_internal
            if state is not None:atomic_write(D/'run-tape-private.json',dict(rows=self.rows,commands=self.commands,checkpoint=d.Study.checkpoint(self,state),hits=self.hits,status=status),True)
            try:
                self.switch('audit');self.mode='audit';self.journal.close();audit=inspect(D/'raw-journal-private.jsonl');self.validate_closure();self.guard()
            except BaseException as exc:
                audit=dict(valid=False,error=str(exc));status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE';error=(error or '')+';AUDIT:'+str(exc)
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            self.result.update(status=status,error=error,failure=failure,planes={k:dict(observation=v,baseline577=self.baseline_planes[k],comparison=bracket_comparison(v,self.baseline_planes[k])) for k,v in self.hits.items()},continuation_actual_raw=self.actual_raw,continuation_selected_holds=len([q for q in self.commands if q['index']>=34]),chooser_calls=self.choice_index,choices=self.choice_summaries,forecast_rejection_reasons=dict(cert_failure_counts),independent_replay=replay,journal=audit,cost=self.cost(),actual_incumbent_s=13.66,source_incumbent_s=13.20,incumbent_changed=False,native_actions=0,whole_executed=False,HOLDOUT=0,SEALED=0,new_FD=0,new_optimizer=0,new_learning=0,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0)
            atomic_write(G/'retry/return583_cost.json',self.cost(),True);atomic_write(G/'retry/return583_result.json',self.result);print(json.dumps(plain(self.result),indent=2))
    def validate_closure(self):
        for f,h in self.contract['dependency_file_sha256'].items():
            if d.sha(G/f if not Path(f).is_absolute() else Path(f))!=h:raise RuntimeError('DEPENDENCY_HASH:'+f)
        if any(f not in self.contract['dependency_file_sha256'] for f in b.manifest()):raise RuntimeError('UNMANIFESTED_IMPORT')

if __name__=='__main__':
    if '--register' in sys.argv:register()
    else:
        study=None
        try:study=object.__new__(Study);study.__init__();study.run()
        except BaseException as exc:
            out=dict(status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE',error=type(exc).__name__+':'+str(exc),source_execution_started=bool(study and getattr(study,'counts',{}).get('attempted_raw',0)),counts=dict(getattr(study,'counts',{})) if study else {},CPU_s=time.process_time()-START_CPU+getattr(study,'prior',{}).get('CPU_s',0),wall_s=time.perf_counter()-START_WALL+getattr(study,'prior',{}).get('wall_s',0))
            if D.exists():atomic_write(D/'outer-failure-private.json',dict(out,traceback=traceback.format_exc()),True)
            atomic_write(G/'retry/return583_outer_failure.json',out);raise
