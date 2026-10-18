"""Conservative floating-point classification only; no safety/terminal limits here."""
import numpy as np


def near_risk(slack,band):
    slack=np.asarray(slack,dtype=np.float64);band=np.asarray(band,dtype=np.float64)
    guard=8*np.finfo(np.float64).eps*np.maximum(1.,np.maximum(abs(slack),abs(band)))
    return (~np.isfinite(slack))|(~np.isfinite(band))|(slack<=band+guard)


def reserve_for(slack,band):
    slack=np.asarray(slack,dtype=np.float64)
    return np.where(near_risk(slack,band),.25*np.maximum(slack,0.),0.)
