"""Finite full-mesh risk checks for plain-edge anchor recovery, public rasters only."""
from pathlib import Path
import sys,json,time
import numpy as np,cv2
from retry.painted_band_check import scene,a
from retry.runtime598_diagnostic import dump
out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[]
for radius in (12.,18.,28.):
 for phase in (-.2,.2):
  for mirror in (-1,1):
   for variable in (False,True,'abrupt','reversing'):
    for paint in ('alternating','white','red'):
     image,truth=scene(radius,phase,mirror,variable,paint_mode=paint);observer=a.Agent();observer.calls=1;observer.last_root=object();observer.distance=100.;observer.speed=30.
     try:geometry,_,_,_=observer._map(image)
     except RuntimeError as exc:
      records.append(dict(radius=radius,phase=phase,mirror=mirror,variable=variable,paint=paint,status='UNSUPPORTED',reason=str(exc)));continue
     outside=[];N=0
     for poly,g in geometry.roads:
      # Vertices, edge midpoints and centroids sample every convex patch.
      points=np.vstack([poly,(np.array(poly)+np.roll(poly,-1,axis=0))*.5,np.mean(poly,axis=0)])
      for point in points:
       N+=1;distance=max(cv2.pointPolygonTest(t,(float(point[0]),float(point[1])),True) for t in truth)
       if distance<-1e-6:outside.append(dict(point=point,outside_m=-distance))
     records.append(dict(radius=radius,phase=phase,mirror=mirror,variable=variable,paint=paint,status='PASS' if not outside else 'FAIL',patches=len(geometry.roads),samples=N,outside=outside,raw_anchor_edges=observer.uncertainty['raster_raw_anchor_edges_refined']))
result=dict(status='PASS' if not any(v['status']=='FAIL' for v in records) else 'FAIL',cases=len(records),records=records,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,scope='Full observed mesh of144 publicly rendered physical turning-road/curb rasters. Finite vertices/midpoints/centroid checks, not a universal bound.')
dump(out,result);print({k:v for k,v in result.items() if k!='records'});print('fails',[(v['radius'],v['phase'],v['mirror'],v['variable'],v['paint'],len(v.get('outside',[]))) for v in records if v['status']=='FAIL']);print('new measurements',sum(v.get('raw_anchor_edges',0) for v in records))

assert result["status"]=="PASS","PHYSICAL_ROAD_OUTSIDE_SAMPLES"
assert sum(v.get("raw_anchor_edges",0) for v in records)>0,"NONVACUOUS_RAW_EDGE_RECOVERY"
