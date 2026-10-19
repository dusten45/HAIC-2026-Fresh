"""Public synthetic pixels: feasible flank intervals can reject an OLS line.

Uses only public vehicle projection, road width and material colours. No case
pixels, recorded actions, private coordinates or simulator/model calls.
"""
from pathlib import Path
import json,sys,time
import cv2,numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a


def fixture(paint=True,step=3):
    cover=a.vehicle_projection_mask(0.)>0
    ys=np.flatnonzero(np.any(cover,axis=1));middle=int(ys[len(ys)//2])
    half=(40./6.)*1.3608
    left=int(round(a.IMAGE_ORIGIN_X-half));right=int(round(a.IMAGE_ORIGIN_X+half))
    image=np.full((84,84),162/255.,np.float32)
    image[:,left:right+1]=102/255.
    # A finite material-boundary perturbation has one clear flank sample;
    # the neighbouring white material makes other flank samples intervals.
    image[middle,left:left+step]=162/255.
    if paint:image[:,left-3]=1.
    opaque=cv2.erode(cover.astype(np.uint8),np.ones((3,3),np.uint8))>0
    image[opaque]=61/255.
    return image,cover,middle


def evaluate(image,initial=False,obstacle=None):
    blocked=np.zeros((84,84),bool) if obstacle is None else obstacle
    asphalt=((image>.36)&(image<.47)).astype(np.uint8);captured={}
    def trace(frame,event,arg):
        if frame.f_code is a.infer_local_road_support.__code__ and event=='return':
            captured.update(frame.f_locals)
        return trace
    previous=sys.gettrace();sys.settrace(trace)
    try:support,info=a.infer_local_road_support(image,asphalt,blocked,0.,initial,0.)
    finally:sys.settrace(previous)
    return support,info,captured


def main():
    out=Path(sys.argv[1]);assert not out.exists();cpu=time.process_time();records=[]
    image,cover,middle=fixture();support,info,locals_=evaluate(image)
    assert locals_.get('interval_fit_failed') is True,'PUBLIC_FIXTURE_DID_NOT_CHALLENGE_OLS'
    assert info.get('road_support_interval_parallel_used') and np.any(support),'FEASIBLE_INTERVALS_REJECTED'
    assert not np.any(support&((image>156/255.)&(image<184/255.))),'VISIBLE_GRASS_FILLED'
    records.append(dict(name='failed_OLS_feasible_public_intervals',inferred_pixels=int(support.sum()),
        failed_OLS=True,common_interval_fit_used=True))
    support,info,_=evaluate(image,initial=True)
    assert not np.any(support),'SPAWN_OLS_POLICY_CHANGED'
    records.append(dict(name='spawn_policy_retained',inferred_pixels=0))
    image,cover,middle=fixture(paint=False)
    support,info,locals_=evaluate(image)
    assert locals_.get('interval_fit_failed') is True and not np.any(support),'IMPOSSIBLE_INTERVALS_ACCEPTED'
    records.append(dict(name='infeasible_plain_flanks_rejected',inferred_pixels=0))
    image,cover,middle=fixture();blocked=cover.copy()
    support,info,_=evaluate(image,obstacle=blocked)
    assert not np.any(support&blocked) and not np.any(support),'OBSTACLE_VETO_IGNORED'
    records.append(dict(name='obstacle_veto',inferred_pixels=0))
    image,cover,middle=fixture();image[cover]=162/255.
    support,info,_=evaluate(image)
    assert not np.any(support),'COHERENT_VISIBLE_GRASS_FILLED'
    records.append(dict(name='current_grass_veto',inferred_pixels=0))
    result=dict(status='PASS',cases=len(records),records=records,CPU_s=time.process_time()-cpu,
        model_ticks=0,native_actions=0,scope='Finite public synthetic pixel counterexamples; unchanged original allowances, width checks, spawn policy and vetoes. Not a universal road-support guarantee.')
    out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
