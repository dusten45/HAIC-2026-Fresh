"""Public-renderer regression of full center-cell collision coverage.

Uses constructed scenes, never a simulator or a hidden evaluation state.
These finite checks supplement the unclipped SDL_gfx/SSE source derivation.
"""
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from retry.object_occlusion_check import a, scene


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time()
    cases=[]
    for shade in (102,107):
        for phase in (0.,.25,.5,.75):
            for angle in np.arange(8)*math.pi/64:
                cases.append((shade,phase,float(angle),0.,0.,True))
    rng=np.random.default_rng(381)
    for _ in range(32):
        cases.append((int(rng.choice([102,104,107])),float(rng.uniform(0,1)),
            float(rng.uniform(0,math.pi/8)),float(rng.uniform(-3,3)),
            float(rng.uniform(-.12,.12)),False))
    accepted=0;worst=-float('inf');records=[]
    for shade,phase,angle,offset,road_angle,required in cases:
        image,_,_=scene(shade,phase,angle,offset=offset,road_angle=road_angle)
        true_center=np.array([offset+phase,16.+phase*.5])
        detections,_=a.detect_observed_obstacles(image)
        result=a.observed_object_road_patch(image,detections[0][0],0.) if len(detections)==1 else None
        assert not required or result is not None,'SUPPORTED_OBJECT_REJECTED'
        if result is None:
            records.append(dict(accepted=False));continue
        accepted+=1;_,_,info=result;disks=info['collision_cell_disks']
        centers=np.array([p for p,r in disks]);radii=np.array([r for p,r in disks])
        # The actual center must lie in a retained FULL square, rather than
        # merely near a selected fit or in the old coarse bounding ball.
        halfside=float(radii[0]-a.OBJECT_RADIUS)/math.sqrt(2)
        assert np.any(np.max(abs(centers-true_center),axis=1)<=halfside+1e-9),'TRUE_CENTER_CELL_EXCLUDED'
        excess=float(np.min(np.linalg.norm(centers-true_center,axis=1)+a.OBJECT_RADIUS-radii))
        assert excess<=1e-9,'PHYSICAL_CIRCLE_NOT_COVERED'
        worst=max(worst,excess)
        records.append(dict(accepted=True,cells=len(disks),circle_cover_excess_m=excess))
    guards=[]
    for material in ('grass','bright_grass','white','opaque'):
        image,_,_=scene(102,.25,0.,material=material)
        guards.append(a.observed_object_road_patch(image,(.25,16.125),0.) is None)
    for offset in (-6.,6.):
        image,_,_=scene(102,.25,0.,offset=offset)
        guards.append(a.observed_object_road_patch(image,(offset+.25,16.125),0.) is None)
    blank=np.full((84,84),102/255.,np.float32)
    guards.append(a.observed_object_road_patch(blank,(0.,16.),0.) is None)
    image,_,_=scene(102,.25,0.);image[35:39,40:44]=0.
    guards.append(a.observed_object_road_patch(image,(.25,16.125),0.) is None)
    assert all(guards)
    result=dict(status='PASS',cases=len(cases),accepted=accepted,
        full_true_center_cell_checks=accepted,negative_guards=len(guards),
        max_circle_cover_excess_m=worst,source_error_m=a.OBJECT_SOURCE_ERROR_M,
        records=records,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,
        limitation='Finite public renderer checks; existing arithmetic +/-3gray and closed asphalt-ring continuity assumptions remain.')
    out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
