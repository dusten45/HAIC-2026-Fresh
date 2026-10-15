"""Close registered frozen diagnostics and preserve separate native reserves."""
import datetime
from pathlib import Path
import sys
import numpy as np
from retry.path271_run import read,save,sha
from retry.link348_stage import G


def close(R):
    D=R/'stage348';assert not (D/'cost.json').exists();p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    outputs=[read(D/f'{g}-output-private.json') for g in p['groups']];records=[r for o in outputs for r in o['records']]
    assert len(records)==12
    calls={k:sum(o['calls'][k] for o in outputs) for k in ['routing','target']};assert calls==dict(routing=24,target=24)
    public_records=[]
    for r,c in zip(records,p['comparisons']):
        assert (r['label'],r['step'])==(c['label'],c['step'])
        restored=r['variants']['restored'];matches=restored['path']==c['peer_path'] and restored['target']==c['peer_target']
        if c['common_input_and_prestate']:assert matches
        if not c['removed']:assert not r['path_changed'] and not r['target_changed']
        public_records.append(dict(context=r['label'],step=r['step'],footprints_restored=c['removed'],path_changed=r['path_changed'],target_changed=r['target_changed'],common_actual_input_prestate=c['common_input_and_prestate'],recorded_control_diff=c['actual_control']!=c['peer_control'],feature_difference_indices=c['feature_difference_indices'],restoration_matches_recorded_peer=matches,causal_control_comparison_allowed=c['common_input_and_prestate']))
    n=next(r for r in public_records if r['context']=='N2' and r['step']==127);assert n['feature_difference_indices']==[9] and n['path_changed'] and not n['target_changed']
    for rel in ['stage297/DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/rel).exists(),rel
    assert sha(R/'stage296/submission296.zip')=='0a6c5e286e87d75498c5aec1174c7af3fd54f6efa34b0d83ca1efba5d404a937'
    assert sha(R/'stage296/champion-manifest.json')=='b92fe5307a491bfb9d1f5081bf97c9c1d4646dcf9c8511fb169bc48c8f9349e5'
    v=read(R/'project-effective-budget-v359.json');assert (v['actual_cumulative_wrapper_actions'],v['research_remaining'],v['final_reserved_actions'],v['final_reserve_used'])==(1284005,233,84000,0)
    cost=dict(stage=348,new_wrapper_actions=0,new_actor_calls=0,new_environment_resets=0,new_source_physics_rollout_ticks=0,new_learning_fits=0,parameter_sweeps=0,new_paid_resources=0,function_calls=calls,function_wall_s=sum(o['wall_s'] for o in outputs),function_CPU_s=sum(o['CPU_s'] for o in outputs),actual_cumulative_wrapper_actions=1284005,research_remaining=233,final_reserved_actions=84000,final_reserve_used=0,B_operating_cap=1368238,measurement_scope='Function timers exclude imports, preparation, hashing, closure and git. No new simulation cost; historical actual records reused without recounting.')
    result=dict(stage=348,reproduction_passed=True,records=public_records,cost=cost,promotion=False,protocol_status='prepared_not_executed',new_protected_split_opened=False,champion296_preserved=True,
        findings=['296 O2: restoring the held footprint changes route and target only at146 among146-153. At146 matched actual inputs/prestate link the intervention to actual steering and pedals. At147-153 actual controls still differ but own trajectories/memory already differ; no fresh independent attribution.',
        'Current334ON/H1 O2: footprint restoration at137 and145 changes neither route nor target; matched actual controls remain identical. No global harmlessness or occlusion claim.',
        'N2: at127 identical actual inputs/prestate show route length feature9 as the only feature difference, same target/steering and different pedals. At128 route/target differ on the recorded candidate state, but actual inputs already diverge; no independent steering attribution.'],
        limits=['No Agent/controller invocation, policy replay, fit, parameter search or new native run. Restored route/target are function counterfactuals; restored controls are not generated.',
        'The203lineage and allocation of the260ms official gap remain unresolved. The previous347 result remains baseline22.360s versus candidate22.620s on one known condition; no promotion or generalization.',
        'Geometric support does not establish semantic identity or actual occlusion. Policy296 and current334ON/H1 contexts remain separate.'],deadline_utc=p['deadline_utc'])
    cost['function_call_scope']='24 direct connected_route entry calls plus24 direct route_target entry calls. Internal route_target calls made by connected_route candidate evaluation are included in routing computation, not separately counted.'
    save(D/'cost.json',cost);save(D/'summary-private.json',result);save(G/'retry/link348_result.json',result)
    v.update(version=360,prior_budget_path=str(R/'project-effective-budget-v359.json'),prior_budget_sha256=sha(R/'project-effective-budget-v359.json'),cost_path=str(D/'cost.json'),cost_sha256=sha(D/'cost.json'),B_increment=0,stage348_new_wrapper_actions=0,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());assert not (R/'project-effective-budget-v360.json').exists();save(R/'project-effective-budget-v360.json',v)
    ledger=R/'experiment-cost-lines.jsonl';assert not any(__import__('json').loads(s).get('stage')==348 for s in ledger.read_text().splitlines())
    with ledger.open('a') as f:f.write(__import__('json').dumps(cost)+'\n')
    save(D/'final-report-verification.json',dict(passed=True,registered_source_hashes_preserved=True,reproduction_states=12,calls=calls,native_actions=0,research_remaining=233,final_reserve=84000,no_new_split_opened=True,protocol_executed=False))
    print(__import__('json').dumps(dict(passed=True,cost=cost)),flush=True)


if __name__=='__main__':close(Path(sys.argv[1]).resolve())
