"""Fixed observed geometry must not be redistributed by a remote crop edge."""
from pathlib import Path
import json,sys,time,math
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def circle(length,start=0.):
    s=np.linspace(start,length,10001)
    return np.column_stack((12*(np.cos(s/12)-1),12*np.sin(s/12)))


def profile(points):
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    t=np.gradient(points,arc,axis=0);second=np.gradient(t,arc,axis=0)
    curvature=np.abs(t[:,0]*second[:,1]-t[:,1]*second[:,0])/np.maximum(np.linalg.norm(t,axis=1)**3,1e-6)
    q=np.minimum(90**2,153/np.maximum(curvature,1e-6));q[-1]=0.
    for i in range(len(q)-2,-1,-1):q[i]=min(q[i],q[i+1]+90*(arc[i+1]-arc[i]))
    return math.sqrt(float(np.interp(5.,arc,q)))


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();old=[];new=[];grids=[]
    for length in (34.999999,35.000001):
        dense=circle(length);arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(dense,axis=0),axis=1))]
        sample=np.linspace(0,arc[-1],math.ceil(arc[-1]/3.5)+1)
        baseline=np.column_stack([np.interp(sample,arc,dense[:,j]) for j in range(2)])
        fixed,info=a.observed_reference_lattice(dense,[])
        old.append(profile(baseline));new.append(profile(fixed));grids.append(fixed)
        assert info['reference_lattice_used'] and info['reference_geometry_sample_step_m']==3.5
    assert abs(old[1]-old[0])>.5 and abs(new[1]-new[0])<1e-5
    assert np.max(np.linalg.norm(grids[0][:-2]-grids[1][:len(grids[0])-2],axis=1))<1e-6
    # A moved camera and a new near crop must reobserve the same physical
    # lattice, rather than anchor a fresh lattice at the camera's new crop.
    previous,_=a.observed_reference_lattice(circle(35.),[])
    angle=.12;r=np.array([[math.cos(angle),math.sin(angle)],[-math.sin(angle),math.cos(angle)]])
    origin=np.array([-.2,2.]);transported=(previous-origin)@r.T
    dense=(circle(38.,3.)-origin)@r.T
    fixed,info=a.observed_reference_lattice(dense,transported)
    assert info['reference_lattice_correspondence'] and info['reference_lattice_matches']>=3
    matched=info['reference_lattice_matches']
    # Current curve interpolation error is finite raster/curve arithmetic;
    # no transported point is copied into the returned current reference.
    errors=[float(np.min(np.linalg.norm(transported-p,axis=1))) for p in fixed[:-1]]
    assert max(errors)<1e-5
    # A foreign branch cannot establish a correspondence phase.
    _,wrong=a.observed_reference_lattice(dense,transported+100.)
    assert not wrong['reference_lattice_correspondence']
    # Object coordinates use dense observed support, not the final sampled
    # grid node, so adding a distant grid node cannot move the object anchor.
    fields=[]
    for length in (34.999999,35.000001):
        dense=circle(length);fixed,info=a.observed_reference_lattice(dense,[])
        stations=info['reference_lattice_phase_m']+3.5*np.arange(len(fixed))
        object_point=circle(40.)[-1]+[.3,.2]
        shifted=a.deform_observed_reference(fixed,dense,stations,[(object_point,1.6)])
        fields.append(shifted-fixed)
    field_error=float(np.max(np.linalg.norm(fields[0][:-2]-fields[1][:len(fields[0])-2],axis=1)))
    assert field_error<1e-5
    # Variable curvature under the public per3.5m heading-change bound; a
    # newly represented final chord cannot rescale an interior object's field.
    station=np.linspace(0.,50.,10001);heading=.04*station+.15*np.sin(.1*station)
    whole=np.cumsum(.005*np.column_stack((-np.sin(heading),np.cos(heading))),axis=0)
    whole_arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(whole,axis=0),axis=1))]
    variable_fields=[]
    object_point=whole[5000]+[1.,0.]
    for length in (34.999999,35.000001):
        ids=whole_arc<length;dense=np.vstack([whole[ids],[np.interp(length,whole_arc,whole[:,j]) for j in range(2)]])
        fixed,info=a.observed_reference_lattice(dense,[])
        stations=info['reference_lattice_phase_m']+3.5*np.arange(len(fixed))
        variable_fields.append(a.deform_observed_reference(fixed,dense,stations,[(object_point,1.6)])-fixed)
    variable_error=float(np.max(np.linalg.norm(variable_fields[0][:-2]-variable_fields[1][:len(variable_fields[0])-2],axis=1)))
    assert variable_error<1e-9
    result=dict(status='PASS',legacy_crop_speed_jump_m_s=abs(old[1]-old[0]),fixed_crop_speed_jump_m_s=abs(new[1]-new[0]),
        fixed_crop_object_field_jump_m=field_error,current_curve_lattice_error_m=max(errors),
        variable_curve_crop_object_field_jump_m=variable_error,
        matches=matched,foreign_branch_rejected=True,
        model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,
        limitation='Finite public curve tests; new support can legitimately change the terminal stop constraint. No universal reference/safety certificate.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
