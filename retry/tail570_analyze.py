"""Read-only validation of full-command objective alignment and exact outcomes."""
import json,time
from pathlib import Path
import numpy as np
from retry.clip561_core import atomic_write
from retry.path569_design import sha

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response570-private');rd=lambda p:json.loads(p.read_text())

def main():
    cpu,wall=time.process_time(),time.perf_counter();result=rd(G/'retry/tail570_result.json');contract=rd(G/'retry/tail570_contract.json');tape=rd(Path('/workspace/haic-response565-private/final-tape-private.json'));seed_x=np.array([v for q in tape['commands'] if 133<=q['index']<=166 for v in [q['action'][0],q['action'][1]-q['action'][2]]]);items=[]
    for e in result['events']:
        if not e.get('source_evaluated'):continue
        label=e['label'];diag=rd(D/(label+'-diagnostic-private.json'));strict=rd(D/(label+'-strict-finish-private.json'));rows=[r for r in strict['rows'] if 'root_without_roads' in r];x=np.asarray(strict['x']);pair_changes=np.any(x.reshape(-1,2)!=seed_x.reshape(-1,2),axis=1)
        stats=dict(min_footprint=min(r['margin'] for r in rows),max_path=max(r['path_error'] for r in rows),max_force=max(f['ratio'] for r in rows for f in r['forces']),max_reference_overspeed=max(r['reference_overspeed'] for r in rows),max_body=max(r['body'] for r in rows),tracking_history=strict['checkpoint']['tracking'])
        item=dict(label=label,strict_safe_finish=e['strict_safe_finish'],working_accept=e['working_accept'],changed_holds_before153=int(sum(pair_changes[:20])),changed_holds153_to166=int(sum(pair_changes[20:])),actual_evaluated_raws=len(rows),exact_safety=stats,predicted_gain_ms=e['model']['predicted_gain_ms'])
        if not e['strict_safe_finish']:
            last=rows[-1];n=int(label.split('-')[1])+1;linear=np.asarray(rd(D/f'linear-{n}-private.json')['linear']['J']);env=rd(D/f'envelope-{n}-private.json');previous=[p for p in result['events'] if p.get('working_accept') and int(p['label'].split('-')[1])<n-1][-1];center=rd(D/(previous['label']+'-diagnostic-private.json'));index=10*(last['global_raw_after']-529);dx=x-np.asarray(center['x']);pred=center['g'][index]+linear[index]@dx;target=env['g'][index]*e['model']['normalized_step']
            item['rejection']=dict(gate=e['strict_failure'],global_raw=last['global_raw_after'],actual_footprint=last['margin'],required_footprint=.5,shortfall_m=.5-last['margin'],linear_predicted_footprint_slack=float(pred),empirical_error_target=float(target),predicted_tightened_slack=float(pred-target),not_incumbent=True)
        if e['strict_safe_finish']:
            item.update(candidate_raw=e['official_candidate_raw'],confirmation_raw=e['confirmation_raw'],official_finish_s=e['official_finish_s'],actual_times=e['actual_times'],whole_cumulative_hull_gain_ms=1000*(result['seed_times']['hull_finish']-e['actual_times']['hull_finish']),accepted_step_gain_ms=e['diagnostic_gain_ms'],objective_same_command_time_exact=e['objective_same_command_time_exact'],diagnostic_strict_prefix_exact=e['strict_and_diagnostic_prefix_exact'],prediction_error_ms=e['model']['predicted_gain_ms']-e['diagnostic_gain_ms'])
        items.append(item)
    linear=rd(D/'linear-1-private.json')['linear'];P=np.asarray(linear['P']);J=np.asarray(linear['J']);causal=True;maxearly=0.
    for j in range(40,68):
        n=min(134,4*(j//2));a=max(float(np.max(abs(P[:n,:,j]))) if n else 0.,float(np.max(abs(J[:10*n,j]))) if n else 0.);maxearly=max(maxearly,a);causal &= a==0
    checks=dict(source_hashes_match_contract=all(sha(G/p)==h for p,h in contract['source_sha256'].items()),all_remaining_34_holds_are_variables=len(seed_x)==68,tail_FD_has_no_earlier_state_effect=causal,maximum_premature_derivative=maxearly,strict_objective_matches_diagnostic_command_trajectory=all(i.get('objective_same_command_time_exact',True) for i in items),independent_full_tape_exact=(result.get('independent_verification') or {}).get('fullstate_force_history_tracker_exact'),no_feedback_method1_evaluations=result['feedback_calls']==0,no_existing_seed_whole_replay=result['existing_whole_replay_repeated'] is False)
    out=dict(checks=checks,candidates=items,scope='A deterministic source-model open-loop command trajectory from exact565raw528 to unchanged official finish. No native driving, pixel/latency/disturbance robustness, or safe switch/recovery guarantee to existing feedback. Whole prediction and evaluation use identical command sequences; interpolation guides search while official raw/time decide whole promotion.',model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    atomic_write(G/'retry/tail570_analysis.json',out);ledger=rd(G/'retry/tail570_cost.json');ledger['finally_first_total']=ledger['total'];ledger['total']=result['cost']['total'];ledger['read_only_analysis']=dict(ticks=0,CPU_s=out['CPU_s'],wall_s=out['wall_s']);atomic_write(G/'retry/tail570_cost.json',ledger,True);print(json.dumps(out,indent=2))

if __name__=='__main__':main()
