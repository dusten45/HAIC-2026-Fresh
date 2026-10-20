"""Source-raster outer bounds for uncertain public regular16-gons.

All integer endpoint pairs in supplied vertex boxes are retained. AA support
is drawn using the actual binding (both extreme directions detect alpha1).
Certain polygon fill uses the pinned SDL_gfx fixedpoint scanline formula,
requiring every edge's crossing parity to agree across every endpoint pair.
No guessed grayscale tolerance or selected best-fit center is used.
"""
import itertools
import math
import numpy as np
import pygame
from pygame import gfxdraw


def _trig_bounds(lo,hi,kind):
    fn=math.cos if kind=='cos' else math.sin
    critical=0. if kind=='cos' else math.pi/2
    points=[lo,hi]
    points += [critical+k*math.pi for k in range(math.ceil((lo-critical)/math.pi),math.floor((hi-critical)/math.pi)+1)]
    values=[fn(v)for v in points]
    # Numerical engineering enclosure of libm roots, not a libm proof.
    return min(values)-1e-14,max(values)+1e-14


def integer_vertex_boxes(center_box,phase_box,radius=float(np.float32(1.2))*16.2,sides=16):
    """Integer source vertex boxes for all centers/phases in the input box.

    center_box=((xmin,xmax),(ymin,ymax)), all BEFORE official vertical flip.
    Default radius includes the public Box2D float32 fixture radius. A1e-14
    trig endpoint expansion covers numerical root noise in this audited
    engineering use; this is not a general transcendental interval library.
    """
    boxes=[]
    for j in range(sides):
        angle=j*2*math.pi/sides
        intervals=[]
        for axis,kind in enumerate(('cos','sin')):
            lo,hi=_trig_bounds(phase_box[0]+angle,phase_box[1]+angle,kind)
            a=center_box[axis][0]+radius*lo;b=center_box[axis][1]+radius*hi
            intervals.append((math.trunc(a),math.trunc(b)))
        boxes.append(tuple(intervals))
    return tuple(boxes)


def endpoint_pairs(box):
    return tuple(itertools.product(range(box[0][0],box[0][1]+1),range(box[1][0],box[1][1]+1)))


def source_masks(vertex_boxes,max_edge_pairs=20000):
    """Return certainfill, possibleAAorfill for all supplied integer vertices.

    Maxy scanline special case is deliberately unknown. Source coordinates
    must lie strictly inside the canvas so line clipping adds no uncertainty.
    Certain parity classification leaves a halfpixel fixedpoint margin.
    """
    corners=[endpoint_pairs(b)for b in vertex_boxes]
    if any(not q for q in corners):raise ValueError('Empty vertex range')
    points=np.array([p for ps in corners for p in ps]);xmin,ymin=points.min(axis=0);xmax,ymax=points.max(axis=0)
    if not(1<=xmin<=xmax<=998 and 1<=ymin<=ymax<=798):raise ValueError('Unclipped source geometry required')
    area=np.s_[max(0,ymin-1):min(800,ymax+2),max(0,xmin-1):min(1000,xmax+2)]
    ys=np.arange(max(0,ymin-1),min(800,ymax+2));xs=np.arange(max(0,xmin-1),min(1000,xmax+2))
    yy=ys[:,None];xx=xs[None,:]*65536
    known=np.ones((len(ys),len(xs)),bool);parity=np.zeros_like(known)
    low_surface=pygame.Surface((1000,800),depth=32);low_surface.fill((0,)*3)
    high_surface=pygame.Surface((1000,800),depth=32);high_surface.fill((255,)*3)
    count=0
    for p,q in zip(corners[-1:]+corners[:-1],corners):
        pairs=list(itertools.product(p,q));count+=len(pairs)
        if len(pairs)>max_edge_pairs:raise ValueError('Edge endpoint enumeration cap')
        minimum=np.full(len(ys),np.iinfo(np.int64).max,dtype=np.int64)
        maximum=np.full(len(ys),np.iinfo(np.int64).min,dtype=np.int64)
        active_count=np.zeros(len(ys),int)
        for a,b in pairs:
            # Degenerate3vertex polygon executes the same _aalineColor path
            # as a real polygon edge; reverse/zero edges only widen support.
            gfxdraw.aapolygon(low_surface,(a,b,b),(255,)*3)
            gfxdraw.aapolygon(high_surface,(a,b,b),(0,)*3)
            x1,y1=a;x2,y2=b
            if y1==y2:continue
            if y1>y2:x1,x2=x2,x1;y1,y2=y2,y1
            active=(ys>=y1)&(ys<y2)
            # Active numerator is nonnegative, so Python// equals C integer /.
            value=((65536*(ys[active]-y1))//(y2-y1))*(x2-x1)+65536*x1
            minimum[active]=np.minimum(minimum[active],value)
            maximum[active]=np.maximum(maximum[active],value)
            active_count[active]+=1
        always=(active_count[:,None]==len(pairs))&(maximum[:,None]<xx-32769)
        never=(active_count[:,None]==0)|(minimum[:,None]>xx+32769)
        known &=always|never;parity ^=always
    min_max_y=max(b[1][0]for b in vertex_boxes)
    special=ys>=min_max_y
    known[special,:]=False
    certain=known&parity
    possible=(~known)|parity
    # Fill scanning cannot leave extrema by >=1sourcepixel in these small
    # polygons. Enforce this precondition rather than assume integer overflow.
    if xmax-xmin>=65534:raise ValueError('Fixedpoint intersection drift cap')
    possible &= (yy>=ymin)&(yy<=ymax)&(xs[None,:]>=xmin-1)&(xs[None,:]<=xmax+1)
    white=np.transpose(np.array(pygame.surfarray.pixels3d(low_surface)),(1,0,2))[:,:,0]
    black=np.transpose(np.array(pygame.surfarray.pixels3d(high_surface)),(1,0,2))[:,:,0]
    affect=(white!=0)|(black!=255)
    possible_full=affect.copy();possible_full[area]|=possible
    certain_full=np.zeros((800,1000),bool);certain_full[area]=certain
    return certain_full,possible_full,count


def raw_enclosure(vertex_boxes,background_bounds=((102,)*3,(107,)*3),color=(255,165,0)):
    certain,possible,count=source_masks(vertex_boxes)
    lo=np.empty((800,1000,3),np.uint8);hi=np.empty_like(lo)
    lo[:]=background_bounds[0];hi[:]=background_bounds[1]
    lo[possible]=np.minimum(lo[possible],color);hi[possible]=np.maximum(hi[possible],color)
    lo[certain]=color;hi[certain]=color
    return lo,hi,dict(endpoint_pairs=count,certain_fill_pixels=int(certain.sum()),possible_pixels=int(possible.sum()))


def check():
    """Check independent vertex choices against actual AA+fill and pipeline."""
    import time
    from retry.raw_pixel_intervals import forward_enclosure,preprocess_raw_rgb
    cpu=time.process_time();rng=np.random.default_rng(381);count=0
    for width,phase_width in ((.03,.001),(.75,.02),(1.3,.04)):
        boxes=integer_vertex_boxes(((500-width,500+width),(400-width,400+width)),(.17-phase_width,.17+phase_width))
        lo,hi,_=raw_enclosure(boxes);flo,fhi=forward_enclosure(lo,hi)
        for _ in range(32):
            vertices=tuple(tuple(int(rng.integers(a,b+1))for a,b in box)for box in boxes)
            surface=pygame.Surface((1000,800),depth=32)
            surface.fill((int(rng.integers(102,108)),)*3)
            gfxdraw.aapolygon(surface,vertices,(255,165,0));gfxdraw.filled_polygon(surface,vertices,(255,165,0))
            raw=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
            assert np.all(raw>=lo)and np.all(raw<=hi)
            gray=preprocess_raw_rgb(raw)
            assert np.all(gray>=flo)and np.all(gray<=fhi)
            count+=1
    return dict(status='PASS',independent_integer_vertex_cases=count,
                source_and_pipeline_inclusion=True,CPU_s=time.process_time()-cpu,
                model_ticks=0,native_actions=0,gray_tolerance=0,
                premise='Source integer vertexboxes and ordinaryasphaltRGB102..107; float/libm interval is engineering.')


if __name__=='__main__':
    import json
    print(json.dumps(check()))
