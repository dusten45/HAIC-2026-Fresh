"""485 charged native common-prefix bootstrap; no execution on import.

Fresh native observations alone establish prefix facts. No legacy recorded
prefix/forecast receipt is fabricated; a later source485 gate qualifies witness.
"""
import copy,hashlib,json,pickle,time,traceback
from dataclasses import asdict
from pathlib import Path
import numpy as np
from retry.authority439 import NativeAuthority439
from retry.planner419 import GoalLedger
from retry.planner419_model_ledger import ForecastLedger
from retry.paired417_common import ActualC,Trace
from retry.fork394_run import complete_state
from retry.terminal410_model import from_actual_full
from retry.loss389_replay import sensor
from retry.executor397 import canonical_projection
from retry.pilot420_backend import TechnicalStop,ResourceStop,fingerprint,rnghash
from retry.ledger439 import require,LedgerStop439
from retry.racing258_plan import solve
from retry.racing258_feasibility import project
from retry.pace268_profile import multipliers
from retry.analyze466 import project_four
from retry.loss389_analyze import sha,read
from retry.signed417_executor import ExecutorDomainError

COEFFICIENT_SHA='ea31d5a16b94b92e860635727ff9421d07e4db7eb987ec757dfff5645ef73c9b'
RULE='485_NEW_CASE_NATURAL_P4_COMMON_NATIVE_PREFIX_FIRST_QUARTER_BEFORE_WITNESS'

class PreparationIneligible485(RuntimeError):
    def __init__(self,reason,details=None):
        super().__init__(reason);self.details=details


def plain485(value):
    if isinstance(value,np.ndarray):return value.tolist()
    if isinstance(value,np.generic):return value.item()
    if isinstance(value,dict):return {k:plain485(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [plain485(v) for v in value]
    return value


def native_model485(env):
    """Original258 mass recipe from the already charged native car; no probe."""
    car=env.unwrapped.car;mass=float(car.hull.mass+sum(w.mass for w in car.wheels))
    require(np.isfinite(mass) and mass>0,'485_NATIVE_MASS')
    return dict(mass=mass,effective_mass=mass+4*1.6/.54**2,rear_traction_accel=.8*800/(mass+2*1.6/.54**2),brake_accel=.3*(4*1.6*15/(.02*.54))/(mass+4*1.6/.54**2),lateral_accel=.4*1600/mass)


def geometry485(snapshot,model,coefficients):
    fixed=plain485(solve(snapshot,model));require(fixed['model_calls']==194,'485_ONE_SOLVE194');fixed['model']=model;fixed['whole_map_GT']=True;repair=None
    if not fixed['free_feasible'] and min(fixed['free_clearance'])>=-.001 and fixed['free_profile']['max_abs_curvature']<=np.tan(.4)/3.24:
        try:
            repaired=project(snapshot,fixed)
            require(repaired['geometry_evaluations']<=100,'485_REPAIR100')
            repair=plain485({k:v for k,v in repaired.items() if k not in ['line','coefficients','profile','clearance']})
            fixed.update(line=plain485(repaired['line']),coefficients=plain485(repaired['coefficients']),free_profile=plain485(repaired['profile']),free_clearance=plain485(repaired['clearance']),free_feasible=True)
        except AssertionError:repair=dict(failed=True)
    fixed['numerical_projection']=repair
    if not fixed['free_feasible']:raise PreparationIneligible485('geometry_not_feasible_no_replacement',fixed)
    ds=np.asarray(fixed['free_profile']['ds']);curvature=np.asarray(fixed['free_profile']['curvature']);speed=np.asarray(fixed['free_profile']['speed'])
    require(np.array_equal(speed*multipliers([0,0,0],curvature,ds,model),speed*1.5),'485_ZERO_COEFFICIENT_REFERENCE_IDENTITY')
    pace=multipliers(coefficients,curvature,ds,model);scaled=speed*pace;nodes=project_four(scaled,ds,model)
    require(nodes[0]==0 and np.isfinite(nodes).all() and np.all(nodes[1:]>0) and np.all(nodes<=scaled),'485_CASE_P4_NODES')
    nodes.setflags(write=False)
    return fixed,pace,nodes


class NativePrefix485(NativeAuthority439):
    """Own-native fact commit only; explicitly no forecast verification claim."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.global_step=0;self.nominal=None
    def commit_prefix_fact485(self):
        require(not self.halted and not self.awaiting_verification,'485_PREFIX_SEQUENCE')
        row,observed=self.observed_row();previous=self.ledger
        row.update(step=self.global_step,nominal=copy.deepcopy(self.nominal),deadline_before=self.global_step-1+13-previous.age_actions)
        self._ledger=observed;self.rows.append(copy.deepcopy(row));self.dispatcher.consume(self.ticket);self.ticket=None;self.prepared=None
        return dict(row=row,ledger_before=asdict(previous),ledger_after=asdict(observed),own_native_fact=True,model_forecast_read=False,source_fidelity_qualified=False)


def prepare_case(case,meter,quota,root,*,coefficients_path,identity_check):
    """One assigned case, one reset, natural prefix+one witness; closes native.

    meter: begin_actual/end_actual, geometry(slot) context, charge four kinds,
    guard/checkpoint. quota: native_dir and save/save_receipt. No ledger writes
    occur here outside meter.charge's authorized transaction.
    """
    from retry.diagnose import make_env
    slot=case['slot'];require(slot in ['D485-A','D485-B'],'485_SLOT')
    identity=case['case_identity_digest'];require(type(identity) is str and len(identity)==64,'485_ASSIGNED_IDENTITY_DIGEST')
    require(callable(identity_check) and sha(coefficients_path)==COEFFICIENT_SHA,'485_COEFFICIENT_OR_IDENTITY_SOURCE')
    coefficient_data=read(Path(coefficients_path));coefficients=coefficient_data['coefficients'] if isinstance(coefficient_data,dict) else coefficient_data
    require(np.asarray(coefficients).shape==(3,),'485_FROZEN_COEFFICIENT_SHAPE')
    folder=Path(quota.native_dir)/slot;require(not folder.exists(),'485_ONCE_CASE_DIRECTORY');folder.mkdir(mode=0o700)
    counts=dict(slot_actions=0,slot_resets=0,slot_reset_raw=0,slot_action_raw=0);events=[];env=ctrl=native=trace=None;material=None;root_context=None;witness=None;initial_ledger=None;root_full=None;root_actions=None;fixed=pace=nodes=None;original_reset=original_step=None;mode='RESET';status='STARTED';error=None;technical=None;initial=None;identity_proof=None
    def put(name,value,receipt=True):
        path=folder/name
        if receipt:quota.save_receipt(path,value)
        else:quota.save(path,value)
        return dict(path=str(path),sha256=sha(path))
    def charge(kind):
        key={'reset':'slot_resets','action':'slot_actions','reset_raw':'slot_reset_raw','action_raw':'slot_action_raw'}[kind]
        cap={'reset':1,'action':128,'reset_raw':64,'action_raw':512}[kind]
        if counts[key]>=cap:raise ResourceStop('485_NATIVE_CAP:'+slot+':'+kind)
        meter.guard();meter.charge(kind,slot);counts[key]+=1
        event=dict(sequence=len(events)+1,kind=kind,charged_before_call=True,**counts);events.append(event)
        put('charge-'+str(event['sequence'])+'-before-call-private.json',event)
    meter.begin_actual()
    try:
        meter.guard();env=make_env();raw=env.unwrapped;original_reset,original_step=raw.reset,raw.step
        def guarded_reset(*args,**kwargs):
            if counts['slot_resets']!=0:raise TechnicalStop('485_INTERNAL_SECOND_RESET_FORBIDDEN')
            charge('reset');return original_reset(*args,**kwargs)
        def guarded_raw_step(*args,**kwargs):
            require(mode in ['RESET','ACTION'],'485_RAW_PHASE')
            charge('reset_raw' if mode=='RESET' else 'action_raw')
            before=float(getattr(raw,'t',0.) or 0.);result=original_step(*args,**kwargs)
            require(round((float(raw.t)-before)*50)==1,'485_RAW_SINGLE_TICK');return result
        raw.reset=guarded_reset;raw.step=guarded_raw_step
        obs,_=env.reset(seed=case['seed'],options={'track_id':case['track_id']});mode='GEOMETRY'
        require(counts['slot_resets']==1 and counts['slot_reset_raw']<=64,'485_RESET_ACCOUNTING')
        identity_proof=identity_check(case,env)
        initial=complete_state(env,obs,dict(index=0,laststeer=0.));initial_ref=put('initial-full-private.json',initial)
        gCPU,gwall=time.process_time(),time.perf_counter()
        with meter.geometry(slot):fixed,pace,nodes=geometry485(initial['physical'],native_model485(env),coefficients)
        if time.process_time()-gCPU>60 or time.perf_counter()-gwall>90:raise ResourceStop('485_GEOMETRY_CPU60_WALL90')
        fixed_ref=put('fixed-plan-private.json',fixed)
        nodes_digest=fingerprint(nodes.tolist());policy_digest=fingerprint(dict(rule=RULE,slot=slot,case_identity_digest=identity,nodes_digest=nodes_digest,fixed_plan_sha256=fixed_ref['sha256'],coefficient_sha256=COEFFICIENT_SHA))
        nodes_ref=put('nodes-private.json',dict(projected_nodes=nodes.tolist(),original_scaled_nodes=(np.asarray(fixed['free_profile']['speed'])*pace).tolist(),pace=pace.tolist(),nodes_digest=nodes_digest,policy_digest=policy_digest))
        ctrl=ActualC(env,fixed,pace);before_injection=copy.deepcopy(ctrl.memory());ctrl.policy.nodes=nodes.copy();ctrl.policy.nodes.setflags(write=False)
        require(ctrl.memory()==before_injection,'485_P4_INJECTION_MEMORY')
        pre=sensor(env);arc=canonical_projection(fixed['line'],pre['pos'],pre['vel'],ctrl.phase())['arc'];L=sum(fixed['free_profile']['ds'])
        initial_ledger=GoalLedger.start(arc,round(pre['time']*50));native=NativePrefix485(env,ctrl,initial_ledger,fixed,charge_native=lambda:charge('action'));trace=Trace(lambda:raw.t);mode='ACTION'
        for step in range(1,129):
            meter.guard();require(not ctrl.policy.nodes.flags.writeable and fingerprint(ctrl.policy.nodes.tolist())==nodes_digest,'485_NATIVE_P4_CHANGED')
            tracker=raw.finish_line_tracker
            if ctrl.phase()=='FIRST_LAP' and native.ledger.progress_m>=L/4 and tracker.candidate_crossing_time_s is None and tracker.finish_time_s is None:
                root_actions=len(native.rows);require(root_actions<=127,'485_ROOT_TOO_LATE')
                root_full=complete_state(env,obs,ctrl.memory());blob=pickle.dumps((__import__('random').getstate(),np.random.get_state()))
                root_context=dict(state=from_actual_full(root_full),before=copy.deepcopy(ctrl.memory()),ledger=asdict(ForecastLedger.fork(native.ledger)),actual_ledger=asdict(native.ledger),RNG=dict(global_pickle=blob,digest=hashlib.sha256(blob).hexdigest()),slot=slot,case_identity_digest=identity,nodes_digest=nodes_digest,policy_digest=policy_digest)
                put('root-full-private.json',root_full);put('root-context-private.json',root_context)
            elif step==128:raise PreparationIneligible485('quarter_not_reached_by127_no_replacement')
            native.global_step=step;native.prepare_before_nominal();full_pre=complete_state(env,obs,ctrl.memory());before=copy.deepcopy(ctrl.memory());nominal=ctrl.act(env);native.nominal=np.asarray(nominal,np.float32).tolist()
            put('action-'+str(step)+'-before-native-private.json',dict(full_pre_before_nominal=full_pre,full_pre_after_nominal=complete_state(env,obs,ctrl.memory()),ledger=asdict(native.ledger),nominal=native.nominal,global_step=step,source_fidelity_claimed=False))
            result=native.dispatch(nominal,trace);obs=result[0];ticket=native.ticket
            full_post=complete_state(env,obs,ctrl.memory());posts=copy.deepcopy(ticket.posts)
            postref=put('action-'+str(step)+'-after-native-private.json',dict(full_post=full_post,posts=posts,tires=copy.deepcopy(ticket.native_tires),raw_hull=copy.deepcopy(ticket.native_hulls),ticket_success=ticket.success,command=ticket.command,own_native_observation=True))
            fact=native.commit_prefix_fact485();fact.update(full_native_post_sha256=postref['sha256']);put('action-'+str(step)+'-fact-private.json',fact)
            row=fact['row']
            if row['safety'] or native.ledger.deadline_missed or row['ended'] or row['truncated'] or native.ledger.done or ctrl.phase() not in ['LAUNCH','FIRST_LAP'] or raw.finish_line_tracker.candidate_crossing_time_s is not None:raise PreparationIneligible485('unsafe_progress_or_terminal_common_prefix')
            require(np.array_equal(np.asarray(row['command'],np.float32),np.asarray(nominal,np.float32)) and row['memory_before']==before and row['nominal_memory_after']==ctrl.memory(),'485_NATURAL_ONCE_MEMORY_COMMAND')
            meter.checkpoint('NATIVE_COMMON_PREFIX',slot=slot,native_step=step,progress_m=native.ledger.progress_m,root_frozen=root_context is not None)
            if root_context is not None:
                witness=dict(row=row,posts=posts,full_pre=full_pre,full_post=full_post,ledger_before=fact['ledger_before'],ledger_after=fact['ledger_after'],nominal=native.nominal,own_native_fact=True)
                put('witness-private.json',witness);status='NATIVE_ROOT_AND_WITNESS_OBSERVED';break
        require(root_context is not None and witness is not None,'485_NO_ROOT_WITNESS')
    except PreparationIneligible485 as exc:
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
                require(cleanup['bodies_after']==cleanup['joints_after']==0,'485_NATIVE_TEARDOWN')
            except BaseException as exc:
                if technical is None:technical=exc;status='TECHNICAL_STOP';error=type(exc).__name__+': '+str(exc)
        try:
            put('cleanup-private.json',cleanup)
            journal_ref=put('native-charge-journal-private.json',dict(slot=slot,case_identity_digest=identity,events=events,counts=counts))
            trace_ref=put('native-trace-private.json',dict(rows=[] if native is None else native.rows,initial_actual_ledger=None if initial_ledger is None else asdict(initial_ledger),root_actual_ledger=None if root_context is None else root_context['actual_ledger'],witness_index=None if root_actions is None else root_actions+1))
            put('preparation-result-private.json',dict(status=status,error=error,slot=slot,case_identity_digest=identity,counts=counts,cleanup=cleanup,source_gate_passed=False))
        finally:meter.end_actual()
    if technical is not None:raise technical
    if status!='NATIVE_ROOT_AND_WITNESS_OBSERVED':return dict(status=status,error=error,slot=slot,case_identity_digest=identity,source_gate_passed=False)
    root_context_ref=dict(path=str(folder/'root-context-private.json'),sha256=sha(folder/'root-context-private.json'));root_full_ref=dict(path=str(folder/'root-full-private.json'),sha256=sha(folder/'root-full-private.json'));witness_ref=dict(path=str(folder/'witness-private.json'),sha256=sha(folder/'witness-private.json'))
    proof=dict(schema='NATIVE_PREFIX_ROOT485_V1',stage=485,passed=True,source_gate_passed=False,slot=slot,case_identity_digest=identity,p4_nodes_digest=nodes_digest,profile_sha256=nodes_ref['sha256'],policy_digest=policy_digest,actions=root_actions,native_actions_including_witness=counts['slot_actions'],initial_actual_ledger=asdict(initial_ledger),root_actual_ledger=root_context['actual_ledger'],root_context_path=root_context_ref['path'],root_context_sha256=root_context_ref['sha256'],root_state_digest=fingerprint(root_context['state']),root_memory_digest=fingerprint(root_context['before']),root_RNG_digest=root_context['RNG']['digest'],native_trace_path=trace_ref['path'],native_trace_sha256=trace_ref['sha256'],native_charge_journal_path=journal_ref['path'],native_charge_journal_sha256=journal_ref['sha256'],witness_path=witness_ref['path'],witness_sha256=witness_ref['sha256'],root_full_path=root_full_ref['path'],root_full_sha256=root_full_ref['sha256'],fixed_plan_path=fixed_ref['path'],fixed_plan_sha256=fixed_ref['sha256'],nodes_path=nodes_ref['path'],nodes_sha256=nodes_ref['sha256'])
    proof_ref=put('prefix-root-proof-private.json',proof)
    return dict(status=status,slot=slot,case_identity_digest=identity,context=root_context,state=root_context['state'],before=root_context['before'],ledger=ForecastLedger(**root_context['ledger']),actual_ledger=GoalLedger(**root_context['actual_ledger']),actual_root_ledger=root_context['actual_ledger'],root_context_sha256=root_context_ref['sha256'],RNG=root_context['RNG'],fixed=fixed,pace=pace.tolist(),projected_nodes=nodes.tolist(),profile_sha256=nodes_ref['sha256'],nodes_digest=nodes_digest,policy_digest=policy_digest,prefixproof=proof,prefixproof_path=proof_ref['path'],prefixproof_sha256=proof_ref['sha256'],witness=witness,witness_row=witness['row'],witness_posts=witness['posts'],witness_path=witness_ref['path'],native_closed=True,source_gate_passed=False,identity_verification=identity_proof,counts=counts)
