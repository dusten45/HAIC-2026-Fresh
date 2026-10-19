"""Read-only final audit: measured primitive recovery and full-command outcomes."""
import json,time
from pathlib import Path
import numpy as np
from retry.clip561_core import atomic_write
from retry.path569_design import sha

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response571-private');rd=lambda p:json.loads(p.read_text())

def main():
    cpu,wall=time.process_time(),time.perf_counter();r=rd(G/'retry/repair571_result.json');contract=rd(G/'retry/repair571_contract.json');prior=rd(G/'retry/tail570_result.json');items=[];recoveries=[]
    for e in r['events']:
        if not e.get('source_evaluated'):continue
        label=e['label'];case=rd(D/(label+'-strict-finish-private.json'));rows=[q for q in case['rows'] if 'root_without_roads' in q];support=rd(D/(label+'-support-private.json'));q=np.asarray(support['seed_slacks']);L=np.asarray(support['error_coefficients'])
        item=dict(label=label,strict_safe_finish=e['strict_safe_finish'],strict_failure=e['strict_failure'],working_accept=e['working_accept'],signed_support_rows=len(q),minimum_seed_support_slack=float(min(q)),maximum_support_error_coefficient=float(max(L)),zero_step_seed_included=e['model']['precheck']['exact_seed_included'],min_evaluated_footprint=min(x['margin'] for x in rows),max_path=max(x['path_error'] for x in rows),max_force=max(f['ratio'] for x in rows for f in x['forces']),max_reference_overspeed=max(x['reference_overspeed'] for x in rows),max_body=max(x['body'] for x in rows),final_history=case['checkpoint']['tracking'])
        if e['strict_safe_finish']:
            item.update(objective_same_command_time_exact=e['objective_same_command_time_exact'],strict_diagnostic_prefix_exact=e['strict_diagnostic_prefix_exact'],actual_times=e['actual_times'],gain_this_step_ms=e['diagnostic_gain_ms'],cumulative_gain_vs570working_ms=1000*(r['seed_times']['hull_finish']-e['actual_times']['hull_finish']),cumulative_gain_vs565_ms=1000*(prior['seed_times']['hull_finish']-e['actual_times']['hull_finish']),official_candidate_raw=e['official_candidate_raw'],confirmation_raw=e['confirmation_raw'],official_finish_s=e['official_finish_s'])
        else:
            last=case['rows'][-1];item['rejected_raw']=last.get('global_raw_after',last['global_raw_before']);item['rejected_margin']=last.get('margin');item['not_incumbent']=True
        if e.get('measured_error_recovery'):recoveries.append(dict(label=label,**e['measured_error_recovery']))
        items.append(item)
    checks=dict(source_hashes_match_contract=all(sha(G/p)==h for p,h in contract['source_sha256'].items()),all_model_seeds_included=all(x['zero_step_seed_included'] for x in items),all_accepted_cases_safe=all(e['strict_safe_finish'] for e in r['events'] if e.get('working_accept')),all_safe_cases_objective_and_execution_match=all(x.get('objective_same_command_time_exact',True) and x.get('strict_diagnostic_prefix_exact',True) for x in items),final_independent_full_tape_exact=(r.get('independent_verification') or {}).get('fullstate_force_history_tracker_exact'),existing_whole_not_replayed=not r['existing_whole_replay_repeated'],actual_and_protected_zero=r['new_native_actions']==r['new_resets']==r['HOLDOUT']==r['SEALED']==r['paid_compute']==r['reserve_used']==0)
    out=dict(checks=checks,candidates=items,observed_component_recoveries=recoveries,scope='Signed support certifies only its fixed polygon/component separation;coverage and other components remain exact-validator checks. Per-center base support set covers573..580,with observed additional components introduced within that center and perfeature coefficient floors retained. No universal empirical-error,feedback/native/robustness claim.',termination='A bounded direction/recovery/acceptance/stagnation rule terminates this run;not a convergence or directional/global infeasibility proof.',model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    atomic_write(G/'retry/repair571_analysis.json',out);ledger=rd(G/'retry/repair571_cost.json');ledger['finally_first_total']=ledger['total'];ledger['total']=r['cost']['total'];ledger['read_only_analysis']=dict(ticks=0,CPU_s=out['CPU_s'],wall_s=out['wall_s']);atomic_write(G/'retry/repair571_cost.json',ledger,True);print(json.dumps(out,indent=2))

if __name__=='__main__':main()
