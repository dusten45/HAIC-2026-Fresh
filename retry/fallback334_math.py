"""Preregistered metric fallback; fixed rate integration, no fitted quantities."""
import math
import numpy as np
DT=.08
ANCHOR=np.array([41.542,62.4475])
PIXEL_LINEAR=np.diag([1.3608,-1.701])


def rotation(a):
    c,s=math.cos(a),math.sin(a);return np.array([[c,-s],[s,c]])


def transport(point,previous_yaw,current_yaw,current_speed):
    delta=DT*(previous_yaw+current_yaw)/2
    return rotation(-delta)@(np.asarray(point,float)-np.array([0.,current_speed*DT]))


def advance(hazards,direct,affine,previous_yaw,current_yaw,current_speed,enabled):
    predicted=[];lineage=[];transported=[]
    for index,(x,y,radius,age) in enumerate(hazards):
        if affine is None:
            if enabled:
                assert previous_yaw is not None
                x,y=map(float,transport([x,y],previous_yaw,current_yaw,current_speed))
            else:y-=current_speed*DT
        else:
            pixel=np.asarray(affine)@np.array([41.542+1.3608*x,62.4475-1.701*y,1.])
            x,y=(pixel[0]-41.542)/1.3608,(62.4475-pixel[1])/1.701
        transported.append([float(x),float(y),radius,age+1])
        if age<8 and abs(x)<=35 and -5<=y<=35:
            predicted.append([float(x),float(y),radius,age+1]);lineage.append(index)
    for di,(x,y,radius) in enumerate(direct):
        keep=[i for i,p in enumerate(predicted) if np.hypot(p[0]-x,p[1]-y)>2]
        predicted=[predicted[i] for i in keep];lineage=[lineage[i] for i in keep]
        predicted.append([x,y,radius,0]);lineage.append(-di-1)
    return predicted,lineage,transported


def validate():
    p=np.array([2.,9.]);a=.13;d=np.array([0.,1.4]);q=rotation(-a)@(p-d)
    assert np.allclose(rotation(a)@q+d,p,atol=1e-12)
    assert np.allclose(transport([0.,10.],1.,1.,0.),[10*math.sin(.08),10*math.cos(.08)],atol=1e-12)
    assert np.array_equal(transport([3.,8.],0.,0.,10.),np.array([3.,7.2]))
    assert np.array_equal(ANCHOR+PIXEL_LINEAR@np.zeros(2),ANCHOR)
    assert (PIXEL_LINEAR@np.array([0.,1.]))[1]<0
    assert np.allclose(np.linalg.solve(PIXEL_LINEAR,PIXEL_LINEAR@p),p,atol=1e-12)
    metric=rotation(-a);pixel=PIXEL_LINEAR@metric@np.linalg.inv(PIXEL_LINEAR)
    assert np.allclose(pixel@(PIXEL_LINEAR@p),PIXEL_LINEAR@(metric@p),atol=1e-12)
    assert not np.allclose(pixel.T@pixel,np.eye(2)) # anisotropic pixels
    return dict(passed=True,origin_pixel_flip_anisotropy_rotation_straight_inverse=True,delta_yaw='0.08*(previous_yaw+current_yaw)/2',body_displacement='(0,current_HUD_speed*.08)',no_speed_average=True,no_lateral_model=True)
