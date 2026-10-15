"""Freeze exactly two cached-policy arms and their hard call/reset budgets."""
import argparse
import datetime
import time
from pathlib import Path
from retry.path271_run import read,save,sha

ROUTE='''def route_observer(image,obstacles_override=None,speed=0.,previous_steer=0.):
    global routing_evidence
    full=copy.deepcopy(agent.hazards)
    assert [list(p) for p in obstacles_override]==[list(p[:3]) for p in full]
    assert len(support_state)==len(full)
    removed=[i for i,item in enumerate(support_state) if confidence_enabled and item['low']]
    selected=[p[:3] for i,p in enumerate(full) if i not in removed]
    path=original_route(image,selected,speed=speed,previous_steer=previous_steer)
    assert agent.hazards==full
    routing_evidence=dict(enabled=confidence_enabled,removed_indices=removed,
        removed_evidence=[support_state[i] for i in removed],full_hazards=full,
        routing_hazards=selected,tracker_preserved=True)
    observed_route['path']=[list(map(float,p)) for p in path]
    return path
'''


def verify(R):
    D=R/'stage342';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    from retry.confidence341_stage import verify as prior_verify
    prior_verify(R);G=Path(__file__).resolve().parent.parent;D=R/'stage342';assert not D.exists();D.mkdir(mode=0o700)
    proposal=read(R/'stage341/summary-private.json')['next_minimum_cache_comparison'];assert proposal['exact_saved_policy_act_calls']==2630
    prior=read(R/'stage337/plan.json');base=prior['config'];original=Path(base['worker_path']);assert sha(original)==base['worker_sha256'];source=original.read_text();logic=G/'retry/support342_logic.py'
    marker='original_tracked=TemporalRouteAgent.tracked_obstacles';assert source.count(marker)==1
    source=source.replace(marker,logic.read_text()+"\nconfidence_enabled=json.loads((clean/'confidence342-config.json').read_text())['enabled']\nsupport_state=[]\nsupport_record=None\nrouting_evidence=None\nact_step=0\n"+marker)
    source=source.replace('    global tracker_record\n','    global tracker_record,support_state,support_record\n')
    marker='    return out\nTemporalRouteAgent.tracked_obstacles=tracked_observer';assert source.count(marker)==1
    source=source.replace(marker,"    support_record=advance_evidence(tracker_record,support_state,act_step,image)\n    support_state=support_record['after']\n"+marker)
    start=source.index('def route_observer(');end=source.index('nominal_module.connected_route=route_observer',start);source=source[:start]+ROUTE+source[end:]
    source=source.replace('agent.reset(obs);history=[];pending=False;last_base=None','agent.reset(obs);history=[];pending=False;last_base=None;support_state=[];support_record=None;routing_evidence=None;act_step=0')
    marker='base=np.asarray(agent.act(obs),np.float32);last_base=base.copy();pending=True';assert source.count(marker)==1;source=source.replace(marker,'act_step+=1\n                '+marker)
    source=source.replace("response['tracker_record']=tracker_record","response['tracker_record']=tracker_record\n    response['support_record']=support_record\n    response['routing_evidence']=routing_evidence")
    worker=D/'observer-worker-private.py';worker.write_text(source);worker.chmod(0o600)
    configs={}
    for mode,enabled in [('baseline',False),('candidate',True)]:
        constants=dict(base.get('constants',{}));assert 'confidence342-config.json' not in constants;constants['confidence342-config.json']=dict(enabled=enabled)
        configs[mode]=dict(base,worker_path=str(worker),worker_sha256=sha(worker),constants=constants)
    allcases=read(R/'stage341/plan.json')['cases'];names={q['key'] for q in proposal['affected_trajectories']};cases=sorted([c for c in allcases if c['key'] in names],key=lambda c:(c['key']!='N2_337',c['key']));untouched=[c for c in allcases if c['key'] not in names]
    for c in cases:
        c['expected_tracker']=str(R/f"stage334/{c['key']}/ON-private.jsonl") if c['format']=='334' else c['records']
    inputs=[original,worker,logic,Path(base['archive_path']),R/'stage341/plan.json',R/'stage341/summary-private.json',R/'stage341/detections-private.json',R/'stage341/final-report-verification.json',R/'stage337/plan.json',R/'stage338/cache/reset-private.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',R/'project-effective-budget-v353.json',R/'research-deadline-current.json']
    for c in allcases:
        inputs += [Path(c['pixels']),Path(c['records'])]
        if c['GT']:inputs.append(Path(c['GT']))
    inputs += [Path(c['expected_tracker']) for c in cases]
    inputs += [G/'retry'/n for n in ['support342_stage.py','support342_run.py','confidence341_run.py','frozen_composite_runtime.py']]
    p=dict(stage=342,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],configs=configs,sandbox_path=prior['sandbox_path'],cases=cases,untouched_cases=untouched,
        rule='Exactly zero raw-road pixels in one-pixel8-neighbor ring of a fresh direct component marks only that source lineage low support. Retain tracker and metadata; withhold its hard routing footprint while original lineage survives. Fresh direct detection independently re-evaluates its own pixels; original dedup/age/expiry ends old flags. No step/coordinate/GT/future-based predicate.',
        unchanged='Detector, tracker, association/dedup/age/expiry, near scheduling, count/min-distance feature definitions, frozen models/controller/lookahead. Only connected_route input filters the flag. Each arm has normal own memory and returned history on same fixed stored pixels.',
        order='Baseline337233fulloutput/state reproduction before candidate or other episodes. Then paired cases in registered order; no extra arm.',
        gates='Baseline337exact; all detector/components/source lineage/tracker invariant, pixel-only native audit, archive/hash/deadline. Any fixture-supported direct or birth-supported retained point withheld, any reproduction/integrity failure: stop, no candidate pass. Unknown semantic material/occlusion is never a safety pass.',
        budgets=dict(actor_act_calls=2630,actor_resets_on_stored_pixels=10,original_input_frames=1315,new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,parameter_sweeps=0,research_remaining=1436,final_reserved_actions=84000),
        recovery='Charge actor/reset requests before calls; journal returned evidence before gates. Record technical failures separately. No automatic replay exceeding2630/10 caps; exact shortfall if unrecoverable. No later native or promotion in342.',
        methodology='Parent confirms both full originals re-reviewed before342. P3/P8, single hypothesis and cheap falsification. Rule postselected from341; fixed before cache. Cache differences are not trajectory gains.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);save(D/'call-budget.json',dict(actor_act_calls=0,actor_resets=0,cap=2630,reset_cap=10));print('342registered baseline/candidate only; actor2630 reset10 caps; native0',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);build(a.parse_args().private_root)
