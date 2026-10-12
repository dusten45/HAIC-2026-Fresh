"""Frozen221 teacher on an actual student snapshot, never an environment actor.

Only the first control is returned as a current-state target. The retained
shadow plan has the original 12-action expiration, including when R is chosen.
"""
import time
import numpy as np
from retry import receding_horizon_oracle as rh
from retry.transition_ranking_probe import endpoint


def rank(snapshot,predictions,specs,oracle,track):
    scores={name:endpoint(q['rows'],12,snapshot['unique_tiles']) for name,q in predictions.items()}
    if oracle.get('contiguous_forward_rank'):rh.add_contiguous_scores(snapshot,predictions,scores)
    if oracle.get('forward_direction_rank'):rh.add_forward_scores(track,predictions,scores)
    if oracle.get('new_internal_gap_rank'):rh.add_new_gap_scores(snapshot,predictions,scores)
    invalid=[n for n,q in predictions.items() if not all(q['initialization'].values())]
    original,relaxed,eligible=rh.choose_with_fallback({n:s for n,s in scores.items() if n not in invalid},specs,
        oracle.get('relax_progress_fallback',False),oracle.get('contiguous_forward_rank',False),
        oracle.get('filter_predicted_contact',True),oracle.get('forward_direction_rank',False),
        oracle.get('new_internal_gap_rank',False))
    return (eligible[0] if eligible else None),scores,invalid


def query(snapshot,nominal,oracle,step,previous,track,actual_previous_steer):
    wall,cpu=time.perf_counter(),time.process_time()
    predictions,specs,retained,commands=rh.forecast_pool(snapshot,nominal,oracle,step,previous,track,actual_previous_steer)
    chosen,scores,invalid=rank(snapshot,predictions['candidates'],specs,oracle,track)
    if chosen=='R':
        assert retained['remaining_actions']>=3
        sequence=retained['actions']
    elif chosen is not None:
        sequence=commands[chosen]
        previous=dict(start_step=step,actions=sequence,origin_candidate=chosen)
    else:sequence=[nominal.copy()]
    label=np.asarray(sequence[0],np.float32).copy()
    return label,previous,dict(action=step,selected=chosen,invalid=invalid,scores=scores,
        model_queries=len(predictions['candidates']),model_physics_ticks=predictions['model_physics_ticks'],
        wall_s=time.perf_counter()-wall,CPU_s=time.process_time()-cpu,
        initialization_all_exact=all(all(q['initialization'].values()) for q in predictions['candidates'].values()),
        first_command_only=True,teacher_target=label.tolist())
