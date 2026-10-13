"""Three road-common coefficients: curvature pressure, drive demand, brake demand."""
import numpy as np

def multipliers(coefficients,curvature,ds,model):
    beta=np.asarray(coefficients,np.float64);k=np.abs(np.asarray(curvature,np.float64));ds=np.asarray(ds,np.float64)
    assert beta.shape==(3,) and np.all(abs(beta)<=.2) and len(k)==len(ds) and np.all(ds>0)
    if np.all(beta==0):return np.full(len(ds)+1,1.5,np.float64)
    # Source400N per wheel; all-road/grip1, equal lateral axle load are assumptions.
    q=1.5*np.minimum(100.,np.sqrt(model['lateral_accel']/np.maximum(k,1e-6)))
    lateral=np.minimum(1600.,model['mass']*q*q*k)
    rear_remaining=np.sqrt(np.maximum(800.**2-(.5*lateral)**2,0))
    total_remaining=np.sqrt(np.maximum(1600.**2-lateral**2,0))
    drive=np.minimum(rear_remaining/(model['mass']+2*1.6/.54**2),80000/(q+2.7)/model['effective_mass'])
    brake=np.minimum(model['brake_accel'],total_remaining/model['mass'])
    requested=(np.roll(q,-1)**2-q*q)/(2*ds)
    positive=np.maximum(requested,0);negative=np.maximum(-requested,0)
    features=np.c_[lateral/1600.,positive/(positive+drive+1e-9),negative/(negative+brake+1e-9)]
    # Relative arc distances only, no absolute phase/road ID; fixed wheelbase smoothing.
    s=np.r_[0,np.cumsum(ds[:-1])];L=ds.sum();distance=abs(s[:,None]-s[None,:]);distance=np.minimum(distance,L-distance);weights=np.exp(-.5*(distance/3.24)**2)*ds[None,:];weights/=weights.sum(1)[:,None];features=weights@features
    pace=np.clip(1.5*np.exp(features@beta),1.,2.)
    return np.r_[pace,pace[0]]
