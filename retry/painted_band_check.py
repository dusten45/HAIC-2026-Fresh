"""Finite public turning-road raster falsification checks, without simulator state."""
from pathlib import Path
import sys,math,json,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a
import numpy as np,cv2,pygame
from pygame import gfxdraw
# Public source constants and tile quads; no environment reset or case input.
def scene(radius,phase,mirror,variable=False,obstacle=False,paint_mode='alternating'):
    surface=pygame.Surface((1000,800));surface.fill((102,204,102))
    def source(v):
        x=a.IMAGE_ORIGIN_X+1.3608*v[0];y=a.IMAGE_ORIGIN_Y-1.701*v[1]
        return ((x+.5)*1000/84-.5,799-((y+.5)*800/84-.5))
    def draw(poly,color):
        points=[source(v) for v in poly];gfxdraw.aapolygon(surface,points,color);gfxdraw.filled_polygon(surface,points,color)
    nodes=[];pos=np.array([0.,-10.]);angle=-.4+phase
    for i in range(26):
        n=np.array([math.cos(angle),math.sin(angle)])
        nodes.append((pos.copy(),n.copy()))
        factor=1+.55*math.sin(i*.65) if variable else 1
        if variable=='abrupt':factor=.25 if i%8<4 else 1.7
        if variable=='reversing':factor=math.sin(i*.35)
        turn=float(np.clip(3.5/radius*factor,-.31,.31));pos+=3.5*np.array([-math.sin(angle+turn/2),math.cos(angle+turn/2)]);angle+=turn
    truth=[]
    for i,((p,n),(q,m)) in enumerate(zip(nodes,nodes[1:])):
        road=[p-6.6666666667*n,p+6.6666666667*n,q+6.6666666667*m,q-6.6666666667*m]
        side=-1 if n[0]*m[1]-n[1]*m[0]>=0 else 1
        paint=[p+side*6.6666666667*n,p+side*8*n,q+side*8*m,q+side*6.6666666667*m]
        road=np.asarray(road)*[mirror,1];paint=np.asarray(paint)*[mirror,1]
        truth.append(road.astype(np.float32));draw(road,(102+int(2.55*(i%3)),)*3)
        color=(255,)*3 if i%2==0 else (255,0,0)
        if paint_mode=='white':color=(255,)*3
        if paint_mode=='red':color=(255,0,0)
        draw(paint,color)
    if obstacle:draw(np.array([[-7,10],[-4,10],[-4,15],[-7,15]]),(170,85,0))
    surface=pygame.transform.flip(surface,False,True);surface=pygame.transform.smoothscale(surface,(96,96))
    image=np.transpose(np.array(pygame.surfarray.pixels3d(surface)),(1,0,2));image=cv2.cvtColor(cv2.resize(image,(84,84)),cv2.COLOR_RGB2GRAY).astype(np.float32)/255
    return image,truth
def main():
    start=time.process_time()
    records=[]
    for radius in (12.,18.,28.):
     for phase in (-.2,.2):
      for mirror in (-1,1):
       for variable in (False,True,'abrupt','reversing'):
        for paint_mode in ('alternating','white','red'):
         image,truth=scene(radius,phase,mirror,variable,paint_mode=paint_mode)
         asphalt=((image>.36)&(image<.47)).astype(np.uint8);blocked=np.zeros((84,84),bool)
         support,info,updates,curves=a.infer_painted_road_band(image,asphalt,blocked)
         bad=[]
         # Added pixel centres must themselves be inside a physical source road tile.
         for row,col in zip(*np.where(support)):
             point=((col-a.IMAGE_ORIGIN_X)/1.3608,(a.IMAGE_ORIGIN_Y-row)/1.701)
             distance=max(cv2.pointPolygonTest(poly,point,True) for poly in truth)
             if distance< -1e-6:bad.append(dict(support_pixel=[int(row),int(col)],outside_m=-distance))
         for (side,row),x in updates.items():
             x+=(1 if side==1 else -1)*.35*1.3608
             point=((x-a.IMAGE_ORIGIN_X)/1.3608,(a.IMAGE_ORIGIN_Y-row)/1.701)
             distance=max(cv2.pointPolygonTest(poly,point,True) for poly in truth)
             if distance< -1e-6:bad.append(dict(side=side,row=row,outside_m=-distance))
         records.append(dict(radius=radius,phase=phase,mirror=mirror,variable=variable,paint_mode=paint_mode,updates=len(updates),added=int(support.sum()),bad=bad))
    guards=[]
    for color in (102,170,255):
     image=np.full((84,84),color/255.,np.float32);mask=((image>.36)&(image<.47)).astype(np.uint8)
     support,_,updates,_=a.infer_painted_road_band(image,mask,np.zeros((84,84),bool))
     guards.append(not support.any() and not updates)
    image,truth=scene(18.,.2,1,True)
    support,_,updates,_=a.infer_painted_road_band(image,((image>.36)&(image<.47)).astype(np.uint8),np.ones((84,84),bool))
    guards.append(not support.any() and not updates)
    # Isolated mixed-paint grey must not become a grass plateau; actual2x2
    # patches remain material evidence and veto inferred road support.
    image=np.full((84,84),102/255.,np.float32);image[30,30]=171/255.
    guards.append(not a.coherent_grass_mask(image)[30,30])
    image[35:37,35:37]=160/255.;guards.append(bool(np.all(a.coherent_grass_mask(image)[35:37,35:37])))
    active=next(r for r in records if r['updates']>0)
    image,truth=scene(active['radius'],active['phase'],active['mirror'],active['variable'],paint_mode=active['paint_mode']);mask=((image>.36)&(image<.47)).astype(np.uint8)
    _,_,original,_=a.infer_painted_road_band(image,mask,np.zeros((84,84),bool))
    assert original,'NONVACUOUS_LOCAL_VETO_SCENE'
    (side,row),x=next(iter(original.items()));col=int(math.floor(x));patch=np.zeros((84,84),bool);patch[row:row+2,col:col+2]=True
    for material in ('grass','obstacle'):
     changed=image.copy();blocked=np.zeros((84,84),bool)
     if material=='grass':changed[patch]=160/255.
     else:blocked[patch]=True
     support,_,updates,_=a.infer_painted_road_band(changed,((changed>.36)&(changed<.47)).astype(np.uint8),blocked)
     safe=not bool(np.any(support[patch]))
     for (which,ry),edge in updates.items():
      if row<=ry<row+2 and col<=edge<=col+1:safe=False
     guards.append(safe)
    assert all(guards),guards
    # A camera rotation crossing atan2's branch cut must preserve local offsets.
    theta=np.linspace(-.7,1.7,65);center=np.array([-12.,4.]);radius=18.
    points=center+(radius+.3*np.sin(3*theta))[:,None]*np.column_stack((np.cos(theta),np.sin(theta)))
    reference,_,_=a.offset_observed_contour(points,center,radius);rotation_errors=[]
    for angle in (2.8,-2.8):
     rotation=np.array([[math.cos(angle),-math.sin(angle)],[math.sin(angle),math.cos(angle)]])
     contour,_,_=a.offset_observed_contour(points@rotation.T,center@rotation.T,radius)
     assert len(contour)==len(reference),'LOCAL_OFFSET_BRANCH_CUT'
     error=float(np.max(np.linalg.norm(np.asarray(contour)[:,:2]@rotation-np.asarray(reference)[:,:2],axis=1)))
     rotation_errors.append(error);assert error<1e-7

    result=dict(rotation_equivariance_errors_m=rotation_errors,negative_guards_passed=len(guards),status='PASS' if all(not r['bad'] for r in records) and sum(r['updates'] for r in records)>0 else 'FAIL',records=records,CPU_s=time.process_time()-start,native_actions=0,model_ticks=0)
    out=Path(sys.argv[1]);assert not out.exists();out.write_text(json.dumps(result,indent=2))
    print(json.dumps(dict(status=result['status'],cases=len(records),updates=sum(r['updates'] for r in records),bad=[r for r in records if r['bad']],CPU_s=result['CPU_s'])))

    assert result['status']=='PASS'


if __name__=='__main__':main()
