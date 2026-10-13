"""Two observed-frame motion-aligned raster blend for road routing only.

HUD, car region and current obstacle detections remain current-frame inputs.
Deterministic similarity fit has no GT, retained plan or control-gain change.
"""
import cv2
import numpy as np
from retry.connected_agent import connected_route

LAST={}


def route(previous,current,obstacles,speed=0.,previous_steer=0.):
    LAST.clear();LAST.update(used=False,road_mask_changed_pixels=0)
    fused=current
    if not np.array_equal(previous,current):
        prev=np.rint(previous*255).astype(np.uint8);now=np.rint(current*255).astype(np.uint8)
        mask=np.ones((84,84),np.uint8)*255;mask[61:]=0;mask[50:61,34:51]=0
        points=cv2.goodFeaturesToTrack(prev,100,.02,4,mask=mask)
        if points is not None and len(points)>=4:
            nextpoints,status,_=cv2.calcOpticalFlowPyrLK(prev,now,points,None,winSize=(11,11),maxLevel=2);valid=status[:,0]!=0
            if valid.sum()>=4:
                p=points[valid,0].astype(float);q=nextpoints[valid,0].astype(float);A=np.zeros((2*len(p),4));A[::2]=np.c_[p[:,0],-p[:,1],np.ones(len(p)),np.zeros(len(p))];A[1::2]=np.c_[p[:,1],p[:,0],np.zeros(len(p)),np.ones(len(p))];a,b,tx,ty=np.linalg.lstsq(A,q.ravel(),rcond=None)[0];T=np.asarray([[a,-b,tx],[b,a,ty]],float)
                if np.isfinite(T).all() and .8<=a*a+b*b<=1.2:
                    aligned=cv2.warpAffine(previous,T,(84,84),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0);coverage=cv2.warpAffine(np.ones((84,84),np.float32),T,(84,84),flags=cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
                    region=(mask>0)&(coverage==1);fused=current.copy();fused[region]=.5*(current[region]+aligned[region]);raw=(current>.32)&(current<.47);mix=(fused>.32)&(fused<.47);LAST.update(used=True,road_mask_changed_pixels=int(np.sum((raw!=mix)&region)),tracked_points=int(valid.sum()))
    assert np.array_equal(fused[61:],current[61:])
    return connected_route(fused,obstacles,speed=speed,previous_steer=previous_steer)
