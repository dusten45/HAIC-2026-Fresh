"""477 natural reference-only comparison at the stored common pre23 root."""
import copy,hashlib,json,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.observer435 import Child
from retry.law468 import profile_inputs468,PROJECTED_SHA
from retry.law465 import _scope465 as _scope477,_finish465 as _finish477
from retry.pilot420_backend import TechnicalStop,snapshot,fingerprint,rnghash
from retry.pilot421_run import compare_frames
from retry.audit439 import replay
from retry.ledger439 import compare_first,require
from retry.planner419 import GoalLedger,Parent
from retry.audit431 import physical_tokens
from retry.receipt421_io import save_receipt,load_receipt
from retry.loss389_analyze import save,read,sha
from retry.terminal410_model import from_actual_full
from retry.signed417_executor import ExecutorDomainError

ORIGINAL='OriginalReference'
PROJECTED='Projected4Reference'
ALLOCATED='AllocationP4'
RULE='477_PRE23_NATURAL_OWN_REFERENCE_POINT_FF_250_OWN_MODEL_FINISH'


def root_source_paths(root):
    d=root/'stage453'
    paths=[d/'actual_baseline/trace-private.jsonl',d/'actual_baseline/baseline_step23-before-native-private.json',d/'actual_candidate/candidate_step23-before-native-private.json',d/'baseline_decision1-before-actual-dispatch-private.json',d/'baseline_decision1_query-before-integration-private.json']
    candidates=[root/'stage466/projection-and-segments-private.json',root/'stage466-numeric-recovery1/projection-and-segments-private.json']
    matches=[p for p in candidates if p.exists() and sha(p)==PROJECTED_SHA]
    require(bool(matches),'477_FROZEN_PROFILE_SOURCE');return paths+[matches[0]]


def root_inputs477(root):
    d=root/'stage453';rows=[json.loads(s) for s in (d/'actual_baseline/trace-private.jsonl').read_text().splitlines()]
    bundle=load_receipt(d/'baseline_decision1-before-actual-dispatch-private.json');src,memory,rng=Parent(**bundle['context']['parent']).fork_inputs()
    state=src['terminal_model'];ledger=GoalLedger(**bundle['context']['ledger']);before=load_receipt(d/'actual_baseline/baseline_step23-before-native-private.json')
    other=load_receipt(d/'actual_candidate/candidate_step23-before-native-private.json')
    require(before['full_pre_before_nominal']==other['full_pre_before_nominal'],'477_COMMON_PRE23_FULL_NATIVE_ROOT')
    require(state==from_actual_full(before['full_pre_before_nominal']) and memory==rows[22]['memory_before']==before['full_pre_before_nominal']['controller'],'477_PRE23_NATIVE_SOURCE')
    require(rows[22]['step']==23 and memory['C']['phase']=='FIRST_LAP' and not ledger.done and not ledger.deadline_missed,'477_ROOT_DOMAIN')
    require(state['finish_tracker']['candidate_crossing_time_s'] is None and state['finish_tracker']['finish_time_s'] is None,'477_ROOT_NO_FINISH')
    expected=rows[22:35];require(len(expected)==13 and all(r['command']==r['nominal'] for r in expected),'477_ORIGINAL_FACTUAL_NATURAL13')
    proof=load_receipt(d/'baseline_decision1_query-before-integration-private.json')
    require(proof['state']==state and proof['memory']==memory and proof['ledger']==asdict(ledger),'477_ROOT_QUERY_INPUT_PROOF')
    require(src['immutable_actual_root_digest']==ledger.digest(),'477_ROOT_ACTUAL_LEDGER_BINDING')
    require(type(proof['global_RNG_pickle']) is bytes and hashlib.sha256(proof['global_RNG_pickle']).hexdigest()==proof['RNG_digest']==rng['model_global_rng_digest'],'477_ROOT_RNG_BINDING')
    return state,memory,ledger,rng,proof['global_RNG_pickle'],expected


class ReferencePolicy477:
    def __init__(self,arm,nodes,source_sha):
        require(arm in [ORIGINAL,PROJECTED,ALLOCATED],'477_ARM')
        self.arm=arm;self.nodes=np.asarray(nodes,float).copy()
        require(self.nodes.ndim==1 and len(self.nodes)>1 and np.isfinite(self.nodes).all() and self.nodes[0]==0 and np.all(self.nodes[1:]>0),'477_NODE_DOMAIN')
        self.nodes.setflags(write=False);self.nodes_digest=fingerprint(self.nodes.tolist());self.source_sha=source_sha
        self.policy_digest=fingerprint(dict(rule=RULE,arm=arm,nodes=self.nodes_digest,source_sha=source_sha))
    def inject(self,child):
        before=copy.deepcopy(child.ctrl.memory());stamp=fingerprint(snapshot(child.m));ledger=child.ledger
        child.ctrl.policy.nodes=self.nodes.copy();child.ctrl.policy.nodes.setflags(write=False);child.reference477=self
        require(child.ctrl.memory()==before and fingerprint(snapshot(child.m))==stamp and child.ledger==ledger,'477_INJECTION_CHANGED_ROOT')
        self.check(child)
    def check(self,child):
        require(not self.nodes.flags.writeable and fingerprint(self.nodes.tolist())==self.nodes_digest,'477_FROZEN_NODES_CHANGED')
        require(not child.ctrl.policy.nodes.flags.writeable and np.array_equal(child.ctrl.policy.nodes,self.nodes),'477_CHILD_NODES_CHANGED')
        require(self.policy_digest==fingerprint(dict(rule=RULE,arm=self.arm,nodes=self.nodes_digest,source_sha=self.source_sha)),'477_POLICY_DIGEST_CHANGED')


def one477(child,arm,index,tag):
    require(arm in [ORIGINAL,PROJECTED,ALLOCATED] and 0<=index<250,'477_DRIVER_SCOPE')
    binding=child.reference477;require(binding.arm==arm and child.ctrl.phase() in ['FIRST_LAP','FINISH_CONFIRM'],'477_DRIVER_PHASE')
    require(child.initial_count==0 and child.tail_count==0,'477_NO_CHILD_TAIL')
    binding.check(child);before=copy.deepcopy(child.ctrl.memory());nominal=child.ctrl.act(child.m);command=np.asarray(nominal,np.float32).copy();after=copy.deepcopy(child.ctrl.memory());n=len(child.rows)
    if arm==ALLOCATED:
        from retry.live477 import allocate_current
        command=allocate_current(child,command,index)
    require(child.ctrl.memory()==after,'477_ALLOCATOR_CHANGED_NOMINAL_MEMORY')
    child.one(tag,first_override=command,prepared_nominal=nominal,prepared_before=before)
    require(len(child.rows)==n+1,'477_NO_OBSERVED_ROW');row=child.rows[-1]
    if arm==ALLOCATED:
        from retry.live477 import check_first_raw
        check_first_raw(child,index)
    require(row['memory_before']==before and row['memory_after']==after and (child.ctrl.memory()==after or child.status=='FINISHED'),'477_MEMORY_ONCE')
    require(np.array_equal(np.asarray(row['command'],np.float32),command),'477_DISPATCH_COMMAND_CHANGED')
    binding.check(child)
    return dict(arm=arm,action=index+1,nominal_calls=1,prepared_nominal_used=True,forced_fullgas=False,natural_command=arm!=ALLOCATED,phase_before=before['C']['phase'],phase_after=after['C']['phase'],policy_digest=binding.policy_digest,nodes_digest=binding.nodes_digest,parent_status=child.status,pending_after=child.m.finish_line_tracker.candidate_crossing_time_s is not None,actual_execution_allowed=False)


def root_h13(root,meter,fixed,pace,state,memory,ledger,expected):
    """Qualify natural original reference and P4 independently at common pre23."""
    require(meter.qualification_passed and type(ledger) is GoalLedger and not ledger.done and not ledger.deadline_missed,'477_FRESH_SOURCE_AND_ACTUAL_ROOT_REQUIRED')
    d=Path(meter.d);origin=(fingerprint(state),fingerprint(memory),ledger.digest(),rnghash(),fingerprint(fixed),fingerprint(np.asarray(pace).tolist()))
    require(len(expected)>=13,'477_expected_native13')
    require(all(r['command']==r['nominal'] for r in expected[:13]),'477_ORIGINAL_NATURAL_NATIVE13')
    original,projected,profile_path=profile_inputs468(root,fixed,pace)
    bindings={arm:ReferencePolicy477(arm,nodes,PROJECTED_SHA) for arm,nodes in [(ORIGINAL,original),(PROJECTED,projected),(ALLOCATED,projected)]}
    startticks,startworlds=meter.b['ticks'],meter.b['worlds'];cohorts=[];drivers=[]
    def persist():
        save(d/'policyrecords-private.json',drivers);save(d/'cohortresults.json',cohorts)
    def immutable():
        require((fingerprint(state),fingerprint(memory),ledger.digest(),rnghash(),fingerprint(fixed),fingerprint(np.asarray(pace).tolist()))==origin,'477_root_input_ledger_RNG_mutation')
    def result(status):
        return dict(status=status,passed=status=='THREE_H13_COHORTS_COMPLETED_REPEAT_EXACT',cohorts=cohorts,model_ticks=meter.b['ticks']-startticks,model_worlds=meter.b['worlds']-startworlds,policyrecords_path=str(d/'policyrecords-private.json'),cohortresults_path=str(d/'cohortresults.json'),actual_execution_allowed=False)
    persist()
    for arm in [ORIGINAL,PROJECTED,ALLOCATED]:
        children=[];held=None;pair=[];armticks,armworlds=meter.b['ticks'],meter.b['worlds']
        try:
            for rep in [1,2]:
                immutable();label=arm+'_H13_'+str(rep)
                binding=bindings[arm]
                save_receipt(d/(label+'-own-reference-before-constructor-private.json'),dict(arm=arm,source_path=str(profile_path),source_sha256=PROJECTED_SHA,nodes=binding.nodes.tolist(),nodes_digest=binding.nodes_digest,policy_digest=binding.policy_digest,immutable_actual_root_digest=ledger.digest(),root_state_digest=fingerprint(state),root_memory_digest=fingerprint(memory),actual_execution_allowed=False))
                meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='477_OWN_REFERENCE_POINT_FF:'+binding.policy_digest)
                child=Child(meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,fixed,pace,label,'nominal',world_tag='477_required' if rep==1 else '477_repeat');children.append(child);binding.inject(child)
                scope=None
                for index in range(13):
                    scope=_scope477(child)
                    if scope or child.status!='ACTIVE':break
                    rec=one477(child,arm,index,'477_'+arm+'_H13');rec.update(repetition=rep,world_label=label);drivers.append(rec);persist();immutable()
                scope=scope or _scope477(child);_finish477(child);child.dump(d)
                same=0;first_divergence=None;calibration=None
                if arm==ORIGINAL:
                    for index,frame in enumerate(child.rows):
                        if first_divergence is None and not np.array_equal(np.asarray(frame['command'],np.float32),np.asarray(expected[index]['command'],np.float32)):first_divergence=index+1
                        if first_divergence is None:same+=1
                    if len(child.rows)==13 and scope is None and child.status=='ACTIVE':
                        calibration=replay(child.rows,expected[:13],fixed)
                        require(calibration['certified_prefix_actions']==13 and calibration['fresh_current_first_pass']>=1,'477_NATURAL_ORIGINAL_NATIVE13_FIDELITY')
                        require(np.array_equal(np.asarray(child.rows[0]['command'],np.float32),np.asarray(expected[0]['command'],np.float32)),'477_ORIGINAL_CURRENT_FIRST_COMMAND_EXACT')
                        compare_first(ledger,child.rows[0],expected[0],fixed)
                packet=dict(arm=arm,repetition=rep,label=label,status=child.status,error=child.error,scope_exit=scope,rows=len(child.rows),signature=child.signature(),initial_safe=child.initial_safe,initial_progress=child.initial_progress,first=copy.deepcopy(child.rows[0]),factual_calibration=calibration,native_same_command_prefix_actions=same if arm==ORIGINAL else 0,native_factual_actions=same if arm==ORIGINAL and calibration is not None else 0,physical_ledger_replay_qualified_actions=13 if arm==ORIGINAL and calibration is not None else 0,native_first_command_divergence=first_divergence if arm==ORIGINAL else None,child_private_path=str(d/(label+'-private.json')),observer_private_path=str(d/(label+'-observer-private.json')))
                pair.append(packet);save_receipt(d/(label+'-cohort-proof-private.json'),packet);child.close();immutable()
            require(pair[0]['signature']==pair[1]['signature'] and pair[0]['scope_exit']==pair[1]['scope_exit'],'477_H13_INDEPENDENT_REPEAT_MISMATCH')
            # A held third world tests the first current transition only.
            label=arm+'_held_first';save_receipt(d/(label+'-own-reference-before-constructor-private.json'),dict(arm=arm,source_sha256=PROJECTED_SHA,nodes=bindings[arm].nodes.tolist(),nodes_digest=bindings[arm].nodes_digest,policy_digest=bindings[arm].policy_digest,immutable_actual_root_digest=ledger.digest(),root_state_digest=fingerprint(state),root_memory_digest=fingerprint(memory),actual_execution_allowed=False));meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='477_HELD_OWN_REFERENCE:'+bindings[arm].policy_digest)
            held=Child(meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,fixed,pace,label,'nominal',world_tag='477_held');bindings[arm].inject(held)
            rec=one477(held,arm,0,'477_held_first');rec.update(repetition='held',world_label=label);drivers.append(rec);persist()
            require(len(held.rows)==1,'477_HELD_NO_FIRST_ROW');z=compare_frames(held.rows[0],pair[0]['first'])
            require(z['passed'] and z['wheel']['clipped_flag_mismatches']==0 and held.rows[0]['memory_before']==pair[0]['first']['memory_before'] and held.rows[0]['memory_after']==pair[0]['first']['memory_after'] and held.rows[0]['command']==pair[0]['first']['command'],'477_HELD_FIRST_MISMATCH')
            held.dump(d);immutable()
            a=pair[0];full=a['rows']==13 and a['status']=='ACTIVE' and a['scope_exit'] is None and a['initial_safe'] and a['initial_progress']
            outcome='COMPLETE_H13' if full else 'SCOPE_EXIT' if a['scope_exit'] else 'TYPED_PHYSICAL_INELIGIBLE' if a['status']=='UNSAFE' else 'SUPPORTED_FULL_H13_PROGRESS_REJECTION' if a['status']=='INFEASIBLE' else 'INCOMPLETE_H13'
            cohort=dict(arm=arm,status=outcome,error=a['error'],scope_exit=a['scope_exit'],rows=a['rows'],independent_repeat_exact=True,held_first_passed=True,trajectories=pair,model_ticks=meter.b['ticks']-armticks,model_worlds=meter.b['worlds']-armworlds,native_factual_scope='13-step physical/geometry/ledger policy replay; exact same-command scope separately counted' if arm==ORIGINAL else 'No native counterpart qualification; P4 model consistency only',policy_digest=bindings[arm].policy_digest,nodes_digest=bindings[arm].nodes_digest,source_profile_sha256=PROJECTED_SHA,native_factual_actions=a['native_factual_actions'],physical_ledger_replay_qualified_actions=a['physical_ledger_replay_qualified_actions'],actual_execution_allowed=False)
            cohorts.append(cohort);persist()
            require(cohort['model_ticks']<=108 and cohort['model_worlds']==3,'477_ARM_COST')
            if not full:return result(outcome)
        finally:
            for child in children:
                if not child.closed:child.dump(d);child.close()
            if held and not held.closed:held.dump(d);held.close()
            persist()
    immutable();require(meter.b['ticks']-startticks<=324 and meter.b['worlds']-startworlds==9,'477_ROOT_COHORT_COST')
    return result('THREE_H13_COHORTS_COMPLETED_REPEAT_EXACT')


def whole_parents(root,meter,fixed,pace,state,memory,ledger,expected):
    require(meter.qualification_passed and type(ledger) is GoalLedger and not ledger.done and not ledger.deadline_missed,'477_SOURCE_AND_ACTUAL_ROOT_REQUIRED')
    d=Path(meter.d);origin=(fingerprint(state),fingerprint(memory),ledger.digest(),rnghash(),fingerprint(fixed),fingerprint(np.asarray(pace).tolist()));original,projected,path=profile_inputs468(root,fixed,pace)
    require(len(expected)>=13 and all(r['command']==r['nominal'] for r in expected[:13]),'477_EXPECTED_NATURAL_ORIGINAL13')
    bindings={arm:ReferencePolicy477(arm,nodes,PROJECTED_SHA) for arm,nodes in [(ORIGINAL,original),(PROJECTED,projected),(ALLOCATED,projected)]}
    startticks,startworlds=meter.b['ticks'],meter.b['worlds'];results=[];records=[]
    def persist():
        save(d/'whole_policyrecords-private.json',records);save(d/'whole_policy-results.json',results)
    def immutable():require((fingerprint(state),fingerprint(memory),ledger.digest(),rnghash(),fingerprint(fixed),fingerprint(np.asarray(pace).tolist()))==origin,'477_ROOT_ACTUAL_LEDGER_MEMORY_RNG_CHANGED')
    persist()
    for arm in [PROJECTED,ALLOCATED]:
        immutable();binding=bindings[arm];label='whole_'+arm;child=None;error=None;exception=None;status='STARTED';prefix_match13=None;native_first_verified=False;t0,w0=meter.b['ticks'],meter.b['worlds'];r0=len(records)
        try:
            save_receipt(d/(label+'-own-reference-before-constructor-private.json'),dict(rule=RULE,arm=arm,source_path=str(path),source_sha256=PROJECTED_SHA,nodes=binding.nodes.tolist(),nodes_digest=binding.nodes_digest,policy_digest=binding.policy_digest,maximum_parent_actions=250,own_model_finish_required=True,actual_execution_allowed=False))
            meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='477_WHOLE_OWN_REFERENCE:'+binding.policy_digest)
            child=Child(meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,fixed,pace,label,'nominal',world_tag='477_whole_parent');binding.inject(child)
            for index in range(250):
                if child.status!='ACTIVE':break
                rec=one477(child,arm,index,'477_parent_'+arm);records.append(rec);persist();immutable()
                row=child.rows[-1];physical_tokens(row['safety'],allow_empty=True)
                if index==0 and arm==ORIGINAL:
                    require(np.array_equal(np.asarray(row['command'],np.float32),np.asarray(expected[0]['command'],np.float32)),'477_WHOLE_ORIGINAL_CURRENT_FIRST_COMMAND_EXACT')
                    compare_first(ledger,row,expected[0],fixed);native_first_verified=True
                if len(child.rows)==13 and child.status=='ACTIVE' and not any(r['safety'] for r in child.rows):
                    qualified=read(d/(arm+'_H13_1-private.json'))['rows']
                    prefix_match13=len(qualified)==13 and child.rows==qualified[:13]
                    rec['prefix_match13']=prefix_match13;rec['qualification_prefix13_exact']=prefix_match13;persist()
                    require(prefix_match13,'477_FRESH_QUALIFICATION_PREFIX13_MISMATCH')
                if child.status=='UNSAFE':physical_tokens(child.error)
                elif child.status=='INFEASIBLE':require(child.error=='predicted_progress_deadline' and child.ledger.deadline_missed,'477_UNREGISTERED_PROGRESS_STOP')
                elif child.status not in ['ACTIVE','FINISHED','CENSORED']:raise TechnicalStop('477_UNREGISTERED_PARENT_STATUS:'+str(child.status))
                require(child.initial_count==0 and child.tail_count==0 and sum(r['predicted']['raw_ticks'] for r in child.rows)<=1000,'477_PARENT_COST_OR_TAIL_SCOPE')
                meter.checkpoint('WHOLE_PARENT_TRANSITION',arm=arm,parent_action=len(child.rows),parent_status=child.status)
            if child.status=='ACTIVE':
                status='SCOPE_CENSORED';error='250_actions_no_aftercap_step';child.status=status;child.error=error
            else:status=child.status;error=child.error
            if status=='FINISHED':
                tracker=child.m.finish_line_tracker;row=child.rows[-1];event=row['predicted']['finish_time_s']
                require(row['predicted']['finished'] and child.ledger.done and child.finish_ticks is not None and tracker.finish_time_s==event and tracker.qualified_time_s is not None and event<=row['predicted']['time'],'477_OWN_MODEL_FINISH_WITNESS')
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
                    require(sha(path)==PROJECTED_SHA,'477_DOMAIN_SOURCE_PROFILE_CHANGED')
                    for group in ['sources','protected','original408_preserve']:
                        for filename,digest in getattr(meter,'p',{}).get(group,{}).items():require(sha(filename)==digest,'477_DOMAIN_SOURCE_MANIFEST_CHANGED')
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
            out=dict(arm=arm,label=label,status=status,error=error,parent_actions=0 if child is None else len(child.rows),raw_ticks=0 if child is None else sum(r['predicted']['raw_ticks'] for r in child.rows),own_model_finish=own_finish,official_model_finish=own_finish,finish_ticks=finish,official_event_time_s=None if not own_finish else child.rows[-1]['predicted']['finish_time_s'],confirmation_time_s=None if not own_finish else child.rows[-1]['predicted']['time'],confirmation_raw_ticks=None if not own_finish else child.rows[-1]['predicted']['raw_ticks'],remaining_model_finish_s=None if finish is None else [finish['lo']/50,finish['hi']/50],policy_digest=binding.policy_digest,nodes_digest=binding.nodes_digest,source_profile_sha256=PROJECTED_SHA,initial_count=0 if child is None else child.initial_count,tail_count=0 if child is None else child.tail_count,whole_arm_runs=1,whole_arm_repeated=False,prefix_match13=prefix_match13,qualification_prefix13_exact=prefix_match13,driver_records=len(records)-r0,model_ticks=meter.b['ticks']-t0,model_worlds=meter.b['worlds']-w0,rows_private_path=str(d/(label+'-private.json')),observer_private_path=str(d/(label+'-observer-private.json')),native_factual_scope='Original first/current and qualified H13 only' if arm==ORIGINAL else 'No native counterpart qualification',native_factual_actions=int(native_first_verified) if arm==ORIGINAL else 0,actual_finish_witness=False,actual_execution_allowed=False)
            results.append(out);persist()
        if exception is not None:raise exception
        immutable();require(sha(path)==PROJECTED_SHA,'477_ARM_JOIN_PROFILE_SOURCE_CHANGED')
        for group in ['sources','protected','original408_preserve']:
            for filename,digest in getattr(meter,'p',{}).get(group,{}).items():require(sha(filename)==digest,'477_ARM_JOIN_SOURCE_MANIFEST_CHANGED')
    immutable();require(meter.b['ticks']-startticks<=2000 and meter.b['worlds']-startworlds==2,'477_WHOLE_COST')
    finished=len(results)==2 and all(x['own_model_finish'] for x in results)
    gain=None if not finished else [(results[0]['finish_ticks']['lo']-results[1]['finish_ticks']['hi'])/50,(results[0]['finish_ticks']['hi']-results[1]['finish_ticks']['lo'])/50]
    return dict(status='TWO_WHOLE_PARENTS_FINISHED' if finished else 'WHOLE_PARENT_OUTCOMES_RECORDED',policies=results,model_remaining_finish_gain_bracket_s=gain,model_ticks=meter.b['ticks']-startticks,model_worlds=meter.b['worlds']-startworlds,whole_arm_repeated=False,records_path=str(d/'whole_policyrecords-private.json'),results_path=str(d/'whole_policy-results.json'),actual_execution_allowed=False)
