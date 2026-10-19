"""Read-only closeout of604 technical stop. No evaluator imports or calls."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import hashlib,json,collections
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response604-private')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def main():
    r=read(G/'retry/residual604_result.json');c=read(G/'retry/residual604_contract.json')
    closed=read(D/'CLOSED-private.json');old=read(Path('/workspace/haic-response597-private/final-independent-tape-private.json'))
    checks={};checks['as_executed_sources_frozen']=all(sha(G/p)==h for p,h in c['source_sha256'].items())
    checks['contract_pinned']=sha(G/'retry/residual604_contract.json')==r['contract_sha256']==read(D/'REGISTERED-private.json')['contract_sha256']
    checks['result_closed_hash']=sha(G/'retry/residual604_result.json')==closed['result_sha256']
    checks['private_evidence_pinned']=all(sha(D/p)==h for p,h in r['private_sha256'].items())
    checks['exact_expected_technical_stop']=r['status']=='TECHNICAL_OR_POSITIVE_CONTROL_STOP' and r['error']=="AttributeError:'Study' object has no attribute 'geometry_context'"
    rows=[];events=collections.Counter();head='0'*64;sequence=0
    for line in (D/'applied-journal-private.jsonl').read_text().splitlines():
        q=json.loads(line);h=q.pop('sha256');assert q['sequence']==sequence and q['previous']==head and digest(q)==h
        sequence+=1;head=h;events[q['kind']]+=1
        if q['kind']=='APPLIED_RESULT':rows.append(q['row'])
    checks['durable_journal_chain_valid']=True
    checks['156applied_no_forecast_ticks']=len(rows)==156 and events['APPLIED_TICK_START']==events['APPLIED_TICK_END']==156
    keys=['index','raw','action','global_raw_before','episode_before_s','before_root_without_roads','forces',
          'tracking_history_before','launch_history_before','proposed_history','pre_failure','diagnostic_probe',
          'root_without_roads','episode_after_s','global_raw_after','progress','progress_delta','projection_limit',
          'margin','path_error','reference_overspeed','body','visited_count','tracker','post_failure','all_failures',
          'tick_executed','visited','checkpoint_sha256','official_finish_raw']
    checks['all156fullrows_exact597']=all(all(digest(q[k])==digest(expected[k]) for k in keys) for q,expected in zip(rows,old['rows'][:156]))
    checks['all156strict_safe']=all(q['pre_failure'] is None and q['post_failure'] is None and not q['all_failures'] and q['body']<100 for q in rows)
    checks['raw96_full_checkpoint_exact597']=digest(read(D/'raw96-checkpoint-private.json'))==old['rows'][95]['checkpoint_sha256']
    checks['final_raw156_full_checkpoint_exact597']=digest(read(D/'final-checkpoint-private.json'))==old['rows'][155]['checkpoint_sha256']
    hold40=read(D/'zero-hold-040-private.json')
    checks['hold40_no_policy_primitive_dispatch']=not hold40['events'] and not hold40['wheel_results'] and hold40['detail'] is None
    checks['no_nonzero_candidate_or_replay_started']=not list(D.glob('H*-STARTED-private.json')) and not (D/'REPLAY_STARTED-private.json').exists()
    checks['no_repeated_prefix']=len(list(D.glob('prefix-hold-*-private.json')))==24 and len(list(D.glob('zero-hold-*-private.json')))==16
    checks['helper157comparisons_exact']=r['cost']['helper_original_comparisons']==157
    checks['force_and_model_accounting']=r['cost']['model_attempted']==r['cost']['model_completed']==r['model_counter']==156 and r['cost']['external_force']==r['cost']['internal_force']==624 and r['cost']['total_force']==1248
    checks['all_work_caps']=all(r['cost'][k]<=cap for k,cap in c['caps'].items())
    checks['zero_not_completed']=not r['candidates'] and not r['checks'].get('zero_all_rows_choices_and_checkpoint_exact597',False)
    checks['zero_forbidden_work']=all(r[k]==0 for k in ['native','worlds','resets','actions','new_seed','HOLDOUT','SEALED','carry'])
    checks['ledger_unchanged']=r['research_remaining']==22211 and r['reserve']==84000 and r['reserve_used']==0
    checks['no_lap_native_or_general_promotion']=not r['whole_lap_claim'] and not r['native_admission'] and not r['general_promotion']
    dt=dict(CPU_s=time.process_time()-CPU,wall_s=time.perf_counter()-WALL)
    total={k:closed['time'][k]+dt[k] for k in dt}
    checks['time_caps_with30_45cleanup_reserve']=total['CPU_s']+30<5400 and total['wall_s']+45<6600
    out=dict(study=604,status='READ_ONLY_AUDIT_PASS_TECHNICAL_STOP_PRESERVED' if all(checks.values()) else 'AUDIT_FAILURE',
        checks=checks,journal_events=dict(events),journal_head=head,
        actual_progress=dict(prefix_raw=96,zero_additional_raw=60,final_global_raw=156,zero_status='PARTIALLY_EXECUTED_TECHNICAL_STOP',
            nonzero_policies_started=0,full_s400_evaluations_completed=0,actual537choose_invocations=0,pre_dispatch_choose_intent_counter=r['cost']['chooser_calls'],
            explanation='chooser_calls increment precedes evaluation of missing geometry_context argument; original537function is never invoked. Frozen result uncompleted list denotes no completed result, not zero unstarted.'),
        audit_time=dt,total_through_audit=total,fix_patch_applied=False,retry_executed=False,
        result_sha256=sha(G/'retry/residual604_result.json'),source=0,model=0,force=0,geometry=0,native=0)
    (G/'retry/residual604_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert all(checks.values())
if __name__=='__main__':main()
