"""One H6 ranking-only falsification; inherited physics and finite pedal domain."""
import copy,pickle,random
from dataclasses import asdict
import numpy as np
import retry.online481 as base
from retry.pilot420_backend import snapshot,fingerprint,rnghash,model_ledger_view
from retry.planner419_model_ledger import ForecastLedger
from retry.law477 import ReferencePolicy477,ALLOCATED,PROJECTED_SHA
from retry.live485 import allocate_current,inputs_current
from retry.history485 import validate_history,authenticate_root485,checked,same
from retry.io481 import read
from retry.loss389_analyze import save,sha
from retry.receipt421_io import save_receipt
from retry.ledger439 import require
from retry.executor397 import canonical_projection

def max_guard_error(row,line):
    q=row['predicted'];phase=row['memory_after']['C']['phase']
    points=[(h['origin_position'],h['origin_linear_velocity']) for h in row['raw_hull']]+[(q['position'],q['velocity'])]
    require(len(points)==q['raw_ticks']+1 and 1<=q['raw_ticks']<=4,'485_RAW_MARGIN_COVERAGE')
    return max(canonical_projection(line,p,v,phase)['path_error_m'] for p,v in points)

def rank(option,arm):
    require(arm in ('control','variant'),'485_RANK_ARM')
    tail=(option['M80'],-option['active_pedal'])
    return tail if arm=='control' else (option['max_guard_path_error_m'],)+tail

def opportunity(queries):
    out=[]
    for query in queries:
        options=query['options'];eligible=[k for k,v in options.items() if v['valid']]
        if not eligible:continue
        a=min(eligible,key=lambda k:rank(options[k],'control'))
        b=min(eligible,key=lambda k:rank(options[k],'variant'))
        out.append(dict(control_key=a,variant_key=b,disagreement=a!=b,same_context=True))
    return out

def decision(control,variant,exposed,rootmargin):
    n=min(control['actions'],variant['actions'])
    equal=bool(n and all(z==4 for z in control['raw_lengths'][:n]+variant['raw_lengths'][:n]))
    cm=min(control['margins_m'][:n]) if equal else None
    vm=min(variant['margins_m'][:n]) if equal else None
    gain=None if not equal else vm-cm
    adverse=bool(exposed and (variant['status']=='UNSAFE' or
        (variant['status']=='EMPTY_FINITE_CANDIDATE_DOMAIN' and variant['raw_ticks'] in control.get('admissible_query_raw_times',[])) or
        (variant.get('progress_deadline_missed') and not control.get('progress_deadline_missed')) or
        (gain is not None and gain<-.25)))
    dominated=cm is not None and rootmargin-cm<=.25
    success=bool(not adverse and exposed and not dominated and equal and gain>.25 and variant['status']=='H6_SAFE_CENSORED' and variant['actions']==6 and variant['safe_own_actions']==6 and not variant.get('progress_deadline_missed'))
    return dict(verdict='REJECT' if adverse else 'BOUNDED_CASE_GATE_PASSED' if success else 'NO_INFORMATION',success=success,reject=adverse,ranking_opportunity=exposed,common_executed_own_actions=n,same_elapsed_common_prefix=equal,control_common_min_margin_m=cm,variant_common_min_margin_m=vm,common_margin_gain_m=gain,root_dominates_identifiability=dominated)


def history(c,memory=None):
    if not c.rows:
        mem=c.ctrl.memory() if memory is None else memory
        proof=checked(c.meter.p['root_proof_path'],c.meter.p['root_proof_sha256'])
        root=authenticate_root485(proof,c.stream.root_state,c.stream.root_ledger,mem)
        require(base.physical_identity(snapshot(c.m))==base.physical_identity(c.stream.root_state) and same(asdict(c.ledger),c.stream.root_ledger),'485_EMPTY_NO_OWN_MUTATION')
        return dict(stage=485,actions=0,raw_ticks=0,pending=False,own_model_finished=False,physical_safe=True,progress_deadline_missed=False,scope='ROOT_AUTHENTICATED_ZERO_OWN_EMPTY_QUERY',root_proof=bool(root is not None))
    return validate_history(c.stream.root_state,c.stream.root_ledger,c.stream.posts,c.stream.actions,c.authorizations481,snapshot(c.m),c.ctrl.memory() if memory is None else memory,asdict(c.ledger),c.fixed['line'],c.policy481)

def prepare(c,index):
    require(c.status=='ACTIVE' and c.ctrl.phase() in ('FIRST_LAP','FINISH_CONFIRM'),'485_CURRENT_PHASE')
    state=snapshot(c.m);before=copy.deepcopy(c.ctrl.memory());ledger=asdict(c.ledger);rh=rnghash();nodes=c.ctrl.policy.nodes.copy()
    if state['finish_tracker']['candidate_crossing_time_s'] is not None:history(c)
    nominal=np.asarray(c.ctrl.act(c.m),np.float32).copy();after=copy.deepcopy(c.ctrl.memory())
    require(after['C']['phase'] in ('FIRST_LAP','FINISH_CONFIRM'),'485_SOURCE_PHASE_AFTER')
    require(snapshot(c.m)==state and asdict(c.ledger)==ledger and rnghash()==rh and np.array_equal(c.ctrl.policy.nodes,nodes),'485_NOMINAL_MUTATED_ROOT')
    qstar=allocate_current(c,nominal,index);number=c.meter.allocator_calls;c.meter.allocation_pending=None
    require(snapshot(c.m)==state and c.ctrl.memory()==after,'485_ALLOCATOR_MUTATION')
    path=c.meter.d/f'context-{number:03d}-private.json'
    ctx=dict(state=state,before=before,after=after,ledger=ledger,RNG=dict(global_pickle=pickle.dumps((random.getstate(),np.random.get_state())),digest=rnghash()),nominal=nominal.tolist(),qstar=qstar.tolist(),allocation_number=number,index=index,label=c.label,wheels=inputs_current(c.m),nominal_calls=1,ranking_arm=c.arm485)
    for kind in ('input','proof'):
        source=c.meter.d/f'allocation-{kind}-{number:03d}.json';ctx['allocation_'+kind+'_path']=str(source);ctx['allocation_'+kind+'_sha256']=sha(source)
    save_receipt(path,ctx);ctx.update(context_path=str(path),context_sha256=sha(path));return ctx

def select(c,ctx,binding,first_expected=None):
    unchanged=base.stamp(c);cmds,active=base.commands(ctx['nominal'],ctx['qstar']);options={};traces={};open_child=None
    try:
        for i,(key,opt) in enumerate(cmds.items()):
            child=base.fresh(c,ctx,f'{c.label}_q{ctx["index"]+1:02d}_c{i}',binding);open_child=child
            row=base.apply(child,ctx,opt['command'],'485_candidate_once')
            traces[key]=dict(signature=child.signature(),row=copy.deepcopy(row),posts=copy.deepcopy(child.stream.posts),RNG=rnghash())
            ok=base.valid(child);path,digest=base.closed(child);open_child=None
            options[key]=dict(command=opt['command'].tolist(),aliases=opt['aliases'],valid=ok,M80=base.score(row),max_guard_path_error_m=max_guard_error(row,c.fixed['line']),active_pedal=0. if active is None else float(opt['command'][active]),first_path=path,first_sha256=digest)
            require(base.stamp(c)==unchanged,'485_FORECAST_PARENT_MUTATION')
        if first_expected:
            # Existing cold source traces, not an assertion that cold is warm.
            require(set(options)==set(first_expected['options']),'485_FIRST_SOURCE_DOMAIN')
            for key,opt in options.items():
                old=first_expected['options'][key];require(opt['command']==old['command'],'485_FIRST_SOURCE_COMMAND')
                base.fidelity(traces[key]['row'],old['row']);base.raw_flags(traces[key]['posts'],old['posts'])
            require(ctx['nominal']==first_expected['nominal'] and ctx['qstar']==first_expected['qstar'] and ctx['after']==first_expected['after'],'485_FIRST_NOMINAL_MEMORY_QSTAR')
        eligible=[k for k,v in options.items() if v['valid']]
        if not eligible:
            save(c.meter.d/f'empty-{ctx["allocation_number"]:03d}-private.json',dict(options=options,parent_unchanged=True,unselected_not_repeated=True,ranking_arm=c.arm485))
            return None,dict(status='EMPTY_FINITE_CANDIDATE_DOMAIN',options=options)
        chosen=min(eligible,key=lambda k:rank(options[k],c.arm485));command=cmds[chosen]['command']
        if first_expected:require(chosen==first_expected['selected'][c.arm485],'485_FIRST_RANK_SCOPE_MISMATCH_NO_OVERRIDE')
        child=base.fresh(c,ctx,f'{c.label}_q{ctx["index"]+1:02d}_selected_repeat',binding);open_child=child
        row=base.apply(child,ctx,command,'485_selected_independent_repeat')
        repeated=dict(signature=child.signature(),row=copy.deepcopy(row),posts=copy.deepcopy(child.stream.posts),RNG=rnghash())
        require(repeated==traces[chosen],'485_SELECTED_REPEAT_NOT_EXACT')
        path,digest=base.closed(child);open_child=None
        require(base.stamp(c)==unchanged,'485_REPEAT_PARENT_MUTATION')
        proof=dict(first_path=options[chosen]['first_path'],first_sha256=options[chosen]['first_sha256'],repeat_path=path,repeat_sha256=digest,full_trace_exact=True)
        auth=base.base_auth(c,ctx,command,cmds,chosen,'online');auth.update(ranking_arm=c.arm485,root_history_proof_path=c.meter.p['root_proof_path'],root_history_proof_sha256=c.meter.p['root_proof_sha256'],selected_repeat_exact=True,repeat_path=path,repeat_sha256=digest)
        auth=base.persist_decision(c,ctx,auth,options,proof)
        return dict(command=command,auth=auth,trace=traces[chosen]),dict(status='SELECTED_REPEAT_EXACT',options=options,selected=chosen,aliases=cmds[chosen]['aliases'])
    finally:
        if open_child and not open_child.closed:base.closed(open_child)

def execute(meter,material):
    fixed=material['fixed'];pace=np.asarray(material['pace']);ctx0=material['context'];line=fixed['line']
    binding=ReferencePolicy477(ALLOCATED,material['projected_nodes'],material['profile_sha256'])
    policies={arm:fingerprint(dict(stage=485,arm=arm,contract=meter.p['contract_sha256'],case=material['case_identity_digest'],reference=binding.nodes_digest,root=meter.p['root_proof_sha256'],sources=fingerprint(meter.p['semantic_sources']))) for arm in ('control','variant')}
    results=[];details=[];pairs={};live=None
    try:
        for arm in material['arm_order']:
            branch=[]
            for repetition,limit in ((1,6),(2,6),('held',1)):
                py,npr=pickle.loads(ctx0['RNG']['global_pickle']);random.setstate(py);np.random.set_state(npr)
                label=f'{material["slot"]}_{arm}_{repetition}';full=ForecastLedger(**ctx0['ledger'])
                meter.capture_inputs(ctx0['state'],ctx0['before'],full,label+'_inputs',gate='485_AUTHENTICATED_ROOT121_NEW_LOCAL_HISTORY')
                c=base.Shadow(meter,copy.deepcopy(ctx0['state']),copy.deepcopy(ctx0['before']),model_ledger_view(full),fixed,pace,label,'nominal',world_tag='485_parent',full_ledger=ctx0['ledger'],confirmation_phase=ctx0['before']['C']['phase']);live=c
                base.setup(c,binding,policies[arm]);c.arm485=arm;rootstate=snapshot(c.m)
                require(base.physical_identity(rootstate)==base.physical_identity(ctx0['state']) and c.ctrl.memory()==ctx0['before'] and asdict(c.ledger)==ctx0['ledger'],'485_LOCAL_ROOT_EXACT')
                queries=[];first=None;undispatched=None
                for index in range(limit):
                    if c.status!='ACTIVE':break
                    ctx=prepare(c,index);query_raw_time=sum(r['predicted']['raw_ticks'] for r in c.rows)
                    selected,summary=select(c,ctx,binding)
                    if selected is None:
                        c.status='EMPTY_FINITE_CANDIDATE_DOMAIN';c.error='all_existing_candidates_ineligible';undispatched=dict(context_sha256=ctx['context_sha256'],allocation_number=ctx['allocation_number'],committed_before_memory_digest=fingerprint(ctx['before']),prepared_after_memory_digest=fingerprint(ctx['after']),actual_controller_memory_digest=fingerprint(c.ctrl.memory()),own_dispatched=False)
                        queries.append(dict(local_query=index+1,query_raw_time=query_raw_time,**summary));break
                    row,join=base.own(c,ctx,selected)
                    queries.append(dict(local_query=index+1,query_raw_time=query_raw_time,status=c.status,selected_aliases=summary['aliases'],options=summary['options'],own_M80=base.score(row),own_guard_error_m=max_guard_error(row,line),source_join=join))
                    if index==0:first=dict(row=copy.deepcopy(row),posts=copy.deepcopy(c.stream.posts),state=snapshot(c.m),memory=c.ctrl.memory(),ledger=asdict(c.ledger),RNG=rnghash())
                    meter.checkpoint('OWN_TRANSITION',arm=arm,repetition=repetition,own_actions=len(c.rows),parent_status=c.status)
                if c.status=='ACTIVE':c.status='HELD_FIRST_SAFE' if repetition=='held' else 'H6_SAFE_CENSORED';c.error=None
                hist=history(c,ctx['before'] if undispatched else None)
                hist['memory_scope']='COMMITTED_BEFORE_UNDISPATCHED_PREPARATION' if undispatched else 'ACTUAL_LOCAL_CONTROLLER'
                physical_signature=c.signature();post_signature=fingerprint(c.stream.posts)
                packet=dict(arm=arm,repetition=repetition,status=c.status,error=c.error,actions=len(c.rows),safe_own_actions=sum(not r['safety'] for r in c.rows),raw_ticks=sum(r['predicted']['raw_ticks'] for r in c.rows),raw_lengths=[r['predicted']['raw_ticks'] for r in c.rows],margins_m=[3-max_guard_error(r,line) for r in c.rows],own_M80=[base.score(r) for r in c.rows],signature=physical_signature,post_signature=post_signature,first=first,history_proof=hist,undispatched=undispatched,official_own_finish=c.status=='FINISHED',progress_deadline_missed=c.ledger.deadline_missed,query_count=len(queries),admissible_query_raw_times=[q['query_raw_time'] for q in queries if any(o['valid'] for o in q['options'].values())])
                if repetition==2:require(packet['signature']==branch[0]['signature'] and packet['post_signature']==branch[0]['post_signature'],'485_INDEPENDENT_BRANCH_REPEAT')
                if repetition=='held':
                    require((first is not None and first==branch[0]['first']) or (first is None and branch[0]['first'] is None and packet['signature']==branch[0]['signature'] and packet['post_signature']==branch[0]['post_signature']),'485_HELD_FIRST_SOURCE_JOIN')
                branch.append(packet);details.append(dict(arm=arm,repetition=repetition,queries=queries,first=first));results.append(packet)
                save(meter.d/'branch-results-private.json',results);save(meter.d/'query-details-private.json',details)
                base.closed(c);live=None;meter.checkpoint('BRANCH_CLOSED',arm=arm,repetition=repetition,status=packet['status'],actions=packet['actions'])
            pairs[arm]=branch
        control=pairs['control'][0];variant=pairs['variant'][0]
        opportunities=[x for d in details for x in opportunity(d['queries'])]
        exposed=any(x['disagreement'] for x in opportunities)
        h=ctx0['state']['physical']['hull'];rooterror=canonical_projection(line,h['position'],h['velocity'],ctx0['before']['C']['phase'])['path_error_m'];rootmargin=3-rooterror
        verdict=decision(control,variant,exposed,rootmargin)
        return dict(status='H6_COMPARISON_COMPLETE',slot=material['slot'],**verdict,parents=results,opportunities=opportunities,registered_effect_cut_m=.25,root_inclusive_margin_upper_bound_m=rootmargin,independent_arm_repeats_exact=True,held_first_passed=True,source_gate_passed=True,posthoc_root=False,whole_finish_improvement=None,native_promotion=False,no_followup=True)
    finally:
        if live and not live.closed:base.closed(live)
