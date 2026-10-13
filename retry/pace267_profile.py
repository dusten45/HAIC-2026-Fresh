"""Eight positive pace knots on normalized arc; smooth bounded periodic interpolation."""
import numpy as np

def multipliers(knots,ds):
    knots=np.asarray(knots,np.float64);ds=np.asarray(ds,np.float64)
    assert knots.shape==(8,) and np.all((knots>=1)&(knots<=2)) and np.all(ds>0)
    if np.all(knots==knots[0]):return np.full(len(ds)+1,knots[0],np.float64)
    y=np.log(knots);d=np.roll(y,-1)-y;previous=np.roll(d,1);m=np.zeros(8);mask=previous*d>0;m[mask]=2*previous[mask]*d[mask]/(previous[mask]+d[mask])
    s=np.r_[0,np.cumsum(ds)];u=s/s[-1]*8;i=np.floor(u).astype(int)%8;t=u-np.floor(u);j=(i+1)%8
    value=(2*t**3-3*t*t+1)*y[i]+(t**3-2*t*t+t)*m[i]+(-2*t**3+3*t*t)*y[j]+(t**3-t*t)*m[j]
    result=np.exp(value);assert result.min()>=1-1e-12 and result.max()<=2+1e-12
    return np.clip(result,1,2)
