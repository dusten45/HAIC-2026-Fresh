"""Public counterexample for a visible plateau seam just beyond an object ROI."""
from pathlib import Path
import argparse,json,sys,time
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def rectangle(left,top,right,bottom):
    x0=(left-a.IMAGE_ORIGIN_X)/a.OBJECT_SX;x1=(right-a.IMAGE_ORIGIN_X)/a.OBJECT_SX
    y0=(a.IMAGE_ORIGIN_Y-bottom)/a.OBJECT_SY;y1=(a.IMAGE_ORIGIN_Y-top)/a.OBJECT_SY
    return np.array([[x0,y0],[x1,y0],[x1,y1],[x0,y1]])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path);parser.add_argument('--expect-missing',action='store_true');parser.add_argument('--expect-overlap-missing',action='store_true');args=parser.parse_args();assert not args.output.exists();cpu=time.process_time();records=[]
    for shade in (100.,105.):
      for side in ('left','right','top','bottom'):
        image=np.full((84,84),shade/255.,np.float32);image[24:27,33:36]=173/255.
        roi=[29,20,40,31];x0,y0,x1,y1=roi;opaque=np.zeros((84,84),bool)
        patch=rectangle(x0+1+.35*a.OBJECT_SX,y0+1+.35*a.OBJECT_SY,x1-1-.35*a.OBJECT_SX,y1-1-.35*a.OBJECT_SY)
        # Independent .35m insets leave a seam on an otherwise continuously
        # visible public road plateau. Existing object's fit is unchanged.
        if side=='left':road=rectangle(10,10,x0-.35*a.OBJECT_SX,45);gap=(slice(10,46),x0-1)
        elif side=='right':road=rectangle(x1+.35*a.OBJECT_SX,10,60,45);gap=(slice(10,46),x1+1)
        elif side=='top':road=rectangle(10,8,60,y0-.35*a.OBJECT_SY);gap=(y0-1,slice(10,61))
        else:road=rectangle(10,y1+.35*a.OBJECT_SY,60,49);gap=(y1+1,slice(10,61))
        roads=[(road,1.)];before_patch=patch.copy();before_road=road.copy()
        additions=a.observed_object_plateau_connectors(image,patch,roi,roads,opaque)
        assert np.array_equal(patch,before_patch)and np.array_equal(road,before_road)
        if args.expect_missing:assert not additions,'BASELINE_ALREADY_COVERS_FIXTURE'
        else:
            assert additions,'CURRENT_VISIBLE_PLATEAU_STILL_OMITTED'
            for p in additions:
                # Every added point lies on the public physical asphalt and
                # in the observed image. No object center or hidden extension.
                px=a.IMAGE_ORIGIN_X+a.OBJECT_SX*p[:,0];py=a.IMAGE_ORIGIN_Y-a.OBJECT_SY*p[:,1]
                assert min(px)>=1 and max(px)<=82 and min(py)>=5 and max(py)<=53
                assert max(px)<33 or min(px)>35 or max(py)<24 or min(py)>26
            for name,value in [('grass',162/255.),('paint',1.),('dark',0.),('orange',173/255.)]:
                changed=image.copy();changed[gap]=value
                assert not a.observed_object_plateau_connectors(changed,patch,roi,roads,opaque),name
            blocked=opaque.copy();blocked[gap]=True
            assert not a.observed_object_plateau_connectors(image,patch,roi,roads,blocked),'OPAQUE_GAP'
            remote=[(road+np.array([100.,0.]),1.)]
            assert not a.observed_object_plateau_connectors(image,patch,roi,remote,opaque),'NO_EXISTING_MESH_OVERLAP'
        records.append(dict(shade=shade,side=side,connectors=len(additions),outside_ROI_material_vetoes=0 if args.expect_missing else 5))
    # Existing inferred patch overlap may have a different road-compatible
    # shade. Only the newly added strip needs to match the surrounding ring.
    image=np.full((84,84),100/255.,np.float32);roi=[29,20,40,31];x0,y0,x1,y1=roi
    patch=rectangle(x0+1+.35*a.OBJECT_SX,y0+1+.35*a.OBJECT_SY,x1-1-.35*a.OBJECT_SX,y1-1-.35*a.OBJECT_SY)
    road=rectangle(x1+.35*a.OBJECT_SX,10,60,45);opaque=np.zeros((84,84),bool)
    image[y0+2:y1-1,x1-2]=108/255.
    additions=a.observed_object_plateau_connectors(image,patch,roi,[(road,1.)],opaque)
    if args.expect_missing or args.expect_overlap_missing:assert not additions,'OVERLAP_COUNTEREXAMPLE_NOT_REPRODUCED'
    else:
        assert additions,'EXISTING_PATCH_SHADE_BLOCKS_NEW_VISIBLE_PLATEAU'
        for value in (162/255.,1.,0.,173/255.):
            changed=image.copy();changed[y0+2:y1-1,x1-2]=value
            assert not a.observed_object_plateau_connectors(changed,patch,roi,[(road,1.)],opaque),'OVERLAP_MATERIAL_VETO'
        blocked=opaque.copy();blocked[y0+2:y1-1,x1-2]=True
        assert not a.observed_object_plateau_connectors(image,patch,roi,[(road,1.)],blocked),'OVERLAP_OPAQUE_VETO'
        # The same shade outside the metric patch must NOT borrow its
        # accepted support, even though it is globally road-compatible.
        changed=image.copy();changed[y0+2:y1-1,x1+1]=108/255.
        assert not a.observed_object_plateau_connectors(changed,patch,roi,[(road,1.)],opaque),'NEW_REGION_SHADE_NOT_VALIDATED'
    records.append(dict(case='already_supported_patch_overlap_shade',connectors=len(additions),overlap_global_road_compatible=True,new_region_matches_ring=True))
    result=dict(status='PUBLIC_OMISSION_CONFIRMED'if args.expect_missing else'PASS',records=records,model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,scope='Synthetic current-visible road plateaus only; no native case, hidden road or object refit. A missing connector is an availability error, not authority to infer unseen pavement.')
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result));assert result['CPU_s']<30


if __name__=='__main__':main()
