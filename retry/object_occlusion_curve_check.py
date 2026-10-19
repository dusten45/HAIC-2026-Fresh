"""Conditional object-pavement inference on public curved tile roads."""
from pathlib import Path
import sys,json,time,math
import numpy as np,cv2,pygame
from pygame import gfxdraw
from retry.object_occlusion_check import a


def scene(radius,phase,mirror,variable):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    def draw(poly,color):
        pixels=[((a.IMAGE_ORIGIN_X+1.3608*x+.5)*1000/84-.5,799-((a.IMAGE_ORIGIN_Y-1.701*y+.5)*800/84-.5)) for x,y in poly]
        gfxdraw.aapolygon(surface,pixels,color);gfxdraw.filled_polygon(surface,pixels,color)
    nodes=[];pos=np.array([0.,0.]);angle=-.6+phase
    for i in range(20):
        n=np.array([math.cos(angle),math.sin(angle)]);nodes.append((pos.copy(),n))
        turn=min(.31,3.5/radius*(1+.55*math.sin(i*.65) if variable else 1.))
        pos+=3.5*np.array([-math.sin(angle+turn/2),math.cos(angle+turn/2)]);angle+=turn
    target=nodes[4][0];shift=np.array([-target[0],16.-target[1]])
    transform=lambda p:(np.asarray(p)+shift)*[mirror,1]
    roads=[]
    for i,((p,n),(q,m)) in enumerate(zip(nodes,nodes[1:])):
        road=transform([p-40/6*n,p+40/6*n,q+40/6*m,q-40/6*m]);roads.append(road.astype(np.float32));draw(road,(102+int(2.55*(i%3)),)*3)
    center=transform(nodes[4][0]);theta=phase+np.arange(16)*2*math.pi/16;obj=center+1.2*np.column_stack((np.cos(theta),np.sin(theta)));draw(obj,(255,165,0))
    surface=pygame.transform.smoothscale(pygame.transform.flip(surface,False,True),(96,96));rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    image=cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255
    return image,roads,obj


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[];accepted=0;outside=0
    for radius in (12.,18.,28.):
     for phase in (-.2,.2):
      for mirror in (-1,1):
       for variable in (False,True):
        image,roads,obj=scene(radius,phase,mirror,variable);detections,_=a.detect_observed_obstacles(image);result=None
        if len(detections)==1:result=a.observed_object_road_patch(image,detections[0][0],0.)
        record=dict(radius=radius,phase=phase,mirror=mirror,variable=variable,accepted=result is not None)
        if result is not None:
            accepted+=1;patch,(center,r),info=result
            xs=np.linspace(min(patch[:,0]),max(patch[:,0]),17);ys=np.linspace(min(patch[:,1]),max(patch[:,1]),17)
            samples=np.array(np.meshgrid(xs,ys)).reshape(2,-1).T
            bad=sum(max(cv2.pointPolygonTest(poly,tuple(p),True) for poly in roads)<-1e-6 for p in samples)
            outside+=bad;record.update(samples=len(samples),outside_samples=bad,collision_silhouette_excess_m=float(max(np.linalg.norm(obj-center,axis=1))-r))
            assert record['collision_silhouette_excess_m']<=1e-9
        records.append(record)
    assert accepted>0 and outside==0
    result=dict(status='PASS',cases=len(records),accepted=accepted,outside_samples=outside,records=records,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,scope='Public fixed-width tile curves, varying node curvature, mirror/crop phases. Closed-ring local pavement continuity remains an inference; finite checks, not a universal geometry certificate.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
