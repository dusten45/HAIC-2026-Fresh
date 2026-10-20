"""Finite raster-phase diagnostics for the public orange regular polygon.

For a FIXED source center/radius, polygon vertices change their integer
truncation only at analytically computed sin/cos integer crossings. This is
not a cover of uncertain continuous center cells. Numerical root arithmetic
is checked against direct phase samples, not advertised as interval proof.
No simulator, controller, or hidden scene state is used.
"""
import math
import numpy as np


SOURCE_RADIUS=float(np.float32(1.2))*16.2


def polygon_vertices(center, phase, radius=SOURCE_RADIUS, sides=16):
    angle=phase+np.arange(sides)*2*math.pi/sides
    return np.column_stack((center[0]+radius*np.cos(angle),
                            center[1]+radius*np.sin(angle)))


def phase_rasters(center, radius=SOURCE_RADIUS, sides=16,all_cyclic_aliases=False):
    """Yield unique integer polygons and representative phase/event metadata.

    Include every open phase interval plus boundary event configurations.
    Vertices at an analytic event are snapped only at1e-10sourcepixel to
    compensate for transcendental root roundoff. No image-gray slack is used.
    The returned coordinates are source coordinates BEFORE vertical flip.
    all_cyclic_aliases=True also retains all16 cyclic edge draw orders. An
    exact gray compatibility test must retain those orders: repeated rounded
    AA blends need not commute. The default is a cheaper geometry diagnostic.
    """
    period=2*math.pi/sides
    events=[0.,period]
    for axis in range(2):
        c=float(center[axis])
        for integer in range(math.ceil(c-radius),math.floor(c+radius)+1):
            z=(integer-c)/radius
            base=math.acos(z) if axis==0 else math.asin(z)
            roots=(base,-base) if axis==0 else (base,math.pi-base)
            for j in range(sides):
                for root in roots:
                    value=(root-j*period)%(2*math.pi)
                    if value<=period:events.append(value)
    events=sorted(events)
    merged=[]
    for event in events:
        if not merged or event-merged[-1]>1e-12:merged.append(event)
    probes=[(q,'event')for q in merged]
    probes += [((a+b)*.5,'open_interval')for a,b in zip(merged,merged[1:]) if b>a]
    seen=set()
    for phase,kind in probes:
        v=polygon_vertices(center,phase,radius,sides)
        if kind=='event':
            near=abs(v-np.rint(v))<1e-10
            v=np.where(near,np.rint(v),v)
        vertices=tuple(map(tuple,np.trunc(v).astype(int)))
        for shift in range(sides if all_cyclic_aliases else 1):
            shifted=vertices[shift:]+vertices[:shift]
            if shifted in seen:continue
            seen.add(shifted)
            yield dict(vertices=shifted,phase=phase+shift*period,kind=kind,
                       fixed_center=tuple(map(float,center)),phase_period=period,
                       cyclic_order_aliases_retained=all_cyclic_aliases)


def check():
    """Meaningful sampling regression of event enumeration, not proof."""
    rng=np.random.default_rng(7148);checks=0;counts=[]
    for center in ((500.,200.),(371.234,493.892),(-.2,10.7)):
        rasters=list(phase_rasters(center,all_cyclic_aliases=True));known={q['vertices']for q in rasters}
        counts.append(len(known))
        for phase in rng.uniform(0,2*math.pi,2000):
            direct=tuple(map(tuple,np.trunc(polygon_vertices(center,phase)).astype(int)))
            assert direct in known
            checks+=1
    return dict(status='PASS',direct_phase_checks=checks,unique_rasters=counts,
                coverage='FIXED_CENTER_NUMERICAL_EVENT_ENUMERATION',
                continuous_center_coverage=False,gray_tolerance=0,
                model_ticks=0,native_actions=0)


if __name__=='__main__':
    import json
    print(json.dumps(check()))
