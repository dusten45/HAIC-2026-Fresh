"""Public orange-on-road raster counterexamples for artificial road holes."""
from pathlib import Path
import sys,json,time,math
import numpy as np,cv2,pygame
from pygame import gfxdraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def scene(angle,offset,phase,shade,paint):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    rotation=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
    shift=np.array([phase,0.])
    def transform(p):return np.asarray(p)@rotation.T+shift
    def draw(poly,color):
        pixels=[]
        for x,y in poly:
            px=a.IMAGE_ORIGIN_X+1.3608*x;py=a.IMAGE_ORIGIN_Y-1.701*y
            pixels.append(((px+.5)*1000/84-.5,799-((py+.5)*800/84-.5)))
        gfxdraw.aapolygon(surface,pixels,color);gfxdraw.filled_polygon(surface,pixels,color)
    road=transform([[-40/6,-20],[40/6,-20],[40/6,70],[-40/6,70]])
    draw(road,(shade,)*3)
    if paint:
        for i,y in enumerate(np.arange(-20,70,3.5)):
            color=(255,)*3 if paint=='white' or (paint=='alternating' and i%2==0) else (255,0,0)
            draw(transform([[-8,y],[-40/6,y],[-40/6,y+3.5],[-8,y+3.5]]),color)
    center=transform([offset,10.])
    theta=np.arange(16)*2*math.pi/16
    draw(center+1.2*np.column_stack((np.cos(theta),np.sin(theta))),(255,165,0))
    surface=pygame.transform.flip(surface,False,True);surface=pygame.transform.smoothscale(surface,(96,96))
    rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    return cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255,road.astype(np.float32)


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[];new_pixels=0;outside=0;rejected=0
    for angle in (-.3,0.,.3):
      for offset in (-4.,4.):
       for phase in (.1,.6):
        for shade in (102,107):
         for paint in (None,'red','white','alternating'):
            image,truth=scene(angle,offset,phase,shade,paint)
            asphalt=(image>.36)&(image<.47);kernel=np.ones((3,3),np.uint8)
            flat=cv2.dilate(image,kernel)-cv2.erode(image,kernel)<=(5.1+2)/255.
            detections,_=a.detect_observed_obstacles(image)
            added=a.object_adjacent_asphalt(image,asphalt,flat,detections)
            assert not np.any(added&~asphalt) and not np.any(added&(image>(107.1+2)/255.))
            assert not a.object_adjacent_asphalt(image,asphalt,flat,[]).any()
            for y,x in zip(*np.where(added)):
                point=((x-a.IMAGE_ORIGIN_X)/1.3608,(a.IMAGE_ORIGIN_Y-y)/1.701)
                assert cv2.pointPolygonTest(truth,point,True)>=-1e-6,'RECOVERY_OUTSIDE_PUBLIC_ROAD'
            observer=a.Agent();observer.calls=1;observer.last_root=object();observer.distance=100.;observer.speed=30.
            try:geometry,_,_,_=observer._map(image)
            except RuntimeError:
                rejected+=1;continue
            bad=0;tested=0
            for poly,g in geometry.roads:
                poly=np.array(poly)
                samples=np.vstack([poly,(poly+np.roll(poly,-1,axis=0))*.5,np.mean(poly,axis=0)])
                for point in samples:
                    tested+=1;bad+=cv2.pointPolygonTest(truth,tuple(point),True)<-1e-6
            outside+=bad;new_pixels+=int(added.sum())
            records.append(dict(angle=angle,offset=offset,phase=phase,shade=shade,paint=paint,
                added_pixels=int(added.sum()),mesh_samples=tested,outside=bad))
    assert new_pixels>0 and outside==0
    # No confirmed object, coherent grass, opaque orange, or arbitrary opaque
    # pixel can relax a road material test by itself.
    guards=[]
    for value in (0.,102/255.,170/255.,1.):
        image=np.full((84,84),value,np.float32);asphalt=(image>.36)&(image<.47)
        restored=a.object_adjacent_asphalt(image,asphalt,np.zeros((84,84),bool),[((0.,10.),1.6)])
        guards.append(not restored.any())
    assert all(guards)
    result=dict(status='PASS',cases=len(records),unsupported=rejected,restored_current_asphalt_pixels=new_pixels,
        mesh_samples=sum(r['mesh_samples'] for r in records),outside_public_road=outside,
        no_opaque_or_nonasphalt_pixels_added=True,negative_guards=len(guards),records=records,
        model_ticks=0,native_actions=0,CPU_s=time.process_time()-cpu,
        limitation='Finite current-pixel orange/road/grass/paint counterexamples, not a universal subpixel or safety bound. No unseen road support is added.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
