"""492 single known-map native prefix + two natural witnesses.

No work runs on import. All native/model dependencies are injected from the
isolated491 opt-in graph. Frozen490 inputs are consumed without recomputation.
"""
import copy,hashlib,json,pickle,time,traceback,os
from dataclasses import asdict
from pathlib import Path
import numpy as np

RULE='492_FIXED490_OPTIN491_NATURAL_PREFIX_FIRST_QUARTER_TWO_WITNESSES'

class PreparationIneligible492(RuntimeError):
    def __init__(self,reason,details=None):
        super().__init__(reason);self.details=details


def prepare_case(case,meter,quota,root,*,fixed,pace,nodes,input_manifest_sha256,identity_check,runtime):
    """One assigned case, one reset, natural prefix+two witnesses; closes native.

    meter: begin_actual/end_actual, charge four kinds,
    guard/checkpoint. quota: native_dir and save/save_receipt. No ledger writes
    occur here outside meter.charge's authorized transaction.
    """
    # Dependencies are the parent's isolated opt-in491 module graph, never globals.
    ActualC=runtime.ActualC;NativeAuthority439=runtime.NativeAuthority439
    canonical_projection=runtime.canonical_projection;ExecutorDomainError=runtime.ExecutorDomainError
    make_env=runtime.make_env;complete_state=runtime.complete_state
    from_actual_full=runtime.from_actual_full;sensor=runtime.sensor;Trace=runtime.Trace
    GoalLedger=runtime.GoalLedger;ForecastLedger=runtime.ForecastLedger
    TechnicalStop=runtime.TechnicalStop;ResourceStop=runtime.ResourceStop
    fingerprint=runtime.fingerprint;sha=runtime.sha;require=runtime.require
    LedgerStop439=runtime.LedgerStop439
    binding=copy.deepcopy(runtime.binding)
    require(isinstance(binding,dict),'492_BINDING_OBJECT')
    for key in ('input_manifest_sha256','projection491_sha256','runtime492_sha256','line_sha256','nodes_sha256'):
        require(type(binding.get(key)) is str and len(binding[key])==64 and all(c in '0123456789abcdef' for c in binding[key]),'492_BINDING_'+key)
    require(binding['input_manifest_sha256']==input_manifest_sha256,'492_BINDING_INPUT')
    manifest_path=str(Path(runtime.input_manifest_path).resolve())
    require(sha(manifest_path)==input_manifest_sha256,'492_FROZEN_MANIFEST_SHA')
    class NativePrefix492(NativeAuthority439):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);self.global_step=0;self.nominal=None
        def commit_prefix_fact492(self):
            require(not self.halted and not self.awaiting_verification,'492_PREFIX_SEQUENCE')
            row,observed=self.observed_row();previous=self.ledger
            row.update(binding=copy.deepcopy(binding),step=self.global_step,nominal=copy.deepcopy(self.nominal),deadline_before=self.global_step-1+13-previous.age_actions)
            self._ledger=observed;self.rows.append(copy.deepcopy(row));self.dispatcher.consume(self.ticket);self.ticket=None;self.prepared=None
            return dict(row=row,ledger_before=asdict(previous),ledger_after=asdict(observed),own_native_fact=True,model_forecast_read=False,source_fidelity_qualified=False)
    slot=case['slot'];require(slot=='D492-A','492_SINGLE_SLOT')
    identity=case['case_identity_digest'];require(type(identity) is str and len(identity)==64,'492_ASSIGNED_IDENTITY_DIGEST')
    require(callable(identity_check) and type(input_manifest_sha256) is str and len(input_manifest_sha256)==64,'492_INPUT_IDENTITY_SOURCE')
    pace=np.asarray(pace,dtype=float);nodes=np.asarray(nodes,dtype=float).copy();nodes.setflags(write=False)
    require(np.isfinite(nodes).all() and nodes.ndim==1 and len(nodes)==len(fixed['line'])+1,'492_FIXED_INPUT_SHAPE')
    folder=Path(quota.native_dir)/slot;require(not folder.exists(),'492_ONCE_CASE_DIRECTORY');folder.mkdir(mode=0o700)
    fd=os.open(folder.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)
    counts=dict(slot_actions=0,slot_resets=0,slot_reset_raw=0,slot_action_raw=0);events=[];env=ctrl=native=trace=None;material=None;root_context=None;witness=None;witnesses=[];initial_ledger=None;root_full=None;root_actions=None;original_reset=original_step=None;mode='RESET';status='STARTED';error=None;technical=None;initial=None;identity_proof=None
    def put(name,value,receipt=True):
        path=folder/name
        require(isinstance(value,dict),'492_RECORD_DICTIONARY')
        value=copy.deepcopy(value)
        require('binding' not in value or value['binding']==binding,'492_RECORD_BINDING_MISMATCH')
        value['binding']=copy.deepcopy(binding)
        from retry.pilot420_json import json_ready
        encoded=(json.dumps(json_ready(value),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
        if len(encoded)>2*1024*1024:raise ResourceStop('492_NATIVE_RECORD_2MIB:'+name)
        if receipt:quota.save_receipt(path,value)
        else:quota.save(path,value)
        require(path.read_bytes()==encoded,'492_COMPLETE_RECORD_READBACK:'+name)
        return dict(path=str(path),sha256=sha(path))
    def native_trace_record():
        # Measure serialized bytes, not guessed row counts; preserve every field.
        from retry.pilot420_json import json_ready
        rows=[] if native is None else native.rows
        refs=[];chunk=[]
        def payload(candidate):
            return dict(schema='NATIVE_TRACE_ROWS492_V1',binding=copy.deepcopy(binding),rows=candidate)
        def size(candidate):
            return len((json.dumps(json_ready(payload(candidate)),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode())
        def flush():
            if chunk:
                ref=put('native-trace-rows-'+str(len(refs)+1)+'-private.json',payload(chunk))
                refs.append(dict(**ref,count=len(chunk)))
        for row in rows:
            if size([row])>1024*1024:raise ResourceStop('492_NATIVE_TRACE_SINGLE_ROW_1MIB')
            if chunk and size(chunk+[row])>1024*1024:
                flush();chunk=[]
            chunk.append(row)
        flush()
        return dict(schema='NATIVE_TRACE_CHUNKS492_V1',rows_refs=refs,row_count=len(rows),initial_actual_ledger=None if initial_ledger is None else asdict(initial_ledger),root_actual_ledger=None if root_context is None else root_context['actual_ledger'],witness_index=None if root_actions is None else root_actions+1)
    def charge(kind):
        key={'reset':'slot_resets','action':'slot_actions','reset_raw':'slot_reset_raw','action_raw':'slot_action_raw'}[kind]
        cap={'reset':1,'action':129,'reset_raw':64,'action_raw':516}[kind]
        if counts[key]>=cap:raise ResourceStop('492_NATIVE_CAP:'+slot+':'+kind)
        meter.guard();meter.charge(kind,slot);counts[key]+=1
        event=dict(binding=copy.deepcopy(binding),sequence=len(events)+1,kind=kind,charged_before_call=True,**counts);events.append(event)
        put('charge-'+str(event['sequence'])+'-before-call-private.json',event)
    def full_state(env,obs,memory):
        state=complete_state(env,obs,memory)
        from retry.pilot420_json import json_ready
        encoded=(json.dumps(json_ready(state),ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
        if len(encoded)>512*1024:raise ResourceStop('492_FULLSTATE_512KIB')
        return state
    meter.begin_actual()
    try:
        meter.guard();env=make_env();raw=env.unwrapped;original_reset,original_step=raw.reset,raw.step
        def guarded_reset(*args,**kwargs):
            if counts['slot_resets']!=0:raise TechnicalStop('492_INTERNAL_SECOND_RESET_FORBIDDEN')
            charge('reset');return original_reset(*args,**kwargs)
        def guarded_raw_step(*args,**kwargs):
            require(mode in ['RESET','ACTION'],'492_RAW_PHASE')
            charge('reset_raw' if mode=='RESET' else 'action_raw')
            before=float(getattr(raw,'t',0.) or 0.);result=original_step(*args,**kwargs)
            require(round((float(raw.t)-before)*50)==1,'492_RAW_SINGLE_TICK');return result
        raw.reset=guarded_reset;raw.step=guarded_raw_step
        obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});mode='GEOMETRY'
        require(counts['slot_resets']==1 and counts['slot_reset_raw']<=64,'492_RESET_ACCOUNTING')
        identity_proof=identity_check(case,env)
        initial=full_state(env,obs,dict(index=0,laststeer=0.))
        require(initial['observation_sha256']==runtime.expected_initial_observation_sha256,'492_INITIAL_OBSERVATION_EXACT_FIRST485')
        initial_ref=put('initial-full-private.json',initial)
        # No copied line/profile/nodes: the frozen490 artifact is referenced by hash.
        fixed_ref=put('fixed-plan-reference-private.json',dict(manifest_path=manifest_path,input_manifest_sha256=input_manifest_sha256,geometry_recomputed=False,profile_recomputed=False,P4_recomputed=False))
        nodes_digest=fingerprint(nodes.tolist());policy_digest=fingerprint(dict(rule=RULE,slot=slot,case_identity_digest=identity,nodes_digest=nodes_digest,input_manifest_sha256=input_manifest_sha256))
        nodes_ref=put('nodes-reference-private.json',dict(manifest_path=manifest_path,input_manifest_sha256=input_manifest_sha256,nodes_digest=nodes_digest,policy_digest=policy_digest))
        ctrl=ActualC(env,fixed,pace);before_injection=copy.deepcopy(ctrl.memory());ctrl.policy.nodes=nodes.copy();ctrl.policy.nodes.setflags(write=False)
        require(ctrl.memory()==before_injection,'492_P4_INJECTION_MEMORY')
        pre=sensor(env);arc=canonical_projection(fixed['line'],pre['pos'],pre['vel'],ctrl.phase())['arc'];L=sum(fixed['free_profile']['ds'])
        initial_ledger=GoalLedger.start(arc,round(pre['time']*50));native=NativePrefix492(env,ctrl,initial_ledger,fixed,charge_native=lambda:charge('action'));trace=Trace(lambda:raw.t);mode='ACTION'
        for step in range(1,130):
            meter.guard();require(not ctrl.policy.nodes.flags.writeable and fingerprint(ctrl.policy.nodes.tolist())==nodes_digest,'492_NATIVE_P4_CHANGED')
            tracker=raw.finish_line_tracker
            if root_context is None and ctrl.phase()=='FIRST_LAP' and native.ledger.progress_m>=L/4 and tracker.candidate_crossing_time_s is None and tracker.finish_time_s is None:
                root_actions=len(native.rows);require(root_actions<=127,'492_ROOT_TOO_LATE')
                root_full=full_state(env,obs,ctrl.memory());blob=pickle.dumps((__import__('random').getstate(),np.random.get_state()))
                root_context=dict(state=from_actual_full(root_full),before=copy.deepcopy(ctrl.memory()),ledger=asdict(ForecastLedger.fork(native.ledger)),actual_ledger=asdict(native.ledger),RNG=dict(global_pickle=blob,digest=hashlib.sha256(blob).hexdigest()),binding=copy.deepcopy(binding),slot=slot,case_identity_digest=identity,nodes_digest=nodes_digest,policy_digest=policy_digest)
                put('root-full-private.json',root_full);put('root-context-private.json',root_context)
            elif root_context is None and step==128:raise PreparationIneligible492('quarter_not_reached_by127_no_replacement')
            native.global_step=step;native.prepare_before_nominal();full_pre=full_state(env,obs,ctrl.memory());before=copy.deepcopy(ctrl.memory());nominal=ctrl.act(env);native.nominal=np.asarray(nominal,np.float32).tolist()
            put('action-'+str(step)+'-before-native-private.json',dict(full_pre_before_nominal=full_pre,full_pre_after_nominal=full_state(env,obs,ctrl.memory()),ledger=asdict(native.ledger),nominal=native.nominal,global_step=step,source_fidelity_claimed=False))
            result=native.dispatch(nominal,trace);obs=result[0];ticket=native.ticket
            full_post=full_state(env,obs,ctrl.memory());posts=copy.deepcopy(ticket.posts)
            postref=put('action-'+str(step)+'-after-native-private.json',dict(full_post=full_post,posts=posts,tires=copy.deepcopy(ticket.native_tires),raw_hull=copy.deepcopy(ticket.native_hulls),ticket_success=ticket.success,command=ticket.command,own_native_observation=True))
            fact=native.commit_prefix_fact492();fact.update(full_native_post_sha256=postref['sha256']);put('action-'+str(step)+'-fact-private.json',fact)
            row=fact['row']
            if row['safety'] or native.ledger.deadline_missed or row['ended'] or row['truncated'] or native.ledger.done or ctrl.phase() not in ['LAUNCH','FIRST_LAP'] or raw.finish_line_tracker.candidate_crossing_time_s is not None:raise PreparationIneligible492('unsafe_progress_or_terminal_common_prefix')
            require(np.array_equal(np.asarray(row['command'],np.float32),np.asarray(nominal,np.float32)) and row['memory_before']==before and row['nominal_memory_after']==ctrl.memory(),'492_NATURAL_ONCE_MEMORY_COMMAND')
            meter.checkpoint('NATIVE_COMMON_PREFIX',slot=slot,native_step=step,progress_m=native.ledger.progress_m,root_frozen=root_context is not None)
            if root_context is not None:
                witness=dict(binding=copy.deepcopy(binding),row=row,posts=posts,full_pre=full_pre,full_post=full_post,ledger_before=fact['ledger_before'],ledger_after=fact['ledger_after'],nominal=native.nominal,own_native_fact=True)
                witnesses.append(witness);put('witness-'+str(len(witnesses))+'-private.json',witness)
                if len(witnesses)==2:
                    status='NATIVE_ROOT_AND_TWO_WITNESSES_OBSERVED';break
        require(root_context is not None and len(witnesses)==2,'492_NO_ROOT_TWO_WITNESSES')
        witness=witnesses[0]
    except PreparationIneligible492 as exc:
        status='PREPARATION_INELIGIBLE';error=str(exc)
        if exc.details is not None:put('unsupported-geometry-private.json',exc.details)
    except ExecutorDomainError as exc:
        error=str(exc)
        if error in ['First_lap_arc_domain','Meaningful_negative_progress_domain','Invalid_finish_confirmation_corridor','Zero_target_outside_launch','Launch_outside_first_lap']:
            status='PREPARATION_INELIGIBLE'
            put('phase-ineligible-private.json',dict(error=error,no_replacement=True))
        else:
            status='TECHNICAL_STOP';technical=exc
            put('stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc(),no_retry=True))
    except LedgerStop439 as exc:
        error=str(exc)
        if error in ['ACTUAL_PRE_SAFETY','ACTUAL_NEW_OBSTACLE_CONTACT','ACTUAL_RAW_CONTACT_OR_COLLISION']:
            status='PREPARATION_INELIGIBLE'
            put('unsafe-prefix-private.json',dict(error=error,own_post_evidence_retained=True,no_replacement=True))
        else:
            status='TECHNICAL_STOP';technical=exc
            put('stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc(),no_retry=True))
    except BaseException as exc:
        status='TECHNICAL_STOP';error=type(exc).__name__+': '+str(exc);technical=exc
        put('stop-private.json',dict(status=status,error=error,traceback=traceback.format_exc(),no_retry=True))
    finally:
        cleanup=dict(native_world_constructed=env is not None,bodies_before=None,joints_before=None,bodies_after=None,joints_after=None)
        if trace:trace.disable()
        if env:
            try:
                raw=env.unwrapped;cleanup.update(bodies_before=len(raw.world.bodies),joints_before=len(raw.world.joints))
                if original_reset is not None:raw.reset=original_reset
                if original_step is not None:raw.step=original_step
                env.close()
                for joint in list(raw.world.joints):raw.world.DestroyJoint(joint)
                for body in list(raw.world.bodies):raw.world.DestroyBody(body)
                cleanup.update(bodies_after=len(raw.world.bodies),joints_after=len(raw.world.joints))
                require(cleanup['bodies_after']==cleanup['joints_after']==0,'492_NATIVE_TEARDOWN')
            except BaseException as exc:
                if technical is None:technical=exc;status='TECHNICAL_STOP';error=type(exc).__name__+': '+str(exc)
        try:
            put('cleanup-private.json',cleanup)
            journal_ref=put('native-charge-journal-private.json',dict(slot=slot,case_identity_digest=identity,events=events,counts=counts))
            trace_ref=put('native-trace-private.json',native_trace_record())
            put('preparation-result-private.json',dict(status=status,error=error,slot=slot,case_identity_digest=identity,counts=counts,cleanup=cleanup,source_gate_passed=False))
        finally:meter.end_actual()
    if technical is not None:raise technical
    if status!='NATIVE_ROOT_AND_TWO_WITNESSES_OBSERVED':return dict(status=status,error=error,slot=slot,case_identity_digest=identity,source_gate_passed=False)
    root_context_ref=dict(path=str(folder/'root-context-private.json'),sha256=sha(folder/'root-context-private.json'));root_full_ref=dict(path=str(folder/'root-full-private.json'),sha256=sha(folder/'root-full-private.json'));witness_ref=dict(path=str(folder/'witness-1-private.json'),sha256=sha(folder/'witness-1-private.json'))
    proof=dict(schema='NATIVE_PREFIX_ROOT492_V1',binding=copy.deepcopy(binding),stage=492,passed=True,source_gate_passed=False,slot=slot,case_identity_digest=identity,input_manifest_sha256=input_manifest_sha256,witness_count=2,p4_nodes_digest=nodes_digest,profile_sha256=nodes_ref['sha256'],policy_digest=policy_digest,actions=root_actions,native_actions_including_witness=counts['slot_actions'],initial_actual_ledger=asdict(initial_ledger),root_actual_ledger=root_context['actual_ledger'],root_context_path=root_context_ref['path'],root_context_sha256=root_context_ref['sha256'],root_state_digest=fingerprint(root_context['state']),root_memory_digest=fingerprint(root_context['before']),root_RNG_digest=root_context['RNG']['digest'],native_trace_path=trace_ref['path'],native_trace_sha256=trace_ref['sha256'],native_charge_journal_path=journal_ref['path'],native_charge_journal_sha256=journal_ref['sha256'],witness_path=witness_ref['path'],witness_sha256=witness_ref['sha256'],witnesses_refs=[dict(path=str(folder/('witness-'+str(i)+'-private.json')),sha256=sha(folder/('witness-'+str(i)+'-private.json'))) for i in (1,2)],root_full_path=root_full_ref['path'],root_full_sha256=root_full_ref['sha256'],fixed_plan_path=fixed_ref['path'],fixed_plan_sha256=fixed_ref['sha256'],nodes_path=nodes_ref['path'],nodes_sha256=nodes_ref['sha256'])
    proof_ref=put('prefix-root-proof-private.json',proof)
    return dict(status=status,binding=copy.deepcopy(binding),slot=slot,case_identity_digest=identity,context=root_context,state=root_context['state'],before=root_context['before'],ledger=ForecastLedger(**root_context['ledger']),actual_ledger=GoalLedger(**root_context['actual_ledger']),actual_root_ledger=root_context['actual_ledger'],root_context_sha256=root_context_ref['sha256'],RNG=root_context['RNG'],fixed=fixed,pace=pace.tolist(),projected_nodes=nodes.tolist(),profile_sha256=nodes_ref['sha256'],nodes_digest=nodes_digest,policy_digest=policy_digest,prefixproof=proof,prefixproof_path=proof_ref['path'],prefixproof_sha256=proof_ref['sha256'],witnesses=witnesses,witness=witness,witness_row=witness['row'],witness_posts=witness['posts'],witness_path=witness_ref['path'],native_closed=True,source_gate_passed=False,identity_verification=identity_proof,counts=counts)
