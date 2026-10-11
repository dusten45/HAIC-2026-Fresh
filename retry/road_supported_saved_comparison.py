"""One saved-only support-cue comparison; privileged evidence never enters cue."""
import argparse,datetime as dt,itertools,json,sys,time
from pathlib import Path
import cv2
import numpy as np
from retry import fresh_dev_distribution as cohort
from retry.qualify_pixel_package import PipeWorker
from retry.saved_occlusion_ownership import ownership
from retry.saved_road_input_reconstruction import saved_geometry
from retry.road_supported_recovery import supported_road
from retry.road_band_saved_comparison import array_sha,gt_allowed,reachable,unpack,target_error,reference_pairs


def main(path):
    p=json.loads(path.read_text());D=path.parent;started=time.perf_counter()
    def check():assert dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(p['deadline_utc'])
    check();assert cohort.sha(path)==path.with_suffix('.sha256').read_text().split()[0]
    for n,h in p['source_sha256'].items():assert cohort.sha(Path(n))==h,n
    refs=[json.loads(l) for l in Path(p['reference_trace']).read_text().splitlines()]
    prior=[json.loads(l) for l in Path(p['prior_comparison_trace']).read_text().splitlines()]
    source=np.load(p['pixels_actions_path'],allow_pickle=False);frames=source['frames'].astype(np.float32)/np.float32(255)
    scene=json.loads(Path(p['scene_path']).read_text());layers=saved_geometry(scene['track'])[0]
    clone=D/p.get('worker_clone_directory','saved-worker');clone.mkdir(mode=0o700);clean,package,worker,runtime=cohort.clone(p,clone)
    helper=clean/'boundary.py';helper.write_bytes(Path(p['boundary_path']).read_bytes());helper.chmod(0o444)
    w=PipeWorker([sys.executable,'-I','-B',str(worker),str(package)],clean,runtime)
    rows=[];receipts=[];last={};first={};roi=np.zeros((84,84),bool);roi[24:57,3:81]=True
    out=D/'paired-arrays';out.mkdir(mode=0o700,exist_ok=True);ownership_wall=0.
    assert not any(out.iterdir()),'Do not overwrite partially retained evidence'
    try:
        w.call('reset',np.concatenate([np.repeat(frames[:1],4,axis=0),np.zeros((1,84,84),np.float32)]))
        for old,previous in zip(refs,prior):
            check();step=old['step'];obs=frames[[max(0,step-4+j) for j in range(4)]]
            # Candidate input is computed before privileged masks are read.
            C=supported_road(obs[-1]);P47=((obs[-1]>.32)&(obs[-1]<.47));P52=((obs[-1]>.32)&(obs[-1]<.52))
            with np.load(Path(p['qualified_mask_directory'])/f'mask-{step:04d}.npz',allow_pickle=False) as saved:A=saved['full_GT'];B=saved['visible_GT']
            assert array_sha(A)==old['mask_receipt']['full_gt_mask_sha256'] and array_sha(B)==old['mask_receipt']['mask_sha256']
            t=time.perf_counter();regions,receipt=ownership(scene,old['truth_before'],old['mask_receipt'],layers);ownership_wall+=time.perf_counter()-t
            assert np.array_equal(B,A*(1-regions['occlusion']))
            Oany=regions['occlusion_coverage']>0;HUDany=regions['HUD_coverage']>0
            boundary=cv2.dilate(A,np.ones((3,3),np.uint8))!=cv2.erode(A,np.ones((3,3),np.uint8))
            # Keep the binary nonroad reference and the stricter unambiguous
            # subset distinct. Partial material coverage is uncertain.
            categories={'visible_road':B.astype(bool),'occluded_road':A.astype(bool)&Oany,
              'HUD':HUDany,'occlusion_or_paint':Oany&~HUDany,'road_boundary':boundary,
              'reference_nonroad_unoccluded':~A.astype(bool)&~regions['occlusion'].astype(bool),
              'known_nonroad_clear':~A.astype(bool)&~Oany&~boundary&~HUDany,
              'uncertain_boundary':boundary&~HUDany,'uncertain_material':Oany&~HUDany}
            r,_=w.call('capture',np.concatenate([obs,C[None].astype(np.float32)]))
            assert np.asarray(r['action'],np.float32).tobytes()==source['actions'][step-1].tobytes()
            assert r['actual_pre_memory_sha256']==old['memory_receipt']['actual_pre_memory_sha256']
            assert r['actual_post_memory_sha256']==old['memory_receipt']['actual_post_memory_sha256'] and r['actual_post_unchanged_by_shadow']
            base=r['pixel'];cand=r['substitution_shadow'];a0=unpack(base);a1=unpack(cand)
            assert np.array_equal(a0['raw_road'],P47) and np.array_equal(a1['raw_road'],C)
            ga,gl=gt_allowed(B,base['hazards']);reach0=reachable(base,a0);reach1=reachable(cand,a1)
            with np.load(Path(p['prior_array_directory'])/f'pair-{step:04d}.npz',allow_pickle=False) as q:
                for k in a0:assert np.array_equal(a0[k],q['base_'+k])
                prior_telem=previous['candidate_same_state_shadow'];pl=q['candidate_labels']
                reach52=np.zeros((84,84),bool) if prior_telem['start'] is None else pl==pl[tuple(prior_telem['start'])]
            added=P52&~P47;admitted=C.astype(bool)&~P47;extra=reach1&~reach0;extra52=reach52&~reach0
            counts={}
            for arm,raw in [('base',P47),('upper52',P52),('supported',C.astype(bool))]:
                counts[arm+'_missing_visible_ROI']=int(np.count_nonzero(~raw&B.astype(bool)&roi))
                counts[arm+'_known_nonroad_ROI']=int(np.count_nonzero(raw&categories['known_nonroad_clear']&roi))
                counts[arm+'_reference_nonroad_ROI']=int(np.count_nonzero(raw&categories['reference_nonroad_unoccluded']&roi))
            for name,mask in categories.items():
                counts['upper52_added_'+name]=int(np.count_nonzero(added&mask&roi))
                counts['supported_added_'+name]=int(np.count_nonzero(admitted&mask&roi))
                counts['upper52_new_reachable_'+name]=int(np.count_nonzero(extra52&mask))
                counts['supported_new_reachable_'+name]=int(np.count_nonzero(extra&mask))
            for name in ('car','obstacles','curb'):
                region=regions[name+'_coverage']>0
                counts['upper52_added_'+name]=int(np.count_nonzero(added&region&roi))
                counts['supported_added_'+name]=int(np.count_nonzero(admitted&region&roi))
            gt=old['visible_GT_shadow'];e0=target_error(base['target'],gt['target']);e1=target_error(cand['target'],gt['target'])
            diffs={'path':base['path']!=cand['path'],'target':base['target']!=cand['target'],'action':base['action']!=cand['action'],
              'effective_target_speed':(base['cap'] or {}).get('effective_target')!=(cand['cap'] or {}).get('effective_target'),
              'post_memory':bool(r['post_memory_different_fields'])}
            for k,v in diffs.items():
                if v and k not in first:first[k]={'step':step,'pre_time_s':old['before_time']}
            pair_gain=reference_pairs(reach1,gl)-reference_pairs(reach0,gl)
            rec={'step':step,'pre_time_s':old['before_time'],'damage_before':old['truth_before']['damage'],'counts':counts,
              'base_target_error':e0,'supported_target_error':e1,'upper52_target_error':previous['candidate_target_error'],
              'base':base,'supported_same_state_shadow':cand,'differences':diffs,'added_reference_component_pairs':[list(x) for x in sorted(pair_gain)],
              'actual_pre_memory_sha256':r['actual_pre_memory_sha256'],'actual_post_memory_sha256':r['actual_post_memory_sha256'],
              'post_memory_different_fields':r['post_memory_different_fields'],'post_controller_different_fields':r['post_controller_different_fields']}
            rows.append(rec);receipts.append({'step':step,**receipt})
            saved=out/f'pair-{step:04d}.npz'
            np.savez_compressed(saved,**regions,**{'category_'+k:v.astype(np.uint8) for k,v in categories.items()},
              **{'base_'+k:v for k,v in a0.items()},**{'supported_'+k:v for k,v in a1.items()})
            saved.chmod(0o600);last=r
    finally:reap=w.close()
    (D/'paired-trace.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows));(D/'paired-trace.jsonl').chmod(0o600)
    totals={k:sum(r['counts'][k] for r in rows) for k in rows[0]['counts']}
    common=[r for r in rows if r['base_target_error'] is not None and r['supported_target_error'] is not None]
    errors0=sum(r['base_target_error'] for r in common);errors1=sum(r['supported_target_error'] for r in common)
    checks={'same_state_exact_all218':len(rows)==218,'noop_source_pass':p['reused_noop_status']=='PASS',
      'visible_missing_reduced':totals['supported_missing_visible_ROI']<totals['base_missing_visible_ROI'],
      'known_nonroad_no_increase':totals['supported_known_nonroad_ROI']<=totals['base_known_nonroad_ROI'],
      'reference_nonroad_no_increase':totals['supported_reference_nonroad_ROI']<=totals['base_reference_nonroad_ROI'],
      'no_new_known_nonroad_reachable':totals['supported_new_reachable_known_nonroad_clear']==0,
      'no_new_material_uncertain_reachable':totals['supported_new_reachable_uncertain_material']==0,
      'no_new_reference_nonroad_reachable':totals['supported_new_reachable_reference_nonroad_unoccluded']==0,
      'no_new_reference_component_pairs':all(not r['added_reference_component_pairs'] for r in rows),
      'target_error_sum_no_increase':errors1<=errors0+1e-12,'no_material_target_regression':all(r['supported_target_error']<=r['base_target_error']+1e-12 for r in common),
      'worker_reaped':reap['process_reaped']}
    report={'status':'SAVED_ONLY_CANDIDATE_REQUIRES_FUTURE_VALIDATION' if all(checks.values()) else 'CLOSE_THIS_SUPPORT_CUE_FAMILY',
      'checks':checks,'failed_checks':[k for k,v in checks.items() if not v],'totals':totals,'frames':len(rows),'first_differences':first,
      'target_error_common_defined_rows':len(common),'target_error_sums':[errors0,errors1],'target_error_material_worse_rows':sum(r['supported_target_error']>r['base_target_error']+1e-12 for r in common),
      'target_missing_base_supported_GT':[sum(r['base']['target'] is None for r in rows),sum(r['supported_same_state_shadow']['target'] is None for r in rows),sum(refs[i]['visible_GT_shadow']['target'] is None for i in range(len(rows)))],
      'ownership_receipts':receipts,'ownership_wall_s':ownership_wall,'wall_s':time.perf_counter()-started,'actor_CPU_s':last['actor_cumulative_CPU_s'],
      'worker_reaping':reap,'actual_policy_calls':len(rows),'shadow_policy_calls':len(rows),'reused_noop_actions':306,
      'new_env_resets':0,'new_wrapper_actions':0,'Stage81_failure_unchanged':True,'GT_in_candidate_input':False,
      'region_tags_overlap':True,'half_coverage_boundary_is_not_physical_safety_truth':True,'shadow_is_not_closed_loop':True,'plan_sha256':cohort.sha(path)}
    cohort.write(D/'saved-comparison.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('ownership_receipts','worker_reaping','totals')},ensure_ascii=False),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);main(a.parse_args().plan.resolve())
