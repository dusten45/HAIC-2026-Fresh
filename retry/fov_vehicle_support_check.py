"""Public raster checks for a vehicle corridor whose outer flank leaves view."""
from pathlib import Path
import sys,json,time
import numpy as np,cv2,pygame
from pygame import gfxdraw
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a
import runtime598 as c


def scene(junction,joint,paint=False,branch_left=-10.,branch_right=None):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    half=(40./6.)*1.3608;left=a.IMAGE_ORIGIN_X-half;right=a.IMAGE_ORIGIN_X+half
    def point(x,y):return ((x+.5)*1000/84-.5,799.-((y+.5)*800/84-.5))
    def draw(poly,color,aa=True):
        p=[point(x,y) for x,y in poly]
        if aa:gfxdraw.aapolygon(surface,p,color);gfxdraw.filled_polygon(surface,p,color)
        else:pygame.draw.polygon(surface,color,p)
    draw([(left,-10),(right,-10),(right,90),(left,90)],(102,)*3)
    if paint:
        step=(21./6.)*1.701;curb=(8./6.)*1.3608
        for i,y in enumerate(np.arange(junction,90,step)):
            draw([(left,y),(left-curb,y),(left-curb,y+step),(left,y+step)],(255,)*3 if i%2==0 else (255,0,0))
    branch_right=right if branch_right is None else branch_right
    draw([(branch_left,-10),(branch_right,-10),(branch_right,junction),(branch_left,junction)],(102,)*3)
    polygons=[[(x*c.SIZE,y*c.SIZE) for x,y in p] for p in (c.HULL_POLY1,c.HULL_POLY2,c.HULL_POLY3,c.HULL_POLY4)]
    for i,(x,y) in enumerate(c.WHEELPOS):polygons.append(c.rectangle((x*c.SIZE,y*c.SIZE),joint if i<2 else 0.))
    for i,p in enumerate(polygons):
        draw([(a.IMAGE_ORIGIN_X+1.3608*x,a.IMAGE_ORIGIN_Y-1.701*y) for x,y in p],(204,0,0) if i<4 else (0,0,0),False)
    surface=pygame.transform.flip(surface,False,True);surface=pygame.transform.smoothscale(surface,(96,96))
    image=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2));image=cv2.cvtColor(cv2.resize(image,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255.
    return image,left,right


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[]
    for junction in (57.2,58.2,59.2):
      for joint in (0.,.25):
       for paint in (False,True):
        image,left,right=scene(junction,joint,paint);asphalt=((image>.36)&(image<.47)).astype(np.uint8);blocked=np.zeros((84,84),bool)
        support,info=a.infer_local_road_support(image,asphalt,blocked,joint,False,30.)
        yy,xx=np.nonzero(support);outside=sum(not((-10<=x<=right and y<=junction) or (left<=x<=right)) for y,x in zip(yy,xx))
        observer=a.Agent();observer.last_root=object();observer.joint=joint;geometry,_,_,_=observer._map(image);root=observer._root(geometry,0.);margin=geometry.margin(root)
        records.append(dict(junction=junction,joint=joint,paint=paint,extension_rows=info.get('road_support_fov_extension_rows',0),outside=outside,current_margin_m=margin))
    # No measured adjacent corridor: a broad paved field is not an anchor.
    broad=np.full((84,84),102/255.,np.float32);cover=a.vehicle_projection_mask(.25);broad[cv2.erode(cover,np.ones((3,3),np.uint8))>0]=61/255.
    mask=((broad>.36)&(broad<.47)).astype(np.uint8);support,_=a.infer_local_road_support(broad,mask,np.zeros((84,84),bool),.25,False,30.);assert not support.any()
    # Visible grass and obstacles veto a clipped-row extension too. An
    # unsupported internal row must not be skipped to reach the other end.
    image,_,_=scene(61.2,.25);cover=a.vehicle_projection_mask(.25).astype(bool)
    negatives={}
    for name,lo,hi in [('visible_grass',57,60),('internal_break',60,61)]:
        changed=image.copy();patch=np.zeros((84,84),bool);patch[lo:hi,35:49]=True
        changed[patch&~cover]=162/255.;mask=((changed>.36)&(changed<.47)).astype(np.uint8)
        support,_=a.infer_local_road_support(changed,mask,np.zeros((84,84),bool),.25,False,30.)
        negatives[name]=not bool(np.any((support>0)&~mask.astype(bool)&(np.indices((84,84))[0]<60)))
    blocked=np.zeros((84,84),bool);blocked[57:62,38:46]=True
    mask=((image>.36)&(image<.47)).astype(np.uint8)
    support,_=a.infer_local_road_support(image,mask,blocked,.25,False,30.)
    negatives['obstacle']=not bool(np.any(support[blocked]))
    distant,_,_=scene(65.2,.25);mask=((distant>.36)&(distant<.47)).astype(np.uint8)
    support,_=a.infer_local_road_support(distant,mask,np.zeros((84,84),bool),.25,False,30.)
    negatives['one_tile_reach']=not bool(np.any((support[:60]>0)&~mask[:60].astype(bool)))
    assert all(negatives.values()),negatives
    assert all(r['outside']==0 and r['current_margin_m']>.5 for r in records),records
    assert sum(r['extension_rows']>0 for r in records)>0,'NONVACUOUS_FOV_EXTENSION'
    result=dict(status='PASS',cases=len(records),records=records,no_unanchored_fill=True,negative_guards=negatives,CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,scope='Finite public road-union and public vehicle-raster examples; not a hidden-obstacle or universal safety proof.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
