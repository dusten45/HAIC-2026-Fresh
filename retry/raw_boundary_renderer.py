"""Finite exact public polygon raster hypotheses, without an environment.

Coverage applies ONLY to bounded ORIGINAL polygon vertex coordinates and a
complete ordered layer model. Cutting a long edge at a local ROI changes its
endpoints and is not certified raster-equivalent. Unknown corners, tile seams,
paint or grass checkerboard must remain unknown nuisance geometry.

pygame2.6.1 src_c/gfxdraw.c Sint16FromObj uses PyNumber_Long then Sint16;
polygon AA and fill both use it. https://github.com/pygame/pygame/blob/2.6.1/src_c/gfxdraw.c
"""
from itertools import product
import argparse
import hashlib
import json
import math
from pathlib import Path
import time
import cv2
import numpy as np
import pygame
from pygame import gfxdraw

ROAD_RGB=((102,102,102),(104,104,104),(107,107,107))
GRASS_RGB=((102,204,102),(102,230,102))
PAINT_RGB=((255,0,0),(255,255,255))


def truncate_vertex(vertex):
    result=[]
    for value in vertex:
        value=float(value)
        if not math.isfinite(value) or not -32768<=value<=32767:
            raise ValueError('Finite Sint16-safe original vertices required')
        result.append(math.trunc(value))
    if len(result)!=2:raise ValueError('Two coordinates required')
    return tuple(result)


def coordinate_cell(integer):
    """Exact real-coordinate preimage of truncation, before input intersection."""
    if integer>0:return dict(lower=integer,upper=integer+1,lower_closed=True,upper_closed=False)
    if integer<0:return dict(lower=integer-1,upper=integer,lower_closed=False,upper_closed=True)
    return dict(lower=-1,upper=1,lower_closed=False,upper_closed=False)


def integer_vertex_count(vertex_boxes):
    count=1
    for box in vertex_boxes:
        if len(box)!=2:raise ValueError('Each vertex needs x/y intervals')
        for lower,upper in box:
            if not all(map(math.isfinite,(lower,upper)))or lower>upper or lower< -32768 or upper>32767:
                raise ValueError('Closed finite Sint16-safe coordinate intervals required')
            count*=math.trunc(upper)-math.trunc(lower)+1
    return count


def enumerate_vertex_cells(vertex_boxes,max_candidates=10000):
    """Every integer polygon from closed ORIGINAL-coordinate boxes, exactly.

    Returns an overapproximation if callers additionally require line/width
    correlations. Such extra correlations can remove candidates, not add any.
    No subpixel grid approximation or gray tolerance is involved.
    """
    count=integer_vertex_count(vertex_boxes)
    if count>max_candidates:raise ValueError(f'Candidate cap: {count}>{max_candidates}')
    ranges=[range(math.trunc(lo),math.trunc(hi)+1)for box in vertex_boxes for lo,hi in box]
    for values in product(*ranges):
        vertices=tuple(zip(values[::2],values[1::2]))
        yield dict(integer_vertices=vertices,
            original_coordinate_cells=[(coordinate_cell(x),coordinate_cell(y))for x,y in vertices],
            input_vertex_intervals=vertex_boxes,
            coverage='COMPLETE_FOR_SUPPLIED_ORIGINAL_VERTEX_BOXES_ONLY')


def render_scene(layers,background=GRASS_RGB[0],flip_vertical=True):
    """Exact AA->filled original-layer order and public1000->96->84 pipeline.

    Each layer is (full polygon vertices, integer RGB). Coordinates are BEFORE
    the official final vertical flip. Background/checkerboard/paint layers are
    explicit; no local geometric completion or unknown-material fill is made.
    Caller supplies already world/camera-transformed original source vertices.
    """
    surface=pygame.Surface((1000,800));surface.fill(background)
    for vertices,color in layers:
        # Assert bounded conversion while passing floats to the actual binding.
        for point in vertices:truncate_vertex(point)
        if len(color)!=3 or any(int(c)!=c or not 0<=c<=255 for c in color):
            raise ValueError('Explicit uint8 RGB required')
        gfxdraw.aapolygon(surface,vertices,color)
        gfxdraw.filled_polygon(surface,vertices,color)
    if flip_vertical:surface=pygame.transform.flip(surface,False,True)
    small=pygame.transform.smoothscale(surface,(96,96))
    rgb=np.transpose(np.array(pygame.surfarray.pixels3d(small)),(1,0,2))
    return cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY)


def model_coverage(*,original_vertices_bounded,all_material_layers_supplied,unknown_corner=False,roi_clipped_endpoints=False):
    complete=original_vertices_bounded and all_material_layers_supplied and not unknown_corner and not roi_clipped_endpoints
    return 'COMPLETE_WITHIN_DECLARED_POLYGON_MODEL'if complete else'UNKNOWN_MODEL_COVERAGE'


def check():
    cpu=time.process_time();tests=[]
    # Finite straight/slanted original edges, plus their original opposite edge.
    boxes=[((400.1,401.9),(200.,200.)),((900.,900.),(200.,200.)),
           ((900.,900.),(600.,600.)),((430.1,431.9),(600.,600.))]
    candidates=list(enumerate_vertex_cells(boxes));assert len(candidates)==4
    known={tuple(tuple(q)for q in c['integer_vertices'])for c in candidates}
    for x0 in (400.1,400.9,401.,401.9):
        for x1 in (430.1,430.9,431.,431.9):
            vertices=[(x0,200.),(900.,200.),(900.,600.),(x1,600.)]
            quantized=tuple(truncate_vertex(q)for q in vertices);assert quantized in known
            for color in (ROAD_RGB[0],ROAD_RGB[2]):
                actual=render_scene([(vertices,color)])
                exact=render_scene([(quantized,color)])
                assert np.array_equal(actual,exact)
                tests.append('straight_original_vertex_cell_exact')
    # Negative coordinates distinguish truncation from floor; include real
    # ordered red/white paint and grass checkerboard polygon nuisance layers.
    for phase in (.1,.9):
        polygon=[(-10-phase,150+phase),(480+phase,200+phase),(520+phase,650+phase),(-20-phase,700+phase)]
        layers=[([(0,0),(500,0),(500,800),(0,800)],GRASS_RGB[1]),
                (polygon,ROAD_RGB[1]),
                ([(460+phase,250),(480+phase,250),(500+phase,450),(480+phase,450)],PAINT_RGB[0]),
                ([(480+phase,450),(500+phase,450),(520+phase,600),(500+phase,600)],PAINT_RGB[1])]
        integer_layers=[([truncate_vertex(q)for q in points],color)for points,color in layers]
        assert np.array_equal(render_scene(layers),render_scene(integer_layers))
        assert truncate_vertex((-10-phase,0))[0]==-10
        tests.append('negative_truncation_ordered_layers_exact')
    assert model_coverage(original_vertices_bounded=True,all_material_layers_supplied=True)=='COMPLETE_WITHIN_DECLARED_POLYGON_MODEL'
    for options in (dict(unknown_corner=True),dict(roi_clipped_endpoints=True)):
        assert model_coverage(original_vertices_bounded=True,all_material_layers_supplied=True,**options)=='UNKNOWN_MODEL_COVERAGE'
    assert model_coverage(original_vertices_bounded=True,all_material_layers_supplied=False)=='UNKNOWN_MODEL_COVERAGE'
    try:list(enumerate_vertex_cells(boxes,max_candidates=3))
    except ValueError:pass
    else:raise AssertionError('Budget must reject incomplete enumeration')
    return dict(status='PASS',exact_render_checks=len(tests),integer_vertex_hypotheses=len(candidates),
        gray_tolerance=0,model_ticks=0,native=0,CPU_s=time.process_time()-cpu,
        implementation_versions=dict(pygame=pygame.version.ver,opencv=cv2.__version__),
        coverage_scope='Finite original vertex boxes and all ordered material layers only. Local clipped lines, unknown tile corners/checkerboard/paint stay UNKNOWN.',
        provenance_url='https://github.com/pygame/pygame/blob/2.6.1/src_c/gfxdraw.c')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--output');args=parser.parse_args()
    if not args.check:parser.error('Use --check, or import the renderer/enumerator API')
    result=check()
    if args.output:Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
