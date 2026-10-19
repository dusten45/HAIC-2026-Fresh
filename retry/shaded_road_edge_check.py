"""Public tile-colour seams must not erase a visible road/grass boundary."""
from pathlib import Path
import sys,json,time,math
import numpy as np,cv2,pygame
from pygame import gfxdraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def render(angle,phase,shift):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102));n=np.array([math.cos(angle),math.sin(angle)]);t=np.array([-math.sin(angle),math.cos(angle)]);origin=np.array([phase/1.3608,15.+phase/1.701])
    for i in range(-12,13):
        p=origin+i*3.5*t;z=p+3.5*t;poly=[p-40/6*n,p+40/6*n,z+40/6*n,z-40/6*n]
        pixels=[((a.IMAGE_ORIGIN_X+1.3608*x+.5)*1000/84-.5,799-((a.IMAGE_ORIGIN_Y-1.701*y+.5)*800/84-.5)) for x,y in poly]
        color=(102+int(2.55*((i+shift)%3)),)*3;gfxdraw.aapolygon(surface,pixels,color);gfxdraw.filled_polygon(surface,pixels,color)
    surface=pygame.transform.smoothscale(pygame.transform.flip(surface,False,True),(96,96));rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    return cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255,origin


def original_edge(image,y,index,direction,blocked,paint):
    for exterior in range(4):
        anchor=index-direction*exterior;ids=anchor+direction*np.arange(-3,5)
        if min(ids)<0 or max(ids)>=84 or paint[y,anchor]:continue
        if not 156/255<=float(np.mean(image[y,ids[:2]]))<=184/255:continue
        result=a.recover_pixel_edge(image,y,anchor,direction,blocked)
        if result is not None and abs(result-index)<=2.5:return result
    return None


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[];recovered=0;outside=[];legacy_outside=[];tightened=0;witness=None
    for angle in (-1.25,-1.1,-.8,-.4,.4,.8,1.1,1.25):
     for phase in (.1,.35,.6,.85):
      for shift in (0,1):
        image,origin=render(angle,phase,shift);blocked=np.zeros((84,84),bool);paint=cv2.dilate(((image<.35)|(image>.75)).astype(np.uint8),np.ones((3,9),np.uint8))>0
        for y in range(33,43):
            mask=(image[y]>.36)&(image[y]<.47);d=np.diff(np.pad(mask,(1,1)).astype(int));starts=np.flatnonzero(d==1);ends=np.flatnonzero(d==-1)
            if not len(starts):continue
            j=int(np.argmax(ends-starts));left,right=int(starts[j]),int(ends[j]-1)
            if right-left<7:continue
            wy=(a.IMAGE_ORIGIN_Y-y)/1.701;cx=origin[0]-math.tan(angle)*(wy-origin[1])
            for index,direction,physical in ((left,1,cx-40/6/math.cos(angle)),(right,-1,cx+40/6/math.cos(angle))):
                actual=a.IMAGE_ORIGIN_X+1.3608*physical
                if not 4<actual<79:continue
                old=original_edge(image,y,index,direction,blocked,paint);new=a.recover_plain_run_edge(image,y,index,direction,blocked,paint)
                if new is not None:
                    error=max(0.,direction*(actual-(new+direction*.35*1.3608)))/1.3608
                    if old is not None:
                        assert direction*(new-old)>=-1e-10,'EXISTING_RECOVERY_EXPANDED'
                        tightened+=abs(new-old)>1e-9
                        legacy_outside.append(max(0.,direction*(actual-(old+direction*.35*1.3608)))/1.3608)
                    if old is None:
                        outside.append(error)
                        recovered+=1
                        if witness is None:witness=(image,y,index,direction,paint)
                assert new is None or error<1e-8,('SHADE_RECOVERY_OUTSIDE_PHYSICAL_ROAD',angle,phase,shift,y,index,direction,actual,old,new,error)
                records.append(dict(angle=angle,phase=phase,shift=shift,row=y,direction=direction,old=old is not None,new=new is not None))
    assert recovered>0 and outside and max(outside)<1e-8
    image,y,index,direction,paint=witness
    assert a.recover_plain_run_edge(image,y,index,direction,np.ones((84,84),bool),paint) is None
    veto=paint.copy();veto[:]=True;assert a.recover_plain_run_edge(image,y,index,direction,np.zeros((84,84),bool),veto) is None
    grass=np.full((84,84),162/255.,np.float32);assert a.recover_plain_run_edge(grass,y,index,direction,np.zeros((84,84),bool),np.zeros((84,84),bool)) is None
    narrow=np.full((84,84),102/255.,np.float32);narrow[:,27:29]=162/255.
    assert a.recover_plain_run_edge(narrow,35,26,-1,np.zeros((84,84),bool),np.zeros((84,84),bool)) is None
    result=dict(status='PASS',public_profiles=len(records),previously_missed_recovered=recovered,max_outward_after_existing_inset_m=max(outside),negative_guards=4,legacy_edges_never_expanded=True,legacy_recoveries_tightened=int(tightened),legacy_max_outward_after_inset_m=max(legacy_outside,default=0.),legacy_outside_profiles=int(sum(x>1e-8 for x in legacy_outside)),CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,records=records,limitation='Both new and conservative tightened recoveries are checked; baseline area inversion errors are separately reported. Public straight tile roads with real transverse shade seams and camera phases. Palette/raster allowances are engineering priors; no controller or geometry admission threshold changes.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
