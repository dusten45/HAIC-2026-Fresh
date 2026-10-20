"""Read-only pixel provenance audit, never a whole-cell road classifier.

The recorded84 image contains no recoverable high-resolution material labels.
Conditional threshold/erosion eligibility is retained separately from UNKNOWN
whole-cell material status. Synthetic mixture examples test preprocessing only;
they are not claimed to obey the complete HAIC track grammar.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time
import cv2
import numpy as np


def sample_support(x,y):
    """Conservative candidate source box, AFTER public vertical surface flip.

    OpenCV linear96->84 uses two96 samples per axis; pygame's shrink filter
    integrates source boxes. One extra1000/800-source pixel guards integer
    endpoints. This records a support bound, not an inverse material proof.
    """
    u=(x+.5)*96/84-.5;v=(y+.5)*96/84-.5
    j,k=math.floor(u),math.floor(v)
    js=sorted(set((max(0,min(95,j)),max(0,min(95,j+1)))))
    ks=sorted(set((max(0,min(95,k)),max(0,min(95,k+1)))))
    bounds=[max(0,math.floor(js[0]*1000/96)-1),max(0,math.floor(ks[0]*800/96)-1),
            min(1000,math.ceil((js[-1]+1)*1000/96)+1),min(800,math.ceil((ks[-1]+1)*800/96)+1)]
    return dict(intermediate96_x=js,intermediate96_y=ks,highres_xyxy_exclusive=bounds,
                highres_coordinates='1000x800 RGB after vertical surface flip',
                mapping_status='CONSERVATIVE_BOX_FILTER_SUPPORT_BOUND_NOT_MATERIAL_CERTIFICATE')


def mixture_counterexample():
    import pygame
    def pipeline(rgb):
        surface=pygame.surfarray.make_surface(np.transpose(rgb,(1,0,2)))
        small=pygame.transform.smoothscale(surface,(96,96))
        rgb96=np.transpose(np.array(pygame.surfarray.pixels3d(small)),(1,0,2))
        return cv2.cvtColor(cv2.resize(rgb96,(84,84)),cv2.COLOR_RGB2GRAY)
    road_results={}
    for color in (102,104,107):
        rgb=np.full((800,1000,3),color,np.uint8);out=pipeline(rgb)
        road_results[int(out[40,40])]=color
    for period in range(5,21):
        for width in range(1,min(5,period)):
            for phase in range(period):
                rgb=np.zeros((800,1000,3),np.uint8);rgb[:,:,0]=255
                white=(np.arange(1000)+phase)%period<width;rgb[:,white]=255
                out=pipeline(rgb);gray=int(out[40,40]);raw=(out/255>.36)&(out/255<.47)
                if gray in road_results and np.all(raw[39:42,39:42]):
                    # Erosion is the actual visible_road_evidence local rule.
                    eroded=cv2.erode(raw.astype(np.uint8),np.ones((3,3),np.uint8))
                    assert eroded[40,40]
                    return dict(status='PASS',pixel=[40,40],same_gray=gray,
                        scene_A=dict(material='asphalt',uniform_source_RGB=[road_results[gray]]*3),
                        scene_B=dict(materials=['red paint','white paint'],source_RGB=[[255,0,0],[255,255,255]],vertical_stripe_period_source_px=period,white_width_source_px=width,phase_source_px=phase,asphalt_source_fraction=0),
                        scene_B_output3x3=out[39:42,39:42].tolist(),scene_B_output3x3_gray_range=int(np.ptp(out[39:42,39:42])),threshold_and3x3_erosion_both_accept=True,
                        scope='Exact public pygame shrink+OpenCV resize/grayscale pipeline; synthetic paint arrangement, not a full HAIC-valid track construction.')
    raise AssertionError('No bounded synthetic mixture alias found')


def audit(checkpoint,output):
    cpu=time.process_time();directory=Path(checkpoint);stack=np.load(directory/'input-private.npy');frame=stack[-1];saved=json.loads((directory/'checkpoint-private.json').read_text());sys.path.insert(0,str(directory/'package'))
    spec=importlib.util.spec_from_file_location('source_audit_agent',directory/'package/agent.py');a=importlib.util.module_from_spec(spec);sys.modules[spec.name]=a;spec.loader.exec_module(a)
    joint=saved['root']['planar']['joints'][0];opaque=a.vehicle_projection_mask(joint).astype(bool);detections,object_mask=a.detect_observed_obstacles(frame);grass=a.coherent_grass_mask(frame);conditional=a.visible_road_evidence(frame).astype(bool);frame_hash=hashlib.sha256(frame.tobytes()).hexdigest();records=[]
    for y in range(84):
        for x in range(84):
            value=float(frame[y,x]);gray=int(round(value*255));exclusions=[]
            if y<5 or y>=70 or x<1 or x>82:exclusions.append('OUTSIDE_AGENT_ROAD_DOMAIN_OR_HUD')
            if opaque[y,x]:exclusions.append('VEHICLE_PROJECTION_WITH_RASTER_FRINGE')
            if object_mask[y,x]:exclusions.append('CURRENT_OBJECT_DETECTOR_BLOCKED')
            if grass[y,x]:exclusions.append('CURRENT_COHERENT_GRASS')
            if 55<=y<70 and 34<=x<51:exclusions.append('BASELINE_FIXED_VEHICLE_EXCLUSION')
            records.append(dict(frame_id=frame_hash,pixel_xy=[x,y],raw_float32=value,quantized_gray_u8=gray,
                quantization_reconstruction_error=abs(value-gray/255),source_sample_support=sample_support(x,y),
                output_cell_xyxy=[x-.5,y-.5,x+.5,y+.5],visibility='CURRENT_OPAQUE_OBJECT_OR_VEHICLE_OR_HUD'if opaque[y,x]or object_mask[y,x]or y>=70 else'CURRENT_UNOBSCURED_BY_KNOWN_MASKS',
                visibility_basis='Known current vehicle/object masks and HUD only; material or conservative operator exclusions do not imply occlusion',
                exclusions=exclusions,raw_asphalt_threshold=bool(.36<value<.47),
                baseline_visible_road_evidence_eligible=bool(conditional[y,x]),
                conditional_sourceeligible=bool(conditional[y,x]and not exclusions),
                sourceeligible_status='CONDITIONAL_VISIBLE_THRESHOLD_INTERIOR'if conditional[y,x]and not exclusions else'NOT_ELIGIBLE',
                whole_source_support_material='UNKNOWN',whole_cell_road_certificate=None))
    result=dict(frame_id=frame_hash,stack_sha256=hashlib.sha256(stack.tobytes()).hexdigest(),call=saved['call'],stack_index=len(stack)-1,frame_shape=list(frame.shape),source_highres_RGB_available=False,
        known_pipeline='1000x800 RGB after vertical flip -> pygame smoothscale96x96 -> cv2.resize84x84 INTER_LINEAR -> RGB2GRAY uint8 -> float32/255',
        detector_current_candidates=detections,cells=records,summary=dict(cells=len(records),baseline_conditional_eligible=int(conditional.sum()),sourceeligible_conditional=sum(v['conditional_sourceeligible']for v in records),whole_cell_certified=0),
        scope='Provenance and engineering eligibility are separate. No whole-source material inferred from gray, flatness or erosion. No Agent/core edits or world/model/native calls.',model_ticks=0,native=0,CPU_s=time.process_time()-cpu)
    Path(output).write_text(json.dumps(result,indent=2)+'\n');return {k:v for k,v in result.items()if k!='cells'}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--checkpoint');parser.add_argument('--output');parser.add_argument('--mixture-test',action='store_true');args=parser.parse_args()
    if args.mixture_test:
        cpu=time.process_time();result=mixture_counterexample();result.update(CPU_s=time.process_time()-cpu,model_ticks=0,native=0)
        if args.output:Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result))
    else:
        if not args.checkpoint or not args.output:parser.error('provide --checkpoint and --output')
        print(json.dumps(audit(args.checkpoint,args.output)))
