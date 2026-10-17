"""Three source copies, including a genuine two-hold warm continuation.

All research dependencies come from the parent's isolated495 runtime. Importing
this module never creates a world or executes a transition.
"""
import copy
import pickle
import random
from dataclasses import asdict
import numpy as np


def qualify(meter, material, *, runtime):
    def module(name):return runtime.import_module('retry.'+name)
    Child=module('observer435').Child
    law=module('law477');backend=module('pilot420_backend')
    ledger=module('ledger439');geometry=module('geometry439')
    online=module('online481');goals=module('planner419')
    models=module('planner419_model_ledger')
    identity=module('mechanism479').physical_identity
    save=module('receipt421_io').save_receipt
    sha=module('loss389_analyze').sha
    require=ledger.require;fingerprint=backend.fingerprint
    ctx=material['context'];witnesses=material['witnesses']
    require(len(witnesses)==2 and material['native_closed'] is True,'495_TWO_NATIVE_WITNESSES_REQUIRED')
    for value in (material,ctx,*witnesses):
        require(value['binding']==runtime.binding,'495_SOURCE_RUNTIME_BINDING')
    capture=module('capture495')
    inputs=module('executor490_input')
    require(inputs.array_sha(material['fixed']['line'])==runtime.binding['line_sha256'] and
            inputs.array_sha(material['projected_nodes'])==runtime.binding['nodes_sha256'],'495_SOURCE_FROZEN_ARRAY_BINDING')
    actual=goals.GoalLedger(**material['actual_root_ledger'])
    require(asdict(actual)==ctx['actual_ledger']==witnesses[0]['ledger_before'],'495_SOURCE_ROOT_LEDGER')
    require(witnesses[0]['ledger_after']==witnesses[1]['ledger_before'],'495_NATIVE_WARM_LEDGER_CHAIN')
    binding=law.ReferencePolicy477(law.PROJECTED,material['projected_nodes'],material['profile_sha256'])
    records=[];first=None;first_capture=None;live=None
    def record(child,row,posts):
        return dict(row=copy.deepcopy(row),posts=copy.deepcopy(posts),state=backend.snapshot(child.m),
                    memory=child.ctrl.memory(),ledger=asdict(child.ledger),RNG=backend.rnghash())
    start_ticks=meter.b['ticks'];start_worlds=meter.b['worlds']
    try:
        for rep in (1,2,'warm'):
            py,npr=pickle.loads(ctx['RNG']['global_pickle']);random.setstate(py);np.random.set_state(npr)
            label=material['slot']+'_source_'+str(rep)
            meter.capture_inputs(ctx['state'],ctx['before'],actual,label+'_inputs',gate='495_NATIVE_TWO_WITNESS_SOURCE_ONLY')
            live=Child(meter,copy.deepcopy(ctx['state']),copy.deepcopy(ctx['before']),actual,
                       material['fixed'],np.asarray(material['pace']),label,'nominal',world_tag='495_source')
            binding.inject(live)
            require(identity(backend.snapshot(live.m))==identity(ctx['state']),'495_SOURCE_ROOT_RESTORE')
            require(live.ctrl.memory()==ctx['before'] and backend.rnghash()==ctx['RNG']['digest'],'495_SOURCE_MEMORY_RNG')
            live.one('495_source_first_nominal')
            binding.check(live)
            require(len(live.rows)==1 and live.status=='ACTIVE' and live.rows[0]['predicted']['raw_ticks']==4,'495_SOURCE_FIRST_SAFE_ACTIVE')
            actual1,report1=ledger.compare_first(actual,live.rows[0],witnesses[0]['row'],material['fixed'])
            require(len(live.capture_holds495)==1,'495_SOURCE_FIRST_DIRECT_CAPTURE')
            model_hold=live.capture_holds495[0]
            flags1=capture.compare_flags495(witnesses[0]['capture_hold495'],model_hold,runtime.binding)
            require(flags1['passed'] and flags1['safe'],'495_SOURCE_FIRST_DIRECT_FLAGS')
            report1['direct_capture495']=flags1
            initial=record(live,live.rows[0],live.stream.posts)
            if first is None:
                first=initial;first_capture=copy.deepcopy(model_hold)
            else:
                require(initial==first,'495_SOURCE_INDEPENDENT_FIRST_REPEAT_EXACT')
                report1['direct_repeat495']=capture.compare_repeat495(first_capture,model_hold,runtime.binding)
            reports=[report1]
            if rep=='warm':
                # No restore, fork, memory replacement or native-state injection
                # between these two holds. Retain first model ledger drift.
                before=asdict(live.ledger);posts_start=len(live.stream.posts)
                require(asdict(actual1)==witnesses[1]['ledger_before'],'495_WARM_NATIVE_JOIN')
                live.one('495_source_second_genuine_warm_nominal')
                binding.check(live)
                require(len(live.rows)==2 and live.status=='ACTIVE','495_SOURCE_WARM_SAFE_ACTIVE')
                frame=live.rows[1];row=witnesses[1]['row']
                require(frame['actual_root_ledger_digest']==actual.digest(),'495_WARM_ROOT_LEDGER_PROVENANCE')
                require(frame['predicted']['raw_ticks']==4 and row['raw_ticks']==4,'495_SOURCE_WARM_FOUR_TICKS')
                require(ledger.equal(frame['command'],row['command']),'495_WARM_COMMAND_MISMATCH')
                require(ledger.equal(frame['memory_before'],row['memory_before']) and ledger.equal(frame['memory_after'],row['nominal_memory_after']),'495_WARM_MEMORY_MISMATCH')
                fidelity=module('paired417_common').shapecheck(frame,row)
                require(fidelity['passed'] and fidelity['wheel']['clipped_flag_mismatches']==0,'495_WARM_PHYSICAL_FIDELITY')
                require(len(live.capture_holds495)==2,'495_SOURCE_WARM_DIRECT_CAPTURE')
                flags2=capture.compare_flags495(witnesses[1]['capture_hold495'],live.capture_holds495[1],runtime.binding)
                require(flags2['passed'] and flags2['safe'],'495_SOURCE_WARM_DIRECT_FLAGS')
                actual2,_=ledger.row_candidate(actual1,row,material['fixed']['line'],sum(material['fixed']['free_profile']['ds']))
                require(asdict(actual2)==witnesses[1]['ledger_after'],'495_WARM_NATIVE_LEDGER')
                projection=geometry.Projection439(material['fixed']['line'],sum(material['fixed']['free_profile']['ds']),.1)
                transition=ledger.geometry_transition(projection,frame,row)
                model1=models.ForecastLedger(**before);model2=live.ledger
                expected=projection.progress(model1.progress_m,transition,'model')
                require(ledger.equal(expected,frame['model_progress']) and ledger.equal(expected,model2.progress_m),'495_WARM_OWN_MODEL_PROGRESS')
                reconstructed=model1.advance_prediction(models.ModelPrediction(expected,model1.last_clock_tick+4,frame['predicted']['finished']))
                require(asdict(reconstructed)==asdict(model2),'495_WARM_FULL_MODEL_LEDGER')
                bound=projection.progress_interval(geometry.Interval(*report1['progress_interval']),transition)
                report2,_=ledger.compare_ledgers(actual1,actual2,model1,model2,
                    bool(actual2.progress_m>=actual1.goal_m or actual2.done),
                    bool(model2.progress_m>=model1.goal_m or model2.done),bound,
                    geometry.Interval(*report1['goal_interval']))
                require(not row['safety'] and not frame['safety'],'495_WARM_SAFETY')
                report2.update(geometry=transition,fidelity=fidelity,direct_capture495=flags2,genuine_warm_no_restore=True,
                               prior_model_ledger=before,actual_execution_allowed=False,actual_DONE_authorized=False)
                reports.append(report2)
            direct_holds=copy.deepcopy(live.capture_holds495)
            path,digest=online.closed(live);live=None
            records.append(dict(repetition=rep,path=path,sha256=digest,holds=len(reports),comparisons=reports,direct_holds495=direct_holds))
            meter.checkpoint('SOURCE_CURRENT_COPY_PASSED',slot=material['slot'],repetition=rep)
        require(meter.b['worlds']-start_worlds==3 and meter.b['ticks']-start_ticks==16,'495_SOURCE_EXACT_COST')
        packet=dict(stage=495,passed=True,slot=material['slot'],binding=copy.deepcopy(runtime.binding),
                    case_identity_digest=material['case_identity_digest'],p4_nodes_digest=fingerprint(material['projected_nodes']),
                    root_context_sha256=material['root_context_sha256'],root_state_digest=fingerprint(ctx['state']),
                    copies=records,new_worlds=3,new_charged_ticks=16,wrapper_holds=4,
                    independent_cold_first_exact=True,genuine_warm_second_native_qualified=True,strict_direct_flags495=True,old_raw_flags_used=False,native_direct_holds495=[copy.deepcopy(w['capture_hold495']) for w in witnesses])
        path=meter.d/(material['slot']+'-source-gate-private.json');save(path,packet)
        return str(path),sha(path)
    finally:
        if live is not None and not live.closed:online.closed(live)
