"""A fixed circular road must not change curvature when its near crop moves."""
from pathlib import Path
import json,sys,time,math
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def legacy(points):
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    t=np.gradient(points,arc,axis=0);d=np.gradient(t,arc,axis=0)
    return np.abs(t[:,0]*d[:,1]-t[:,1]*d[:,0])/np.maximum(np.linalg.norm(t,axis=1)**3,1e-6)


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();errors=[];jumps=[]
    for radius in (12.,18.,28.):
      for mirror in (-1,1):
        s=3.5*np.arange(12);points=np.column_stack((mirror*radius*(np.cos(s/radius)-1),radius*np.sin(s/radius)))
        old=legacy(points);new=a.observed_reference_curvature(points)
        errors.append(float(np.max(abs(new-1/radius))));assert errors[-1]<1e-12
        cropped=points[1:];old_crop=legacy(cropped);new_crop=a.observed_reference_curvature(cropped)
        jump=abs(float(old[2]-old_crop[1]));jumps.append(jump);assert jump>.005
        assert abs(new[2]-new_crop[1])<1e-12
        # The unchanged q153/curvature formula receives a stable input at
        # the same physical point; no force or controller threshold is changed.
        assert abs(math.sqrt(153/new[2])-math.sqrt(153/new_crop[1]))<1e-9
    for points in (np.array([[0.,0.],[0.,3.5],[0.,7.]]),np.array([[0.,0.],[0.,1.],[0.,7.],[0.,10.]])):
        assert np.max(a.observed_reference_curvature(points))==0.
    result=dict(status='PASS',circle_cases=len(errors),max_geometric_curvature_error_per_m=max(errors),
        legacy_same_point_near_crop_curvature_jumps_per_m=jumps,geometric_same_point_near_crop_jump_per_m=0.,
        model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,
        limitation='Local3point geometry estimator; exact for finite circular samples, not a universal bound for noisy pixels or variable curvature.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
