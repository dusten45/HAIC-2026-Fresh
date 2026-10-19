"""Read-only interrupted-run reconciliation; never runs the simulator."""
import datetime,json,time
from pathlib import Path
from retry.durable568 import inspect
from retry.clip561_core import atomic_write
from retry.reference572_model import CAPS,TOTAL
from retry.path569_design import sha

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response572-private');rd=lambda p:json.loads(p.read_text())
def main():
    cpu,wall=time.process_time(),time.perf_counter();r=rd(G/'retry/reference572_result.json');start=rd(D/'RECOVERY_STARTED.json');a=inspect(D/'raw-journal-private.jsonl');b=inspect(D/'recovery-raw-journal-private.jsonl');seen=set();duplicates=[]
    for path in [D/'raw-journal-private.jsonl',D/'recovery-raw-journal-private.jsonl']:
        for line in path.open():
            e=json.loads(line)
            if e['kind']!='AFTER_TICK':continue
            c=e['context'];key=(c['label'].removesuffix('-resume'),c['global_raw'],c['index'],c['raw'])
            if key in seen:duplicates.append(key)
            seen.add(key)
    counts={k:a['kinds'].get(k,0)+b['kinds'].get(k,0) for k in set(a['kinds'])|set(b['kinds'])};c=r['cost'];total=c['total'];sums={name:{key:sum(p[key] for p in c['phases'] if p['bucket']==name) for key in cap} for name,cap in CAPS.items()};checks=dict(original_input_hashes_match=all(sha(Path(p))==h for p,h in rd(G/'retry/reference572_contract.json')['input_sha256'].items()),original_source_hashes_match=all(sha(G/p)==h for p,h in rd(G/'retry/reference572_contract.json')['source_sha256'].items()),recovery_source_hash_matches=sha(G/'retry/reference572_recover.py')==start['recovery_source_sha256'],both_journal_chains_valid=a['valid'] and b['valid'],no_duplicate_source_ticks=not duplicates,source_tick_cost_exact=total['ticks']==counts['AFTER_TICK'],source_force_cost_exact=total['force']==4*counts['FORCE_VERDICT'],aggregate_charges_within_original_caps=all(total[k]<=v for k,v in TOTAL.items()),bucket_charges_within_original_caps=all(sums[n][k]<=v for n,cap in CAPS.items() for k,v in cap.items()),independent_exact=bool((r.get('independent_verification') or {}).get('fullstate_force_history_tracker_exact')))
    out=dict(status='RECOVERED_SAME_572' if r['completed'] and all(checks.values()) else 'INCOMPLETE_OR_AUDIT_FAILURE',deadline_KST='2026-10-20T19:01:55+09:00',authorization='Explicit user extension transcript supplied in latest delegation; supersedes closeout authorization interpretation. Historical failure records preserved.',checks=checks,old_journal=a,recovery_journal=b,combined_event_counts=counts,duplicate_ticks=duplicates,cost=dict(exact_source_ticks=counts['AFTER_TICK'],exact_force_rows=4*counts['FORCE_VERDICT'],old_exact_ticks=a['kinds']['AFTER_TICK'],new_exact_ticks=b['kinds']['AFTER_TICK'],old_measured_CPU_lower_s=396.682209993,old_CPU_wall_exact_lost=True,historical_aggregate_budget_charge_s=500.,historical_verification_budget_charge_s=25.,historical_charge_interpretation='Conservative accounting reservations, not measured CPU recovery. The stopped process last verification journal write was 13.923s after its error record; the 25s verification reservation includes a termination allowance. Aggregate500s exceeds the original registered-to-closeout wall interval. Exact historical CPU and strict CPU-cap certification cannot be reconstructed.',new_metered_CPU_after_recovery_marker_s=total['CPU_s']-500.,new_metered_wall_after_recovery_marker_s=total['wall_s']-500.,aggregate_charged=total,bucket_charged=sums),reused_completed_FD_columns=109,resumed_partial_FD_prefix_ticks=30,reused_independent_prefix_ticks=489,independent_remaining_ticks=(r.get('independent_verification') or {}).get('new_ticks'),native_actions_and_resets_zero=bool(r['new_native_actions']==0 and r['new_resets']==0),HOLDOUT=r['HOLDOUT'],SEALED=r['SEALED'],paid_compute=r['paid_compute'],research_remaining=r['research_remaining'],reserve=r['reserve'],reserve_used=r['reserve_used'],original_failure_sha256=sha(D/'ERROR-private.json'),closeout_records_preserved=True,files_transferred_this_recovery=False,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    full_path=D/'final-independent-tape-private.json'
    if full_path.exists():
        full=rd(full_path)['rows'];tracking=[v for v in full if v['index']>24];launch=[v for v in full if v['index']<=24]
        out['full_independent_safety']=dict(raw_count=len(full),minimum_footprint=min(v['margin'] for v in full),maximum_path=max(v['path_error'] for v in full),maximum_body=max(v['body'] for v in full),maximum_tracking_force=max(f['ratio'] for v in tracking for f in v['forces']),maximum_launch_force=max(f['ratio'] for v in launch for f in v['forces']),maximum_tracking_reference_overspeed=max(v['reference_overspeed'] for v in tracking),maximum_tracking_clip_fraction=max(v['proposed_history'][0]/v['proposed_history'][1] for v in tracking),maximum_checked_launch_clip_fraction=max(v['proposed_history'][0]/v['proposed_history'][1] for v in launch if v['index']>=24),all_original_failure_flags_clear=all(not v.get('pre_failure') and not v.get('post_failure') for v in full))
    out['partial_FD_recovery_payload_sha256']=sha(D/'FD-2-41-recovered-private.json')
    out['interrupted_FD_last_tick_validation']='Original AFTER_TICK raw558 existed; missing post-tick geometry/verdict was reconstructed without reintegration, and full recovered FD rows were saved privately. One extra geometry check is charged.'
    out['supersedes_authorization_interpretation_only']='delegation_closeout_20261019.md/json; all failure evidence retained'
    atomic_write(G/'retry/reference572_recovery.json',out);print(json.dumps(out,indent=2))
if __name__=='__main__':main()
