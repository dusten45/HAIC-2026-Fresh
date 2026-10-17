"""468 fixed original/projected reference H13 cohorts; existing observed physics, no selector."""
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
from retry.loss389_analyze import save,read,sha


from retry.law465 import _scope465 as _scope468,_finish465 as _finish468

ORIGINAL='OriginalReferenceCommonPulse'
PROJECTED='Projected4ReferenceCommonPulse'
PROJECTED_SHA='85ac335bf32d11da78e2d76a213b6096a0d357bc4f5d334196695343717d213f'


def command468(fixed,nodes,pos,vel,nominal,phase):
    """Pure original point-derivative law at an explicitly supplied profile."""
    nodes=np.asarray(nodes,float);ds=np.asarray(fixed['free_profile']['ds'],float)
    pos=np.asarray(pos,float);vel=np.asarray(vel,float);nominal=np.asarray(nominal,np.float32)
    require(phase=='FIRST_LAP' and pos.shape==(2,) and vel.shape==(2,) and nominal.shape==(3,),'468_POINT_DOMAIN')
    require(nodes.shape==(len(ds)+1,) and np.isfinite(nodes).all() and np.isfinite(ds).all() and np.all(ds>0) and nodes[0]==0 and np.all(nodes[1:]>0),'468_PROFILE_DOMAIN')
    require(np.isfinite(pos).all() and np.isfinite(vel).all() and np.isfinite(nominal).all(),'468_FINITE_INPUT')
    q=canonical_projection(fixed['line'],pos,vel,phase);j,u=q['index'],q['u']
    require(0<q['arc']<sum(ds) and q['sigma']>=-.1,'468_POINT_FORWARD_INTERIOR')
    w=(1-u)*nodes[j]**2+u*nodes[j+1]**2;require(math.isfinite(w) and w>0,'468_POINT_POSITIVE_TARGET')
    r=float(np.sqrt(w));f=float((nodes[j+1]**2-nodes[j]**2)/(2*ds[j]));raw=f*(q['sigma']/r)+1.5*(r-math.hypot(*vel))
    require(math.isfinite(raw),'468_POINT_FINITE_ACCELERATION')
    z=pedals(raw,math.hypot(*vel),fixed['model']);out=nominal.copy();out[1:]=[z['gas'],z['brake']]
    require(np.isfinite(out).all() and np.all(out>=np.asarray([-.4,0,0],np.float32)) and np.all(out<=np.asarray([.4,1,1],np.float32)),'468_COMMAND_BOUNDS')
    return out


class ReferencePolicy468:
    """Frozen own-reference binding; SourceC retains its original point law."""
    def __init__(self,arm,nodes,source_sha,first_command):
        require(arm in [ORIGINAL,PROJECTED],'468_ARM')
        self.arm=arm;self.nodes=np.asarray(nodes,float).copy()
        require(self.nodes.ndim==1 and len(self.nodes)>=2 and np.isfinite(self.nodes).all() and self.nodes[0]==0 and np.all(self.nodes[1:]>0),'468_BOUND_REFERENCE_DOMAIN')
        self.nodes.setflags(write=False)
        self.nodes_digest=fingerprint(self.nodes.tolist());self.source_sha=source_sha
        self.policy_digest=fingerprint(dict(rule='468_COMMON_FIRST_FULLGAS_THEN_OWN_REFERENCE_POINT_FF_13',arm=arm,nodes=self.nodes_digest,source_sha=source_sha))
        self.first_command=np.asarray(first_command,np.float32).copy()
        require(self.first_command.shape==(3,) and np.isfinite(self.first_command).all() and self.first_command[1]==1 and self.first_command[2]==0,'468_BOUND_FIRST_FULLGAS')
        self.first_command.setflags(write=False)
    def inject(self,child):
        before=copy.deepcopy(child.ctrl.memory());stamp=fingerprint(snapshot(child.m));ledger=child.ledger
        child.ctrl.policy.nodes=self.nodes.copy();child.ctrl.policy.nodes.setflags(write=False);child.reference468=self
        require(child.ctrl.memory()==before and fingerprint(snapshot(child.m))==stamp and child.ledger==ledger,'468_INJECTION_CHANGED_STATE_OR_MEMORY')
        self.check(child)
    def check(self,child):
        require(not self.nodes.flags.writeable and fingerprint(self.nodes.tolist())==self.nodes_digest,'468_FROZEN_REFERENCE_CHANGED')
        require(not child.ctrl.policy.nodes.flags.writeable and np.array_equal(child.ctrl.policy.nodes,self.nodes),'468_CHILD_REFERENCE_CHANGED')
        require(self.policy_digest==fingerprint(dict(rule='468_COMMON_FIRST_FULLGAS_THEN_OWN_REFERENCE_POINT_FF_13',arm=self.arm,nodes=self.nodes_digest,source_sha=self.source_sha)),'468_POLICY_DIGEST_CHANGED')


def one468(child,arm,index,tag):
    require(arm in [ORIGINAL,PROJECTED] and 0<=index<13,'468_DRIVER_SCOPE')
    binding=child.reference468;require(binding.arm==arm and child.ctrl.phase()=='FIRST_LAP','468_DRIVER_REFERENCE_ARM_PHASE');binding.check(child)
    before=copy.deepcopy(child.ctrl.memory());nominal=child.ctrl.act(child.m)
    command=np.asarray(nominal,np.float32).copy();natural_first_fullgas=None
    if index==0:
        alias=command.copy();alias[1:]=[1.,0.]
        require(np.array_equal(alias,binding.first_command),'468_COMMON_FIRST_FULL_VECTOR')
        natural_first_fullgas=np.array_equal(command,alias)
        if arm==PROJECTED:require(natural_first_fullgas,'468_PROJECTED_NATURAL_FIRST_NOT_FULLGAS')
        command=alias
    after=copy.deepcopy(child.ctrl.memory());count=len(child.rows)
    child.one(tag,first_override=command,prepared_nominal=nominal,prepared_before=before)
    if len(child.rows)==count+1:
        row=child.rows[-1]
        require(row['memory_before']==before and row['memory_after']==after and (child.ctrl.memory()==after or child.status=='FINISHED'),'468_MEMORY_ONCE')
        require(np.array_equal(np.asarray(row['command'],np.float32),command),'468_DISPATCH_COMMAND')
    binding.check(child)
    return dict(arm=arm,action=index+1,nominal_calls=1,prepared_nominal_used=True,first_fullgas_alias=index==0,natural_first_fullgas=natural_first_fullgas,policy_digest=binding.policy_digest,nodes_digest=binding.nodes_digest,phase=after['C']['phase'],observed_row=len(child.rows)==count+1)


def profile_inputs468(root,fixed,pace):
    matches=[path for path in [root/'stage466/projection-and-segments-private.json',root/'stage466-numeric-recovery1/projection-and-segments-private.json'] if path.exists() and sha(path)==PROJECTED_SHA]
    require(len(matches)>=1,'468_FROZEN_PROJECTED_SOURCE_SHA');path=matches[0];data=read(path)
    original=np.asarray(data['original_nodes'],float);projected=np.asarray(data['projected_nodes'],float)
    require(np.array_equal(original,np.asarray(fixed['free_profile']['speed'])*np.asarray(pace)),'468_ORIGINAL_REFERENCE_EXACT')
    require(original.shape==projected.shape and original[0]==projected[0]==0 and np.isfinite(projected).all() and np.all(projected[1:]>0) and np.all(projected<=original),'468_PROJECTED_VECTOR_DOMAIN')
    return original,projected,path


def natural_first468(fixed,nodes,row):
    command=command468(fixed,nodes,row['pre']['pos'],row['pre']['vel'],row['nominal'],'FIRST_LAP')
    alias=np.asarray(row['nominal'],np.float32).copy();alias[1:]=[1.,0.]
    require(np.array_equal(command,alias),'468_PROJECTED_NATURAL_FIRST_PURE_GATE')
    return command


def root_h13(root,meter,fixed,pace,state,memory,ledger,expected):
    """Run original-reference common pulse before projected-reference cohort."""
    require(meter.qualification_passed and type(ledger) is GoalLedger and not ledger.done and not ledger.deadline_missed,'468_FRESH_SOURCE_AND_ACTUAL_ROOT_REQUIRED')
    d=Path(meter.d);origin=(fingerprint(state),fingerprint(memory),ledger.digest(),rnghash())
    require(len(expected)>=13,'468_expected_native13')
    require(np.array_equal(np.asarray(expected[0]['command'],np.float32),np.asarray([expected[0]['nominal'][0],1.,0.],np.float32)) and all(r['command']==r['nominal'] for r in expected[1:13]),'468_NATIVE_PULSE_ONCE_POLICY')
    original,projected,profile_path=profile_inputs468(root,fixed,pace)
    natural_first468(fixed,projected,expected[0])
    bindings={arm:ReferencePolicy468(arm,nodes,PROJECTED_SHA,expected[0]['command']) for arm,nodes in [(ORIGINAL,original),(PROJECTED,projected)]}
    startticks,startworlds=meter.b['ticks'],meter.b['worlds'];cohorts=[];drivers=[]
    def persist():
        save(d/'policyrecords-private.json',drivers);save(d/'cohortresults.json',cohorts)
    def immutable():
        require((fingerprint(state),fingerprint(memory),ledger.digest(),rnghash())==origin,'468_root_input_ledger_RNG_mutation')
    def result(status):
        return dict(status=status,passed=status=='TWO_H13_COHORTS_COMPLETED_REPEAT_EXACT',cohorts=cohorts,model_ticks=meter.b['ticks']-startticks,model_worlds=meter.b['worlds']-startworlds,policyrecords_path=str(d/'policyrecords-private.json'),cohortresults_path=str(d/'cohortresults.json'),actual_execution_allowed=False)
    persist()
    for arm in [ORIGINAL,PROJECTED]:
        children=[];held=None;pair=[];armticks,armworlds=meter.b['ticks'],meter.b['worlds']
        try:
            for rep in [1,2]:
                immutable();label=arm+'_H13_'+str(rep)
                binding=bindings[arm]
                save_receipt(d/(label+'-own-reference-before-constructor-private.json'),dict(arm=arm,source_path=str(profile_path),source_sha256=PROJECTED_SHA,nodes=binding.nodes.tolist(),nodes_digest=binding.nodes_digest,policy_digest=binding.policy_digest,actual_execution_allowed=False))
                meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='468_OWN_REFERENCE_POINT_FF:'+binding.policy_digest)
                child=Child(meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,fixed,pace,label,'nominal',world_tag='468_required' if rep==1 else '468_repeat');children.append(child);binding.inject(child)
                scope=None
                for index in range(13):
                    scope=_scope468(child)
                    if scope or child.status!='ACTIVE':break
                    rec=one468(child,arm,index,'468_'+arm+'_H13');rec.update(repetition=rep,world_label=label);drivers.append(rec);persist();immutable()
                scope=scope or _scope468(child);_finish468(child);child.dump(d)
                same=0;first_divergence=None;calibration=None
                if arm==ORIGINAL:
                    for index,frame in enumerate(child.rows):
                        if first_divergence is None and not np.array_equal(np.asarray(frame['command'],np.float32),np.asarray(expected[index]['command'],np.float32)):first_divergence=index+1
                        if first_divergence is None:same+=1
                    if len(child.rows)==13 and scope is None and child.status=='ACTIVE':
                        calibration=replay(child.rows,expected[:13],fixed)
                        require(calibration['certified_prefix_actions']==13 and calibration['fresh_current_first_pass']>=1,'468_PULSE_NATIVE13_FIDELITY')
                        compare_first(ledger,child.rows[0],expected[0],fixed)
                compare_first(ledger,child.rows[0],expected[0],fixed)
                require(np.array_equal(np.asarray(child.rows[0]['command'],np.float32),np.asarray(expected[0]['command'],np.float32)),'468_NATIVE_COMMON_FIRST_COMMAND')
                if arm==PROJECTED:
                    require(child.rows[0]==cohorts[0]['trajectories'][0]['first'],'468_CROSS_ARM_FIRST_FRAME_EXACT')
                packet=dict(arm=arm,repetition=rep,label=label,status=child.status,error=child.error,scope_exit=scope,rows=len(child.rows),signature=child.signature(),initial_safe=child.initial_safe,initial_progress=child.initial_progress,first=copy.deepcopy(child.rows[0]),factual_calibration=calibration,native_same_command_prefix_actions=same if arm==ORIGINAL else 1,native_first_command_divergence=first_divergence if arm==ORIGINAL else None,child_private_path=str(d/(label+'-private.json')),observer_private_path=str(d/(label+'-observer-private.json')))
                pair.append(packet);save_receipt(d/(label+'-cohort-proof-private.json'),packet);child.close();immutable()
            require(pair[0]['signature']==pair[1]['signature'] and pair[0]['scope_exit']==pair[1]['scope_exit'],'468_H13_INDEPENDENT_REPEAT_MISMATCH')
            # A held third world tests the first current transition only.
            label=arm+'_held_first';save_receipt(d/(label+'-own-reference-before-constructor-private.json'),dict(arm=arm,source_sha256=PROJECTED_SHA,nodes=bindings[arm].nodes.tolist(),nodes_digest=bindings[arm].nodes_digest,policy_digest=bindings[arm].policy_digest,actual_execution_allowed=False));meter.capture_inputs(state,memory,ledger,label+'_inputs',gate='468_HELD_OWN_REFERENCE:'+bindings[arm].policy_digest)
            held=Child(meter,copy.deepcopy(state),copy.deepcopy(memory),ledger,fixed,pace,label,'nominal',world_tag='468_held');bindings[arm].inject(held)
            rec=one468(held,arm,0,'468_held_first');rec.update(repetition='held',world_label=label);drivers.append(rec);persist()
            require(len(held.rows)==1,'468_HELD_NO_FIRST_ROW');z=compare_frames(held.rows[0],pair[0]['first'])
            require(z['passed'] and z['wheel']['clipped_flag_mismatches']==0 and held.rows[0]['memory_before']==pair[0]['first']['memory_before'] and held.rows[0]['memory_after']==pair[0]['first']['memory_after'] and held.rows[0]['command']==pair[0]['first']['command'],'468_HELD_FIRST_MISMATCH')
            held.dump(d);immutable()
            a=pair[0];full=a['rows']==13 and a['status']=='ACTIVE' and a['scope_exit'] is None and a['initial_safe'] and a['initial_progress']
            outcome='COMPLETE_H13' if full else 'SCOPE_EXIT' if a['scope_exit'] else 'TYPED_PHYSICAL_INELIGIBLE' if a['status']=='UNSAFE' else 'SUPPORTED_FULL_H13_PROGRESS_REJECTION' if a['status']=='INFEASIBLE' else 'INCOMPLETE_H13'
            cohort=dict(arm=arm,status=outcome,error=a['error'],scope_exit=a['scope_exit'],rows=a['rows'],independent_repeat_exact=True,held_first_passed=True,trajectories=pair,model_ticks=meter.b['ticks']-armticks,model_worlds=meter.b['worlds']-armworlds,native_factual_scope='13-step physical/geometry/ledger policy replay; exact same-command scope separately counted' if arm==ORIGINAL else 'First command only; later projected reference model consistency only',policy_digest=bindings[arm].policy_digest,nodes_digest=bindings[arm].nodes_digest,source_profile_sha256=PROJECTED_SHA,actual_execution_allowed=False)
            cohorts.append(cohort);persist()
            require(cohort['model_ticks']<=108 and cohort['model_worlds']==3,'468_ARM_COST')
            if not full:return result(outcome)
        finally:
            for child in children:
                if not child.closed:child.dump(d);child.close()
            if held and not held.closed:held.dump(d);held.close()
            persist()
    immutable();require(meter.b['ticks']-startticks<=216 and meter.b['worlds']-startworlds==6,'468_ROOT_COHORT_COST')
    return result('TWO_H13_COHORTS_COMPLETED_REPEAT_EXACT')
