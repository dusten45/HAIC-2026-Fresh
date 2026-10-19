"""Read-only progress, active-condition and dual report; no source calls."""
import json,time
from pathlib import Path
from retry.clip561_core import atomic_write
from retry.path569_design import sha

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response572-private');rd=lambda p:json.loads(p.read_text())

def safety(rows):
    rr=[r for r in rows if 'root_without_roads' in r];return dict(min_footprint=min(r['margin'] for r in rr),footprint_slack=min(r['margin'] for r in rr)-.5,max_path=max(r['path_error'] for r in rr),path_slack=3-max(r['path_error'] for r in rr),max_force=max(f['ratio'] for r in rr for f in r['forces']),force_slack=1.059-max(f['ratio'] for r in rr for f in r['forces']),max_reference_overspeed=max(r['reference_overspeed'] for r in rr),reference_slack=4.85-max(r['reference_overspeed'] for r in rr),max_body=max(r['body'] for r in rr),body_slack=100-max(r['body'] for r in rr),tracking_fraction_max=max(r['proposed_history'][0]/r['proposed_history'][1] for r in rr),tracking_history=rr[-1]['proposed_history'])

def main():
    cpu,wall=time.process_time(),time.perf_counter();result=rd(G/'retry/reference572_result.json');contract=rd(G/'retry/reference572_contract.json');items=[];gains=[]
    for e in result['events']:
        if not e.get('source_evaluated'):continue
        label=e['label'];case=rd(D/(label+'-strict-finish-private.json'));rows=case['rows'];duals=e['model']['local_duals'];item=dict(label=label,safe_finish=e['strict_safe_finish'],failure=e['strict_failure'],working_accept=e['working_accept'],strict_safety=safety(rows),local_model_reference_duals=duals['reference'],local_model_dominant_physical=duals['dominant_physical'],local_model_dominant_signed_support=duals['dominant_signed_support'])
        if e['strict_safe_finish']:
            item.update(actual_times=e['actual_times'],gain_step_ms=e['diagnostic_gain_ms'],cumulative_hull_gain_ms=1000*(result['seed_times']['hull_finish']-e['actual_times']['hull_finish']),official_candidate_raw=e['official_candidate_raw'],confirmation_raw=e['confirmation_raw'],official_finish_s=e['official_finish_s'],strict_diagnostic_prefix_exact=e['strict_diagnostic_prefix_exact'],objective_same_command_time_exact=e['objective_same_command_time_exact'])
        if e.get('working_accept'):gains.append(e['diagnostic_gain_ms'])
        items.append(item)
    recent=gains[-3:];window=bool(len(recent)==3 and sum(recent)<.10 and all(x<.05 for x in recent[-2:]));checks=dict(source_hashes_match=all(sha(G/p)==h for p,h in contract['source_sha256'].items()),all_accepted_safe=all(e['strict_safe_finish'] for e in result['events'] if e.get('working_accept')),safe_cases_objective_match=all(i.get('objective_same_command_time_exact',True) and i.get('strict_diagnostic_prefix_exact',True) for i in items),independent_full_tape_exact=(result.get('independent_verification') or {}).get('fullstate_force_history_tracker_exact'),existing_whole_not_replayed=not result['existing_whole_replay_repeated'])
    out=dict(checks=checks,actual_source_candidates=items,fresh_center_sensitivity_summaries=result['local_sensitivity_summaries'],accepted_step_gains_ms=gains,last_three_gain_sum_ms=sum(recent),observed_small_progress_window_met=window,stop_reason=result['stop_reason'],termination_interpretation='Only an observed small-gain window or measured failed-repair/safe-nonimprovement criterion is local stagnation evidence. A linearization/acceptance/resource cap alone is bounded termination,not convergence. Neither is a global/physical optimum proof.',dual_interpretation='Duals differentiate conditional RHS of one unrounded local LP with fixed Jacobian/rank/support/error/trust assumptions. Reference is a fixed design condition in this study,not a physical limit. Differing units prevent naive cross-constraint ranking. All actual source thresholds were unchanged.',scope='Source openloop660/13.20baseline;Native13.66 remains separate. No Native/feedbacktransition/robustness evidence added.',model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    atomic_write(G/'retry/reference572_analysis.json',out);ledger=rd(G/'retry/reference572_cost.json');ledger['finally_first_total']=ledger['total'];ledger['total']=result['cost']['total'];ledger['read_only_analysis']=dict(ticks=0,CPU_s=out['CPU_s'],wall_s=out['wall_s']);atomic_write(G/'retry/reference572_cost.json',ledger,True);print(json.dumps(out,indent=2))

if __name__=='__main__':main()
