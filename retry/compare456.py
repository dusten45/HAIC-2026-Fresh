"""Once-only455 contract: four independent MODEL parents, no native entrypoint."""
import time
WORKER_START=time.perf_counter()
import copy,datetime,json,os,pickle,random,signal,sys,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.budget456 import Meter,Planning456
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
PLAN_CAPS=dict(ticks=212992,worlds=1792,CPU_s=6000,wall_s=9000,max_parallel=1)

def scope456(name,planner_used,phase,pending=False):
    require(name in ['C0','P'] and type(planner_used) is int and planner_used>=0,'456_SCOPE_INPUT')
    require(phase in ['FIRST_LAP','FINISH_CONFIRM'] and type(pending) is bool,'456_SCOPE_PHASE')
    return 100,name=='P' and planner_used<8 and phase=='FIRST_LAP' and not pending

def root_inputs(root,p=None):
    d=root/'stage453';rows=[json.loads(x) for x in (d/'actual_candidate/trace-private.jsonl').read_text().splitlines()]
    origin=rows[22]['progress_before'];n=next(r['step'] for r in rows if r['progress_before']>=origin+450.)
    require(n==113,'456_ROOT_FIRST_PRE450')
    bundle=load_receipt(d/f'candidate_decision{n-22}-before-actual-dispatch-private.json')
    parent=Parent(**bundle['context']['parent']);src,memory,rng=parent.fork_inputs();state=src['terminal_model'];ledger=GoalLedger(**bundle['context']['ledger'])
    before=load_receipt(d/f'actual_candidate/candidate_step{n}-before-native-private.json')
    require(state==from_actual_full(before['full_pre_before_nominal']) and memory==rows[n-1]['memory_before'],'456_ROOT_NATIVE_SOURCE')
    require(not ledger.done and not ledger.deadline_missed and state['finish_tracker']['candidate_crossing_time_s'] is None and state['finish_tracker']['finish_time_s'] is None,'456_ROOT_DOMAIN')
    expected=rows[n-1:n+12];require(len(expected)==13 and all(x['command']==x['nominal'] for x in expected),'456_ROOT_FACTUAL_NOMINAL13')
    proof=load_receipt(d/f'candidate_decision{n-22}_query-before-integration-private.json')
    require(proof['memory']==memory and proof['ledger']==asdict(ledger) and proof['state']==state,'456_ROOT_INPUT_PROOF')
    return state,memory,ledger,rng,proof['global_RNG_pickle'],expected

def prepare(root):
    d=root/'stage456';require(not d.exists(),'456_ONCE_ONLY');d.mkdir(mode=0o700)
    old=read(root/'stage453/plan.json');v=read(root/'project-effective-budget-v473.json');deadline=read(root/'research-deadline-current.json')['deadline_utc']
    require((v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(27059,84000,0),'456_LEDGER')
    require(deadline=='2026-10-20T10:01:55Z','456_DEADLINE')
    files=set(G.glob('retry/*456*.py'));files.update([G/'retry/design455.md',G/'retry/saved454_result.json',root/'project-effective-budget-v473.json',root/'research-deadline-current.json'])
    # Source implementations from frozen453/442 remain unchanged. Saved analysis
    # is deliberately outside semantic physics; freeze all selected new sources.
    files.update(Path(f) for f in old['sources'] if Path(f).suffix=='.py' and 'analyze453' not in str(f))
    for stage in [423,425,427,433,435]:files.update(f for f in (root/f'stage{stage}').rglob('*') if f.is_file())
    files.update(f for f in (root/'stage453/actual_candidate').glob('*') if f.is_file())
    files.update([root/'stage453/candidate_decision91-before-actual-dispatch-private.json',root/'stage453/candidate_decision91_query-before-integration-private.json',Path(old['fixed_plan']),Path(old['pace_path'])])
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=456,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=deadline,fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],caps=PLAN_CAPS,planned_ticks=206194,planned_worlds=1677,qualification_caps=dict(ticks=1458,worlds=41),order=['C0-1','P-1','C0-2','P-2'],parent_cap=100,planner_cap=8,sources={str(f):sha(f) for f in sorted(files)},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],authorization='Explicit456 execute single455 bounded model comparison; first global error stops; no repair/retry after opening.',actual_reset_seed_learning_HOLDOUT_SEALED_reserve_paid_cap=0,research_remaining=27059,reserve=84000,reserve_used=0,contract_sha256=sha(G/'retry/design455.md'))
    for group in ['protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'456_PROTECTED')
    root_inputs(root,p)
    save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n')
    save(d/'progress-private.json',dict(stage=456,phase='PLAN_FROZEN',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_ticks=0,model_worlds=0,actual_actions=0))
    print(json.dumps(dict(stage=456,plan_sha256=sha(d/'plan.json'),planned_ticks=206194,planned_worlds=1677)))

class Comparison456(Planning456):
    def __init__(self,root,meter,fixed,pace,state,memory,ledger,rng):
        super().__init__(root,meter,fixed,pace,state,memory,ledger,rng);self.d=meter.d
        self.policy_digest=fingerprint(dict(contract=meter.p['contract_sha256'],semantic=meter.p['semantic_sources'],scope='C0guardian_Pfirst8eligible_then_guardian'))
    def policy456(self,name):
        base=name.split('-')[0];self.active_context=None;self.active_pending=None
        parent=self.new(self.state,self.memory,self.actual_ledger,'parent_'+name,tag='456_model_parent');self.assert_actual();planner_used=0;records=[];startticks=self.meter.b['ticks'];startworlds=self.meter.b['worlds']
        self.meter.context.update(arm=name,parent_action=0,planner_used=0)
        try:
            for index in range(100):
                if parent.status!='ACTIVE':break
                before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m);ctx=capture_context(parent.m,parent.ctrl,before,nominal,parent.ledger,self.fixed,self.policy_digest,self.archive_rng,self.actual_digest);label=name+'_decision'+str(index+1);self.active_pending=None
                pending_now=parent.m.finish_line_tracker.candidate_crossing_time_s is not None
                if pending_now:
                    self.active_pending=capture_pending(parent,ctx,before,self.meter.p['semantic_sources']);route=self.active_pending.validate(parent.stream.child_id,ctx)['gate'];save_receipt(self.d/(label+'-registered-pending-parent-private.json'),asdict(self.active_pending))
                else:
                    ctx.validate();route=ctx.gate();require(parent.ctrl.phase()=='FIRST_LAP' and route=='QUERY_CURRENT','456_CURRENT_GATE')
                self.active_context=ctx;self.meter.query_proof=self.meter.capture_inputs(snapshot(parent.m),before,ctx.ledger,label+'_query',context=ctx,gate=route)
                ph,mh,rh=fingerprint(snapshot(parent.m)),fingerprint(parent.ctrl.memory()),rnghash()
                _,planned=scope456(base,planner_used,parent.ctrl.phase(),pending_now)
                self.meter.context.update(parent_action=index,planner_used=planner_used);self.meter.checkpoint('PLANNER_QUERY' if planned else 'GUARDIAN_QUERY',current_decision=index+1)
                qc,qw=time.process_time(),time.perf_counter();selected=self.planning_query(parent,ctx,before,label) if planned else self.guardian(parent,ctx,before,label)
                if planned:planner_used+=1
                self.unchanged(parent,ph,mh,rh)
                save_receipt(self.d/(label+'-before-parent-step-private.json'),dict(context=asdict(ctx),query_proof=self.meter.query_proof,selected_recipe=selected['recipe'],first_command=selected['first']['command'],parent_unchanged=True,actual_execution_allowed=False))
                native_before=parent.m.native_ticks;parent.one('456_parent_'+name,first_override=selected['first']['command'],prepared_nominal=nominal,prepared_before=before)
                require(len(parent.rows)==index+1,'456_PARENT_NO_OBSERVED_ROW');check=compare_frames(parent.rows[-1],selected['first']);self.assert_actual();self.validate_child(parent)
                require(check['passed'] and check['wheel']['clipped_flag_mismatches']==0,'456_PARENT_SELECTED_FIRST_MISMATCH')
                own=None
                if self.active_pending is not None:own=verify_parent_step(self.active_pending,parent,native_before);save_receipt(self.d/(label+'-parent-own-confirmation-private.json'),dict(proof=own,pending_key=self.active_pending.key()))
                rec=dict(arm=name,decision=index+1,planner_used=planned,planner_quota_used=planner_used,recipe=selected['recipe'],route=route,phase=ctx.phase,query_CPU_s=time.process_time()-qc,query_wall_s=time.perf_counter()-qw,guardian_certificate=selected.get('certificate'),choice=selected.get('summary'),first_pass=check['passed'],own_pending=own,parent_status=parent.status,actual_execution_allowed=False)
                records.append(rec);self.decisions.append(rec);save(self.d/'decisions-private.json',self.decisions)
                self.meter.context.update(parent_action=len(parent.rows),planner_used=planner_used);self.meter.checkpoint('PARENT_TRANSITION_VERIFIED')
                print(json.dumps(dict(stage=456,arm=name,action=len(parent.rows),planner_used=planner_used,recipe=selected['recipe'],status=parent.status,model_ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])),flush=True)
                require(parent.status not in ['UNSAFE','INFEASIBLE','CENSORED'],'456_PARENT_UNSAFE_PROGRESS_NONFINISH')
            if parent.status=='ACTIVE':parent.status='SCOPE_CENSORED';parent.error='100parent_actions_no_aftercap_tail'
            out=dict(arm=name,status=parent.status,error=parent.error,parent_actions=len(parent.rows),planner_decisions=planner_used,guardian_decisions=len(records)-planner_used,finish_ticks=None if parent.finish_ticks is None else asdict(parent.finish_ticks),official_model_finish=parent.status=='FINISHED',signature=parent.signature(),model_ticks=self.meter.b['ticks']-startticks,model_worlds=self.meter.b['worlds']-startworlds+1,actual_root_unchanged=self.actual_ledger.digest()==self.actual_digest,actual_finish_witness=False,actual_DONE_allowed=False)
            self.results.append(out);save(self.d/'policy-results.json',self.results)
            if name.endswith('-2'):
                prior=next(x for x in self.results if x['arm']==base+'-1');require(prior['signature']==out['signature'],'456_FULL_ARM_REPEAT_MISMATCH')
            require(parent.status=='FINISHED','456_PARENT_SCOPE_CENSOR');return out
        finally:
            parent.dump(self.d);parent.close()

def qualify_root456(root,meter,fixed,pace,state,memory,ledger,expected):
    start=(meter.b['ticks'],meter.b['worlds']);records={};immutable=(fingerprint(state),fingerprint(memory),ledger.digest(),rnghash())
    for recipe in ['nominal','fullgas']:
        children=[];held=None;pair=[]
        try:
            meter.capture_inputs(state,memory,ledger,'root456_'+recipe+'_held',gate='SAVED_ROOT_QUALIFICATION')
            held=Child(meter,state,memory,ledger,fixed,pace,'root456_'+recipe+'_held',world_tag='456_root_held');before=copy.deepcopy(held.ctrl.memory());nominal=held.ctrl.act(held.m);stamp=(fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())
            for rep in [1,2]:
                label='root456_'+recipe+'_'+str(rep);meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='SAVED_ROOT_QUALIFICATION');c=Child(meter,state,memory,ledger,fixed,pace,label,recipe,world_tag='456_root_required' if rep==1 else '456_root_repeat');children.append(c);c.initial13('456_root_'+recipe);c.dump(meter.d)
                if recipe=='nominal':
                    factual=replay(c.rows,expected,fixed);require(factual['certified_prefix_actions']==13 and factual['fresh_current_first_pass']>=1,'456_ROOT_NATIVE_NOMINAL13');compare_first(ledger,c.rows[0],expected[0],fixed)
                elif not c.initial_ok:
                    require(c.status=='UNSAFE' and not c.ledger.deadline_missed and not c.ledger.done,'456_ROOT_UNSUPPORTED_EARLY')
                    from retry.audit431 import physical_tokens
                    physical_tokens(c.error)
                require((fingerprint(snapshot(held.m)),fingerprint(held.ctrl.memory()),rnghash())==stamp,'456_HELD_CHANGED')
                pair.append(dict(signature=c.signature(),first=copy.deepcopy(c.rows[0]),status=c.status));c.close()
            require(pair[0]==pair[1],'456_ROOT_REPEAT')
            held.one('456_root_held_first',first_override=pair[0]['first']['command'],prepared_nominal=nominal,prepared_before=before);z=compare_frames(held.rows[0],pair[0]['first']);require(z['passed'] and not z['wheel']['clipped_flag_mismatches'],'456_ROOT_HELD_FIRST')
            records[recipe]=dict(repeat_exact=True,held_first_passed=True,status=pair[0]['status'],native_factual_qualified=recipe=='nominal',native_scope='Saved same-root nominal13 only; fullgas model consistency only')
        finally:
            for c in children:
                if not c.closed:c.dump(meter.d);c.close()
            if held:held.dump(meter.d);held.close()
        require((fingerprint(state),fingerprint(memory),ledger.digest(),rnghash())==immutable,'456_ROOT_INPUT_MUTATION')
    cost=(meter.b['ticks']-start[0],meter.b['worlds']-start[1]);require(cost[0]<=216 and cost[1]==6,'456_ROOT_QUAL_CAP');save(meter.d/'root-qualification-private.json',dict(passed=True,records=records,ticks=cost[0],worlds=cost[1]));return records

def run(root):
    d=root/'stage456';p=read(d/'plan.json');require(not(d/'opening.json').exists() and read(d/'static-result.json')['passed'],'456_STATIC_OR_ONCE')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256'],'456_PLAN_STATIC_BINDING')
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'456_SOURCE_CHANGED:'+f)
    state,memory,ledger,rng,blob,expected=root_inputs(root,p);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);meter=Meter(d,start_wall=WORKER_START);pilot=None;status='STARTED';error=None;stage='qualification'
    save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),plan_sha256=sha(d/'plan.json'),static_sha256=sha(d/'static-result.json')))
    def timeout(*args):raise ResourceStop('456_worker_time_deadline')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};meter.timers()
    try:
        meter.checkpoint('FRESH_QUALIFICATION_STARTED')
        fork=read(root/'stage423/actual_C0/fork-private.json');oldstate=from_actual_full(fork);oldmem=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);oldledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(oldstate['physical']['actual_time']*50))
        qualify(root,meter,fixed,pace,oldstate,oldmem,oldledger);qualify_pending(root,meter,fixed,pace);meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace)
        require(meter.b['ticks']<=1242 and meter.b['worlds']==35,'456_OLD_QUAL_CAP')
        qualify_root456(root,meter,fixed,pace,state,memory,ledger,expected)
        require(meter.b['ticks']<=1458 and meter.b['worlds']==41,'456_FRESH_PREFLIGHT_CAP')
        save(d/'preflight-private.json',dict(passed=True,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual=0));meter.checkpoint('ALL_PREFLIGHT_PASSED')
        pilot=Comparison456(root,meter,fixed,pace,state,memory,ledger,rng);stage='four_model_parents'
        for name in p['order']:pilot.policy456(name)
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
        a,b=results[:2];gain=[(a['finish_ticks']['lo']-b['finish_ticks']['hi'])/50,(a['finish_ticks']['hi']-b['finish_ticks']['lo'])/50]
    meter.persist();out=dict(stage=456,status=status,error=error,last_stage=stage,policies=results,model_remaining_finish_gain_bracket_s=gain,budget=meter.b,plan_sha256=sha(d/'plan.json'),new_actual_reset_seed_learning_HOLDOUT_SEALED_reserve_paid=0,actual_gate_opened=False,actual_finish_witness=False)
    save(d/'result.json',out);meter.checkpoint('CLOSED',status=status,error=error);print(json.dumps(dict(stage=456,status=status,error=error,policies=results,gain=gain,ticks=meter.b['ticks'],worlds=meter.b['worlds'])),flush=True)

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
