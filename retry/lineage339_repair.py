"""Repair the birth-index selector; rerun only the two affected fixed scenes."""
import argparse
import datetime
import json
import time
from pathlib import Path
import numpy as np
from retry.path271_run import read,save,sha
from retry.probe338_stage import stack
from retry.frozen_composite_runtime import prepare


def register(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage339';assert not (D/'selection-repair.json').exists()
    plan=read(D/'plan.json');old=D/'executed-source/observer-worker-initial.py';worker=D/'observer-worker-private.py'
    source=old.read_text();old_line="selected=[p for p in hazards if diagnostic_step-int(p[3])!=birth]"
    new_line="selected=[p for p in hazards if diagnostic_step-int(p[3])!=birth or (int(p[3])==0 and tuple(p[:3])!=tuple(direct[0]))]"
    first_fix="selected=[p for p in hazards if diagnostic_step-int(p[3])!=birth or (int(p[3])==0 and p[:3]!=direct[0])]"
    assert source.count(old_line)==1 and worker.read_text() in [source,source.replace(old_line,first_fix)]
    worker.write_text(source.replace(old_line,new_line));worker.chmod(0o600)
    replacements={}
    for current,original in [(worker,old),(G/'retry/lineage339_stage.py',D/'executed-source/lineage339_stage.initial.py')]:
        assert sha(original)==plan['source_hashes'][str(current)]
        replacements[str(current)]=dict(original_path=str(original),original_sha256=sha(original),fixed_sha256=sha(current))
    save(D/'selection-repair.json',dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        error='At birth124 two direct components shared age0; original step-only filter removed both. Only124 drop_birth124 is invalid on each recorded trajectory. Other original and counterfactual calls remain archived.',
        correction='At the birth frame select direct index0 only; at later frames the surviving birth124 lineage is unique. Birth121 is already unique. No change to actor, tracker, routing or controller.',
        validation='Exactly one selected hazard removed on each affected frame; other hazards byte/value preserved, current real-obstacle component remains. Original cloned output and live state unchanged. All later fixed-scene variants unchanged by the selector fix.',
        affected_scenes=[dict(stage=s,step=124,mode='drop_birth124') for s in [337,338]],source_replacements=replacements,
        fixed_worker_sha256=sha(worker),repair_script_sha256=sha(Path(__file__)),new_native_actions=0,new_environment_resets=0,planned_cached_actor_calls=248,planned_clone_calls=8))


def run(R):
    from retry.lineage339_stage import verify
    D=R/'stage339';p=verify(R,True);repair=read(D/'selection-repair.json');assert sha(Path(__file__))==repair['repair_script_sha256'];assert not (D/'selection-repair-opening.json').exists()
    save(D/'selection-repair-opening.json',dict(epoch=time.time()));start,cpu=time.perf_counter(),time.process_time();receipts=[]
    for stage in [337,338]:
        z=np.load(R/f'stage{stage}/B/frames-actions-private.npz');old=[json.loads(s) for s in (R/f'stage{stage}/B/trace-private.jsonl').read_text().splitlines()];F=D/f'selection-repair/{stage}';F.mkdir(parents=True,mode=0o700);w=prepare(p['config'],F/'cpu',p['sandbox_path'])
        try:
            w.call('reset',stack(z['frames_uint8'],0))
            for i in range(124):
                verify(R);obs=stack(z['frames_uint8'],i);r,_=w.call('act',obs);o=old[i]
                assert r['action']==o['returned_action'] and r['features']==o['features'] and r['tracker_record']==o['tracker'] and r['pixel_path']==o['pixel_path'] and r['delta_audit']==o['audit']
                if i==123:
                    probe,_=w.call('lineage_probe',obs);assert probe['state_preserved'] and probe['state']==r['state']
                    v=probe['variants'];base=v['original']['hazards'];chosen=v['drop_birth124']['hazards'];direct=o['tracker']['direct']
                    assert len(base)-len(chosen)==1
                    assert chosen==[h for h in base if h[:3]!=direct[0]]
                    assert direct[1]+[0] in chosen and direct[0]+[0] not in chosen
                    initial=read(D/f'diagnostic/{stage}/probes-initial-private.json')
                    before=next(q for q in initial if q['step']==124)['probe']['variants']
                    for mode in ['original','drop_birth121','current_only']:assert v[mode]==before[mode]
                    updated=[dict(q,probe=probe) if q['step']==124 else q for q in initial]
                    save(F/'probe-private.json',probe);save(D/f'diagnostic/{stage}/probes-private.json',updated)
                c,_=w.call('commit',z['actions'][i]);assert c['state']==o['policy'] and c['memory']==o['nominal_memory']
            receipts.append(dict(stage=stage,cached_actor_calls=124,clone_act_calls=4,actor_CPU_s=c['actor_cumulative_CPU_s'],one_lineage_only=True,real_current_component_preserved=True,other_variants_exact=True))
        finally:assert w.close()['process_reaped']
    verify(R,True)
    result=dict(passed=True,stages=receipts,cached_actor_calls=248,clone_act_calls=8,pure_routing_calls=8,actor_resets=2,new_environment_resets=0,new_native_actions=0,new_source_physics_ticks=0,new_learning_fits=0,wall_s=time.perf_counter()-start,runner_CPU_s=time.process_time()-cpu,actor_CPU_s=sum(x['actor_CPU_s'] for x in receipts))
    save(D/'selection-repair-receipt.json',result);print(json.dumps(result),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('command',choices=['register','run']);a.add_argument('--private-root',required=True,type=Path);args=a.parse_args();globals()[args.command](args.private_root)
