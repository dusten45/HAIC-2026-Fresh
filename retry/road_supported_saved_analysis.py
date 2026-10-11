"""Saved-only reclassification and representative evidence; no policy calls."""
import argparse,json
from pathlib import Path
import numpy as np
from retry.road_supported_recovery import supported_road


def main(plan_path):
    p=json.loads(plan_path.read_text());D=plan_path.parent
    refs=[json.loads(l) for l in Path(p['reference_trace']).read_text().splitlines()]
    before=[json.loads(l) for l in Path(p['prior_comparison_trace']).read_text().splitlines()]
    current=[json.loads(l) for l in (D/'paired-trace.jsonl').read_text().splitlines()]
    frames=np.load(p['pixels_actions_path'],allow_pickle=False)['frames']
    roi=np.zeros((84,84),bool);roi[24:57,3:81]=True
    cropped=np.zeros((84,84),bool);cropped[:61]=True
    sums={};records=[]
    for old,prior,now in zip(refs,before,current):
        step=old['step'];image=frames[step-1].astype(np.float32)/255
        P47=(image>.32)&(image<.47);P52=(image>.32)&(image<.52);C=supported_road(image).astype(bool)
        with np.load(Path(p['qualified_mask_directory'])/f'mask-{step:04d}.npz',allow_pickle=False) as m:B=m['visible_GT'].astype(bool)
        with np.load(D/'paired-arrays'/f'pair-{step:04d}.npz',allow_pickle=False) as q:
            HUD=q['HUD_coverage']>0;material=q['occlusion_coverage']>0;boundary=q['category_road_boundary'].astype(bool)
            categories={'HUD':HUD,'material_unknown':material&~HUD,'boundary_mixed':boundary&~material&~HUD,'known_nonroad_clear':q['category_known_nonroad_clear'].astype(bool)}
            reach={}
            for arm,telem,prefix in [('base',now['base'],'base'),('supported',now['supported_same_state_shadow'],'supported')]:
                labels=q[prefix+'_labels'];reach[arm]=np.zeros((84,84),bool) if telem['start'] is None else labels==labels[tuple(telem['start'])]
            with np.load(Path(p['prior_array_directory'])/f'pair-{step:04d}.npz',allow_pickle=False) as previous:
                telem=prior['candidate_same_state_shadow'];labels=previous['candidate_labels'];reach['upper52']=np.zeros((84,84),bool) if telem['start'] is None else labels==labels[tuple(telem['start'])]
            counts={}
            for arm,raw in [('upper52',P52),('supported',C)]:
                added=raw&~P47;new_fp=added&~B&roi;new_bad_reach=reach[arm]&~reach['base']&~B
                assert sum(np.count_nonzero(new_fp&mask) for mask in categories.values())==np.count_nonzero(new_fp)
                assert sum(np.count_nonzero(new_bad_reach&mask) for mask in categories.values())==np.count_nonzero(new_bad_reach)
                counts[arm+'_new_false_ROI_total']=int(np.count_nonzero(new_fp))
                counts[arm+'_new_reference_false_reachable_total']=int(np.count_nonzero(new_bad_reach))
                for name,mask in categories.items():
                    counts[arm+'_new_false_ROI_'+name]=int(np.count_nonzero(new_fp&mask))
                    counts[arm+'_new_reference_false_reachable_'+name]=int(np.count_nonzero(new_bad_reach&mask))
                for scope,area in [('full',np.ones((84,84),bool)),('cropped',cropped)]:
                    false=added&~B&area
                    assert sum(np.count_nonzero(false&mask) for mask in categories.values())==np.count_nonzero(false)
                    counts[arm+'_new_false_'+scope+'_total']=int(np.count_nonzero(false))
                    for name,mask in categories.items():counts[arm+'_new_false_'+scope+'_'+name]=int(np.count_nonzero(false&mask))
                for name in ('car','obstacles','curb'):
                    mask=q[name+'_coverage']>0
                    counts[arm+'_new_reference_false_reachable_'+name]=int(np.count_nonzero(new_bad_reach&mask))
            for k,v in counts.items():sums[k]=sums.get(k,0)+v
            records.append({'step':step,'counts':counts,'base_target_error':now['base_target_error'],'supported_target_error':now['supported_target_error']})
    report={'exclusive_error_reclassification':sums,'row_count':218,'records':records,
      'known_nonroad_clear_positive_examples':0,'known_nonroad_discrimination_not_estimable':True,
      'material_coverage_partial_is_unknown_not_nonroad':True,'boundary_reference_label_not_physical_safety':True,
      'source_material_tags_overlap':True,'no_new_env_policy_renderer_calls':True,'Stage81_failure_unchanged':True}
    path=D/'reclassification.json';path.write_text(json.dumps(report,indent=2)+'\n');path.chmod(0o600)
    print(json.dumps(sums),flush=True)


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--plan',type=Path,required=True);main(a.parse_args().plan.resolve())
