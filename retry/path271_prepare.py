"""Freeze one GT-path diagnostic and validate stored-input identity, no physics."""
import argparse, hashlib, json, zipfile
from pathlib import Path
import numpy as np
from retry.path271_geometry import local_path, pack, BOUNDS, SPACING, project
from retry.path271_run import read, save, sha

def prepare(R):
    from retry.frozen_composite_runtime import prepare as actor
    G=Path(__file__).resolve().parent.parent; D=R/'stage271'; D.mkdir(mode=0o700)
    assert not (D/'plan.json').exists()
    old=read(R/'stage270/plan.json'); archive=R/'stage240/submission240.zip'
    with zipfile.ZipFile(archive) as z:
        members={n:hashlib.sha256(z.read(n)).hexdigest() for n in z.namelist()}
    worker=G/'retry/path271_worker.py'
    config=dict(type='champion',archive_path=str(archive),archive_sha256=sha(archive),members_sha256=members,
        worker_path=str(worker),worker_sha256=sha(worker),assets={},constants={})
    sources=[G/'retry'/n for n in ['path271_geometry.py','path271_worker.py','path271_run.py',
        'path271_prepare.py','frozen_composite_runtime.py','pixel_sandbox_runtime.py','diagnose.py']]
    paths={r:str(R/'stage258'/f'{r}-plan-private.json') for r in ['O0','N0']}
    hashes={str(q):sha(q) for q in sources+[archive,R/'project-effective-budget-v271.json']}
    for road in paths:
        for q in [Path(paths[road]),R/'stage251/training'/road/'cache-private.npz',R/'stage251/training'/road/'materialized.json']:
            hashes[str(q)]=sha(q)
    p=dict(stage=271,deadline_utc='2026-10-16T10:01:55+00:00',order=['O0','N0'],max_actions=3856,per_case_cap=1928,
        candidate=config,sandbox_path=old['sandbox_path'],cases={r:old['cases'][r] for r in paths},
        initial_observations={r:old['initial_observations'][r] for r in paths},
        baselines={r:old['baselines'][r] for r in paths},frozen_paths=paths,hashes=hashes,
        intervention='Only ordered path supplied to exact240; no teacher pace/profile/GTspeed fed to policy',
        geometry_rule=dict(bounds_right_forward_metres=BOUNDS.tolist(),max_arc_spacing_m=SPACING,origin_prefix=True,
            first_contiguous_forward_slice_only=True,whole_map_foresight=True,occlusion_filter=False),
        advancement_gate='Both complete and both faster than cached240; otherwise close simple teacher-path regression. GT-only evidence never promotes submission.',
        stop='No fit/sweep/new labels/pace change; one episode each. Technical errors stop with consumed costs, no native replay. Budget cap is censoring.')
    save(D/'plan.json',p); (D/'plan.sha256').write_text(sha(D/'plan.json')+'\n'); (D/'plan.sha256').chmod(0o600)
    save(D/'budget.json',dict(actions=0)); identities=[]; coordinates=[]; baseline_tracking={}; calls=0
    for road in paths:
        z=np.load(R/'stage251/training'/road/'cache-private.npz'); m=read(R/'stage251/training'/road/'materialized.json')
        line=np.array(read(paths[road])['line']); baseline=identity=None
        try:
            baseline=actor(config,D/(road+'-preflight-base'),p['sandbox_path'])
            identity=actor(config,D/(road+'-preflight-identity'),p['sandbox_path'])
            for a in [baseline,identity]: a.call('reset',pack(z['observations'][0])); calls+=1
            for i in range(117):
                b,_=baseline.call('act',pack(z['observations'][i])); calls+=1
                c,_=identity.call('act',pack(z['observations'][i],2,b['path'])); calls+=1
                assert b['path_calls']==c['path_calls']==1
                assert np.array_equal(b['action'],c['action']) and b['features']==c['features'] and b['nominal_state']==c['nominal_state']
                assert np.array_equal(np.array(b['action'],np.float32),z['commands'][i])
                assert np.array_equal(np.array(b['features']),z['features'][i])
            identities.append(dict(road=road,pairs=117,action_features_memory_and_cached240_exact=True))
        finally:
            if baseline: assert baseline.close()['process_reaped']
            if identity: assert identity.close()['process_reaped']
        index=0; errors=[]
        for i in range(len(m['actual'])):
            state=m['snapshots']['1']['hull'] if i==0 else m['actual'][i-1]
            pos=np.array(state['position']); angle=state['angle']
            path,index,detail=local_path(line,pos,angle,index); errors.append(detail['path_error_m'])
            if i in [0,12,64,116]:
                points=np.array(path[1:]); assert len(points)>1
                assert np.all(points[:,0]>=BOUNDS[0]-1e-8) and np.all(points[:,0]<=BOUNDS[1]+1e-8)
                assert np.all(points[:,1]>=BOUNDS[2]-1e-8) and np.all(points[:,1]<=BOUNDS[3]+1e-8)
                assert max(np.linalg.norm(np.diff(points,axis=0),axis=1))<=SPACING+1e-8
                # Independent scalar SE2 inverse and pixel-unit round trips.
                world=pos+points[:,0,None]*[np.cos(angle),np.sin(angle)]+points[:,1,None]*[-np.sin(angle),np.cos(angle)]
                delta=world-pos
                recovered=np.c_[delta[:,0]*np.cos(angle)+delta[:,1]*np.sin(angle),-delta[:,0]*np.sin(angle)+delta[:,1]*np.cos(angle)]
                pixel=np.c_[42+1.3608*points[:,0],63-1.701*points[:,1]]
                converted=np.c_[(pixel[:,0]-42)/1.3608,(63-pixel[:,1])/1.701]
                assert np.max(abs(points-recovered))<1e-10 and np.max(abs(points-converted))<1e-10
                coordinates.append(dict(road=road,action=i+1,path_points=len(path),
                    forward_entry=path[1][1],pixel_row_min=float(pixel[:,1].min()),pixel_row_max=float(pixel[:,1].max()),
                    inverse_error=float(np.max(abs(points-recovered))),pixel_units_error=float(np.max(abs(points-converted))),
                    projection_distance_m=detail['path_error_m']))
        baseline_tracking[road]=dict(mean=float(np.mean(errors)),p95=float(np.percentile(errors,95)),max=float(max(errors)),
            reference='Cached240 pre-action poses measured against same frozen258 free line, same forward cursor')
    save(D/'preflight.json',dict(passed=True,identities=identities,coordinates=coordinates,baseline_tracking=baseline_tracking,
        offline_actor_calls=calls,native_actions=0,model_physics_ticks=0,original_archive_unmodified=True))
    print(json.dumps(dict(preflight_passed=True,identity_pairs=234,coordinate_samples=8,offline_actor_calls=calls,native=0)),flush=True)

if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__); a.add_argument('--private-root',type=Path,required=True); prepare(a.parse_args().private_root.resolve())
