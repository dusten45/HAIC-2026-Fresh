"""Saved-evidence audit only. No policy, force, geometry or physics imports."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import collections,hashlib,json,math
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response605-private')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def main():
    raw_path=D/'as-executed-result-private.json'
    r=read(raw_path);public=read(G/'retry/residual605_result.json');c=read(G/'retry/residual605_contract.json');closed=read(D/'CLOSED-private.json')
    tests=read(G/'retry/residual605_tests.json');review=read(G/'retry/residual605_change_review.json')
    checks={}
    checks['frozen_source_pins']=all(sha(G/p)==h for p,h in c['source_sha256'].items())
    checks['604_failure_and_cost_preserved']=sha(G/'retry/residual604_result.json')==c['prior604_result_sha256'] and sha(G/'retry/residual604.py')==c['prior604_code_sha256']
    checks['19_unchanged_method_checks']=review['passed'] and all(review['checks'].values()) and len(review['checks'])==19
    checks['registered_and_closed_pins']=sha(G/'retry/residual605_contract.json')==r['contract_sha256']==read(D/'REGISTERED-private.json')['contract_sha256'] and sha(raw_path)==closed['result_sha256']
    from retry.residual605_public import projection
    checks['public_aggregate_exact_projection_raw_reports_private']=digest(public)==digest(projection(r,sha(raw_path)))
    checks['required_pure_stubs_pass']=tests['passed'] and tests['clone_memo_checks']['passed'] and tests['context_transition_stubs']['passed']
    checks['stub_no_science']=all(tests['context_transition_stubs'][k]==0 for k in ['actual_choose','physics_ticks','force_evaluator','geometry_evaluator','native'])
    checks['all_private_evidence_pinned']=all(sha(D/p)==h for p,h in r['private_sha256'].items())
    checks['new_raw96_checkpoint_exact']=r['checks'].get('raw96_initial_prefix_all_rows_and_full_checkpoint_exact597',False)
    checks['zero_completed_exact597']=r['checks'].get('zero_all_rows_choices_and_checkpoint_exact597',False) and r['checks'].get('zero_saved597_worldplanes_exact',False)
    checks['not_604_partial_control']=read(D/'raw96-checkpoint-private.json')==read(Path('/workspace/haic-response604-private/raw96-checkpoint-private.json'))
    events=collections.Counter();applied=collections.defaultdict(list);head='0'*64;n=0
    for line in (D/'applied-journal-private.jsonl').read_text().splitlines():
        row=json.loads(line);h=row.pop('sha256');assert row['sequence']==n and row['previous']==head and digest(row)==h
        n+=1;head=h;events[row['kind']]+=1
        if row['kind']=='APPLIED_RESULT':applied[row['label']].append(row['row'])
    checks['durable_journal_valid']=True
    token_counts=collections.Counter()
    for p in D.glob('*-hold-*-private.json'):
        data=p.read_bytes()
        for label,token in [('model_attempted',b'"kind": "BEFORE_MODEL_FORCE"'),('model_completed',b'"kind": "AFTER_MODEL_TICK"'),
                            ('external_force',b'"external_force",\n'),('internal_force',b'"internal_force",\n')]:
            token_counts[label]+=data.count(token)
    checks['all_forecast_reject_FINAL_applied_model_and_force_charged']=all(token_counts[k]==r['cost'][k] for k in token_counts) and token_counts['external_force']+token_counts['internal_force']==r['cost']['total_force']
    old=read(Path('/workspace/haic-response597-private/final-independent-tape-private.json'))
    keys=list(applied['prefix'][0]) if applied['prefix'] else []
    def row_match(a,b):return all(k in b and digest(v)==digest(b[k]) for k,v in a.items())
    checks['new_prefix96_raws_independently_counted_and_exact']=len(applied['prefix'])==96 and all(row_match(a,b) for a,b in zip(applied['prefix'],old['rows'][:96]))
    zero=next((q for q in r['candidates'] if q['label']=='zero'),None)
    checks['zero_full_interval_allrows_exact']=zero is not None and zero['safe_s400'] and all(row_match(a,old['rows'][a['global_raw_before']]) for a in applied['zero'])
    fixed_order=[n for n,_ in c['family']]
    observed_order=[q['label'] for q in r['candidates']]
    checks['fixed_family_order_no_retries']=observed_order==fixed_order[:len(observed_order)] and all(len(list(D.glob(n+'-STARTED-private.json')))<=1 for n in fixed_order)
    checks['all_coefficients_frozen']=all(q['coefficients']==dict(c['family'])[q['label']] for q in r['candidates'])
    safe=[];baseline=zero['crossings']['400']['time_s'] if zero and zero['safe_s400'] else None
    for q in r['candidates']:
        label=q['label'];data=read(D/(label+'-result-private.json'))
        rr=data['rows']
        assert digest(rr)==digest(applied[label])
        if q['safe_s400']:
            assert all(x.get('tick_executed') and not x['pre_failure'] and not x['post_failure'] and x['body']<100 for x in rr)
            assert q['crossings']['400']['eligible'] and q['crossings']['400']['whole_hold_safe']
            gain=baseline-q['crossings']['400']['time_s'];assert gain==q['s400_gain_s']
            if label!='zero' and gain>0:safe.append(q)
        elif q['stop'].startswith('APPLIED_STRICT_'):
            assert rr and (rr[-1].get('pre_failure') or rr[-1].get('post_failure'))
        assert q['endpoint_is_official_lap'] is False
    checks['all_candidate_rows_and_outcomes_consistent']=True
    best=min(safe,key=lambda q:q['crossings']['400']['time_s']) if safe else None
    checks['best_selection_fixed_order_no100or500ms_gate']=r['best_evaluated_label']==(best['label'] if best else None)
    if r['replay'] and r['replay'].get('exact'):
        replay=read(D/'independent-replay-private.json');chosen=read(D/(best['label']+'-result-private.json'))
        expected=applied['prefix']+chosen['rows']
        checks['only_one_conditional_replay']=best is not None and r['replay']['label']==best['label'] and len(list(D.glob('REPLAY_STARTED-private.json')))==1
        checks['independent_replay_allrows_checkpoint_planes_exact']=digest(replay['rows'])==digest(expected) and digest(replay['checkpoint'])==digest(chosen['checkpoint']) and digest(replay['crossings'])==digest(chosen['crossings'])
    else:
        checks['no_unconditional_replay']=not (D/'REPLAY_STARTED-private.json').exists() or (r['replay'] and not r['replay'].get('exact') and 'CENSORED' in r['replay'].get('status',''))
    checks['all_global_work_caps']=all(r['cost'][k]<=cap for k,cap in c['caps'].items())
    checks['model_counter_unchanged_kernel']=r['model_counter']==r['cost']['model_completed'] and r['kernel_hardcap']==200000
    checks['zero_forbidden_work_and_original_ledger']=all(r[k]==0 for k in ['native','worlds','resets','actions','new_seed','HOLDOUT','SEALED','carry']) and r['research_remaining']==22211 and r['reserve']==84000 and r['reserve_used']==0
    checks['no_full_lap_native_or_general_claim']=not r['whole_lap_claim'] and not r['native_admission'] and not r['general_promotion'] and r['native_incumbent_s']==13.22
    dt=dict(CPU_s=time.process_time()-CPU,wall_s=time.perf_counter()-WALL);total={k:closed['time'][k]+dt[k] for k in dt}
    checks['time_caps_with30_45summary_reserve']=total['CPU_s']+30<5400 and total['wall_s']+45<6600
    out=dict(study=605,status='READ_ONLY_AUDIT_PASS' if all(checks.values()) else 'AUDIT_FAILURE',checks=checks,
        durable_events=dict(events),durable_head=head,primitive_counts_from_all_hold_files=dict(token_counts),
        applied_rows_by_label={k:len(v) for k,v in applied.items()},audit_time=dt,total_through_audit=total,
        summary_reserve=dict(CPU_s=30,wall_s=45),new_scientific_evaluations=0,as_executed_sha256=sha(raw_path),public_result_sha256=sha(G/'retry/residual605_result.json'))
    (G/'retry/residual605_audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2));assert all(checks.values())
if __name__=='__main__':main()
