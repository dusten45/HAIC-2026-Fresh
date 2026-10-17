"""Typed model-current B selection, explicitly registered alternative rejections."""
import copy,time
from dataclasses import asdict
from retry.query445 import bind_model_query
from retry.pilot420_backend import fingerprint,snapshot,rnghash,metrics,canonical_projection
from retry.planner419_model_ledger import ForecastLedger,ModelPrediction
from retry.audit431 import physical_tokens
from retry.ledger439 import require
from retry.receipt421_io import save_receipt


def classify451(c):
    require(c.rows and c.status in ['ACTIVE','UNSAFE','INFEASIBLE'],'451_SHADOW_UNEXPECTED_TECHNICAL_TERMINAL_OR_EMPTY')
    flags=[];ledger=ForecastLedger.fork(c.root_ledger)
    h=c.rows[0]['raw_hull'][0];previous_arc=canonical_projection(c.line,h['origin_position'],h['COM_linear_velocity'],c.rows[0]['memory_before']['C']['phase'])['arc']
    for row in c.rows:
        physical_tokens(row['safety'],allow_empty=True)
        projected,computed=metrics(row['predicted'],row['tires'],row['raw_hull'],c.line,row['memory_after']['C']['phase'])
        progress=ledger.progress_m+(projected['arc']-previous_arc+c.L/2)%c.L-c.L/2;previous_arc=projected['arc']
        ledger=ledger.advance_prediction(ModelPrediction(progress,ledger.last_clock_tick+row['predicted']['raw_ticks'],row['predicted']['finished']))
        require(progress==row['model_progress'] and ledger.goal_m==row['model_goal'] and ledger.age_actions==row['model_age'] and ledger.actual_root_digest==row['actual_root_ledger_digest'],'451_SHADOW_LEDGER_NOT_OWN_OBSERVED_GEOMETRY')
        require(set(computed)==set(row['safety']),'451_SHADOW_PHYSICAL_REASON_NOT_OBSERVED')
        flags.append(set(row['safety']))
    require(asdict(ledger)==asdict(c.ledger),'451_SHADOW_FINAL_LEDGER_NOT_CHAIN')
    if c.status=='ACTIVE':
        require(len(c.rows)==13 and c.initial_ok and c.initial_safe and c.initial_progress and not any(flags) and not c.ledger.deadline_missed,'451_SHADOW_ACTIVE_WITHOUT_H13_CERTIFICATE')
        return dict(valid=True,kind='SAFE_PROGRESS_H13',actions=len(c.rows))
    if c.status=='UNSAFE':
        reasons=physical_tokens(c.error)
        require(len(c.rows)<=13 and not any(flags[:-1]) and flags[-1]==set(reasons),'451_PHYSICAL_REJECTION_NOT_FIRST_STOP')
        return dict(valid=False,kind='REGISTERED_PHYSICAL_INELIGIBILITY',actions=len(c.rows),reasons=sorted(reasons))
    require(c.error=='predicted_progress_deadline' and c.ledger.deadline_missed and not any(flags),'451_NONREGISTERED_PROGRESS_REJECTION')
    return dict(valid=False,kind='REGISTERED_PROGRESS_INELIGIBILITY',actions=len(c.rows))


def select451(study,parent,before,nominal,label):
    query=bind_model_query(parent,study.actual,before,nominal,study.fixed,study.policy_digest)
    query.validate(parent,study.actual)
    save_receipt(study.d/(label+'-query-root-private.json'),dict(context=asdict(query.context),context_digest=query.context_digest,full_parent_ledger=asdict(parent.ledger),immutable_native_ledger=asdict(study.actual),actual_execution_allowed=False,actual_DONE_allowed=False))
    alternatives=[];selected=None
    for recipe in ['nominal','neutralbrake']:
        pair=[]
        for rep in [1,2]:
            child=query.spawn(study,parent,study.actual,label+'_'+recipe+str(rep),recipe)
            try:
                child.initial13('451_shadow_'+recipe)
                query.validate(parent,study.actual)
                classification=classify451(child)
                require(child.rows[0]['memory_before']==before and child.rows[0]['memory_after']==parent.ctrl.memory(),'451_SHADOW_CURRENT_NOMINAL_MEMORY')
                pair.append(dict(signature=child.signature(),classification=classification,first=copy.deepcopy(child.rows[0])))
            finally:child.dump(study.d);child.close()
        require(pair[0]==pair[1],'451_SHADOW_INDEPENDENT_REPEAT')
        alternatives.append(dict(recipe=recipe,**pair[0]['classification']))
        if pair[0]['classification']['valid']:
            selected=dict(recipe=recipe,first=pair[0]['first']);break
        # Only classify451's two preregistered ineligibility kinds arrive here.
    require(selected is not None,'451_NO_SAFE_B_OPTION')
    query.validate(parent,study.actual)
    record=dict(context_digest=query.context_digest,alternatives=alternatives,selected_recipe=selected['recipe'],actual_execution_allowed=False,actual_DONE_allowed=False)
    save_receipt(study.d/(label+'-selection-before-parent-private.json'),dict(record=record,selected_first=selected['first'],parent_state=snapshot(parent.m),parent_memory_after_nominal=parent.ctrl.memory(),RNG_digest=rnghash()))
    return query,selected,record
