"""A continuous forward transition must not start from a quantized future node."""
from pathlib import Path
import json,sys,time,math
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time()
    points=np.column_stack((np.zeros(8),-2.+3.5*np.arange(8)))
    arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
    before=np.array([0.,-.08]);after=np.array([0.,.9])
    old=float(arc[np.argmin(np.linalg.norm(points-before,axis=1))])
    start=a.observed_reference_progress(points,arc,before)
    end=a.observed_reference_progress(points,arc,after)
    assert end-old<-.5 and abs(end-start-.98)<1e-12
    errors=[]
    for angle in (-2.,-.3,.7,2.8):
        r=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
        offset=np.array([8.,-4.]);p=points@r.T+offset
        actual=a.observed_reference_progress(p,arc,before@r.T+offset)
        errors.append(abs(actual-start));assert errors[-1]<1e-12
    # No rounding jumps on either side of a node Voronoi boundary.
    starts=[a.observed_reference_progress(points,arc,[0.,y]) for y in (-.250001,-.249999)]
    assert abs(starts[1]-starts[0]-2e-6)<1e-12
    result=dict(status='PASS',nearest_node_false_backward_delta_m=end-old,
        continuous_forward_delta_m=end-start,rigid_transform_max_error_m=max(errors),
        node_boundary_progress_change_m=starts[1]-starts[0],model_ticks=0,native_actions=0,
        CPU_s=time.process_time()-cpu,scope='Original core.project, observed finite polyline only; no force threshold/chooser/controller change.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
