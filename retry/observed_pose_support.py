"""Continuous SE2 common support under explicit coverage/provenance premises.

Source True cells denote *entire closed cells* of directly observed asphalt.
No image threshold or correspondence fit is certified by this module. A PoseBox
covers source-body -> target-body motion R(theta) p + (tx,ty), in metres/radians.
Grid maps pixel coordinates to ((x-origin_x)/sx,(origin_y-y)/sy).
"""
from dataclasses import dataclass,replace
from fractions import Fraction
from functools import lru_cache
import math

import numpy as np


@dataclass(frozen=True)
class PoseBox:
    theta_lo: float
    theta_hi: float
    tx_lo: float
    tx_hi: float
    ty_lo: float
    ty_hi: float


@dataclass(frozen=True)
class Grid:
    sx: float
    sy: float
    origin_x: float
    origin_y: float


def split_pose_boxes(boxes,*,axes=('theta','tx','ty'),maximum_boxes=8192):
    """Exact closed-box cover; a cap retains ALL original coarse hypotheses.

    Shared midpoint boundaries are present in both children. If binary64 has
    no representable interior midpoint, that axis is left coarse. Invalid boxes
    are retained without interpreting or pruning their coverage.
    """
    boxes = tuple(boxes)
    axes = tuple(dict.fromkeys(axes))
    if any(axis not in ('theta','tx','ty') for axis in axes):
        raise ValueError('Unknown pose axis')
    if not isinstance(maximum_boxes,int) or maximum_boxes<0:
        raise ValueError('Nonnegative integer maximum_boxes required')
    plans = []
    invalid = 0
    projected_count = 0
    for box in boxes:
        vals = (box.theta_lo,box.theta_hi,box.tx_lo,box.tx_hi,box.ty_lo,box.ty_hi)
        ordered = ((box.theta_lo,box.theta_hi),(box.tx_lo,box.tx_hi),(box.ty_lo,box.ty_hi))
        splits = []
        if any(not math.isfinite(v) for v in vals) or any(lo>hi for lo,hi in ordered):
            invalid += 1
        else:
            for axis in axes:
                lo,hi = getattr(box,axis+'_lo'),getattr(box,axis+'_hi')
                # Exact rational average followed by one conversion avoids
                # overflow; any interior rounded midpoint partitions exactly.
                middle = float((Fraction.from_float(float(lo))+Fraction.from_float(float(hi)))/2)
                if lo<middle<hi:
                    splits.append((axis,middle))
        plans.append(splits)
        projected_count += 2**len(splits)
    diagnostics = dict(input_boxes=len(boxes),output_boxes=len(boxes),axes=axes,
        requested_output_boxes=projected_count,maximum_boxes=maximum_boxes,
        cap_preserved_coarse=projected_count>maximum_boxes,
        invalid_boxes_retained=invalid,split_parent_boxes=0)
    if projected_count>maximum_boxes:
        return boxes,diagnostics
    output = []
    for box,splits in zip(boxes,plans):
        children = [box]
        for axis,middle in splits:
            children = [part for child in children for part in
                (replace(child,**{axis+'_hi':middle}),replace(child,**{axis+'_lo':middle}))]
        output.extend(children)
        diagnostics['split_parent_boxes'] += bool(splits)
    diagnostics['output_boxes'] = len(output)
    return tuple(output),diagnostics


def _down(x):
    return math.nextafter(x,-math.inf)


def _up(x):
    return math.nextafter(x,math.inf)


def _add(a,b):
    return _down(a[0]+b[0]),_up(a[1]+b[1])


def _neg(a):
    return -a[1],-a[0]


def _sub(a,b):
    return _add(a,_neg(b))


def _mul(a,b):
    products = [x*y for x in a for y in b]
    return _down(min(products)),_up(max(products))


def _divide_positive(a,d):
    return _down(a[0]/d),_up(a[1]/d)


def _fraction_bound(value, upper):
    floating = float(value)
    represented = Fraction.from_float(floating)
    if upper and represented<value:
        floating = _up(floating)
    if not upper and represented>value:
        floating = _down(floating)
    return floating


@lru_cache(maxsize=4096)
def trig_enclosure(lo,hi):
    """Rigorous rational Taylor + global Lipschitz enclosure, no libm sin/cos.

    For |midpoint|<=8 the finite polynomials are evaluated as exact rationals.
    Taylor's theorem bounds the remainders by |m|^62/62! and |m|^61/61!.
    |sin'|,|cos'|<=1 then encloses the complete input interval. Wide or remote
    intervals use [-1,1]; no periodic reduction or sampled-pose claim is made.
    """
    if not math.isfinite(lo) or not math.isfinite(hi) or lo>hi:
        raise ValueError('Finite ordered angle interval required')
    left,right = Fraction.from_float(float(lo)),Fraction.from_float(float(hi))
    middle,half = (left+right)/2,(right-left)/2
    if abs(middle)>8 or half>=2:
        return (-1.,1.),(-1.,1.)
    sine = sum(((-1)**k*middle**(2*k+1)/math.factorial(2*k+1) for k in range(31)),Fraction())
    cosine = sum(((-1)**k*middle**(2*k)/math.factorial(2*k) for k in range(31)),Fraction())
    se = abs(middle)**62/math.factorial(62)+half
    ce = abs(middle)**61/math.factorial(61)+half
    def bounded(center,error):
        return (_fraction_bound(max(Fraction(-1),center-error),False),
                _fraction_bound(min(Fraction(1),center+error),True))
    return bounded(sine,se),bounded(cosine,ce)


def inverse_cell_bounds(x,y,box,grid,trig=None):
    """Pixel-coordinate AABB enclosing inverse images of the WHOLE target cell.

    Each interval operation rounds outward. Dependency is discarded, making
    this potentially loose; it never replaces a box with its center transform.
    """
    sine,cosine = trig if trig is not None else trig_enclosure(box.theta_lo,box.theta_hi)
    qx = _divide_positive(_sub((x-.5,x+.5),(grid.origin_x,grid.origin_x)),grid.sx)
    qy = _divide_positive(_sub((grid.origin_y,grid.origin_y),(y-.5,y+.5)),grid.sy)
    dx = _sub(qx,(box.tx_lo,box.tx_hi))
    dy = _sub(qy,(box.ty_lo,box.ty_hi))
    px = _add(_mul(cosine,dx),_mul(sine,dy))
    py = _add(_mul(_neg(sine),dx),_mul(cosine,dy))
    ix = _add(_mul((grid.sx,grid.sx),px),(grid.origin_x,grid.origin_x))
    iy = _sub((grid.origin_y,grid.origin_y),_mul((grid.sy,grid.sy),py))
    return ix,iy


def forward_point_bounds(x,y,box,grid,trig=None):
    """Enclose one source cell CENTER's forward image across the entire box."""
    sine,cosine = trig if trig is not None else trig_enclosure(box.theta_lo,box.theta_hi)
    px = _divide_positive(_sub((x,x),(grid.origin_x,grid.origin_x)),grid.sx)
    py = _divide_positive(_sub((grid.origin_y,grid.origin_y),(y,y)),grid.sy)
    qx = _add(_sub(_mul(cosine,px),_mul(sine,py)),(box.tx_lo,box.tx_hi))
    qy = _add(_add(_mul(sine,px),_mul(cosine,py)),(box.ty_lo,box.ty_hi))
    ix = _add(_mul((grid.sx,grid.sx),qx),(grid.origin_x,grid.origin_x))
    iy = _sub((grid.origin_y,grid.origin_y),_mul((grid.sy,grid.sy),qy))
    return ix,iy


def prune_pose_boxes(source_known_asphalt,current_known_grass,boxes,*,grid,material_premise):
    """Remove a box only on a contradiction valid for EVERY pose inside it.

    Certified source asphalt implies its center point is asphalt. If that
    point's entire forward AABB lies in certified current grass, no pose in the
    box is possible. Unknown/off-image/ego/object pixels are not negative
    evidence. Without the material premise every input box is returned.
    """
    boxes = tuple(boxes)
    masks = (source_known_asphalt,current_known_grass)
    if any(not isinstance(m,np.ndarray) or m.ndim!=2 or m.dtype!=bool for m in masks):
        raise ValueError('Two-dimensional Boolean material masks required')
    diagnostics = dict(input_boxes=len(boxes),surviving_boxes=len(boxes),
        rejected_boxes=0,source_point_tests=0,invalid_boxes_retained=0,
        material_premise_used=bool(material_premise),rejections=[])
    if not material_premise:
        return boxes,diagnostics
    if any(not math.isfinite(v) for v in (grid.sx,grid.sy,grid.origin_x,grid.origin_y)) or grid.sx<=0 or grid.sy<=0:
        diagnostics['invalid_grid_retained_all'] = True
        return boxes,diagnostics
    points = [(int(x),int(y)) for y,x in zip(*np.nonzero(source_known_asphalt))]
    h,w = current_known_grass.shape
    nongrass = np.pad((~current_known_grass).astype(np.int64),((1,0),(1,0))).cumsum(0).cumsum(1)
    survivors = []
    for index,box in enumerate(boxes):
        vals = (box.theta_lo,box.theta_hi,box.tx_lo,box.tx_hi,box.ty_lo,box.ty_hi)
        if any(not math.isfinite(v) for v in vals) or any(lo>hi for lo,hi in
                ((box.theta_lo,box.theta_hi),(box.tx_lo,box.tx_hi),(box.ty_lo,box.ty_hi))):
            survivors.append(box);diagnostics['invalid_boxes_retained'] += 1
            continue
        trig = trig_enclosure(box.theta_lo,box.theta_hi)
        witness = None
        for x,y in points:
            diagnostics['source_point_tests'] += 1
            ix,iy = forward_point_bounds(x,y,box,grid,trig)
            if any(not math.isfinite(v) for v in (*ix,*iy)):
                continue
            x0,x1 = math.floor(_down(ix[0]+.5)),math.ceil(_up(ix[1]+.5))-1
            y0,y1 = math.floor(_down(iy[0]+.5)),math.ceil(_up(iy[1]+.5))-1
            if x0<0 or y0<0 or x1>=w or y1>=h:
                continue
            if nongrass[y1+1,x1+1]-nongrass[y0,x1+1]-nongrass[y1+1,x0]+nongrass[y0,x0] == 0:
                witness = dict(box_index=index,source_center=[x,y],
                    forward_x_interval=ix,forward_y_interval=iy,
                    current_grass_rectangle=[x0,x1,y0,y1])
                break
        if witness is None:
            survivors.append(box)
        else:
            diagnostics['rejections'].append(witness)
    diagnostics['surviving_boxes'] = len(survivors)
    diagnostics['rejected_boxes'] = len(boxes)-len(survivors)
    return tuple(survivors),diagnostics


def common_support(source_asphalt,source_direct,boxes,current_grass,current_object,
                   *,grid,coverage_complete,source_cells_certified):
    """Intersect every alias/continuous box; invalid/uncovered inputs discard.

    The source grid and target grid use the same Grid coordinate convention.
    A pixel survives only if every source cell touched by the conservative
    inverse AABB is certified direct asphalt. Ego opacity is not a contradiction
    veto. Callers must include every alias and all remaining pose uncertainty.
    Floating outward rounding may require extra cells at exact boundaries.
    """
    masks = (source_asphalt,source_direct,current_grass,current_object)
    if any(not isinstance(m,np.ndarray) or m.ndim!=2 or m.dtype!=bool for m in masks):
        raise ValueError('Two-dimensional Boolean masks required')
    if source_asphalt.shape!=source_direct.shape or current_grass.shape!=current_object.shape:
        raise ValueError('Mask shapes disagree')
    output = np.zeros_like(current_grass)
    boxes = tuple(boxes)
    if not coverage_complete or not source_cells_certified or not boxes:
        return output
    parameters = (grid.sx,grid.sy,grid.origin_x,grid.origin_y)
    if any(not math.isfinite(v) for v in parameters) or grid.sx<=0 or grid.sy<=0:
        return output
    for box in boxes:
        values = (box.theta_lo,box.theta_hi,box.tx_lo,box.tx_hi,box.ty_lo,box.ty_hi)
        if any(not math.isfinite(v) for v in values):
            return output
        if any(lo>hi for lo,hi in ((box.theta_lo,box.theta_hi),(box.tx_lo,box.tx_hi),(box.ty_lo,box.ty_hi))):
            return output
    eligible = source_asphalt & source_direct
    bad = np.pad((~eligible).astype(np.int64),((1,0),(1,0))).cumsum(0).cumsum(1)
    h,w = eligible.shape
    output[:] = ~(current_grass | current_object)
    for box in boxes:
        trig = trig_enclosure(box.theta_lo,box.theta_hi)
        for y,x in zip(*np.nonzero(output)):
            ix,iy = inverse_cell_bounds(int(x),int(y),box,grid,trig)
            if any(not math.isfinite(v) for v in (*ix,*iy)):
                output[y,x] = False
                continue
            # Positive-area source-cell intersection. Outward rounding also
            # includes uncertain boundary-touching neighbors conservatively.
            x0,x1 = math.floor(_down(ix[0]+.5)),math.ceil(_up(ix[1]+.5))-1
            y0,y1 = math.floor(_down(iy[0]+.5)),math.ceil(_up(iy[1]+.5))-1
            if x0<0 or y0<0 or x1>=w or y1>=h:
                output[y,x] = False
            elif bad[y1+1,x1+1]-bad[y0,x1+1]-bad[y1+1,x0]+bad[y0,x0]:
                output[y,x] = False
        if not output.any():
            break
    return output
