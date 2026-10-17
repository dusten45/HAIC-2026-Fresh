"""Once-only455 contract: two roots, four independent MODEL parents, no native entrypoint."""
import time
WORKER_START=time.perf_counter()
import copy,datetime,json,os,pickle,random,signal,sys,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.budget456 import Meter as BudgetMeter460,Planning456
from retry.pilot420_backend import *
from retry.observer435 import Child
from retry.parent436 import capture_pending,verify_parent_step
from retry.qualify453 import qualify,qualify_pending
from retry.qualify_parent453 import qualify as qualify_parent
from retry.receipt421_io import load_receipt,save_receipt
from retry.terminal410_model import from_actual_full
from retry.pilot421_run import compare_frames
from retry.audit439 import replay
from retry.ledger439 import compare_first,require
from retry.loss389_analyze import read,save,sha
G=Path(__file__).resolve().parents[1]
PLAN_CAPS=dict(ticks=327680,worlds=1792,CPU_s=9000,wall_s=12000,max_parallel=1)

class Meter460(BudgetMeter460):
    def guard(self):
        super().guard()
        import shutil
        if shutil.disk_usage(self.d).free<self.p.get('storage_free_stop_bytes',512*1024**2):raise ResourceStop('460_storage_reserve_512MiB')
    def checkpoint(self,phase,**facts):
        q=super().checkpoint(phase,**facts);q['stage']=460;save(self.d/'progress-private.json',q);return q

def create_meter(d):
    return Meter460(d,start_wall=WORKER_START)

def scope460(name,planner_used,phase,pending=False):
    require(name in ['NoPulse','Pulse'] and type(planner_used) is int and planner_used>=0,'460_SCOPE_INPUT')
    require(phase in ['FIRST_LAP','FINISH_CONFIRM'] and type(pending) is bool,'460_SCOPE_PHASE')
    return 100,planner_used<8 and phase=='FIRST_LAP' and not pending

ORDER=['NoPulse-1','Pulse-1','NoPulse-2','Pulse-2']

def planned_budget():
    # Bind accounting to the actual scheduler on every registered arm.
    quotas={name:sum(scope460(name.split('-')[0],i,'FIRST_LAP')[1] for i in range(100)) for name in ORDER}
    parents=sum(scope460(name.split('-')[0],0,'FIRST_LAP')[0] for name in ORDER)
    planner=sum(quotas.values());guardian=parents-planner
    parts=dict(planner=dict(queries=planner,ticks=planner*3*2*321*4,worlds=planner*3*2),
               guardian=dict(queries=guardian,ticks=guardian*2*2*13*4,worlds=guardian*2*2),
               parents=dict(actions=parents,ticks=parents*4,worlds=len(ORDER)),
               qualification=dict(ticks=1242+2*216,worlds=35+2*6))
    return dict(quotas=quotas,parts=parts,ticks=sum(x['ticks'] for x in parts.values()),worlds=sum(x['worlds'] for x in parts.values()))

def root_inputs(root,label):
    require(label in ['NoPulse','Pulse'],'460_ROOT_LABEL')
    arm='baseline' if label=='NoPulse' else 'candidate'
    d=root/'stage453';rows=[json.loads(x) for x in (d/f'actual_{arm}/trace-private.jsonl').read_text().splitlines()]
    origin=rows[22]['progress_before'];n=next(r['step'] for r in rows if r['progress_before']>=origin+450.)
    require(n==(117 if label=='NoPulse' else 113),'460_ROOT_FIRST_PRE450')
    bundle=load_receipt(d/f'{arm}_decision{n-22}-before-actual-dispatch-private.json')
    parent=Parent(**bundle['context']['parent']);src,memory,rng=parent.fork_inputs();state=src['terminal_model'];ledger=GoalLedger(**bundle['context']['ledger'])
    before=load_receipt(d/f'actual_{arm}/{arm}_step{n}-before-native-private.json')
    require(state==from_actual_full(before['full_pre_before_nominal']) and memory==rows[n-1]['memory_before'],'460_ROOT_NATIVE_SOURCE')
    require(not ledger.done and not ledger.deadline_missed and state['finish_tracker']['candidate_crossing_time_s'] is None and state['finish_tracker']['finish_time_s'] is None,'460_ROOT_DOMAIN')
    expected=rows[n-1:n+12];require(len(expected)==13 and all(x['command']==x['nominal'] for x in expected),'460_ROOT_FACTUAL_NOMINAL13')
    proof=load_receipt(d/f'{arm}_decision{n-22}_query-before-integration-private.json')
    require(proof['memory']==memory and proof['ledger']==asdict(ledger) and proof['state']==state,'460_ROOT_INPUT_PROOF')
    elapsed=rows[n-1]['pre']['time']-rows[0]['pre']['time']
    require(abs(elapsed-(9.28 if label=='NoPulse' else 8.96))<1e-8,'460_PREFIX_ELAPSED')
    return state,memory,ledger,rng,proof['global_RNG_pickle'],expected

def prepare(root):
    d=root/'stage460';require(not d.exists() and not d.is_symlink(),'460_ONCE_ONLY')
    # New evidence only; existing workspace originals remain untouched.
    storage=Path('/tmp/haic-retry-stage460-private');require(not storage.exists(),'460_STORAGE_ONCE_ONLY')
    import shutil
    require(shutil.disk_usage('/tmp').free>=7*1024**3,'460_STORAGE_PREFLIGHT_7GiB')
    storage.mkdir(mode=0o700);d.symlink_to(storage,target_is_directory=True)
    old=read(root/'stage453/plan.json');v=read(root/'project-effective-budget-v474.json');deadline=read(root/'research-deadline-current.json')['deadline_utc']
    require((v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(26695,84000,0),'460_LEDGER')
    require(deadline=='2026-10-20T10:01:55Z','460_DEADLINE')
    calculated=planned_budget();require(calculated['ticks']==326346 and calculated['worlds']==1715,'460_PLANNED_ACCOUNTING')
    require(calculated['ticks']<=PLAN_CAPS['ticks'] and calculated['worlds']<=PLAN_CAPS['worlds'],'460_PLANNED_OVER_HARD')
    files=set(G.glob('retry/*460*.py'));files.update([G/'retry/compare457.py',G/'retry/budget456.py',G/'retry/design460.md',G/'retry/design459_next.md',G/'retry/compare459_result.json',root/'project-effective-budget-v474.json',root/'research-deadline-current.json'])
    files.update(Path(f) for f in old['sources'] if Path(f).suffix=='.py' and 'analyze453' not in str(f))
    for stage in [423,425,427,433,435]:files.update(f for f in (root/f'stage{stage}').rglob('*') if f.is_file())
    for arm,n in [('baseline',117),('candidate',113)]:
        files.update(f for f in (root/f'stage453/actual_{arm}').glob('*') if f.is_file())
        files.update([root/f'stage453/{arm}_decision{n-22}-before-actual-dispatch-private.json',root/f'stage453/{arm}_decision{n-22}_query-before-integration-private.json'])
    files.update([Path(old['fixed_plan']),Path(old['pace_path'])])
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=460,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],caps=PLAN_CAPS,planned_ticks=calculated['ticks'],planned_worlds=calculated['worlds'],budget_fixture=calculated,qualification_caps=dict(ticks=1674,worlds=47),order=ORDER,parent_cap=100,planner_cap=8,sources={str(f):sha(f) for f in sorted(files)},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],authorization='Explicit460 corrected four-planner-arm accounting; one fresh two-root model comparison; first global error stops; actual0; no repair/retry after opening.',actual_reset_seed_learning_HOLDOUT_SEALED_reserve_paid_cap=0,research_remaining=26695,reserve=84000,reserve_used=0,contract_sha256=sha(G/'retry/design460.md'),prefix_elapsed_s=dict(NoPulse=9.28,Pulse=8.96),storage_free_stop_bytes=512*1024**2)
    for group in ['protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'460_PROTECTED')
    for label in ['NoPulse','Pulse']:root_inputs(root,label)
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    save(d/'progress-private.json',dict(stage=460,phase='PLAN_FROZEN',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_ticks=0,model_worlds=0,actual_actions=0))
    print(json.dumps(dict(stage=460,plan_sha256=sha(d/'plan.json'),planned=calculated)))

class Comparison460(Planning456):
    def __init__(self,root,meter,fixed,pace,state,memory,ledger,rng):
        super().__init__(root,meter,fixed,pace,state,memory,ledger,rng);self.d=meter.d
        self.policy_digest=fingerprint(dict(contract=meter.p['contract_sha256'],semantic=meter.p['semantic_sources'],scope='BothRoots_first8eligible_then_guardian'))
    def policy460(self,name):
        base=name.split('-')[0];self.active_context=None;self.active_pending=None
        parent=self.new(self.state,self.memory,self.actual_ledger,'parent_'+name,tag='460_model_parent');self.assert_actual();planner_used=0;records=[];startticks=self.meter.b['ticks'];startworlds=self.meter.b['worlds']
        self.meter.context.update(arm=name,parent_action=0,planner_used=0)
        try:
            for index in range(100):
                if parent.status!='ACTIVE':break
                before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m);ctx=capture_context(parent.m,parent.ctrl,before,nominal,parent.ledger,self.fixed,self.policy_digest,self.archive_rng,self.actual_digest);label=name+'_decision'+str(index+1);self.active_pending=None
                pending_now=parent.m.finish_line_tracker.candidate_crossing_time_s is not None
                if pending_now:
                    self.active_pending=capture_pending(parent,ctx,before,self.meter.p['semantic_sources']);route=self.active_pending.validate(parent.stream.child_id,ctx)['gate'];save_receipt(self.d/(label+'-registered-pending-parent-private.json'),asdict(self.active_pending))
                else:
                    ctx.validate();route=ctx.gate();require(parent.ctrl.phase()=='FIRST_LAP' and route=='QUERY_CURRENT','460_CURRENT_GATE')
                self.active_context=ctx;self.meter.query_proof=self.meter.capture_inputs(snapshot(parent.m),before,ctx.ledger,label+'_query',context=ctx,gate=route)
                ph,mh,rh=fingerprint(snapshot(parent.m)),fingerprint(parent.ctrl.memory()),rnghash()
                _,planned=scope460(base,planner_used,parent.ctrl.phase(),pending_now)
                self.meter.context.update(parent_action=index,planner_used=planner_used);self.meter.checkpoint('PLANNER_QUERY' if planned else 'GUARDIAN_QUERY',current_decision=index+1)
                qc,qw=time.process_time(),time.perf_counter();selected=self.planning_query(parent,ctx,before,label) if planned else self.guardian(parent,ctx,before,label)
                if planned:planner_used+=1
                self.unchanged(parent,ph,mh,rh)
                save_receipt(self.d/(label+'-before-parent-step-private.json'),dict(context=asdict(ctx),query_proof=self.meter.query_proof,selected_recipe=selected['recipe'],first_command=selected['first']['command'],parent_unchanged=True,actual_execution_allowed=False))
                native_before=parent.m.native_ticks;parent.one('460_parent_'+name,first_override=selected['first']['command'],prepared_nominal=nominal,prepared_before=before)
                require(len(parent.rows)==index+1,'460_PARENT_NO_OBSERVED_ROW');check=compare_frames(parent.rows[-1],selected['first']);self.assert_actual();self.validate_child(parent)
                require(check['passed'] and check['wheel']['clipped_flag_mismatches']==0,'460_PARENT_SELECTED_FIRST_MISMATCH')
                own=None
                if self.active_pending is not None:own=verify_parent_step(self.active_pending,parent,native_before);save_receipt(self.d/(label+'-parent-own-confirmation-private.json'),dict(proof=own,pending_key=self.active_pending.key()))
                rec=dict(arm=name,decision=index+1,planner_used=planned,planner_quota_used=planner_used,recipe=selected['recipe'],route=route,phase=ctx.phase,query_CPU_s=time.process_time()-qc,query_wall_s=time.perf_counter()-qw,guardian_certificate=selected.get('certificate'),choice=selected.get('summary'),first_pass=check['passed'],own_pending=own,parent_status=parent.status,actual_execution_allowed=False)
                records.append(rec);self.decisions.append(rec);save(self.d/'decisions-private.json',self.decisions)
                self.meter.context.update(parent_action=len(parent.rows),planner_used=planner_used);self.meter.checkpoint('PARENT_TRANSITION_VERIFIED')
                print(json.dumps(dict(stage=460,arm=name,action=len(parent.rows),planner_used=planner_used,recipe=selected['recipe'],status=parent.status,model_ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])),flush=True)
                require(parent.status not in ['UNSAFE','INFEASIBLE','CENSORED'],'460_PARENT_UNSAFE_PROGRESS_NONFINISH')
            if parent.status=='ACTIVE':parent.status='SCOPE_CENSORED';parent.error='100parent_actions_no_aftercap_tail'
            out=dict(arm=name,status=parent.status,error=parent.error,parent_actions=len(parent.rows),planner_decisions=planner_used,guardian_decisions=len(records)-planner_used,finish_ticks=None if parent.finish_ticks is None else asdict(parent.finish_ticks),official_model_finish=parent.status=='FINISHED',signature=parent.signature(),model_ticks=self.meter.b['ticks']-startticks,model_worlds=self.meter.b['worlds']-startworlds+1,actual_root_unchanged=self.actual_ledger.digest()==self.actual_digest,actual_finish_witness=False,actual_DONE_allowed=False)
            self.results.append(out);save(self.d/'policy-results.json',self.results)
            if name.endswith('-2'):
                prior=next(x for x in self.results if x['arm']==base+'-1');require(prior['signature']==out['signature'],'460_FULL_ARM_REPEAT_MISMATCH')
            require(parent.status=='FINISHED','460_PARENT_SCOPE_CENSOR');return out
        finally:
            parent.dump(self.d);parent.close()

def qualify_root460(root,meter,fixed,pace,state,memory,ledger,expected,root_label):
    start=(meter.b['ticks'],meter.b['worlds']);records={};immutable=(fingerprint(state),fingerprint(memory),ledger.digest(),rnghash())
    for recipe in ['nominal','fullgas']:
        children=[];held=None;pair=[]
        try:
            meter.capture_inputs(state,memory,ledger,'root460_'+root_label+'_'+recipe+'_held',gate='SAVED_ROOT_QUALIFICATION')
            held=Child(meter,state,memory,ledger,fixed,pace,'root460_'+root_label+'_'+recipe+'_held',world_tag='460_root_held');before=copy.deepcopy(held.ctrl.memory());nominal=held.ctrl.act(held.m);stamp=(fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())
            for rep in [1,2]:
                label='root460_'+root_label+'_'+recipe+'_'+str(rep);meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='SAVED_ROOT_QUALIFICATION');c=Child(meter,state,memory,ledger,fixed,pace,label,recipe,world_tag='460_root_required' if rep==1 else '460_root_repeat');children.append(c);c.initial13('460_root_'+recipe);c.dump(meter.d)
                if recipe=='nominal':
                    factual=replay(c.rows,expected,fixed);require(factual['certified_prefix_actions']==13 and factual['fresh_current_first_pass']>=1,'460_ROOT_NATIVE_NOMINAL13');compare_first(ledger,c.rows[0],expected[0],fixed)
                elif not c.initial_ok:
                    require(c.status=='UNSAFE' and not c.ledger.deadline_missed and not c.ledger.done,'460_ROOT_UNSUPPORTED_EARLY')
                    from retry.audit431 import physical_tokens
                    physical_tokens(c.error)
                require((fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())==stamp,'460_HELD_CHANGED')
                pair.append(dict(signature=c.signature(),first=copy.deepcopy(c.rows[0]),status=c.status));c.close()
            require(pair[0]==pair[1],'460_ROOT_REPEAT')
            held.one('460_root_held_first',first_override=pair[0]['first']['command'],prepared_nominal=nominal,prepared_before=before);z=compare_frames(held.rows[0],pair[0]['first']);require(z['passed'] and not z['wheel']['clipped_flag_mismatches'],'460_ROOT_HELD_FIRST')
            records[recipe]=dict(repeat_exact=True,held_first_passed=True,status=pair[0]['status'],native_factual_qualified=recipe=='nominal',native_scope='Saved same-root nominal13 only; fullgas model consistency only')
        finally:
            for c in children:
                if not c.closed:c.dump(meter.d);c.close()
            if held:held.dump(meter.d);held.close()
        require((fingerprint(state),fingerprint(memory),ledger.digest(),rnghash())==immutable,'460_ROOT_INPUT_MUTATION')
    cost=(meter.b['ticks']-start[0],meter.b['worlds']-start[1]);require(cost[0]<=216 and cost[1]==6,'460_ROOT_QUAL_CAP');save(meter.d/('root-'+root_label+'-qualification-private.json'),dict(passed=True,records=records,ticks=cost[0],worlds=cost[1]));return records

def run(root):
    d=root/'stage460';p=read(d/'plan.json');require(not(d/'opening.json').exists() and read(d/'static-result.json')['passed'],'460_STATIC_OR_ONCE')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256'],'460_PLAN_STATIC_BINDING')
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'460_SOURCE_CHANGED:'+f)
    roots={label:root_inputs(root,label) for label in ['NoPulse','Pulse']};state,memory,ledger,rng,blob,expected=roots['NoPulse'];py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);meter=create_meter(d);pilot=None;status='STARTED';error=None;stage='qualification'
    save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),plan_sha256=sha(d/'plan.json'),static_sha256=sha(d/'static-result.json')))
    def timeout(*args):raise ResourceStop('460_worker_time_deadline')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};meter.timers()
    try:
        meter.checkpoint('FRESH_QUALIFICATION_STARTED')
        fork=read(root/'stage423/actual_C0/fork-private.json');oldstate=from_actual_full(fork);oldmem=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);oldledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(oldstate['physical']['actual_time']*50))
        qualify(root,meter,fixed,pace,oldstate,oldmem,oldledger);qualify_pending(root,meter,fixed,pace);meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
        require(meter.b['ticks']<=1242 and meter.b['worlds']==35,'460_OLD_QUAL_CAP')
        for root_label in ['NoPulse','Pulse']:
            state,memory,ledger,rng,blob,expected=roots[root_label];py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
            qualify_root460(root,meter,fixed,pace,state,memory,ledger,expected,root_label)
        require(meter.b['ticks']<=1674 and meter.b['worlds']==47,'460_FRESH_PREFLIGHT_CAP')
        save(d/'preflight-private.json',dict(passed=True,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual=0));meter.checkpoint('ALL_PREFLIGHT_PASSED')
        pilot=Comparison460(root,meter,fixed,pace,state,memory,ledger,rng);stage='four_model_parents'
        for name in p['order']:
            pilot.assert_actual();state,memory,ledger,rng,blob,expected=roots[name.split('-')[0]];py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
            pilot.state,pilot.memory,pilot.actual_ledger,pilot.archive_rng=state,memory,ledger,rng;pilot.actual_digest=ledger.digest()
            save_receipt(d/(name+'-root-binding-private.json'),dict(root=name.split('-')[0],state_digest=fingerprint(state),memory_digest=fingerprint(memory),actual_ledger_digest=ledger.digest(),global_RNG_digest=rnghash(),prefix_elapsed_s=p['prefix_elapsed_s'][name.split('-')[0]],actual_execution_allowed=False))
            pilot.policy460(name)
        status='FOUR_MODEL_PARENTS_COMPLETED_REPEAT_EXACT'
    except BaseException as e:
        status='STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc(),no_retry=True))
    finally:
        signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
        try:
            if pilot:
                for c in pilot.children:
                    if not c.closed:c.dump(d);c.close()
            meter.closeall()
        except BaseException as e:
            save(d/'cleanup-stop-private.json',dict(error=type(e).__name__+': '+str(e),original_error=error));status='STOP'
            if error is None:error=type(e).__name__+': '+str(e)
        for s,h in handlers.items():signal.signal(s,h)
    results=[] if pilot is None else pilot.results;gain=None
    if status=='FOUR_MODEL_PARENTS_COMPLETED_REPEAT_EXACT':
        a,b=results[:2];gain=[round(p['prefix_elapsed_s']['NoPulse']-p['prefix_elapsed_s']['Pulse']+(a['finish_ticks']['lo']-b['finish_ticks']['hi'])/50,8),round(p['prefix_elapsed_s']['NoPulse']-p['prefix_elapsed_s']['Pulse']+(a['finish_ticks']['hi']-b['finish_ticks']['lo'])/50,8)]
    meter.persist();out=dict(stage=460,status=status,error=error,last_stage=stage,policies=results,hybrid_total_NoPulse_minus_Pulse_bracket_s=gain,budget=meter.b,plan_sha256=sha(d/'plan.json'),new_actual_reset_seed_learning_HOLDOUT_SEALED_reserve_paid=0,actual_gate_opened=False,actual_finish_witness=False)
    save(d/'result.json',out);meter.checkpoint('CLOSED',status=status,error=error);print(json.dumps(dict(stage=460,status=status,error=error,policies=results,gain=gain,ticks=meter.b['ticks'],worlds=meter.b['worlds'])),flush=True)

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
