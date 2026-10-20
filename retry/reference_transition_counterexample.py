"""Public analytic reference counterexamples; no Agent act, model or native run."""
from pathlib import Path
import sys,time,json,math
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def ordered_intervals(stations,error):
    """Diagnostic feasibility of uncertain forward stations, not production rule."""
    lower=-float('inf')
    for station in stations:
        lower=max(lower,float(station)-error)
        if lower>float(station)+error:return False
    return True


def main():
    cpu=time.process_time();pixel=math.hypot(1/1.3608,1/1.701);records=[]
    radius=30.;half=40./6.;ys=np.arange(0.,23.,.25)
    center_x=-radius+np.sqrt(radius**2-ys**2)
    left=-radius+np.sqrt((radius-half)**2-ys**2)
    right=-radius+np.sqrt((radius+half)**2-ys**2)
    raw=np.c_[(left+right)/2,ys];truth=np.c_[center_x,ys]
    radial=np.linalg.norm(raw-np.array([-radius,0.]),axis=1)
    assert np.all((radius-half<=radial)&(radial<=radius+half))
    deviation=np.linalg.norm(raw-truth,axis=1);curvature=a.observed_reference_curvature(raw)
    assert max(deviation)>pixel and max(abs(curvature-1/radius))>.01
    # Same physical lane; clipping a cross-section moves its midpoint farther.
    clipped=np.c_[(np.maximum(left,-8.)+right)/2,ys]
    assert np.max(np.linalg.norm(clipped-truth,axis=1))>max(deviation)
    records.append(dict(case='circular_asphalt_midpoint_is_not_centerline',all_midpoints_on_actual_asphalt=True,max_same_y_centerline_error_m=float(max(deviation)),max_nearest_circle_centerline_distance_m=float(max(abs(radial-radius))),max_curvature_error_per_m=float(max(abs(curvature-1/radius))),partial_crosssection_max_error_m=float(np.max(np.linalg.norm(clipped-truth,axis=1)))))
    # S bend from the public fixed half-width normal corridor. Its horizontal
    # sections are independent of the parameterized physical centerline.
    sy=np.linspace(-8,38,1001);sx=4*np.sin(sy/7);sp=np.c_[sx,sy];t=np.c_[(4/7)*np.cos(sy/7),np.ones_like(sy)];n=np.c_[t[:,1],-t[:,0]]/np.linalg.norm(t,axis=1)[:,None];poly=np.vstack((sp+half*n,(sp-half*n)[::-1]));midpoints=[];actual=[]
    for y in np.linspace(0,30,121):
        hits=[]
        for p,q in zip(poly,np.roll(poly,-1,axis=0)):
            if (p[1]<=y<q[1])or(q[1]<=y<p[1]):hits.append(float(p[0]+(y-p[1])*(q[0]-p[0])/(q[1]-p[1])))
        assert len(hits)==2;midpoints.append(((min(hits)+max(hits))/2,y));actual.append((4*math.sin(y/7),y))
    err=np.linalg.norm(np.asarray(midpoints)-actual,axis=1)
    assert max(err)>.1
    records.append(dict(case='S_normal_corridor_scanline_bias',max_row_parameter_centerline_error_m=float(max(err)),scope='At same y station; reference may remain inside physical corridor.'))
    # Measured CURRENT points have bounded localization error around an
    # underlying monotonically observed straight line. Central tangents stay
    # forward although exact nearest stations contain small reversals.
    stations=np.arange(0,10.01,.5);noise=np.where(np.arange(len(stations))%2,.4,-.4);measured=stations+noise
    previous=np.c_[np.zeros(81),np.linspace(-5,15,81)];clean=np.c_[np.zeros(len(stations)),stations];jitter=np.c_[np.zeros(len(measured)),measured]
    backtrack=np.r_[np.arange(0,8.01,.5),np.arange(7.5,0.,-.5)];back=np.c_[np.zeros(len(backtrack)),backtrack]
    for mirror in (-1,1):
      for angle in (0.,.7):
        rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])@np.diag([mirror,1.]);shift=np.array([2.,-1.]);transform=lambda p:p@rot.T+shift
        dclean=a.observed_reference_run_direction(transform(clean),transform(previous));djitter=a.observed_reference_run_direction(transform(jitter),transform(previous));dback=a.observed_reference_run_direction(transform(back),transform(previous))
        assert dclean==1 and djitter==0 and dback==0
        assert ordered_intervals(measured,pixel) and not ordered_intervals(backtrack,pixel)
        records.append(dict(case='localization_order_vs_real_backtrack',mirror=mirror,rotation=angle,clean_direction=dclean,jitter_direction=djitter,actual_backtrack_direction=dback,max_localization_error_m=float(max(abs(noise))),min_measured_station_step_m=float(min(np.diff(measured))),jitter_forward_interval_feasible=True,backtrack_forward_interval_feasible=False))
    # A forward dense run can approach a coarse INTERNAL corner from its
    # outgoing tangent: two measured stations exactly clamp to that vertex.
    corner=np.array([[0.,-5.],[0.,0.],[5.,0.],[10.,0.]])
    tie=np.c_[[-.6,-.3,0.,.4,1.,2.,3.],np.full(7,-.2)]
    duplicate=np.c_[[-.6,-.3,-.3,.4,1.,2.,3.],np.full(7,-.2)]
    real_reverse=np.c_[[-.6,-.3,.4,1.,.7,2.,3.],np.full(7,-.2)]
    no_net_progress=np.c_[[-.6,-.4,-.2],np.full(3,-.2)]
    parallel=np.array([[-2.,-.2],[4.,-.2],[4.,.2],[-2.,.2]])
    forward=np.c_[np.linspace(-1,3,9),np.zeros(9)]
    for mirror in (-1,1):
      for angle in (0.,.7):
        rot=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])@np.diag([mirror,1.]);shift=np.array([2.,-1.]);transform=lambda p:p@rot.T+shift
        outcomes={name:a.observed_reference_run_direction(transform(points),transform(old))
          for name,points,old in [('internal_vertex_forward',tie,corner),('internal_vertex_reverse',tie[::-1],corner),('zero_duplicate',duplicate,corner),('actual_negative_station',real_reverse,corner),('all_clamped_no_net_progress',no_net_progress,corner),('opposite_parallel_ambiguity',forward,parallel)]}
        assert outcomes==dict(internal_vertex_forward=1,internal_vertex_reverse=-1,zero_duplicate=0,actual_negative_station=0,all_clamped_no_net_progress=0,opposite_parallel_ambiguity=0),outcomes
        records.append(dict(case='exact_internal_vertex_clamp',mirror=mirror,rotation=angle,outcomes=outcomes,scope='Only canonical internal-vertex equality with physically forward displacement is accepted. Negative station steps, stationary duplicates, opposite parallel matches and no net advance remain rejected.'))
    # Material vetoes stay independent of direction. These tests call the
    # existing width selector, not a proposed future validator.
    line=np.c_[np.zeros(20),np.linspace(0,15,20)];curve=dict(points=[(float(x),float(y),float(y)/30)for x,y in line]);asphalt=np.ones((84,84),np.uint8);clear=np.zeros((84,84),bool)
    for name,road,blocked,expected in [('visible_asphalt',asphalt,clear,True),('current_grass',np.zeros_like(asphalt),clear,False),('current_object',asphalt,np.ones_like(clear),False)]:
        _,info=a.reference_from_observed_width(line,[curve],road,blocked,None);assert info['observed_width_reference_used']==expected;records.append(dict(case=name,width_reference_used=expected))
    result=dict(status='PUBLIC_COUNTEREXAMPLES_CONFIRMED',cases=records,model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,conclusion='Asphalt containment and forward local direction do not establish lane centerline or stable curvature. Exact station monotonicity can reject bounded localization jitter; monotone station-interval feasibility separates this example from large real backtrack. This test file does not modify production. Narrow internal-vertex equality is tested separately; bounded negative jitter remains rejected.',limitations='Analytic/synthetic finite cases, not a true-lane certificate. Station intervals alone cannot resolve parallel branches, mixed tangent signs, or direction ambiguities. Material veto tests do not assert fallback validity.')
    assert result['CPU_s']<30
    if len(sys.argv)>1:
        out=Path(sys.argv[1]);assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
