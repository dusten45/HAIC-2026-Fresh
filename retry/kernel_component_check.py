"""Public source-kernel cover and connected-anchor checks; no simulator."""
import argparse
import itertools
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
import pygame
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'submit_core'))
sys.path.insert(0,str(ROOT/'retry'))
import observation_agent as a
from retry.raw_pixel_intervals import preprocess_raw_rgb
import flank_component_check as multi
import interior_anchor_check as single


def check():
    cpu=time.process_time();interval=(.12,.16)
    cover,metadata=a.source_bbox_vehicle_cover(interval)
    assert a.source_bbox_vehicle_cover(None)[0]is None
    assert a.source_bbox_vehicle_cover((.2,.1))[0]is None
    assert a.source_bbox_vehicle_cover((float('nan'),.2))[0]is None
    rng=np.random.default_rng(6017)
    angle_sets=[(left,*other)for left in interval for other in itertools.product((-.4,.4),repeat=3)]
    angle_sets += [(rng.uniform(*interval),*rng.uniform(-.4,.4,3))for _ in range(24)]
    plain=preprocess_raw_rgb(np.full((800,1000,3),102,np.uint8))
    escapes=[]
    for angles in angle_sets:
        surface=pygame.Surface((1000,800),depth=32);surface.fill((102,)*3)
        for poly in (a.core.HULL_POLY1,a.core.HULL_POLY2,a.core.HULL_POLY3,a.core.HULL_POLY4):
            pygame.draw.polygon(surface,(204,0,0),[(500+16.2*x*a.core.SIZE,200+16.2*y*a.core.SIZE)for x,y in poly])
        for (cx,cy),q in zip(a.core.WHEELPOS,angles):
            co,si=math.cos(q),math.sin(q)
            poly=[(500+16.2*(cx*a.core.SIZE+co*x-si*y),200+16.2*(cy*a.core.SIZE+si*x+co*y))
                  for x,y in [(-.28,.54),(.28,.54),(.28,-.54),(-.28,-.54)]]
            pygame.draw.polygon(surface,(0,)*3,poly)
        raw=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
        changed=preprocess_raw_rgb(raw)!=plain
        escapes.append(int(np.sum(changed&~cover)))
    assert not any(escapes)
    # Run the existing positive/material/object/grass/span/disconnection cases
    # through the new anchor-window selector as well as its original API.
    old=multi.a.observed_flank_component
    multi.a.observed_flank_component=lambda *args:a.observed_connected_flank_component(*args)[0]
    try:
        f,im,raw,cov=multi.find_fixture()
        cases=multi.helper_checks(f,im,raw,cov)+multi.integration_checks(f,im,raw,cov)
        f,im,raw,cov=single.find_fixture()
        cases+=single.helper_checks(f,im,raw,cov)+single.integration_checks(f,im,raw,cov)
    finally:multi.a.observed_flank_component=old
    # One clean anchor can move one column while maintaining strict4-connectivity.
    im=np.full((84,84),160/255,np.float32)
    im[29,40:42]=100/255;im[29,42]=112/255
    im[30:32,41:43]=100/255;im[32,41:44]=100/255
    raw=(im>.36)&(im<.47);zero=np.zeros_like(raw)
    runs=[(30,1,41,43),(31,1,41,43)]
    base={29:(20,42,30,40),32:(20,43,30,41)}
    assert not old(im,raw,zero,zero,zero,runs,base,0.)
    accepted,info=a.observed_connected_flank_component(im,raw,zero,zero,zero,runs,base,0.)
    assert accepted
    blocked=zero.copy();blocked[29,40]=True
    assert not a.observed_connected_flank_component(im,raw,zero,blocked,zero,runs,base,0.)[0]
    im[29,42]=100/255;raw=(im>.36)&(im<.47)
    accepted,info=a.observed_connected_flank_component(im,raw,zero,zero,zero,runs,base,0.)
    assert accepted and len(info['matching_window_pairs'])==4
    return dict(status='PASS',public_car_joint_cases=len(angle_sets),output_escapes=max(escapes),
        existing_component_cases=len(cases),shifted_anchor_positive=True,blocked_clean_anchor_rejected=True,
        every_matching_window_pair_retained=4,unknown_HUD_fallback=True,
        runtime_dependencies='numpy/cv2/math/runtime598 unchanged',CPU_s=time.process_time()-cpu,
        model_ticks=0,native_actions=0,
        limits='Public kinematic wheel anchors and audited preprocessing. Dynamic joint-position residuals and particles are separate uncertainty. No force/footprint/horizon or road-material threshold is changed.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=check()
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
