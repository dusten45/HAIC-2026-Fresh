"""One feasible-incumbent, fifty-coordinate bounded SLSQP source shooting run."""
import time
START_CPU=time.process_time();START_WALL=time.perf_counter()
import sys,json,math,datetime,signal,traceback,hashlib,copy
from pathlib import Path
from collections import Counter
import numpy as np
import scipy
from scipy.optimize import minimize
from retry.clip561_core import atomic_write,plain
from retry.durable568 import Journal,digest,inspect
import retry.beam579_model as b
from retry.beam579_math import immutable,clone,isolated,crossing
from retry.shoot586_math import SCALE,DOMAIN,NCON,ExpressionStop,seed_controls,canonical,action,command_key,fd_point,residuals,objective,faster,numeric_resolution

d=b.d;G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response586-private');CONTRACT=G/'retry/shoot586_contract.json'
INPUTS={**b.INPUTS,'planes':G/'retry/beam579_contract.json'}
CAPS=dict(attempted_raw=22000,completed_model_ticks=22000,geometry_checks=22500,external_force=90000,internal_force=90000,total_force=180000,CPU_s=900,wall_s=1200)
STAGES={'preparation':dict(CPU_s=30,wall_s=45),'positive':dict(attempted_raw=252,CPU_s=15,wall_s=25),'optimization':dict(CPU_s=780,wall_s=1000),'verification':dict(attempted_raw=1324,CPU_s=50,wall_s=80),'audit':dict(CPU_s=15,wall_s=25)}
class OptimizationStop(RuntimeError):pass
class BodyStop(RuntimeError):
    def __init__(self,after,value,pending):super().__init__('BODY');self.after=after;self.value=value;self.pending=pending

def warm_solver():
    # One pure numerical toy, no source/force calls; preload actual solver imports.
    result=minimize(lambda x:float(x[0]**2),np.array([.1]),jac=lambda x:np.array([2*x[0]]),bounds=[(-1.,1.)],constraints=[{'type':'ineq','fun':lambda x:np.array([1.-x[0]**2]),'jac':lambda x:np.array([[-2*x[0]]])}],method='SLSQP',options={'maxiter':1,'ftol':1e-9,'disp':False})
    return dict(minimize_calls=1,pure_numerical=True,source_ticks=0,status=int(result.status))

def register():
    warm=warm_solver();tests=d.rd(G/'retry/shoot586_tests.json');assert tests['passed']
    c=dict(study=586,status='FROZEN_BEFORE_SOURCE',parent_commit='7e49e350f64c9ce76d047c76bd2083b68b993368',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',question='Canjointdirectshootingofholds25..49improvefixeds300crossingwhileretainingstrictsafetyand577fixedcontinuation?',scope='Positiveinitial252raw577exactcontrol;independentfullraw96checkpointpernewcandidate;25holds/50individualsteer-signedpedalcoords;unchanged577holds50..63to252;max128suffixcachemissesincludingFD/line-search/failure. Onlyonefasterstrictsafe candidategetsoneinitialwhole<=662andifwhole safeoneinitialexactreplay<=662.No585EARLY/LATEprograms,beam,basis,feedback,seedrestart,sweep,native,automaticpromotion.',variables=dict(holds=[25,49],coordinates=50,order='steer,signedpedalperhold;float32commands,4rawduration;u>0gas,u<0brake',scale=SCALE.tolist(),bounds='Fullphysicalrepresentablefloat32steer±float32(.4),signedpedal±1;zero canonicalized. z=(x−seed)/scale;noextra tube/trust-region thatcouldexcludeoriginalincumbent.',FD='Forwardnormalizedh=.001(steer2e-5,pedal1e-4),minusonlyifpluswouldexceedphysicalupperbound;actualfloat32commanddelta/scale denominator;zeroactualdelta=>expressionstop,nootherstep.50columnsperJacobian,derivativesproposalonly.'),solver=dict(library='scipy.optimize.minimize',scipy_version=scipy.__version__,method='SLSQP',maxiter=3,ftol=1e-9,disp=False,restarts=0,manual_objective_and_inequality_Jacobian=True,Jacobian_cache='Shared50-columnFD forobjective/constraints,oneperactualcanonicalanchor;cachedactualcommandbytekeycollapsesquantizedidenticalproposals;countmissBEFOREevaluation. Baselinecachecomesfromfreshpositivecontrol,notnewunrecordedsource.',failure='Firstexactstrictsafetyfailurestopsdiagnosticcase;fixed1718residuals156x11plus2terminal. Observedforce/clip/bodyonlywhereavailable;unobservedgeometryandallunobservedlatercomponents−1. Completesuffixandvalids300terminalflags±1. No observedpartial can becomeadmissible. Nonfinite/control/domain/integrity/durableIO=>technicalstudy stop. Finitebody>=100=>caseBODYrejectbeforenextphysics,unlikepriorwhole-studybodyexceptionhandling;thresholdbody<100unchanged.',constraints='Perraw4force(1.059−ratio),clip(.1−clip/samples)/.1,footprint(margin−.5),path(3−error)/3,reference(4.85−overspeed)/5,projectionlow(delta+.5),projectionup(limit−delta)/5,body(100−body)/100. Exactsourcepredicate separately decideseligibility;SLSQPnonnegative/ftolneverreplacesstrictbody<100ororiginalsafety.',objective='Complete252strictsafe+firsteligiblefixeds300crossingwholeholdsafe=>absoluteepisodecentreplanechordtime. Elsebaseline_s300_time+1+(156−observedattemptrows)/156. Missedcrossing/failedtrajectoryinadmissible;eventfailureFDnotafeasible-set/infeasibilitycertificate.'),acceptance='Originalrepresentable577seedexplicitlysafeandcachedfrompositivecontrol. EveryactualevaluatedFD/proposalsafecompletecandidateeligibleforbestcontinuouss300time,notjustsolverreturn. Improvement>32ULPofcrossingtimeonlynumericresolution,no100/500msperformancegate. RequireactualcommandbytesANDendcheckpointchange.No universal tube/error gate. Keeporiginalincumbentalways;candidateislocalonlyuntilwholeandindependentexactreplay.',crossing='Existing579s200/s300fixedworldplanes,firstforwardcrossinglocked,progress±10/pathcorridor3,wholecrossingholdstrictsafe. s200observation;objectiveonlys300continuouschordtimeandintegerbracketbothreported.',verification='Onlyselectedonefasterlocalcandidate:initialwholeexecutealtered25..49andallotherunchanged577commandsuntiloriginalofficialtrackerconfirmedfinishor662max.Noextrapolation/newcommandbeyondstoredtape. Firstsafetyfailure/missedfinish=>failedwhole,noreplay. Wholefirst252suffixmustexactlymatchselectedcase. Ifsafe,oneinitialexacttape replayallfullrows/forces/history/tracker/visited/clock/finalCPcontents andplaneobservations. Nativeandincumbentautomaticpromotionexcluded.',caps=CAPS,stage_caps=STAGES,worst_work=dict(suffix_calls=128,suffix_raw_each=156,positive_raw=252,whole_and_replay_raw=1324,total_raw_attempts_and_completed=21544,external_force=86176,internal_force=86176,total_force=172352,current_root_geometry_extra=131,total_geometry=21675,forecast_ticks=0),reservation='Beforeeachnewactualproposalreserve156raw+remainingwhole/replay1324rawandcurrentrootgeometry1+remaining2;CPU50/wall80verification+audit15CPU/wall25. Keepentireverificationreservationthroughoptimization. Currentrootcheck/failedpreforce/internalcallsseparate. Solver/FD/cache/numericalCPUincluded;purewarmtoyoneperregistrationandruntimechargedpreparation.',preparation_prior_charge=dict(CPU_s=tests['CPU_s']+1,wall_s=tests['wall_s']+1,meaning='Measuredsource0testsallattemptsplusconservative1sregistration/hash/toynumerics;runtimeimports/warmtoyalsoincluded.'),numerical_preparation=dict(registration=warm,tests_pure_minimize_calls=len(tests['attempts']),tests=tests),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},initial_visited_sha256=digest(d.rd(INPUTS['ledger'])['initial_visited']),dependency_file_sha256=b.manifest(),implementation_sha256={str(p.relative_to(G)):d.sha(p) for p in [Path(__file__),G/'retry/shoot586_math.py',G/'tests/test_shoot586.py']},actual_incumbent_s=13.66,source_incumbent_s=13.20,native_actions=0,HOLDOUT=0,SEALED=0,new_learning=0,new_world=0,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0,privacy='Onlytechnicalcode/contracts/aggregatespublic;rawplans/states/journalprivateoutsideG.Preservealloldfailures/577/585proposal/main/Participants/userchanges/backups.Noautomaticfollowup.')
    assert 128*156+252+1324==21544 and 21544+131<22500
    atomic_write(CONTRACT,c);print(json.dumps(dict(registered=True,dependency_files=len(c['dependency_file_sha256']),source_ticks=0,worst_work=c['worst_work'])))

class Phase(b.Phase):
    def tick(self,root,gas,brake,index,counter):
        p=self.pending
        if counter is not self.counter or p is None or p['root_id']!=digest(d.short(root)) or [gas,brake]!=p['action'][1:]:raise RuntimeError('EXACT_FORCE_TICK_IDENTITY')
        self.s.journal.append('BEFORE_TICK',force_event=p['event'],context=p['context'],**p['identity']);after=d.source_tick(root,gas,brake,index,counter);self.s.count('completed_model_ticks',1);body=b.base.body(after)
        self.s.journal.append('AFTER_TICK',force_event=p['event'],root=d.short(after),body=body,body_domain_pass=math.isfinite(body) and body<100,context=p['context']);self.cost['body_checks']+=1;self.cost['max_body']=max(self.cost['max_body'],body);self.pending=None
        if not math.isfinite(body):raise RuntimeError('NONFINITE_BODY_DOMAIN')
        if body>=100:raise BodyStop(after,body,p)
        return after
    def geometry(self,root):
        self.s.guard(geometry=1);self.s.count('geometry_checks',1);event=self.s.journal.append('BEFORE_GEOMETRY',mode=self.s.mode,state_id=digest(d.short(root)));value=d.margin(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles']);self.s.journal.append('GEOMETRY_VERDICT',input_event=event,margin=value,mode=self.s.mode);self.s.guard();return value

class Study:
    phase_times=b.Study.phase_times;wheel_call=b.Study.wheel_call
    def __init__(self):
        self.contract=d.rd(CONTRACT);self.prior=self.contract['preparation_prior_charge'];self.bucket='preparation';self.mode='preparation';self.stage_start_cpu=START_CPU;self.stage_start_wall=START_WALL;self.phases={'preparation':{k:self.prior[k] for k in ['CPU_s','wall_s']}};self.counts=Counter();self.stage_counts={};self.mode_counts={};self.cases=0;self.cache_requests=0;self.cache_hits=0;self.fd_columns=0;self.fd_batches=0;self.numerical_calls=0;self.events=[];self.cache={};self.best=None;self.seedcase=None;self.fd_cache=None;self.journal=None;self.result={};self.last_partial=None;self.verification_raw_remaining=1324
        D.mkdir(mode=0o700,exist_ok=False);self.journal=Journal(D/'raw-journal-private.jsonl');self.guard();self.result['runtime_pure_warm_solver']=warm_solver();self.numerical_calls+=1
        self.validate_closure()
        for k,h in self.contract['input_sha256'].items():
            if d.sha(INPUTS[k])!=h:raise RuntimeError('INPUT_HASH:'+k)
        for f,h in self.contract['implementation_sha256'].items():
            if d.sha(G/f)!=h:raise RuntimeError('IMPLEMENTATION_HASH:'+f)
        self.tape,self.static,self.paths,self.ledger=[d.rd(INPUTS[k]) for k in ['tape','static','paths','ledger']];self.commands={q['index']:np.asarray(q['action'],np.float32) for q in self.tape['commands']};self.seed=seed_controls(self.commands);assert all(action(self.seed,i).tobytes()==self.commands[i].tobytes() for i in range(25,50));self.planes=d.rd(INPUTS['planes'])['gates']['planes'];self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.orig_external=b.wheel.wheel_response;self.orig_internal=b.planar.wheel_response
        if digest(self.ledger['initial_visited'])!=self.contract['initial_visited_sha256']:raise RuntimeError('INITIAL_VISITED_HASH')
        atomic_write(D/'STARTED.json',dict(contract_sha256=d.sha(CONTRACT),source_ticks=0,input_sha256=self.contract['input_sha256']))
    def count(self,k,n):self.counts[k]+=n;self.stage_counts.setdefault(self.bucket,Counter())[k]+=n;self.mode_counts.setdefault(self.mode,Counter())[k]+=n
    def elapsed(self):return dict(CPU_s=time.process_time()-START_CPU+self.prior['CPU_s'],wall_s=time.perf_counter()-START_WALL+self.prior['wall_s'])
    def cost(self):return dict(total=dict(self.counts,**self.elapsed()),phases={k:dict(self.stage_counts.get(k,{}),**v) for k,v in self.phase_times().items()},modes={k:dict(v) for k,v in self.mode_counts.items()},suffix_cache_misses=self.cases,cache_requests=self.cache_requests,cache_hits=self.cache_hits,FD_columns=self.fd_columns,FD_batches=self.fd_batches,minimize_calls_runtime=self.numerical_calls,forecast_ticks=0)
    def guard(self,attempts=0,external=0,internal=0,geometry=0):
        for k,n in [('attempted_raw',attempts),('completed_model_ticks',0),('external_force',external),('internal_force',internal),('geometry_checks',geometry)]:
            if self.counts[k]+n>CAPS[k]:raise b.BudgetStop('AGGREGATE_'+k)
        if self.counts['external_force']+self.counts['internal_force']+external+internal>180000:raise b.BudgetStop('AGGREGATE_total_force')
        for key,val in self.elapsed().items():
            tail=(65 if key=='CPU_s' else 105) if self.bucket=='optimization' else 0
            if val+tail>=CAPS[key] or self.phase_times()[self.bucket][key]>=STAGES[self.bucket][key]:raise b.BudgetStop('TIME_'+self.bucket+'_'+key)
        if 'attempted_raw' in STAGES[self.bucket] and self.stage_counts.get(self.bucket,{}).get('attempted_raw',0)+attempts>STAGES[self.bucket]['attempted_raw']:raise b.BudgetStop('PHASE_ATTEMPTS_'+self.bucket)
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc'].replace('Z','+00:00')):raise b.BudgetStop('DEADLINE')
    def switch(self,name):
        # Reserved validation/audit must remain reachable after an optimization cap.
        if name not in ['verification','audit']:self.guard()
        self.phases=self.phase_times();self.bucket=name;self.stage_start_cpu=time.process_time();self.stage_start_wall=time.perf_counter();self.phases.setdefault(name,dict(CPU_s=0.,wall_s=0.));self.guard()
    def reserve(self,raw,geometry,cpu,wall):
        self.guard()
        for k,n in [('attempted_raw',raw),('completed_model_ticks',raw),('external_force',4*raw),('internal_force',4*raw),('geometry_checks',geometry)]:
            if self.counts[k]+n>CAPS[k]:raise b.BudgetStop('RESERVE_'+k)
        if self.counts['external_force']+self.counts['internal_force']+8*raw>180000:raise b.BudgetStop('RESERVE_total_force')
        if self.elapsed()['CPU_s']+cpu>900 or self.elapsed()['wall_s']+wall>1200:raise b.BudgetStop('RESERVE_TIME')
    def validate_closure(self):
        for f,h in self.contract['dependency_file_sha256'].items():
            if d.sha(G/f if not Path(f).is_absolute() else Path(f))!=h:raise RuntimeError('DEPENDENCY_HASH:'+f)
        if any(f not in self.contract['dependency_file_sha256'] for f in b.manifest()):raise RuntimeError('UNMANIFESTED_IMPORT')
    def raw(self,state,a,index,k,phase):
        try:return b.base.Study.raw(self,state,a,index,k,phase)
        except BodyStop as exc:
            p=exc.pending;row=dict(index=index,raw=k,action=a.tolist(),global_raw_before=state['global_raw'],global_raw_after=state['global_raw']+1,episode_before_s=state['elapsed'],episode_after_s=state['elapsed']+.02,before_root_without_roads=None,root_without_roads=d.short(exc.after),forces=p['forces'],tracking_history_before=state['tracking'].copy(),launch_history_before=state['launch'].copy(),proposed_history=p['history'],pre_failure=None,post_failure='BODY',all_failures=['BODY'],body=exc.value,failed_body_state_not_committed=True)
            self.journal.append('RAW_BODY_REJECTION',context=p['context'],force_event=p['event'],body=exc.value);return row,'BODY'
    def initial(self):
        state=d.Study.initial(self);immutable(state['root']);return state
    def checkpoint(self,state):return d.Study.checkpoint(self,state)
    def expected_checkpoint(self,raw):
        rr=self.tape['rows'][raw-1];visited=set(self.ledger['initial_visited'])
        for r in self.tape['rows'][:raw]:
            for ids in r['root_without_roads']['current_contacts']:visited.update(ids)
        return dict(root_without_roads=rr['root_without_roads'],visited=sorted(visited),tracker=rr['tracker'],elapsed=rr['episode_after_s'],global_raw=raw,progress=rr['progress'],launch=self.tape['rows'][95]['proposed_history'],tracking=rr['proposed_history'] if raw>96 else [0,0])
    def observations(self,rows):
        hits={}
        for row in rows:
            if 'margin' not in row:continue
            for plane in self.planes:
                key=str(int(plane['station_m']))
                if key in hits:continue
                h=crossing(row,plane)
                if h:
                    holdrows=[r for r in rows if r['index']==row['index']];h.update(time_s=h['before_s']+h['fraction']*(h['after_s']-h['before_s']),hold=row['index'],whole_hold_safe=len(holdrows)==4 and all(not r['pre_failure'] and not r.get('post_failure') for r in holdrows));hits[key]=h
        return hits
    def compile_case(self,rows,state,failure,x,case_id):
        hits=self.observations(rows);complete=failure is None and len(rows)==156 and state['global_raw']==252;valid=complete and '300' in hits and hits['300']['eligible'] and hits['300']['whole_hold_safe'];g=residuals(rows,complete,valid);f=objective(valid,hits.get('300'),self.baseline_time,len(rows));cp=self.checkpoint(state)
        return dict(id=case_id,x=x.copy(),safe=complete,admissible=valid,f=f,g=g,hits=hits,failure=failure,observed_attempt_rows=len(rows),end_checkpoint_sha256=digest(cp))
    def positive(self):
        self.switch('positive');self.mode='positive';phase=Phase(self,'positive');state=self.initial();rows=[];phase.geometry(state['root'])
        for index in range(1,64):
            for k in range(1,5):
                row,why=self.raw(state,self.commands[index],index,k,phase);rows.append(row);self.guard()
                if why or d.canonical(row)!=self.tape['rows'][row['global_raw_before']]:raise RuntimeError('POSITIVE_ROW_IDENTITY_OR_SAFETY')
                if state['global_raw']==96:
                    self.start=clone(state);immutable(self.start['root']);isolated(self.start,[state])
                    if d.canonical(self.checkpoint(self.start))!=d.canonical(self.expected_checkpoint(96)):raise RuntimeError('POSITIVE_RAW96_CHECKPOINT')
                    self.start_digest=digest(self.checkpoint(self.start));atomic_write(D/'raw96-checkpoint-private.json',self.checkpoint(self.start))
        if d.canonical(self.checkpoint(state))!=d.canonical(self.expected_checkpoint(252)):raise RuntimeError('POSITIVE_RAW252_CHECKPOINT')
        seedhits=self.observations(rows[96:]);assert seedhits['300']['eligible'] and seedhits['300']['whole_hold_safe'];self.baseline_time=seedhits['300']['time_s'];self.seedcase=self.compile_case(rows[96:],state,None,self.seed,0)
        if not self.seedcase['admissible'] or np.min(self.seedcase['g'])<0:raise RuntimeError('FEASIBLE_SEED_REPRESENTATION')
        self.best=self.seedcase;self.cache[command_key(self.seed)]=self.seedcase;atomic_write(D/'positive-private.json',dict(rows=rows,checkpoint=self.checkpoint(state),suffix=self.seedcase));self.result['positive']=dict(raw=252,all_full_rows_exact=True,all_available_checkpoint_fields_exact=True,raw96_full_checkpoint_sha256=self.start_digest,baseline_planes=seedhits,seed_minimum_constraint=float(np.min(self.seedcase['g'])),representable_incumbent_explicitly_retained=True)
    def evaluate_x(self,x,kind):
        self.cache_requests+=1;key=command_key(x)
        if key in self.cache:self.cache_hits+=1;return self.cache[key]
        if self.cases>=128:raise OptimizationStop('SUFFIX_CALL_CAP')
        self.reserve(156+self.verification_raw_remaining,157+self.verification_raw_remaining+2,65,105);self.cases+=1;case_id=self.cases;self.mode='suffix_'+kind;self.last_partial=dict(id=case_id,kind=kind,x=x,rows=[]);state=clone(self.start);isolated(state,[self.start]);phase=Phase(self,'optimization');rows=[];why=None
        if digest(self.checkpoint(state))!=self.start_digest:raise RuntimeError('INDEPENDENT_RAW96_CHECKPOINT')
        self.journal.append('CANDIDATE_STARTED',id=case_id,candidate_kind=kind,control_sha256=hashlib.sha256(key).hexdigest(),checkpoint_sha256=self.start_digest);phase.geometry(state['root'])
        for index in range(25,64):
            a=action(x,index) if index<=49 else self.commands[index]
            for k in range(1,5):
                row,why=self.raw(state,a,index,k,phase);rows.append(row);self.last_partial['rows']=rows;self.guard()
                if why:break
            if why:break
        if digest(self.checkpoint(self.start))!=self.start_digest:raise RuntimeError('SUFFIX_MUTATED_SHARED_CHECKPOINT')
        case=self.compile_case(rows,state,why,x,case_id);record=dict(id=case_id,candidate_kind=kind,safe=case['safe'],admissible=case['admissible'],failure=why,attempted_rows=len(rows),first_failure_raw=rows[-1]['global_raw_before']+1 if why else None,objective_s=case['f'],planes=case['hits'],minimum_residual=float(np.min(case['g'])),changed_coordinates=int(np.count_nonzero(x!=self.seed)),selected_local_best=False)
        if case['admissible'] and faster(case['f'],self.best['f']) and key!=command_key(self.seed) and case['end_checkpoint_sha256']!=self.seedcase['end_checkpoint_sha256']:self.best=case;record['selected_local_best']=True
        self.events.append(record);self.cache[key]=case;atomic_write(D/f'case-{case_id:03d}-private.json',dict(rows=rows,checkpoint=self.checkpoint(state),case=case,record=record));self.journal.append('CANDIDATE_FINISHED',**record);atomic_write(G/'retry/shoot586_events.json',self.events,True);atomic_write(G/'retry/shoot586_cost.json',self.cost(),True);self.last_partial=None;print(json.dumps(dict(stage='CASE',**record,cost=self.cost()['total'])),flush=True);return case
    def query(self,z):return self.evaluate_x(canonical(z,self.seed),'proposal')
    def jacobian(self,z):
        x=canonical(z,self.seed);key=command_key(x)
        if self.fd_cache is not None and self.fd_cache['key']==key:return self.fd_cache
        center=self.evaluate_x(x,'FD_anchor');J=np.empty((NCON,50));df=np.empty(50);details=[];self.fd_batches+=1
        for j in range(50):
            y,delta,sign=fd_point(x,j);case=self.evaluate_x(y,'FD');df[j]=(case['f']-center['f'])/delta;J[:,j]=(case['g']-center['g'])/delta;self.fd_columns+=1;details.append(dict(coordinate=j,delta_normalized=delta,sign=sign,case_id=case['id'],admissible=case['admissible']))
        if not np.all(np.isfinite(J)) or not np.all(np.isfinite(df)):raise ExpressionStop('NONFINITE_JACOBIAN')
        self.fd_cache=dict(key=key,df=df,J=J);atomic_write(D/f'FD-{self.fd_batches:02d}-private.json',dict(anchor=x,details=details,df=df,J=J));return self.fd_cache
    def whole(self,x,label,expected=None):
        self.mode=label;phase=Phase(self,'verification');state=self.initial();rows=[];failure=None;phase.geometry(state['root'])
        for index in range(1,167):
            a=action(x,index) if 25<=index<=49 else self.commands[index]
            for k in range(1,5):
                if len(rows)>=662:break
                row,failure=self.raw(state,a,index,k,phase);rows.append(row);self.verification_raw_remaining-=1;self.guard()
                if expected is not None:
                    if len(rows)>len(expected) or d.canonical(row)!=d.canonical(expected[len(rows)-1]):raise RuntimeError('EXACT_WHOLE_REPLAY_ROW')
                if failure or state['tracker'].finish_time_s is not None:break
            if failure or state['tracker'].finish_time_s is not None or len(rows)>=662:break
        finished=state['tracker'].finish_time_s is not None;safe=failure is None and finished;hits=self.observations(rows);out=dict(safe=safe,finished=finished,failure=failure or (None if finished else 'NO_FINISH_BY662'),raw=len(rows),official_candidate_time_s=state['tracker'].finish_time_s-1.02 if finished else None,official_candidate_raw=round((state['tracker'].finish_time_s-1.02)/.02) if finished else None,planes=hits)
        atomic_write(D/(label+'-private.json'),dict(rows=rows,checkpoint=self.checkpoint(state),outcome=out));return rows,state,out
    def run(self):
        status=error=None;optimizer_out=None;optimization_stop=None;whole_out=replay_out=None
        b.wheel.wheel_response=lambda *a,**k:self.wheel_call('external_force',self.orig_external,*a,**k);b.planar.wheel_response=lambda *a,**k:self.wheel_call('internal_force',self.orig_internal,*a,**k)
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(b.BudgetStop('CPU_SIGNAL')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(b.BudgetStop('WALL_SIGNAL')));signal.setitimer(signal.ITIMER_PROF,max(.01,900-self.elapsed()['CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,1200-self.elapsed()['wall_s']))
        try:
            self.reserve(21544,21675,860,1130);self.positive();self.switch('optimization');self.mode='optimizer';bounds=list(zip((-DOMAIN-self.seed)/SCALE,(DOMAIN-self.seed)/SCALE));self.numerical_calls+=1
            try:
                result=minimize(lambda z:self.query(z)['f'],np.zeros(50),jac=lambda z:self.jacobian(z)['df'],bounds=bounds,constraints=[{'type':'ineq','fun':lambda z:self.query(z)['g'],'jac':lambda z:self.jacobian(z)['J']}],method='SLSQP',options={'maxiter':3,'ftol':1e-9,'disp':False});optimizer_out=dict(success=bool(result.success),status=int(result.status),message=str(result.message),nit=int(result.nit),nfev=int(result.nfev),njev=int(result.njev),returned_objective_s=float(result.fun))
            except (OptimizationStop,b.BudgetStop) as exc:
                optimization_stop=type(exc).__name__+':'+str(exc);atomic_write(D/'optimizer-stop-private.json',dict(reason=optimization_stop,partial=self.last_partial,cost=self.cost()))
            if self.best['id']!=0:
                self.switch('verification');self.reserve(1324,1326,65,105);whole_rows,whole_state,whole_out=self.whole(self.best['x'],'whole-validation');local=d.rd(D/f"case-{self.best['id']:03d}-private.json")
                if d.canonical(whole_rows[96:252])!=local['rows']:raise RuntimeError('WHOLE_SELECTED_SUFFIX_IDENTITY')
                if whole_out['safe']:
                    replay_rows,replay_state,replay_out=self.whole(self.best['x'],'independent-replay',expected=whole_rows)
                    if not replay_out['safe'] or len(replay_rows)!=len(whole_rows) or d.canonical(self.checkpoint(replay_state))!=d.canonical(self.checkpoint(whole_state)) or replay_out['planes']!=whole_out['planes']:raise RuntimeError('INDEPENDENT_WHOLE_IDENTITY')
                    replay_out['all_full_rows_and_checkpoint_contents_exact']=True;status='FASTER_S300_WHOLE_SAFE_EXACT_REPLAY'
                else:status='FASTER_S300_FIXED_REMAINDER_WHOLE_FAILED'
            else:
                status='OPTIMIZATION_BUDGET_CENSORED_NO_NEW_LOCAL_CANDIDATE' if optimization_stop and ('BudgetStop' in optimization_stop or 'SUFFIX_CALL_CAP' in optimization_stop) else 'NO_NEW_SAFE_FASTER_S300'
        except BaseException as exc:status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE';error=type(exc).__name__+':'+str(exc);atomic_write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),partial=self.last_partial,cost=self.cost()),True)
        finally:
            atomic_write(G/'retry/shoot586_cost.json',self.cost(),True);b.wheel.wheel_response=self.orig_external;b.planar.wheel_response=self.orig_internal
            try:self.switch('audit');self.mode='audit';self.journal.close();audit=inspect(D/'raw-journal-private.jsonl');self.validate_closure();self.guard()
            except BaseException as exc:audit=dict(valid=False,error=str(exc));status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE';error=(error or '')+';AUDIT:'+str(exc)
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            changes=[]
            if self.best is not None:
                for j,delta in enumerate(self.best['x']-self.seed):changes.append(dict(hold=25+j//2,coordinate='steering' if j%2==0 else 'signed_pedal',delta=float(delta),normalized_delta=float(delta/SCALE[j])))
            atomic_write(D/'coordinate-changes-private.json',dict(coordinates=50,changes=changes));change_summary=dict(total_coordinates=50,changed_coordinates=sum(v['delta']!=0 for v in changes),changed_holds=len({v['hold'] for v in changes if v['delta']!=0}),max_abs_steering_delta=max((abs(v['delta']) for v in changes if v['coordinate']=='steering'),default=0.),max_abs_signed_pedal_delta=max((abs(v['delta']) for v in changes if v['coordinate']=='signed_pedal'),default=0.),normalized_Linf=max((abs(v['normalized_delta']) for v in changes),default=0.),full50_vector_private=True,private_sha256=d.sha(D/'coordinate-changes-private.json'))
            self.result.update(status=status,error=error,optimization_stop=optimization_stop,optimization_censored=bool(optimization_stop and ('BudgetStop' in optimization_stop or 'SUFFIX_CALL_CAP' in optimization_stop)),optimizer=optimizer_out,suffix_calls=self.cases,best_case_id=self.best['id'] if self.best else None,best_local_time_s=self.best['f'] if self.best else None,baseline_local_time_s=getattr(self,'baseline_time',None),best_local_planes=self.best['hits'] if self.best else None,coordinate_change_summary=change_summary,whole=whole_out,independent_replay=replay_out,events=self.events,journal=audit,cost=self.cost(),actual_incumbent_s=13.66,source_incumbent_s=13.20,incumbent_changed=False,native_actions=0,HOLDOUT=0,SEALED=0,new_learning=0,new_world=0,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0)
            atomic_write(G/'retry/shoot586_cost.json',self.cost(),True);atomic_write(G/'retry/shoot586_result.json',self.result);print(json.dumps(plain(self.result),indent=2),flush=True)

if __name__=='__main__':
    if '--register' in sys.argv:register()
    else:
        study=None
        try:study=object.__new__(Study);study.__init__();study.run()
        except BaseException as exc:
            out=dict(status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE',error=type(exc).__name__+':'+str(exc),source_execution_started=bool(study and getattr(study,'counts',{}).get('attempted_raw',0)),counts=dict(getattr(study,'counts',{})),CPU_s=time.process_time()-START_CPU+getattr(study,'prior',{}).get('CPU_s',0),wall_s=time.perf_counter()-START_WALL+getattr(study,'prior',{}).get('wall_s',0))
            if D.exists():atomic_write(D/'outer-failure-private.json',dict(out,traceback=traceback.format_exc()),True)
            atomic_write(G/'retry/shoot586_outer_failure.json',out);raise
