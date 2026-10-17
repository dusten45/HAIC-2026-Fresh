"""One authorized 461-contract model pair; no native entrypoint or repeat arm."""
import time
WORKER_START=time.perf_counter()
import copy,datetime,json,os,pickle,random,signal,sys,traceback,shutil,math
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.budget456 import Meter as BaseMeter,Planning456
from retry.budget461 import calculate
from retry.compare460 import qualify_root460
from retry.pilot420_backend import *
from retry.parent436 import capture_pending,verify_parent_step
from retry.qualify453 import qualify,qualify_pending
from retry.qualify_parent453 import qualify as qualify_parent
from retry.receipt421_io import load_receipt,save_receipt
from retry.terminal410_model import from_actual_full
from retry.pilot421_run import compare_frames
from retry.paired417_common import shapecheck
from retry.loss389_analyze import read,save,sha
from retry.ledger439 import require
from retry.scalar392_audit import pedals
G=Path(__file__).resolve().parents[1]

def contract():return read(G/'retry/design461_next.json')

def schedule462(p,name,index,phase,pending):
    choices={x['arm']:x['first_recipe'] for x in p['execution']['order']}
    require(name in choices and 0<=index<p['execution']['parent_cap'],'462_SCOPE')
    require(phase in ['FIRST_LAP','FINISH_CONFIRM'] and type(pending) is bool,'462_PHASE')
    if index==0:
        require(phase=='FIRST_LAP' and not pending,'462_FIRST_DOMAIN');return choices[name]
    return None

def secant_command(fixed,pace,pos,vel,nominal):
    line=np.asarray(fixed['line']);ds=np.asarray(fixed['free_profile']['ds']);nodes=np.asarray(fixed['free_profile']['speed'])*pace;arc=np.r_[0,np.cumsum(ds)]
    q=canonical_projection(line,pos,vel,'FIRST_LAP');s=q['arc'];sigma=q['sigma'];ahead=s+sigma*.08
    require(sigma>=0 and 0<s<ahead<arc[-1],'462_SECANT_DOMAIN')
    def target(where):
        j=int(np.searchsorted(arc,where,side='right')-1);u=(where-arc[j])/ds[j]
        return math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2)
    r=target(s);raw=(target(ahead)-r)/.08+1.5*(r-math.hypot(*vel));z=pedals(raw,math.hypot(*vel),fixed['model']);candidate=np.asarray(nominal,np.float32).copy();candidate[1:]=[z['gas'],z['brake']]
    expected=np.asarray(nominal,np.float32).copy();expected[1:]=[1.,0.]
    require(np.array_equal(candidate,expected),'462_SECANT_FULL_VECTOR_ALIAS');return candidate

class Meter462(BaseMeter):
    def guard(self):
        super().guard()
        if shutil.disk_usage(self.d).free<self.p['storage_free_stop_bytes']:raise ResourceStop('462_storage_reserve')
    def checkpoint(self,phase,**facts):
        q=super().checkpoint(phase,**facts);q['stage']=462;save(self.d/'progress-private.json',q);return q

def create_meter(d):return Meter462(d,start_wall=WORKER_START)

def root_inputs(root):
    d=root/'stage458';rows=[json.loads(x) for x in (d/'actual_P/trace-private.jsonl').read_text().splitlines()];n=126
    bundle=load_receipt(d/'P_decision14-before-actual-dispatch-private.json');src,memory,rng=Parent(**bundle['context']['parent']).fork_inputs();state=src['terminal_model'];ledger=GoalLedger(**bundle['context']['ledger'])
    native=load_receipt(d/'actual_P/P_step126-before-native-private.json');proof=load_receipt(d/'P_decision14_query-before-integration-private.json')
    require(state==from_actual_full(native['full_pre_before_nominal']) and memory==rows[n-1]['memory_before'],'462_ROOT_NATIVE')
    require(proof['state']==state and proof['memory']==memory and proof['ledger']==asdict(ledger),'462_ROOT_QUERY_PROOF')
    require(not ledger.done and not ledger.deadline_missed and state['finish_tracker']['candidate_crossing_time_s'] is None and state['finish_tracker']['finish_time_s'] is None,'462_ROOT_DOMAIN')
    expected=rows[n-1:];require(len(expected)>=13 and all(x['command']==x['nominal'] for x in expected),'462_FACTUAL_SUFFIX_NOMINAL')
    require(abs(rows[n-1]['progress_before']-rows[22]['progress_before']-522.6118488137196)<1e-8 and abs(rows[n-1]['pre']['time']-rows[0]['pre']['time']-10.)<1e-8,'462_ROOT_FROZEN')
    old=read(root/'stage453/plan.json');fixed=read(Path(old['fixed_plan']));pace=np.asarray(read(old['pace_path'])['frozen268']);secant_command(fixed,pace,rows[n-1]['pre']['pos'],rows[n-1]['pre']['vel'],rows[n-1]['nominal'])
    return state,memory,ledger,rng,proof['global_RNG_pickle'],expected

def prepare(root):
    d=root/'stage462';store=Path('/tmp/haic-retry-stage462-private');require(not d.exists() and not d.is_symlink() and not store.exists(),'462_ONCE_ONLY')
    c=contract();budget=calculate(c);require((budget['ticks'],budget['worlds'])==(43650,839),'462_SINGLE_BUDGET')
    free=shutil.disk_usage('/tmp').free;require(free>=budget['empirical_raw_bytes_at_hard_with_margin_and_reserve'],'462_STORAGE_PREFLIGHT')
    old=read(root/'stage453/plan.json');ledger=read(root/'project-effective-budget-v474.json');require((ledger['research_remaining'],ledger['final_reserved_actions'],ledger['final_reserve_used'])==(26695,84000,0),'462_LEDGER')
    deadline=read(root/'research-deadline-current.json')['deadline_utc'];require(deadline==c['deadline_utc']=='2026-10-20T10:01:55Z','462_DEADLINE')
    root_inputs(root)
    files=set(G.glob('retry/*462*.py'));files.update([G/'retry/design461_next.md',G/'retry/design461_next.json',G/'retry/budget461.py',G/'retry/budget456.py',G/'retry/compare460.py',root/'project-effective-budget-v474.json',root/'research-deadline-current.json'])
    files.update(Path(f) for f in old['sources'] if Path(f).suffix=='.py' and 'analyze453' not in str(f))
    for stage in [423,425,427,433,435]:files.update(f for f in (root/f'stage{stage}').rglob('*') if f.is_file())
    files.update(f for f in (root/'stage458/actual_P').glob('*') if f.is_file());files.update(root/('stage458/'+name) for name in ['P_decision14-before-actual-dispatch-private.json','P_decision14_query-before-integration-private.json']);files.update([Path(old['fixed_plan']),Path(old['pace_path'])])
    semantic=dict(old['semantic_sources']);semantic.update({str(f):sha(f) for f in files if str(f).startswith(str(G)) and f.suffix=='.py'})
    p=dict(stage=462,execution=c,caps=c['hard'],planned_ticks=budget['ticks'],planned_worlds=budget['worlds'],budget_fixture=budget,deadline_utc=deadline,fixed_plan=old['fixed_plan'],pace_path=old['pace_path'],order=[x['arm'] for x in c['order']],sources={str(f):sha(f) for f in sorted(files)},semantic_sources=semantic,protected=old['protected'],original408_preserve=old['original408_preserve'],contract_sha256=sha(G/'retry/design461_next.md'),contract_json_sha256=sha(G/'retry/design461_next.json'),storage_start_free_bytes=free,storage_free_stop_bytes=c['storage']['final_dump_reserve_bytes'],authorization='Explicit462 one model Original/SecantOnce pair under unchanged461 contract; actual0; no arm repeat; first80ms only; first global error stops, no repair/retry.')
    for group in ['protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'462_PROTECTED')
    store.mkdir(mode=0o700);d.symlink_to(store,target_is_directory=True);save(d/'plan.json',p);(d/'plan.sha256').write_text(sha(d/'plan.json')+'\n');save(root/'stage462-plan-durable-private.json',p)
    save(d/'progress-private.json',dict(stage=462,phase='PLAN_FROZEN',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),model_ticks=0,model_worlds=0,actual_actions=0))
    print(json.dumps(dict(stage=462,planned=budget,storage_start_free_bytes=free,plan_sha256=sha(d/'plan.json'))))

class Comparison462(Planning456):
    def __init__(self,root,meter,fixed,pace,state,memory,ledger,rng,expected):
        super().__init__(root,meter,fixed,pace,state,memory,ledger,rng);self.d=meter.d;self.expected=expected
        self.policy_digest=fingerprint(dict(contract=meter.p['contract_sha256'],semantic=meter.p['semantic_sources'],scope='FixedFirstOriginalOrSecantAliasThenSameGuardian'))
    def fixed_first(self,parent,ctx,before,label,name,recipe):
        if name=='SecantOnce':secant_command(self.fixed,self.pace,list(parent.m.car.hull.position),list(parent.m.car.hull.linearVelocity),ctx.nominal)
        selected=self.short_pair(parent,ctx,before,label,recipe);require(selected['valid'],'462_FIXED_FIRST_INELIGIBLE_NO_FALLBACK');return selected
    def dispatch_query(self,parent,ctx,before,label,name,recipe):
        return self.fixed_first(parent,ctx,before,label,name,recipe) if recipe else self.guardian(parent,ctx,before,label)
    def policy462(self,name):
        self.active_context=None;self.active_pending=None
        parent=self.new(self.state,self.memory,self.actual_ledger,'parent_'+name,tag='462_model_parent');self.assert_actual();records=[];startticks=self.meter.b['ticks'];startworlds=self.meter.b['worlds'];factual=0;factual_live=True;factual_command_divergence=None
        self.meter.context.update(arm=name,parent_action=0,planner_used=0)
        try:
            for index in range(self.meter.p['execution']['parent_cap']):
                if parent.status!='ACTIVE':break
                before=copy.deepcopy(parent.ctrl.memory());nominal=parent.ctrl.act(parent.m);ctx=capture_context(parent.m,parent.ctrl,before,nominal,parent.ledger,self.fixed,self.policy_digest,self.archive_rng,self.actual_digest);label=name+'_decision'+str(index+1);self.active_pending=None
                pending_now=parent.m.finish_line_tracker.candidate_crossing_time_s is not None
                if pending_now:
                    self.active_pending=capture_pending(parent,ctx,before,self.meter.p['semantic_sources']);route=self.active_pending.validate(parent.stream.child_id,ctx)['gate'];save_receipt(self.d/(label+'-registered-pending-parent-private.json'),asdict(self.active_pending))
                else:
                    ctx.validate();route=ctx.gate();require(parent.ctrl.phase()=='FIRST_LAP' and route=='QUERY_CURRENT','462_CURRENT_GATE')
                self.active_context=ctx;self.meter.query_proof=self.meter.capture_inputs(snapshot(parent.m),before,ctx.ledger,label+'_query',context=ctx,gate=route)
                ph,mh,rh=fingerprint(snapshot(parent.m)),fingerprint(parent.ctrl.memory()),rnghash()
                fixed_recipe=schedule462(self.meter.p,name,index,parent.ctrl.phase(),pending_now);self.meter.context.update(parent_action=index);self.meter.checkpoint('FIXED_FIRST_QUERY' if fixed_recipe else 'GUARDIAN_QUERY',current_decision=index+1)
                qc,qw=time.process_time(),time.perf_counter();selected=self.dispatch_query(parent,ctx,before,label,name,fixed_recipe)
                self.unchanged(parent,ph,mh,rh);save_receipt(self.d/(label+'-before-parent-step-private.json'),dict(context=asdict(ctx),query_proof=self.meter.query_proof,selected_recipe=selected['recipe'],first_command=selected['first']['command'],parent_unchanged=True,actual_execution_allowed=False))
                native_before=parent.m.native_ticks;parent.one('462_parent_'+name,first_override=selected['first']['command'],prepared_nominal=nominal,prepared_before=before)
                require(len(parent.rows)==index+1,'462_PARENT_NO_ROW');check=compare_frames(parent.rows[-1],selected['first']);self.assert_actual();self.validate_child(parent);require(check['passed'] and not check['wheel']['clipped_flag_mismatches'],'462_SELECTED_FIRST_MISMATCH')
                if name=='Original':
                    require(index<len(self.expected),'462_ORIGINAL_BEYOND_FACTUAL_SUFFIX');target=self.expected[index];frame=parent.rows[-1]
                    same=np.array_equal(np.asarray(frame['command'],np.float32),np.asarray(target['command'],np.float32))
                    if factual_live and not same:factual_live=False;factual_command_divergence=index+1
                    if factual_live:
                        comparison=shapecheck(frame,target);require(comparison['passed'] and not comparison['wheel']['clipped_flag_mismatches'],'462_ORIGINAL_FACTUAL_SUFFIX_MISMATCH');factual+=1
                own=None
                if self.active_pending is not None:own=verify_parent_step(self.active_pending,parent,native_before);save_receipt(self.d/(label+'-parent-own-confirmation-private.json'),dict(proof=own,pending_key=self.active_pending.key()))
                rec=dict(arm=name,decision=index+1,fixed_first=fixed_recipe is not None,recipe=selected['recipe'],route=route,phase=ctx.phase,query_CPU_s=time.process_time()-qc,query_wall_s=time.perf_counter()-qw,guardian_certificate=selected.get('certificate'),first_pass=check['passed'],own_pending=own,parent_status=parent.status,actual_execution_allowed=False)
                records.append(rec);self.decisions.append(rec);save(self.d/'decisions-private.json',self.decisions);self.meter.context.update(parent_action=len(parent.rows));self.meter.checkpoint('PARENT_TRANSITION_VERIFIED')
                print(json.dumps(dict(stage=462,arm=name,action=len(parent.rows),recipe=selected['recipe'],status=parent.status,model_ticks=self.meter.b['ticks'],worlds=self.meter.b['worlds'])),flush=True);require(parent.status not in ['UNSAFE','INFEASIBLE','CENSORED'],'462_PARENT_UNSAFE_PROGRESS_NONFINISH')
            if parent.status=='ACTIVE':parent.status='SCOPE_CENSORED';parent.error='100parent_actions_no_aftercap_tail'
            out=dict(arm=name,status=parent.status,error=parent.error,parent_actions=len(parent.rows),fixed_first_queries=sum(x['fixed_first'] for x in records),guardian_decisions=sum(not x['fixed_first'] for x in records),finish_ticks=None if parent.finish_ticks is None else asdict(parent.finish_ticks),official_model_finish=parent.status=='FINISHED',signature=parent.signature(),model_ticks=self.meter.b['ticks']-startticks,model_worlds=self.meter.b['worlds']-startworlds+1,original_factual_same_control_rows=factual,original_first_command_divergence=factual_command_divergence,actual_root_unchanged=self.actual_ledger.digest()==self.actual_digest,actual_finish_witness=False,whole_arm_repeated=False)
            self.results.append(out);save(self.d/'policy-results.json',self.results);require(parent.status=='FINISHED','462_PARENT_SCOPE_CENSOR');return out
        finally:parent.dump(self.d);parent.close()

def run(root):
    d=root/'stage462';p=read(d/'plan.json');require(not(d/'opening.json').exists() and read(d/'static-result.json')['passed'],'462_STATIC_OR_ONCE')
    require(sha(d/'plan.json')==(d/'plan.sha256').read_text().strip()==read(d/'static-result.json')['plan_sha256'],'462_PLAN_STATIC_BINDING')
    require(p['execution']==contract() and p['caps']==p['execution']['hard'] and calculate(p['execution'])==p['budget_fixture'],'462_SINGLE_SETTING')
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():require(sha(f)==h,'462_SOURCE_CHANGED:'+f)
    require(shutil.disk_usage(d).free>=p['budget_fixture']['empirical_raw_bytes_at_hard_with_margin_and_reserve'],'462_START_STORAGE')
    state,memory,ledger,rng,blob,expected=root_inputs(root);py,npr=pickle.loads(blob);random.setstate(py);np.random.set_state(npr)
    fixed=read(Path(p['fixed_plan']));pace=np.asarray(read(p['pace_path'])['frozen268']);meter=create_meter(d);pilot=None;status='STARTED';error=None;stage='qualification'
    save(d/'opening.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),pid=os.getpid(),plan_sha256=sha(d/'plan.json'),static_sha256=sha(d/'static-result.json')))
    def timeout(*args):raise ResourceStop('462_worker_time_deadline')
    handlers={s:signal.signal(s,timeout) for s in [signal.SIGPROF,signal.SIGALRM]};meter.timers()
    try:
        meter.checkpoint('FRESH_QUALIFICATION_STARTED');fork=read(root/'stage423/actual_C0/fork-private.json');oldstate=from_actual_full(fork);oldmem=fork['controller']['before'];row=json.loads((root/'stage423/actual_C0/trace-private.jsonl').read_text().splitlines()[118]);oldledger=GoalLedger(row['progress_before'],row['goal_before'],H-(row['deadline_before']-118),round(oldstate['physical']['actual_time']*50))
        qualify(root,meter,fixed,pace,oldstate,oldmem,oldledger);qualify_pending(root,meter,fixed,pace);meter.qualification_passed=True;qualify_parent(root,meter,fixed,pace);require(meter.b['ticks']<=1242 and meter.b['worlds']==35,'462_OLD_QUAL_CAP')
        random.setstate(py);np.random.set_state(npr);qualify_root460(root,meter,fixed,pace,state,memory,ledger,expected[:13],'462SecantRoot');require(meter.b['ticks']<=1458 and meter.b['worlds']==41,'462_PREFLIGHT_CAP')
        save(d/'preflight-private.json',dict(passed=True,ticks=meter.b['ticks'],worlds=meter.b['worlds'],actual=0));meter.checkpoint('ALL_PREFLIGHT_PASSED')
        pilot=Comparison462(root,meter,fixed,pace,state,memory,ledger,rng,expected);stage='two_model_parents'
        for name in p['order']:
            pilot.assert_actual();random.setstate(py);np.random.set_state(npr);save_receipt(d/(name+'-root-binding-private.json'),dict(state_digest=fingerprint(state),memory_digest=fingerprint(memory),actual_ledger_digest=ledger.digest(),global_RNG_digest=rnghash(),observed_prefix_elapsed_s=10.,actual_execution_allowed=False));pilot.policy462(name)
        status='TWO_MODEL_PARENTS_COMPLETED_NO_ARM_REPEAT'
    except BaseException as e:status='STOP';error=type(e).__name__+': '+str(e);save(d/'stop-private.json',dict(stage=stage,error=error,traceback=traceback.format_exc(),no_retry=True))
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
    if status=='TWO_MODEL_PARENTS_COMPLETED_NO_ARM_REPEAT':
        a,b=results;gain=[(a['finish_ticks']['lo']-b['finish_ticks']['hi'])/50,(a['finish_ticks']['hi']-b['finish_ticks']['lo'])/50]
    meter.persist();out=dict(stage=462,status=status,error=error,last_stage=stage,policies=results,model_tail_Original_minus_SecantOnce_bracket_s=gain,budget=meter.b,plan_sha256=sha(d/'plan.json'),new_actual_reset_seed_learning_HOLDOUT_SEALED_reserve_paid=0,actual_gate_opened=False,actual_finish_witness=False,whole_arm_repeated=False)
    save(d/'result.json',out);meter.checkpoint('CLOSED',status=status,error=error);print(json.dumps(dict(stage=462,status=status,error=error,policies=results,gain=gain,ticks=meter.b['ticks'],worlds=meter.b['worlds'])),flush=True)

if __name__=='__main__':prepare(Path(sys.argv[2])) if sys.argv[1]=='prepare' else run(Path(sys.argv[2]))
