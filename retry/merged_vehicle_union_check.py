"""Visible broad pavement is a union-inclusion observation, not one lane."""
from pathlib import Path
import sys,json,time
import numpy as np
from retry.fov_vehicle_support_check import scene,a,c


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[]
    cases=[('left',8.,57.7,False),('left',20.,59.2,True),('left',26.,61.2,False),
           ('right',76.,57.7,False),('right',64.,59.2,True),('right',58.,61.2,False)]
    half=(40./6.)*1.3608;base_left=a.IMAGE_ORIGIN_X-half;base_right=a.IMAGE_ORIGIN_X+half
    for side,extent,junction,paint in cases:
      for joint in (-.25,.25):
        bl=extent if side=='left' else base_left;br=base_right if side=='left' else extent
        image,left,right=scene(junction,joint,paint,bl,br);asphalt=((image>.36)&(image<.47)).astype(np.uint8)
        support,info=a.infer_local_road_support(image,asphalt,np.zeros((84,84),bool),joint,False,30.)
        yy,xx=np.nonzero(support)
        outside=sum(not((left<=x<=right) or (y<=junction and bl<=x<=br)) for y,x in zip(yy,xx))
        observer=a.Agent();observer.last_root=object();observer.joint=joint;geometry,_,_,_=observer._map(image);root=observer._root(geometry,0.)
        pixel=(bl+3 if side=='left' else br-3,junction-3)
        point=((pixel[0]-a.IMAGE_ORIGIN_X)/1.3608,(a.IMAGE_ORIGIN_Y-pixel[1])/1.701)
        preserved=any(c.inside(point,poly) for poly,_ in geometry.roads)
        record=dict(side=side,extent=extent,junction=junction,joint=joint,paint=paint,outside=outside,
            union_extension_rows=info.get('road_support_union_extension_rows',0),
            wide_union_rows=info.get('road_support_wide_union_rows',0),
            current_margin_m=geometry.margin(root),observed_wide_union_preserved=preserved)
        records.append(record)
    assert all(r['outside']==0 and r['current_margin_m']>.5 and r['observed_wide_union_preserved'] for r in records),records
    assert any(r['wide_union_rows'] and r['union_extension_rows'] for r in records),'NONVACUOUS_MERGE_SUPPORT'
    result=dict(status='PASS',cases=len(records),records=records,CPU_s=time.process_time()-cpu,
        model_ticks=0,native_actions=0,scope='Finite public vehicle/road-union raster tests. No hidden-obstacle or universal reconstruction claim.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
