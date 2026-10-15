"""Register a bounded saved-pixel lineage audit; never import the simulator."""
import argparse
import datetime
import time
from pathlib import Path
from retry.path271_run import read, save, sha


PROBE = '''    if op=='lineage_probe':
        assert pending and 124<=diagnostic_step<=132
        obs=payload.reshape(4,84,84).copy();before_state=state()
        import retry.connected_agent as routing
        saved_route=copy.deepcopy(observed_route);saved_features=copy.deepcopy(observed_features)
        saved_evaluation=copy.deepcopy(routing.LAST_CONNECTION_EVALUATION)
        original_candidates=routing.route_candidates
        captured={}
        def candidates_observer(*args,**kwargs):
            values=original_candidates(*args,**kwargs)
            captured['candidates']=copy.deepcopy(values)
            return values
        hazards=copy.deepcopy(agent.hazards);direct=copy.deepcopy(tracker_record['direct'])
        variants={}
        try:
            routing.route_candidates=candidates_observer
            for mode in ['original','drop_birth121','drop_birth124','current_only']:
                if mode=='current_only': selected=[p+[0] for p in direct]
                elif mode.startswith('drop_birth'):
                    birth=int(mode.split('birth')[1])
                    selected=[p for p in hazards if diagnostic_step-int(p[3])!=birth or (int(p[3])==0 and tuple(p[:3])!=tuple(direct[0]))]
                else:selected=copy.deepcopy(hazards)
                clone=copy.deepcopy(diagnostic_before_agent)
                # Remove the observer's instance closure bound to the live agent.
                clone.__dict__.pop('correct_pedals',None)
                clone.hazards=copy.deepcopy(selected)
                clone.tracked_obstacles=lambda image,speed:[p[:3] for p in selected]
                calculated=np.asarray(clone.act(obs),np.float32)
                f=list(clone.selector_features)
                variants[mode]=dict(action=calculated.tolist(),features=f,
                    nominal_memory=float(clone.controller.previous_steer),
                    path=copy.deepcopy(observed_route['path']),target=None if f[0] else f[1:3],
                    nominal=f[13:16],delta_audit=copy.deepcopy(clone.delta_audit),
                    connection_evaluation=copy.deepcopy(routing.LAST_CONNECTION_EVALUATION),
                    candidates=copy.deepcopy(captured['candidates']),hazards=selected)
            original=variants['original']
            assert original['action']==last_base.tolist()
            assert original['features']==saved_features['features']
            assert original['path']==saved_route['path']
            assert original['nominal_memory']==float(agent.controller.previous_steer)
            assert original['delta_audit']==agent.delta_audit
        finally:
            routing.route_candidates=original_candidates
            routing.LAST_CONNECTION_EVALUATION=saved_evaluation
            observed_route.clear();observed_route.update(saved_route)
            observed_features.clear();observed_features.update(saved_features)
        assert state()==before_state
        response=dict(step=diagnostic_step,variants=variants,state_preserved=True,
            state=state(),clone_act_calls=4,pure_routing_calls=4,
            actual_frozen_package=True,not_a_trajectory=True)
    elif op=='commit':
'''


def verify(R, full=False):
    D=R/'stage339';p=read(D/'plan.json')
    assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        repairs=read(D/'selection-repair.json')['source_replacements'] if (D/'selection-repair.json').exists() else {}
        for f,h in p['source_hashes'].items():
            if sha(f)==h:continue
            repair=repairs[f];assert repair['original_sha256']==h and sha(repair['original_path'])==h and sha(f)==repair['fixed_sha256'],f
    if (D/'selection-repair.json').exists():
        repair=read(D/'selection-repair.json');p['config']=dict(p['config'],worker_sha256=repair['fixed_worker_sha256'])
    return p


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage339';assert not D.exists();D.mkdir(mode=0o700)
    prior=read(R/'stage338/plan.json')
    for f,h in prior['source_hashes'].items():assert sha(f)==h,f
    assert read(R/'stage338/final-saved-evidence-check.json')['passed']
    original=Path(prior['config']['worker_path']);source=original.read_text()
    start=source.index("    if op=='direct_probe':\n");end=source.index("    elif op=='commit':\n",start)
    source=source[:start]+PROBE+source[end+len("    elif op=='commit':\n"):]
    source=source.replace('last_base=None\ndef state():','last_base=None\ndiagnostic_step=0\ndiagnostic_before_agent=None\ndef state():')
    source=source.replace('agent.reset(obs);history=[];pending=False;last_base=None','agent.reset(obs);history=[];pending=False;last_base=None;diagnostic_step=0')
    source=source.replace('base=np.asarray(agent.act(obs),np.float32);last_base=base.copy();pending=True','diagnostic_before_agent=copy.deepcopy(agent);diagnostic_step+=1\n                base=np.asarray(agent.act(obs),np.float32);last_base=base.copy();pending=True')
    assert 'diagnostic_before_agent=copy.deepcopy(agent)' in source
    worker=D/'observer-worker-private.py';worker.write_text(source);worker.chmod(0o600)
    inputs=[original,worker,R/'stage338/plan.json',R/'stage338/final-saved-evidence-check.json',R/'stage334/summary-private.json',R/'project-effective-budget-v350.json',R/'research-deadline-current.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',Path(prior['config']['archive_path'])]
    for stage in [337,338]:
        inputs += [R/f'stage{stage}/B'/name for name in ['result.json','trace-private.jsonl','frames-actions-private.npz']]
    inputs += [R/'stage337/B/initial-scene-private.json']
    inputs += [G/'retry'/name for name in ['lineage339_stage.py','lineage339_run.py','lineage339_audit.py','frozen_composite_runtime.py']]
    inputs += [G/'core/vendor/car_racing.py',G/'env_wrapper.py']
    p=dict(stage=339,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],
        base_config=prior['config'],config=dict(prior['config'],worker_path=str(worker),worker_sha256=sha(worker)),sandbox_path=prior['sandbox_path'],
        question='Birth pixels, source lineage and fixed-scene routing influence of unresolved detections during the recorded approach.',
        gate='Reproduce every recorded337/338 input and returned action/features/audit/tracker/path/committed full state and nominal memory before any counterfactual. Actor resets on stored pixels only, no environment reset.',
        design='Audit every tracker update through the recorded endpoints; inspect births and124-132. Compare original vs dropping exactly one birth lineage121 or124 at a time, and current-only, on each same saved scene. Full frozen actor pipeline on pre-act clones with fixed routing hazards, prior nominal memory and all pedal machinery unchanged. No cloning state fed into continuation.',
        selection='121 and124 are the two separately unresolved birth lineages present in the already registered124-132 approach, not chosen by output magnitude. Drop each separately, never both except distinct current-only comparator. No GT enters the actor.',
        failure_taxonomy=['pixel detection birth','capture/projection correspondence uncertainty','temporal transport or expiry','routing candidate/target influence','controller target following','physical collision/retirement not re-tested'],
        stop='Any gate mismatch, state pollution, archive/source hash change, simulator import or deadline: stop dependent diagnosis. No native/reset/source rollout/fits/tuning; no threshold or policy edits. No promotion.',
        scope='Official objective remains completion/finish time. Fixed-scene path, target, controls and correspondence are diagnostic surrogates, not trajectory effects or completion improvements. Actual occlusion unverified; preserve334 aggregate deterioration and subset caveat.',
        budget=dict(new_native_actions=0,new_environment_resets=0,new_source_physics_ticks=0,new_learning_fits=0,research_remaining=1669,final_reserved_actions=84000,planned_reproduction_act_calls=369,planned_diagnostic_replay_act_calls=264,planned_clone_act_calls=72),
        methodology='Parent attests full24chapters and applied plan reread in this conversation. One hypothesis/change, explicit falsification and gate, costs and uncertainty; private originals not copied.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600)
    print('339 registered: native/reset/source rollout/fits0; gate369, replay264, clone72',flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--private-root',required=True,type=Path);build(a.parse_args().private_root)
