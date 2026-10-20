"""Current visible near-car profiles retain the original material/veto guards."""
import json
from pathlib import Path
import sys
import time
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'submit_core'))
import observation_agent as a


def check():
    cpu=time.process_time();image=np.full((84,84),102/255,np.float32)
    profile=np.array([160,160,145,115,102,102,102,102])/255
    index=60;ids=index-np.arange(-3,5)
    image[54,ids]=profile;image[55,ids]=profile
    blocked=np.zeros((84,84),bool);paint=np.zeros_like(blocked)
    def call(y,mask=blocked,p=paint,max_row=55):
        return a.recover_plain_run_edge(image,y,index,-1,mask,p,(55,61),max_row=max_row)
    at54=call(54);assert at54 is not None
    assert call(55)is None
    at55=call(55,max_row=69);assert at55 is not None and abs(at54-at55)<1e-12
    opaque=blocked.copy();opaque[55,index]=True
    assert call(55,mask=opaque,max_row=69)is None
    painted=paint.copy();painted[55,60:64]=True
    assert call(55,p=painted,max_row=69)is None
    # The palette fallback's old row domain is deliberately unchanged.
    assert a.recover_shaded_run_edge(image,54,index,-1,blocked)is None
    return dict(status='PASS',row54_original_plain_domain=True,
        near_plain_requires_explicit_domain=True,current_opaque_sample_rejected=True,
        paint_rejected=True,shaded_domain_unchanged=True,CPU_s=time.process_time()-cpu,
        model_ticks=0,native_actions=0)


if __name__=='__main__':print(json.dumps(check()))
