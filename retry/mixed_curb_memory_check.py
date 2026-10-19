"""Finite public paint/raster and observed-evidence transport checks."""
from pathlib import Path
import sys
import json
import time
import math
import numpy as np
import cv2
import pygame
from pygame import gfxdraw


def curb_image(slope,phase,paint,junction=False):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    def left(y):return 27.+phase+slope*(y-35.)
    def point(x,y):return ((x+.5)*1000/84-.5,799.-((y+.5)*800/84-.5))
    road=[point(left(y)+dx,y) for dx,y in [(0,-10),(22,-10),(22,90),(0,90)]]
    gfxdraw.aapolygon(surface,road,(102,)*3);gfxdraw.filled_polygon(surface,road,(102,)*3)
    width=(8./6.)*1.3608*math.sqrt(1+(slope*1.701/1.3608)**2)
    pieces=[(-10,35,paint),(35,90,(255,0,0) if paint==(255,)*3 else (255,)*3)] if junction else [(-10,90,paint)]
    for low,high,color in pieces:
        poly=[point(left(y)+dx,y) for dx,y in [(0,low),(-width,low),(-width,high),(0,high)]]
        gfxdraw.aapolygon(surface,poly,color);gfxdraw.filled_polygon(surface,poly,color)
    surface=pygame.transform.flip(surface,False,True);surface=pygame.transform.smoothscale(surface,(96,96))
    image=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    return cv2.cvtColor(cv2.resize(image,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255.,left


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
    from observation_agent import recover_curb_edge,transport_road_evidence
    out=Path(sys.argv[1] if len(sys.argv)>1 else '/workspace/haic-observation-link-private/mixed-curb-memory-public-private.json');assert not out.exists()
    start=time.perf_counter();cpu=time.process_time();records=[];blocked=np.zeros((84,84),bool)
    for slope in (0.,.5,-.75):
        for phase in (.15,.65):
            for paint in [(255,)*3,(255,0,0)]:
                image,left=curb_image(slope,phase,paint)
                for y in (20,40,50):
                    mask=(image[y]>.36)&(image[y]<.47);d=np.diff(np.pad(mask,(1,1)).astype(int));s=np.flatnonzero(d==1);e=np.flatnonzero(d==-1);i=int(np.argmax(e-s));index=int(s[i])
                    edge=recover_curb_edge(image,y,index,1,slope,blocked);estimate=index if edge is None else edge
                    records.append(dict(refined=edge is not None,old_error_px=abs(index-left(y)),
                        new_error_px=abs(estimate-left(y)),outward_after_inset_m=max(0.,left(y)-(estimate+.35*1.3608))/1.3608))
    image,left=curb_image(0.,.35,(255,)*3,True);junction=[]
    for y in (34,35,36):
        mask=(image[y]>.36)&(image[y]<.47);index=int(np.flatnonzero(mask)[0]);edge=recover_curb_edge(image,y,index,1,0.,blocked)
        junction.append(dict(refined=edge is not None,outward_after_inset_m=0. if edge is None else max(0.,left(y)-edge-.35*1.3608)/1.3608))
    # Known synthetic road and texture; fixed opaque car is overlaid only after
    # moving the world. The transport routine sees pixels, not the road truth.
    yy,xx=np.indices((84,84));checker=((xx//7+yy//9)%2).astype(np.uint8)
    base=np.where(checker,177,162).astype(np.float32)/255.
    truth=np.zeros((84,84),np.uint8);truth[:,24:60]=1
    base[truth>0]=(102+((xx[truth>0]//6+yy[truth>0]//8)%3)*2).astype(np.float32)/255.
    frames=[]
    for i in range(8):
        transform=np.array([[1.,0.,.25*i],[0.,1.,4.*i]],np.float32)
        image=cv2.warpAffine(base,transform,(84,84),borderValue=162/255.)
        image[55:70,34:51]=0.;frames.append(image)
    evidence,temporal=transport_road_evidence(frames)
    actual=cv2.warpAffine(truth.astype(np.float32),transform,(84,84),borderValue=0)
    false_pixels=int(np.sum((evidence>0)&(actual<.999)))
    tiled,tiled_info=transport_road_evidence([frames[0]]*4)
    failed,failed_info=transport_road_evidence([frames[0],np.zeros((84,84),np.float32)])
    result=dict(status='PASS',edge_tests=len(records),curb_refined=sum(r['refined'] for r in records),
        old_MAE_px=float(np.mean([r['old_error_px'] for r in records])),new_MAE_px=float(np.mean([r['new_error_px'] for r in records])),
        max_outward_after_inset_m=max(r['outward_after_inset_m'] for r in records+junction),
        paint_junction=junction,transport=temporal,transport_outside_known_road_pixels=false_pixels,
        tiled_reset_pixels=int(np.sum(tiled)),tiled_unique_frames=tiled_info['unique_frames'],
        failed_registration_pixels=int(np.sum(failed)),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,
        native_actions=0,model_ticks=0,scope='Finite practical tests, not universal observation-error or safety bounds.',records=records)
    ok=result['curb_refined']>0 and result['new_MAE_px']<result['old_MAE_px'] and result['max_outward_after_inset_m']<=1e-9
    ok &= temporal['registered_pairs']>0 and temporal['transported_vehicle_pixels']>0 and false_pixels==0
    ok &= result['tiled_reset_pixels']==0 and result['tiled_unique_frames']==1 and result['failed_registration_pixels']==0
    result['status']='PASS' if ok else 'FAIL';out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2));assert ok


if __name__=='__main__':main()
