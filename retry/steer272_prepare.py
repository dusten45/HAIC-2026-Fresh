"""Freeze one steering-target ablation; cached identity and formula checks."""
import argparse, time
from pathlib import Path
import numpy as np
from retry.path271_run import read, save, sha
from retry.path271_geometry import local_path, pack as pack271
from retry.steer272_target import target, pack

def prepare(R):
    from retry.frozen_composite_runtime import prepare as actor
    G=Path(__file__).resolve().parent.parent; D=R/'stage272'; D.mkdir(mode=0o700)
    assert not (D/'plan.json').exists()
    previous=read(R/'stage271/plan.json'); config=dict(previous['candidate'])
    config.update(worker_path=str(G/'retry/steer272_worker.py'),worker_sha256=sha(G/'retry/steer272_worker.py'))
    sources=[G/'retry'/n for n in ['steer272_prepare.py','steer272_target.py','steer272_worker.py','steer272_run.py',
        'path271_geometry.py','path271_worker.py','racing258_run.py','pace268_run.py','frozen_composite_runtime.py','diagnose.py']]
    hashes={str(q):sha(q) for q in sources+[Path(config['archive_path']),R/'project-effective-budget-v272.json']}
    for road in previous['order']:
        for q in [Path(previous['frozen_paths'][road]),R/'stage271'/road/'result.json',R/'stage251/training'/road/'cache-private.npz',R/'stage251/training'/road/'materialized.json']:
            hashes[str(q)]=sha(q)
    p=dict(previous); p.update(stage=272,max_actions=3230,per_case_cap=1615,candidate=config,hashes=hashes,
        intervention='Only steering target selection:258 projected arc + actualGTspeed lookahead.271 path and240 longitudinal goal/P/head/scales retained.',
        advancement_gate='Both complete, faster than271 on both, no higher damage or p95path error than271 to recommend pixel component experiment. Beating240 remains separate candidate performance requirement.',
        stop='One frozen candidate, one native episode each; no fit/pace/grid. Technical failures stop without replay; cap means censoring.')
    save(D/'plan.json',p); (D/'plan.sha256').write_text(sha(D/'plan.json')+'\n'); (D/'plan.sha256').chmod(0o600)
    save(D/'budget.json',dict(actions=0)); identities=[]; samples=[]; calls=0; started=time.perf_counter()
    for road in p['order']:
        m=read(R/'stage251/training'/road/'materialized.json'); z=np.load(R/'stage251/training'/road/'cache-private.npz')
        frozen=read(p['frozen_paths'][road]); line=np.array(frozen['line']); ds=np.array(frozen['free_profile']['ds'])
        a=b=None; index=0
        try:
            a=actor(previous['candidate'],D/(road+'-identity271'),p['sandbox_path'])
            b=actor(config,D/(road+'-identity272'),p['sandbox_path'])
            a.call('reset',pack271(z['observations'][0])); b.call('reset',pack(z['observations'][0])); calls+=2
            for i in range(16):
                state=m['snapshots']['1']['hull'] if i==0 else m['actual'][i-1]
                path,index,_=local_path(line,np.array(state['position']),state['angle'],index)
                ra,_=a.call('act',pack271(z['observations'][i],2,path)); rb,_=b.call('act',pack(z['observations'][i],2,path)); calls+=2
                assert ra['action']==rb['action'] and ra['features']==rb['features'] and ra['nominal_state']==rb['nominal_state']
            identities.append(dict(road=road,pairs=16,disabled_steering_override_exact271=True))
        finally:
            if a: assert a.close()['process_reaped']
            if b: assert b.close()['process_reaped']
        b=None; index=0
        try:
            b=actor(config,D/(road+'-active-samples'),p['sandbox_path']); b.call('reset',pack(z['observations'][0])); calls+=1
            for i in range(117):
                state=m['snapshots']['1']['hull'] if i==0 else m['actual'][i-1]
                pos=np.array(state['position']); angle=state['angle']; speed=float(np.linalg.norm(state['velocity']))
                path,index,detail=local_path(line,pos,angle,index)
                if i not in [0,12,64,116]: continue
                steering,meta=target(line,ds,pos,angle,speed,index,detail['projection_fraction'])
                # Independent exact258 formula, with global arc and source frame.
                sarc=np.r_[0,np.cumsum(ds)]; j=index%len(line)
                goal=(sarc[j]+detail['projection_fraction']*ds[j]+max(6.,min(25.,3.24+.22*speed)))%sarc[-1]
                k=min(len(line)-1,int(np.searchsorted(sarc,goal,side='right')-1))
                alpha=(goal-sarc[k])/max(ds[k],1e-9); delta=line[k]+alpha*(line[(k+1)%len(line)]-line[k])-pos
                expected=float(delta@[np.cos(angle),np.sin(angle)])
                assert steering[0]==expected and steering[2]==float(delta@delta)
                rb,_=b.call('act',pack(z['observations'][i],2,path,steering)); calls+=1
                f=rb['features']; audit=rb['steering_audit']; assert audit['active'] and audit['controller_calls']==1
                assert audit['original_nominal_gas']==f[14] and audit['original_nominal_brake']==f[15]
                expected_steer=.8*float(np.clip(np.arctan(2*3.24*expected/max(delta@delta,1e-6)),-.4,.4))+.2*f[7]
                assert np.float32(expected_steer)==np.float32(rb['action'][0])
                samples.append(dict(road=road,action=i+1,lookahead_m=meta['steering_lookahead_m'],
                    GT_actual_speed=speed,pixel_path_speed=f[3],HUD_feedback_speed=f[4],original_longitudinal_target=f[6],
                    original_steer=audit['original_steer'],new_steer=rb['action'][0],nominal_pedals_unchanged=True))
        finally:
            if b: assert b.close()['process_reaped']
    save(D/'preflight.json',dict(passed=True,identities=identities,samples=samples,offline_actor_calls=calls,
        identity_pairs=32,formula_samples=8,wall_s=time.perf_counter()-started,native_actions=0,model_physics_ticks=0))
    print('272preflight passed:32identitypairs,8formula samples,native0',flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--private-root',type=Path,required=True);prepare(a.parse_args().private_root.resolve())
