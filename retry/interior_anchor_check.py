"""Public fixed-width synthetic anchor omission; no model/environment use."""
import importlib.util
import json
from pathlib import Path
import sys
import time
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'submit_core'))
import runtime598
spec=importlib.util.spec_from_file_location('anchor_observation_agent',ROOT/'submit_core/observation_agent.py')
a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)


def original_rows(asphalt,cover):
    rows={}
    for y in np.flatnonzero(np.any(cover,axis=1)):
        raw=asphalt[y].astype(bool)&~cover[y].astype(bool)
        z=np.diff(np.pad(raw,(1,1)).astype(np.int16));starts=np.flatnonzero(z==1);ends=np.flatnonzero(z==-1)
        good=ends-starts>=3;starts,ends=starts[good],ends[good]
        left=[i for i in range(len(starts))if ends[i]<=np.ceil(a.IMAGE_ORIGIN_X)]
        right=[i for i in range(len(starts))if starts[i]>=np.floor(a.IMAGE_ORIGIN_X)]
        if not left or not right:continue
        l=max(left,key=lambda i:ends[i]);r=min(right,key=lambda i:starts[i]);lo,hi=int(ends[l]),int(starts[r])
        if lo>=hi or np.any((~asphalt[y,lo:hi].astype(bool))&~cover[y,lo:hi].astype(bool)):continue
        if starts[l]==0 or ends[r]>=84:continue
        if cover[y,starts[l]-1]or cover[y,ends[r]]:continue
        rows[int(y)]=(int(starts[l]),int(ends[r]-1),lo,hi)
    return rows


def find_fixture():
    yy,xx=np.indices((84,84));wx=(xx-a.IMAGE_ORIGIN_X)/a.OBJECT_SX;wy=(a.IMAGE_ORIGIN_Y-yy)/a.OBJECT_SY
    joint,slope,offset=.2,-.4,-1.8
    road=np.abs(wx-slope*wy-offset)<=40/6*np.sqrt(1+slope*slope)
    cover=a.vehicle_projection_mask(joint)
    image=np.where(road,100,162).astype(np.float32)/255;image[cover.astype(bool)]=20/255
    asphalt=((image>.36)&(image<.47)).astype(np.uint8);base=original_rows(asphalt,cover)
    fixture=dict(joint=joint,slope=slope,offset_m=offset,row=59,lo=46,hi=48,base_rows=base)
    return fixture,image,asphalt,cover


def helper_checks(fixture,image,asphalt,cover):
    helper=a.interior_two_sample_anchor;sy,lo,hi=fixture['row'],fixture['lo'],fixture['hi']
    obstacle=np.zeros((84,84),bool);grass=a.coherent_grass_mask(image);base=fixture['base_rows']
    def call(im=image,raw=asphalt,cov=cover,obj=obstacle,gr=grass,y=sy,l=lo,h=hi,rows=base):
        return bool(helper(im,raw,cov,obj,gr,y,l,h,rows))
    assert call();passed=['positive_six_visible_raw_samples']
    assert not call(h=hi+1);passed.append('not_exactly_two')
    for missing in (sy-1,sy+1):
        rows={k:v for k,v in base.items()if k!=missing}
        assert not call(rows=rows);passed.append('original_neighbor_missing_'+str(missing))
    assert not call(y=0);passed.append('endpoint')
    raw=asphalt.copy();raw[sy-1,lo]=0
    assert not call(raw=raw);passed.append('same_columns_missing')
    cov=cover.copy();cov[sy+1,hi-1]=1
    assert not call(cov=cov);passed.append('covered_sample')
    obj=obstacle.copy();obj[sy,lo]=1
    assert not call(obj=obj);passed.append('object_sample')
    gr=grass.copy();gr[sy,lo]=1
    assert not call(gr=gr);passed.append('grass_sample')
    im=image.copy();im[sy,lo]=108/255
    assert not call(im=im);passed.append('raw_road_but_range_eight')
    return passed


def integration_checks(fixture,image,asphalt,cover):
    sy=fixture['row'];joint=fixture['joint'];cases=[]
    def reject(name,im,obj=None):
        raw=((im>.36)&(im<.47)).astype(np.uint8)
        if obj is None:obj=np.zeros((84,84),bool)
        support,info=a.infer_local_road_support(im,raw,obj,joint,False,10.)
        assert not np.any(support[sy].astype(bool)&cover[sy].astype(bool)), name
        cases.append(name)
    # Keep only two samples on the OTHER flank: neither side is original >=3.
    im=image.copy();left=np.flatnonzero(asphalt[sy]&~cover[sy].astype(bool)&(np.arange(84)<a.IMAGE_ORIGIN_X))
    im[sy,left[:-2]]=162/255;reject('opposite_flank_below_three',im)
    im=image.copy();im[sy-1,46:48]=162/255;im[sy+1,46:49]=162/255
    reject('no_recursive_neighbor_fill',im)
    # Remove the last currently visible left-flank road pixel. It becomes a
    # nonopaque missing pixel inside the proposed gap, not inferred pavement.
    im=image.copy();im[sy,left[-1]]=124/255
    reject('visible_nonopaque_gap_missing',im)
    obj=np.zeros((84,84),bool);obj[sy,41]=True
    reject('object_inside_opaque_gap',image.copy(),obj)
    im=image.copy();im[sy-1:sy+2,40:43]=162/255
    reject('grass_inside_gap',im)
    # Shift only this row's outer left edge beyond the frozen line interval.
    im=image.copy();im[sy,left[:4]]=162/255
    reject('frozen_line_and_width_mismatch',im)
    return cases


def check():
    cpu=time.process_time();fixture,image,asphalt,cover=find_fixture();sy=fixture['row'];lo,hi=fixture['lo'],fixture['hi']
    assert sy not in fixture['base_rows']and sy-1 in fixture['base_rows']and sy+1 in fixture['base_rows']
    assert hi-lo==2 and np.all(asphalt[sy-1:sy+2,lo:hi])and not np.any(cover[sy-1:sy+2,lo:hi])
    helper_present=hasattr(a,'interior_two_sample_anchor')
    support,info=a.infer_local_road_support(image,asphalt,np.zeros((84,84),bool),fixture['joint'],False,10.)
    if helper_present:
        negatives=helper_checks(fixture,image,asphalt,cover)
        integration=integration_checks(fixture,image,asphalt,cover)
        assert np.any(support[sy]), 'full infer must recover the original missing interior row'
    else:
        negatives=[];integration=[]
        assert not np.any(support[sy])
    return dict(status='MINIMAL_ANCHOR_CHECK_PASS'if helper_present else'BASELINE_INTERIOR_ANCHOR_OMISSION_REPRODUCED',fixture=fixture,info=info,recovered_row_pixels=np.flatnonzero(support[sy]).tolist(),road_width_m=40/3,turn_per_node_rad=0.,helper_cases_passed=negatives,integration_cases_passed=integration,new_helper_present=helper_present,model_ticks=0,native=0,CPU_s=time.process_time()-cpu)


if __name__=='__main__':print(json.dumps(check(),sort_keys=True))
