"""Prospective saved-trajectory road-band test; privileged masks stay evaluator-side."""
import argparse, base64, datetime as dt, hashlib, itertools, json, sys, time
from pathlib import Path
import cv2
import numpy as np
from retry import fresh_dev_distribution as cohort
from retry.qualify_pixel_package import PipeWorker
from retry.saved_road_input_reconstruction import reconstruction
from retry.road_input_shadow_capture import decoded


def array_sha(a):return hashlib.sha256(a.tobytes()).hexdigest()
def check(p):
    assert dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(p['deadline_utc'])
def gt_allowed(B,hazards):
    road=B.copy();road[61:]=0
    road=cv2.morphologyEx(road,cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
    distance=cv2.distanceTransform(road,cv2.DIST_L2,5);allowed=distance>=1.5
    allowed[:24]=False;allowed[57:]=False;allowed[:,:3]=False;allowed[:,81:]=False
    yy,xx=np.indices(B.shape)
    for x,y,radius,*_ in hazards:
        allowed &= ((xx-42)/1.3608-x)**2+((63-yy)/1.701-y)**2>(2.6+radius)**2
    return allowed,cv2.connectedComponents(allowed.astype(np.uint8),connectivity=4)[1]
def reachable(arm,arrays):
    if arm['start'] is None:return np.zeros((84,84),bool)
    labels=arrays['labels'];return labels==labels[tuple(arm['start'])]
def reference_pairs(reach,labels):
    ids=sorted(set(map(int,labels[reach]))-{0})
    return set(itertools.combinations(ids,2))
def target_error(target,reference):
    if target is None or reference is None:return None
    return float(np.linalg.norm(np.array(target)-reference))
def unpack(arm):return {k:decoded(v) for k,v in arm.pop('arrays').items()}


def main(path):
    p=json.loads(path.read_text());D=path.parent;check(p)
    assert cohort.sha(path)==path.with_suffix('.sha256').read_text().split()[0]
    for name,h in p['source_sha256'].items():assert cohort.sha(Path(name))==h,name
    source=np.load(p['pixels_actions_path'],allow_pickle=False);frames=source['frames'].astype(np.float32)/np.float32(255)
    old=[json.loads(l) for l in Path(p['reference_trace']).read_text().splitlines()]
    scene=json.loads(Path(p['scene_path']).read_text());masks={};mask_receipts=[];reconstruction_start=time.perf_counter()
    maskdir=D/'qualified-masks';maskdir.mkdir(mode=0o700,exist_ok=True)
    for row in old:
        check(p);step=row['step'];maskpath=maskdir/f'mask-{step:04d}.npz'
        if maskpath.exists():
            with np.load(maskpath,allow_pickle=False) as saved:A=saved['full_GT'];B=saved['visible_GT']
            assert array_sha(A)==row['mask_receipt']['full_gt_mask_sha256']
            assert array_sha(B)==row['mask_receipt']['mask_sha256']
            receipt={'recorded_full_GT_sha_exact':True,'recorded_visible_GT_sha_exact':True,'reused_qualified_saved_mask':True,'new_env_or_physics_actions':0}
        else:A,B,receipt=reconstruction(scene,row['truth_before'],row['mask_receipt'])
        masks[step]=B
        maskpath=maskdir/f'mask-{step:04d}.npz';np.savez_compressed(maskpath,full_GT=A,visible_GT=B);maskpath.chmod(0o600)
        mask_receipts.append({'step':step,'sha256':cohort.sha(maskpath),**receipt})
    reconstruction_wall=time.perf_counter()-reconstruction_start
    assert len(masks)==p['saved_steps']
    cohort.write(D/'mask-reconstruction.json',{'qualified_count':len(masks),'receipts':mask_receipts,'wall_s':reconstruction_wall,'new_env_or_physics_calls':0})
    clone=D/p.get('worker_clone_directory','saved-worker');clone.mkdir(mode=0o700);clean,package,worker,runtime=cohort.clone(p,clone)
    helper=clean/'boundary.py';helper.write_bytes(Path(p['boundary_path']).read_bytes());helper.chmod(0o444)
    w=PipeWorker([sys.executable,'-I','-B',str(worker),str(package)],clean,runtime)
    zero=np.zeros((1,84,84),np.float32);initial=np.repeat(frames[:1],4,axis=0);started=time.perf_counter();noop=0;result_rows=[];last={};first={}
    try:
        if p.get('reuse_noop_gate'):
            prior=json.loads(Path(p['reuse_noop_gate']).read_text())
            assert cohort.sha(Path(p['reuse_noop_gate']))==p['reuse_noop_gate_sha256']
            assert prior['status']=='PASS' and prior['matched_actions']==len(source['actions'])
            noop=prior['matched_actions'];noop_calls_this_attempt=0;noop_reaping=p['reused_noop_worker_reaping']
        else:
            w.call('reset',np.concatenate([initial,zero]))
            for i,action in enumerate(source['actions']):
                check(p);obs=frames[[max(0,i-3+j) for j in range(4)]]
                r,_=w.call('noop',np.concatenate([obs,zero]));assert np.asarray(r['action'],np.float32).tobytes()==action.tobytes();noop+=1
            noop_calls_this_attempt=noop;noop_reaping=w.close()
            cohort.write(D/'noop-gate.json',{'status':'PASS','matched_actions':noop,'noop_arrays_action_postmemory_exact':True,'new_env_calls':0,'worker_reaping':noop_reaping})
            # Agent.reset need not clear every diagnostic field. A fresh process
            # restores constructor memory before the independent comparison.
            w=PipeWorker([sys.executable,'-I','-B',str(worker),str(package)],clean,runtime)
        w.call('reset',np.concatenate([initial,zero]))
        roi=np.zeros((84,84),bool);roi[24:57,3:81]=True;cropped=np.zeros((84,84),bool);cropped[:61]=True
        out=D/'paired-arrays';out.mkdir(mode=0o700,exist_ok=True)
        assert not any(out.iterdir()),'Do not overwrite a partially retained comparison'
        for row in old:
            check(p);step=row['step'];obs=frames[[max(0,step-4+j) for j in range(4)]];B=masks[step]
            candidate=((obs[-1]>.32)&(obs[-1]<p['candidate_upper'])).astype(np.uint8)
            r,_=w.call('capture',np.concatenate([obs,candidate[None].astype(np.float32)]))
            assert np.asarray(r['action'],np.float32).tobytes()==source['actions'][step-1].tobytes()
            assert array_sha(obs)==row['observation_sha256_before']
            assert r['actual_pre_memory_sha256']==row['memory_receipt']['actual_pre_memory_sha256']
            assert r['actual_post_memory_sha256']==row['memory_receipt']['actual_post_memory_sha256']
            assert r['actual_pre_memory_sha256']==r['shadow_pre_memory_sha256'] and r['actual_post_unchanged_by_shadow']
            base=r['pixel'];cand=r['substitution_shadow'];a0=unpack(base);a1=unpack(cand)
            assert np.array_equal(a1['raw_road'],candidate)
            ga,gl=gt_allowed(B,base['hazards']);reach0=reachable(base,a0);reach1=reachable(cand,a1)
            pairs0=reference_pairs(reach0,gl);pairs1=reference_pairs(reach1,gl)
            captured=Path(p['saved_capture_directory'])/f'paired-step-{step:04d}.npz'
            if captured.exists():
                with np.load(captured,allow_pickle=False) as c:
                    assert np.array_equal(ga,c['visible_GT_shadow_allowed'])
                    for k in a0:assert np.array_equal(a0[k],c['pixel_'+k]),(step,k)
            counts={}
            for label,area in [('full',np.ones((84,84),bool)),('cropped',cropped),('ROI',roi)]:
                for arm,raw in [('base',a0['raw_road'].astype(bool)),('candidate',candidate.astype(bool))]:
                    counts[label+'_'+arm+'_FP']=int(np.count_nonzero(raw&~B.astype(bool)&area))
                    counts[label+'_'+arm+'_FN']=int(np.count_nonzero(~raw&B.astype(bool)&area))
            added_reach=reach1&~reach0
            gt=row['visible_GT_shadow'];e0=target_error(base['target'],gt['target']);e1=target_error(cand['target'],gt['target'])
            differences={
                'path':base['path']!=cand['path'],'target':base['target']!=cand['target'],
                'inherited_target_speed':(base['cap'] or {}).get('inherited_target')!=(cand['cap'] or {}).get('inherited_target'),
                'effective_target_speed':(base['cap'] or {}).get('effective_target')!=(cand['cap'] or {}).get('effective_target'),
                'action':base['action']!=cand['action'],'post_memory':bool(r['post_memory_different_fields']),
                'controller_previous_steer':'previous_steer' in r['post_controller_different_fields']}
            for k,changed in differences.items():
                if changed and k not in first:first[k]={'step':step,'pre_time_s':row['before_time'],'damage_before':row['truth_before']['damage']}
            rec={'step':step,'pre_time_s':row['before_time'],'damage_before':row['truth_before']['damage'],**counts,
                 'added_reference_component_pairs':[list(x) for x in sorted(pairs1-pairs0)],
                 'added_false_raw_reachable_cells':int(np.count_nonzero(added_reach&~B.astype(bool))),
                 'added_reference_disallowed_reachable_cells':int(np.count_nonzero(added_reach&~ga)),
                 'base_target_error':e0,'candidate_target_error':e1,'base':base,'candidate_same_state_shadow':cand,
                 'differences':differences,'pre_memory_sha256':r['actual_pre_memory_sha256'],
                 'base_post_memory_sha256':r['actual_post_memory_sha256'],'candidate_post_memory_sha256':r['shadow_post_memory_sha256'],
                 'post_memory_different_fields':r['post_memory_different_fields'],'post_controller_different_fields':r['post_controller_different_fields'],
                 'GT_not_environment_action':True}
            result_rows.append(rec)
            save=out/f'pair-{step:04d}.npz';np.savez_compressed(save,**{'base_'+k:v for k,v in a0.items()},**{'candidate_'+k:v for k,v in a1.items()},GT_allowed=ga,GT_labels=gl);save.chmod(0o600)
            last=r
    finally:reap=w.close()
    (D/'paired-trace.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in result_rows));(D/'paired-trace.jsonl').chmod(0o600)
    totals={k:sum(r[k] for r in result_rows) for k in result_rows[0] if any(k.startswith(a+'_') for a in ('full','cropped','ROI'))}
    checks={
      'all_saved_steps_exact':len(result_rows)==p['saved_steps'],
      'no_op_exact':noop==len(source['actions']),
      'ROI_missing_reduced':totals['ROI_candidate_FN']<totals['ROI_base_FN'],
      'ROI_errors_reduced':totals['ROI_candidate_FP']+totals['ROI_candidate_FN']<totals['ROI_base_FP']+totals['ROI_base_FN'],
      'ROI_FP_never_increased':all(r['ROI_candidate_FP']<=r['ROI_base_FP'] for r in result_rows),
      'cropped_FP_not_increased':totals['cropped_candidate_FP']<=totals['cropped_base_FP'],
      'no_added_reference_component_pairs':all(not r['added_reference_component_pairs'] for r in result_rows),
      'no_added_reference_false_reachable_cells':all(r['added_false_raw_reachable_cells']==0 and r['added_reference_disallowed_reachable_cells']==0 for r in result_rows),
      'precontact_control_difference':any(r['differences']['action'] for r in result_rows if r['step']<p['first_original_damage_step']),
      'worker_reaped':reap['process_reaped']}
    report={'status':'PASS_ALLOW_ONE_NATIVE' if all(checks.values()) else 'FALSIFIED_NO_NATIVE','checks':checks,'failed_checks':[k for k,v in checks.items() if not v],
            'totals':totals,'first_differences':first,'frames':len(result_rows),'no_op_matched':noop,
            'new_wrapper_actions':0,'new_env_resets':0,'policy_actual_calls':noop_calls_this_attempt+len(result_rows),'policy_shadow_calls':noop_calls_this_attempt+len(result_rows),
            'reused_noop_actions':noop-noop_calls_this_attempt,'noop_worker_reaping':noop_reaping,
            'wall_s':time.perf_counter()-started,'mask_reconstruction_wall_s':reconstruction_wall,'actor_CPU_s':last['actor_cumulative_CPU_s'],
            'worker_reaping':reap,'worker_ready':w.ready,'plan_sha256':cohort.sha(path),
            'target_error_common_defined_rows':sum(r['base_target_error'] is not None and r['candidate_target_error'] is not None for r in result_rows),
            'base_target_missing_rows':sum(r['base']['target'] is None for r in result_rows),
            'candidate_target_missing_rows':sum(r['candidate_same_state_shadow']['target'] is None for r in result_rows),
            'GT_target_missing_rows':sum(old[i]['visible_GT_shadow']['target'] is None for i in range(len(result_rows))),
            'target_error_sum_base':sum(r['base_target_error'] for r in result_rows if r['base_target_error'] is not None and r['candidate_target_error'] is not None),
            'target_error_sum_candidate':sum(r['candidate_target_error'] for r in result_rows if r['base_target_error'] is not None and r['candidate_target_error'] is not None),
            'target_error_not_a_new_performance_gate':True,'same_state_shadow_is_not_candidate_closed_loop':True,
            'reference_false_and_connectivity_are_representation_proxies_not_physical_safety_truth':True}
    cohort.write(D/'saved-comparison.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('worker_ready','worker_reaping')},ensure_ascii=False),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);main(a.parse_args().plan.resolve())
