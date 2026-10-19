"""External polygon-margin error decomposition; never loads truth into Agent."""
from pathlib import Path
import json
import sys
import time


def physical_decomposition():
    """True geometry is an external evaluation target, never an Agent input."""
    import math
    import numpy as np
    import cv2
    import pygame
    from pygame import gfxdraw
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
    import runtime598 as core
    from observation_agent import IMAGE_ORIGIN_X,IMAGE_ORIGIN_Y
    parent=Path('/workspace/haic-observation-link-private')
    source=Path('/workspace/haic-submission-private/runtime598-state-corrected-continuous01')
    output=parent/'raster-physical-decomposition-private.json';assert not output.exists()
    load=lambda p:json.loads(p.read_text())
    inputs=load(parent/'input-attribution40/inputs-private.json');old=load(source/'checkpoint-private.json')
    events=load(source/'geometry-probe-private.json')
    target=load(parent/'input-attribution40/result-private.json')['failed_polygon_margin_comparison']
    start=time.perf_counter();cpu=time.process_time();surface=pygame.Surface((1000,800));surface.fill((0,0,0))
    for poly,coefficient in inputs['roads']:
        # Same public projection/flip/smoothscale/resize, monochrome physical
        # road occupancy only: paint/grass/occluders are intentionally excluded.
        vertices=[(500.+16.2*x,200.+16.2*y) for x,y in poly]
        gfxdraw.aapolygon(surface,vertices,(255,)*3);gfxdraw.filled_polygon(surface,vertices,(255,)*3)
    surface=pygame.transform.flip(surface,False,True);small=pygame.transform.smoothscale(surface,(96,96))
    image=np.transpose(np.array(pygame.surfarray.pixels3d(small)),(1,0,2))
    binary=cv2.cvtColor(cv2.resize(image,(84,84)),cv2.COLOR_RGB2GRAY).astype(float)/255.
    n=(len(old['boundary'])-2)//2
    left=[old['boundary'][0][0]]+[p[1] for p in old['boundary'][:n]]
    right=[old['boundary'][n][0]]+[p[1] for p in old['boundary'][n:2*n]]
    exact_rows=[];raster_rows=[];actual_rows=[];inset_rows=[]
    for (lx,y),(rx,_) in zip(left,right):
        anchor=(lx+rx)/2;intervals=[]
        for poly,coefficient in inputs['roads']:
            xs=[]
            for a,b in zip(poly,poly[1:]+poly[:1]):
                if min(a[1],b[1])<=y<max(a[1],b[1]):xs.append(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]))
            if len(xs)>=2:intervals.append((min(xs),max(xs)))
        intervals.sort();merged=[]
        for a,b in intervals:
            if merged and a<=merged[-1][1]+1e-9:merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
            else:merged.append((a,b))
        a,b=min(merged,key=lambda p:max(p[0]-anchor,0.,anchor-p[1]))
        exact_rows.append((a,b,y))
        py=int(round(IMAGE_ORIGIN_Y-1.701*y));mask=binary[py]>=.5
        d=np.diff(np.pad(mask,(1,1)).astype(int));starts=np.flatnonzero(d==1);ends=np.flatnonzero(d==-1)
        choices=[((s-IMAGE_ORIGIN_X)/1.3608,(e-1-IMAGE_ORIGIN_X)/1.3608) for s,e in zip(starts,ends)]
        a,b=min(choices,key=lambda p:max(p[0]-anchor,0.,anchor-p[1]))
        raster_rows.append((a,b,y));actual_rows.append((lx-.35,rx+.35,y));inset_rows.append((lx,rx,y))
    def geometry(rows):
        l=[(a,y) for a,b,y in rows];r=[(b,y) for a,b,y in rows]
        return ([(l[i],r[i],r[i+1],l[i+1]) for i in range(len(l)-1)],
                list(zip(l,l[1:]))+list(zip(r,r[1:]))+[(l[0],r[0]),(l[-1],r[-1])])
    variants={name:geometry(rows) for name,rows in [('oracle_rows',exact_rows),('binary_raster_rows',raster_rows),('observed_color_rows',actual_rows),('inset_rows',inset_rows)]}
    def margin(poly,data):
        roads,edges=data;dist=min(core.polygon_distance(poly,e) for e in edges)
        return dist if all(any(core.inside(v,p) for p in roads) for v in poly) else -dist
    rows=[]
    for event,t in zip(events,target):
        m={name:margin(event['polygon'],data) for name,data in variants.items()}
        row=dict(row_mesh_error=t['true_road_margin']-m['oracle_rows'],
                 resampling_and_pixel_center_error=m['oracle_rows']-m['binary_raster_rows'],
                 color_classification_error=m['binary_raster_rows']-m['observed_color_rows'],
                 inset_effect=m['observed_color_rows']-m['inset_rows'])
        assert abs(sum(row.values())-(t['true_road_margin']-event['road_margin']))<1e-10
        rows.append(row)
    summary={}
    for name in rows[0]:
        v=[r[name] for r in rows];summary[name]=dict(min_m=min(v),max_m=max(v),mean_m=sum(v)/len(v))
    result=dict(summary=summary,rows=rows,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,
        model_ticks=0,native_actions=0,scope='Exact telescoping, order-specific decomposition on fixed failure polygons. Binary0.5 is diagnostic occupancy only, not Agent threshold or safety gate. True map never enters Agent.')
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))


def main():
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
    import runtime598 as core
    start=time.perf_counter();cpu=time.process_time()
    source=Path('/workspace/haic-submission-private/runtime598-state-corrected-continuous01')
    parent=Path('/workspace/haic-observation-link-private')
    output=parent/'raster-error-decomposition-private.json';assert not output.exists()
    load=lambda p:json.loads(p.read_text())
    old=load(source/'checkpoint-private.json')
    new=load(parent/'raster-refined-cache02/estimated-input-private.json')
    events=load(source/'geometry-probe-private.json')
    true=load(parent/'input-attribution40/result-private.json')['failed_polygon_margin_comparison']
    def sides(boundary):
        n=(len(boundary)-2)//2
        return ([boundary[0][0]]+[e[1] for e in boundary[:n]],
                [boundary[n][0]]+[e[1] for e in boundary[n:2*n]])
    def scene(left,right,remove_inset=False):
        left=[(x-(.35 if remove_inset else 0.),y) for x,y in left]
        right=[(x+(.35 if remove_inset else 0.),y) for x,y in right]
        roads=[((left[i],right[i],right[i+1],left[i+1]),1.) for i in range(len(left)-1)]
        edges=list(zip(left,left[1:]))+list(zip(right,right[1:]))+[(left[0],right[0]),(left[-1],right[-1])]
        return roads,edges
    left,right=sides(old['boundary']);nl,nr=sides(new['boundary'])
    variants={'old_with_inset':scene(left,right),'old_no_inset':scene(left,right,True),
              'subpixel_coarse_no_inset':scene(nl[::2],nr[::2],True),
              'subpixel_dense_no_inset':scene(nl,nr,True),'subpixel_dense_with_inset':scene(nl,nr)}
    def margin(poly,data):
        roads,edges=data;distance=min(core.polygon_distance(poly,e) for e in edges)
        covered=all(any(core.inside(v,p) for p,coefficient in roads) for v in poly)
        return distance if covered else -distance
    rows=[]
    for event,t in zip(events,true):
        values={name:margin(event['polygon'],data) for name,data in variants.items()}
        assert abs(values['old_with_inset']-event['road_margin'])<1e-12
        rows.append(dict(values=values,true_margin=t['true_road_margin'],
            inset_contribution=values['old_no_inset']-values['old_with_inset'],
            subpixel_contribution=values['subpixel_coarse_no_inset']-values['old_no_inset'],
            row_mesh_contribution=values['subpixel_dense_no_inset']-values['subpixel_coarse_no_inset'],
            residual_after_no_inset_refinement=t['true_road_margin']-values['subpixel_dense_no_inset']))
    summary={}
    for name in ['inset_contribution','subpixel_contribution','row_mesh_contribution','residual_after_no_inset_refinement']:
        values=[r[name] for r in rows];summary[name]=dict(min_m=min(values),max_m=max(values),mean_m=sum(values)/len(values))
    q=dict(polygon_count=len(rows),summary=summary,rows=rows,
        CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start,native_actions=0,model_ticks=0,
        scope='Order-specific diagnostic ablation; no-inset variants are never Agent code. These are former failure polygons, not a new controller rollout.')
    output.write_text(json.dumps(q,indent=2)+'\n');print(json.dumps({k:v for k,v in q.items() if k!='rows'},indent=2))


if __name__=='__main__':
    if '--physical' in sys.argv:physical_decomposition()
    else:main()
