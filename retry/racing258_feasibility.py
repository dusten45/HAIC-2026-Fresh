"""Numerical geometric projection for an unexecuted fixed-solver candidate.

No radius/speed/follower changes. Used once on0.384mm obstacle-margin residual.
"""
import numpy as np
from retry.racing258_plan import geometry,basis,obstacle_clearance,profile


def project(snapshot,plan):
    center,normal,obstacles,radii=geometry(snapshot);B,_,_=basis(center);old=np.asarray(plan['coefficients']);theta=old.copy();bound=40/6-1.4-.35;calls=0
    def clear(t):
        nonlocal calls;calls+=1;return obstacle_clearance(center+normal*(B@t)[:,None],obstacles,radii)
    for _ in range(3):
        c=clear(theta)
        if c.min()>=0:break
        j=int(np.argmin(c));gradient=[]
        for k in range(16):
            plus=theta.copy();minus=theta.copy();plus[k]+=1e-4;minus[k]-=1e-4;gradient.append((clear(plus)[j]-clear(minus)[j])/2e-4)
        g=np.asarray(gradient);theta=np.clip(theta+g*((-c[j]+1e-4)/max(g@g,1e-12)),-bound,bound)
    line=center+normal*(B@theta)[:,None];c=clear(theta);p=profile(line,plan['model']);assert c.min()>=0 and abs(p['curvature']).max()<=np.tan(.4)/3.24
    return dict(line=line,coefficients=theta,profile=p,clearance=c,geometry_evaluations=calls,max_coefficient_change=float(abs(theta-old).max()))
