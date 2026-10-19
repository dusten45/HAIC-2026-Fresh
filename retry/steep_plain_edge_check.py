"""Steep public road/grass transitions need a correctly placed sample window."""
from pathlib import Path
import json,sys,time,math
import numpy as np,cv2
from retry.raster_boundary_check import render
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def halo(image):return cv2.dilate(((image<.35)|(image>.75)).astype(np.uint8),np.ones((3,9),np.uint8))>0


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[];extra=0;outside=[];witness=None
    for slope in (-2.6,-2.2,-1.8,1.8,2.2,2.6):
     for phase in (.15,.65):
      for shade in (102,107):
        left=lambda y:(25.+phase+slope*(y-35.),y)
        width=2*(40/6)*1.3608*math.sqrt(1+(slope*1.701/1.3608)**2)
        right=lambda y:(left(y)[0]+width,y)
        source=render(left,right,shade)
        for mirror in (False,True):
         image=source[:,::-1].copy() if mirror else source
         paint=halo(image);blocked=np.zeros((84,84),bool);direction=-1 if mirror else 1
         for y in (34,35,36):
            road=(image[y]>.36)&(image[y]<.47)
            ids=np.flatnonzero(road)
            if not len(ids):continue
            index=int(ids[-1] if mirror else ids[0]);actual=83-left(y)[0] if mirror else left(y)[0]
            old=None
            for anchor in (index,index-direction):
                profile=anchor+direction*np.arange(-3,5)
                if min(profile)<0 or max(profile)>=84 or paint[y,index]:continue
                if 156/255<=float(np.mean(image[y,profile[:2]]))<=184/255:
                    old=a.recover_pixel_edge(image,y,anchor,direction,blocked)
                    if old is not None:break
            new=a.recover_plain_run_edge(image,y,index,direction,blocked,paint)
            if new is not None:
                outward=max(0.,direction*(actual-(new+direction*.35*1.3608)))/1.3608
                outside.append(outward)
                assert outward<1e-9 and abs(new-index)<=2.5
                if old is None:
                    extra+=1
                    if witness is None:witness=(image.copy(),y,index,direction)
            records.append(dict(slope=slope,phase=phase,shade=shade,mirror=mirror,row=y,
                old_available=old is not None,new_available=new is not None,
                abs_error_px=None if new is None else abs(new-actual)))
    assert extra>0 and outside and max(outside)<1e-9
    image,y,index,direction=witness;blocked=np.ones((84,84),bool)
    assert a.recover_plain_run_edge(image,y,index,direction,blocked,halo(image)) is None
    changed=image.copy();changed[y-1,index-direction*6]=76/255.
    assert a.recover_plain_run_edge(changed,y,index,direction,np.zeros_like(blocked),halo(changed)) is None
    # A narrow grass gap has no valid monotone road/grass plateau pair;
    # searching must not silently skip it into another road branch.
    narrow=np.full((84,84),100/255.,np.float32);narrow[:,27:29]=162/255.
    assert a.recover_plain_run_edge(narrow,35,26,-1,np.zeros_like(blocked),halo(narrow)) is None
    for direction,index in ((1,1),(-1,82)):
        assert a.recover_plain_run_edge(narrow,35,index,direction,np.zeros_like(blocked),halo(narrow)) is None
    result=dict(status='PASS',public_edges=len(records),old_missed_new_recovered=extra,
        max_outward_after_existing_inset_m=max(outside),guards=['blocked','paint in shifted window','narrow grass gap','both FOV edges'],
        model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,records=records,
        limitation='Finite public raster slopes/phases/mirrors and material guards; no universal inversion error bound.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
