"""Independent saved-evidence and static-geometry checks, no actor/simulation."""
import argparse
import json
import math
import time
from pathlib import Path

import cv2
import numpy as np
from retry.path271_run import read,save,sha
from retry.diagnostic332_run import rotate,world,local,signed_polygon_distance,source_footprints


def verify(R):
    G=Path(__file__).resolve().parent.parent;D=R/'stage332';start,cpu=time.perf_counter(),time.process_time();p=read(D/'plan.json');assert sha(D/'plan.json')==(D/'plan.sha256').read_text().strip()
    for f,h in p['source_hashes'].items():assert sha(f)==h,f
    for f,h in read(D/'build-private.json')['source_hashes'].items():assert sha(f)==h,f
    assert np.allclose(rotate([1.,0.],math.pi/2),[0.,1.],atol=1e-12)
    assert np.allclose(local(world([[2.,3.]],{'angle':.6,'position':[17.,-3.]}),{'angle':.6,'position':[17.,-3.]}),[[2.,3.]],atol=1e-12)
    square=np.array([[-1.,-1.],[1.,-1.],[1.,1.],[-1.,1.]])
    assert signed_polygon_distance([0.,0.],square)==-1. and signed_polygon_distance([3.,0.],square)==2.
    geometries=read(D/'geometry-private.json')['actual_precontact_geometries'];footprints=source_footprints(G/'core/vendor/car_dynamics.py');maximum_error=0.;queries=0
    for label in ['A','B']:
        replay=read(D/label/'saved-pixel-replay-private.json');source=[json.loads(s) for s in (R/'stage331'/label/'trace-private.jsonl').read_text().splitlines()]
        assert len(replay)==68 and [r['boundary'] for r in replay]==list(range(68))
        for index,item in enumerate(replay):
            assert item['response']['action']==source[index]['calculated330'];assert item['response']['features']==source[index]['features'];assert item['executed']==source[index]['executed']
        for expected in geometries[label]:
            snapshot=source[expected['boundary']]['pre_physical'];polygons=[world(p,snapshot['hull']) for p in footprints[0]]+[world(footprints[1],w['body']) for w in snapshot['wheels']]
            for obstacle in expected['obstacles']:
                spec=snapshot['obstacles'][obstacle['obstacle']];center=world(spec['fixture']['geometry']['pos'],spec['body']);radius=spec['fixture']['radius'];reference=[]
                for polygon in polygons:
                    shifted=polygon-center;got=-cv2.pointPolygonTest(np.asarray(shifted,np.float32),(0.,0.),True)-radius;actual=signed_polygon_distance(center,polygon)-radius
                    error=abs(got-actual);bound=8*np.finfo(np.float32).eps*max(1.,np.abs(shifted).max());assert error<=bound,(error,bound);maximum_error=max(maximum_error,error);queries+=1;reference.append(got)
                assert abs(min(reference[:4])-obstacle['hull_core_gap_m'])<=8*np.finfo(np.float32).eps*max(1.,np.abs(center).max())
                assert abs(min(reference[4:])-obstacle['wheel_core_gap_m'])<=8*np.finfo(np.float32).eps*max(1.,np.abs(center).max())
    latest=read(R/'project-effective-budget-v339.json');old=read(R/'project-effective-budget-v338.json')
    for key in ['actual_cumulative_wrapper_actions','research_remaining','final_reserved_actions','final_reserve_used','B_operating_cap']:assert latest[key]==old[key]
    assert latest['research_remaining']==71 and latest['final_reserved_actions']==84000 and latest['final_reserve_used']==0
    assert sum(json.loads(s).get('stage')==332 for s in (R/'experiment-cost-lines.jsonl').read_text().splitlines())==1
    for name in ['DEV','screen-opening.json','DEV-opened-by309.json']:assert not (R/'stage297'/name).exists()
    cost=read(D/'cost.json');assert cost['new_wrapper_actions']==cost['new_fits']==cost['new_source_physics_ticks']==0
    actor=read(D/'actor-cost.json');assert actor['saved_observation_actor_calls']==136 and all(r['process_reaped'] and r['actor_pids_absent'] for r in actor['reaping'])
    receipt=dict(passed=True,independent_OpenCV_polygon_distance_queries=queries,maximum_geometry_distance_error_m=maximum_error,coordinate_roundtrip_and_analytic_square_passed=True,
        stored_actor_input_action_feature_reproduction_count=136,source_hashes_unchanged=True,cost_ledger_stage332_entries=1,native_budget_unchanged=True,research_remaining=71,final_reserved_actions=84000,splits_unopened=True,
        new_native_actions=0,new_actor_calls=0,new_fits=0,new_source_physics_ticks=0,verification_wall_s=time.perf_counter()-start,verification_CPU_s=time.process_time()-cpu)
    save(D/'independent-verification.json',receipt);print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--private-root',required=True,type=Path);verify(p.parse_args().private_root)
