"""Nearest valid pre-scale inverse for a frozen240 residual correction label."""
import numpy as np


def residual_delta(nominal,raw_residual,target,scales):
    nominal=np.asarray(nominal,float);raw=np.asarray(raw_residual,float);target=np.asarray(target,np.float32);scales=np.asarray(scales,float)
    pre=np.clip(nominal+np.clip(raw,-.5,.5),0,1);baseline=np.clip(pre*scales,0,1).astype(np.float32);delta=np.zeros(2)
    for j in range(2):
        if target[j]==baseline[j]:continue
        # Saturated final1 has preimage[1/scale,1]; project current pre onto it.
        q=float(np.clip(pre[j],1/scales[j],1)) if target[j]==1 else float(np.clip(float(target[j])/scales[j],0,1))
        if q==0:desired=min(raw[j],-nominal[j])
        elif q==1:desired=max(raw[j],1-nominal[j])
        else:desired=q-nominal[j]
        delta[j]=desired-raw[j]
    reconstructed=np.clip(np.clip(nominal+np.clip(raw+delta,-.5,.5),0,1)*scales,0,1).astype(np.float32)
    assert np.max(np.abs(reconstructed-target))<1e-6
    return delta
