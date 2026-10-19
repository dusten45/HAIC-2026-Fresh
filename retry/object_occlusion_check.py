"""Public16-gon exterior and conditional pavement-under-object counterexamples."""
from pathlib import Path
import sys,json,time,math
import numpy as np,cv2,pygame
from pygame import gfxdraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def scene(shade,phase,angle,offset=0.,material='orange',road_angle=0.):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    rot=np.array([[math.cos(road_angle),-math.sin(road_angle)],[math.sin(road_angle),math.cos(road_angle)]])
    center=np.array([offset+phase,16.+phase*.5]);road=np.array([[-40/6,-30],[40/6,-30],[40/6,70],[-40/6,70]])@rot.T
    def draw(poly,color):
        pixels=[((a.IMAGE_ORIGIN_X+1.3608*x+.5)*1000/84-.5,799-((a.IMAGE_ORIGIN_Y-1.701*y+.5)*800/84-.5)) for x,y in poly]
        gfxdraw.aapolygon(surface,pixels,color);gfxdraw.filled_polygon(surface,pixels,color)
    draw(road,(shade,)*3)
    theta=angle+np.arange(16)*2*math.pi/16
    polygon=center+1.2*np.column_stack((np.cos(theta),np.sin(theta)))
    color={'orange':(255,165,0),'grass':(102,204,102),'bright_grass':(102,230,102),'white':(255,255,255),'opaque':(200,200,200)}[material]
    draw(polygon,color)
    surface=pygame.transform.smoothscale(pygame.transform.flip(surface,False,True),(96,96))
    rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    image=cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255
    return image,road.astype(np.float32),polygon


def observer():
    result=a.Agent();result.calls=1;result.last_root=object();result.speed=30.;result.distance=100.;return result


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[];accepted=0;covered=0;max_excess=0.;paired=0
    for shade in (102,107):
     for phase in (0.,.25,.5,.75):
      for angle in np.arange(8)*math.pi/64:
        image,road,polygon=scene(shade,phase,float(angle))
        detections,_=a.detect_observed_obstacles(image);assert len(detections)==1
        recovered=a.observed_object_road_patch(image,detections[0][0],0.)
        assert recovered is not None,'SUPPORTED_PUBLIC_OBJECT_REJECTED'
        patch,(center,radius),record=recovered;accepted+=1
        excess=float(max(np.linalg.norm(polygon-center,axis=1))-radius);max_excess=max(max_excess,excess);assert excess<=1e-9,'TRUE_SILHOUETTE_UNDERESTIMATED'
        covered+=len(polygon)
        samples=np.vstack([patch,(patch+np.roll(patch,-1,axis=0))*.5,np.mean(patch,axis=0)])
        assert all(cv2.pointPolygonTest(road,tuple(point),True)>=-1e-6 for point in samples),'INFERRED_ROAD_OUTSIDE_PUBLIC_ROAD'
        if phase==0. and angle==0.:
            original=a.observed_object_road_patch
            a.observed_object_road_patch=lambda *args:None
            baseline=observer()._map(image)
            a.observed_object_road_patch=original
            restored=observer()._map(image)
            assert baseline[1:]==restored[1:],'REFERENCE_CHANGED_BY_ROAD_PATCH'
            assert all(o in restored[0].obstacles for o in baseline[0].obstacles),'EXISTING_COLLISION_DISK_REMOVED'
            for poly,mu in restored[0].roads:
                samples=np.vstack([poly,(np.array(poly)+np.roll(poly,-1,axis=0))*.5,np.mean(poly,axis=0)])
                assert all(cv2.pointPolygonTest(road,tuple(point),True)>=-1e-6 for point in samples)
            paired+=1
        records.append(dict(shade=shade,phase=phase,angle=float(angle),collision_radius_m=radius,compatible_cells=record['compatible_center_cells'],silhouette_excess_m=excess))
    guards=[]
    for name in ('grass','bright_grass','white','opaque'):
        image,_,_=scene(102,.25,0.,material=name)
        center=(.25,16.125)
        guards.append(a.observed_object_road_patch(image,center,0.) is None)
    for phase in (0.,.25,.5,.75):
     for angle in (0.,math.pi/16):
        image,_,_=scene(102,phase,angle,material='bright_grass')
        guards.append(a.observed_object_road_patch(image,(phase,16.+phase*.5),0.) is None)
    for offset in (-6.,6.):
        image,_,_=scene(102,.25,0.,offset=offset)
        guards.append(a.observed_object_road_patch(image,(offset+.25,16.125),0.) is None)
    image,_,_=scene(102,.25,0.)
    for point in ((0.,0.),(0.,40.),(-30.,16.)):
        guards.append(a.observed_object_road_patch(image,point,0.) is None)
    blank=np.full((84,84),102/255.,np.float32);guards.append(a.observed_object_road_patch(blank,(0.,16.),0.) is None)
    changed=image.copy();changed[35:39,40:44]=0.
    guards.append(a.observed_object_road_patch(changed,(.25,16.125),0.) is None)
    assert all(guards),guards
    result=dict(status='PASS',cases=len(records),accepted_current_objects=accepted,physical16gon_vertices_enclosed=covered,max_silhouette_undercoverage_m=max_excess,paired_reference_and_collision_preservation_checks=paired,negative_guards=len(guards),records=records,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,
        limitation='Finite public rasters. All-compatible-cell silhouette envelope uses explicit3-source-pixel and3-gray engineering assumptions, not a universal backend proof. Closed-ring pavement continuity is an inference beneath the object; existing collision disks remain.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='records'}))


if __name__=='__main__':main()
