"""Small deterministic public-renderer geometry checks, without simulator state."""
import json
from pathlib import Path
import sys
import time
import cv2
import numpy as np
import pygame
from pygame import gfxdraw


def render(left,right,road=102,curb=None):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    def source(p):return ((p[0]+.5)*1000/84-.5,799.-((p[1]+.5)*800/84-.5))
    polygon=[source(p) for p in [left(-10),right(-10),right(90),left(90)]]
    gfxdraw.aapolygon(surface,polygon,(road,)*3);gfxdraw.filled_polygon(surface,polygon,(road,)*3)
    if curb is not None:
        border=[source(p) for p in [left(-10),(left(-10)[0]-1.8144,-10),
                                   (left(90)[0]-1.8144,90),left(90)]]
        gfxdraw.aapolygon(surface,border,curb);gfxdraw.filled_polygon(surface,border,curb)
    surface=pygame.transform.flip(surface,False,True)
    image=pygame.transform.smoothscale(surface,(96,96))
    image=np.transpose(np.array(pygame.surfarray.pixels3d(image)),(1,0,2))
    return cv2.cvtColor(cv2.resize(image,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255.


def main():
    start=time.perf_counter();cpu=time.process_time()
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
    from observation_agent import recover_pixel_edge
    output=Path('/workspace/haic-observation-link-private/raster-public-check-private.json')
    assert not output.exists(),'NO_REPEAT_PUBLIC_CHECK'
    records=[];blocked=np.zeros((84,84),bool)
    scenes=[(slope,phase,None) for slope in (0.,.5,-.75) for phase in (.15,.65)]
    scenes += [(0.,.35,(255,255,255)),(0.,.35,(255,0,0))]
    for scene,(slope,phase,curb) in enumerate(scenes):
        def left(y):return (25.+phase+slope*(y-35.),y)
        def right(y):return (left(y)[0]+22.,y)
        image=render(left,right,102 if scene%2==0 else 107,curb)
        mask=(image>.36)&(image<.47)
        for y in (20,40,50):
            edges=np.diff(np.pad(mask[y],(1,1)).astype(int));starts=np.flatnonzero(edges==1);ends=np.flatnonzero(edges==-1)
            j=int(np.argmax(ends-starts))
            for index,direction,actual in [(int(starts[j]),1,left(y)[0]),(int(ends[j]-1),-1,right(y)[0])]:
                refined=recover_pixel_edge(image,y,index,direction,blocked)
                estimate=float(index) if refined is None else refined
                inset_estimate=estimate+direction*.35*1.3608
                outward=max(0.,direction*(actual-inset_estimate))/1.3608
                records.append(dict(scene=scene,y=y,refined=refined is not None,
                    old_abs_error_px=abs(index-actual),new_abs_error_px=abs(estimate-actual),outward_after_inset_m=outward))
    unknown=np.ones((84,84),bool)
    assert recover_pixel_edge(image,40,25,1,unknown) is None
    assert recover_pixel_edge(image,60,25,1,blocked) is None
    assert recover_pixel_edge(image,40,1,1,blocked) is None
    q=dict(status='PASS',scenes=len(scenes),edges=len(records),refined_edges=sum(r['refined'] for r in records),
        old_MAE_px=float(np.mean([r['old_abs_error_px'] for r in records])),
        new_MAE_px=float(np.mean([r['new_abs_error_px'] for r in records])),
        max_outward_after_existing_inset_m=max(r['outward_after_inset_m'] for r in records),
        occluded_or_clipped_not_refined=True,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,
        native_actions=0,model_ticks=0,scope='Finite deterministic raster tests, not a validated universal uncertainty bound.',records=records)
    q['status']='PASS' if q['new_MAE_px']<q['old_MAE_px'] and q['max_outward_after_existing_inset_m']<=1e-9 else 'FAIL'
    output.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k!='records'},indent=2))
    assert q['status']=='PASS'


if __name__=='__main__':main()
