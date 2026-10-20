"""Set-valued visual correspondence constraints, not a best-fit pose estimator.

Each group contains all alternative associations for one required landmark.
Every Cartesian-product assignment and every angular interval is retained unless
interval translation constraints prove it infeasible. Unknown/missed identities
are an explicit uncovered-pose branch, never silently dropped. Localization
bounds must be supplied by evidence; this module does not estimate them from FB
error, least-squares residuals, or an own-action prediction.
"""
from dataclasses import dataclass
import itertools
import math

from retry.observed_pose_support import PoseBox, trig_enclosure, _add, _sub, _mul


@dataclass(frozen=True)
class PointBox:
    x_lo: float
    x_hi: float
    y_lo: float
    y_hi: float

    def valid(self):
        return (all(math.isfinite(v) for v in (self.x_lo,self.x_hi,self.y_lo,self.y_hi))
                and self.x_lo<=self.x_hi and self.y_lo<=self.y_hi)


@dataclass(frozen=True)
class Association:
    source: PointBox
    target: PointBox
    label: str


@dataclass(frozen=True)
class PoseCandidates:
    boxes: tuple
    coverage_complete: bool
    unknown_reasons: tuple
    assignments_enumerated: int
    angular_intervals_per_assignment: int
    assignments_with_surviving_boxes: tuple


def translation_box(association,theta_lo,theta_hi,trig=None):
    """Enclose all q-R(theta)p, including source and target localization sets."""
    if not association.source.valid() or not association.target.valid():
        raise ValueError('Finite ordered point localization intervals required')
    p,q=association.source,association.target
    sine,cosine=trig if trig is not None else trig_enclosure(theta_lo,theta_hi)
    rx=_sub(_mul(cosine,(p.x_lo,p.x_hi)),_mul(sine,(p.y_lo,p.y_hi)))
    ry=_add(_mul(sine,(p.x_lo,p.x_hi)),_mul(cosine,(p.y_lo,p.y_hi)))
    tx=_sub((q.x_lo,q.x_hi),rx);ty=_sub((q.y_lo,q.y_hi),ry)
    return tx,ty


def build_pose_candidates(groups,*,angle_domain,angular_intervals,
                          association_coverage_proved,localization_proved,angle_coverage_proved,
                          unmatched_possible,maximum_assignments=4096):
    """Cover all feasible transforms under the supplied association model.

    Angle partitions are computational resolution, NOT confidence intervals.
    Each cell covers its full continuous interval. Translation boxes are outer
    enclosures; intersection can retain infeasible transforms but never selects
    a best residual/closest prior. Domain coverage must itself be established by
    the caller. [-4,4] covers a full circle without relying on rounded pi ends.

    A false premise does not erase conditional diagnostic boxes: it appends an
    unknown branch and makes coverage_complete false, so production support is
    empty. No absolute error bound is invented to make a correspondence pass.
    """
    groups=tuple(tuple(group) for group in groups)
    reasons=[]
    if not association_coverage_proved:reasons.append('ASSOCIATION_COVERAGE_UNPROVED')
    if not localization_proved:reasons.append('ABSOLUTE_LOCALIZATION_UNPROVED')
    if not angle_coverage_proved:reasons.append('ANGLE_DOMAIN_COVERAGE_UNPROVED')
    if unmatched_possible:reasons.append('UNMATCHED_OR_HIDDEN_IDENTITY_BRANCH')
    if (len(angle_domain)!=2 or not all(math.isfinite(v) for v in angle_domain)
            or angle_domain[0]>angle_domain[1]
            or not math.isfinite(angle_domain[1]-angle_domain[0])):
        return PoseCandidates((),False,tuple(reasons+['INVALID_ANGLE_DOMAIN']),0,0,())
    if not isinstance(angular_intervals,int) or angular_intervals<1:
        raise ValueError('Positive integer angular partition count required')
    if not isinstance(maximum_assignments,int) or maximum_assignments<1:
        raise ValueError('Positive integer assignment cap required')
    if not groups:
        return PoseCandidates((),False,tuple(reasons+['NO_REQUIRED_LANDMARK_CONSTRAINT']),0,0,())
    count=math.prod(len(group) for group in groups)
    if count>maximum_assignments:
        return PoseCandidates((),False,tuple(reasons+['ASSIGNMENT_CAP_NO_ALIAS_PRUNING']),0,0,())
    if any(not a.source.valid() or not a.target.valid() for group in groups for a in group):
        return PoseCandidates((),False,tuple(reasons+['INVALID_LOCALIZATION_SET']),0,0,())
    lo,hi=map(float,angle_domain)
    # Adjacent intervals share the same computed endpoints; no angular gaps.
    endpoints=[lo+(hi-lo)*i/angular_intervals for i in range(angular_intervals+1)]
    endpoints[0]=lo;endpoints[-1]=hi
    angles=[(a,b,trig_enclosure(a,b)) for a,b in zip(endpoints,endpoints[1:])]
    boxes=[];survivors=[]
    for assignment in itertools.product(*groups):
        start=len(boxes)
        for a,b,trig in angles:
            tx=(-math.inf,math.inf);ty=(-math.inf,math.inf)
            for correspondence in assignment:
                x,y=translation_box(correspondence,a,b,trig)
                tx=(max(tx[0],x[0]),min(tx[1],x[1]))
                ty=(max(ty[0],y[0]),min(ty[1],y[1]))
                if tx[0]>tx[1] or ty[0]>ty[1]:break
            else:
                boxes.append(PoseBox(a,b,*tx,*ty))
        if len(boxes)>start:
            survivors.append(tuple(c.label for c in assignment))
    return PoseCandidates(tuple(boxes),not reasons,tuple(reasons),count,
                          angular_intervals,tuple(survivors))
