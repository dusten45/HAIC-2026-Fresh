"""Public grid-memory design checks; no estimator or actual-episode admission.

Every source True cell must be entirely directly observed asphalt. The supplied
hypothesis set MUST cover actual motion, and each displacement bound MUST cover
all remaining continuous error in output-grid L-infinity distance. These are
explicit premises, not properties established by optical flow or these tests.
Nominal transforms here are exact quarter-turns and integer translations only.
"""
import argparse
from dataclasses import dataclass
import json
import math
from pathlib import Path
import time

import numpy as np


@dataclass(frozen=True)
class Motion:
    quarter_turns: int = 0
    dx: int = 0
    dy: int = 0
    displacement_bound_px: float = 0.
    resampling_bound_px: float = 0.


def erode_square(mask, radius):
    """Intersect every integer offset; outside-image material stays unknown."""
    h,w = mask.shape
    padded = np.pad(mask,radius,constant_values=False)
    out = np.ones_like(mask,dtype=bool)
    for dy in range(2*radius+1):
        for dx in range(2*radius+1):
            out &= padded[dy:dy+h,dx:dx+w]
    return out


def exact_grid_warp(mask, motion):
    if not all(isinstance(v,int) for v in (motion.quarter_turns,motion.dx,motion.dy)):
        raise ValueError('Exact grid transform requires integer parameters')
    if mask.shape[0] != mask.shape[1]:
        raise ValueError('Quarter-turn grid must be square')
    rotated = np.rot90(mask,motion.quarter_turns)
    h,w = mask.shape
    out = np.zeros_like(mask,dtype=bool)
    x0,x1 = max(0,motion.dx),min(w,w+motion.dx)
    y0,y1 = max(0,motion.dy),min(h,h+motion.dy)
    if x0<x1 and y0<y1:
        out[y0:y1,x0:x1] = rotated[y0-motion.dy:y1-motion.dy,x0-motion.dx:x1-motion.dx]
    return out


def eligible_memory(asphalt, directly_visible, hypotheses, current_grass,
                    current_object, *, coverage_premise, error_bound_premise):
    """Return support only under explicit, externally supplied premises.

    Opaque ego pixels are unknown background, so they are not a material veto.
    Ambiguous hypotheses are intersected. A bound b removes ceil(b) full cell
    rings, a conservative enclosure for ALL continuous displacements, including
    resampling error. No sampling of an uncertainty interval is used.
    """
    shape = asphalt.shape
    masks = [asphalt,directly_visible,current_grass,current_object]
    if len(shape)!=2 or any(m.shape!=shape or m.dtype!=bool for m in masks):
        raise ValueError('Equal-shaped Boolean masks required')
    if not coverage_premise or not error_bound_premise or not hypotheses:
        return np.zeros_like(asphalt)
    source = asphalt & directly_visible
    support = np.ones_like(source)
    for motion in hypotheses:
        bounds = (motion.displacement_bound_px,motion.resampling_bound_px)
        if any(not math.isfinite(b) or b<0 for b in bounds):
            raise ValueError('Finite nonnegative certified bounds required')
        warped = exact_grid_warp(source,motion)
        radius = math.ceil(sum(bounds))
        if radius>=max(shape):
            warped = np.zeros_like(warped)
        elif radius:
            warped = erode_square(warped,radius)
        support &= warped
    return support & ~current_grass & ~current_object


def rigid_distance_violation(before, after, absolute_error_bound):
    """Necessary condition only; passing does not prove correspondence identity."""
    p,q = np.asarray(before,float),np.asarray(after,float)
    if p.shape!=q.shape or p.ndim!=2 or p.shape[1]!=2 or absolute_error_bound<0:
        raise ValueError('Paired points and nonnegative error bound required')
    delta = np.abs(np.linalg.norm(p[:,None]-p[None,:],axis=2)-
                   np.linalg.norm(q[:,None]-q[None,:],axis=2))
    return bool(np.any(delta>2*absolute_error_bound))


def run_checks():
    start = time.process_time()
    n = 17
    empty = np.zeros((n,n),bool)
    full = np.ones((n,n),bool)
    source = empty.copy(); source[4:13,3:10] = True
    def use(src, motions, visible=full, grass=empty, obstacle=empty, **kwargs):
        return eligible_memory(src,visible,motions,grass,obstacle,
            coverage_premise=kwargs.get('coverage',True),
            error_bound_premise=kwargs.get('bounds',True))
    results = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        results.append(dict(name=name,passed=True))
    shifted = use(source,[Motion(dx=2,dy=-1)])
    expected = empty.copy(); expected[3:12,5:12] = True
    check('exact_translation',np.array_equal(shifted,expected))
    check('exact_quarter_rotation',np.array_equal(use(source,[Motion(quarter_turns=1)]),np.rot90(source)))
    # The current ego occlusion never supplies source evidence or a material veto.
    ego = empty.copy(); ego[6:9,6:9] = True
    check('current_ego_occlusion_allowed',np.all(use(source,[Motion()])[ego]))
    visible = full.copy(); visible[6:9,6:9] = False
    check('historical_inferred_hole_discarded',not np.any(use(source,[Motion()],visible=visible)[ego]))
    grass = empty.copy(); grass[7,7] = True
    check('current_grass_veto',not use(source,[Motion()],grass=grass)[7,7])
    obstacle = empty.copy(); obstacle[8,7] = True
    check('current_object_veto',not use(source,[Motion()],obstacle=obstacle)[8,7])
    ambiguous = use(source,[Motion(),Motion(dx=3)])
    check('repeated_pattern_alias_contracts',np.array_equal(ambiguous,source & exact_grid_warp(source,Motion(dx=3))))
    check('disjoint_aliases_empty',not np.any(use(source,[Motion(),Motion(dx=10)])))
    aperture = use(source,[Motion(dy=-3),Motion(dy=3)])
    check('edge_aperture_no_optimistic_selection',np.all(aperture<=source) and aperture.sum()<source.sum())
    bounded = use(source,[Motion(displacement_bound_px=1)])
    check('continuous_displacement_enclosure',np.array_equal(bounded,erode_square(source,1)))
    check('resampling_error_included',np.array_equal(use(source,[Motion(displacement_bound_px=.4,resampling_bound_px=.7)]),erode_square(source,2)))
    check('missing_coverage_discards',not np.any(use(source,[Motion()],coverage=False)))
    check('uncertified_error_discards',not np.any(use(source,[Motion()],bounds=False)))
    check('empty_hypothesis_set_discards',not np.any(use(source,[])))
    check('outlier_pair_distance_rejected',rigid_distance_violation([[0,0],[5,0]],[[0,0],[7,0]],.25))
    check('rigid_pair_gate_not_identity_proof',not rigid_distance_violation([[0,0],[5,0]],[[10,0],[15,0]],.25))
    return dict(status='PUBLIC_CONSERVATIVE_MEMORY_DESIGN_PASS',tests=results,
        CPU_s=time.process_time()-start,model_ticks=0,native_actions=0,
        premises=['Historical True cells are directly observed whole-cell asphalt, not inferred support.',
            'Supplied transform hypotheses cover the actual correspondence aliases/motion.',
            'Displacement plus resampling bound covers every continuous output-grid error.'],
        limitations='These premises are not proved for actual call51. No registration optimizer, motion fit, inferred road source, Agent modification or actual-frame admission is included.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    result = run_checks()
    if args.output:
        if args.output.exists():
            raise FileExistsError(args.output)
        args.output.write_text(json.dumps(result,indent=2)+'\n')
        args.output.chmod(0o600)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
