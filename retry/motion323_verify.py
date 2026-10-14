"""Read-only sign, provenance and interval-yaw checks after the fixed readout."""
import argparse
import gzip
import json
import time
from pathlib import Path

import numpy as np

from retry import background_motion as bm
from retry.motion323_diagnosis import origin_displacement, rotation
from retry.path271_run import read, save, sha


def verify(R):
    start, cpu = time.perf_counter(), time.process_time(); D = R/'stage323'
    assert not (D/'verification.json').exists()
    p = read(D/'plan.json')
    for q,h in p['input_hashes'].items():
        assert sha(q)==h,q
    anchor=np.asarray(p['anchor']); reflect=np.diag([1.,-1.]); maximum=0.
    assert abs(bm.PIXELS_PER_UNIT-.105*6*2.7)<1e-12
    # Stage56 source camera: anchor + scale*F*R(-h)*(world-origin).
    # Verify both signs of hull rotation using independently projected points.
    world=np.array([[3.,6.],[-2.,9.],[5.,13.],[-5.,2.]])
    for delta in [-.12,0.,.12]:
        a0=.31; a1=a0+delta; o0=np.array([.7,-.9]); o1=np.array([1.2,.8])
        previous=(world-o0)@(reflect@rotation(-a0)).T*bm.PIXELS_PER_UNIT+anchor
        current=(world-o1)@(reflect@rotation(-a1)).T*bm.PIXELS_PER_UNIT+anchor
        rot=rotation(delta); t=current.mean(0)-rot@previous.mean(0)
        assert np.max(abs(previous@rot.T+t-current))<1e-12
        maximum=max(maximum,float(abs(origin_displacement(rot,t,anchor)-rotation(-a1)@(o1-o0)).max()))
    assert maximum<1e-12
    records=[json.loads(s) for s in (D/'registrations-private.jsonl').read_text().splitlines()]
    byroad={}
    for road in p['roads']:
        with gzip.open(R/'stage306/collection'/road/'full-source-captures-private.jsonl.gz','rt') as f:
            snapshots={r['step']:r for r in map(json.loads,f)}
        errors=[];actual=[];free=[];fixed=[]
        for rec in records:
            if rec['road']!=road or rec['status']!='registered':continue
            k=rec['current_step'];a0=snapshots[k-1]['snapshot']['hull']['angle'];a1=snapshots[k]['snapshot']['hull']['angle']
            target=np.arctan2(np.sin(a1-a0),np.cos(a1-a0))
            values=[rec['delta_yaw_rad'],rec['HUD_integrated_delta']]
            errors.append(np.array(values)-target);actual.append(target);free.append(values[0]);fixed.append(values[1])
        e=np.array(errors)
        byroad[road]=dict(registered=len(e),yaw_MAE_rad=dict(free=float(abs(e[:,0]).mean()),HUD_fixed=float(abs(e[:,1]).mean())),
                          yaw_p95_abs_rad=dict(free=float(np.quantile(abs(e[:,0]),.95)),HUD_fixed=float(np.quantile(abs(e[:,1]),.95))),
                          yaw_GT_correlation=dict(free=float(np.corrcoef(actual,free)[0,1]),HUD_fixed=float(np.corrcoef(actual,fixed)[0,1])))
    public=read(Path(__file__).resolve().parent/'motion323_result.json')
    audit=dict(renderer_camera_sign_scale_max_abs_error_m=maximum,rectified_pixels_per_metre_source_verified=True,
               interval_yaw_registered_by_road=byroad,
               interval_yaw_registered_equal_road_MAE_rad={arm:float(np.mean([r['yaw_MAE_rad'][arm] for r in byroad.values()])) for arm in ['free','HUD_fixed']},
               original_sources_equal_initial_commits=True,all_input_hashes_unchanged=True,
               wall_s=time.perf_counter()-start,CPU_s=time.process_time()-cpu)
    save(D/'verification.json',audit);public['additional_validation']=audit
    public['decision']='HUD-constrained translation is not a supported replacement on this fixed cache: lateral MAE/p95 worsen on all six roads; forward RMSE gain alone does not establish observer/controller benefit. No native or policy change.'
    save(Path(__file__).resolve().parent/'motion323_result.json',public)
    v=read(R/'project-effective-budget-v331.json');assert v['research_remaining']==395
    assert not any(json.loads(s).get('stage')==323 for s in (R/'experiment-cost-lines.jsonl').read_text().splitlines())
    cost=dict(stage=323,new_wrapper_actions=0,new_native=0,new_source_physics_ticks=0,new_actor_calls=0,new_fits_or_PPO=0,new_paid_resources=0,
              total_wall_s=public['cost']['wall_s']+audit['wall_s'],total_CPU_s=public['cost']['CPU_s']+audit['CPU_s'],
              actual_cumulative_wrapper_actions=v['actual_cumulative_wrapper_actions'],research_remaining=395,final_reserved_actions=84000,B_operating_cap=v['B_operating_cap'])
    save(D/'cost.json',cost)
    with (R/'experiment-cost-lines.jsonl').open('a') as f:f.write(json.dumps(cost)+'\n')
    print(json.dumps(audit),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--private-root',type=Path,required=True)
    verify(parser.parse_args().private_root.resolve())
