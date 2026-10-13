"""Verbatim256paired math; source constants unchanged."""
import numpy as np

def paired(action,speed):
    K=.06*(max(0.,float(speed))/.54+5);d=min(float(action[2]),float(action[1])/K);out=np.asarray(action,np.float32).copy();out[1:]=np.clip([float(action[1])-K*d,float(action[2])-d],0,1).astype(np.float32)
    return out,K,d
