"""One current-cone/path-target law, twelve holds; no forecast or retry."""
import time
START_CPU=time.process_time();START_WALL=time.perf_counter()
import sys,json,math,datetime,signal,traceback
from pathlib import Path
from collections import Counter
import numpy as np
from retry.clip561_core import atomic_write,plain
from retry.durable568 import Journal,digest,inspect
import retry.beam579_model as b
from retry.beam579_math import immutable
from retry.cone584_math import select,LawStop,COUNTS

d=b.d;policy=b.base.policy;G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response584-private');CONTRACT=G/'retry/cone584_contract.json'
INPUTS={**b.INPUTS,'verified581':Path('/workspace/haic-response581-private/verified-tape-private.json'),'result583':G/'retry/return583_result.json','forensic584':G/'retry/cone584_forensic.json'}
CAPS=dict(attempted_raw=1000,completed_model_ticks=1000,external_force=4000,internal_force=4000,total_force=8000,geometry_checks=1100,CPU_s=90,wall_s=120)
STAGES={'preparation':dict(CPU_s=15,wall_s=20),'prefix':dict(attempted_raw=132,CPU_s=8,wall_s=12),'intervention':dict(attempted_raw=48,CPU_s=40,wall_s=55),'verification':dict(attempted_raw=180,CPU_s=10,wall_s=15),'audit':dict(CPU_s=10,wall_s=12)}

def register():
    tests=d.rd(G/'retry/cone584_tests.json');f=d.rd(INPUTS['forensic584']);assert tests['passed'] and f['source_ticks']==0
    priorpure=sum(f['pure_arithmetic_counts'].get(k,0)+tests['pure_arithmetic_counts'].get(k,0) for k in ['pure_wheel_formula','pure_cone_coefficients']);worst=1440+2016+priorpure
    assert worst<=4000 and worst+1440<=8000
    c=dict(study=584,status='FROZEN_BEFORE_SOURCE',parent_commit='66de0c832cb292ae7c3ecb6029c04d92c8146974',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',question='Can one current full-force-cone projected path target retain strict local viability for48raw after exact581escape?',law=dict(name='CURRENT_UNCLIPPED_FRONT_CONE_PATH_PROJECTION',coordinates='Worldforward(theta)=(-sin theta,cos theta),side=(cos theta,sin theta);currentwheelvi=COMvelocity+storedyawoffset. Rootsteer=qtarget=-action[0],wheelheading=bodyangle+joint. Onceperhold4raw.',pedals='One original537nominal(root,candidate551path,actualprogress) pure arithmetic call perhold. Keep float32gas/brake byteidentical. No choose/backup/forecast,feedbackgainchange,orbaseline rerun.',force='Applysourceorderedenginegas-memorythenbrakeanalyticallytocurrentomega:rolling=R*omega_braked. Frontgasremainsitsstoredgas. Ki=82,R=.54,dt=.02. Retainstoredwheel.frictionandstoredvelocityoffsets;neverreplacewithnewcontactfriction.',set='Qi={q in[-.4,.4]:82²[(Romega_braked)²+|vi|²−2Romega_braked|vi|cos(bodyangle+q−atan2(-vix,viy))]<=wheel.friction²}. Selectphysicalunclippedratio1.0asconservativetargetconstraint;actualsafety1.059/exactcliphistoryunchanged. Q=Q0intersectionQ1,anglewrapintervalunionsincluded.',sign_cases='Ifrolling<0 useabs(rolling)andshiftcone centreby pi. Ifrolling*|vi|=0 heading-independentall-domainor-emptyusing82*hypot(rolling,|vi|)<=friction. Nonfinite/nonpositivefriction stops. No rolling/zero-speed numericaleps.',choice='qpath=-float32originalnominalsteer. In eachcommonclosedintervalchoose nearest float32q toqpath inside interval (endpoints roundedinward);checkoriginalfullforceformula forbothvirtualfrontheadings. Up to8ULP repair towardthatintervalmidpoint only,elsetechnicalnumericstop. Acrossvalidintervals minimize lexicographic(abs(q-qpath),abs(q),q). Returnfloat32[-q,nominalgas,nominalbrake]. Qempty/no float32target=>LAW_TARGET_EMPTY;nootheraction/law/parent/retry.',transition='Source servo q_i_next=q_i+clip(qtarget-q_i,−.06,.06),withphysicaljointclip±.4 fornormalsteering_multiplier1. Underfrozenwheelstate,currentjointandtargetinsameconnectedQiintervalimplymonotonejointstaysinthatinterval. ThisisNOTapredictionofmovingbody/yaw/omega/contact. qtargetbounds thesustainedservoexcursionthatcaused583wall;actual4rawstrictsourceistherefutationtest.',limits='Staticproxydoesnotcertifyfutureforce/currentactualforce/path/footprint. Changesinvi/yaw/omega/frictionmayinvalidateit. No4rawsafety,fullfinish,timegainclaim.'),scope='Oneactual581statefromfreshinitial132raw;holds34..45max48actualraw;firstoriginalstrictsafetyfailurestops. Only48rawsafe->oneexactcommandtapeinitialreplay<=180raw. No pose/historytransplant,otherlaw/gain/parent or new baseline.',success='48actualrawalloriginalsafetypredicatesplusfullinitialexactreplay=>local48rawviability/pathmaintenanceonly. Firststrictfailurefalsifiesthisonefinitecase. LAW_TARGET_EMPTYisproxysetfailure,notall-controlinfeasibility. Budget/time=>censored;body/domain/integrity/IO/numerical=>technical. Noautomaticfollowup.',caps=CAPS,stage_caps=STAGES,worst_work=dict(prefix_raw=132,actual_raw=48,replay_raw=180,source_attempts_and_completed_max=360,forecast_ticks=0,actual_external_force_max=1440,actual_internal_force_max=1440,source_geometry_max=360,pure_force_or_cone_formula_per_decision_max=168,derivation='4currentwheel+2conecoefficients+9intervalpairs*9boundedchecks*2virtualwheel=168,12decisions=>2016. This deliberatelyoverboundsactualintervalcomponents.',runtime_pure_force_or_cone_max=2016,prior_pure_force_or_cone=priorpure,all_external_and_pure_max=worst,all_internal_max=1440,all_force_including_pure_max=worst+1440),force_accounting='Actualexternal/internalwheel_responsecallsseparate. Everypurewheel_formulaandcone_coefficientevaluation(forerensics/tests/runtime)separatebutALSOchargedtoexternal4000andcombined8000caps. Algebraicprojection/ULPrepairisnotmodelintegration;forecast0. Counterincrementsbeforeevaluation,includingfailedformula.',reservation='Beforeprefixreserve360sourceattempts/completed/geometry,external/internal1440eachplus2016pure,CPU68/wall94. Beforeeverylawreserve4actual+180replayattempts/geometry,168pure,CPU20/wall27replay+audit. Everyinterventionguardpreservesreplay10CPU/15wall+audit10CPU/12wall. Stagecapsapplytoactualcurrentwork,notfuturestage reservation.',safety='Actualforcepeak1.059tracking/2.5launch;exactclippedratio>1 and cumulativecounts10%tracking/15%launchafterhold24;footprint>=.5,path<=3,referenceoverspeed<=4.85,body<100,projectionunchanged;finitefloat32action/onepedal/steerbounds. Clocksource1224raw;wholecase<=180raw. Inheritedvisited/tracker/history/clockfromoriginalinitiallineage.',verification='Oneexactrecordedcommandreplayfromoriginalinitialstateonlyafterall48rawsafe;allfullrowsandfinalroot/visited/tracker/history/clockcheckpointcontentsmustmatch;no lawreselection.',preparation_prior_charge=dict(CPU_s=tests['CPU_s']+f['CPU_s']+1,wall_s=tests['wall_s']+f['wall_s']+1,meaning='Allsource0testsandstoredforensicsmeasuredplusconservative1sregistration/write;runtimeimportsalsocounted.'),prior_pure_counts={k:f['pure_arithmetic_counts'].get(k,0)+tests['pure_arithmetic_counts'].get(k,0) for k in set(f['pure_arithmetic_counts'])|set(tests['pure_arithmetic_counts'])},tests=tests,input_sha256={k:d.sha(p) for k,p in INPUTS.items()},initial_visited_sha256=digest(d.rd(INPUTS['ledger'])['initial_visited']),dependency_file_sha256=b.manifest(),implementation_sha256={str(p.relative_to(G)):d.sha(p) for p in [Path(__file__),G/'retry/cone584_math.py',G/'retry/cone584_forensic.py',G/'tests/test_cone584.py']},actual_incumbent_s=13.66,source_incumbent_s=13.20,native_actions=0,new_FD=0,new_optimizer=0,new_learning=0,new_world=0,whole=0,HOLDOUT=0,SEALED=0,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0,privacy='Onlytechnicalcode/contracts/aggregatespublic;rawstates/commands/journalprivateoutsiderepository. Preserveallpriorresults/main/Participants/userchanges/backups.')
    atomic_write(CONTRACT,c);print(json.dumps(dict(registered=True,source_ticks=0,worst_work=c['worst_work'])))

class Phase(b.Phase):
    def geometry(self,root):
        self.s.guard(geometry=1);self.s.count('geometry_checks',1)
        event=self.s.journal.append('BEFORE_GEOMETRY',mode=self.s.mode,state_id=digest(d.short(root)))
        value=d.margin(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles'])
        self.s.journal.append('GEOMETRY_VERDICT',input_event=event,margin=value,mode=self.s.mode);self.s.guard();return value

class Study:
    raw=b.base.Study.raw;phase_times=b.Study.phase_times;switch=b.Study.switch;wheel_call=b.Study.wheel_call
    def __init__(self):
        self.contract=d.rd(CONTRACT);self.prior=self.contract['preparation_prior_charge'];self.priorpure=self.contract['prior_pure_counts'];self.bucket='preparation';self.mode='preparation';self.stage_start_cpu=START_CPU;self.stage_start_wall=START_WALL;self.phases={'preparation':{k:self.prior[k] for k in ['CPU_s','wall_s']}};self.counts=Counter();self.stage_counts={};self.mode_counts={};self.result={'holds':[]};self.rows=[];self.commands=[];self.journal=None;self.law_calls=0
        assert not COUNTS
        D.mkdir(mode=0o700,exist_ok=False);self.journal=Journal(D/'raw-journal-private.jsonl');self.guard()
        for k,h in self.contract['input_sha256'].items():
            if d.sha(INPUTS[k])!=h:raise RuntimeError('INPUT_HASH:'+k)
        self.validate_closure()
        for f,h in self.contract['implementation_sha256'].items():
            if d.sha(G/f)!=h:raise RuntimeError('IMPLEMENTATION_HASH:'+f)
        self.static,self.paths,self.ledger,self.verified=[d.rd(INPUTS[k]) for k in ['static','paths','ledger','verified581']];self.prefix={q['index']:np.asarray(q['action'],np.float32) for q in self.verified['commands']};assert sorted(self.prefix)==list(range(1,34)) and len(self.verified['rows'])==132
        if digest(self.ledger['initial_visited'])!=self.contract['initial_visited_sha256']:raise RuntimeError('INITIAL_VISITED_HASH')
        self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.orig_external=b.wheel.wheel_response;self.orig_internal=b.planar.wheel_response
        atomic_write(D/'STARTED.json',dict(contract_sha256=d.sha(CONTRACT),source_ticks=0,input_sha256=self.contract['input_sha256']))
    def count(self,key,n):self.counts[key]+=n;self.stage_counts.setdefault(self.bucket,Counter())[key]+=n;self.mode_counts.setdefault(self.mode,Counter())[key]+=n
    def elapsed(self):return dict(CPU_s=time.process_time()-START_CPU+self.prior['CPU_s'],wall_s=time.perf_counter()-START_WALL+self.prior['wall_s'])
    def pure_work(self):return sum(self.priorpure.get(k,0)+COUNTS[k] for k in ['pure_wheel_formula','pure_cone_coefficients'])
    def cost(self):return dict(total=dict(self.counts,**self.elapsed()),phases={k:dict(self.stage_counts.get(k,{}),**v) for k,v in self.phase_times().items()},modes={k:dict(v) for k,v in self.mode_counts.items()},pure_arithmetic_prior=self.priorpure,pure_arithmetic_runtime=dict(COUNTS),all_external_including_pure=self.counts['external_force']+self.pure_work(),all_force_including_pure=self.counts['external_force']+self.counts['internal_force']+self.pure_work(),forecast_attempts=0,forecast_ticks=0)
    def guard(self,attempts=0,external=0,internal=0,geometry=0):
        c=self.counts
        for key,n in [('attempted_raw',attempts),('completed_model_ticks',0),('external_force',external+self.pure_work()),('internal_force',internal),('geometry_checks',geometry)]:
            if c[key]+n>CAPS[key]:raise b.BudgetStop('AGGREGATE_'+key)
        if c['external_force']+c['internal_force']+external+internal+self.pure_work()>8000:raise b.BudgetStop('AGGREGATE_total_force')
        for key,value in self.elapsed().items():
            tail=(20 if key=='CPU_s' else 27) if self.bucket=='intervention' else 0
            if value+tail>=CAPS[key] or self.phase_times()[self.bucket][key]>=STAGES[self.bucket][key]:raise b.BudgetStop('TIME_'+self.bucket+'_'+key)
        if 'attempted_raw' in STAGES[self.bucket] and self.stage_counts.get(self.bucket,{}).get('attempted_raw',0)+attempts>STAGES[self.bucket]['attempted_raw']:raise b.BudgetStop('PHASE_ATTEMPTS_'+self.bucket)
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc'].replace('Z','+00:00')):raise b.BudgetStop('DEADLINE')
    def reserve(self,raw,pure,cpu,wall):
        self.guard()
        for key,extra in [('attempted_raw',raw),('completed_model_ticks',raw),('external_force',4*raw+pure+self.pure_work()),('internal_force',4*raw),('geometry_checks',raw)]:
            if self.counts[key]+extra>CAPS[key]:raise b.BudgetStop('RESERVE_'+key)
        if self.counts['external_force']+self.counts['internal_force']+8*raw+pure+self.pure_work()>8000:raise b.BudgetStop('RESERVE_total_force')
        if self.elapsed()['CPU_s']+cpu>90 or self.elapsed()['wall_s']+wall>120:raise b.BudgetStop('RESERVE_TIME')
    def validate_closure(self):
        for f,h in self.contract['dependency_file_sha256'].items():
            if d.sha(G/f if not Path(f).is_absolute() else Path(f))!=h:raise RuntimeError('DEPENDENCY_HASH:'+f)
        if any(f not in self.contract['dependency_file_sha256'] for f in b.manifest()):raise RuntimeError('UNMANIFESTED_IMPORT')
    def hold(self,state,action,index,phase,prefix=False):
        assert state['global_raw']==4*(index-1) and state['global_raw']+4<=1224
        if not np.all(np.isfinite(action)):raise RuntimeError('ACTION_NONFINITE')
        rows=[]
        for k in range(1,5):
            row,reason=self.raw(state,action,index,k,phase);rows.append(row);self.guard()
            if prefix and (reason or d.canonical(row)!=self.verified['rows'][row['global_raw_before']]):raise RuntimeError('581_PREFIX_ROW_IDENTITY')
            if reason:return rows,reason
        return rows,None
    def run(self):
        status=error=failure=replay=None;state=None
        b.wheel.wheel_response=lambda *a,**k:self.wheel_call('external_force',self.orig_external,*a,**k);b.planar.wheel_response=lambda *a,**k:self.wheel_call('internal_force',self.orig_internal,*a,**k)
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(b.BudgetStop('CPU_SIGNAL')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(b.BudgetStop('WALL_SIGNAL')));signal.setitimer(signal.ITIMER_PROF,max(.01,90-self.elapsed()['CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,120-self.elapsed()['wall_s']))
        try:
            self.reserve(360,2016,68,94);self.switch('prefix');self.mode='prefix';phase=Phase(self,'prefix');state=d.Study.initial(self);immutable(state['root'])
            for index in range(1,34):
                rr,_=self.hold(state,self.prefix[index],index,phase,prefix=True);self.rows+=rr;self.commands.append(dict(index=index,action=self.prefix[index].tolist()))
            cp=d.Study.checkpoint(self,state)
            if d.canonical(cp)!=self.verified['checkpoint']:raise RuntimeError('581_FULL_CHECKPOINT_IDENTITY')
            self.result['prefix']=dict(raw=132,all_full_rows_and_checkpoint_exact=True,checkpoint_sha256=digest(cp));atomic_write(D/'prefix-checkpoint-private.json',cp)
            self.switch('intervention');self.mode='actual';phase=Phase(self,'intervention')
            for index in range(34,46):
                self.reserve(184,168,20,27);self.law_calls+=1;before=dict(pure=COUNTS.copy(),checkpoint=digest(d.Study.checkpoint(self,state)));nominal=policy.nominal(state['root'],self.paths['candidate'],state['progress'])
                self.journal.append('BEFORE_LAW',index=index,checkpoint=d.Study.checkpoint(self,state),nominal_action=nominal.tolist(),pure_before=dict(COUNTS))
                try:action,detail=select(d.short(state['root']),nominal)
                except LawStop as exc:
                    if str(exc) in ['EMPTY_CURRENT_FRONT_CONE','NO_REPRESENTABLE_TARGET']:status='LAW_TARGET_EMPTY';failure=dict(index=index,reason=str(exc));break
                    raise
                if sum((COUNTS-before['pure'])[k] for k in ['pure_wheel_formula','pure_cone_coefficients'])>168:raise RuntimeError('PURE_WORK_BOUND')
                if digest(d.Study.checkpoint(self,state))!=before['checkpoint']:raise RuntimeError('LAW_MUTATED_ACTUAL_STATE')
                self.guard();self.journal.append('LAW_COMMAND',index=index,action=action.tolist(),detail=detail,pure_after=dict(COUNTS));self.commands.append(dict(index=index,action=action.tolist()))
                rr,reason=self.hold(state,action,index,phase);self.rows+=rr;self.result['holds'].append(hold_summary(index,rr,detail));atomic_write(D/f'hold{index}-private.json',dict(rows=rr,detail=detail,checkpoint=d.Study.checkpoint(self,state),reason=reason,cost=self.cost()))
                if reason:status='ACTUAL_SAFETY_FAILURE';failure=dict(index=index,raw=rr[-1]['raw'],attempted_global_raw=rr[-1]['global_raw_before']+1,reason=reason);break
            if status is None:
                status='LOCAL48_SAFE';self.reserve(180,0,20,27);self.switch('verification');self.mode='replay';phase=Phase(self,'verification');again=d.Study.initial(self);immutable(again['root']);actual=[]
                for command in self.commands:
                    rr,reason=self.hold(again,np.asarray(command['action'],np.float32),command['index'],phase);actual+=rr
                    if reason:raise RuntimeError('INDEPENDENT_REPLAY_SAFETY:'+reason)
                if len(actual)!=180 or d.canonical(actual)!=d.canonical(self.rows) or d.canonical(d.Study.checkpoint(self,again))!=d.canonical(d.Study.checkpoint(self,state)):raise RuntimeError('INDEPENDENT_REPLAY_IDENTITY')
                replay=dict(raw=180,all_full_rows_exact=True,full_checkpoint_contents_exact=True,law_reselection=False);atomic_write(D/'verified-tape-private.json',dict(rows=actual,commands=self.commands,checkpoint=d.Study.checkpoint(self,again)));status='LOCAL48_VIABLE_EXACT_REPLAY'
        except BaseException as exc:
            status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE';error=type(exc).__name__+':'+str(exc);atomic_write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost()),True)
        finally:
            atomic_write(G/'retry/cone584_cost.json',self.cost(),True);b.wheel.wheel_response=self.orig_external;b.planar.wheel_response=self.orig_internal
            if state is not None:atomic_write(D/'run-tape-private.json',dict(rows=self.rows,commands=self.commands,checkpoint=d.Study.checkpoint(self,state),status=status),True)
            try:self.switch('audit');self.mode='audit';self.journal.close();audit=inspect(D/'raw-journal-private.jsonl');self.validate_closure();self.guard()
            except BaseException as exc:status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE';error=(error or '')+';AUDIT:'+str(exc);audit=dict(valid=False,error=str(exc))
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            self.result.update(status=status,error=error,failure=failure,law_calls=self.law_calls,independent_replay=replay,journal=audit,cost=self.cost(),actual_incumbent_s=13.66,source_incumbent_s=13.20,incumbent_changed=False,native_actions=0,whole_executed=False,HOLDOUT=0,SEALED=0,new_FD=0,new_optimizer=0,new_learning=0,new_world=0,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0)
            atomic_write(G/'retry/cone584_cost.json',self.cost(),True);atomic_write(G/'retry/cone584_result.json',self.result);print(json.dumps(plain(self.result),indent=2))

def pose(z):
    p=z['planar'];return dict(COM_speed_m_s=math.hypot(*p['linear']['velocity']),yaw_rad_s=p['yaw'],front_joints_rad=p['joints'][:2],front_rates_rad_s=p['rates'][:2])
def hold_summary(index,rows,detail):
    safe=[r for r in rows if not r['pre_failure'] and not r.get('post_failure')];complete=[r for r in rows if 'root_without_roads' in r];forces=[f for r in rows for f in r['forces']];last=rows[-1];peak=max(range(4),key=lambda j:last['forces'][j]['ratio'])
    return dict(hold=index,attempted_raw=len(rows),completed_raw=len(complete),strict_safe_raw=len(safe),safe=len(safe)==4,failure=last['pre_failure'] or last.get('post_failure'),start=pose(rows[0]['before_root_without_roads']),end=pose(complete[-1]['root_without_roads']) if complete else None,last_strict_safe_progress_m=safe[-1]['progress'] if safe else None,progress_end_m=complete[-1]['progress'] if complete else None,minimum_footprint_margin_m=min((r['margin'] for r in complete),default=None),maximum_path_error_m=max((r['path_error'] for r in complete),default=None),maximum_reference_overspeed_m_s=max((r['reference_overspeed'] for r in complete),default=None),maximum_body_m_s=max((r['body'] for r in complete),default=None),maximum_force_ratio=max(f['ratio'] for f in forces),maximum_front_force_ratio=max(f['ratio'] for r in rows for f in r['forces'][:2]),maximum_rear_force_ratio=max(f['ratio'] for r in rows for f in r['forces'][2:]),maximum_applied_vector_norm_N=max(math.hypot(*f['vector']) for f in forces),proposed_clipped_samples=sum(f['clipped'] for f in forces),tracking_before=rows[0]['tracking_history_before'],tracking_proposed=last['proposed_history'],peak_last_wheel=peak,peak_last_ratio=last['forces'][peak]['ratio'],path_target_joint_rad=detail['path_joint_target_rad'],selected_target_joint_rad=detail['selected_joint_target_rad'],proxy_virtual_target_max_ratio=max(detail['virtual_target_force_ratios']))

if __name__=='__main__':
    if '--register' in sys.argv:register()
    else:
        study=None
        try:study=object.__new__(Study);study.__init__();study.run()
        except BaseException as exc:
            out=dict(status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE',error=type(exc).__name__+':'+str(exc),source_execution_started=bool(study and getattr(study,'counts',{}).get('attempted_raw',0)),counts=dict(getattr(study,'counts',{})),CPU_s=time.process_time()-START_CPU+getattr(study,'prior',{}).get('CPU_s',0),wall_s=time.perf_counter()-START_WALL+getattr(study,'prior',{}).get('wall_s',0))
            if D.exists():atomic_write(D/'outer-failure-private.json',dict(out,traceback=traceback.format_exc()),True)
            atomic_write(G/'retry/cone584_outer_failure.json',out);raise
