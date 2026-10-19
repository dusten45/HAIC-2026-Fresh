"""Same586 instrumentation recovery before its first FD/QP. Never rerun positive."""
import time
RECOVERY_CPU=time.process_time();RECOVERY_WALL=time.perf_counter()
import json,sys,math,hashlib,copy,traceback
from pathlib import Path
from collections import Counter
import numpy as np
import retry.shoot586_model as s
s.START_CPU=RECOVERY_CPU;s.START_WALL=RECOVERY_WALL
G=s.G;OLD=Path('/workspace/haic-response586-private');NEW=Path('/workspace/haic-response586-recovery-private');RC=G/'retry/shoot586_recovery_contract.json';BACKUP=Path('/workspace/shoot586-initial-model-private.py')
FILES={'original_contract':s.CONTRACT,'initial_result':G/'retry/shoot586_initial_result.json','initial_cost':G/'retry/shoot586_initial_cost.json','positive':OLD/'positive-private.json','raw96':OLD/'raw96-checkpoint-private.json','failure':OLD/'failure-private.json','journal':OLD/'raw-journal-private.jsonl','initial_model':BACKUP,'connection_check':Path('/workspace/shoot586-connection-check-private.json')}

def proof():
    original=s.d.rd(s.CONTRACT);result=s.d.rd(FILES['initial_result']);cost=s.d.rd(FILES['initial_cost']);failure=s.d.rd(FILES['failure']);positive=s.d.rd(FILES['positive']);cp=s.d.rd(FILES['raw96']);tests=s.d.rd(G/'retry/shoot586_tests.json')
    transformed=BACKUP.read_text().replace('id=case_id,kind=kind,control_sha256=','id=case_id,candidate_kind=kind,control_sha256=').replace('record=dict(id=case_id,kind=kind,safe=','record=dict(id=case_id,candidate_kind=kind,safe=')
    assert transformed==(G/'retry/shoot586_model.py').read_text() and s.d.sha(BACKUP)==original['implementation_sha256']['retry/shoot586_model.py']
    for f,h in original['dependency_file_sha256'].items():
        if f!='retry/shoot586_model.py':assert s.d.sha(G/f if not Path(f).is_absolute() else Path(f))==h,f
    tape=s.d.rd(s.INPUTS['tape']);commands={q['index']:np.asarray(q['action'],np.float32) for q in tape['commands']};seed=s.seed_controls(commands);case=positive['suffix'];partial=np.asarray(failure['partial']['x'],float);first,delta,sign=s.fd_point(seed,0)
    assert np.array_equal(seed,np.asarray(case['x'])) and np.array_equal(s.residuals(positive['rows'][96:],True,True),np.asarray(case['g']))
    assert np.array_equal(first,partial) and s.command_key(first)==s.command_key(partial)
    assert len(positive['rows'])==252 and positive['rows']==tape['rows'][:252] and s.digest(cp)==result['positive']['raw96_full_checkpoint_sha256']
    assert cost['total']['attempted_raw']==cost['total']['completed_model_ticks']==252 and cost['total']['geometry_checks']==253 and cost['total']['external_force']==cost['total']['internal_force']==1008
    assert cost['suffix_cache_misses']==1 and cost['FD_columns']==0 and cost['FD_batches']==1 and failure['partial']['rows']==[]
    journal=s.inspect(FILES['journal']);assert journal['valid'] and journal['head']==result['journal']['head'] and journal['events']==1766 and journal['kinds']['BEFORE_FORCE']==252 and journal['kinds'].get('CANDIDATE_STARTED',0)==0
    assert '_prepare_scalar_function' in failure['traceback'] and '_update_grad' in failure['traceback'] and 'CANDIDATE_STARTED' in failure['traceback']
    extra_cpu=tests['CPU_s']-original['numerical_preparation']['tests']['CPU_s'];extra_wall=tests['wall_s']-original['numerical_preparation']['tests']['wall_s'];assert extra_cpu>=0 and extra_wall>=0
    return dict(same_scientific_contract_sha256=s.d.sha(s.CONTRACT),instrumentation_only_two_metadata_keys=True,positive252_reused_without_source=True,raw96_full_checkpoint_sha256=s.digest(cp),first_pending_FD_command_sha256=hashlib.sha256(s.command_key(first)).hexdigest(),first_pending_FD_coordinate=0,first_pending_FD_actual_normalized_delta=delta,initial_SLSQP_QP_calls=0,initial_FD_source_columns=0,initial_source_attempts=252,consumed_unexecuted_candidate_slot=1,remaining_actual_suffix_slots=127,initial_journal=journal,extra_test_CPU_s=extra_cpu,extra_test_wall_s=extra_wall,recovery_auxiliary_registration_and_old_final_writer_CPU_wall_charge_s=3.,solver_reentry='SameScalarFunctioninitialgradient,whichfailedbeforefirstFortranSLSQPcall. Samezeroanchor/seed/options/residuals/FDinput;nooptimizationiterationorresearchrestart. Pythoninitializationandcachequeriesarerepeatedandcharged,no source/FDcandidate duplicated.')

def register():
    p=proof();warm=s.warm_solver()
    c=dict(study=586,status='INSTRUMENTATION_RECOVERY_FROZEN_BEFORE_NEW_SOURCE',scope='Sameenvironment,task,scientificcontractandremainingbudgets. Do notrerunpositive252;firstunexecutedFDonly. Preservefailedinitialsegmentandcost. No newseed/settings/horizon/cap.',proof=p,input_sha256={k:s.d.sha(v) for k,v in FILES.items()},original_input_sha256=s.d.rd(s.CONTRACT)['input_sha256'],dependency_file_sha256=s.b.manifest(),implementation_sha256={str(v.relative_to(G)):s.d.sha(v) for v in [Path(__file__),G/'retry/shoot586_model.py',G/'retry/shoot586_math.py',G/'tests/test_shoot586.py']},recovery_registration_pure_warm_solver=warm,tests=s.d.rd(G/'retry/shoot586_tests.json'),initial_result_preserved='retry/shoot586_initial_result.json',initial_cost_preserved='retry/shoot586_initial_cost.json',recovery_journal_links_original_head=True,aggregate_and_stage_caps_unchanged=True,native_actions=0,new_FD_before_recovery=0,new_source_before_recovery=0)
    s.atomic_write(RC,c);print(json.dumps(dict(recovery_registered=True,proof=p,source_ticks=0)))

class RecoveryStudy(s.Study):
    def __init__(self):
        self.overlay=s.d.rd(RC);self.recovery_proof=proof();assert self.recovery_proof==self.overlay['proof']
        for k,h in self.overlay['input_sha256'].items():assert s.d.sha(FILES[k])==h,k
        self.contract=s.d.rd(s.CONTRACT);old=s.d.rd(FILES['initial_cost']);initial=s.d.rd(FILES['initial_result']);extra_cpu=self.recovery_proof['extra_test_CPU_s'];extra_wall=self.recovery_proof['extra_test_wall_s']
        self.prior=dict(CPU_s=old['total']['CPU_s']+extra_cpu+3,wall_s=old['total']['wall_s']+extra_wall+3);self.bucket='preparation';self.mode='recovery_preparation';self.stage_start_cpu=RECOVERY_CPU;self.stage_start_wall=RECOVERY_WALL;self.phases={k:{j:v[j] for j in ['CPU_s','wall_s']} for k,v in old['phases'].items()};self.phases['preparation']['CPU_s']+=extra_cpu+2.5;self.phases['preparation']['wall_s']+=extra_wall+2.5;self.phases['audit']['CPU_s']+=.5;self.phases['audit']['wall_s']+=.5
        self.counts=Counter({k:v for k,v in old['total'].items() if k not in ['CPU_s','wall_s']});self.stage_counts={k:Counter({j:x for j,x in v.items() if j not in ['CPU_s','wall_s']}) for k,v in old['phases'].items()};self.mode_counts={k:Counter(v) for k,v in old['modes'].items()};self.cases=old['suffix_cache_misses'];self.cache_requests=old['cache_requests'];self.cache_hits=old['cache_hits'];self.fd_columns=old['FD_columns'];self.fd_batches=old['FD_batches'];self.numerical_calls=old['minimize_calls_runtime'];self.events=[];self.cache={};self.best=self.seedcase=self.fd_cache=None;self.last_partial=None;self.verification_raw_remaining=1324;self.result={'recovery':self.recovery_proof,'positive':initial['positive']};self.first_actual_restored=False
        NEW.mkdir(mode=0o700,exist_ok=False);s.D=NEW;self.journal=s.Journal(NEW/'raw-journal-private.jsonl');self.guard();self.result['recovery_runtime_pure_warm_solver']=s.warm_solver();self.numerical_calls+=1;self.validate_closure()
        for f,h in self.overlay['implementation_sha256'].items():assert s.d.sha(G/f)==h,f
        for k,h in self.contract['input_sha256'].items():assert s.d.sha(s.INPUTS[k])==h,k
        self.tape,self.static,self.paths,self.ledger=[s.d.rd(s.INPUTS[k]) for k in ['tape','static','paths','ledger']];self.commands={q['index']:np.asarray(q['action'],np.float32) for q in self.tape['commands']};self.seed=s.seed_controls(self.commands);self.planes=s.d.rd(s.INPUTS['planes'])['gates']['planes'];self.index=s.d.bounds(self.static['root']['roads']);self.edge=s.d.boundary_index(self.static['boundary']);self.orig_external=s.b.wheel.wheel_response;self.orig_internal=s.b.planar.wheel_response
        self.journal.append('RESUME_FROM_CLOSED_SEGMENT',original_head=self.recovery_proof['initial_journal']['head'],original_events=1766,original_cost=old,original_contract_sha256=s.d.sha(s.CONTRACT),recovery_contract_sha256=s.d.sha(RC));s.atomic_write(NEW/'STARTED.json',dict(contract_sha256=s.d.sha(s.CONTRACT),recovery_contract_sha256=s.d.sha(RC),source_ticks_before=252,input_sha256=self.contract['input_sha256']))
    def validate_closure(self):
        for f,h in self.overlay['dependency_file_sha256'].items():
            if s.d.sha(G/f if not Path(f).is_absolute() else Path(f))!=h:raise RuntimeError('RECOVERY_DEPENDENCY_HASH:'+f)
        if any(f not in self.overlay['dependency_file_sha256'] for f in s.b.manifest()):raise RuntimeError('RECOVERY_UNMANIFESTED_IMPORT')
    def positive(self):
        positive=s.d.rd(FILES['positive']);cp=s.d.rd(FILES['raw96']);self.start=dict(root=s.d.load_root(dict(cp['root_without_roads'],roads=self.static['root']['roads'])),visited=set(cp['visited']),tracker=s.d.FinishLineTracker(**cp['tracker']),elapsed=cp['elapsed'],global_raw=cp['global_raw'],progress=cp['progress'],launch=list(cp['launch']),tracking=list(cp['tracking']));s.immutable(self.start['root']);self.start_digest=s.digest(self.checkpoint(self.start))
        if self.start_digest!=self.recovery_proof['raw96_full_checkpoint_sha256'] or s.d.canonical(self.checkpoint(self.start))!=s.d.canonical(self.expected_checkpoint(96)):raise RuntimeError('RESTORED_RAW96_IDENTITY')
        case=positive['suffix'];case['x']=np.asarray(case['x'],float);case['g']=np.asarray(case['g'],float);assert case['x'].shape==(50,) and case['g'].shape==(1718,) and case['admissible'] and np.array_equal(case['x'],self.seed)
        if s.d.canonical(positive['checkpoint'])!=s.d.canonical(self.expected_checkpoint(252)):raise RuntimeError('STORED_POSITIVE252_CHECKPOINT')
        self.seedcase=self.best=case;self.cache[s.command_key(self.seed)]=case;self.baseline_time=case['f'];self.journal.append('POSITIVE_AND_CHECKPOINT_RESTORED_SOURCE0',raw96_sha256=self.start_digest,positive_rows=252,seed_minimum_constraint=float(np.min(case['g'])),source_ticks_added=0)
    def evaluate_x(self,x,kind):
        if s.command_key(x) not in self.cache and not self.first_actual_restored:
            expected=np.asarray(s.d.rd(FILES['failure'])['partial']['x'],float)
            if self.cases!=1 or kind!='FD' or not np.array_equal(x,expected) or hashlib.sha256(s.command_key(x)).hexdigest()!=self.recovery_proof['first_pending_FD_command_sha256']:raise RuntimeError('FIRST_RESTORED_FD_IDENTITY')
            self.first_actual_restored=True;self.journal.append('FIRST_RESTORED_FD_IDENTITY',command_sha256=self.recovery_proof['first_pending_FD_command_sha256'],consumed_unexecuted_slot=1)
        return super().evaluate_x(x,kind)

if __name__=='__main__':
    if '--register' in sys.argv:register()
    else:
        study=None
        try:study=RecoveryStudy();study.run()
        except BaseException as exc:
            out=dict(status='BUDGET_CENSORED' if isinstance(exc,s.b.BudgetStop) else 'TECHNICAL_FAILURE',error=type(exc).__name__+':'+str(exc),source_execution_started=bool(study and getattr(study,'counts',{}).get('attempted_raw',0)>252),source_attempts_including_prior=getattr(study,'counts',{}).get('attempted_raw',252) if study else 252)
            if NEW.exists():s.atomic_write(NEW/'outer-failure-private.json',dict(out,traceback=traceback.format_exc()),True)
            s.atomic_write(G/'retry/shoot586_recovery_outer_failure.json',out);raise
