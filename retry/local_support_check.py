"""Deterministic local-road inference checks and explicit negative examples."""
from pathlib import Path
import sys
import json
import time
import numpy as np
import cv2
from retry.raster_boundary_check import render


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
    from observation_agent import infer_local_road_support,vehicle_projection_mask,IMAGE_ORIGIN_X,IMAGE_ORIGIN_Y
    out=Path(sys.argv[1] if len(sys.argv)>1 else '/workspace/haic-observation-link-private/local-support-public-private.json');assert not out.exists()
    start=time.perf_counter();cpu=time.process_time();cover=vehicle_projection_mask(0.)
    opaque=cv2.erode(cover,np.ones((3,3),np.uint8),iterations=1)>0
    records=[]
    def evaluate(name,image,initial,truth_left,truth_right,obstacle=None,forbidden=None):
        image=image.copy();image[opaque]=61/255.
        asphalt=((image>.36)&(image<.47)).astype(np.uint8)
        blocked=np.zeros((84,84),bool) if obstacle is None else obstacle
        support,info=infer_local_road_support(image,asphalt,blocked,0.,initial,0.)
        yy,xx=np.nonzero(support);outside=sum(not truth_left(float(y))<=float(x)<=truth_right(float(y)) for y,x in zip(yy,xx))
        records.append(dict(name=name,inferred_pixels=int(support.sum()),outside_true_road_pixels=outside,
            spawn_prior_used=info['spawn_prior_used'],obstacle_pixels=int(np.sum((support>0)&blocked)),
            forbidden_pixels=0 if forbidden is None else int(np.sum((support>0)&forbidden)),
            hidden_obstacle_clearance_claim=info['occluded_obstacle_clearance_proved']))
        return support
    half=(40./6.)*1.3608
    left=lambda y:(IMAGE_ORIGIN_X-half,y);right=lambda y:(IMAGE_ORIGIN_X+half,y)
    image=render(left,right)
    evaluate('straight_spawn',image,True,lambda y:left(y)[0],lambda y:right(y)[0])
    image_curb=render(left,right,curb=(255,255,255))
    evaluate('painted_spawn',image_curb,True,lambda y:left(y)[0],lambda y:right(y)[0])
    slope=.6;half_tilt=half*np.sqrt(1+(slope*1.701/1.3608)**2)
    left_t=lambda y:(IMAGE_ORIGIN_X+1.+slope*(y-IMAGE_ORIGIN_Y)-half_tilt,y)
    right_t=lambda y:(left_t(y)[0]+2*half_tilt,y)
    tilted=render(left_t,right_t)
    evaluate('tilted_drive_not_spawn',tilted,False,lambda y:left_t(y)[0],lambda y:right_t(y)[0])
    evaluate('tilted_rejects_spawn_orientation',tilted,True,lambda y:left_t(y)[0],lambda y:right_t(y)[0])
    # A visible grass break extends beyond the opaque vehicle: never bridge it.
    broken=image.copy();broken[59:67,35:49]=162/255.
    forbidden=np.zeros((84,84),bool);forbidden[59:67,35:49]=True
    evaluate('grass_break_beyond_vehicle',broken,False,lambda y:left(y)[0],lambda y:right(y)[0],forbidden=forbidden)
    wide=render(lambda y:(12.,y),lambda y:(72.,y))
    evaluate('overwide_intersection',wide,False,lambda y:12.,lambda y:72.)
    abrupt=image.copy();abrupt[60:65]=np.roll(abrupt[60:65],7,axis=1)
    abrupt_band=np.zeros((84,84),bool);abrupt_band[60:65]=True
    evaluate('abrupt_curvature',abrupt,False,
        lambda y:left(y)[0]+(7 if 60<=y<65 else 0),
        lambda y:right(y)[0]+(7 if 60<=y<65 else 0),forbidden=abrupt_band)
    obstacle=np.zeros((84,84),bool);obstacle[60:65,39:45]=True
    evaluate('visible_obstacle_gap',image,True,lambda y:left(y)[0],lambda y:right(y)[0],obstacle)
    # Full public raster pipeline, with alternating curb tiles beside the car.
    # Their grey mixtures can be classified as asphalt outside the true edge.
    import pygame
    from pygame import gfxdraw
    for phase in (.2,.7):
        l=33.+phase;r=l+2*half
        surface=pygame.Surface((1000,800));surface.fill((102,204,102))
        def point(x,y):return ((x+.5)*1000/84-.5,799.-((y+.5)*800/84-.5))
        def draw(poly,color):
            poly=[point(x,y) for x,y in poly];gfxdraw.aapolygon(surface,poly,color);gfxdraw.filled_polygon(surface,poly,color)
        draw([(l,-10),(r,-10),(r,90),(l,90)],(102,)*3)
        step=(21./6.)*1.701;curb=(8./6.)*1.3608
        for i,y in enumerate(np.arange(-10,90,step)):
            draw([(l,y),(l-curb,y),(l-curb,y+step),(l,y+step)],(255,)*3 if i%2==0 else (255,0,0))
        surface=pygame.transform.flip(surface,False,True);surface=pygame.transform.smoothscale(surface,(96,96))
        image=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
        image=cv2.cvtColor(cv2.resize(image,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255.
        support=evaluate('mixed_curb_flanks_'+str(phase),image,False,lambda y:l,lambda y:r)
        assert support.any(),'MIXED_CURB_SUPPORT_MISSING'
    by={r['name']:r for r in records}
    assert by['straight_spawn']['inferred_pixels']>0 and by['painted_spawn']['inferred_pixels']>0
    assert by['tilted_drive_not_spawn']['inferred_pixels']>0 and not by['tilted_drive_not_spawn']['spawn_prior_used']
    for name in ['tilted_rejects_spawn_orientation','overwide_intersection']:
        assert by[name]['inferred_pixels']==0,name
    assert all(r['outside_true_road_pixels']==r['obstacle_pixels']==r['forbidden_pixels']==0 and not r['hidden_obstacle_clearance_claim'] for r in records)
    result=dict(status='PASS',records=records,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,native_actions=0,model_ticks=0,
        scope='Finite conditioning tests, not a universal safety certificate. Index-based obstacle exclusion is not spatial exclusion; inferred road support is not hidden-obstacle clearance.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
