"""Public merge raster: a forward union midpoint must not pick the far leg."""
from pathlib import Path
import sys,json,time
import numpy as np,cv2,pygame
from pygame import gfxdraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def scene(junction):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    def pixel(x,y):return ((x+.5)*1000/84-.5,799.-((y+.5)*800/84-.5))
    half=(40./6.)*1.3608;left=a.IMAGE_ORIGIN_X-half;right=a.IMAGE_ORIGIN_X+half
    other_left=left-20*1.3608;other_right=right-20*1.3608
    for lo,hi,top,bottom in [(left,right,-5,90),(other_left,other_right,-5,90),(other_left,right,-5,junction)]:
        poly=[pixel(lo,top),pixel(hi,top),pixel(hi,bottom),pixel(lo,bottom)]
        gfxdraw.aapolygon(surface,poly,(102,)*3);gfxdraw.filled_polygon(surface,poly,(102,)*3)
    surface=pygame.transform.flip(surface,False,True);surface=pygame.transform.smoothscale(surface,(96,96))
    image=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    return cv2.cvtColor(cv2.resize(image,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255.


def legacy_forward_midpoint(image,road,blocked):
    # Exact old near-edge association rule, isolated from subsequent fitting.
    d=np.diff(np.pad(road[54],(1,1)).astype(np.int16));s=np.flatnonzero(d==1);e=np.flatnonzero(d==-1)
    anchor=float((s[0]+e[-1]-1)*.5);points=[]
    for y in range(55,69):
        d=np.diff(np.pad(road[y],(1,1)).astype(np.int16));s=np.flatnonzero(d==1);e=np.flatnonzero(d==-1);good=e-s>=8;s=s[good];e=e[good]
        outside=np.maximum(s-anchor,0)+np.maximum(anchor-e,0)
        j=int(np.argmin(3*outside+.1*abs((s+e-1)*.5-anchor)));anchor=(s[j]+e[j]-1)*.5
        edge=a.recover_pixel_edge(image,y,int(e[j]-1),-1,blocked,max_row=69)
        if edge is not None:points.append((edge-a.IMAGE_ORIGIN_X)/1.3608)
    return points


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[]
    for joint in (-.25,0.,.25):
        image=scene(54.5);road=((image>.36)&(image<.47)).astype(np.uint8);blocked=a.vehicle_projection_mask(joint).astype(bool)
        current=a.near_vehicle_reference_edges(image,road,blocked);old=legacy_forward_midpoint(image,road,blocked)
        assert len(current[1])>=7 and all(5.<x<8. for x,y in current[1]),current
        assert len(old)>=7 and max(old)<-10.,old
        # Changing only the forward union/crop cannot change the near branch.
        other=scene(49.5);otherroad=((other>.36)&(other<.47)).astype(np.uint8)
        assert current[1]==a.near_vehicle_reference_edges(other,otherroad,blocked)[1]
        assert not any(a.near_vehicle_reference_edges(image,road,np.ones((84,84),bool)))
        grass=image.copy();grass[55:69]=162/255.;grassroad=((grass>.36)&(grass<.47)).astype(np.uint8)
        assert not any(a.near_vehicle_reference_edges(grass,grassroad,blocked))
        records.append(dict(joint=joint,current_near_side_points=len(current[1]),legacy_far_side_points=len(old),current_right_edge_range_m=[min(x for x,y in current[1]),max(x for x,y in current[1])],legacy_right_edge_range_m=[min(old),max(old)]))
    result=dict(status='PASS',cases=len(records),records=records,guards=['same near branch under forward union crop change','current blocked pixels','current grass contradiction'],CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,
        scope='Public road width, two visible legs and renderer raster only. No environment reset, hidden metadata, force fitting or geometry expansion.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))


if __name__=='__main__':main()
