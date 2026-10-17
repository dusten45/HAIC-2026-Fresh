"""470 one own-reference whole MODEL parent per arm; no guardian or tail query."""
import copy,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.law468 import ReferencePolicy468,profile_inputs468,natural_first468,ORIGINAL,PROJECTED,PROJECTED_SHA
from retry.observer435 import Child
from retry.pilot420_backend import TechnicalStop,snapshot,fingerprint,rnghash
from retry.planner419 import GoalLedger
from retry.audit431 import physical_tokens
from retry.ledger439 import require,compare_first
from retry.receipt421_io import save_receipt
from retry.loss389_analyze import save,sha,read
from retry.signed417_executor import ExecutorDomainError

RULE='469_70_COMMON_FIRST_FULLGAS_THEN_OWN_REFERENCE_POINT_FF_OWN_FINISH'

class ReferencePolicy470(ReferencePolicy468):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.policy_digest=fingerprint(dict(rule=RULE,arm=self.arm,nodes=self.nodes_digest,source_sha=self.source_sha))
    def inject(self,child):
        super().inject(child);child.reference470=self
    def check(self,child):
        require(not self.nodes.flags.writeable and fingerprint(self.nodes.tolist())==self.nodes_digest,'470_FROZEN_REFERENCE_CHANGED')
        require(not child.ctrl.policy.nodes.flags.writeable and np.array_equal(child.ctrl.policy.nodes,self.nodes),'470_CHILD_REFERENCE_CHANGED')
        require(self.policy_digest==fingerprint(dict(rule=RULE,arm=self.arm,nodes=self.nodes_digest,source_sha=self.source_sha)),'470_POLICY_DIGEST_CHANGED')


def one470(child,arm,index,tag):
    require(arm in [ORIGINAL,PROJECTED] and 0<=index<70,'470_DRIVER_SCOPE')
    binding=child.reference470
    require(binding.arm==arm and child.ctrl.phase() in ['FIRST_LAP','FINISH_CONFIRM'],'470_DRIVER_ARM_PHASE')
    require(child.initial_count==0 and child.tail_count==0,'470_WHOLE_PARENT_NOT_CHILD_TAIL')
    if index==0:require(child.ctrl.phase()=='FIRST_LAP','470_FIRST_PHASE')
    binding.check(child);before=copy.deepcopy(child.ctrl.memory());nominal=child.ctrl.act(child.m)
    command=np.asarray(nominal,np.float32).copy();natural_first_fullgas=None
    if index==0:
        alias=command.copy();alias[1:]=[1.,0.]
        require(np.array_equal(alias,binding.first_command),'470_COMMON_FIRST_FULL_VECTOR')
        natural_first_fullgas=bool(np.array_equal(command,alias))
        if arm==PROJECTED:require(natural_first_fullgas,'470_PROJECTED_FIRST_NATURAL_ALIAS')
        command=alias
    after=copy.deepcopy(child.ctrl.memory());n=len(child.rows)
    child.one(tag,first_override=command,prepared_nominal=nominal,prepared_before=before)
    require(len(child.rows)==n+1,'470_NO_OBSERVED_PARENT_ROW')
    row=child.rows[-1]
    require(row['memory_before']==before and row['memory_after']==after and (child.ctrl.memory()==after or child.status=='FINISHED'),'470_MEMORY_ONCE')
    require(np.array_equal(np.asarray(row['command'],np.float32),command),'470_DISPATCH_COMMAND')
    binding.check(child)
    return dict(arm=arm,action=index+1,nominal_calls=1,prepared_nominal_used=True,first_fullgas_alias=index==0,natural_first_fullgas=natural_first_fullgas,phase_before=before['C']['phase'],phase_after=after['C']['phase'],policy_digest=binding.policy_digest,nodes_digest=binding.nodes_digest,parent_status=child.status,pending_after=child.m.finish_line_tracker.candidate_crossing_time_s is not None,actual_execution_allowed=False)


def whole_parents(root,meter,fixed,pace,state,memory,ledger,expected):
    require(meter.qualification_passed and type(ledger) is GoalLedger and not ledger.done and not ledger.deadline_missed,'470_SOURCE_AND_ACTUAL_ROOT_REQUIRED')
    d=Path(meter.d);origin=(fingerprint(state),fingerprint(memory),ledger.digest(),rnghash());original,projected,path=profile_inputs468(root,fixed,pace)
    require(len(expected)>=1,'470_EXPECTED_FIRST');natural_first468(fixed,projected,expected[0])
    bindings={arm:ReferencePolicy470(arm,nodes,PROJECTED_SHA,expected[0]['command']) for arm,nodes in [(ORIGINAL,original),(PROJECTED,projected)]}
    startticks,startworlds=meter.b['ticks'],meter.b['worlds'];results=[];records=[];first_frame=None
    def persist():
        save(d/'whole_policyrecords-private.json',records);save(d/'whole_policy-results.json',results)
    def immutable():require((fingerprint(state),fingerprint(memory),ledger.digest(),rnghash())==origin,'470_ROOT_ACTUAL_LEDGER_MEMORY_RNG_CHANGED')
    persist()
    for arm in [ORIGINAL,PROJECTED]:
        immutable();binding=bindings[arm];label='whole_'+arm;child=None;error=None;exception=None;status='STARTED';prefix_match13=None;t0,w0=meter.b['ticks'],meter.b['worlds'];r0=len(records)
        try:
            save_receipt(d/(label+'-own-reference-before-constructor-private.json'),dict(rule=RULE,arm=arm,source_path=str(path),source_sha256=PROJECTED_SHA,nodes=binding.nodes.tolist(),nodes_digest=binding.nodes_digest,policy_digest=binding.policy_digest,maximum_parent_actions=70,own_model_finish_required=True,actual_execution_allowed=False))
            meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='470_WHOLE_OWN_REFERENCE:'+binding.policy_digest)
            child=Child(meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,fixed,pace,label,'nominal',world_tag='470_whole_parent');binding.inject(child)
            for index in range(70):
                if child.status!='ACTIVE':break
                rec=one470(child,arm,index,'470_parent_'+arm);records.append(rec);persist();immutable()
                row=child.rows[-1];physical_tokens(row['safety'],allow_empty=True)
                if index==0:
                    compare_first(ledger,row,expected[0],fixed)
                    if first_frame is None:first_frame=copy.deepcopy(row)
                    else:require(row==first_frame,'470_CROSS_ARM_FIRST_FRAME_EXACT')
                if len(child.rows)==13 and child.status=='ACTIVE' and not any(r['safety'] for r in child.rows):
                    qualified=read(d/(arm+'_H13_1-private.json'))['rows']
                    prefix_match13=len(qualified)==13 and child.rows==qualified[:13]
                    rec['prefix_match13']=prefix_match13;rec['qualification_prefix13_exact']=prefix_match13;persist()
                    require(prefix_match13,'470_FRESH_QUALIFICATION_PREFIX13_MISMATCH')
                if child.status=='UNSAFE':physical_tokens(child.error)
                elif child.status=='INFEASIBLE':require(child.error=='predicted_progress_deadline' and child.ledger.deadline_missed,'470_UNREGISTERED_PROGRESS_STOP')
                elif child.status not in ['ACTIVE','FINISHED','CENSORED']:raise TechnicalStop('470_UNREGISTERED_PARENT_STATUS:'+str(child.status))
                require(child.initial_count==0 and child.tail_count==0 and sum(r['predicted']['raw_ticks'] for r in child.rows)<=280,'470_PARENT_COST_OR_TAIL_SCOPE')
                meter.checkpoint('WHOLE_PARENT_TRANSITION',arm=arm,parent_action=len(child.rows),parent_status=child.status)
            if child.status=='ACTIVE':
                status='SCOPE_CENSORED';error='70_actions_no_aftercap_step';child.status=status;child.error=error
            else:status=child.status;error=child.error
            if status=='FINISHED':
                tracker=child.m.finish_line_tracker;row=child.rows[-1];event=row['predicted']['finish_time_s']
                require(row['predicted']['finished'] and child.ledger.done and child.finish_ticks is not None and tracker.finish_time_s==event and tracker.qualified_time_s is not None and event<=row['predicted']['time'],'470_OWN_MODEL_FINISH_WITNESS')
            immutable()
        except ExecutorDomainError as exc:
            allowed={'First_lap_arc_domain','Meaningful_negative_progress_domain','Invalid_finish_confirmation_corridor','Zero_target_outside_launch'}
            error=type(exc).__name__+': '+str(exc);status='DOMAIN_STOP'
            if str(exc) not in allowed:
                status='TECHNICAL_STOP';exception=exc
            else:
                try:
                    immutable()
                    if child is not None:binding.check(child)
                    require(sha(path)==PROJECTED_SHA,'470_DOMAIN_SOURCE_PROFILE_CHANGED')
                    for group in ['sources','protected','original408_preserve']:
                        for filename,digest in getattr(meter,'p',{}).get(group,{}).items():require(sha(filename)==digest,'470_DOMAIN_SOURCE_MANIFEST_CHANGED')
                except BaseException as verification:
                    exception=verification;status='TECHNICAL_STOP';error=type(verification).__name__+': '+str(verification)
            if child is not None:child.status=status;child.error=error
            save(d/(label+'-domain-stop-private.json'),dict(status=status,error=error,raw_ticks=0 if child is None else sum(r['predicted']['raw_ticks'] for r in child.rows),parent_actions=0 if child is None else len(child.rows),no_rescue=True,unchanged_root_required_to_continue=True))
        except BaseException as exc:
            error=type(exc).__name__+': '+str(exc);status='TECHNICAL_STOP';exception=exc
            save(d/(label+'-stop-private.json'),dict(status=status,error=error,traceback=traceback.format_exc(),no_retry=True,actual_execution_allowed=False))
        finally:
            if child:
                try:child.dump(d);child.close()
                except BaseException as cleanup:
                    if exception is None:exception=cleanup;status='TECHNICAL_STOP';error=type(cleanup).__name__+': '+str(cleanup)
                    save(d/(label+'-cleanup-stop-private.json'),dict(error=type(cleanup).__name__+': '+str(cleanup),original_error=error))
            own_finish=bool(child is not None and status=='FINISHED');finish=None if not own_finish else asdict(child.finish_ticks)
            out=dict(arm=arm,label=label,status=status,error=error,parent_actions=0 if child is None else len(child.rows),raw_ticks=0 if child is None else sum(r['predicted']['raw_ticks'] for r in child.rows),own_model_finish=own_finish,official_model_finish=own_finish,finish_ticks=finish,official_event_time_s=None if not own_finish else child.rows[-1]['predicted']['finish_time_s'],confirmation_time_s=None if not own_finish else child.rows[-1]['predicted']['time'],confirmation_raw_ticks=None if not own_finish else child.rows[-1]['predicted']['raw_ticks'],remaining_model_finish_s=None if finish is None else [finish['lo']/50,finish['hi']/50],policy_digest=binding.policy_digest,nodes_digest=binding.nodes_digest,source_profile_sha256=PROJECTED_SHA,initial_count=0 if child is None else child.initial_count,tail_count=0 if child is None else child.tail_count,whole_arm_runs=1,whole_arm_repeated=False,prefix_match13=prefix_match13,qualification_prefix13_exact=prefix_match13,driver_records=len(records)-r0,model_ticks=meter.b['ticks']-t0,model_worlds=meter.b['worlds']-w0,rows_private_path=str(d/(label+'-private.json')),observer_private_path=str(d/(label+'-observer-private.json')),actual_finish_witness=False,actual_execution_allowed=False)
            results.append(out);persist()
        if exception is not None:raise exception
    immutable();require(meter.b['ticks']-startticks<=560 and meter.b['worlds']-startworlds==2,'470_WHOLE_COST')
    finished=len(results)==2 and all(x['own_model_finish'] for x in results)
    gain=None if not finished else [(results[0]['finish_ticks']['lo']-results[1]['finish_ticks']['hi'])/50,(results[0]['finish_ticks']['hi']-results[1]['finish_ticks']['lo'])/50]
    return dict(status='TWO_WHOLE_PARENTS_FINISHED' if finished else 'WHOLE_PARENT_OUTCOMES_RECORDED',policies=results,model_remaining_finish_gain_bracket_s=gain,model_ticks=meter.b['ticks']-startticks,model_worlds=meter.b['worlds']-startworlds,whole_arm_repeated=False,records_path=str(d/'whole_policyrecords-private.json'),results_path=str(d/'whole_policy-results.json'),actual_execution_allowed=False)
