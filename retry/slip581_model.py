"""One two-hold source-only mechanical steering pilot; no search or restart."""
import time
START_CPU=time.process_time();START_WALL=time.perf_counter()
import sys,math,json,copy,datetime,signal,traceback
from pathlib import Path
from collections import Counter
import numpy as np
from retry.clip561_core import atomic_write,plain
from retry.durable568 import Journal,digest,inspect
import retry.beam579_model as b
from retry.beam579_math import immutable
from retry.slip581_math import alignment,diagnostic,branch_equal

d=b.d;G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response581-private');CONTRACT=G/'retry/slip581_contract.json'
INPUTS={**b.INPUTS,'prefix':Path('/workspace/haic-response580-private/selected-prefix-private.json'),'proposal':G/'retry/forensic580_next_contract.json','analysis580':G/'retry/forensic580_analysis.json'}


def register():
    c=d.rd(INPUTS['proposal']);tests=d.rd(G/'retry/slip581_tests.json');assert tests['passed']
    c.update(study=581,status='FROZEN_BEFORE_SOURCE',registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),parent_commit='5b91de254c3e8cd2ec4daddd242335bba8bff18e',proposal_sha256=d.sha(INPUTS['proposal']),input_sha256={k:d.sha(p) for k,p in INPUTS.items()},dependency_file_sha256=b.manifest(),implementation_sha256={str(p.relative_to(G)):d.sha(p) for p in [Path(__file__),G/'retry/slip581_math.py',G/'tests/test_slip581.py']},tests=tests,preparation_prior_charge={'CPU_s':tests['CPU_s']+1.,'wall_s':tests['wall_s']+1.,'meaning':'Measured source0tests plus conservative1s registration/hash/write charge; actual runtime imports/preparation also counted.'})
    c['budget_reservation']='Beforeprefixreserve124+8+132ticksandprefix5/intervention2/verification6/audit3CPU,8/3/8/5wall; beforeintervention reserve remaining intervention plus132replay+audit. No probe/selector/baseline sweep.'
    atomic_write(CONTRACT,c);print(json.dumps({'registered':True,'dependency_files':len(c['dependency_file_sha256']),'source_ticks':0}))


class Study:
    raw=b.base.Study.raw
    count=b.Study.count;phase_times=b.Study.phase_times;cost=b.Study.cost;switch=b.Study.switch;wheel_call=b.Study.wheel_call
    def __init__(self):
        self.contract=d.rd(CONTRACT);self.prior=self.contract['preparation_prior_charge'];self.bucket='preparation';self.stage_start_cpu=START_CPU;self.stage_start_wall=START_WALL;self.phases={'preparation':dict(self.prior)};self.phases['preparation'].pop('meaning');self.counts=Counter();self.stage_counts={};self.result={'holds':[]};self.rows=[];self.intervention_actions=[];self.last_state=None;self.journal=None
        D.mkdir(mode=0o700,exist_ok=False);self.journal=Journal(D/'raw-journal-private.jsonl');self.guard()
        for k,h in self.contract['input_sha256'].items():
            if d.sha(INPUTS[k])!=h:raise RuntimeError('INPUT_HASH:'+k)
        self.validate_closure()
        for f,h in self.contract['implementation_sha256'].items():
            if d.sha(G/f)!=h:raise RuntimeError('IMPLEMENTATION_HASH:'+f)
        self.tape,self.static,self.paths,self.ledger,self.prefix=[d.rd(INPUTS[k]) for k in ['tape','static','paths','ledger','prefix']]
        if digest(self.ledger['initial_visited'])!=self.contract['initial_visited_sha256']:raise RuntimeError('INITIAL_VISITED_HASH')
        self.commands={r['index']:np.asarray(r['action'],np.float32) for r in self.tape['commands']};self.prefix_commands={r['index']:np.asarray(r['action'],np.float32) for r in self.prefix['commands']};self.index=d.bounds(self.static['root']['roads']);self.edge=d.boundary_index(self.static['boundary']);self.orig_external=b.wheel.wheel_response;self.orig_internal=b.planar.wheel_response
        assert sorted(self.prefix_commands)==list(range(1,32)) and len(self.prefix['branch_expected_rows'])==28
        atomic_write(D/'STARTED.json',dict(contract_sha256=d.sha(CONTRACT),source_ticks=0,input_sha256=self.contract['input_sha256']))
    def validate_closure(self):
        for f,h in self.contract['dependency_file_sha256'].items():
            if d.sha(G/f if not Path(f).is_absolute() else Path(f))!=h:raise RuntimeError('DEPENDENCY_HASH:'+f)
        if any(f not in self.contract['dependency_file_sha256'] for f in b.manifest()):raise RuntimeError('UNMANIFESTED_IMPORT')
    def elapsed(self):return dict(CPU_s=time.process_time()-START_CPU+self.prior['CPU_s'],wall_s=time.perf_counter()-START_WALL+self.prior['wall_s'])
    def guard(self,attempts=0,external=0,internal=0):
        limits=self.contract['budgets']['caps'];c=self.counts
        for key,extra in [('attempted_raw',attempts),('completed_model_ticks',0),('external_force',external),('internal_force',internal),('geometry_checks',0)]:
            if c[key]+extra>limits[key]:raise b.BudgetStop('AGGREGATE_'+key)
        if c['external_force']+c['internal_force']+external+internal>limits['total_force']:raise b.BudgetStop('AGGREGATE_total_force')
        phase=self.phase_times()[self.bucket];specific=self.contract['budgets']['stage_caps'][self.bucket]
        for key,value in self.elapsed().items():
            if value>=limits[key] or phase[key]>=specific[key]:raise b.BudgetStop('TIME_'+self.bucket+'_'+key)
        if 'attempted_raw' in specific and self.stage_counts.get(self.bucket,{}).get('attempted_raw',0)+attempts>specific['attempted_raw']:raise b.BudgetStop('PHASE_ATTEMPTS_'+self.bucket)
        if datetime.datetime.now(datetime.timezone.utc)>=datetime.datetime.fromisoformat(self.contract['deadline_utc'].replace('Z','+00:00')):raise b.BudgetStop('DEADLINE')
    def reserve(self,raw,cpu,wall):
        self.guard()
        if self.counts['attempted_raw']+raw>300 or self.counts['external_force']+4*raw>1200 or self.counts['internal_force']+4*raw>1200 or self.counts['external_force']+self.counts['internal_force']+8*raw>2400:raise b.BudgetStop('RESERVE_WORK')
        if self.counts['completed_model_ticks']+raw>300 or self.counts['geometry_checks']+raw>300:raise b.BudgetStop('RESERVE_TICKS_GEOMETRY')
        e=self.elapsed()
        if e['CPU_s']+cpu>25 or e['wall_s']+wall>35:raise b.BudgetStop('RESERVE_TIME')
    def summarize_row(self,row):
        before=diagnostic(row['before_root_without_roads']);after=diagnostic(row['root_without_roads']) if 'root_without_roads' in row else None;forces=row['forces'];peak=max(range(4),key=lambda j:forces[j]['ratio'])
        return dict(hold=row['index'],raw_in_hold=row['raw'],attempted_global_raw=row['global_raw_before']+1,completed_global_raw=row.get('global_raw_after'),maximum_force_ratio=forces[peak]['ratio'],peak_wheel=peak,maximum_computed_clipped_force_vector_norm_N=max(math.hypot(*f['vector']) for f in forces),before=before,after=after,progress_after_m=row.get('progress'),footprint_margin_after_m=row.get('margin'),path_error_after_m=row.get('path_error'),reference_overspeed_after_m_s=row.get('reference_overspeed'),tracking_history_before=row['tracking_history_before'],tracking_history_proposed=row['proposed_history'],failure=row.get('pre_failure') or row.get('post_failure'),integrated='root_without_roads' in row)
    def hold(self,state,action,index,phase,verify_prefix=False,diagnostics=False):
        assert index==state['global_raw']//4+1
        summary={'hold':index,'safe':False,'rows':[],'start_progress_m':state['progress'],'start':diagnostic(d.short(state['root'])),'tracking_before':state['tracking'].copy(),'launch_before':state['launch'].copy()};rows=[]
        if diagnostics:self.result['holds'].append(summary)
        for k in range(1,5):
            last_safe_raw,last_safe_progress=state['global_raw'],state['progress']
            row,reason=self.raw(state,action,index,k,phase);rows.append(row)
            if diagnostics:summary['rows'].append(self.summarize_row(row))
            self.guard()
            if verify_prefix:
                if reason:raise RuntimeError('PREFIX_SAFETY_MISMATCH:'+reason)
                gr=row['global_raw_before']
                if gr<96:
                    if not all(d.canonical(row.get(key))==d.canonical(self.tape['rows'][gr].get(key)) for key in b.KEYS):raise RuntimeError('PREFIX_LAUNCH_IDENTITY')
                elif not branch_equal(row,self.prefix['branch_expected_rows'][gr-96],self.tape['rows'][gr]) or row['launch_history_before']!=self.tape['rows'][95]['proposed_history']:raise RuntimeError('PREFIX_BRANCH_IDENTITY')
            if reason:
                summary.update(failure=reason,last_safe_global_raw=last_safe_raw,last_safe_progress_m=last_safe_progress,failed_after_global_raw=row.get('global_raw_after'),end=diagnostic(d.short(state['root'])),tracking_after=state['tracking'].copy());return rows,reason
        summary.update(safe=True,failure=None,end=diagnostic(d.short(state['root'])),end_progress_m=state['progress'],tracking_after=state['tracking'].copy(),launch_after=state['launch'].copy());return rows,None
    def run(self):
        status=None;error=None;replay=None;state=None;failure=None
        b.wheel.wheel_response=lambda *a,**k:self.wheel_call('external_force',self.orig_external,*a,**k)
        b.planar.wheel_response=lambda *a,**k:self.wheel_call('internal_force',self.orig_internal,*a,**k)
        signal.signal(signal.SIGPROF,lambda *_:(_ for _ in ()).throw(b.BudgetStop('CPU_SIGNAL')));signal.signal(signal.SIGALRM,lambda *_:(_ for _ in ()).throw(b.BudgetStop('WALL_SIGNAL')));signal.setitimer(signal.ITIMER_PROF,max(.01,25-self.elapsed()['CPU_s']));signal.setitimer(signal.ITIMER_REAL,max(.01,35-self.elapsed()['wall_s']))
        try:
            self.reserve(264,16,24);self.switch('prefix');phase=b.Phase(self,'prefix');state=d.Study.initial(self);immutable(state['root']);self.last_state=state
            for index in range(1,32):
                rows,_=self.hold(state,self.prefix_commands[index],index,phase,verify_prefix=True);self.rows+=rows
            expected=self.prefix['expected_available_end_state'];exact=d.canonical(d.short(state['root']))==expected['root'] and state['tracking']==expected['tracking'] and state['progress']==expected['progress'] and state['global_raw']==124
            if not exact:raise RuntimeError('PARENT25_AVAILABLE_CHECKPOINT')
            self.result['prefix']={'raw':124,'all_available_fields_exact':True,'full_tracker_visited_from_actual_initial_lineage':True,'checkpoint_sha256':digest(d.Study.checkpoint(self,state))};atomic_write(D/'prefix-checkpoint-private.json',d.Study.checkpoint(self,state))
            self.reserve(140,11,16);self.switch('intervention');phase=b.Phase(self,'intervention')
            for index in [32,33]:
                action=alignment(d.short(state['root']),self.commands[index][1:].tolist());self.intervention_actions.append(dict(index=index,action=action.tolist()));self.journal.append('ALIGNMENT_COMMAND',index=index,action=action.tolist(),global_raw=state['global_raw'],root=d.short(state['root']))
                rows,failure=self.hold(state,action,index,phase,diagnostics=True);self.rows+=rows
                atomic_write(D/f'hold{index}-private.json',dict(rows=rows,checkpoint=d.Study.checkpoint(self,state),failure=failure,cost=self.cost()))
                if failure:status='FIRST_HOLD_LAW_REJECTED' if index==32 else 'SECOND_HOLD_RETENTION_REJECTED';break
            if failure is None:
                self.reserve(132,9,13);self.switch('verification');phase=b.Phase(self,'verification');again=d.Study.initial(self);immutable(again['root']);actual=[];tape={**self.prefix_commands,**{q['index']:np.asarray(q['action'],np.float32) for q in self.intervention_actions}}
                for index in range(1,34):
                    rows,reason=self.hold(again,tape[index],index,phase);actual+=rows
                    if reason:raise RuntimeError('INDEPENDENT_REPLAY_SAFETY:'+reason)
                exact=len(actual)==len(self.rows)==132 and all(all(d.canonical(a.get(key))==d.canonical(z.get(key)) for key in b.KEYS) for a,z in zip(actual,self.rows));checkpoint=d.canonical(d.Study.checkpoint(self,again))==d.canonical(d.Study.checkpoint(self,state))
                if not exact or not checkpoint:raise RuntimeError('INDEPENDENT_REPLAY_IDENTITY')
                replay={'raw':132,'all_rows_full_state_force_history_visited_tracker_clock_exact':True,'checkpoint_contents_exact':True,'law_reselection':False};atomic_write(D/'verified-tape-private.json',dict(rows=actual,commands=[dict(index=i,action=tape[i].tolist()) for i in sorted(tape)],checkpoint=d.Study.checkpoint(self,again)));status='EIGHT_RAW_VIABLE_EXACT_REPLAY'
        except BaseException as exc:
            error=type(exc).__name__+':'+str(exc);status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE';atomic_write(D/'failure-private.json',dict(error=error,traceback=traceback.format_exc(),cost=self.cost(),partial_holds=self.result['holds']),True)
        finally:
            atomic_write(G/'retry/slip581_cost.json',self.cost(),True);b.wheel.wheel_response=self.orig_external;b.planar.wheel_response=self.orig_internal
            if state is not None:atomic_write(D/'run-tape-private.json',dict(rows=self.rows,actions=self.intervention_actions,checkpoint=d.Study.checkpoint(self,state),status=status),True)
            try:
                self.switch('audit');self.journal.close();audit=inspect(D/'raw-journal-private.jsonl');self.validate_closure();self.guard()
            except BaseException as exc:
                audit={'valid':False,'error':str(exc)};status='BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE';error=(error or '')+';AUDIT:'+str(exc)
            signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
            self.result.update(status=status,error=error,independent_replay=replay,journal=audit,cost=self.cost(),native_actions=0,HOLDOUT=0,SEALED=0,new_FD=0,optimizer=0,actual_incumbent_s=13.66,source_incumbent_s=13.20,incumbent_changed=False,whole_executed=False,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0)
            atomic_write(G/'retry/slip581_cost.json',self.cost(),True);atomic_write(G/'retry/slip581_result.json',self.result);print(json.dumps(plain(self.result),indent=2))

if __name__=='__main__':
    if '--register' in sys.argv:register()
    else:
        study=None
        try:study=object.__new__(Study);study.__init__();study.run()
        except BaseException as exc:
            failure={'status':'BUDGET_CENSORED' if isinstance(exc,b.BudgetStop) else 'TECHNICAL_FAILURE','error':type(exc).__name__+':'+str(exc),'source_execution_started':bool(study and getattr(study,'counts',{}).get('attempted_raw',0)),'counts':dict(getattr(study,'counts',{})) if study else {},'CPU_s':time.process_time()-START_CPU+getattr(study,'prior',{}).get('CPU_s',0),'wall_s':time.perf_counter()-START_WALL+getattr(study,'prior',{}).get('wall_s',0)}
            if D.exists():atomic_write(D/'outer-failure-private.json',dict(failure,traceback=traceback.format_exc()),True)
            atomic_write(G/'retry/slip581_outer_failure.json',failure);raise
