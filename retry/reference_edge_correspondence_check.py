"""Public raster counterexamples for current-pixel contour correspondence."""
from pathlib import Path
import sys,json,time,math
import numpy as np,cv2
from retry.painted_band_check import scene,a


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[]
    D=np.diag([1.3608,-1.701]);origin=np.array([a.IMAGE_ORIGIN_X,a.IMAGE_ORIGIN_Y])
    for radius in (12.,18.,28.):
      for mirror in (-1,1):
        previous,_=scene(radius,-.2,mirror,False)
        road=((previous>.36)&(previous<.47)).astype(np.uint8);blocked=np.zeros((84,84),bool)
        _,_,_,curves=a.infer_painted_road_band(previous,road,blocked)
        assert curves,'NO_PUBLIC_EDGE_SEEDS'
        angle=.1*mirror;co,si=math.cos(angle),math.sin(angle)
        rotation=np.array([[co,si],[-si,co]]);translation=np.array([0.,-2.])
        linear=D@rotation@np.linalg.inv(D);offset=origin+D@translation-linear@origin
        current=cv2.warpAffine(previous,np.column_stack((linear,offset)),(84,84),flags=cv2.INTER_LINEAR,borderValue=162/255.)
        seeds=[dict(outer_side=c['outer_side'],edge_points=c['edge_points']@rotation.T+translation,edge_normals=c['edge_normals']@rotation.T) for c in curves]
        road=((current>.36)&(current<.47)).astype(np.uint8)
        bands0=[];bands1=[]
        baseline=a.infer_painted_road_band(current,road,blocked,geometry_bands=bands0)
        tracked=a.infer_painted_road_band(current,road,blocked,geometry_bands=bands1,reference_seeds=seeds)
        assert np.array_equal(baseline[0],tracked[0]) and baseline[2]==tracked[2]
        assert len(bands0)==len(bands1) and all(np.array_equal(x,y) for x,y in zip(bands0,bands1))
        matched=sum(c['current_edge_matches'] for c in tracked[3]);novel=sum(c['current_edge_new_observations'] for c in tracked[3])
        if radius==12.:
            assert not tracked[3],'UNSUPPORTED_TIGHT_VIEW_PROMOTED'
        else:assert matched>0,'NO_CURRENT_EDGE_MATCHES'
        wrong=[dict(s,edge_normals=-s['edge_normals']) for s in seeds]
        rejected=a.infer_painted_road_band(current,road,blocked,reference_seeds=wrong)
        assert sum(c['current_edge_matches'] for c in rejected[3])==0,'REVERSED_MATERIAL_ORDER_ACCEPTED'
        far=[dict(s,edge_points=s['edge_points']+100.) for s in seeds]
        rejected=a.infer_painted_road_band(current,road,blocked,reference_seeds=far)
        assert sum(c['current_edge_matches'] for c in rejected[3])==0,'OFFSCREEN_HISTORY_ACCEPTED'
        forbidden=a.infer_painted_road_band(current,road,np.ones((84,84),bool),reference_seeds=seeds)
        assert not forbidden[3],'BLOCKED_CURRENT_IMAGE_REUSED'
        grass=np.full((84,84),162/255.,np.float32)
        forbidden=a.infer_painted_road_band(grass,np.zeros((84,84),np.uint8),blocked,reference_seeds=seeds)
        assert not forbidden[3],'GRASS_CONTRADICTION_IGNORED'
        records.append(dict(radius=radius,mirror=mirror,matches=matched,new_actual_observations=novel,geometry_unchanged=True))
    observer=a.Agent();observer.reference_seeds=seeds;observer.reset(None);assert not observer.reference_seeds
    result=dict(status='PASS',records=records,cases=len(records),guards=['wrong material normal','offscreen prior','current obstacle veto','current grass contradiction','reset clears correspondence'],CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,
        scope='Finite publicly rendered roads under known camera transforms. Correspondence is reobserved in current pixels and does not change safety geometry. No universal registration or hidden-obstacle claim.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
