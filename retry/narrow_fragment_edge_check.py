"""Current raw road rays survive object-hole/flatness fragment narrowing."""
from pathlib import Path
import sys,json,time,inspect
import numpy as np,cv2
from retry.object_road_support_check import scene,a


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();events=[];records=[];original=a.recover_plain_run_edge;physical=None
    def record(image,y,index,direction,blocked,paint,*args):
        value=original(image,y,index,direction,blocked,paint,*args)
        local=inspect.currentframe().f_back.f_locals
        width=local.get('se',100)-local.get('ss',0)
        if value is not None and width<8:
            point=((value+direction*.35*1.3608-a.IMAGE_ORIGIN_X)/1.3608,(a.IMAGE_ORIGIN_Y-y)/1.701)
            gap=cv2.pointPolygonTest(physical,point,True)
            assert gap>=-1e-6,'NARROW_FRAGMENT_EDGE_OUTSIDE_ROAD'
            events.append(dict(geometry_fragment_pixels=width,raw_interval_pixels=args[0][1]-args[0][0],physical_margin_m=gap))
        return value
    a.recover_plain_run_edge=record
    for angle in (-.3,0.,.3):
     for offset in (-2.,-1.5,1.5,2.):
      for phase in (.1,.6):
        image,physical=scene(angle,offset,phase,102,None);observer=a.Agent();observer.calls=1;observer.last_root=object();observer.speed=30.;observer.distance=100.
        try:geometry,_,_,_=observer._map(image)
        except RuntimeError as exc:
            records.append(dict(angle=angle,offset=offset,phase=phase,supported=False));continue
        samples=0;bad=0
        for poly,mu in geometry.roads:
            points=np.vstack([poly,(np.asarray(poly)+np.roll(poly,-1,axis=0))*.5,np.mean(poly,axis=0)])
            for point in points:samples+=1;bad+=cv2.pointPolygonTest(physical,tuple(point),True)<-1e-6
        assert not bad
        records.append(dict(angle=angle,offset=offset,phase=phase,supported=True,mesh_samples=samples,outside=bad))
    a.recover_plain_run_edge=original
    assert events,'NONVACUOUS_NARROW_FRAGMENT_COUNTEREXAMPLE'
    # Required inner plateau samples must belong to the same raw run. The
    # material/blocked gates remain in force even for an apparent short ray.
    image,physical=scene(0.,-1.5,.1,102,None);blocked=np.ones((84,84),bool);paint=np.zeros((84,84),bool)
    assert original(image,35,30,1,blocked,paint,(30,35)) is None
    assert original(image,35,30,1,np.zeros((84,84),bool),paint,(30,31)) is None
    result=dict(status='PASS',cases=len(records),newly_tested_narrow_fragment_edges=len(events),all_inner_plateaus_in_raw_run=True,outside_samples=sum(r.get('outside',0) for r in records),negative_guards=2,events=events,records=records,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,scope='Public current orange objects on actual road polygons. Ray eligibility uses observed plateau containment rather than eroded geometry width; no collision exclusion removed.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('events','records')}))


if __name__=='__main__':main()
