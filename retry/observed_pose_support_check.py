"""Public checks for continuous pose support, not actual-frame certification."""
import argparse
import json
import math
from pathlib import Path
import time

import numpy as np

from retry.observed_pose_support import Grid,PoseBox,common_support,inverse_cell_bounds,prune_pose_boxes,split_pose_boxes


def run_checks():
    start = time.process_time()
    grid = Grid(2.,3.,15.,15.)
    source = np.zeros((31,31),bool);source[3:28,4:27] = True
    full = np.ones_like(source);empty = np.zeros_like(source)
    identity = PoseBox(0.,0.,0.,0.,0.,0.)
    def use(boxes, asphalt=source, direct=full, grass=empty, obj=empty, **premises):
        return common_support(asphalt,direct,boxes,grass,obj,grid=grid,
            coverage_complete=premises.get('coverage',True),
            source_cells_certified=premises.get('certified',True))
    tests = []
    def check(name,condition):
        if not condition:
            raise AssertionError(name)
        tests.append(dict(name=name,passed=True))
    zero = use([identity])
    check('identity_nonempty_and_subset',zero.any() and np.all(zero<=source))
    shift = use([PoseBox(0.,0.,.5,.5,0.,0.)])
    expected = np.zeros_like(source);expected[:,1:] = source[:,:-1]
    check('exact_translation_conservative',shift[15,16] and np.all(shift<=expected))
    fixed = PoseBox(.37,.37,.3,.3,-.2,-.2)
    rotated = use([fixed])
    check('nonquarter_rotation_positive',rotated[15,15] and rotated.sum()>20)
    # Independent analytic rectangle: inverse corner coordinates must lie in
    # the physical union of the source rectangle's certified square cells.
    def source_point(x,y,theta,tx,ty):
        qx,qy=(x-grid.origin_x)/grid.sx,(grid.origin_y-y)/grid.sy
        c,s=math.cos(theta),math.sin(theta)
        px=c*(qx-tx)+s*(qy-ty);py=-s*(qx-tx)+c*(qy-ty)
        return grid.origin_x+grid.sx*px,grid.origin_y-grid.sy*py
    valid = True
    for y,x in zip(*np.nonzero(rotated)):
        for dx in [-.5,.5]:
            for dy in [-.5,.5]:
                px,py=source_point(x+dx,y+dy,.37,.3,-.2)
                valid &= 3.5<=px<=26.5 and 2.5<=py<=27.5
    check('fixed_rotation_whole_cell_rectangle_bound',valid)
    uncertain = PoseBox(.31,.43,.2,.4,-.3,-.1)
    bounded = use([uncertain])
    check('continuous_box_positive_conservative',bounded.any() and np.all(bounded<=rotated))
    # Dense samples are only a conditional regression check; production proof
    # uses outward interval enclosures over the entire continuous box.
    valid = True;sampled = 0
    for y,x in zip(*np.nonzero(bounded)):
        for theta in np.linspace(.31,.43,7):
            for tx in [.2,.3,.4]:
                for ty in [-.3,-.2,-.1]:
                    for dx,dy in [(-.5,-.5),(-.5,.5),(.5,-.5),(.5,.5),(0.,0.)]:
                        px,py=source_point(x+dx,y+dy,float(theta),tx,ty)
                        valid &= 3.5<=px<=26.5 and 2.5<=py<=27.5
                        sampled += 1
    check('dense_sample_subset_regression_not_proof',valid and sampled>0)
    near = inverse_cell_bounds(15,15,PoseBox(-.1,.1,0.,0.,0.,0.),grid)
    far = inverse_cell_bounds(28,15,PoseBox(-.1,.1,0.,0.,0.,0.),grid)
    check('rotation_uncertainty_spatial_growth',far[1][1]-far[1][0]>near[1][1]-near[1][0])
    aliases = use([identity,PoseBox(0.,0.,2.,2.,0.,0.)])
    check('aliases_intersect_instead_of_choose',aliases.sum()<zero.sum() and np.all(aliases<=zero))
    check('disjoint_aliases_empty',not use([identity,PoseBox(0.,0.,20.,20.,0.,0.)]).any())
    hole = full.copy();hole[15,15]=False
    check('provenance_hole_veto',not use([identity],direct=hole)[15,15])
    grass=empty.copy();grass[15,15]=True
    obj=empty.copy();obj[16,15]=True
    contradicted=use([identity],grass=grass,obj=obj)
    check('current_grass_and_object_veto',not contradicted[15,15] and not contradicted[16,15])
    check('missing_source_certification_empty',not use([identity],certified=False).any())
    check('incomplete_alias_coverage_empty',not use([identity],coverage=False).any())
    check('empty_pose_set_empty',not use([]).any())
    check('inverted_box_empty',not use([PoseBox(.2,-.2,0.,0.,0.,0.)]).any())
    check('unbounded_box_empty',not use([PoseBox(-math.inf,0.,0.,0.,0.,0.)]).any())
    check('nan_bound_empty',not use([PoseBox(0.,0.,math.nan,0.,0.,0.)]).any())
    point = empty.copy();point[15,15] = True
    def prune(boxes,grass, premise=True):
        return prune_pose_boxes(point,grass,boxes,grid=grid,material_premise=premise)
    grass_right = empty.copy();grass_right[:,16:] = True
    negative = PoseBox(0.,0.,2.,2.,0.,0.)
    survived,diagnostics = prune([negative],grass_right)
    check('semantic_exact_negative_box_rejected',not survived and diagnostics['rejected_boxes']==1)
    uncertain_grass = empty.copy();uncertain_grass[:,15:] = True
    straddles = PoseBox(-.1,.1,-1.,1.,0.,0.)
    check('semantic_uncertain_straddling_box_retained',prune([straddles],uncertain_grass)[0]==(straddles,))
    offscreen = PoseBox(0.,0.,100.,100.,0.,0.)
    check('semantic_off_fov_not_negative',prune([offscreen],full)[0]==(offscreen,))
    check('semantic_unknown_material_no_pruning',prune([negative],grass_right,False)[0]==(negative,))
    check('semantic_unknown_pixels_not_negative',prune([identity],empty)[0]==(identity,))
    aliases_kept,diagnostics = prune([identity,negative],grass_right)
    check('semantic_keep_positive_remove_negative_alias',aliases_kept==(identity,) and diagnostics['rejected_boxes']==1)
    invalid = PoseBox(-math.inf,0.,0.,0.,0.,0.)
    check('semantic_unbounded_alias_retained',prune([invalid],full)[0]==(invalid,))
    # A continuous box containing true motion must survive when that source
    # point never maps into the explicitly separated grass region.
    actual_box = PoseBox(.2,.4,-.2,.2,-.2,.2)
    grass_far = empty.copy();grass_far[:,:5] = True
    check('semantic_true_motion_box_retained',prune([actual_box],grass_far)[0]==(actual_box,))
    offcenter = empty.copy();offcenter[15,22] = True
    grass_top = empty.copy();grass_top[:8,:] = True
    rotated_negative = PoseBox(1.55,1.59,0.,0.,0.,0.)
    survived,diagnostics = prune_pose_boxes(offcenter,grass_top,[rotated_negative],
        grid=grid,material_premise=True)
    check('semantic_rotation_offcenter_witness',not survived and diagnostics['rejected_boxes']==1)
    # Independent sampled countercheck of every reported rejection witness.
    # Sampling is regression evidence only; rejection uses interval enclosure.
    rejected_boxes = [PoseBox(-.1,.1,2.,3.,-.1,.1),negative]
    survived,diagnostics = prune(rejected_boxes,grass_right)
    valid = diagnostics['rejected_boxes']==2
    for witness in diagnostics['rejections']:
        box = rejected_boxes[witness['box_index']]
        for theta in np.linspace(box.theta_lo,box.theta_hi,9):
            for tx in np.linspace(box.tx_lo,box.tx_hi,5):
                for ty in np.linspace(box.ty_lo,box.ty_hi,5):
                    # The chosen source center is at the grid origin.
                    px,py = grid.origin_x+grid.sx*tx,grid.origin_y-grid.sy*ty
                    valid &= bool(grass_right[math.floor(py+.5),math.floor(px+.5)])
    check('semantic_rejection_dense_regression_not_proof',valid)
    parent = PoseBox(-.4,.4,-1.,3.,-.5,.5)
    children,diagnostics = split_pose_boxes([parent])
    check('split_all_eight_closed_children',len(children)==8 and diagnostics['split_parent_boxes']==1)
    def contains(box,theta,tx,ty):
        return box.theta_lo<=theta<=box.theta_hi and box.tx_lo<=tx<=box.tx_hi and box.ty_lo<=ty<=box.ty_hi
    points = [(theta,tx,ty) for theta in [-.4,-.2,0.,.2,.4]
        for tx in [-1.,0.,1.,2.,3.] for ty in [-.5,-.25,0.,.25,.5]]
    check('split_full_parent_coverage_regression',all(any(contains(b,*point) for b in children) for point in points))
    check('split_midpoint_shared_by_all_eight',sum(contains(b,0.,1.,0.) for b in children)==8)
    check('split_no_axes_unchanged',split_pose_boxes([parent],axes=())[0]==(parent,))
    check('split_degenerate_box_unchanged',split_pose_boxes([identity])[0]==(identity,))
    partially_degenerate = PoseBox(0.,0.,-1.,1.,-1.,1.)
    check('split_only_nondegenerate_axes',len(split_pose_boxes([partially_degenerate])[0])==4)
    coarse,diagnostics = split_pose_boxes([parent],maximum_boxes=7)
    check('split_cap_keeps_entire_coarse_box',coarse==(parent,) and diagnostics['cap_preserved_coarse'])
    coarse,diagnostics = split_pose_boxes([parent,identity],maximum_boxes=8)
    check('split_cap_never_partial_alias_truncation',coarse==(parent,identity) and diagnostics['requested_output_boxes']==9)
    invalid_children,diagnostics = split_pose_boxes([invalid])
    check('split_invalid_alias_retained',len(invalid_children)==1 and invalid_children[0] is invalid)
    adjacent = PoseBox(0.,math.nextafter(0.,1.),0.,0.,0.,0.)
    check('split_unrepresentable_midpoint_keeps_coarse',split_pose_boxes([adjacent])[0]==(adjacent,))
    survivors = (parent,)
    for _ in range(2):
        survivors,_ = split_pose_boxes(survivors)
        survivors,_ = prune(survivors,grass_right)
    check('split_and_semantic_prune_two_rounds_true_pose_retained',
        any(contains(box,0.,0.,0.) for box in survivors))
    return dict(status='PUBLIC_CONTINUOUS_POSE_SUPPORT_PASS',tests=tests,
        CPU_s=time.process_time()-start,model_ticks=0,native_actions=0,
        sampled_regression_points=sampled,
        support_pixels=dict(identity=int(zero.sum()),fixed_rotation=int(rotated.sum()),continuous_box=int(bounded.sum())),
        premises='Certified direct whole-cell source and complete pose-box coverage are supplied premises, not proved for actual51.',
        proof='Exact-rational Taylor remainder and Lipschitz enclose sine/cosine intervals; outward-rounded interval operations enclose inverse images of whole target cells. Every intersected source cell must be direct eligible for every box.',
        limitations='Axis-aligned interval dependency loss and floating boundary rounding can discard valid support. Dense sampling is only a test; no correspondence estimator or production Agent modification.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args()
    result=run_checks()
    if args.output:
        if args.output.exists():raise FileExistsError(args.output)
        args.output.write_text(json.dumps(result,indent=2)+'\n');args.output.chmod(0o600)
    print(json.dumps(result))


if __name__=='__main__':main()
