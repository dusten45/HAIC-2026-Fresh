"""Read-only checkpoint pose-set audit: official pixels and Agent memory only.

Full poses, source-cell lineage and masks are private outputs. Conditional
inverse-render/object and flow assumptions are kept separate from admissible
support. This module never invokes Agent.act, a dynamics tick, or a simulator.
"""
import argparse
from dataclasses import asdict
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

import cv2
import numpy as np

from retry.observed_pose_candidates import Association,PointBox,build_pose_candidates
from retry.observed_pose_support import Grid,common_support,prune_pose_boxes,split_pose_boxes,_down,_up
from retry.observed_source_cells import sample_support


def frame_id(frame):return hashlib.sha256(frame.tobytes()).hexdigest()


def load_agent(directory):
    sys.path.insert(0,str(directory/'package'))
    spec=importlib.util.spec_from_file_location('memory_pose_audit_agent',directory/'package/agent.py')
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module
    spec.loader.exec_module(module);return module


def object_sets(agent,image):
    """Retain every accepted observed ROI, every center cell via an outer AABB.

    These are conditional inverse-render sets. The current detector does not
    exhaustively cover hidden/cropped candidates and its raster error allowance
    is an engineering assumption, so actual localization/coverage stay unproved.
    """
    joint,_=agent.decode_joint_hud(image,None)
    detections,blocked=agent.detect_observed_obstacles(image);candidates=[]
    for index,(center,radius) in enumerate(detections):
        patch=agent.observed_object_road_patch(image,center,joint)
        if patch is None:continue
        roi=patch[2]['observed_roi_pixels'];x0,y0,x1,y1=roi
        v=np.rint(image[y0:y1+1,x0:x1+1]*255).astype(np.uint8)
        ring=np.ones(v.shape,bool);ring[2:-2,2:-2]=False
        envelope=agent.compatible_object_envelope(np.rint(image*255).astype(np.uint8),roi,
                    (float(v[ring].min()),float(v[ring].max())))
        if not envelope.get('accepted',False):continue
        cells=np.asarray(envelope['centers_world_pixel_origin'],float)
        cells[:,0]-=agent.IMAGE_ORIGIN_X/agent.OBJECT_SX
        cells[:,1]=agent.IMAGE_ORIGIN_Y/agent.OBJECT_SY-cells[:,1]
        radius=envelope['center_cell_half_diagonal_m']
        p=PointBox(_down(float(cells[:,0].min()-radius)),_up(float(cells[:,0].max()+radius)),
                   _down(float(cells[:,1].min()-radius)),_up(float(cells[:,1].max()+radius)))
        candidates.append(dict(label='observed_object_'+str(index),point_box=p,
            source_ROI=list(roi),center_cells=cells.tolist(),cell_enclosing_radius_m=radius,
            full_envelope=envelope))
    return candidates,blocked.astype(bool),agent.vehicle_projection_mask(joint).astype(bool)


def flow_pairs(agent,before,after):
    a=np.rint(before*255).astype(np.uint8);b=np.rint(after*255).astype(np.uint8)
    mask=np.zeros((84,84),np.uint8);mask[5:70,2:82]=255;mask[54:70,33:52]=0
    p=cv2.goodFeaturesToTrack(a,128,.01,3,mask=mask)
    if p is None:return np.empty((0,2)),np.empty((0,2))
    q,status,_=cv2.calcOpticalFlowPyrLK(a,b,p,None,winSize=(15,15),maxLevel=3)
    if q is None:return np.empty((0,2)),np.empty((0,2))
    back,reverse,_=cv2.calcOpticalFlowPyrLK(b,a,q,None,winSize=(15,15),maxLevel=3)
    if back is None:return np.empty((0,2)),np.empty((0,2))
    valid=status.ravel().astype(bool)&reverse.ravel().astype(bool)
    valid&=np.linalg.norm(back[:,0]-p[:,0],axis=1)<=.5
    points=[p[valid,0].astype(float),q[valid,0].astype(float)]
    for v in points:
        v[:,0]=(v[:,0]-agent.IMAGE_ORIGIN_X)/agent.OBJECT_SX
        v[:,1]=(agent.IMAGE_ORIGIN_Y-v[:,1])/agent.OBJECT_SY
    return points


def build(groups,angular_intervals):
    return build_pose_candidates(groups,angle_domain=(-4.,4.),angular_intervals=angular_intervals,
        association_coverage_proved=False,localization_proved=False,
        angle_coverage_proved=True,unmatched_possible=True)


def result_candidates(candidate):
    return dict(box_count=len(candidate.boxes),coverage_complete=candidate.coverage_complete,
        unknown_reasons=list(candidate.unknown_reasons),assignments_enumerated=candidate.assignments_enumerated,
        assignments_with_surviving_boxes=candidate.assignments_with_surviving_boxes,
        angular_intervals_per_assignment=candidate.angular_intervals_per_assignment,
        boxes=[asdict(box) for box in candidate.boxes])


def audit(checkpoint,output,angular_intervals=256,material_contradiction_test=False,refinement_rounds=0):
    start=time.process_time();wall=time.perf_counter();directory=Path(checkpoint).resolve();out=Path(output).resolve()
    repository=Path(__file__).resolve().parents[1]
    if out.is_relative_to(repository):raise ValueError('Private checkpoint output must be outside repository')
    out.mkdir(mode=0o700,parents=True,exist_ok=False)
    if not 0<=refinement_rounds<=3:raise ValueError('Refinement rounds must be0..3')
    if refinement_rounds and not material_contradiction_test:
        raise ValueError('Refinement requires explicit conditional material test')
    a=load_agent(directory)
    memory=json.loads((directory/'agent-before-private.json').read_text())['memory']
    observation=np.load(directory/'input-private.npy')
    frames=[np.asarray(v,np.float32) for v in memory['road_frames'][-8:]]
    current=observation[-1]
    current_objects,current_blocked,current_cover=object_sets(a,current)
    grass=a.coherent_grass_mask(current);grid=Grid(a.OBJECT_SX,a.OBJECT_SY,a.IMAGE_ORIGIN_X,a.IMAGE_ORIGIN_Y)
    yy,xx=np.indices(current.shape)
    conditional_grass=grass&~current_blocked&~current_cover&(yy>=5)&(yy<70)&(xx>=1)&(xx<=82)
    arrays=dict(current=current,current_grass=grass,current_objects=current_blocked)
    results=[];union=np.zeros((84,84),bool);actual_union=np.zeros((84,84),bool)
    for index,old in enumerate(frames):
        objects,blocked,cover=object_sets(a,old)
        baseline=a.visible_road_evidence(old).astype(bool)
        conditional=baseline&~blocked&~cover&~a.coherent_grass_mask(old)
        yy,xx=np.indices(old.shape);conditional&=(yy>=5)&(yy<70)&(xx>=1)&(xx<=82)
        source_hash=frame_id(old);lineage=[]
        for y,x in zip(*np.nonzero(baseline)):
            lineage.append(dict(frame_id=source_hash,pixel_xy=[int(x),int(y)],
                raw_float32=float(old[y,x]),quantized_gray_u8=int(round(float(old[y,x])*255)),
                source_sample_support=sample_support(int(x),int(y)),
                conditional_eligible=bool(conditional[y,x]),whole_cell_material='UNKNOWN',
                whole_cell_certificate=None))
        alternatives=[Association(p['point_box'],q['point_box'],p['label']+'->'+q['label'])
                      for p in objects for q in current_objects]
        candidate=build([alternatives],angular_intervals)
        # A material-conflict box is removed only when every pose in that box
        # maps one old asphalt point entirely into current grass. These masks
        # are CONDITIONAL materials, so this remains a sensitivity diagnostic.
        survivors,pruning=prune_pose_boxes(conditional,conditional_grass,candidate.boxes,
             grid=grid,material_premise=material_contradiction_test)
        refinement=[]
        for round_index in range(refinement_rounds):
            if not survivors:break
            children,split_info=split_pose_boxes(survivors,axes=('theta','tx','ty'),maximum_boxes=8192)
            survivors,prune_info=prune_pose_boxes(conditional,conditional_grass,children,
                grid=grid,material_premise=True)
            refinement.append(dict(round=round_index+1,split=split_info,pruning=prune_info))
        # Conditional sensitivity computation explicitly assumes, rather than
        # proves, completeness and whole-cell asphalt for the source mask.
        conditional_support=common_support(baseline,conditional,survivors,
             grass,current_blocked,grid=grid,coverage_complete=bool(alternatives),source_cells_certified=True)
        actual_support=common_support(conditional,np.zeros_like(conditional),candidate.boxes,
             grass,current_blocked,grid=grid,coverage_complete=candidate.coverage_complete,source_cells_certified=False)
        union|=conditional_support;actual_union|=actual_support
        arrays['source_'+str(index)]=old;arrays['conditional_source_'+str(index)]=conditional
        arrays['conditional_support_'+str(index)]=conditional_support
        results.append(dict(source_frame_id=source_hash,age=len(frames)-index,
            baseline_source_cells=int(baseline.sum()),conditional_source_cells=int(conditional.sum()),
            certified_source_cells=0,source_lineage=lineage,
            source_object_candidates=[dict(v,point_box=asdict(v['point_box'])) for v in objects],
            pose_candidates=result_candidates(candidate),
            conditional_material_pruning=pruning,
            conditional_refinement_history=refinement,
            conditional_surviving_pose_boxes=[asdict(box) for box in survivors],
            conditional_common_support_cells=int(conditional_support.sum()),
            conditional_common_under_current_vehicle=int(np.sum(conditional_support&current_cover)),
            admissible_support_cells=int(actual_support.sum())))
    oldp,newp=flow_pairs(a,frames[-1],current)
    def exact(p):return PointBox(float(p[0]),float(p[0]),float(p[1]),float(p[1]))
    def residual(p):return PointBox(_down(float(p[0]-.25)),_up(float(p[0]+.25)),_down(float(p[1]-.25)),_up(float(p[1]+.25)))
    # .25m is the pre-existing RANSAC tolerance, not a newly claimed bound.
    fixed=build([[Association(exact(p),residual(q),'FB_'+str(i))] for i,(p,q) in enumerate(zip(oldp,newp))],angular_intervals)
    all_aliases=build([[Association(exact(p),residual(q),str(i)+'->'+str(j))
        for i,p in enumerate(oldp) for j,q in enumerate(newp)]],angular_intervals)
    arrays['conditional_union']=union;arrays['admissible_union']=actual_union
    np.savez_compressed(out/'source-and-support-private.npz',**arrays)
    result=dict(status='ACTUAL_CHECKPOINT_POSE_SET_GATE_NOT_PASSED',
        agent_sha256=hashlib.sha256((directory/'package/agent.py').read_bytes()).hexdigest(),
        current_frame_id=frame_id(current),sources=results,
        current_object_candidates=[dict(v,point_box=asdict(v['point_box'])) for v in current_objects],
        flow=dict(FB_pair_count=len(oldp),fixed_all_pairs_conditional=result_candidates(fixed),
                  every_single_pair_assignment_conditional=result_candidates(all_aliases),
                  localization_scope='Existing .25m residual tolerance is a conditional test, not an absolute correspondence-error certificate.'),
        conditional_union_cells=int(union.sum()),conditional_union_under_vehicle=int(np.sum(union&current_cover)),
        admissible_union_cells=int(actual_union.sum()),
        scope='All source center-cell choices are enclosed; all observed ROI associations and full angular circle are retained. Missed/hidden identity and uncertified localization/source material remain explicit unknown branches. No best-fit pose or own-prediction tolerance is used.',
        limitations='Conditional common-support masks assume object identity/localization and whole source-cell road premises. They cannot be fed to Agent or promoted as certificates.',
        conditional_material_pruning_enabled=material_contradiction_test,
        refinement_rounds=refinement_rounds,
        model_ticks=0,native_actions=0,CPU_s=time.process_time()-start,wall_s=time.perf_counter()-wall)
    (out/'pose-set-private.json').write_text(json.dumps(result,indent=2)+'\n')
    summary={k:v for k,v in result.items() if k not in ('sources','current_object_candidates','flow')}
    summary['sources']=[{k:v for k,v in item.items() if k not in ('source_lineage','source_object_candidates','pose_candidates','conditional_material_pruning','conditional_refinement_history','conditional_surviving_pose_boxes')}|{'pose_box_count':item['pose_candidates']['box_count'],'surviving_pose_boxes':len(item['conditional_surviving_pose_boxes'])} for item in results]
    summary['flow']=dict(FB_pair_count=len(oldp),fixed_all_pairs_box_count=len(fixed.boxes),all_single_assignment_box_count=len(all_aliases.boxes))
    return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--checkpoint',required=True)
    parser.add_argument('--output-directory',required=True);parser.add_argument('--angular-intervals',type=int,default=256)
    parser.add_argument('--material-contradiction-test',action='store_true')
    parser.add_argument('--refinement-rounds',type=int,default=0)
    args=parser.parse_args()
    print(json.dumps(audit(args.checkpoint,args.output_directory,args.angular_intervals,args.material_contradiction_test,args.refinement_rounds)))
