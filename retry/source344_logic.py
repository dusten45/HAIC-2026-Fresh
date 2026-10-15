"""Same342birth rule; metadata follows the original296straight fallback only."""
import cv2
import numpy as np


def birth_evidence(image,direct):
    road=((image>.32)&(image<.47)).astype(np.uint8);road[61:]=0
    closed=cv2.morphologyEx(road,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    holes=((closed!=0)&(road==0)&(image>=.64)&(image<=.71)).astype(np.uint8);holes[61:]=0
    count,labels,stats,centroids=cv2.connectedComponentsWithStats(holes,connectivity=8);out=[]
    for index in range(1,count):
        _,_,width,height,area=stats[index]
        if not (3<=area<=30 and 2<=width<=9 and 2<=height<=9):continue
        cx,cy=centroids[index];metric=[(float(cx)-41.542)/1.3608,(62.4475-float(cy))/1.701,1.2]
        mask=(labels==index).astype(np.uint8);ring=(cv2.dilate(mask,np.ones((3,3),np.uint8))!=0)&(mask==0)
        neighbors=int(road[ring].sum())
        out.append(dict(point=metric,raw_road_neighbors=neighbors,low=neighbors==0,component_area=int(area)))
    assert [q['point'] for q in out]==[list(p) for p in direct]
    return out


def advance_evidence(tracker,previous,step,image):
    assert len(previous)==len(tracker['before']);pending=[];origins=[]
    for index,((x,y,radius,age),evidence) in enumerate(zip(tracker['before'],previous)):
        if tracker['affine'] is None:
            y-=tracker['current_speed']*.08
        else:
            pixel=np.asarray(tracker['affine'])@np.array([41.542+1.3608*x,62.4475-1.701*y,1])
            x,y=(pixel[0]-41.542)/1.3608,(62.4475-pixel[1])/1.701
        if age<8 and abs(x)<=35 and -5<=y<=35:
            pending.append(dict(point=[float(x),float(y),radius,age+1],evidence=evidence));origins.append(index)
    births=birth_evidence(image,tracker['direct'])
    for index,birth in enumerate(births):
        x,y,radius=birth['point'];keep=[j for j,q in enumerate(pending) if np.hypot(q['point'][0]-x,q['point'][1]-y)>2]
        pending=[pending[j] for j in keep];origins=[origins[j] for j in keep]
        item=dict(birth,uid=[step,index])
        pending.append(dict(point=[x,y,radius,0],evidence=item));origins.append(-index-1)
        births[index]=item
    a=np.asarray([q['point'] for q in pending]).reshape(-1,4);b=np.asarray(tracker['after']).reshape(-1,4)
    assert a.shape==b.shape and np.allclose(a,b,rtol=0,atol=1e-12)
    return dict(after=[q['evidence'] for q in pending],births=births,lineage=origins)
