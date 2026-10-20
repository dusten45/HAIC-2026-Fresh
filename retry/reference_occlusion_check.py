"""Lane-centre geometry under an observed occluder stays collision-blocked."""
import json
from pathlib import Path
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'submit_core'))
import observation_agent as a


def check():
    cpu=time.process_time();yy,xx=np.indices((84,84))
    world_y=(a.IMAGE_ORIGIN_Y-yy)/1.701
    world_x=(xx-a.IMAGE_ORIGIN_X)/1.3608
    asphalt=(abs(world_x)<40/6).astype(np.uint8)
    blocked=(abs(world_x)<1.6)&(abs(world_y-10)<1.6)
    asphalt[blocked]=0
    raw=np.array([(0.,float(y))for y in range(-3,1)])
    curves=[dict(points=[(0.,float(y),float(y))for y in range(23)])]
    before_asphalt=asphalt.copy();before_blocked=blocked.copy()
    base,_=a.reference_from_observed_width(raw,curves,asphalt,blocked)
    patch=np.array([[-2.5,7.],[2.5,7.],[2.5,13.],[-2.5,13.]])
    extended,info=a.reference_from_observed_width(raw,curves,asphalt,blocked,
        road_occlusion_patches=[patch])
    assert max(base[:,1])<10<max(extended[:,1])
    assert max(extended[:,1])==22
    wrong=patch+np.array([10.,0.])
    rejected,_=a.reference_from_observed_width(raw,curves,asphalt,blocked,
        road_occlusion_patches=[wrong])
    assert np.array_equal(rejected,base)
    assert np.array_equal(asphalt,before_asphalt)and np.array_equal(blocked,before_blocked)
    footprint=a.core.rectangle((0.,10.),0.)
    assert a.core.obstacle_margin([footprint],[((0.,10.),1.6)])<0
    assert info['reference_current_road_occlusion_patches']==1
    return dict(status='PASS',baseline_endpoint=float(max(base[:,1])),
        conditional_geometric_endpoint=float(max(extended[:,1])),
        outside_patch_rejected=True,pixels_and_collision_mask_unchanged=True,
        occupied_footprint_collision_still_rejected=True,CPU_s=time.process_time()-cpu,
        model_ticks=0,native_actions=0,
        scope='Synthetic known road and explicit conditional patch. Runtime patches still require the existing CURRENT closed asphalt ring and material envelope; no collision-free claim.')


if __name__=='__main__':print(json.dumps(check()))
