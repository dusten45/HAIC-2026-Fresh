"""Public synthetic direction/coordinate counterexamples; no runtime rollout."""
import json,math,sys,time
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time()
    raw=np.array([[0.,-2.],[-.2,-1.],[0.,0.],[-1.,1.],[-2.,2.],[-3.,3.]])
    curve=np.array([[-2.,3.1],[-2.5,4.],[-3.,5.],[-3.5,6.],[-4.,7.],[-4.5,8.]])
    previous=np.vstack(([-1.,1.],curve,[-5.,9.]))
    road=np.ones((84,84),np.uint8);blocked=np.zeros((84,84),bool)
    nearest=int(np.argmin(np.linalg.norm(raw-curve[0],axis=1)))
    assert float((raw[nearest]-raw[nearest-1])@(curve[0]-raw[nearest]))<0.
    cases=[]
    for angle in (-.8,0.,.7,2.7):
        rotation=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
        offset=np.array([1.,8.])
        rr=raw@rotation.T+offset;cc=curve@rotation.T+offset;pp=previous@rotation.T+offset
        for reverse in (False,True):
            run=cc[::-1] if reverse else cc
            samples=[(*point,i*.05) for i,point in enumerate(run)]
            result,info=a.reference_from_observed_width(rr,[dict(points=samples)],road,blocked,pp)
            assert info['observed_width_reference_used'] and info['reference_backward_joins_rejected']>=1,(angle,reverse,info)
            expected=np.vstack((raw[:5],curve))@rotation.T+offset
            assert result.shape==expected.shape and np.max(np.linalg.norm(result-expected,axis=1))<1e-10
            incoming=result[4]-result[3];join=result[5]-result[4];outgoing=result[6]-result[5]
            assert min(float(incoming@join),float(join@outgoing),float(incoming@outgoing))>=0.
            cases.append(dict(angle_rad=angle,reversed_sample_order=reverse))
    samples=[(*point,i*.05) for i,point in enumerate(curve)]
    # Neither an unsupported retained prefix nor a grass/obstacle join may
    # be bypassed by trying a different raw prefix endpoint.
    negatives=[]
    for name in ('unsupported_prefix','grass_join','blocked_join'):
        mask=road.copy();veto=blocked.copy()
        if name=='unsupported_prefix':
            x=int(round(a.IMAGE_ORIGIN_X+1.3608*raw[0,0]));y=int(round(a.IMAGE_ORIGIN_Y-1.701*raw[0,1]));mask[y,x]=0
        else:
            top=int(math.floor(a.IMAGE_ORIGIN_Y-1.701*2.9));bottom=int(math.ceil(a.IMAGE_ORIGIN_Y-1.701*2.3))
            if name=='grass_join':mask[top:bottom+1,:]=0
            else:veto[top:bottom+1,:]=True
        result,info=a.reference_from_observed_width(raw,[dict(points=samples)],mask,veto,previous)
        assert not info['observed_width_reference_used'] and np.array_equal(result,raw),(name,info,result)
        negatives.append(name)
    # Two unresolved opposite-direction branches within current localization
    # support cannot establish a direction correspondence.
    ambiguous=np.array([[-.2,0.],[-.2,4.],[-.2,8.],[.2,8.],[.2,4.],[.2,0.]])
    current=np.array([[0.,y] for y in range(1,8)])
    assert a.observed_reference_run_direction(current,ambiguous)==0
    result,info=a.reference_from_observed_width(np.array([[0.,-1.],[0.,0.]]),
        [dict(points=[(*p,i*.05) for i,p in enumerate(current)])],road,blocked,ambiguous)
    assert not info['observed_width_reference_used'] and info['reference_ambiguous_direction_runs']==1
    negatives.append('opposite_branch_correspondence')
    # Existing lattice phase ambiguity is still rejected; this correction
    # never makes a phase from only the agreeing subset of old nodes.
    dense=np.array([[0.,y] for y in np.linspace(0.,21.,100)])
    old=np.array([[0.,y] for y in (1.,4.5,8.,11.5,18.5)])
    _,info=a.observed_reference_lattice(dense,old)
    assert not info['reference_lattice_correspondence']
    negatives.append('lattice_station_ambiguity_unchanged')
    result=dict(status='PASS',legacy_nearest_join_direction_reversal=True,
        rigid_and_reversed_order_cases=cases,negatives=negatives,
        model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,
        scope='Public synthetic coordinates only; same original pavement/distance/lattice gates. No simulation or force/controller evaluation.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
