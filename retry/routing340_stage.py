"""Register and qualify one persistent single-lineage routing intervention."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.probe338_stage import stack

ROUTE='''act_step=0
observed_filter=None
def route_observer(image,obstacles_override=None,speed=0.,previous_steer=0.):
    global observed_filter
    full=copy.deepcopy(agent.hazards)
    assert [list(p) for p in obstacles_override]==[list(p[:3]) for p in full]
    if act_step==121:
        fresh=[p for p in full if p[3]==0]
        assert len(tracker_record['direct'])==len(fresh)==1
        assert list(fresh[0][:3])==tracker_record['direct'][0]
    removed=[i for i,p in enumerate(full) if act_step>=127 and act_step-int(p[3])==121]
    assert len(removed)<=1
    selected=[p[:3] for i,p in enumerate(full) if i not in removed]
    path=original_route(image,selected,speed=speed,previous_steer=previous_steer)
    assert agent.hazards==full
    observed_filter=dict(step=act_step,removed_indices=removed,removed=[full[i] for i in removed],
        full_hazards=full,routing_hazards=selected,tracker_preserved=True,
        lineage_birth=121,lineage_direct_index=0)
    observed_route['path']=[list(map(float,p)) for p in path]
    return path
'''


def verify(R,full=False):
    D=R/'stage340';p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    assert time.time()<datetime.datetime.fromisoformat(p['deadline_utc'].replace('Z','+00:00')).timestamp()
    if full:
        for f,h in p['source_hashes'].items():assert sha(f)==h,f
    return p


def build(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage340';assert not D.exists();D.mkdir(mode=0o700)
    from retry.lineage339_stage import verify as previous_verify
    previous_verify(R,True);assert read(R/'stage339/final-saved-evidence-check.json')['passed'];assert read(R/'stage339/routing-only-receipt.json')['passed']
    prior=read(R/'stage337/plan.json');base=prior['config'];original=Path(base['worker_path']);assert sha(original)==base['worker_sha256'];source=original.read_text()
    a=source.index('def route_observer(');b=source.index('nominal_module.connected_route=route_observer',a);source=source[:a]+ROUTE+source[b:]
    source=source.replace('agent.reset(obs);history=[];pending=False;last_base=None','agent.reset(obs);history=[];pending=False;last_base=None;act_step=0')
    old='base=np.asarray(agent.act(obs),np.float32);last_base=base.copy();pending=True';assert source.count(old)==1;source=source.replace(old,'act_step+=1\n                '+old)
    source=source.replace("response['tracker_record']=tracker_record","response['tracker_record']=tracker_record\n    response['routing_filter']=observed_filter")
    worker=D/'observer-worker-private.py';worker.write_text(source);worker.chmod(0o600)
    cfg=dict(base,worker_path=str(worker),worker_sha256=sha(worker))
    inputs=[original,worker,Path(base['archive_path']),R/'stage337/plan.json',R/'stage337/B/initial-scene-private.json',R/'stage337/B/result.json',R/'stage337/B/trace-private.jsonl',R/'stage337/B/frames-actions-private.npz',R/'stage335/B/first-divergence-private.json',R/'stage339/plan.json',R/'stage339/selection-repair.json',R/'stage339/selection-repair-receipt.json',R/'stage339/routing-only-receipt.json',R/'stage339/final-saved-evidence-check.json',R/'stage339/summary-private.json',R/'stage296/champion-manifest.json',R/'stage296/submission296.zip',R/'project-effective-budget-v351.json',R/'research-deadline-current.json']
    inputs += [R/f'stage339/routing-only/{s}/probes-private.json' for s in [337,338]]
    inputs += [G/'retry'/n for n in ['routing340_stage.py','routing340_run.py','frozen_composite_runtime.py','episode337_run.py','pedal331_run.py','diagnose.py','full_route_reproduction.py','source_vehicle_transition.py']]
    inputs += [G/'env_wrapper.py',G/'damage.py']+list((G/'core').rglob('*.py'))
    p=dict(stage=340,registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),deadline_utc=read(R/'research-deadline-current.json')['deadline_utc'],config=cfg,base_config=base,case=prior['case'],sandbox_path=prior['sandbox_path'],observer_rng_seed=prior['observer_rng_seed'],cap=233,
        hypothesis='Persistent exclusion of the single121:0lineage from routing, through its normal lifetime, is locally sufficient to resolve the new blockage; one paired test, not detector semantics or general completion.',
        authorization='Parent explicitly approved340 retry after full original review; no existing registration or running experiment found. Reuse actual337 A, exactly one newN2B, no extra grant/reserve.',
        change='Only connected_route obstacle input excludes121:0from127while present. Birth121 has exactly one fresh detection, verified on immutable339cache and live originalprefix. Tracker retains point and original dedup/age/spatial-expiry; schedule/count/min-distance features still see all hazards. No model/feature definition/controller/threshold/pedal/lookahead change.',
        contract='Exact actualprefix1-126 and127input.127+own observations, full returned modified-policy controls and normal own nominal-memory updates, no stored continuation or memory override. Filter follows unique birth-age lineage and ceases on original dedup/expiry, expected130 on saved inputs. NoGT in actor.',
        gate='First339frozen clone single-lineage selection and actual obstacle preserved, then fresh cache133 with original outputs/state exact126, full tracker exact133, original339routing-only controls exact127/128 while prior nominal memories agree. First full float32 control difference127pedals, firststeer128. Cache continuation memory thereafter may legitimately differ from A.',
        outcomes='Compare first contact fixture/time, touching endpoints, tile progress past132, speed and official retirement; damage alone not pass. Same blockage/retirement rejects only this local sufficiency.233survival nofinish isprotocolcensor, never completion.',
        stop='Official terminal, prefix/gate/hash mismatch,233cap or authorizationdeadline. No retries after nativeopening, newA, fits, tuning, protected splits or promotion.',
        budget=dict(research_remaining=1669,cap=233,research_after_maximum=1436,additional_research=0,final_reserved_actions=84000,final_reserve_used=0),
        scope='334aggregate deterioration and subset caveat, actual occlusion unknown, normal avoidance curve target following not presumed defective. Known postselectedN2, no causal identification of all birth/transport/control mechanisms.',source_hashes={str(f):sha(f) for f in inputs})
    save(D/'plan.json',p);(D/'plan.sha256').write_text(sha(D/'plan.json')+'\n');(D/'plan.sha256').chmod(0o600);print('340registered: oneB cap233 from1669; reserve84000 separate',flush=True)


def cache(R):
    from retry.frozen_composite_runtime import prepare
    D=R/'stage340';p=verify(R,True);assert not (D/'cache-opening.json').exists();save(D/'cache-opening.json',dict(epoch=time.time()))
    for stage in [337,338]:
        records=read(R/f'stage339/routing-only/{stage}/probes-private.json')
        for row in records:
            v=row['probe']['variants'];base=v['original']['hazards'];selected=v['drop_birth121']['hazards'];removed=[h for h in base if h not in selected]
            assert len(removed)==int(row['step']<=129)
            if removed:assert row['step']-removed[0][3]==121
            if row['step']==124:assert base[-1] in selected
    save(D/'339-cache-gate.json',dict(passed=True,scenes=18,one_lineage_only=True,actual_current_obstacle_preserved=True,new_native_actions=0,new_actor_calls=0))
    z=np.load(R/'stage337/B/frames-actions-private.npz');old=[json.loads(s) for s in (R/'stage337/B/trace-private.jsonl').read_text().splitlines()];expected={q['step']:q['probe']['variants']['drop_birth121'] for q in read(R/'stage339/routing-only/337/probes-private.json')}
    w=prepare(p['config'],D/'cache/cpu',p['sandbox_path']);start,cpu=time.perf_counter(),time.process_time();records=[];changes=[];steerchanges=[]
    try:
        reset,_=w.call('reset',stack(z['frames_uint8'],0));assert reset['state']==read(R/'stage338/cache/reset-private.json')['state'];save(D/'cache/reset-private.json',reset)
        for i in range(133):
            obs=stack(z['frames_uint8'],i);r,_=w.call('act',obs);f=r['routing_filter'];assert r['tracker_record']==old[i]['tracker'] and f['tracker_preserved']
            assert len(f['removed'])==int(126<=i<=128)
            if f['removed']:assert i+1-f['removed'][0][3]==121 and len(f['removed'])==1
            assert r['features'][11]==len(r['tracker_record']['after'])
            if r['action']!=old[i]['returned_action']:changes.append(i+1)
            if r['action'][0]!=old[i]['returned_action'][0]:steerchanges.append(i+1)
            if i<126:assert r['action']==old[i]['returned_action'] and r['features']==old[i]['features'] and r['pixel_path']==old[i]['pixel_path'] and r['delta_audit']==old[i]['audit']
            if i in [126,127]:assert r['action']==expected[i+1]['action'] and r['features']==expected[i+1]['features'] and r['pixel_path']==expected[i+1]['path']
            c,_=w.call('commit',np.asarray(r['action'],np.float32));assert c['memory']==r['state']['previous_steer'] and np.float32(c['memory'])==np.float32(r['action'][0])
            if i<126:assert c['state']==old[i]['policy'] and c['memory']==old[i]['nominal_memory']
            records.append(dict(response=r,commit=c))
        assert changes[0]==127 and steerchanges[0]==128
        receipt=dict(passed=True,cached_actor_calls=133,full_prefix126_exact=True,all_tracker_updates133_exact=True,first_full_control_difference=127,first_steering_difference=128,stage339_single_lineage_and_real_obstacle_gate=True,normal_own_memory=True,filter_off_after_saved_expiry130=True,new_native_actions=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=c['actor_cumulative_CPU_s'])
    finally:receipt_reaping=w.close()
    receipt['reaping']=receipt_reaping;save(D/'cache/records-private.json',records);save(D/'cache-receipt.json',receipt);verify(R,True)
    v=read(R/'project-effective-budget-v351.json');assert (v['research_remaining'],v['actual_cumulative_wrapper_actions'],v['final_reserved_actions'],v['final_reserve_used'])==(1669,1282569,84000,0)
    save(D/'reservation.json',dict(cap=233,from_existing_research=1669,research_after_maximum=1436,additional_research=0,final_reserve_change=0));save(D/'native-budget.json',dict(cap=233,actions=0));print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['build','cache']);a.add_argument('--private-root',required=True,type=Path);args=a.parse_args();globals()[args.command](args.private_root)
