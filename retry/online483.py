"""One H6 ranking-only falsification; inherited physics and finite pedal domain."""
import copy,pickle,random
from dataclasses import asdict
import numpy as np
import retry.online481 as base
from retry.pilot420_backend import snapshot,fingerprint,rnghash,model_ledger_view
from retry.planner419_model_ledger import ForecastLedger
from retry.law477 import ReferencePolicy477,ALLOCATED,PROJECTED_SHA
from retry.live483 import allocate_current,inputs_current
from retry.history483 import validate_history
from retry.io481 import read
from retry.loss389_analyze import save,sha
from retry.receipt421_io import save_receipt
from retry.ledger439 import require
from retry.executor397 import canonical_projection

def max_guard_error(row,line):
    q=row['predicted'];phase=row['memory_after']['C']['phase']
    points=[(h['origin_position'],h['origin_linear_velocity']) for h in row['raw_hull']]+[(q['position'],q['velocity'])]
    require(len(points)==q['raw_ticks']+1 and 1<=q['raw_ticks']<=4,'483_RAW_MARGIN_COVERAGE')
    return max(canonical_projection(line,p,v,phase)['path_error_m'] for p,v in points)

def rank(option,arm):
    require(arm in ('control','variant'),'483_RANK_ARM')
    tail=(option['M80'],-option['active_pedal'])
    return tail if arm=='control' else (option['max_guard_path_error_m'],)+tail

def decision(control,variant):
    n=min(control['actions'],variant['actions'])
    equal=bool(n and all(z==4 for z in control['raw_lengths'][:n]+variant['raw_lengths'][:n]))
    cm=min(control['margins_m'][:n]) if equal else None;vm=min(variant['margins_m'][:n]) if equal else None;gain=None if not equal else vm-cm
    variant_ok=(variant['status']=='H6_SAFE_CENSORED' and variant['actions']==6) or variant['official_own_finish']
    control_failed=control['status'] in ('EMPTY_FINITE_CANDIDATE_DOMAIN','UNSAFE') and control['actions']<6
    primary=bool(equal and variant_ok and control_failed and gain is not None and gain>.25)
    reject=bool(variant['status']=='UNSAFE' or (variant['status']=='EMPTY_FINITE_CANDIDATE_DOMAIN' and variant['raw_ticks']<=control['raw_ticks']) or (equal and gain is not None and gain<=0))
    verdict='LOCAL_HYPOTHESIS_PROMOTION_GATE_PASSED' if primary else 'LOCAL_HYPOTHESIS_REJECTED' if reject else 'LOCAL_INCONCLUSIVE'
    return dict(verdict=verdict,primary=primary,common_executed_own_actions=n,same_elapsed_common_prefix=equal,control_common_min_margin_m=cm,variant_common_min_margin_m=vm,common_margin_gain_m=gain)

def history(c,memory=None):
    return validate_history(c.stream.root_state,c.stream.root_ledger,c.stream.posts,c.stream.actions,c.authorizations481,snapshot(c.m),c.ctrl.memory() if memory is None else memory,asdict(c.ledger),c.fixed['line'],c.policy481)

def prepare(c,index):
    require(c.status=='ACTIVE' and c.ctrl.phase() in ('FIRST_LAP','FINISH_CONFIRM'),'483_CURRENT_PHASE')
    state=snapshot(c.m);before=copy.deepcopy(c.ctrl.memory());ledger=asdict(c.ledger);rh=rnghash();nodes=c.ctrl.policy.nodes.copy()
    if state['finish_tracker']['candidate_crossing_time_s'] is not None:history(c)
    nominal=np.asarray(c.ctrl.act(c.m),np.float32).copy();after=copy.deepcopy(c.ctrl.memory())
    require(after['C']['phase'] in ('FIRST_LAP','FINISH_CONFIRM'),'483_SOURCE_PHASE_AFTER')
    require(snapshot(c.m)==state and asdict(c.ledger)==ledger and rnghash()==rh and np.array_equal(c.ctrl.policy.nodes,nodes),'483_NOMINAL_MUTATED_ROOT')
    qstar=allocate_current(c,nominal,index);number=c.meter.allocator_calls;c.meter.allocation_pending=None
    require(snapshot(c.m)==state and c.ctrl.memory()==after,'483_ALLOCATOR_MUTATION')
    path=c.meter.d/f'context-{number:03d}-private.json'
    ctx=dict(state=state,before=before,after=after,ledger=ledger,RNG=dict(global_pickle=pickle.dumps((random.getstate(),np.random.get_state())),digest=rnghash()),nominal=nominal.tolist(),qstar=qstar.tolist(),allocation_number=number,index=index,label=c.label,wheels=inputs_current(c.m),nominal_calls=1,ranking_arm=c.arm483)
    for kind in ('input','proof'):
        source=c.meter.d/f'allocation-{kind}-{number:03d}.json';ctx['allocation_'+kind+'_path']=str(source);ctx['allocation_'+kind+'_sha256']=sha(source)
    save_receipt(path,ctx);ctx.update(context_path=str(path),context_sha256=sha(path));return ctx

def select(c,ctx,binding,first_expected=None):
    unchanged=base.stamp(c);cmds,active=base.commands(ctx['nominal'],ctx['qstar']);options={};traces={};open_child=None
    try:
        for i,(key,opt) in enumerate(cmds.items()):
            child=base.fresh(c,ctx,f'{c.label}_q{ctx["index"]+1:02d}_c{i}',binding);open_child=child
            row=base.apply(child,ctx,opt['command'],'483_candidate_once')
            traces[key]=dict(signature=child.signature(),row=copy.deepcopy(row),posts=copy.deepcopy(child.stream.posts),RNG=rnghash())
            ok=base.valid(child);path,digest=base.closed(child);open_child=None
            options[key]=dict(command=opt['command'].tolist(),aliases=opt['aliases'],valid=ok,M80=base.score(row),max_guard_path_error_m=max_guard_error(row,c.fixed['line']),active_pedal=0. if active is None else float(opt['command'][active]),first_path=path,first_sha256=digest)
            require(base.stamp(c)==unchanged,'483_FORECAST_PARENT_MUTATION')
        if first_expected:
            # Existing cold source traces, not an assertion that cold is warm.
            require(set(options)==set(first_expected['options']),'483_FIRST_SOURCE_DOMAIN')
            for key,opt in options.items():
                old=first_expected['options'][key];require(opt['command']==old['command'],'483_FIRST_SOURCE_COMMAND')
                base.fidelity(traces[key]['row'],old['row']);base.raw_flags(traces[key]['posts'],old['posts'])
            require(ctx['nominal']==first_expected['nominal'] and ctx['qstar']==first_expected['qstar'] and ctx['after']==first_expected['after'],'483_FIRST_NOMINAL_MEMORY_QSTAR')
        eligible=[k for k,v in options.items() if v['valid']]
        if not eligible:
            save(c.meter.d/f'empty-{ctx["allocation_number"]:03d}-private.json',dict(options=options,parent_unchanged=True,unselected_not_repeated=True,ranking_arm=c.arm483))
            return None,dict(status='EMPTY_FINITE_CANDIDATE_DOMAIN',options=options)
        chosen=min(eligible,key=lambda k:rank(options[k],c.arm483));command=cmds[chosen]['command']
        if first_expected:require(chosen==first_expected['selected'][c.arm483],'483_FIRST_RANK_SCOPE_MISMATCH_NO_OVERRIDE')
        child=base.fresh(c,ctx,f'{c.label}_q{ctx["index"]+1:02d}_selected_repeat',binding);open_child=child
        row=base.apply(child,ctx,command,'483_selected_independent_repeat')
        repeated=dict(signature=child.signature(),row=copy.deepcopy(row),posts=copy.deepcopy(child.stream.posts),RNG=rnghash())
        require(repeated==traces[chosen],'483_SELECTED_REPEAT_NOT_EXACT')
        path,digest=base.closed(child);open_child=None
        require(base.stamp(c)==unchanged,'483_REPEAT_PARENT_MUTATION')
        proof=dict(first_path=options[chosen]['first_path'],first_sha256=options[chosen]['first_sha256'],repeat_path=path,repeat_sha256=digest,full_trace_exact=True)
        auth=base.base_auth(c,ctx,command,cmds,chosen,'online');auth.update(ranking_arm=c.arm483,root_history_proof_path=c.meter.p['root_proof_path'],root_history_proof_sha256=c.meter.p['root_proof_sha256'],selected_repeat_exact=True,repeat_path=path,repeat_sha256=digest)
        auth=base.persist_decision(c,ctx,auth,options,proof)
        return dict(command=command,auth=auth,trace=traces[chosen]),dict(status='SELECTED_REPEAT_EXACT',options=options,selected=chosen,aliases=cmds[chosen]['aliases'])
    finally:
        if open_child and not open_child.closed:base.closed(open_child)

def execute(meter,material):
    fixed=material['fixed'];pace=np.asarray(material['pace']);ctx0=material['context'];expected=material['first_expected'];line=fixed['line']
    binding=ReferencePolicy477(ALLOCATED,material['projected_nodes'],PROJECTED_SHA)
    policies={arm:fingerprint(dict(stage=483,arm=arm,contract=meter.p['contract_sha256'],reference=binding.nodes_digest,root=meter.p['root_proof_sha256'],sources=fingerprint(meter.p['semantic_sources']))) for arm in ('control','variant')}
    results=[];details=[];pairs={};live=None
    try:
        for arm in ('control','variant'):
            branch=[]
            for repetition,limit in ((1,6),(2,6),('held',1)):
                py,npr=pickle.loads(ctx0['RNG']['global_pickle']);random.setstate(py);np.random.set_state(npr)
                label=f'{arm}_{repetition}';full=ForecastLedger(**ctx0['ledger'])
                meter.capture_inputs(ctx0['state'],ctx0['before'],full,label+'_inputs',gate='483_AUTHENTICATED_ROOT121_NEW_LOCAL_HISTORY')
                c=base.Shadow(meter,copy.deepcopy(ctx0['state']),copy.deepcopy(ctx0['before']),model_ledger_view(full),fixed,pace,label,'nominal',world_tag='483_parent',full_ledger=ctx0['ledger'],confirmation_phase=ctx0['before']['C']['phase']);live=c
                base.setup(c,binding,policies[arm]);c.arm483=arm;rootstate=snapshot(c.m)
                require(base.physical_identity(rootstate)==base.physical_identity(ctx0['state']) and c.ctrl.memory()==ctx0['before'] and asdict(c.ledger)==ctx0['ledger'],'483_LOCAL_ROOT_EXACT')
                queries=[];first=None;undispatched=None
                for index in range(limit):
                    if c.status!='ACTIVE':break
                    ctx=prepare(c,index)
                    selected,summary=select(c,ctx,binding,expected if index==0 else None)
                    if selected is None:
                        c.status='EMPTY_FINITE_CANDIDATE_DOMAIN';c.error='all_existing_candidates_ineligible';undispatched=dict(context_sha256=ctx['context_sha256'],allocation_number=ctx['allocation_number'],committed_before_memory_digest=fingerprint(ctx['before']),prepared_after_memory_digest=fingerprint(ctx['after']),actual_controller_memory_digest=fingerprint(c.ctrl.memory()),own_dispatched=False)
                        queries.append(dict(local_query=index+1,**summary));break
                    row,join=base.own(c,ctx,selected)
                    queries.append(dict(local_query=index+1,status=c.status,selected_aliases=summary['aliases'],options=summary['options'],own_M80=base.score(row),own_guard_error_m=max_guard_error(row,line),source_join=join))
                    if index==0:first=dict(row=copy.deepcopy(row),posts=copy.deepcopy(c.stream.posts),state=snapshot(c.m),memory=c.ctrl.memory(),ledger=asdict(c.ledger),RNG=rnghash())
                    meter.checkpoint('OWN_TRANSITION',arm=arm,repetition=repetition,own_actions=len(c.rows),parent_status=c.status)
                if c.status=='ACTIVE':c.status='HELD_FIRST_SAFE' if repetition=='held' else 'H6_SAFE_CENSORED';c.error=None
                hist=history(c,ctx['before'] if undispatched else None)
                hist['memory_scope']='COMMITTED_BEFORE_UNDISPATCHED_PREPARATION' if undispatched else 'ACTUAL_LOCAL_CONTROLLER'
                physical_signature=c.signature();post_signature=fingerprint(c.stream.posts)
                packet=dict(arm=arm,repetition=repetition,status=c.status,error=c.error,actions=len(c.rows),safe_own_actions=sum(not r['safety'] for r in c.rows),raw_ticks=sum(r['predicted']['raw_ticks'] for r in c.rows),raw_lengths=[r['predicted']['raw_ticks'] for r in c.rows],margins_m=[3-max_guard_error(r,line) for r in c.rows],own_M80=[base.score(r) for r in c.rows],signature=physical_signature,post_signature=post_signature,first=first,history_proof=hist,undispatched=undispatched,official_own_finish=c.status=='FINISHED',query_count=len(queries))
                if repetition==2:require(packet['signature']==branch[0]['signature'] and packet['post_signature']==branch[0]['post_signature'],'483_INDEPENDENT_BRANCH_REPEAT')
                if repetition=='held':
                    require(first is not None and first==branch[0]['first'],'483_HELD_FIRST_SOURCE_JOIN')
                branch.append(packet);details.append(dict(arm=arm,repetition=repetition,queries=queries,first=first));results.append(packet)
                save(meter.d/'branch-results-private.json',results);save(meter.d/'query-details-private.json',details)
                base.closed(c);live=None;meter.checkpoint('BRANCH_CLOSED',arm=arm,repetition=repetition,status=packet['status'],actions=packet['actions'])
            pairs[arm]=branch
        control=pairs['control'][0];variant=pairs['variant'][0];verdict=decision(control,variant)
        h=ctx0['state']['physical']['hull'];rooterror=canonical_projection(line,h['position'],h['velocity'],ctx0['before']['C']['phase'])['path_error_m'];rootmargin=3-rooterror;cm=verdict['control_common_min_margin_m'];possible=None if cm is None else rootmargin-cm
        return dict(status='H6_COMPARISON_COMPLETE',**verdict,parents=results,registered_effect_cut_m=.25,root_inclusive_margin_upper_bound_m=rootmargin,max_possible_common_margin_gain_m=possible,root_dominates_identifiability=bool(possible is not None and possible<=.25),independent_arm_repeats_exact=True,held_first_passed=True,source_gate_passed=True,unselected_independently_repeated=False,unselected_warm_counterfactual_observed=False,posthoc_root=True,whole_finish_improvement=None,native_promotion=False,no_followup=True)
    finally:
        if live and not live.closed:base.closed(live)
