"""Public source-car raster and exact preprocessing footprint diagnostics.
No world/model. Known kinematic body/wheel polygons only; no particle trails.
Empirical changed output pixels are not claimed a universal dependency proof.
"""
import argparse,json,math,sys,time
from pathlib import Path
import cv2,numpy as np,pygame
from retry.raw_pixel_intervals import preprocess_raw_rgb
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'submit_core'));import runtime598 as c
from observation_agent import vehicle_projection_mask


def car_polygons(joint):
    result=[[(x*c.SIZE,y*c.SIZE)for x,y in p]for p in(c.HULL_POLY1,c.HULL_POLY2,c.HULL_POLY3,c.HULL_POLY4)]
    for i,(x,y)in enumerate(c.WHEELPOS):
        q=joint if i<2 else 0.;co,si=math.cos(q),math.sin(q)
        result.append([(x*c.SIZE+co*dx-si*dy,y*c.SIZE+si*dx+co*dy)for dx,dy in[(-.28,.54),(.28,.54),(.28,-.54),(-.28,-.54)]])
    return result


def source_car(joint,background=(102,102,102),wheel_gray=0):
    surface=pygame.Surface((1000,800),depth=32);surface.fill(background)
    for i,poly in enumerate(car_polygons(joint)):
        points=[(500+16.2*x,200+16.2*y)for x,y in poly]
        pygame.draw.polygon(surface,(204,0,0)if i<4 else(wheel_gray,)*3,points)
    return np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))


def preprocessing_support_box(x,y,*,flip_y=True):
    """Pinned SSE area-read support enclosure, no output-pixel dilation.

    SSE shrink uses space=floor(16384*source/96). A96 sample reads integer
    source cells intersecting its fixed-point area. cv96->84 uses both positive
    neighbors: coordinate=(16*x+1)/14 has no integer/zero-coefficient case.
    Tiny contributions can vanish under uint8 arithmetic, so this is a safe
    dependency enclosure, not a claim every source pixel changes output.
    """
    if not 0<=x<84 or not 0<=y<84:raise ValueError('Outside84 grid')
    j=(16*x+1)//14;k=(16*y+1)//14
    xs=16384*1000//96;ys=16384*800//96
    left=j*xs//16384;right=((j+2)*xs+16383)//16384
    top=k*ys//16384;bottom=((k+2)*ys+16383)//16384
    return(left,800-bottom,right,800-top)if flip_y else(left,top,right,bottom)


def known_occlusion_veto(raw_source_mask,*,flip_y=True):
    """Union of source occluder geometry through audited kernel dependencies.

    raw_source_mask is preflip800x1000 bool, including all allowed geometry
    variants. Caller must handle joint/pose/center intervals and particles.
    """
    from retry.raw_pixel_intervals import audit_backend
    audit_backend();mask=np.asarray(raw_source_mask)
    if mask.shape!=(800,1000)or mask.dtype!=bool:raise ValueError('800x1000bool required')
    integral=np.pad(mask.astype(np.int64),((1,0),(1,0))).cumsum(axis=0).cumsum(axis=1);out=np.zeros((84,84),bool)
    for y in range(84):
        for x in range(84):
            left,top,right,bottom=preprocessing_support_box(x,y,flip_y=flip_y)
            out[y,x]=integral[bottom,right]-integral[top,right]-integral[bottom,left]+integral[top,left]>0
    return out


def obstacle_checks():
    from retry.raw_pixel_intervals import _polygon_masks
    from retry.raw_boundary_renderer import render_scene
    records=[]
    for phase in(0.,.25,.75):
        for angle in(0.,.3):
            cx,cy=620+phase*1000/84,430+phase*800/84
            vertices=[(int(cx+1.2*16.2*math.cos(angle+2*math.pi*i/16)),int(cy+1.2*16.2*math.sin(angle+2*math.pi*i/16)))for i in range(16)]
            _,source_mask=_polygon_masks(tuple(vertices));veto=known_occlusion_veto(source_mask)
            for road in(102,104,107):
                plain=render_scene([],background=(road,)*3)
                shown=render_scene([(vertices,(255,165,0))],background=(road,)*3)
                escape=(shown!=plain)&~veto;assert not np.any(escape)
                records.append(dict(phase=phase,angle=angle,road=road,changed_pixels=int(np.sum(shown!=plain)),kernel_veto_pixels=int(veto.sum()),outside_kernel_veto=int(escape.sum())))
    return records


def check(extra_joints=()):
    cpu=time.process_time();records=[]
    for joint in list((0.,.1,.2,.3))+list(extra_joints):
        mask=vehicle_projection_mask(joint).astype(bool)
        raw_car=source_car(joint,(255,255,255),0)
        source_mask=np.any(raw_car!=255,axis=2);kernel_mask=known_occlusion_veto(source_mask)
        kernel_escape=kernel_mask&~mask
        for color in(102,104,107):
            plain=preprocess_raw_rgb(np.full((800,1000,3),color,np.uint8))
            for wheel in(0,77):
                shown=preprocess_raw_rgb(source_car(joint,(color,)*3,wheel));changed=shown!=plain;outside=changed&~mask
                records.append(dict(joint=joint,source_road=color,wheel_gray=wheel,changed_pixels=int(changed.sum()),outside_existing_mask=int(outside.sum()),kernel_support_pixels=int(kernel_mask.sum()),kernel_support_outside_existing_mask=int(kernel_escape.sum()),outside_kernel_veto=int((changed&~kernel_mask).sum()),escaped_pixels=[dict(pixel=[int(x),int(y)],with_car=int(shown[y,x]),without_car=int(plain[y,x]))for y,x in np.argwhere(outside)]))
    assert all(r['outside_kernel_veto']==0 for r in records)
    objects=obstacle_checks()
    return dict(object_records=objects,status='PASS'if all(r['outside_existing_mask']==0 for r in records)else'ESCAPING_CAR_PIXELS_FOUND',records=records,CPU_s=time.process_time()-cpu,model_ticks=0,native=0,scope='Finite exact-color public car raster cases; known joint/ideal public kinematic wheel locations. Kernel-derived conservative veto also checked on18 known16gon object cases. Unknown dynamic pose/joint interval, HUD and skid particles not covered; dependency masks need the union of all allowed source geometries.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output');args=parser.parse_args();result=check()
    if args.output:Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items()if k!='records'}))
