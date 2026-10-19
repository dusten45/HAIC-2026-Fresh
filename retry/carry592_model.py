"""One finite577 carry source evaluation and conditional exact replay; native0."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import copy,datetime,hashlib,importlib.util,json,math,signal,subprocess,sys,traceback,unittest
from collections import Counter
from dataclasses import asdict
from pathlib import Path
import numpy as np
import retry.late568_model as base
import retry.handoff562_model as d
import retry.brake502_response as wheel
import retry.brake504_planar as planar
from retry.durable568 import Journal,digest,evaluate_force,inspect
from retry.clip561_core import atomic_write
from core.vendor.car_racing import CarRacing
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response592-private');C=G/'retry/carry592_contract.json'
INPUTS=dict(tape=Path('/workspace/haic-response577-private/final-independent-tape-private.json'),static=Path('/workspace/haic-response515-private/collected-map-state-private.json'),paths=Path('/workspace/haic-response551-private/frozen-paths-private.json'),ledger=Path('/workspace/haic-response519-private/model-ledger-private.json'),handoff=Path('/workspace/haic-response518-private/action-100-047.json'),previous=Path('/workspace/haic-response518-private/action-100-046.json'),lastactual=Path('/workspace/haic-response518-private/raw-1384.json'),oldclose=Path('/workspace/haic-response518-private/close-80-private.json'),coldresult=G/'retry/direct577_result.json',coldanalysis=G/'retry/direct577_analysis.json',coldcontract=G/'retry/direct577_contract.json',coldjournal=Path('/workspace/haic-response577-private/raw-journal-private.jsonl'),coldregistration=Path('/workspace/haic-response577-private/STARTED.json'),proposal=G/'retry/validation591_proposed_contract.json',evidence=G/'retry/validation591_evidence.json')
for j in range(1,185):INPUTS[f'legacyraw{j}']=Path('/workspace/haic-response518-private')/f'raw-{1200+j:04d}.json'
class BudgetStop(RuntimeError):pass
class SourceDomain(RuntimeError):pass
class HandoffGate(RuntimeError):pass

def action_at(commands,index):
    if not 47<=index<=166:raise ValueError('FINITE_CARRY_TAPE_DOMAIN')
    return np.asarray(commands[index],np.float32)
def clone(state):
    return dict(root=state['root'],visited=set(state['visited']),tracker=d.FinishLineTracker(**asdict(state['tracker'])),elapsed=state['elapsed'],global_raw=state['global_raw'],progress=state['progress'],launch=state['launch'].copy(),tracking=state['tracking'].copy())
def replay_allowed(safe,finish):return safe and finish is not None and finish<=14.46

class Phase:
    def __init__(self,s,name):self.s=s;self.name=name;self.counter=[0];self.cost=dict(force_evaluations=0);self.pending=None;self.counts=Counter()
    def add(self,key,n=1):self.s.counts[key]+=n;self.counts[key]+=n
    def evaluate(self,root,action,history,context,peak,clip,check_clip):
        self.s.guard();self.s.reserve_raw();self.add('attempted_raw');self.s.journal.append('RAW_ATTEMPT',phase=self.name,context=context)
        verdict=evaluate_force(self.s.journal,d.short(root),action.tolist(),history,dict(phase=self.name,**context),lambda:d.force_rows(root,action),peak,clip,check_clip)
        self.pending=dict(verdict,root_id=digest(d.short(root)),action=action.tolist(),context=context);return verdict
    def tick(self,root,gas,brake,index,counter):
        self.s.guard();p=self.pending
        if counter is not self.counter or p is None or p['root_id']!=digest(d.short(root)) or [gas,brake]!=p['action'][1:]:raise RuntimeError('EXACT_PENDING_TICK')
        self.add('tick_attempts');self.s.journal.append('BEFORE_TICK',force_event=p['event'],phase=self.name,context=p['context']);after=d.source_tick(root,gas,brake,index,counter);self.add('completed_ticks');self.pending=None;v=base.body(after);self.s.journal.append('AFTER_TICK',root=d.short(after),body=v,phase=self.name)
        if not math.isfinite(v):raise RuntimeError('NONFINITE_BODY')
        if v>=100:raise SourceDomain('BODY_GE100')
        return after
    def geometry(self,root):
        self.s.guard();tail=481 if self.name=='carry' else 0
        if self.s.counts['geometry']+1+tail>962:raise BudgetStop('GEOMETRY_REPLAY_RESERVE')
        self.add('geometry');self.s.journal.append('BEFORE_GEOMETRY',root=d.short(root),phase=self.name);v=d.margin(root,self.s.static['roads'],self.s.index,self.s.static['boundary'],self.s.edge,self.s.static['obstacles']);self.s.journal.append('GEOMETRY_VERDICT',margin=v,phase=self.name);return v

class Study:
    def __init__(self):
        self.counts=Counter();self.phase=None;self.sourceCPU=self.sourceWall=0.;self.result={};self.current=None;self.prior=10.;self.journal=None;self.stage='preparation';D.mkdir(mode=0o700,exist_ok=False)
        self.register();self.journal=Journal(D/'raw-journal-private.jsonl')
    def times(self):
        active=self.stage in ['carry','replay'];sCPU=self.sourceCPU+(time.process_time()-self.pc if active else 0);sWall=self.sourceWall+(time.perf_counter()-self.pw if active else 0);totalCPU=time.process_time()-CPU+self.prior;totalWall=time.perf_counter()-WALL+self.prior
        return dict(source_CPU_s=sCPU,source_wall_s=sWall,preparation_audit_CPU_s=totalCPU-sCPU,preparation_audit_wall_s=totalWall-sWall,total_CPU_s=totalCPU,total_wall_s=totalWall)
    def guard(self):
        t=self.times()
        for key,cap in dict(source_CPU_s=60,source_wall_s=90,preparation_audit_CPU_s=60,preparation_audit_wall_s=90,total_CPU_s=120,total_wall_s=180).items():
            if t[key]>=cap:raise BudgetStop(key)
        if self.stage!='audit' and (t['preparation_audit_CPU_s']>=55 or t['preparation_audit_wall_s']>=80):raise BudgetStop('AUDIT_RESERVE')
        if self.stage in ['carry','replay'] and (time.process_time()-self.pc>=30 or time.perf_counter()-self.pw>=45):raise BudgetStop('CASE_TIME_CAP')
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime(2026,10,20,10,1,55,tzinfo=datetime.timezone.utc):raise BudgetStop('DEADLINE')
    def reserve_raw(self):
        tail=480 if self.stage=='carry' else 0
        for key,cap,per in [('attempted_raw',960,1),('completed_ticks',960,1),('external_force',3840,4),('internal_force',3840,4)]:
            if self.counts[key]+per+tail*per>cap:raise BudgetStop(key+'_REPLAY_RESERVE')
        if self.phase.counts['attempted_raw']>=480:raise BudgetStop('CASE_RAW_CAP')
    def wheel(self,key,fn,*a,**kw):
        self.guard()
        if self.counts[key]>=3840:raise BudgetStop(key+'_CALL_CAP')
        self.phase.add(key);return fn(*a,**kw)
    def register(self):
        local={str(Path(x.__file__).resolve().relative_to(G)):d.sha(Path(x.__file__).resolve()) for x in tuple(sys.modules.values()) if getattr(x,'__file__',None) and Path(x.__file__).is_file() and Path(x.__file__).resolve().is_relative_to(G) and '.venv' not in Path(x.__file__).parts};local.update({f:d.sha(G/f) for f in ['retry/carry592_model.py','tests/test_carry592.py']});deps={str(Path(x.__file__).resolve()):d.sha(Path(x.__file__).resolve()) for x in tuple(sys.modules.values()) if getattr(x,'__file__',None) and Path(x.__file__).is_file() and ('.venv' in Path(x.__file__).parts or not Path(x.__file__).resolve().is_relative_to(G))}
        c=dict(study=592,status='FROZEN_BEFORE_TESTS_HANDOFF_SOURCE',parent_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=G,text=True).strip(),registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc='2026-10-20T10:01:55Z',input_sha256={k:d.sha(p) for k,p in INPUTS.items()},implementation_sha256=local,dependency_sha256=deps,caps=dict(attempted_raw=960,completed_ticks=960,external_force=3840,internal_force=3840,total_force=7680,geometry=962,source_CPU_s=60,source_wall_s=90,preparation_audit_CPU_s=60,preparation_audit_wall_s=90,total_CPU_s=120,total_wall_s=180,per_case_CPU_s=30,per_case_wall_s=45,per_case_raw=480),spec='Reusecoldfull661raw166commandsCPandjournalpinsread-only.No coldsource. Actuallegacybefore47root/visited/tracker/clock/tracking0,352;globalraw184. Deriveelapsed=actualclock-1.02,neverroundto3.68. Freezeprivatecompletehandoff beforephysics. tape47..166only;noreindex/progressalignment/feedback/167. Original late568 rawstrictsource1.059/clip.10/footprint.50/path3/reference4.85/body<100/projection/tracker/visited unchanged. Countcurrentrootgeometryandposttick. Initialcurrentrootsafetychecked.480rawcarryonce;onlysafeofficialfinish episode<=14.46=>oneindependentcloneexactreplay480. No500msgate. Firstfailure/exhaustion/domain/integrity/IO/coststop,neverrepair. Sourcecold13.20remainsvalidifcarryfails,butcombinedpromotionclosed. Nativeactionsresetworld0.',reservation='Candidate maximum480raw+481geometry+30CPU45wall reserved forreplay, prep/auditremaining60CPU90wall separately. Individualcase30CPU45wall. 10CPU/wallpreparationcharge includesearlierinspection;import/tests/register/pins/journalaudit measured. Cleanup/audit reserve5CPU10wall,totalhard120/180. Exclusiveprivate directory/STARTED/fsyncedhashchain;no rerun.',research_remaining=22758,reserve=84000,reserve_used=0)
        atomic_write(C,c);self.contract=c;atomic_write(D/'REGISTERED-private.json',dict(contract_sha256=d.sha(C)))
    def pins(self):
        for k,h in self.contract['input_sha256'].items():assert d.sha(INPUTS[k])==h,('INPUT',k)
        for p,h in {**self.contract['implementation_sha256'],**self.contract['dependency_sha256']}.items():assert d.sha(Path(p) if Path(p).is_absolute() else G/p)==h,('CODE',p)
    def prepare(self):
        self.guard();self.pins();spec=importlib.util.spec_from_file_location('test_carry592',G/'tests/test_carry592.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);r=unittest.TestResult();unittest.defaultTestLoader.loadTestsFromModule(m).run(r);self.result['pure_tests']=dict(count=r.testsRun,passed=r.wasSuccessful());assert r.wasSuccessful(),(r.errors,r.failures)
        tape=d.rd(INPUTS['tape']);cold=d.rd(INPUTS['coldresult']);analysis=d.rd(INPUTS['coldanalysis']);oldc=d.rd(INPUTS['coldcontract']);checks=dict(tape_pin=d.sha(INPUTS['tape'])=='bc432812cdd71702ec030edda72a9aa63ca79e61dceb1f970891a659f20cd5a6',rows=len(tape['rows'])==661,commands=len(tape['commands'])==166,exact=tape['exact'] and tape['checkpoint_exact'],fullCP=set(tape['checkpoint'])=={'root_without_roads','visited','tracker','elapsed','global_raw','progress','launch','tracking'},storedsafe=all(not q['pre_failure'] and not q['post_failure'] and not q['all_failures'] for q in tape['rows']),old_audit=analysis['passed'],old_source_pins=all(d.sha(G/p)==h for p,h in oldc['source_sha256'].items()),old_input_pins=all(d.sha(Path(p))==h for p,h in oldc['input_sha256'].items()),journal_registered=d.rd(INPUTS['coldregistration'])['contract_sha256']==d.sha(INPUTS['coldcontract']))
        coldvisited=set(d.rd(INPUTS['ledger'])['initial_visited'])
        for row in tape['rows']:
            for ids in row['root_without_roads']['current_contacts']:coldvisited.update(ids)
        last=tape['rows'][-1];expectedCP=dict(root_without_roads=last['root_without_roads'],visited=sorted(coldvisited),tracker=last['tracker'],elapsed=last['episode_after_s'],global_raw=last['global_raw_after'],progress=last['progress'],launch=last['launch_history_before'],tracking=last['proposed_history']);checks['fullCP_from_stored_rows_exact']=expectedCP==tape['checkpoint'];checks['command_rows_identity']=all(row['action']==tape['commands'][row['index']-1]['action'] for row in tape['rows'])
        chain=inspect(INPUTS['coldjournal']);checks['journal_exact']=chain==cold['journal'];assert all(checks.values()),checks;self.result['cold_read_only']=dict(checks=checks,journal=chain,new_cold_ticks=0)
        self.static=d.rd(INPUTS['static']);self.paths=d.rd(INPUTS['paths']);ledger=d.rd(INPUTS['ledger']);cp=d.rd(INPUTS['handoff']);previous=d.rd(INPUTS['previous']);actual=d.rd(INPUTS['lastactual']);self.commands={q['index']:np.asarray(q['action'],np.float32) for q in tape['commands']};assert sorted(self.commands)==list(range(1,167))
        legacy=[d.rd(INPUTS[f'legacyraw{i}']) for i in range(1,185)];visited=set(ledger['initial_visited']);history=[0,0];launch=[0,0]
        for i,row in enumerate(legacy):
            if row['phase']!='action' or row['action']!=i//4+1 or row['errors']:raise HandoffGate('LEGACY_RAW_ORDER_OR_SAFETY')
            for ids in row['after_contacts']:visited.update(ids)
            group=launch if i<96 else history;group[0]+=sum(f['ratio']>1 for f in row['forces']);group[1]+=4
        handoffchecks=dict(actual_raw_pin=d.sha(INPUTS['lastactual'])==d.rd(INPUTS['proposal'])['carry_start']['last_actual_raw_record_sha256'],root_exact=cp['before_root_without_roads']==previous['after_root_without_roads'],raw_last=legacy[-1]==actual and actual['action']==46,completed=ledger['completed_actions']==46,tracking=history==[0,352],visited=visited==set(ledger['carry_visited']) and len(visited)==actual['visited_tiles']==43,tracker_live_unfinished=actual['official_tracker']['finish_time_s'] is None and actual['official_tracker']['qualified_time_s'] is None,clock=abs(actual['time']-(1.02+184*.02))<1e-10,checkpoint_pin=d.sha(INPUTS['handoff'])=='f214ec85a254121a332a5c4347b61efda6fb00cdbbed2bd9a716038dcca701b0')
        if not all(handoffchecks.values()):raise HandoffGate(str(handoffchecks))
        root=d.load_root(dict(cp['before_root_without_roads'],roads=self.static['root']['roads']));self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);progress=d.project(root.center,self.paths['candidate'],ledger['anchor'])['s'];self.start=dict(root=root,visited=visited,tracker=d.FinishLineTracker(**actual['official_tracker']),elapsed=actual['time']-1.02,global_raw=184,progress=progress,launch=launch,tracking=history);assert 1.02+self.start['elapsed']==actual['time'];atomic_write(D/'frozen-handoff-private.json',base.checkpoint(self.start));self.handoff_sha=d.sha(D/'frozen-handoff-private.json');self.result['handoff']=dict(checks=handoffchecks,checkpoint_sha256=self.handoff_sha,global_raw=184,next_hold=47,tracking=history,launch=launch,visited_count=len(visited),clock_s=actual['time'],elapsed_s=self.start['elapsed'],tracker='Actualstoredlegacy518raw1384allfields;not541tracker_for reconstructeddeparture');self.pins();self.guard()
        atomic_write(D/'SOURCE_FROZEN-private.json',dict(contract_sha256=d.sha(C),handoff_sha256=self.handoff_sha))
    def summary(self,rows,state,reason):
        post=[q for q in rows if 'margin' in q];finish=state['tracker'].finish_time_s;episode=finish-1.02 if finish is not None else None;safe=reason is None and finish is not None
        return dict(safe_official_finish=safe,finish_episode_s=episode,eligible=replay_allowed(safe,episode),reason=reason,attempt_rows=len(rows),completed_rows=len(post),global_raw=state['global_raw'],elapsed_s=state['elapsed'],tracking=state['tracking'],visited_count=len(state['visited']),minimum_margin_m=min((q['margin'] for q in post),default=None),maximum_force_ratio=max((f['ratio'] for q in rows for f in q['forces']),default=None),maximum_path_error_m=max((q['path_error'] for q in post),default=None),maximum_reference_excess_m_s=max((q['reference_overspeed'] for q in post),default=None),maximum_body_speed_m_s=max((q['body'] for q in post),default=None),first_failure_global_raw=rows[-1]['global_raw_before']+1 if rows and (rows[-1].get('pre_failure') or rows[-1].get('post_failure')) else None)
    def case(self,name,expected=None):
        self.stage=name;self.pc=time.process_time();self.pw=time.perf_counter();self.phase=Phase(self,name);state=clone(self.start);rows=[];used=[];reason='TAPE_EXHAUSTED';self.journal.append('CASE_STARTED',phase=name,handoff_sha256=self.handoff_sha)
        try:
            gap=self.phase.geometry(state['root']);q=d.project(state['root'].center,self.paths['candidate'],state['progress']);over=math.hypot(*state['root'].planar.linear.velocity)-d.reference(q['s'],self.paths['candidate'])[0];body=base.body(state['root']);self.result.setdefault('initial_root',dict(margin_m=gap,path_error_m=q['distance'],reference_excess_m_s=over,body_speed_m_s=body))
            if not math.isfinite(body):raise RuntimeError('NONFINITE_INITIAL_BODY')
            if body>=100:raise SourceDomain('INITIAL_BODY_GE100')
            if gap<.5 or q['distance']>3 or over>4.85:reason='INITIAL_STRICT_STATE_FAILURE';return rows,state,reason
            for h in range(47,167):
                action=action_at(self.commands,h);used.append(dict(index=h,action=action.tolist()))
                for k in range(1,5):
                    self.current=dict(phase=name,index=h,raw=k);row,why=base.Study.raw(self,state,action,h,k,self.phase);rows.append(row)
                    if expected is not None and (len(rows)>len(expected) or d.canonical(row)!=d.canonical(expected[len(rows)-1])):raise RuntimeError('REPLAY_ROW_MISMATCH')
                    if why:reason=why;return rows,state,reason
                    if state['tracker'].finish_time_s is not None:reason=None;return rows,state,reason
                    self.guard()
            return rows,state,reason
        except BaseException as exc:reason=type(exc).__name__+':'+str(exc);raise
        finally:
            self.sourceCPU+=time.process_time()-self.pc;self.sourceWall+=time.perf_counter()-self.pw;self.stage='audit';self.result[name]=self.summary(rows,state,reason);self.result[name]['counts']=dict(self.phase.counts);atomic_write(D/(name+'-private.json'),dict(rows=rows,commands=used,checkpoint=base.checkpoint(state),reason=reason,cost=dict(self.counts)));self.journal.append('CASE_FINISHED',phase=name,counts=dict(self.phase.counts));self.guard()
    def run(self):
        status='TECHNICAL_FAILURE';error=None;oe=wheel.wheel_response;oi=planar.wheel_response
        def forbidden(*a,**kw):raise RuntimeError('NATIVE_FORBIDDEN_592')
        CarRacing.__init__=CarRacing.reset=CarRacing.step=forbidden
        signal.signal(signal.SIGPROF,lambda *a:(_ for _ in ()).throw(BudgetStop('TOTAL_CPU_TIMER')));signal.signal(signal.SIGALRM,lambda *a:(_ for _ in ()).throw(BudgetStop('TOTAL_WALL_TIMER')));signal.setitimer(signal.ITIMER_PROF,max(.01,118-self.times()['total_CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,178-self.times()['total_wall_s']))
        try:
            self.prepare();wheel.wheel_response=lambda *a,**kw:self.wheel('external_force',oe,*a,**kw);planar.wheel_response=lambda *a,**kw:self.wheel('internal_force',oi,*a,**kw);self.guard()
            rows,state,reason=self.case('carry');carry=self.result['carry'];status='SOURCE_CARRY_FAILED'
            if carry['eligible']:
                if self.sourceCPU+30>60 or self.sourceWall+45>90:raise BudgetStop('REPLAY_TIME_RESERVE')
                replay,again,rwhy=self.case('replay',rows);exact=rwhy is None and len(replay)==len(rows) and d.canonical(base.checkpoint(state))==d.canonical(base.checkpoint(again));self.result['replay_exact']=exact
                if not exact:raise RuntimeError('REPLAY_CHECKPOINT_MISMATCH')
                status='SOURCE_CARRY_SAFE_EXACT_PASS'
            if d.sha(D/'frozen-handoff-private.json')!=self.handoff_sha or d.canonical(base.checkpoint(self.start))!=d.rd(D/'frozen-handoff-private.json'):raise RuntimeError('HANDOFF_MUTATED')
        except BaseException as exc:
            error=type(exc).__name__+':'+str(exc);status='BUDGET_CENSORED' if isinstance(exc,BudgetStop) else 'SOURCE_DOMAIN_STOP' if isinstance(exc,SourceDomain) else 'HANDOFF_GATE_FAILED_SOURCE0' if isinstance(exc,HandoffGate) else 'TECHNICAL_FAILURE';atomic_write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),current=self.current,cost=dict(self.counts)))
        finally:
            wheel.wheel_response=oe;planar.wheel_response=oi;self.stage='audit';self.journal.close()
            try:
                audit=inspect(D/'raw-journal-private.jsonl');self.pins();self.guard()
                if status not in ['TECHNICAL_FAILURE','BUDGET_CENSORED','SOURCE_DOMAIN_STOP']:
                    assert self.counts['external_force']==4*self.counts['attempted_raw'] and self.counts['internal_force']==4*self.counts['completed_ticks'];assert audit['kinds'].get('BEFORE_TICK',0)==audit['kinds'].get('AFTER_TICK',0)==self.counts['completed_ticks'];assert audit['kinds'].get('BEFORE_GEOMETRY',0)==audit['kinds'].get('GEOMETRY_VERDICT',0)==self.counts['geometry']
            except BaseException as exc:audit=dict(valid=False,error=str(exc));status='BUDGET_CENSORED' if isinstance(exc,BudgetStop) else 'TECHNICAL_FAILURE';error=(error or '')+';AUDIT:'+str(exc)
            self.result.update(study=592,status=status,error=error,cost=dict(self.counts),time=self.times(),journal=audit,new_cold_ticks=0,new_FD=0,new_profiles=0,new_feedback=0,native_actions=0,native_resets=0,native_worlds=0,HOLDOUT=0,SEALED=0,paid_compute=0,research_remaining=22758,reserve=84000,reserve_used=0,source_cold_incumbent_s=13.20,actual_cold_incumbent_s=13.66,incumbents_changed=False,combined_source_gate=status=='SOURCE_CARRY_SAFE_EXACT_PASS',native_promotion=False)
            atomic_write(G/'retry/carry592_result.json',self.result);signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0);print(json.dumps(self.result,indent=2))
if __name__=='__main__':Study().run()
