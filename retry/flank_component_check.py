"""Public straight-road multirow anchor-availability regression; model-free."""
import json
import time
import numpy as np
from interior_anchor_check import a, original_rows


def find_fixture():
    yy,xx=np.indices((84,84));wx=(xx-a.IMAGE_ORIGIN_X)/a.OBJECT_SX;wy=(a.IMAGE_ORIGIN_Y-yy)/a.OBJECT_SY
    joint,slope,offset=.2,-.4,-2.
    cover=a.vehicle_projection_mask(joint)
    road=np.abs(wx-slope*wy-offset)<=40/6*np.sqrt(1+slope*slope)
    image=np.where(road,100,162).astype(np.float32)/255;image[cover.astype(bool)]=20/255
    raw=((image>.36)&(image<.47)).astype(np.uint8);base=original_rows(raw,cover)
    first,last,lo,hi=58,61,46,48
    assert first in base and last in base and all(y not in base for y in range(first+1,last))
    assert np.all(raw[first:last+1,lo:hi]) and not np.any(cover[first:last+1,lo:hi])
    distance=(last-first)/a.OBJECT_SY*np.sqrt(1+slope*slope)
    assert distance<=21/6
    support,info=a.infer_local_road_support(image,raw,np.zeros((84,84),bool),joint,False,10.)
    return dict(joint=joint,slope=slope,offset_m=offset,first_anchor=first,last_anchor=last,missing_rows=list(range(first+1,last)),lo=lo,hi=hi,bracket_distance_m=float(distance),base_rows=base,info=info),image,raw,cover


def integration_checks(f,image,raw,cover):
    block=f['missing_rows'];first,last=f['first_anchor'],f['last_anchor'];lo,hi=f['lo'],f['hi'];cases=[]
    def reject(name,im,obj=None):
        if obj is None:obj=np.zeros((84,84),bool)
        asphalt=((im>.36)&(im<.47)).astype(np.uint8)
        support,info=a.infer_local_road_support(im,asphalt,obj,f['joint'],False,10.)
        assert not any(np.any(support[y].astype(bool)&cover[y].astype(bool))for y in block),name
        cases.append(name)
    im=image.copy();im[block[0],lo]=108/255;reject('one_bad_shade_rejects_whole_component',im)
    im=image.copy();im[block[-1],lo]=162/255;reject('missing_same_column_rejects_whole_component',im)
    im=image.copy();im[first,lo:hi]=162/255;reject('missing_original_start_anchor',im)
    im=image.copy();im[last,lo:hi]=162/255;reject('missing_original_end_anchor',im)
    y=block[0];xs=np.flatnonzero(raw[y]&~cover[y].astype(bool)&(np.arange(84)<a.IMAGE_ORIGIN_X))
    im=image.copy();im[y,xs[:-2]]=162/255;reject('one_bad_opposite_flank_atomic',im)
    obj=np.zeros((84,84),bool);obj[y,41]=True;reject('one_gap_object_atomic',image.copy(),obj)
    im=image.copy();im[y-1:y+2,40:43]=162/255;reject('coherent_gap_grass',im)
    im=image.copy();im[y,xs[-1]]=124/255;reject('visible_nonopaque_gap_missing_atomic',im)
    im=image.copy();im[y,xs[:4]]=162/255;reject('one_frozen_line_width_mismatch_atomic',im)
    return cases


def helper_checks(f,image,raw,cover):
    runs=[(y,1,f['lo'],f['hi'])for y in f['missing_rows']]
    obj=np.zeros((84,84),bool);grass=a.coherent_grass_mask(image);base=f['base_rows'];cases=[]
    def call(im=image,asphalt=raw,cov=cover,obstacle=obj,gr=grass,r=runs,b=base,slope=.32):
        return a.observed_flank_component(im,asphalt,cov,obstacle,gr,r,b,slope)
    assert call();cases.append('connected_current_component_positive')
    assert not call(r=[runs[0],(runs[1][0],1,48,50)]);cases.append('disconnected_columns')
    assert not call(r=[runs[0],(runs[1][0]+1,1,46,48)]);cases.append('nonconsecutive_rows')
    assert not call(r=[runs[0],(runs[1][0],0,46,48)]);cases.append('mixed_sides')
    assert not call(b={y:v for y,v in base.items()if y!=f['first_anchor']});cases.append('missing_original_anchor')
    assert not call(slope=100.);cases.append('existing_tile_span_cap')
    cov=cover.copy();cov[runs[0][0],46]=1
    assert not call(cov=cov);cases.append('current_cell_vehicle_opaque')
    obstacle=obj.copy();obstacle[runs[-1][0],47]=1
    assert not call(obstacle=obstacle);cases.append('current_cell_obstacle')
    gr=grass.copy();gr[runs[0][0],46]=1
    assert not call(gr=gr);cases.append('current_cell_grass')
    im=image.copy();im[runs[0][0],46]=108/255
    assert not call(im=im);cases.append('current_component_gray_range')
    return cases


def check():
    cpu=time.process_time();f,image,raw,cover=find_fixture()
    present=hasattr(a,'observed_flank_component')
    support,info=a.infer_local_road_support(image,raw,np.zeros((84,84),bool),f['joint'],False,10.)
    if present:
        helpers=helper_checks(f,image,raw,cover);negatives=integration_checks(f,image,raw,cover)
        assert all(np.any(support[y].astype(bool)&cover[y].astype(bool))for y in f['missing_rows'])
    else:
        helpers=[];negatives=[]
        assert not any(np.any(support[y].astype(bool)&cover[y].astype(bool))for y in f['missing_rows'])
    return dict(status='GENERAL_COMPONENT_CHECK_PASS'if present else'BASELINE_MULTIROW_OMISSION_REPRODUCED',fixture=f,info=info,helper_cases_passed=helpers,integration_cases_passed=negatives,road_width_m=40/3,turn_per_node_rad=0.,model_ticks=0,native=0,CPU_s=time.process_time()-cpu)


if __name__=='__main__':print(json.dumps(check(),sort_keys=True))
