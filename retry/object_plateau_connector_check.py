"""Public orange-road plateau union seams and current-pixel connector vetoes."""
from pathlib import Path
import sys,json,time,math
import numpy as np,cv2
from retry.object_occlusion_check import observer,a
import pygame
from pygame import gfxdraw


def scene(shade,phase,angle):
    # Public uniform camera-phase grid; the object and road move together.
    ix,iy=phase;shift=np.array([ix/(16*1.3608),iy/(16*1.701)])
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    def draw(poly,color):
        points=[((a.IMAGE_ORIGIN_X+1.3608*x+.5)*1000/84-.5,799-((a.IMAGE_ORIGIN_Y-1.701*y+.5)*800/84-.5)) for x,y in poly]
        gfxdraw.aapolygon(surface,points,color);gfxdraw.filled_polygon(surface,points,color)
    physical=np.array([[-40/6,-30],[40/6,-30],[40/6,70],[-40/6,70]])+shift
    draw(physical,(shade,)*3);center=np.array([0.,16.])+shift
    theta=angle+np.arange(16)*2*math.pi/16
    object_polygon=center+1.2*np.column_stack((np.cos(theta),np.sin(theta)))
    draw(object_polygon,(255,165,0))
    surface=pygame.transform.smoothscale(pygame.transform.flip(surface,False,True),(96,96))
    rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2))
    image=cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255
    return image,physical.astype(np.float32),object_polygon


def inside(point,roads):
    return any(cv2.pointPolygonTest(np.asarray(poly,np.float32),tuple(point),False)>=0 for poly,g in roads)


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[];total=0;witnesses=0;active_fixture=None
    for shade in (102,107):
     for phase in ((0,1),(0,7),(1,3),(2,5),(4,6),(8,1),(12,3),(15,15)):
      for angle in (0.,math.pi/16):
        image,physical,object_polygon=scene(shade,phase,angle)
        captured=[];original=a.observed_object_road_patch
        connector=a.observed_object_plateau_connectors
        def record(*args):
            result=original(*args)
            if result is not None:captured.append(result)
            return result
        a.observed_object_road_patch=record
        a.observed_object_plateau_connectors=lambda *args:[]
        try:baseline=observer()._map(image)
        finally:
            a.observed_object_road_patch=original
            a.observed_object_plateau_connectors=connector
        assert len(captured)==1
        patch,collision,metadata=captured[0]
        # Recover the prior public patch's ROI coordinates for the pre-integration
        # prototype as well; production records provide them without a refit.
        roi=metadata.get('observed_roi_pixels')
        if roi is None:
            roi=[int(round((patch[:,0].min()-.35)*1.3608+a.IMAGE_ORIGIN_X-1)),
                 int(round(a.IMAGE_ORIGIN_Y-(patch[:,1].max()+.35)*1.701-1)),
                 int(round((patch[:,0].max()+.35)*1.3608+a.IMAGE_ORIGIN_X+1)),
                 int(round(a.IMAGE_ORIGIN_Y-(patch[:,1].min()-.35)*1.701+1))]
        roads=[(p,g) for p,g in baseline[0].roads if not np.array_equal(np.asarray(p),patch)]
        opaque=a.vehicle_projection_mask(0.).astype(bool)
        additions=a.observed_object_plateau_connectors(image,patch,roi,roads,opaque)
        joined=list(baseline[0].roads)+[(p.tolist(),1.) for p in additions]
        found=0
        for p in additions:
            samples=np.vstack((p,(p+np.roll(p,-1,axis=0))*.5,np.mean(p,axis=0)))
            xx=np.arange(math.ceil(a.IMAGE_ORIGIN_X+1.3608*p[:,0].min()),math.floor(a.IMAGE_ORIGIN_X+1.3608*p[:,0].max())+1)
            yy=np.arange(math.ceil(a.IMAGE_ORIGIN_Y-1.701*p[:,1].max()),math.floor(a.IMAGE_ORIGIN_Y-1.701*p[:,1].min())+1)
            gx,gy=np.meshgrid(xx,yy)
            samples=np.vstack((samples,np.column_stack(((gx.ravel()-a.IMAGE_ORIGIN_X)/1.3608,(a.IMAGE_ORIGIN_Y-gy.ravel())/1.701))))
            assert all(cv2.pointPolygonTest(physical,tuple(q),True)>=-1e-6 for q in samples),'CONNECTOR_OUTSIDE_PUBLIC_ROAD'
            # The public physical road is convex: all rectangle vertices
            # inside it imply its entire continuous area stays inside it.
            pixels=np.column_stack((a.IMAGE_ORIGIN_X+1.3608*p[:,0],a.IMAGE_ORIGIN_Y-1.701*p[:,1]))
            roundtrip=np.column_stack(((pixels[:,0]-a.IMAGE_ORIGIN_X)/1.3608,(a.IMAGE_ORIGIN_Y-pixels[:,1])/1.701))
            assert np.max(abs(roundtrip-p))<1e-12,'ANISOTROPIC_COORDINATE_ROUNDTRIP'
            for q in samples:
                if not inside(q,baseline[0].roads):found+=1;assert inside(q,joined)
        assert not additions or found,'CONNECTOR_DID_NOT_COVER_NEW_PLATEAU'
        if shade==102 and phase==(0,1) and angle==0.:
            integrated=observer()._map(image)
            assert integrated[1:]==baseline[1:],'REFERENCE_OR_PROGRESS_CHANGED'
            assert integrated[0].obstacles==baseline[0].obstacles,'COLLISION_OBJECTS_CHANGED'
            assert len(integrated[0].roads)==len(joined),'INTEGRATION_DID_NOT_ADD_SAME_CONNECTORS'
        # An image change anywhere in the ring invalidates reuse of its
        # earlier support. No topology or geometry is inferred through it.
        x0,y0,x1,y1=roi;guards=[]
        for name,value in [('grass',162/255.),('paint',1.),('opaque',0.),('orange',173/255.)]:
            changed=image.copy();changed[y0:y1+1,x1]=value
            guards.append(not a.observed_object_plateau_connectors(changed,patch,roi,roads,opaque))
        all_opaque=np.ones_like(opaque)
        guards.append(not a.observed_object_plateau_connectors(image,patch,roi,roads,all_opaque))
        # A real gap separates the inferred patch from every other road. It
        # must not be bridged merely because the old ROI still looks smooth.
        remote=[((np.asarray(p)+[100.,0.]).tolist(),g) for p,g in roads]
        guards.append(not a.observed_object_plateau_connectors(image,patch,roi,remote,opaque))
        assert all(guards),'CURRENT_SUPPORT_OR_OVERLAP_VETO_FAILED'
        if additions and active_fixture is None:active_fixture=(image.copy(),patch.copy(),roi,roads,opaque.copy())
        total+=len(additions);witnesses+=found
        records.append(dict(shade=shade,phase=phase,orientation=angle,connectors=len(additions),new_current_plateau_witnesses=found,negative_guards=len(guards)))
    assert total and witnesses,'PUBLIC_UNION_SEAM_NOT_EXERCISED'
    # A visible physical grass break crosses a previously active plateau;
    # this is separate from the remote-mesh positive-overlap negative above.
    image,patch,roi,roads,opaque=active_fixture;x0,y0,x1,y1=roi
    gap=image.copy();ymid=(y0+y1)//2;gap[ymid-1:ymid+2,x0:x1+1]=162/255.
    assert not a.observed_object_plateau_connectors(gap,patch,roi,roads,opaque),'VISIBLE_PHYSICAL_GRASS_GAP_BRIDGED'
    result=dict(status='PASS',cases=len(records),connectors=total,uncovered_before_covered_after=witnesses,records=records,
        visible_physical_grass_gap_rejected=True,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,
        scope='Finite entirely public raster and union counterexamples. Current plateau only, unchanged0.35m four-flank inset; original inferred patch and collision objects unchanged. No universal safety certificate.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
