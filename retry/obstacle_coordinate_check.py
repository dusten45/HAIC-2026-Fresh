"""Public geometric counterexamples for finite-reference object coordinates."""
from pathlib import Path
import json,sys,time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
from observation_agent import observed_obstacle_coordinates


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();checks=[]
    def locate(points,center):
        points=np.asarray(points,float)
        arc=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))]
        # Tests include repeated nodes, so construct normals on valid segments.
        normals=np.tile([1.,0.],(len(points),1))
        return observed_obstacle_coordinates(points,arc,normals,center)
    legacy=[];corrected=[]
    for end in (14.,18.,22.,26.):
        for count in (5,9,17):
            points=np.column_stack([np.zeros(count),np.linspace(0,end,count)])
            s,lateral=locate(points,[1.,28.]);assert abs(s-28.)<1e-12 and abs(lateral-1.)<1e-12
            corrected.append(-2.8*np.exp(-.5*(s/16.)**2))
            legacy.append(-2.8*np.exp(-.5*(end/16.)**2))
    assert np.ptp(legacy)>.9 and np.ptp(corrected)<1e-12
    checks.append('straight_crop_and_sampling_invariance_12')
    for y in (-4.,3.,12.,28.):
        s,lateral=locate([[0,0],[0,8],[0,16]],[1,y])
        assert abs(s-y)<1e-12 and abs(lateral-1.)<1e-12
    checks.append('interior_and_both_endpoint_coordinates')
    points=np.array([[0.,0.],[0.,8.],[0.,16.]])
    for angle in (-2.,-.7,.2,1.4):
        r=np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
        offset=np.array([11.,-7.]);p=points@r.T+offset
        normal=np.tile(np.array([1.,0.])@r.T,(3,1))
        s,lateral=observed_obstacle_coordinates(p,np.array([0.,8.,16.]),normal,np.array([1.,28.])@r.T+offset)
        assert abs(s-28.)<1e-12 and abs(lateral-1.)<1e-12
    checks.append('rigid_transform_4')
    s,lateral=locate([[0,0],[0,0],[0,8],[0,16],[0,16]],[1,28])
    assert abs(s-28)<1e-12 and abs(lateral-1)<1e-12
    checks.append('duplicate_endpoint_nodes')
    # The infinite endpoint ray is closer, but the finite interior segment
    # must establish correspondence before any endpoint residual is applied.
    p=np.array([[0.,0.],[0.,10.],[5.,10.],[5.,0.]])
    arc=np.array([0.,10.,15.,25.]);n=np.array([[1.,0.],[1.,0.],[-1.,0.],[-1.,0.]])
    s,_=observed_obstacle_coordinates(p,arc,n,[1.,-5.]);assert s<0.
    s,_=observed_obstacle_coordinates(p,arc,n,[4.,5.]);assert abs(s-20.)<1e-12
    checks.append('finite_segment_before_endpoint_ray')
    result=dict(status='PASS',checks=checks,legacy_crop_field_range_m=float(np.ptp(legacy)),
        corrected_crop_field_range_m=float(np.ptp(corrected)),reference_nodes_added=0,
        native_actions=0,model_ticks=0,CPU_s=time.process_time()-cpu,
        limitation='Endpoint tangent coordinates are local estimates, not evidence of unseen curved road.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
