"""Public set-valued correspondence tests; no episode data or simulator."""
import json
import math
import time
import numpy as np

from retry.observed_pose_candidates import PointBox,Association,build_pose_candidates
from retry.observed_pose_support import Grid,common_support


def run_checks():
    cpu=time.process_time();checks=[]
    def check(name,value):
        assert value,name
        checks.append(name)
    def point(x,y):return PointBox(x,x,y,y)
    def build(groups,**kw):
        opts=dict(angle_domain=(0.,0.),angular_intervals=1,
            association_coverage_proved=True,localization_proved=True,
            angle_coverage_proved=True,unmatched_possible=False)
        opts.update(kw);return build_pose_candidates(groups,**opts)
    simple=Association(point(1,2),point(4,1),'translation')
    result=build([[simple]])
    check('exact_translation_enclosed',any(b.tx_lo<=3<=b.tx_hi and b.ty_lo<=-1<=b.ty_hi for b in result.boxes))
    second=Association(point(1,2),point(-5,1),'second_alias')
    aliases=build([[simple,second]])
    check('both_aliases_retained',len(aliases.boxes)==2 and len(aliases.assignments_with_surviving_boxes)==2)
    unknown=build([[simple]],unmatched_possible=True)
    check('unmatched_branch_preserved',not unknown.coverage_complete and bool(unknown.boxes))
    check('missing_localization_not_fitted',not build([[simple]],localization_proved=False).coverage_complete)
    check('unproved_angle_domain_not_accepted',not build([[simple]],angle_coverage_proved=False).coverage_complete)
    wide=build([[simple]],angle_domain=(-1e308,1e308))
    check('overflowing_angle_span_discards',not wide.coverage_complete and not wide.boxes)
    theta=.37;tx,ty=1.5,-2.25;groups=[]
    for i,(x,y) in enumerate(((-3,2),(4,-1))):
        qx=math.cos(theta)*x-math.sin(theta)*y+tx
        qy=math.sin(theta)*x+math.cos(theta)*y+ty
        # Declared synthetic measurement cells, not an estimated real error.
        groups.append([Association(point(x,y),PointBox(qx-1e-12,qx+1e-12,qy-1e-12,qy+1e-12),str(i))])
    bounded=build(groups,angle_domain=(.3,.4),angular_intervals=32)
    check('nonquarter_rotation_and_translation_enclosed',any(b.theta_lo<=theta<=b.theta_hi and b.tx_lo<=tx<=b.tx_hi and b.ty_lo<=ty<=b.ty_hi for b in bounded.boxes))
    impossible=build([[Association(point(0,0),point(0,0),'anchor')],
                     [Association(point(5,0),point(7,0),'inconsistent_distance')]],
                    angle_domain=(-4.,4.),angular_intervals=256)
    check('distance_inconsistent_assignment_empty',impossible.coverage_complete and not impossible.boxes)
    capped=build([[simple,second],[simple,second]],maximum_assignments=2)
    check('assignment_cap_discards_without_pruning',not capped.coverage_complete and not capped.boxes)
    bad=build([[Association(PointBox(1,-1,0,0),point(0,0),'bad')]])
    check('invalid_localization_discards',not bad.coverage_complete and not bad.boxes)
    n=25;source=np.zeros((n,n),bool);source[4:21,4:21]=True
    zero=np.zeros_like(source);direct=np.ones_like(source);grid=Grid(1.,1.,12.,12.)
    single=common_support(source,direct,result.boxes,zero,zero,grid=grid,
        coverage_complete=result.coverage_complete,source_cells_certified=True)
    union=common_support(source,direct,aliases.boxes,zero,zero,grid=grid,
        coverage_complete=aliases.coverage_complete,source_cells_certified=True)
    check('alias_intersection_contracts_support',0<union.sum()<single.sum())
    empty=common_support(source,direct,unknown.boxes,zero,zero,grid=grid,
        coverage_complete=unknown.coverage_complete,source_cells_certified=True)
    check('unknown_identity_support_empty',not empty.any())
    return dict(status='POSE_CANDIDATE_CHECK_PASS',checks=checks,checks_passed=len(checks),
                CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0)


if __name__=='__main__':print(json.dumps(run_checks()))
