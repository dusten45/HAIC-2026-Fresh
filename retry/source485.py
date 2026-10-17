"""Three independently restored first nominal holds; no policy selection."""
import copy,pickle,random
from dataclasses import asdict
import numpy as np
from retry.observer435 import Child
from retry.law477 import ReferencePolicy477,PROJECTED
from retry.planner419 import GoalLedger
from retry.ledger439 import compare_first,require
from retry.pilot420_backend import snapshot,fingerprint,rnghash
from retry.online481 import closed,raw_flags
from retry.mechanism479 import physical_identity
from retry.receipt421_io import save_receipt
from retry.loss389_analyze import sha


def qualify(meter,material):
    ctx=material['context'];actual=GoalLedger(**material['actual_root_ledger'])
    binding=ReferencePolicy477(PROJECTED,material['projected_nodes'],material['profile_sha256'])
    records=[];first=None;live=None
    try:
        for rep in (1,2,'held'):
            py,npr=pickle.loads(ctx['RNG']['global_pickle']);random.setstate(py);np.random.set_state(npr)
            label=material['slot']+'_source_'+str(rep)
            meter.capture_inputs(ctx['state'],ctx['before'],actual,label+'_inputs',gate='485_NEW_CASE_CURRENT_NATIVE_WITNESS_ONLY')
            live=Child(meter,copy.deepcopy(ctx['state']),copy.deepcopy(ctx['before']),actual,material['fixed'],np.asarray(material['pace']),label,'nominal',world_tag='485_source')
            binding.inject(live)
            require(physical_identity(snapshot(live.m))==physical_identity(ctx['state']),'485_SOURCE_ROOT_RESTORE')
            require(live.ctrl.memory()==ctx['before'] and rnghash()==ctx['RNG']['digest'],'485_SOURCE_MEMORY_RNG')
            live.one('485_nominal_source')
            require(len(live.rows)==1 and live.status=='ACTIVE','485_SOURCE_SAFE_ACTIVE')
            row=live.rows[0]
            _,report=compare_first(actual,row,material['witness_row'],material['fixed'])
            raw_flags(live.stream.posts,material['witness_posts'])
            record=dict(row=copy.deepcopy(row),posts=copy.deepcopy(live.stream.posts),state=snapshot(live.m),memory=live.ctrl.memory(),ledger=asdict(live.ledger),RNG=rnghash())
            if first is None:first=record
            else:require(record==first,'485_SOURCE_COLD_HELD_REPEAT_EXACT')
            path,digest=closed(live);live=None
            records.append(dict(repetition=rep,path=path,sha256=digest,comparison=report))
            meter.checkpoint('SOURCE_CURRENT_COPY_PASSED',slot=material['slot'],repetition=rep)
        packet=dict(stage=485,passed=True,slot=material['slot'],case_identity_digest=material['case_identity_digest'],p4_nodes_digest=fingerprint(material['projected_nodes']),root_context_sha256=material['root_context_sha256'],root_state_digest=fingerprint(ctx['state']),copies=records,new_worlds=3,new_charged_ticks=12)
        path=meter.d/(material['slot']+'-source-gate-private.json');save_receipt(path,packet)
        return str(path),sha(path)
    finally:
        if live is not None and not live.closed:closed(live)
