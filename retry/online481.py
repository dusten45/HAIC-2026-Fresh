"""Fixed B200 online model policy. No location-dependent triggers or native API."""
import copy,hashlib,json,math,pickle,random
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.observer435 import ObserveMixin,Stream,Child
from retry.guardian426_confirmed import GuardianChild as BaseGuardian
from retry.pilot420_backend import model_ledger_view,snapshot,fingerprint,rnghash
from retry.planner419_model_ledger import ForecastLedger
from retry.law477 import ReferencePolicy477,ALLOCATED,PROJECTED_SHA,profile_inputs468
from retry.live481 import allocate_current,inputs_current
from retry.mechanism479 import physical_identity,first_force,fidelity
from retry.qualify_parent453 import saved_history
from retry.history481 import validate_history
from retry.boundary434 import replay as replay_tracker,encoded
from retry.ledger439 import require
from retry.io481 import load_receipt,read
from retry.loss389_analyze import save,sha
from retry.receipt421_io import save_receipt

class Shadow(ObserveMixin,BaseGuardian):
    def __init__(self,*args,full_ledger,**kwargs):
        BaseGuardian.__init__(self,*args,**kwargs)
        self.ledger=ForecastLedger(**copy.deepcopy(full_ledger));self.stream=Stream(self)

def key(command):return np.asarray(command,dtype='<f4').tobytes().hex()
def commands(nominal,qstar):
    nominal=np.asarray(nominal,np.float32);qstar=np.asarray(qstar,np.float32);zero=nominal.copy()
    active=1 if nominal[1]>0 else 2 if nominal[2]>0 else None
    if active is not None:zero[active]=np.float32(0)
    result={}
    for name,command in [('nominal',nominal),('qstar',qstar),('zero',zero)]:
        k=key(command)
        if k not in result:result[k]=dict(command=command.copy(),aliases=[])
        result[k]['aliases'].append(name)
    return result,active

def stamp(c):
    return fingerprint(dict(state=snapshot(c.m),memory=c.ctrl.memory(),ledger=asdict(c.ledger),nodes=c.ctrl.policy.nodes.tolist(),rows=c.rows,status=c.status,RNG=rnghash()))

def history(c,*,state=None,memory=None,ledger=None):
    current=snapshot(c.m) if state is None else state
    mem=c.ctrl.memory() if memory is None else memory
    return validate_history(c.stream.root_state,c.stream.root_ledger,c.stream.posts,c.stream.actions,c.authorizations481,current,mem,asdict(c.ledger) if ledger is None else ledger,c.fixed['line'],c.policy481)

def prepare(c,index):
    require(c.status=='ACTIVE' and c.ctrl.phase() in ('FIRST_LAP','FINISH_CONFIRM'),'481_CURRENT_PHASE')
    state=snapshot(c.m);before=copy.deepcopy(c.ctrl.memory());ledger=asdict(c.ledger);rh=rnghash();nodes=c.ctrl.policy.nodes.copy()
    if state['finish_tracker']['candidate_crossing_time_s'] is not None:
        if getattr(c,'historical481',None):
            h=c.historical481
            validate_history(h['root'],h['ledger'],h['posts'],h['actions'],h['authorizations'],state,before,ledger,c.fixed['line'],c.policy481,historical=True)
        else:history(c,state=state,memory=before,ledger=ledger)
    nominal=np.asarray(c.ctrl.act(c.m),np.float32).copy();after=copy.deepcopy(c.ctrl.memory())
    require(after['C']['phase'] in ('FIRST_LAP','FINISH_CONFIRM'),'481_SOURCE_PHASE_AFTER')
    require(snapshot(c.m)==state and asdict(c.ledger)==ledger and rnghash()==rh and np.array_equal(c.ctrl.policy.nodes,nodes),'481_NOMINAL_MUTATED_PHYSICAL_LEDGER_RNG_REFERENCE')
    qstar=allocate_current(c,nominal,index);number=c.meter.allocator_calls;c.meter.allocation_pending=None
    require(snapshot(c.m)==state and c.ctrl.memory()==after,'481_ALLOCATOR_MUTATION')
    path=c.meter.d/f'context-{number:03d}-private.json'
    ctx=dict(state=state,before=before,after=after,ledger=ledger,RNG=dict(global_pickle=pickle.dumps((random.getstate(),np.random.get_state())),digest=rnghash()),nominal=nominal.tolist(),qstar=qstar.tolist(),allocation_number=number,index=index,label=c.label,wheels=inputs_current(c.m),nominal_calls=1)
    for kind in ('input','proof'):
        source=c.meter.d/f'allocation-{kind}-{number:03d}.json';ctx['allocation_'+kind+'_path']=str(source);ctx['allocation_'+kind+'_sha256']=sha(source)
    save_receipt(path,ctx);ctx['context_path']=str(path);ctx['context_sha256']=sha(path)
    return ctx

def apply(c,ctx,command,tag):
    command=np.asarray(command,np.float32)
    require(c.ctrl.memory()==ctx['after'] and physical_identity(snapshot(c.m))==physical_identity(ctx['state']) and asdict(c.ledger)==ctx['ledger'],'481_PREPARED_JOIN')
    n=len(c.rows);c.one(tag,first_override=command,prepared_nominal=ctx['nominal'],prepared_before=ctx['before'])
    require(len(c.rows)==n+1,'481_ONE_HOLD_OBSERVED');row=c.rows[-1];q=row['predicted'];nraw=q['raw_ticks']
    require(row['memory_before']==ctx['before'] and row['memory_after']==ctx['after'],'481_NOMINAL_ONCE')
    expected=copy.deepcopy(ctx['after'])
    if c.status=='FINISHED':expected['C']['phase']='DONE'
    require(c.ctrl.memory()==expected,'481_ONLY_OWN_OFFICIAL_FINISH_MARKS_DONE')
    require(row['command']==command.tolist() and 1<=nraw<=4 and (nraw==4 or q['finished'] or q['terminal']),'481_SOURCE_HOLD_LENGTH')
    first_force(row,ctx['wheels'],command)
    return row

def score(row):
    n=row['predicted']['raw_ticks'];ratios=[float(t['force_ratio']) for t in row['tires']]
    require(len(ratios)==4*n and all(math.isfinite(x) and x>=0 for x in ratios),'481_ALL_FINITE_RATIOS')
    return max(max(0.,x-1.) for x in ratios)

def valid(c):
    return c.status in ('ACTIVE','FINISHED') and not c.rows[-1]['safety'] and not c.ledger.deadline_missed and c.rows[-1]['memory_after']['C']['phase'] in ('FIRST_LAP','FINISH_CONFIRM')

def raw_flags(a,b):
    require(len(a)==len(b) and 1<=len(a)<=4,'481_RAW_FLAG_COUNT')
    require(all(all(x[k]==y[k] for k in ('damage','collision','grass','wheel_road_contacts','phase')) for x,y in zip(a,b)),'481_RAW_DISCRETE_EXACT')

def closed(c):
    c.dump(c.meter.d);c.close()
    path=c.meter.d/(c.label+'-private.json')
    return str(path),sha(path)

def fresh(parent,ctx,label,binding):
    meter=parent.meter;ledger=ForecastLedger(**ctx['ledger'])
    meter.capture_inputs(ctx['state'],ctx['after'],ledger,label+'_inputs',gate='481_PREPARED_AFTER_NO_NOMINAL_RECALL')
    c=Shadow(meter,copy.deepcopy(ctx['state']),copy.deepcopy(ctx['after']),model_ledger_view(ledger),parent.fixed,parent.pace,label,'nominal',world_tag='481_shadow',full_ledger=ctx['ledger'],confirmation_phase=ctx['after']['C']['phase'])
    binding.inject(c)
    require(asdict(c.ledger)==ctx['ledger']==c.stream.root_ledger and c.ctrl.memory()==ctx['after'],'481_FULL_LEDGER_BEFORE_STREAM')
    require(physical_identity(snapshot(c.m))==physical_identity(ctx['state']),'481_FULL_STATE_RESTORE')
    require(rnghash()==ctx['RNG']['digest'],'481_RESTORE_RNG')
    return c

def base_auth(c,ctx,command,cmds,chosen,mode):
    return dict(policy_digest=c.policy481,parent_token=c.stream.child_id,action_index=len(c.rows)+1,mode=mode,before_memory_digest=fingerprint(ctx['before']),after_memory_digest=fingerprint(ctx['after']),ledger_before_digest=fingerprint(ctx['ledger']),state_before_digest=fingerprint(ctx['state']),command=np.asarray(command,np.float32).tolist(),nominal=ctx['nominal'],qstar=ctx['qstar'],selected_key=chosen,commands={k:v['command'].tolist() for k,v in cmds.items()},allocation_number=ctx['allocation_number'],context_path=ctx['context_path'],context_sha256=ctx['context_sha256'])

def persist_decision(c,ctx,authorization,options,repeat=None):
    name=f"decision-{ctx['allocation_number']:03d}-private.json";path=c.meter.d/name
    record=dict(authorization=authorization,options=options,selected_repeat_proof=repeat,unselected_independent_repeats=False,unselected_warm_counterfactual_observed=False)
    require(len((json.dumps(record,indent=2)+'\n').encode())<64000,'481_DECISION64KiB')
    save_receipt(path,record)
    return {**authorization,'decision_path':str(path),'decision_sha256':sha(path)}

def select(c,ctx,binding,source_expected=None):
    unchanged=stamp(c);cmds,active=commands(ctx['nominal'],ctx['qstar']);options={};traces={};open_child=None
    try:
        for i,(k,opt) in enumerate(cmds.items()):
            child=fresh(c,ctx,f"{c.label}_q{ctx['index']+1:03d}_c{i}",binding);open_child=child
            row=apply(child,ctx,opt['command'],'481_candidate_once')
            trace=dict(signature=child.signature(),row=copy.deepcopy(row),posts=copy.deepcopy(child.stream.posts),RNG=rnghash())
            ok=valid(child);path,digest=closed(child);open_child=None
            traces[k]=trace
            options[k]=dict(command=opt['command'].tolist(),aliases=opt['aliases'],valid=ok,M80=score(row),active_pedal=0. if active is None else float(opt['command'][active]),first_path=path,first_sha256=digest)
            require(stamp(c)==unchanged,'481_FORECAST_MUTATED_PARENT')
        if source_expected is not None:
            q=traces[key(ctx['qstar'])];expected=source_expected['row']
            require(all(q['row'][k]==expected[k] for k in ('command','memory_before','memory_after')),'481_CURRENT_SOURCE_NOMINAL_COMMAND_MEMORY_EXACT')
            fidelity(q['row'],expected);raw_flags(q['posts'],source_expected['posts'])
        eligible=[k for k,v in options.items() if v['valid']]
        if not eligible:
            save(c.meter.d/f"empty-{ctx['allocation_number']:03d}-private.json",dict(options=options,parent_unchanged=True,unselected_not_repeated=True))
            return None,dict(status='EMPTY_FINITE_CANDIDATE_DOMAIN',options=options)
        chosen=min(eligible,key=lambda k:(options[k]['M80'],-options[k]['active_pedal']));command=cmds[chosen]['command']
        child=fresh(c,ctx,f"{c.label}_q{ctx['index']+1:03d}_selected_repeat",binding);open_child=child
        row=apply(child,ctx,command,'481_selected_independent_repeat')
        repeated=dict(signature=child.signature(),row=copy.deepcopy(row),posts=copy.deepcopy(child.stream.posts),RNG=rnghash())
        require(repeated==traces[chosen],'481_SELECTED_REPEAT_NOT_EXACT')
        path,digest=closed(child);open_child=None
        require(stamp(c)==unchanged,'481_SELECTED_REPEAT_MUTATED_PARENT')
        proof=dict(first_path=options[chosen]['first_path'],first_sha256=options[chosen]['first_sha256'],repeat_path=path,repeat_sha256=digest,full_trace_exact=True)
        auth=base_auth(c,ctx,command,cmds,chosen,'online');auth.update(selected_repeat_exact=True,repeat_path=path,repeat_sha256=digest)
        auth=persist_decision(c,ctx,auth,options,proof)
        return dict(command=command,auth=auth,trace=traces[chosen]),dict(status='SELECTED_REPEAT_EXACT',options=options,selected=chosen,aliases=cmds[chosen]['aliases'])
    finally:
        if open_child and not open_child.closed:closed(open_child)

def own(c,ctx,selected):
    require(selected['auth']['parent_token']==c.stream.child_id and selected['auth']['action_index']==len(c.rows)+1,'481_OWN_POLICY_PARENT_BINDING')
    row=apply(c,ctx,selected['command'],'481_parent_own')
    join=None
    if selected.get('trace'):
        join=fidelity(row,selected['trace']['row']);raw_flags(c.stream.posts[-row['predicted']['raw_ticks']:],selected['trace']['posts'])
    c.authorizations481.append(selected['auth'])
    save(c.meter.d/f"own-link-{ctx['allocation_number']:03d}-private.json",dict(parent_token=c.stream.child_id,action=len(c.rows),decision_sha256=selected['auth']['decision_sha256'],row_digest=fingerprint(row),ledger_after=asdict(c.ledger),selected_source_join=join,own_M80=score(row),status=c.status))
    return row,join

def setup(c,binding,policy_digest):
    binding.inject(c);c.policy481=policy_digest;c.authorizations481=[];c.historical481=None
    return c

def execute(root,meter,fixed,pace,state,memory,actual):
    _,nodes,_=profile_inputs468(root,fixed,pace);binding=ReferencePolicy477(ALLOCATED,nodes,PROJECTED_SHA)
    policy={mode:fingerprint(dict(stage=481,mode=mode,contract=meter.p['contract480_sha256'],reference=binding.nodes_digest,source_manifest=fingerprint(meter.p['semantic_sources']))) for mode in ('baseline','online')}
    archived=read(root/'stage477-revision1/whole_AllocationP4-private.json')['rows'];oldposts=read(root/'stage477-revision1/whole_AllocationP4-observer-private.json')['posts']
    results=[];fixtures=[];queries=[];all_children=[]
    def parent(label,which,state0=state,memory0=memory,ledger0=actual,full=None):
        meter.capture_inputs(state0,memory0,ledger0,label+'_inputs',gate='481_FIXED_INPUT_OWN_PARENT')
        if full is None:c=Child(meter,copy.deepcopy(state0),copy.deepcopy(memory0),ledger0,fixed,pace,label,'nominal',world_tag='481_parent')
        else:c=Shadow(meter,copy.deepcopy(state0),copy.deepcopy(memory0),ledger0,fixed,pace,label,'nominal',world_tag='481_pending_held',full_ledger=full,confirmation_phase='FINISH_CONFIRM')
        setup(c,binding,policy[which]);all_children.append(c);return c
    try:
        # Exactly one held fixture parent plus<=3candidate worlds+selected repeat.
        c=parent('fixture_source','online');ctx=prepare(c,0)
        selected,summary=select(c,ctx,binding,dict(row=archived[0],posts=oldposts[:4]));require(selected is not None,'481_SOURCE_EMPTY')
        row,join=own(c,ctx,selected);require(valid(c),'481_SOURCE_FIXTURE_GUARD');history(c)
        fixtures.append(dict(name='source',passed=True,status=c.status,raw_ticks=row['predicted']['raw_ticks'],selected=summary['aliases']));closed(c)
        stop,h=saved_history(root);full=read(root/'stage435/parent_P-private.json')['model_ledger'];view=model_ledger_view(ForecastLedger(**full))
        c=parent('fixture_pending','online',stop['live_parent'],stop['memory_before_nominal'],view,full=full)
        n=read(root/'stage435/parent_P-observer-private.json')['link']['world_number']
        paths=['stage435/P_decision55-context-stop-private.json','stage435/parent_P-private.json','stage435/parent_P-observer-private.json',f'stage435/world{n}-before-constructor-private.json']
        historical_sources={str(root/x):sha(root/x) for x in paths}
        c.historical481={**h,'authorizations':[dict(mode='historical435',sources=historical_sources,history_path=str(root/'stage435/parent_P-observer-private.json'),history_sha256=sha(root/'stage435/parent_P-observer-private.json'))]}
        ctx=prepare(c,0);selected,summary=select(c,ctx,binding);require(selected is not None,'481_PENDING_EMPTY')
        row,join=own(c,ctx,selected);event=ctx['state']['finish_tracker']['candidate_crossing_time_s']
        require(valid(c) and c.status=='FINISHED' and c.guardian_certificate['event_time_s']==event and not c.guardian_certificate['actual_done_allowed'],'481_PENDING_SAME_EVENT_OWN_CONFIRMATION')
        replayed,times=replay_tracker(h['root']['finish_tracker'],h['posts']+c.stream.posts,h['ledger']['last_clock_tick'],h['root']['physical']['actual_time'])
        require(encoded(replayed)==encoded(snapshot(c.m)['finish_tracker']) and event in times and c.ledger.last_clock_tick==c.stream.posts[-1]['raw_clock'],'481_PENDING_COMPLETE_OBSERVED_TRACKER_CLOCK_REPLAY')
        fixtures.append(dict(name='pending',complete_tracker_history_replayed=True,passed=True,status=c.status,raw_ticks=row['predicted']['raw_ticks'],same_event=True,selected=summary['aliases']));closed(c)
        save(meter.d/'integrated-fixtures-private.json',dict(passed=True,fixtures=fixtures,counts=dict(worlds=meter.b['worlds'],ticks=meter.b['ticks'],charged=meter.b['reserved_ticks'])));meter.checkpoint('FIXTURES_PASSED')
        for mode in ('baseline','online'):
            c=parent(mode,mode);undispatched=None
            for index in range(200):
                if c.status!='ACTIVE':break
                ctx=prepare(c,index)
                if mode=='online':
                    selected,summary=select(c,ctx,binding)
                    if selected is None:
                        c.status='EMPTY_FINITE_CANDIDATE_DOMAIN';c.error='all_current_three_commands_ineligible'
                        undispatched=dict(context_sha256=ctx['context_sha256'],allocation_number=ctx['allocation_number'],committed_memory_digest=fingerprint(ctx['before']),prepared_after_memory_digest=fingerprint(ctx['after']),actual_controller_memory_digest=fingerprint(c.ctrl.memory()),nominal_calls=1,own_step_performed=False)
                        queries.append(dict(action=index+1,**summary));break
                else:
                    command=np.asarray(ctx['qstar'],np.float32);k=key(command);cmds={k:dict(command=command)}
                    auth=base_auth(c,ctx,command,cmds,k,'baseline');auth=persist_decision(c,ctx,auth,{})
                    selected=dict(command=command,auth=auth);summary=dict(status='FROZEN_FIRST_RAW_QSTAR')
                row,join=own(c,ctx,selected)
                if mode=='baseline':require(index<len(archived) and row==archived[index],'481_BASELINE_FROZEN477_EXACT')
                else:queries.append(dict(action=index+1,selected_aliases=summary['aliases'],own_M80=score(row),path_error_m=row['path_error_m'],status=c.status,source_join=join,options=summary['options']))
                meter.checkpoint('PARENT_TRANSITION',arm=mode,actions=len(c.rows),parent_status=c.status)
            if c.status=='ACTIVE':c.status='SCOPE_CENSORED';c.error='200_action_limit_no_aftercap_step'
            proof=history(c,memory=ctx['before']) if undispatched else history(c)
            proof['memory_scope']='LAST_COMMITTED_OWN_CHAIN_BEFORE_UNDISPATCHED_PREPARATION' if undispatched else 'ACTUAL_CURRENT_CONTROLLER_INCLUDING_LEGITIMATE_DONE'
            event=c.rows[-1]['predicted']['finish_time_s'] if c.status=='FINISHED' else None
            result=dict(arm=mode,status=c.status,error=c.error,actions=len(c.rows),official_own_model_finish=c.status=='FINISHED',event_time_s=event,confirmation_time_s=None if event is None else c.rows[-1]['predicted']['time'],finish_ticks=None if c.finish_ticks is None else asdict(c.finish_ticks),max_path_error_m=max((r['path_error_m'] for r in c.rows),default=0.),last_path_error_m=None if not c.rows else c.rows[-1]['path_error_m'],history_proof=proof,undispatched_preparation=undispatched,actual_controller_memory_digest=fingerprint(c.ctrl.memory()),policy_digest=c.policy481)
            results.append(result);save(meter.d/'whole-results-private.json',results);save(meter.d/'online-query-summaries-private.json',queries);closed(c)
        both=all(x['official_own_model_finish'] for x in results);gain=None
        if both:
            a,b=[r['finish_ticks'] for r in results];gain=[(a['lo']-b['hi'])/50,(a['hi']-b['lo'])/50]
        return dict(status='B200_MODEL_PAIR_COMPLETE',fixtures=fixtures,parents=results,online_queries=queries,finish_time_gain_bracket_s=gain,both_own_finish=both,unselected_independently_repeated=False,unselected_warm_counterfactual_observed=False,native_promotion=False)
    finally:
        for c in all_children:
            if not c.closed:closed(c)
