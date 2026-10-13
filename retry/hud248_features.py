"""Six quantized current-pixel HUD proxies; no simulator access or decoder fit.

Renderer places7..10: 0.01*wheel omega; place20: -10*front joint angle;
place30: -0.8*hull yaw rate. RGB96 becomes grayscale84; antialiasing,
adjacent-bar leakage and viewport clipping prevent exact state reconstruction.
"""
import numpy as np

NAMES=['wheel0_omega_HUD_proxy','wheel1_omega_HUD_proxy',
       'wheel2_omega_HUD_proxy','wheel3_omega_HUD_proxy',
       'front_joint_angle_HUD_proxy','yaw_rate_HUD_proxy']


def decode(image):
    image=np.asarray(image)
    assert image.shape==(84,84)
    # s=h=84/40=2.1. HUD baseline y=81.9; positive wheel bars go up.
    # RGB->GRAY full-color references: blue29/255, rear blue+red44/255.
    values=[]
    for column,color in zip([16,18,20,22],[29/255,29/255,44/255,44/255]):
        bar=image[74:84,column].astype(np.float64)
        signed_extent=(bar[:8].sum()-bar[8:].sum())/color
        values.append(signed_extent/(2.1*.01))
    for start,end,anchor,color,scale in [(31,53,42,150/255,-10.),(54,75,63,76/255,-.8)]:
        region=image[75:82,start:end].astype(np.float64)
        signs=np.where(np.arange(start,end)+.5<anchor,-1.,1.)
        signed_area=float((region*signs[None,:]).sum())/color
        displayed_value=signed_area/(2*2.1*2.1)
        values.append(displayed_value/scale)
    return np.asarray(values,np.float64)
