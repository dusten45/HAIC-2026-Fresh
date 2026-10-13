"""Four fixed paired parameter probes and one bounded ARS-style update."""
import numpy as np


def rms(theta,covariance):
    return float(np.sqrt(max(0.,np.trace(theta.T@covariance@theta)/2)))


def draw(covariance,seed=247):
    directions=np.random.default_rng(seed).normal(size=(4,17,2))
    probes=[]
    for direction in directions:
        radius=rms(direction,covariance)
        assert radius>0
        delta=direction*(.2/radius)
        probes.extend([delta,-delta])
    return np.asarray(probes)


def update(probes,mean_returns,covariance):
    returns=np.asarray(mean_returns,float);sigma=float(returns.std())
    difference=returns[::2]-returns[1::2]
    gradient=np.zeros((17,2)) if sigma==0 else np.einsum('i,ijk->jk',difference/sigma,probes[::2])/4
    radius=rms(gradient,covariance)
    scale=1. if radius<=.2 else .2/radius
    theta=gradient*scale
    return theta,dict(return_population_std=sigma,paired_differences=difference.tolist(),raw_update_latent_RMS=radius,scale=scale,final_latent_RMS=rms(theta,covariance),zero_handling='exact zero if return std or direction sum zero')
