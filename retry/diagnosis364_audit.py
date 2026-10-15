"""Reconstruct pixel birth evidence and geometric labels from saved records only."""
from pathlib import Path
import sys,time
import cv2
import numpy as np
from retry.path271_run import read,save,sha
from retry.diagnosis364_stage import verify
from retry.diagnosis364_run import rows
from retry.lineage339_audit import components,track
from retry.support342_logic import advance_evidence
from retry.confidence341_run import label

def descriptor(frame,c):
    mask=np.zeros((84,84),np.uint8);xy=np.array(c['pixel_xy']);mask[xy[:,1],xy[:,0]]=1;ring=(cv2.dilate(mask,np.ones((3,3),np.uint8))!=0)&(mask==0);padded=np.pad(mask,1);allring=(cv2.dilate(padded,np.ones((3,3),np.uint8))!=0)&(padded==0);image=frame.astype(np.float32)/255;road=((image>.32)&(image<.47)).astype(np.uint8);road[61:]=0;wide=(cv2.dilate(mask,np.ones((7,7),np.uint8))!=0)&(mask==0);x,y,w,h=c['bbox']
    return dict(area_pixels=c['area'],bbox_xywh=c['bbox'],width=w,height=h,aspect_width_over_height=w/h,component_gray_range=[min(c['gray_values']),max(c['gray_values'])],touches_left=x==0,touches_right=x+w==84,touches_top=y==0,touches_HUD_mask=y+h==61,raw_road_neighbors=int(road[ring].sum()),observed_ring_pixels=int(ring.sum()),outside_unobserved_ring_positions=int(allring.sum()-ring.sum()),ring_gray_range=[int(frame[ring].min()),int(frame[ring].max())],raw_road_pixels_in_existing7x7_neighborhood=int(road[wide].sum()))

def run(R):
    D=R/'stage364';p=verify(R,True);assert not (D/'audit-private.json').exists();wall=time.perf_counter();cpu=time.process_time();out={};private={}
    for key,prefix,limit,window,target in [('T29510','stage363/T29510/B',66,(55,65),59),('N2','stage359/B',131,(118,131),121)]:
        rr=rows(R/prefix/'trace-private.jsonl');frames=np.load(R/prefix/'frames-actions-private.npz')['frames_uint8'];lineage=track(rr[:limit]);prev=[];births={};details=[]
        for i,x in enumerate(rr[:limit]):
            assert sha_image(frames[i])==x['actor_state']['previous_image_sha256'];comp=components(frames[i]);assert [c['metric'] for c in comp]==x['tracker']['direct'];sr=advance_evidence(x['tracker'],prev,i+1,frames[i].astype(np.float32)/255);assert sr==x['support_record'];prev=sr['after'];lr=lineage['records'][i]
            for j,(c,b) in enumerate(zip(comp,sr['births'])):
                legal=descriptor(frames[i],c);assert legal['raw_road_neighbors']==b['raw_road_neighbors'];lab,idx=label(b['point'],x['pre_physical']);incoming=[a for a in lr['associations'] if a['new_tag']==f'{i+1}:{j}'];prior_positive=bool(len(incoming)==1 and births[incoming[0]['old_tag']]['positive_history'])
                item=dict(action=i+1,uid=b['uid'],legal_pixel_features=legal,raw_birth_low=b['low'],unique_predecessor=len(incoming)==1,prior_positive_history=prior_positive,current_road_positive=b['raw_road_neighbors']>0,positive_history=prior_positive or b['raw_road_neighbors']>0,predecessors=[dict(old_tag=a['old_tag'],distance_m=a['distance_m']) for a in incoming],posthoc_geometric_label=lab)
                births[f'{i+1}:{j}']=item
                if window[0]<=i+1<=window[1]:details.append(item)
        life=[]
        for x,lr in zip(rr[:limit],lineage['records']):
            for j,(h,b) in enumerate(zip(x['tracker']['after'],x['support_record']['after'])):
                if b['uid']!=[target,0]:continue
                life.append(dict(action=x['step'],age=h[3],low=b['low'],routed=j not in x['routing_evidence']['removed_indices'],optical_reason=lr['optical_reason'],mode=lr['points'][j]['mode'],direct_detections=len(x['tracker']['direct']),full_tracker_preserved=True))
        targetitem=births[f'{target}:0'];expiries=[dict(action=lr['step'],reason=e['reason']) for lr in lineage['records'] for e in lr['expiries'] if e['item']['tag']==f'{target}:0']
        out[key]=dict(target_birth=targetitem,nearby_direct_births=details,target_life=life,expiry=expiries,tracker_and_metadata_reconstructed_inputs=limit,lineage_maximum_error=lineage['maximum_reconstruction_error']);private[key]=dict(lineage=lineage,target_birth=targetitem)
    assert out['T29510']['target_birth']['prior_positive_history'] and not out['N2']['target_birth']['prior_positive_history']
    assert [x['action'] for x in out['T29510']['target_life'] if not x['routed']]==[60,61,62,63] and [x['action'] for x in out['N2']['target_life'] if not x['routed']]==list(range(122,130))
    save(D/'audit-private.json',out);save(D/'lineage-private.json',private);save(D/'audit-cost.json',dict(wall_s=time.perf_counter()-wall,CPU_s=time.process_time()-cpu,metadata_updates=197,tracker_updates=197,detector_reconstructions=197,new_actor=0,new_native=0));print({k:v['target_birth'] for k,v in out.items()},flush=True)
def sha_image(image):
    import hashlib
    return hashlib.sha256(image.tobytes()).hexdigest()
if __name__=='__main__':run(Path(sys.argv[1]).resolve())
