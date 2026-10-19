"""Finite public-raster mesh risk checks, including a concave visible corner."""
from pathlib import Path
import sys
import json
import time
import numpy as np
import cv2
import pygame
from pygame import gfxdraw
from retry.raster_boundary_check import render


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
    from observation_agent import Agent,IMAGE_ORIGIN_X,IMAGE_ORIGIN_Y
    import runtime598 as core
    output=Path(sys.argv[1] if len(sys.argv)>1 else '/workspace/haic-observation-link-private/raster-mesh-check-private.json');assert not output.exists()
    cpu=time.process_time();start=time.perf_counter();records=[]
    cases=[]
    for slope,phase in [(0.,.15),(.5,.65),(-.75,.15)]:
        left=lambda y,s=slope,p=phase:(25.+p+s*(y-35),y)
        right=lambda y,f=left:(f(y)[0]+22.,y)
        poly=[left(-10),right(-10),right(90),left(90)]
        cases.append((render(left,right),[poly]))
    # A road union with a concave corner. No pixels behind objects are supplied.
    polys=[[(30.,40.),(52.,40.),(52.,90.),(30.,90.)],
           [(5.,15.),(52.,15.),(52.,40.),(5.,40.)]]
    surf=pygame.Surface((1000,800));surf.fill((102,204,102))
    for poly in polys:
        vertices=[((x+.5)*1000/84-.5,799.-((y+.5)*800/84-.5)) for x,y in poly]
        gfxdraw.aapolygon(surf,vertices,(102,)*3);gfxdraw.filled_polygon(surf,vertices,(102,)*3)
    surf=pygame.transform.flip(surf,False,True);surf=pygame.transform.smoothscale(surf,(96,96))
    im=np.transpose(np.array(pygame.surfarray.pixels3d(surf)),(1,0,2))
    cases.append((cv2.cvtColor(cv2.resize(im,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255.,polys))
    for i,(image,truth) in enumerate(cases):
        agent=Agent()
        try:scene,_,_,_=agent._map(image)
        except RuntimeError as exc:
            records.append(dict(scene=i,status='UNSUPPORTED',reason=str(exc)));continue
        assert len(scene.boundary)==2*len(scene.roads)+2,'MESH_BOUNDARY_COUNT'
        outside=0;samples=0
        for poly,coefficient in scene.roads:
            for u in np.linspace(0.,1.,5):
                for v in np.linspace(0.,1.,5):
                    point=tuple((1-v)*((1-u)*poly[0][j]+u*poly[1][j])+v*((1-u)*poly[3][j]+u*poly[2][j]) for j in range(2))
                    pixel=(IMAGE_ORIGIN_X+1.3608*point[0],IMAGE_ORIGIN_Y-1.701*point[1])
                    samples+=1;outside+=not any(core.inside(pixel,p) for p in truth)
        records.append(dict(scene=i,status='PASS' if outside==0 else 'FAIL',mesh_samples=samples,outside_true_road=outside,road_cells=len(scene.roads)))
    result=dict(status='PASS' if all(r['status']!='FAIL' for r in records) else 'FAIL',
        records=records,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,
        native_actions=0,model_ticks=0,scope='Finite synthetic risk checks only; no universal safety bound.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['status']=='PASS'


if __name__=='__main__':main()
