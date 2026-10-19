"""Observed row-union topology and public raster geometry counterexamples."""
from pathlib import Path
import sys,json,time
import cv2,numpy as np
from retry.painted_band_check import scene
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a
import runtime598 as core


def exposed(roads,boundary):
    def inside(p):return any(core.inside(p,poly) for poly,_ in roads)
    for first,last in boundary:
        first=np.asarray(first);last=np.asarray(last);d=last-first
        if np.linalg.norm(d)<1e-12:return False
        normal=np.array([-d[1],d[0]])/np.linalg.norm(d);mid=(first+last)*.5
        if inside(mid+1e-6*normal)==inside(mid-1e-6*normal):return False
    return True


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time()
    rows=[(float(y),[(-16.,-8.),(8.,16.)] if y<10 else [(-16.,16.)]) for y in range(21)]
    roads,boundary=a.strip_union_mesh(rows,1.);assert exposed(roads,boundary)
    observer=a.Agent();scene0=core.Scene(roads,boundary,[]);root=observer._root(scene0,0.);root=core.replace(root,center=(-12.,10.+observer.com[1]));scene_margin=scene0.margin(root)
    brute=min(core.polygon_distance(poly,edge) for poly in core.polygons(root) for edge in boundary)
    assert scene_margin==brute and scene_margin>.5
    for intervals in [[(-5.,5.)],[(-5.,1.),(-1.,5.)],[(-5.,-1.),(1.,5.)]]:
        mesh,edge=a.strip_union_mesh([(0.,intervals),(1.,intervals),(2.,intervals)],1.);assert exposed(mesh,edge)
    records=[]
    for radius in (12.,18.,28.):
      for phase in (-.2,.2):
       for mirror in (-1,1):
        for variable in (False,True,'abrupt','reversing'):
         for paint in ('alternating','white','red'):
          image,truth=scene(radius,phase,mirror,variable,paint_mode=paint);observer=a.Agent();observer.calls=1
          geometry,_,_,_=observer._map(image);bad=[]
          for first,last in geometry.boundary:
            for point in [first,tuple((first[j]+last[j])*.5 for j in range(2))]:
              distance=max(cv2.pointPolygonTest(poly,point,True) for poly in truth)
              if distance< -1e-5:bad.append(dict(point=point,outside_m=-distance))
          records.append(dict(radius=radius,phase=phase,mirror=mirror,variable=variable,paint=paint,bad=bad,roads=len(geometry.roads),edges=len(geometry.boundary)))
    failures=[r for r in records if r['bad']]
    result=dict(status='PASS' if not failures else 'FAIL',cases=len(records),physical_outside_cases=len(failures),outside_samples=sum(len(r['bad']) for r in records),max_outside_m=max([p['outside_m'] for r in records for p in r['bad']]+[0.]),logical_topology_cases=4,all_internal_interfaces_excluded=True,U_fixture_full_car_margin_m=scene_margin,callback_equals_brute=True,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,records=records,scope='Finite public geometry/raster cases; not a universal observation bound.')
    out.write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2));assert result['status']=='PASS'


if __name__=='__main__':main()
