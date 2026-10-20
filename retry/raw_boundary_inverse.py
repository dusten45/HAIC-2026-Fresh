"""Finite polygon-cell inverse; exact gray constraints and interval geometry.

True observed_mask pixels APPLY constraints. False pixels (occlusion/HUD/etc)
apply none. Every compatible hypothesis survives. A finite/conditional local
model cannot certify source material unless the caller explicitly supplies
complete original-vertex/material coverage. No grid search completeness claim.
"""
import argparse
import json
import math
from pathlib import Path
import time
import numpy as np
from retry.observed_pose_support import _sub,_mul,_fraction_bound
from fractions import Fraction
from retry.raw_boundary_renderer import coordinate_cell


def intersect_original_vertex_cell(original_boxes,integer_vertices):
    """Closed hull of real original boxes intersected with truncation cells."""
    if len(original_boxes)!=len(integer_vertices):raise ValueError('Vertex count mismatch')
    result=[]
    for box,vertex in zip(original_boxes,integer_vertices):
        point=[]
        for (lo,hi),integer in zip(box,vertex):
            if not math.isfinite(lo)or not math.isfinite(hi)or lo>hi:raise ValueError('Invalid original interval')
            cell=coordinate_cell(integer);left=max(lo,cell['lower']);right=min(hi,cell['upper'])
            if left>right or(left==right and math.trunc(left)!=integer):return None
            point.append((float(left),float(right)))
        result.append(point)
    return result


def _cross(a,b):
    return _sub(_mul(a[0],b[1]),_mul(a[1],b[0]))


def _difference(a,b):return (_sub(a[0],b[0]),_sub(a[1],b[1]))


def _physical_polygon(record):
    boxes=record.get('vertex_boxes',record.get('original_vertex_boxes'))if isinstance(record,dict)else record
    if boxes is None:return None
    if isinstance(record,dict)and 'integer_vertices'in record:
        boxes=intersect_original_vertex_cell(boxes,record['integer_vertices'])
    if boxes is None or len(boxes)not in(3,4):return None
    result=[]
    for box in boxes:
        if len(box)!=2:return None
        point=[]
        for lo,hi in box:
            if not math.isfinite(lo)or not math.isfinite(hi)or lo>hi or lo< -32768 or hi>32767:return None
            point.append((float(lo),float(hi)))
        result.append(point)
    signs=[_cross(_difference(result[(i+1)%len(result)],result[i]),
                  _difference(result[(i+2)%len(result)],result[(i+1)%len(result)]))for i in range(len(result))]
    if all(s[0]>0 for s in signs):return result,1
    if all(s[1]<0 for s in signs):return result,-1
    return None


def _cell_corners(x,y):
    # Whole84 cell in source coordinates BEFORE the official vertical flip.
    def bound(q):return (_fraction_bound(q,False),_fraction_bound(q,True))
    left=Fraction(int(x)*1000,84)-Fraction(1,2);right=Fraction((int(x)+1)*1000,84)-Fraction(1,2)
    bottom=Fraction(1599,2)-Fraction((int(y)+1)*800,84);top=Fraction(1599,2)-Fraction(int(y)*800,84)
    return [(bound(xx),bound(yy))for xx,yy in ((left,bottom),(right,bottom),(right,top),(left,top))]


def _contains_whole(polygon,corners):
    vertices,orientation=polygon
    for first,last in zip(vertices,vertices[1:]+vertices[:1]):
        direction=_difference(last,first)
        for corner in corners:
            cross=_cross(direction,_difference(corner,first))
            if orientation==1 and cross[0]<0:return False
            if orientation==-1 and cross[1]>0:return False
    return True


def common_whole_cells(models,*,coverage_complete=False,targets=None):
    """All real vertices/all retained models; no gray-to-whole-cell shortcut.

    physical_road_polygons entries are {vertex_boxes:[((xlo,xhi),(ylo,yhi)),..],
    integer_vertices:optional}. Bare vertex-box lists also work. A single known
    convex road polygon must contain the whole cell for each retained model.
    Uncertain convexity/orientation is UNKNOWN and contributes no support.
    physical_road_polygons must already represent pure-asphalt regions after
    material overlays, not merely the road beneath paint. This is a material
    proof only; caller must separately intersect direct-source visibility.
    """
    models=list(models)
    mask=np.zeros((84,84),bool);prepared=[]
    for model in models:
        prepared.append([p for record in model.get('physical_road_polygons',[])if(p:=_physical_polygon(record))is not None])
    targets=list(targets)if targets is not None else[(x,y)for y in range(84)for x in range(84)]
    if models:
        for x,y in targets:
            if not 0<=x<84 or not 0<=y<84:raise ValueError('Target outside84 grid')
            corners=_cell_corners(x,y)
            mask[y,x]=all(any(_contains_whole(poly,corners)for poly in polys)for polys in prepared)
    premise=bool(coverage_complete and models and all(
        model.get('material_complete',False)and not any(model.get(key,False)for key in
        ('unknown_corner','roi_clipped_endpoints','unknown_layer','inverse_schema_unknown'))for model in models))
    return dict(conditional_whole_cells=mask,certified_whole_cells=mask.copy()if premise else np.zeros_like(mask),
        source_certificate_premises_satisfied=premise,conditional_count=int(mask.sum()),certified_count=int(mask.sum())if premise else 0,
        status='CERTIFIED_WITHIN_COMPLETE_MODEL'if premise else'UNKNOWN_SOURCE_MODEL_COVERAGE')


def _forward(model):
    if 'gray_lower'in model and 'gray_upper'in model:
        lo=np.asarray(model['gray_lower']);hi=np.asarray(model['gray_upper'])
    else:
        from retry.raw_pixel_intervals import raster_layer_enclosure,forward_enclosure
        rawlo,rawhi=raster_layer_enclosure(model['layers'],model.get('background_bounds',((102,204,102),(102,230,102))))
        lo,hi=forward_enclosure(rawlo,rawhi)
    if lo.shape!=(84,84)or hi.shape!=(84,84)or lo.dtype!=np.uint8 or hi.dtype!=np.uint8 or np.any(lo>hi)or np.any(lo<0)or np.any(hi>255):
        raise ValueError('Malformed forward gray enclosure')
    return lo,hi


def inverse_models(observed84u8,observed_maskbool,models,*,coverage_complete):
    observed=np.asarray(observed84u8);mask=np.asarray(observed_maskbool)
    if observed.shape!=(84,84)or observed.dtype!=np.uint8:raise ValueError('84x84uint8 observation required')
    if mask.shape!=(84,84)or mask.dtype!=bool:raise ValueError('84x84bool apply-constraint mask required')
    kept=[];rejected=[];unknown=[]
    for i,model in enumerate(models):
        identity=model.get('id',i)
        try:lo,hi=_forward(model)
        except (ValueError,KeyError,TypeError,ImportError,RuntimeError)as exc:
            retained=dict(model,inverse_schema_unknown=True);kept.append(retained);unknown.append(dict(id=identity,reason=str(exc)));continue
        contradiction=mask&((observed<lo)|(observed>hi))
        if np.any(contradiction):
            y,x=map(int,np.argwhere(contradiction)[0]);rejected.append(dict(id=identity,witness=dict(pixel=[x,y],observed=int(observed[y,x]),lower=int(lo[y,x]),upper=int(hi[y,x]))))
        else:kept.append(model)
    return dict(feasibility_scope='necessary outer compatibility, not joint RGB/material witness',status='COMPATIBLE_MODELS_RETAINED'if kept else'NO_COMPATIBLE_MODELS',kept_models=kept,kept_ids=[m.get('id',i)for i,m in enumerate(kept)],rejected=rejected,unknown_enclosures_retained=unknown,coverage_complete=bool(coverage_complete),observed_constraints=int(mask.sum()),empty_candidate_source_certificate=False if not kept else None)


def check():
    from retry.raw_boundary_renderer import render_scene
    cpu=time.process_time();vertices=[(300.2,200.2),(800.2,200.2),(800.2,650.2),(300.2,650.2)];boxes=[[(x-.1,x+.1),(y-.1,y+.1)]for x,y in vertices]
    im=render_scene([(vertices,(102,102,102))]);model=dict(id='original_quad',gray_lower=im,gray_upper=im,material_complete=True,physical_road_polygons=[dict(vertex_boxes=boxes,integer_vertices=[(int(x),int(y))for x,y in vertices])]);mask=np.ones((84,84),bool)
    result=inverse_models(im,mask,[model],coverage_complete=True);assert result['kept_ids']==['original_quad']
    support=common_whole_cells(result['kept_models'],coverage_complete=True,targets=[(40,40),(1,1)]);assert support['certified_whole_cells'][40,40]and not support['certified_whole_cells'][1,1]
    changed=im.copy();changed[40,40]=255
    reject=inverse_models(changed,mask,[model],coverage_complete=True);assert not reject['kept_models']and reject['rejected'][0]['witness']['pixel']==[40,40]
    mask[40,40]=False;assert inverse_models(changed,mask,[model],coverage_complete=True)['kept_models']
    uncertain=common_whole_cells([model],coverage_complete=False,targets=[(40,40)]);assert uncertain['conditional_count']==1 and uncertain['certified_count']==0
    corner=dict(model,unknown_corner=True);assert common_whole_cells([corner],coverage_complete=True,targets=[(40,40)])['certified_count']==0
    mixed=dict(model,id='paint_only',physical_road_polygons=[]);assert common_whole_cells([model,mixed],coverage_complete=True,targets=[(40,40)])['certified_count']==0
    assert common_whole_cells([],coverage_complete=True,targets=[(40,40)])['certified_count']==0
    assert common_whole_cells(iter(()),coverage_complete=True,targets=[(40,40)])['certified_count']==0
    nonconvex=dict(model,physical_road_polygons=[dict(vertex_boxes=[[(300,700),(200,600)],[(300,700),(200,600)],[(300,700),(200,600)],[(300,700),(200,600)]])]);assert common_whole_cells([nonconvex],coverage_complete=True,targets=[(40,40)])['certified_count']==0
    assert intersect_original_vertex_cell([[(-1.,0.),(0.,0.)]],[(-1,0)])==[[(-1.,-1.),(0.,0.)]]
    # Actual upstream raster-layer and preprocessing interval integration.
    layers=[dict(vertices=[(int(x),int(y))for x,y in vertices],rgb_lo=(102,102,102),rgb_hi=(102,102,102),optional=False)]
    raster_model=dict(model,id='layer_enclosure',layers=layers,background_bounds=((102,204,102),(102,204,102)))
    raster_model.pop('gray_lower');raster_model.pop('gray_upper')
    integrated=inverse_models(im,np.ones((84,84),bool),[raster_model],coverage_complete=True)
    assert integrated['kept_ids']==['layer_enclosure']and not integrated['unknown_enclosures_retained']
    optional=dict(raster_model,id='optional_paint',layers=layers+[dict(vertices=[(450,350),(550,350),(550,450),(450,450)],rgb_lo=(255,0,0),rgb_hi=(255,255,255),optional=True)],material_complete=False,physical_road_polygons=[])
    assert inverse_models(im,np.ones((84,84),bool),[optional],coverage_complete=False)['kept_models']
    # Pixelwise enclosures forget CONSTANT layer-color/presence correlation.
    # Two interior samples cannot be red and white in one constant paint layer.
    paint_vertices=[(450,350),(550,350),(550,450),(450,450)]
    red=render_scene([(paint_vertices,(255,0,0))]);white=render_scene([(paint_vertices,(255,255,255))]);absent=render_scene([])
    pairmask=np.zeros((84,84),bool);pairmask[40,40:42]=True
    impossible=red.copy();impossible[40,41]=white[40,41]
    outer=dict(id='optional_red_white_outer',layers=[dict(vertices=paint_vertices,rgb_lo=(255,0,0),rgb_hi=(255,255,255),optional=True)],background_bounds=((102,204,102),(102,204,102)),material_complete=False,physical_road_polygons=[])
    assert inverse_models(impossible,pairmask,[outer],coverage_complete=False)['kept_ids']==['optional_red_white_outer']
    constants=[dict(id=name,gray_lower=picture,gray_upper=picture)for name,picture in(('absent',absent),('red',red),('white',white))]
    exact_choices=inverse_models(impossible,pairmask,constants,coverage_complete=False)
    assert not exact_choices['kept_models']and len(exact_choices['rejected'])==3
    correlation=dict(pixel_positions=[[40,40],[41,40]],observed_gray=[int(impossible[40,40]),int(impossible[40,41])],outer_interval_keeps=1,constant_absent_red_white_keeps=0)
    # Backend guard failure loses constraints, never a candidate or uncertainty.
    from unittest.mock import patch
    with patch(__name__+'._forward',side_effect=RuntimeError('PUBLIC_BACKEND_GUARD')):
        unknown=inverse_models(im,mask,[model],coverage_complete=True)
    assert len(unknown['kept_models'])==1 and len(unknown['unknown_enclosures_retained'])==1
    assert common_whole_cells(unknown['kept_models'],coverage_complete=True,targets=[(40,40)])['certified_count']==0
    return dict(status='PASS',checks=15,model_ticks=0,native=0,gray_epsilon=0,CPU_s=time.process_time()-cpu,scope='Finite model, exact interval integration, correlation-loss counterexample and backend-guard UNKNOWN retention.',feasibility_scope='necessary outer compatibility, not joint RGB/material witness',constant_polygon_color_counterexample=correlation,backend_RuntimeError_retained_unknown_certified_zero=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--output');args=parser.parse_args()
    if not args.check:parser.error('Import API or use --check')
    result=check()
    if args.output:Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
