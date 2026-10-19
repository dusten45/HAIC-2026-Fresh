"""Public raster counterexamples to shrinking an observed object hole by best fit.

Physical source polygons score error only; no simulator or case inputs.
"""
from pathlib import Path
import sys
import os,time,json,math,hashlib
os.environ['SDL_VIDEODRIVER']='dummy'
import numpy as np,cv2,pygame
from pygame import gfxdraw
cpu=time.process_time();records=[];images=[];polygons=[]
sx,sy=1.3608,1.701;R=1.2
for shade in (102,104,107):
 for phase in (0.,.25,.5,.75):
  for oi in range(8):
   angle=oi*math.pi/64;center=np.array([41.5+phase,35.5+phase/2]);theta=angle+np.arange(16)*2*math.pi/16
   poly=center+R*np.column_stack((sx*np.cos(theta),sy*np.sin(theta)))
   surf=pygame.Surface((1000,800));surf.fill((shade,)*3)
   source=[((x+.5)*1000/84-.5,799-((y+.5)*800/84-.5)) for x,y in poly]
   gfxdraw.aapolygon(surf,source,(255,165,0));gfxdraw.filled_polygon(surf,source,(255,165,0))
   surf=pygame.transform.smoothscale(pygame.transform.flip(surf,False,True),(96,96));rgb=np.transpose(np.array(pygame.surfarray.pixels3d(surf)),(1,0,2));im=cv2.cvtColor(cv2.resize(rgb,(84,84)),cv2.COLOR_RGB2GRAY)
   # Mid-level edge inversion from actual grayscale, with the known public
   # colors only. Public fixture truth below is used solely to score error.
   level=(shade+(.299*255+.587*165))/2;edges=[];errors=[]
   for y in range(31,41):
    line=im[y].astype(float);changes=np.flatnonzero((line[:-1]-level)*(line[1:]-level)<0)
    exact=[]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
     if (a[1]<=y<b[1]) or (b[1]<=y<a[1]):exact.append(a[0]+(y-a[1])/(b[1]-a[1])*(b[0]-a[0]))
    for x in changes:
     edge=x+(level-line[x])/(line[x+1]-line[x]);edges.append([edge/sx,y/sy])
     if exact:errors.append(min(abs(edge-v) for v in exact)/sx)
   p=np.array(edges);row=dict(shade=shade,phase=phase,angle_rad=angle,halfplane_edge_errors_m=errors,contour_points=len(p),image_sha256=hashlib.sha256(im.tobytes()).hexdigest())
   if len(p)>=3:
    coef=np.linalg.lstsq(np.column_stack((2*p,np.ones(len(p)))),np.sum(p*p,axis=1),rcond=None)[0];radius=math.sqrt(max(0,coef[2]+coef[:2]@coef[:2]));truth=poly/np.array([sx,sy]);miss=np.max(np.linalg.norm(truth-coef[:2],axis=1)-radius)
    row.update(circle_fit_radius_m=radius,circle_center_error_m=float(np.linalg.norm(coef[:2]-center/[sx,sy])),circle_undercoverage_m=float(miss))
   records.append(row);images.append(im);polygons.append(poly)
# Exact full-image equivalence is checked, not assumed from near similarity.
exact=[];near=[]
for i in range(96):
 for j in range(i):
  if records[i]['shade']!=records[j]['shade'] or records[i]['phase']!=records[j]['phase']:continue
  delta=int(np.max(abs(images[i].astype(int)-images[j].astype(int))))
  if delta==0:exact.append([j,i])
  elif delta<=1:near.append([j,i])
res=dict(status='COUNTEREXAMPLE_MEASURED',configurations=len(records),CPU_s=time.process_time()-cpu,model_ticks=0,native_actions=0,exact_equal_full_image_pairs=exact,max_gray_difference_le1_pairs=near,max_halfplane_edge_error_m=max(max(r['halfplane_edge_errors_m'],default=0) for r in records),max_circle_undercoverage_m=max(r.get('circle_undercoverage_m',0) for r in records),circle_undercoverage_cases=sum(r.get('circle_undercoverage_m',0)>0 for r in records),records=records,scope='Public16-gon radius1.2 and exact public two-stage raster chain only. No case images/state/map. Algebraic best circle and half-level inversion are illustrative simple estimators, not the optimum of all possible estimators. Near-equal images are NOT exact ambiguity. No production correction established.')
assert res['configurations']==96 and res['circle_undercoverage_cases']>0
assert res['max_halfplane_edge_error_m']>.35
path=Path(sys.argv[1]);assert not path.exists();path.write_text(json.dumps(res,indent=2)+'\n')
print(json.dumps({k:v for k,v in res.items() if k!='records'}))
