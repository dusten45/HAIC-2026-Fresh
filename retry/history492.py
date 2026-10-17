"""492 root authority adapter for an isolated clone of the full485 history gate.

Only root registration changes: reference-owned490 input, two native witnesses
and492 source/warm qualification. The finite-policy/replay validator is reused
without changing its candidate, ranking, pending or safety rules.
"""
import copy
import hashlib
import sys
from dataclasses import asdict,fields
from pathlib import Path
import numpy as np

PREFIX_SCHEMA492='NATIVE_PREFIX_ROOT492_V1'
ROOT_SCHEMA492='SOURCE_QUALIFIED_NATIVE_PREFIX_ROOT492_V1'


def install(runtime):
    """Call before aliasing history485 for online485; return that private clone."""
    module=runtime.import_module('retry.history485')
    if getattr(module,'_installed492',False):return module
    if module is sys.modules.get('retry.history485'):
        raise RuntimeError('492_HISTORY_REQUIRES_ISOLATED_CLONE')
    require=module.require;checked=module.checked;same=module.same;digest=module.digest;bits=module.bits
    original_type=module.NativePrefix485;full_validate=module.validate_history
    names=[f.name for f in fields(original_type)]
    def imported(name):return runtime.import_module('retry.'+name)
    GoalLedger=imported('planner419').GoalLedger
    ForecastLedger=imported('planner419_model_ledger').ForecastLedger
    row_candidate=imported('ledger439').row_candidate
    from_actual_full=imported('terminal410_model').from_actual_full
    def bound(value):
        require(type(value) is dict and value.get('binding')==runtime.binding,'492_runtime_binding')
    class NativePrefix492(original_type):
        @classmethod
        def parse(cls,value,*,qualified=False):
            require(type(value) is dict and all(name in value for name in names),'492_prefix_fields')
            bound(value);p=cls(**{name:value[name] for name in names})
            require(p.schema==(ROOT_SCHEMA492 if qualified else PREFIX_SCHEMA492),'492_prefix_schema')
            require(type(p.stage) is int and p.stage==492 and p.passed is True and p.slot=='D492-A','492_stage_slot')
            require(type(p.actions) is int and 1<=p.actions<=127,'492_root_action_cap')
            require(value.get('witness_count')==2 and type(p.native_actions_including_witness) is int and p.native_actions_including_witness==p.actions+2<=129,'492_two_witness_cap')
            require(value.get('input_manifest_sha256')==runtime.binding['input_manifest_sha256'],'492_input_binding')
            for name in names:
                if name.endswith(('digest','sha256')):
                    h=getattr(p,name);require(type(h) is str and len(h)==64 and all(c in '0123456789abcdef' for c in h),'492_hash:'+name)
                elif name.endswith('_path'):require(type(getattr(p,name)) is str and bool(getattr(p,name)),'492_path:'+name)
            require(type(p.initial_actual_ledger) is dict and type(p.root_actual_ledger) is dict,'492_actual_ledgers')
            return p
    def source_gate(p,gate):
        bound(gate)
        require(gate.get('stage')==492 and gate.get('passed') is True,'492_source_not_passed')
        for key,value in [('slot',p.slot),('case_identity_digest',p.case_identity_digest),('p4_nodes_digest',p.p4_nodes_digest),('root_context_sha256',p.root_context_sha256),('root_state_digest',p.root_state_digest)]:
            require(gate.get(key)==value,'492_source_binding:'+key)
        require(gate.get('new_worlds')==3 and gate.get('new_charged_ticks')==16 and gate.get('wrapper_holds')==4 and gate.get('independent_cold_first_exact') is True and gate.get('genuine_warm_second_native_qualified') is True,'492_source_warm_scope')
        copies=gate.get('copies');require(type(copies) is list and len(copies)==3,'492_source_copies')
        require([r['repetition'] for r in copies]==[1,2,'warm'] and [r['holds'] for r in copies]==[1,1,2],'492_source_hold_counts')
        for rec in copies:checked(rec['path'],rec['sha256'])
    def finish_root_proof(prefix_proof,source_gate_path,source_gate_sha256):
        p=NativePrefix492.parse(prefix_proof);ctx=checked(p.root_context_path,p.root_context_sha256)
        source_gate(p,checked(source_gate_path,source_gate_sha256))
        result=copy.deepcopy(prefix_proof)
        result.update(schema=ROOT_SCHEMA492,prefix_schema=PREFIX_SCHEMA492,source_gate_path=str(source_gate_path),source_gate_sha256=source_gate_sha256,state_digest=p.root_state_digest,before_memory_digest=p.root_memory_digest,ledger_digest=digest(ctx['ledger']),source_gate_passed=True,actual_execution_allowed=False,actual_DONE_allowed=False)
        return result
    def charges(journal,p,raw_ticks):
        bound(journal)
        require(journal.get('slot')==p.slot and journal.get('case_identity_digest')==p.case_identity_digest,'492_charge_identity')
        events=journal.get('events');require(type(events) is list and bool(events),'492_charge_events')
        counts=dict(action=0,reset=0,action_raw=0,reset_raw=0)
        labels=dict(action='slot_actions',reset='slot_resets',action_raw='slot_action_raw',reset_raw='slot_reset_raw')
        for sequence,event in enumerate(events,1):
            bound(event);kind=event.get('kind')
            require(kind in counts and event.get('sequence')==sequence and event.get('charged_before_call') is True,'492_charge_sequence')
            counts[kind]+=1
            require(all(type(event.get(field)) is int and event[field]==counts[key] for key,field in labels.items()),'492_charge_counters')
            require(counts['reset']==1 and counts['action']<=129 and counts['reset_raw']<=64 and counts['action_raw']<=4*counts['action'],'492_charge_caps')
            if kind=='action':require(counts['reset_raw']>0,'492_action_before_reset_raw')
            if kind=='action_raw':require(counts['action']>0,'492_raw_before_action')
        require(counts['action']==p.native_actions_including_witness and counts['reset']==1 and 1<=counts['reset_raw']<=64 and counts['action_raw']==raw_ticks,'492_charge_totals')
        require(all(journal.get('counts',{}).get(field)==counts[key] for key,field in labels.items()),'492_charge_final_counts')
    def trace_rows(trace):
        bound(trace);require(trace.get('schema')=='NATIVE_TRACE_CHUNKS492_V1','492_trace_schema')
        refs=trace.get('rows_refs');require(type(refs) is list and bool(refs),'492_trace_refs')
        rows=[];seen=set()
        for ref in refs:
            require((ref['path'],ref['sha256']) not in seen,'492_trace_repeated_chunk');seen.add((ref['path'],ref['sha256']))
            chunk=checked(ref['path'],ref['sha256']);bound(chunk)
            require(chunk.get('schema')=='NATIVE_TRACE_ROWS492_V1' and type(chunk.get('rows')) is list and len(chunk['rows'])==ref['count'] and ref['count']>0,'492_trace_chunk')
            rows.extend(chunk['rows'])
        require(len(rows)==trace.get('row_count'),'492_trace_total')
        return rows
    def authenticate_root492(proof,root_state,initial_ledger,before_memory,expected_line=None):
        p=NativePrefix492.parse(proof,qualified=True)
        require(proof.get('prefix_schema')==PREFIX_SCHEMA492 and proof.get('source_gate_passed') is True and proof.get('actual_execution_allowed') is False and proof.get('actual_DONE_allowed') is False,'492_authority_scope')
        source_gate(p,checked(proof['source_gate_path'],proof['source_gate_sha256']))
        ctx=checked(p.root_context_path,p.root_context_sha256);bound(ctx)
        for key,value in [('slot',p.slot),('case_identity_digest',p.case_identity_digest),('nodes_digest',p.p4_nodes_digest),('policy_digest',p.policy_digest)]:require(ctx.get(key)==value,'492_context_identity:'+key)
        actual=GoalLedger(**p.root_actual_ledger);source=ctx['state']
        require(type(actual.done) is bool and type(actual.deadline_missed) is bool and not actual.done and not actual.deadline_missed,'492_root_stopped')
        require(same(ctx['actual_ledger'],p.root_actual_ledger),'492_context_actual_ledger')
        fork=asdict(ForecastLedger.fork(actual));require(same(ctx['ledger'],fork) and same(initial_ledger,fork),'492_exact_forecast_fork')
        require(proof['state_digest']==p.root_state_digest==digest(source),'492_root_state_digest')
        require(proof['before_memory_digest']==p.root_memory_digest==digest(ctx['before']) and same(before_memory,ctx['before']),'492_root_memory')
        require(proof['ledger_digest']==digest(initial_ledger),'492_root_ledger_digest')
        rng=ctx['RNG'];require(type(rng['global_pickle']) is bytes and hashlib.sha256(rng['global_pickle']).hexdigest()==rng['digest']==p.root_RNG_digest,'492_root_RNG')
        full=checked(p.root_full_path,p.root_full_sha256);bound(full)
        require(same(from_actual_full(full),source),'492_full_to_model_root')
        local=copy.deepcopy(root_state);saved=copy.deepcopy(source)
        for value in (local,saved):value['physical'].pop('source_world_contacts',None)
        require(same(local,saved),'492_local_root_not_native')
        require(before_memory['C']['phase']=='FIRST_LAP' and source['finish_tracker']['candidate_crossing_time_s'] is None and source['finish_tracker']['finish_time_s'] is None,'492_root_phase_event')
        fixed_ref=checked(p.fixed_plan_path,p.fixed_plan_sha256);nodes_ref=checked(p.nodes_path,p.nodes_sha256)
        for ref in (fixed_ref,nodes_ref):
            bound(ref);require(ref.get('input_manifest_sha256')==runtime.binding['input_manifest_sha256'],'492_reference_manifest')
            require(Path(ref['manifest_path']).resolve()==Path(runtime.input_manifest_path).resolve(),'492_reference_manifest_path')
        require(all(fixed_ref.get(k) is False for k in ('geometry_recomputed','profile_recomputed','P4_recomputed')),'492_no_regeneration')
        require(module.file_sha(runtime.input_manifest_path)==runtime.binding['input_manifest_sha256'],'492_manifest_file_hash')
        fixed,pace,nodes=imported('executor490_input').load(runtime.input_manifest_path)
        require(imported('executor490_input').array_sha(fixed['line'])==runtime.binding['line_sha256'] and imported('executor490_input').array_sha(nodes)==runtime.binding['nodes_sha256'],'492_reference_array_binding')
        if expected_line is not None:require(same(np.asarray(expected_line).tolist(),fixed['line'].tolist()),'492_other_line')
        require(nodes_ref.get('nodes_digest')==p.p4_nodes_digest==digest(nodes.tolist()) and nodes_ref.get('policy_digest')==p.policy_digest and p.profile_sha256==p.nodes_sha256,'492_P4_reference')
        trace=checked(p.native_trace_path,p.native_trace_sha256);rows=trace_rows(trace)
        require(len(rows)==p.native_actions_including_witness and trace['witness_index']==p.actions+1,'492_prefix_two_witness_count')
        require(same(trace['initial_actual_ledger'],p.initial_actual_ledger) and same(trace['root_actual_ledger'],p.root_actual_ledger),'492_trace_ledger_endpoints')
        line=fixed['line'];L=float(sum(fixed['free_profile']['ds']));old=GoalLedger(**p.initial_actual_ledger)
        require(not old.done and not old.deadline_missed,'492_initial_stopped')
        previous=None;before_witness=[];after_witness=[]
        for index,row in enumerate(rows,1):
            bound(row);require(row['step']==index and bits(row['command'])==bits(row['nominal']),'492_natural_P4_command')
            require(row['memory_before']['C']['phase'] in ('LAUNCH','FIRST_LAP') and row['nominal_memory_after']['C']['phase'] in ('LAUNCH','FIRST_LAP'),'492_native_prefix_phase')
            require(row['raw_ticks']==4 and not row['safety'] and not row['completed'] and not row['ended'] and not row['truncated'],'492_native_unsafe_terminal_partial')
            if previous is not None:require(same(row['pre'],previous['post']) and same(row['memory_before'],previous['nominal_memory_after']),'492_native_observation_memory_chain')
            if index==p.actions+1:
                require(same(asdict(old),p.root_actual_ledger) and same(row['memory_before'],ctx['before']),'492_before_witness_root_join')
                h=source['physical']['hull'];require(row['pre']['time']==source['physical']['actual_time'] and row['pre']['pos']==h['position'] and row['pre']['vel']==h['velocity'],'492_witness_root_hull_clock')
            if index>p.actions:before_witness.append(asdict(old))
            candidate,_=row_candidate(old,row,line,L)
            require(not candidate.done and not candidate.deadline_missed,'492_native_ledger_stopped')
            if index<p.actions and row['nominal_memory_after']['C']['phase']=='FIRST_LAP':require(candidate.progress_m<L/4,'492_not_earliest_quarter')
            if index==p.actions:require(candidate.progress_m>=L/4 and same(asdict(candidate),p.root_actual_ledger),'492_quarter_root')
            if index>p.actions:after_witness.append(asdict(candidate))
            old=candidate;previous=row
        refs=proof.get('witnesses_refs');require(type(refs) is list and len(refs)==2,'492_witness_refs')
        require(refs[0]['path']==p.witness_path and refs[0]['sha256']==p.witness_sha256,'492_first_witness_alias')
        witnesses=[]
        for i,ref in enumerate(refs):
            w=checked(ref['path'],ref['sha256']);bound(w)
            require(w.get('own_native_fact') is True and same(w['row'],rows[p.actions+i]),'492_witness_own_fact')
            require(same(w['ledger_before'],before_witness[i]) and same(w['ledger_after'],after_witness[i]),'492_witness_ledger_join')
            require(bits(w['nominal'])==bits(rows[p.actions+i]['nominal']),'492_witness_nominal')
            witnesses.append(w)
        # The root full receipt has a top-level provenance envelope added by
        # the writer; nested witness full snapshots retain their original schema.
        full_payload=copy.deepcopy(full);full_payload.pop('binding',None)
        require(same(witnesses[0]['full_pre'],full_payload) and same(witnesses[1]['full_pre'],witnesses[0]['full_post']),'492_genuine_native_warm_full_join')
        charges(checked(p.native_charge_journal_path,p.native_charge_journal_sha256),p,sum(row['raw_ticks'] for row in rows))
        return dict(stage=492,scope='SOURCE_WARM_QUALIFIED_NATIVE_PREFIX_ROOT',slot=p.slot,actions=p.actions,
                    case_identity_digest=p.case_identity_digest,p4_nodes_digest=p.p4_nodes_digest,
                    root_context_sha256=p.root_context_sha256,binding=copy.deepcopy(runtime.binding),
                    actual_DONE_allowed=False,actual_execution_allowed=False)
    def validate_history(*args,**kwargs):
        require(kwargs.get('historical',False) is False,'492_no_historical_fixture_authority')
        result=full_validate(*args,**kwargs);result['stage']=492;result['binding']=copy.deepcopy(runtime.binding)
        return result
    module.NativePrefix485=NativePrefix492
    module.PREFIX_SCHEMA485=PREFIX_SCHEMA492;module.ROOT_SCHEMA485=ROOT_SCHEMA492
    module.authenticate_root485=authenticate_root492;module.authenticate_root492=authenticate_root492
    module._source_gate485=source_gate;module._charges485=charges
    module.finish_root_proof=finish_root_proof;module.validate_history=validate_history
    module._installed492=True
    return module
