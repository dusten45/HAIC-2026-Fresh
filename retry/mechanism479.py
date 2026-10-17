"""One registered finite 80ms mechanism test. No online location policy."""
import copy,json,math,pickle,random
from dataclasses import asdict
import numpy as np
from retry.observer435 import ObserveMixin,Stream
from retry.pilot420_backend import Child as BaseChild,model_ledger_view,snapshot,fingerprint,rnghash
from retry.planner419_model_ledger import ForecastLedger
from retry.law477 import ReferencePolicy477,ALLOCATED,PROJECTED_SHA,profile_inputs468
from retry.live479 import allocate_current,check_first_raw,inputs_current
from retry.allocator476 import force
from retry.pilot421_run import compare_frames
from retry.ledger439 import require
from retry.receipt421_io import save_receipt
from retry.loss389_analyze import read,save

class Restored(ObserveMixin,BaseChild):
    def __init__(self,*args,full_ledger,**kwargs):
        # Observer must see the complete original forecast goal/clock provenance.
        BaseChild.__init__(self,*args,**kwargs)
        self.ledger=ForecastLedger(**copy.deepcopy(full_ledger))
        self.stream=Stream(self)

def stamp(c):
    return fingerprint(dict(state=snapshot(c.m),memory=c.ctrl.memory(),ledger=asdict(c.ledger),nodes=c.ctrl.policy.nodes.tolist(),rows=c.rows,status=c.status,RNG=rnghash()))

def physical_identity(state):
    value=copy.deepcopy(state)
    value['physical'].pop('source_world_contacts',None)
    return value

def prepare(c,index):
    require(c.status=='ACTIVE' and c.ctrl.phase()=='FIRST_LAP','479_CURRENT_DOMAIN')
    state=snapshot(c.m);before=copy.deepcopy(c.ctrl.memory());ledger=asdict(c.ledger);rh=rnghash();nodes=c.ctrl.policy.nodes.copy()
    nominal=np.asarray(c.ctrl.act(c.m),np.float32).copy()
    after=copy.deepcopy(c.ctrl.memory())
    require(snapshot(c.m)==state and asdict(c.ledger)==ledger and rnghash()==rh and np.array_equal(c.ctrl.policy.nodes,nodes),'479_NOMINAL_MUTATED_PHYSICS_LEDGER_RNG_REFERENCE')
    qstar=allocate_current(c,nominal,index)
    pending=copy.deepcopy(c.meter.allocation_pending);c.meter.allocation_pending=None
    require(c.ctrl.memory()==after and snapshot(c.m)==state,'479_PREPARATION_NOT_ISOLATED')
    return dict(state=state,before=before,after=after,ledger=ledger,RNG=pickle.dumps((random.getstate(),np.random.get_state())),nominal=nominal,qstar=qstar,pending=pending,index=index,wheels=inputs_current(c.m),nominal_calls=1)

def first_force(row,wheels,command):
    branch='gas' if command[1]>0 else 'brake' if command[2]>0 else 'none';active=1 if branch=='gas' else 2
    expected=[force(w,float(command[active]),branch,'model64') for w in wheels]
    raw=[z for z in row['tires'] if z['raw_tick']==1]
    require(len(raw)==4,'479_FIRST_RAW_FOUR_WHEELS')
    for a,b in zip(expected,raw):
        require(all(a[k]==b[v] for k,v in {'omega':'omega','gas':'gas','brake':'brake','long':'raw_long_N','lat':'raw_lat_N','ratio':'force_ratio'}.items()),'479_FIRST_RAW_SOURCE_FORCE_EXACT')

def apply(c,ctx,command,tag,qstar=False):
    require(c.ctrl.memory()==ctx['after'] and physical_identity(snapshot(c.m))==physical_identity(ctx['state']) and asdict(c.ledger)==ctx['ledger'],'479_PREPARED_CONTEXT_JOIN')
    n=len(c.rows);c.one(tag,first_override=command,prepared_nominal=ctx['nominal'],prepared_before=ctx['before'])
    require(len(c.rows)==n+1,'479_ONE_OBSERVED_HOLD')
    row=c.rows[-1]
    require(row['memory_before']==ctx['before'] and row['memory_after']==ctx['after'] and c.ctrl.memory()==ctx['after'],'479_NOMINAL_ONCE')
    require(row['command']==command.tolist() and row['predicted']['raw_ticks']==4,'479_FROZEN_FOUR_RAW_HOLD')
    first_force(row,ctx['wheels'],command)
    if qstar:
        c.meter.allocation_pending=ctx['pending'];check_first_raw(c,ctx['index'])
    return row

def score(row):
    ratios=[float(t['force_ratio']) for t in row['tires']]
    require(len(ratios)==16 and all(math.isfinite(x) and x>=0 for x in ratios),'479_FINITE_NONNEGATIVE_ALL_RAW_RATIOS')
    value=max(max(0.,x-1.) for x in ratios)
    require(math.isfinite(value),'479_FINITE_M80')
    return value

def valid(c):
    return c.status=='ACTIVE' and not c.rows[-1]['safety'] and not c.ledger.deadline_missed and c.ctrl.phase()=='FIRST_LAP'

def fidelity(a,b):
    out=compare_frames(a,b)
    # compare_frames includes frozen hull/wheel/body tolerances. These discrete
    # raw attributes remain exact, never traded for a smaller force objective.
    fields=('clipped','grass')
    require(len(a['tires'])==len(b['tires']),'479_SOURCE_TIRE_LENGTH')
    exact=all(all(x[k]==y[k] for k in fields) for x,y in zip(a['tires'],b['tires']))
    out['raw_discrete_exact']=exact
    require(out['passed'] and exact and out['wheel']['clipped_flag_mismatches']==0,'479_EXISTING_SOURCE_FIDELITY_STOP:'+json.dumps(out))
    return out

def raw_flags_exact(a,b):
    require(len(a)==len(b)==4,'479_RAW_FLAG_COVERAGE')
    fields=('damage','collision','grass','wheel_road_contacts','phase')
    require(all(all(x[k]==y[k] for k in fields) for x,y in zip(a,b)),'479_RAW_DISCRETE_FLAGS_NOT_EXACT')

def execute(root,meter,fixed,pace,state,memory,actual_ledger):
    archived=read(root/'stage477-revision1/whole_AllocationP4-private.json')['rows']
    archived_posts=read(root/'stage477-revision1/whole_AllocationP4-observer-private.json')['posts']
    require(len(archived)==74,'479_ARCHIVED_SOURCE74')
    _,nodes,_=profile_inputs468(root,fixed,pace);binding=ReferencePolicy477(ALLOCATED,nodes,PROJECTED_SHA)
    children=[];diagnostics=[];driver=[]
    def fresh(ctx,label):
        meter.capture_inputs(ctx['state'],ctx['after'],ForecastLedger(**ctx['ledger']),label+'_inputs',gate='479_PREPARED_AFTER_NOMINAL_NO_RECALL')
        c=Restored(meter,copy.deepcopy(ctx['state']),copy.deepcopy(ctx['after']),model_ledger_view(ForecastLedger(**ctx['ledger'])),fixed,pace,label,'nominal',world_tag='479_single_hold',full_ledger=ctx['ledger'])
        children.append(c);binding.inject(c)
        require(asdict(c.ledger)==ctx['ledger'] and c.stream.root_ledger==ctx['ledger'],'479_FULL_LEDGER_BEFORE_STREAM')
        require(c.ctrl.memory()==ctx['after'] and rnghash()==fingerprint_rng(ctx['RNG']),'479_FRESH_PREPARED_MEMORY_RNG')
        # Full exported physical root is required, not reconstructed telemetry.
        require(physical_identity(snapshot(c.m))==physical_identity(ctx['state']),'479_FULL_ROOT_RESTORE')
        return c
    def close(c):
        c.dump(meter.d);c.close()
    def diagnostic(parent,ctx,number):
        parent_before=stamp(parent)
        save_receipt(meter.d/f'root{number}-full-prepared-private.json',{**ctx,'nominal':ctx['nominal'].tolist(),'qstar':ctx['qstar'].tolist()})
        active=1 if ctx['nominal'][1]>0 else 2 if ctx['nominal'][2]>0 else None
        require(active is not None,'479_ACTIVE_PEDAL_REQUIRED')
        zero=ctx['nominal'].copy();zero[active]=np.float32(0)
        commands={'nominal':ctx['nominal'],'qstar':ctx['qstar'],'zero':zero};options={};rows={};posts={}
        for name,command in commands.items():
            pair=[]
            for rep in (1,2):
                c=fresh(ctx,f'root{number}_{name}_{rep}')
                row=apply(c,ctx,command,'479_shadow_'+name)
                pair.append(dict(row=copy.deepcopy(row),signature=c.signature(),valid=valid(c),posts=copy.deepcopy(c.stream.posts)))
                close(c);require(stamp(parent)==parent_before,'479_SHADOW_MUTATED_LIVE_PARENT')
            require(pair[0]==pair[1],'479_INDEPENDENT_COLD_REPEAT_NOT_EXACT')
            row=pair[0]['row'];rows[name]=row;posts[name]=pair[0]['posts']
            options[name]=dict(command=command.tolist(),M80=score(row),valid=pair[0]['valid'],repeat_exact=True,active_pedal=float(command[active]))
        # Same-root force before the first integration is exact even when warm
        # solver impulses make subsequent cold/warm dynamics differ slightly.
        first_force(archived[number-1],ctx['wheels'],ctx['qstar'])
        source_join=fidelity(rows['qstar'],archived[number-1]);raw_flags_exact(posts['qstar'],archived_posts[(number-1)*4:number*4])
        feasible=[name for name,opt in options.items() if opt['valid']]
        decision=dict(root=number,options=options,source_join=source_join,parent_isolated=True,nominal_calls=1,allocator_calls=1)
        if not feasible:
            decision.update(status='EMPTY_FINITE_CANDIDATE_DOMAIN',selected=None);save_summary(meter,number,decision);diagnostics.append(decision);return False
        selected=min(feasible,key=lambda name:(options[name]['M80'],-options[name]['active_pedal']))
        command=commands[selected]
        own=parent if number==69 else fresh(ctx,'root47_held')
        require(stamp(parent)==parent_before,'479_PARENT_CHANGED_BEFORE_OWN_HOLD')
        ownrow=apply(own,ctx,command,'479_held_own')
        ownjoin=fidelity(ownrow,rows[selected]);raw_flags_exact(own.stream.posts[-4:],posts[selected]);ownvalid=valid(own)
        decision.update(selected=selected,held_M80=score(ownrow),held_valid=ownvalid,held_safety=ownrow['safety'],held_path_error_m=ownrow['path_error_m'],held_progress_m=ownrow['model_progress'],held_source_join=ownjoin,archived_warm_qstar_M80=score(archived[number-1]),cold_qstar_gap=options['qstar']['M80']-options[selected]['M80'],source_two_trace_gap_bound=.10,uncertainty_is_not_optimizer_epsilon=True)
        if number==47:
            require(ownvalid,'479_POSITIVE_CONTROL_SAFETY_PROGRESS_STOP');decision['status']='POSITIVE_CONTROL_PASSED';close(own)
            require(stamp(parent)==parent_before,'479_HELD47_MUTATED_PREFIX')
        else:
            improvement=score(archived[68])-score(ownrow)
            decision['warm_own_M80_improvement']=improvement
            decision['status']=('MECHANISM_LOCAL_OWN_HOLD_IMPROVED' if ownvalid and improvement>0 and options[selected]['M80']<options['qstar']['M80'] else 'FORECAST_RANKING_NOT_TRANSFERRED' if options[selected]['M80']<options['qstar']['M80'] and improvement<0 else 'FINITE_COMPARISON_NO_OWN_IMPROVEMENT')
            decision['promotion']=False
        diagnostics.append(decision);save_summary(meter,number,decision);meter.checkpoint('DIAGNOSTIC_HOLD_COMPLETE',root=number,status=decision['status'])
        return True
    def fingerprint_rng(blob):
        import hashlib
        return hashlib.sha256(blob).hexdigest()
    meter.capture_inputs(state,memory,actual_ledger,'prefix_inputs',gate='479_SAME_PRE23_FROZEN477_PREFIX68')
    prefix=__import__('retry.observer435',fromlist=['Child']).Child(meter,copy.deepcopy(state),copy.deepcopy(memory),actual_ledger,fixed,pace,'prefix','nominal',world_tag='479_prefix_and_held69');children.append(prefix);binding.inject(prefix)
    try:
        for index in range(68):
            ctx=prepare(prefix,index);driver.append(dict(action=index+1,nominal_calls=1,allocator_calls=1))
            if index==46 and not diagnostic(prefix,ctx,47):return dict(status='FINITE_DOMAIN_STOP',diagnostics=diagnostics,driver=driver)
            row=apply(prefix,ctx,ctx['qstar'],'479_frozen477_prefix',qstar=True)
            require(row==archived[index],'479_PREFIX_NOT_EXACT_AT:'+str(index+1))
            require(prefix.status=='ACTIVE','479_PREFIX_SAFETY_PROGRESS_STOP')
            meter.checkpoint('PREFIX_EXACT',actions=index+1)
        ctx=prepare(prefix,68);driver.append(dict(action=69,nominal_calls=1,allocator_calls=1))
        if not diagnostic(prefix,ctx,69):return dict(status='FINITE_DOMAIN_STOP',prefix_exact_actions=68,diagnostics=diagnostics,driver=driver)
        require(meter.b['worlds']==14 and meter.b['ticks']==328 and meter.b['reserved_ticks']==328 and meter.allocator_calls==69,'479_EXACT_TOTAL_COUNTS')
        save(meter.d/'nominal-once-driver-private.json',driver)
        return dict(status='FINITE_HOLD_COMPARISON_COMPLETE',prefix_exact_actions=68,nominal_calls=69,diagnostics=diagnostics,driver=driver,no_policy_promotion=True)
    finally:
        for c in children:
            if not c.closed:close(c)

def save_summary(meter,number,value):
    require(len((json.dumps(value,indent=2)+'\n').encode())<=65536,'479_SELECTION_SUMMARY64KiB')
    save(meter.d/f'root{number}-selection-private.json',value)
