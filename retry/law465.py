"""465 fixed PulseOnce/S13 H13 cohorts; existing observed physics, no selector."""
import copy,math
from pathlib import Path
import numpy as np
from retry.signed417_executor import canonical_projection
from retry.scalar392_audit import pedals
from retry.observer435 import Child
from retry.pilot420_backend import TechnicalStop,snapshot,fingerprint,rnghash
from retry.pilot421_run import compare_frames
from retry.audit439 import replay
from retry.ledger439 import compare_first,require
from retry.planner419 import GoalLedger
from retry.audit431 import physical_tokens
from retry.receipt421_io import save_receipt
from retry.loss389_analyze import save


def command465(fixed,pace,pos,vel,nominal,phase):
    """Pure general secant command; explicit strict interior forward domain."""
    if phase!='FIRST_LAP':raise TechnicalStop('465_secant_phase')
    line=np.asarray(fixed['line'],float);ds=np.asarray(fixed['free_profile']['ds'],float)
    nodes=np.asarray(fixed['free_profile']['speed'],float)*np.asarray(pace,float)
    pos=np.asarray(pos,float);vel=np.asarray(vel,float);nominal=np.asarray(nominal,np.float32)
    if pos.shape!=(2,) or vel.shape!=(2,) or nominal.shape!=(3,) or line.ndim!=2 or line.shape[1]!=2 or len(ds)!=len(line) or len(nodes)!=len(ds)+1:raise TechnicalStop('465_secant_input_shape')
    if not all(np.isfinite(x).all() for x in [line,ds,nodes,pos,vel,nominal]) or np.any(ds<=0) or np.any(nodes<0):raise TechnicalStop('465_secant_nonfinite_or_profile')
    if not(np.all(nominal>=np.asarray([-.4,0,0],np.float32)) and np.all(nominal<=np.asarray([.4,1,1],np.float32))):raise TechnicalStop('465_nominal_bounds')
    q=canonical_projection(line,pos,vel,phase);s=q['arc'];sigma=q['sigma'];arc=np.r_[0,np.cumsum(ds)];ahead=s+.08*sigma
    if not(math.isfinite(s) and math.isfinite(sigma) and sigma>0 and 0<s<ahead<arc[-1]):raise TechnicalStop('465_secant_strict_domain')
    def target(where):
        j=int(np.searchsorted(arc,where,side='right')-1)
        if not 0<=j<len(ds):raise TechnicalStop('465_secant_reference_index')
        u=(where-arc[j])/ds[j];w=(1-u)*nodes[j]**2+u*nodes[j+1]**2
        if not(math.isfinite(w) and w>0):raise TechnicalStop('465_secant_positive_target')
        return math.sqrt(w)
    j=q['index'];u=q['u'];w=(1-u)*nodes[j]**2+u*nodes[j+1]**2
    if not(math.isfinite(w) and w>0):raise TechnicalStop('465_secant_positive_current_target')
    r=math.sqrt(w);end=target(ahead);v=math.hypot(*vel);raw=(end-r)/.08+1.5*(r-v)
    if not math.isfinite(raw):raise TechnicalStop('465_secant_nonfinite_acceleration')
    z=pedals(raw,v,fixed['model']);command=nominal.copy();command[1:]=[z['gas'],z['brake']]
    if not(np.isfinite(command).all() and np.all(command>=np.asarray([-.4,0,0],np.float32)) and np.all(command<=np.asarray([.4,1,1],np.float32))):raise TechnicalStop('465_secant_action_bounds')
    return command


def _one465(child,arm,index,tag):
    require(arm in ['PulseOnce','S13'] and 0<=index<13,'465_DRIVER_SCOPE')
    before=copy.deepcopy(child.ctrl.memory());nominal=child.ctrl.act(child.m)
    command=np.asarray(nominal,np.float32).copy()
    if arm=='S13':command=command465(child.fixed,child.pace,list(child.m.car.hull.position),list(child.m.car.hull.linearVelocity),nominal,child.ctrl.phase())
    elif index==0:command[1:]=[1.,0.]
    if index==0:
        alias=np.asarray(nominal,np.float32).copy();alias[1:]=[1.,0.]
        require(np.array_equal(command,alias),'465_FIRST_FULL_VECTOR_ALIAS')
    after=copy.deepcopy(child.ctrl.memory());count=len(child.rows)
    child.one(tag,first_override=command,prepared_nominal=nominal,prepared_before=before)
    if len(child.rows)==count+1:
        row=child.rows[-1]
        require(row['memory_before']==before and row['memory_after']==after and (child.ctrl.memory()==after or child.status=='FINISHED'),'465_MEMORY_ONCE')
        require(np.array_equal(np.asarray(row['command'],np.float32),command),'465_DISPATCH_COMMAND')
    return dict(arm=arm,action=index+1,nominal_calls=1,prepared_nominal_used=True,first_fullgas_alias=index==0,phase=after['C']['phase'],observed_row=len(child.rows)==count+1)


def _scope465(child):
    tracker=child.m.finish_line_tracker
    if tracker.finish_time_s is not None or child.status=='FINISHED':return 'OFFICIAL_MODEL_FINISH_SCOPE_EXIT'
    if tracker.candidate_crossing_time_s is not None or child.ctrl.phase()=='FINISH_CONFIRM':return 'PENDING_FINISH_SCOPE_EXIT'
    return None


def _finish465(child):
    child.initial_count=len(child.rows)
    if not child.rows:raise TechnicalStop('465_no_observed_first_action')
    child.end13=child._end_vector()
    child.initial_ok=len(child.rows)==13 or child.status=='FINISHED'
    child.initial_safe=not any(r['safety'] for r in child.rows)
    child.initial_progress=child.ledger.progress_qualified()
    for row in child.rows:physical_tokens(row['safety'],allow_empty=True)
    if child.status=='UNSAFE':physical_tokens(child.error)
    if child.status=='INFEASIBLE':
        if len(child.rows)<13:raise TechnicalStop('465_unsupported_early_progress_rejection')
        require(child.error=='predicted_progress_deadline' and child.ledger.deadline_missed,'465_unregistered_progress_rejection')
    if child.status not in ['ACTIVE','UNSAFE','INFEASIBLE','FINISHED']:raise TechnicalStop('465_unregistered_child_status:'+str(child.status))


def root_h13(root,meter,fixed,pace,state,memory,ledger,expected):
    """Run source-qualified PulseOnce first; same cohorts supply science output."""
    require(meter.qualification_passed and type(ledger) is GoalLedger and not ledger.done and not ledger.deadline_missed,'465_FRESH_SOURCE_AND_ACTUAL_ROOT_REQUIRED')
    d=Path(meter.d);origin=(fingerprint(state),fingerprint(memory),ledger.digest(),rnghash())
    require(len(expected)>=13,'465_expected_native13')
    require(np.array_equal(np.asarray(expected[0]['command'],np.float32),np.asarray([expected[0]['nominal'][0],1.,0.],np.float32)) and all(r['command']==r['nominal'] for r in expected[1:13]),'465_NATIVE_PULSE_ONCE_POLICY')
    startticks,startworlds=meter.b['ticks'],meter.b['worlds'];cohorts=[];drivers=[]
    def persist():
        save(d/'policyrecords-private.json',drivers);save(d/'cohortresults.json',cohorts)
    def immutable():
        require((fingerprint(state),fingerprint(memory),ledger.digest(),rnghash())==origin,'465_root_input_ledger_RNG_mutation')
    def result(status):
        return dict(status=status,passed=status=='TWO_H13_COHORTS_COMPLETED_REPEAT_EXACT',cohorts=cohorts,model_ticks=meter.b['ticks']-startticks,model_worlds=meter.b['worlds']-startworlds,policyrecords_path=str(d/'policyrecords-private.json'),cohortresults_path=str(d/'cohortresults.json'),actual_execution_allowed=False)
    persist()
    for arm in ['PulseOnce','S13']:
        children=[];held=None;pair=[];armticks,armworlds=meter.b['ticks'],meter.b['worlds']
        try:
            for rep in [1,2]:
                immutable();label=arm+'_H13_'+str(rep)
                meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='465_FIXED_LAW_SOURCE_COHORT')
                child=Child(meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,fixed,pace,label,'nominal',world_tag='465_required' if rep==1 else '465_repeat');children.append(child)
                scope=None
                for index in range(13):
                    scope=_scope465(child)
                    if scope or child.status!='ACTIVE':break
                    rec=_one465(child,arm,index,'465_'+arm+'_H13');rec.update(repetition=rep,world_label=label);drivers.append(rec);persist();immutable()
                scope=scope or _scope465(child);_finish465(child);child.dump(d)
                same=0;first_divergence=None;calibration=None
                if arm=='PulseOnce':
                    for index,frame in enumerate(child.rows):
                        if first_divergence is None and not np.array_equal(np.asarray(frame['command'],np.float32),np.asarray(expected[index]['command'],np.float32)):first_divergence=index+1
                        if first_divergence is None:same+=1
                    if len(child.rows)==13 and scope is None and child.status=='ACTIVE':
                        calibration=replay(child.rows,expected[:13],fixed)
                        require(calibration['certified_prefix_actions']==13 and calibration['fresh_current_first_pass']>=1,'465_PULSE_NATIVE13_FIDELITY')
                        compare_first(ledger,child.rows[0],expected[0],fixed)
                packet=dict(arm=arm,repetition=rep,label=label,status=child.status,error=child.error,scope_exit=scope,rows=len(child.rows),signature=child.signature(),initial_safe=child.initial_safe,initial_progress=child.initial_progress,first=copy.deepcopy(child.rows[0]),factual_calibration=calibration,native_same_command_prefix_actions=same if arm=='PulseOnce' else 1,native_first_command_divergence=first_divergence if arm=='PulseOnce' else None,child_private_path=str(d/(label+'-private.json')),observer_private_path=str(d/(label+'-observer-private.json')))
                pair.append(packet);save_receipt(d/(label+'-cohort-proof-private.json'),packet);child.close();immutable()
            require(pair[0]['signature']==pair[1]['signature'] and pair[0]['scope_exit']==pair[1]['scope_exit'],'465_H13_INDEPENDENT_REPEAT_MISMATCH')
            # A held third world tests the first current transition only.
            label=arm+'_held_first';meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='465_HELD_FIRST')
            held=Child(meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,fixed,pace,label,'nominal',world_tag='465_held')
            rec=_one465(held,arm,0,'465_held_first');rec.update(repetition='held',world_label=label);drivers.append(rec);persist()
            require(len(held.rows)==1,'465_HELD_NO_FIRST_ROW');z=compare_frames(held.rows[0],pair[0]['first'])
            require(z['passed'] and z['wheel']['clipped_flag_mismatches']==0 and held.rows[0]['memory_before']==pair[0]['first']['memory_before'] and held.rows[0]['memory_after']==pair[0]['first']['memory_after'] and held.rows[0]['command']==pair[0]['first']['command'],'465_HELD_FIRST_MISMATCH')
            held.dump(d);immutable()
            a=pair[0];full=a['rows']==13 and a['status']=='ACTIVE' and a['scope_exit'] is None and a['initial_safe'] and a['initial_progress']
            outcome='COMPLETE_H13' if full else 'SCOPE_EXIT' if a['scope_exit'] else 'TYPED_PHYSICAL_INELIGIBLE' if a['status']=='UNSAFE' else 'SUPPORTED_FULL_H13_PROGRESS_REJECTION' if a['status']=='INFEASIBLE' else 'INCOMPLETE_H13'
            cohort=dict(arm=arm,status=outcome,error=a['error'],scope_exit=a['scope_exit'],rows=a['rows'],independent_repeat_exact=True,held_first_passed=True,trajectories=pair,model_ticks=meter.b['ticks']-armticks,model_worlds=meter.b['worlds']-armworlds,native_factual_scope='13-step physical/geometry/ledger policy replay; exact same-command scope separately counted' if arm=='PulseOnce' else 'First command only; later sustained law model consistency only',actual_execution_allowed=False)
            cohorts.append(cohort);persist()
            require(cohort['model_ticks']<=108 and cohort['model_worlds']==3,'465_ARM_COST')
            if not full:return result(outcome)
        finally:
            for child in children:
                if not child.closed:child.dump(d);child.close()
            if held and not held.closed:held.dump(d);held.close()
            persist()
    immutable();require(meter.b['ticks']-startticks<=216 and meter.b['worlds']-startworlds==6,'465_ROOT_COHORT_COST')
    return result('TWO_H13_COHORTS_COMPLETED_REPEAT_EXACT')
