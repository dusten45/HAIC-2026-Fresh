"""Public reference geometry falsification; no simulator reset or actual case."""
from pathlib import Path
import sys,math,json,time
import numpy as np
import cv2
from retry.painted_band_check import scene
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def center_distance(point,line):
    p=np.asarray(point);first=line[:-1];delta=np.diff(line,axis=0)
    t=np.clip(np.sum((p-first)*delta,axis=1)/np.sum(delta*delta,axis=1),0.,1.)
    return float(np.min(np.linalg.norm(p-first-t[:,None]*delta,axis=1)))


def main():
    out=Path(sys.argv[1]);assert not out.exists();start=time.process_time();records=[]
    original=a.reference_from_observed_width
    for radius in (12.,18.,28.):
      for phase in (-.2,.2):
       for mirror in (-1,1):
        for variable in (False,True,'abrupt','reversing'):
         for paint_mode in ('alternating','white','red'):
          image,truth=scene(radius,phase,mirror,variable,paint_mode=paint_mode)
          line=np.vstack((truth[0][:2].mean(axis=0),[poly[2:].mean(axis=0) for poly in truth]))
          before=a.Agent();before.calls=1;after=a.Agent();after.calls=1
          try:
            a.reference_from_observed_width=lambda raw,*args:(raw,dict(observed_width_reference_used=False))
            old_scene,old,_,_=before._map(image)
            a.reference_from_observed_width=original
            new_scene,new,_,_=after._map(image)
          except RuntimeError as exc:
            records.append(dict(unsupported=str(exc)));continue
          finally:a.reference_from_observed_width=original
          assert old_scene.roads==new_scene.roads and old_scene.boundary==new_scene.boundary,'GEOMETRY_CHANGED'
          used=after.uncertainty['observed_width_reference_used']
          if not used:
            assert old==new,'FALLBACK_CHANGED'
            records.append(dict(used=False));continue
          points=np.asarray(new['points']);baseline=np.asarray(old['points']);bad=[];errors=[];old_errors=[]
          for point in points:
            if not any(cv2.pointPolygonTest(poly,tuple(point),False)>=0 for poly in truth):bad.append(point.tolist())
            if baseline[:,1].min()<=point[1]<=baseline[:,1].max():
              old_point=(float(np.interp(point[1],baseline[:,1],baseline[:,0])),point[1])
              old_errors.append(center_distance(old_point,line));errors.append(center_distance(point,line))
          records.append(dict(radius=radius,phase=phase,mirror=mirror,variable=variable,paint_mode=paint_mode,used=True,
            points=len(points),outside_physical_road=bad,baseline_matched_MAE_m=float(np.mean(old_errors)),new_MAE_m=float(np.mean(errors))))
    raw=np.array([[0.,-2.],[0.,0.],[0.,2.]])
    curves=[dict(points=[(0.,3.,0.),(0.,4.,.05),(0.,5.,.1)])]
    image=np.ones((84,84),np.uint8);blocked=np.ones((84,84),bool)
    fallback,info=original(raw,curves,image,blocked)
    assert np.array_equal(fallback,raw) and not info['observed_width_reference_used']
    fallback,info=original(raw,curves,np.zeros((84,84),np.uint8),~blocked)
    assert np.array_equal(fallback,raw) and not info['observed_width_reference_used']
    used=[r for r in records if r.get('used')];bad=[r for r in used if r['outside_physical_road']]
    old_mae=float(np.mean([r['baseline_matched_MAE_m'] for r in used]));new_mae=float(np.mean([r['new_MAE_m'] for r in used]))
    result=dict(status='PASS' if used and not bad and new_mae<old_mae else 'FAIL',cases=len(records),used_cases=len(used),
      unsupported_cases=sum('unsupported' in r for r in records),outside_physical_road_cases=len(bad),
      baseline_matched_MAE_m=old_mae,new_MAE_m=new_mae,blocked_and_unknown_fallback=True,geometry_unchanged=True,
      CPU_s=time.process_time()-start,native_actions=0,model_ticks=0,
      scope='Finite public tile/raster cases; reference estimate only, no universal guarantee.',records=records)
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2));assert result['status']=='PASS'


if __name__=='__main__':main()
