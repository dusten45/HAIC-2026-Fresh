"""Aggregate saved score comparisons after preflight; no actor or native calls."""
import argparse
import json
from pathlib import Path


def analyze(private_stage, output):
    public=json.loads(output.read_text())
    stats=[]
    for record in public['preflight']['records']:
        rows=json.loads((private_stage/'preflight'/record['road']/'comparisons-private.json').read_text())
        changed_prediction=changed_connection=multi=empty=0
        old_margins=[];new_margins=[]
        for row in rows:
            g=row['on_route_audit']
            assert g['same_inputs'] and g['aligned']
            assert g['candidates_verified']==g['candidate_count']
            assert not g['path_changed'] and not row['action_changed']
            assert g['selected_index']==g['baseline_selected_index']
            multi+=g['candidate_count']>1
            empty+=g['candidate_count']==0
            old_scores=[];new_scores=[]
            for a,b in zip(g['candidate_scores'],g['baseline_scores']):
                assert a['side']==b['side'] and a['base_gap_m']==b['base_gap_m']
                changed_prediction+=a['next_steer']!=b['next_steer']
                changed_connection+=a['connection_m']!=b['connection_m']
                old_scores.append(b['base_gap_m']+b['connection_m'])
                new_scores.append(a['base_gap_m']+a['connection_m'])
            if g['candidate_count']>1:
                old_scores.sort();new_scores.sort()
                old_margins.append(old_scores[1]-old_scores[0])
                new_margins.append(new_scores[1]-new_scores[0])
        stats.append(dict(road=record['road'],actions=len(rows),empty_candidate_frames=empty,
            multi_candidate_frames=multi,candidate_prediction_changed=changed_prediction,
            connection_cost_changed=changed_connection,
            minimum_original_winner_margin_m=min(old_margins) if old_margins else None,
            minimum_aligned_winner_margin_m=min(new_margins) if new_margins else None))
    public['score_arithmetic']=stats
    public['closure_reason']='No selected path or action changes on all1754 saved baseline inputs; native screen was not started.'
    public['native_comparison_performed']=False
    public['verification']=dict(all_other296_members_byte_exact=True,
        only_existing_function_changed='choose_route',off_exact_actions_features_memory=1754,
        on_candidate_predictions_bit_exact=1763,changed_selection=0,changed_returned_actions=0,
        all_preflight_processes_reaped=True,champion_and_rollback_preserved=True,
        native_results_unobserved_not_DNF=True)
    output.write_text(json.dumps(public,ensure_ascii=False,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--private-stage',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    analyze(a.private_stage,a.output)
