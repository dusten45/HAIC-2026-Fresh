"""Read-only607 audit, including actual whole-task wall since acceptance."""
import time
CPU=time.process_time()
import hashlib,json,collections
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response607-private')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def main():
    r=read(G/'retry/pairs607_result.json');c=read(G/'retry/pairs607_contract.json');closed=read(D/'CLOSED-private.json')
    pairs=read(D/'all-pairs-private.json');task=read(D/'TASK_STARTED-private.json');checks={}
    checks['source_frozen']=all(sha(G/p)==h for p,h in c['source_sha256'].items())
    checks['input_checkpoint_and_runtime_pins']=sha(Path('/workspace/haic-response606-private/proposed-input-private.json'))==c['input_packet_sha256'] and sha(G/'retry/scalar603_contract.json')==c['runtime_manifest603_sha256']
    checks['registered_contract_and_closed_result']=read(D/'REGISTERED-private.json')['contract_sha256']==sha(G/'retry/pairs607_contract.json') and closed['result_sha256']==sha(G/'retry/pairs607_result.json')
    checks['all_private_outputs_pinned']=all(sha(D/p)==h for p,h in r['private_sha256'].items())
    tests=read(G/'retry/pairs607_tests.json');checks['pure_stubs_pass']=tests['passed'] and all(tests[k]==0 for k in ['real_choose','model','force','geometry'])
    checks['exactly_one_original_choose']=r['original_choose_calls']==r['cost']['chooser_calls']==1
    checks['zero_before_grid_pass']=r['zero_pass'] and r['zero_full_report_primitive_FINAL_first4_exact'] and r['zero_work_delta']==c['expected_zero_work_delta']
    checks['all_fixed_pairs_evaluated']=len(pairs)==r['grid_evaluated']==c['pairs']==42 and c['grid_points']==21
    checks['dedup_and_order']=len({q['action_bits'] for q in pairs})==42 and [q['index'] for q in pairs]==list(range(42))
    base=[q['u'] for q in pairs if q['row']=='base'];shifted=[q['u'] for q in pairs if q['row']=='shifted']
    checks['identical_fixed_descending_grid']=base==shifted==sorted(set(base),reverse=True)
    checks['row_result_counts']=all(sum(q['row']==name and q['report']['ok'] for q in pairs)==r['row_results'][name]['feasible']==9 for name in ['base','shifted'])
    selected=r['selected'];chosen=pairs[selected['index']]
    packet=read(Path('/workspace/haic-response606-private/proposed-input-private.json'))
    import struct
    modified=struct.unpack('<3f',bytes.fromhex(packet['stored_hold41_detail']['action_bits']))
    target=modified[1] if modified[1]>0 else -modified[2]
    eligible=[q for q in pairs if q['row']=='shifted' and q['report']['ok']]
    expected=min(eligible,key=lambda q:(abs(q['u']-target),-q['u'],q['index']))
    checks['selection_rule_and_no_original_FINAL_reuse']=chosen==expected and not selected['original_FINAL_reused'] and r['fresh_FINAL']==1
    counts=collections.Counter();certificates=0
    for name in ['zero-telemetry-private.json','joint-telemetry-private.json','final-telemetry-private.json']:
        q=read(D/name)
        for e in q['events']:
            if e['kind']=='BEFORE_MODEL_FORCE':counts['model_attempted']+=1
            if e['kind']=='AFTER_MODEL_TICK':counts['model_completed']+=1
            if e['kind']=='TRACKING_TRIAL_START':certificates+=1
        counts.update(w[0] for w in q['wheel_results'])
    checks['all_model_force_primitive_costs_counted']=all(counts[k]==r['cost'][k] for k in counts) and counts['external_force']+counts['internal_force']==r['cost']['total_force']
    checks['exact_certificate_count']=certificates==31+42+1
    events=collections.Counter();head='0'*64;n=0;sequence=[]
    for line in (D/'applied-journal-private.jsonl').read_text().splitlines():
        e=json.loads(line);h=e.pop('sha256');assert e['previous']==head and e['sequence']==n and digest(e)==h
        n+=1;head=h;events[e['kind']]+=1;sequence.append(e['kind'])
    checks['durable_journal_chain']=True
    checks['whole_reservation_precedes_any_application']=sequence[0]=='FULL_STUDY_RESERVE' and events['FULL_STUDY_RESERVE']==1
    checks['per_certificate_remainder_reservations']=events['REMAINING_RESERVE']==42+1
    a=read(D/'shifted-apply-rows-private.json');b=read(D/'shifted-replay-rows-private.json');z=read(D/'zero-apply-rows-private.json')
    checks['strict_12raw_and_independent_replay']=r['applied_raw']==12 and all(len(q['rows'])==4 and all(not x['pre_failure'] and not x['post_failure'] and x['body']<100 for x in q['rows']) for q in [a,b,z]) and digest(a)==digest(b) and r['independent_replay']
    checks['only_saved_raw160_to164']=all(q['rows'][0]['global_raw_before']==160 and q['checkpoint']['global_raw']==164 for q in [a,b,z])
    checks['all_work_caps_and_original_kernel']=all(r['cost'][k]<=v for k,v in c['caps'].items()) and r['kernel_hardcap']==200000 and r['model_counter']==r['cost']['model_completed']
    checks['zero_forbidden_work_original_ledger']=all(r[k]==0 for k in ['native','worlds','resets','actions','new_seed','HOLDOUT','SEALED','carry','FD','solver']) and r['research_remaining']==22211 and r['reserve']==84000 and r['reserve_used']==0
    checks['local_scope_only']=not r['native_admission'] and not r['whole_lap_claim'] and r['native_incumbent_s']==13.22
    checks['606_overtime_preserved']=sha(G/'retry/forensic606_closeout.json')==c['prior606_overtime_preserved']
    audit_cpu=time.process_time()-CPU
    totals=dict(CPU_s=closed['time']['CPU_s']+audit_cpu,wall_s=time.time()-task['start_epoch'])
    checks['actual_whole_task_time_with_cleanup_reserve']=totals['CPU_s']+30<600 and totals['wall_s']+60<900
    out=dict(study=607,status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILURE',checks=checks,
        certificates=certificates,counts_from_primitive_results=dict(counts),durable_events=dict(events),
        task_start_utc=task['start_utc'],audit_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),total_through_audit=totals,
        CPU_prior_preparation_charge_s=10,cleanup_reserve=dict(CPU_s=30,wall_s=60),new_evaluations=0,
        selected_vs_zero_progress_delta_diagnostic=a['checkpoint']['progress']-z['checkpoint']['progress'],
        result_sha256=sha(G/'retry/pairs607_result.json'))
    (G/'retry/pairs607_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert all(checks.values())
if __name__=='__main__':main()
