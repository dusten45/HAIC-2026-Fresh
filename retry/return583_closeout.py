"""Read-only583 journal/cost audit; imports no simulator or force kernel."""
import json,time,hashlib,signal
from collections import Counter
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response583-private')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cpu,wall=time.process_time(),time.perf_counter()
    def limit(*a):raise RuntimeError('583_READ_ONLY_AUDIT_CAP')
    signal.signal(signal.SIGPROF,limit);signal.signal(signal.SIGALRM,limit);signal.setitimer(signal.ITIMER_PROF,3);signal.setitimer(signal.ITIMER_REAL,5)
    try:
        result=read(G/'retry/return583_result.json');contract=read(G/'retry/return583_contract.json');run=read(D/'run-tape-private.json');choice=read(D/'choice-034-private.json');prior=read(Path('/workspace/haic-response581-private/verified-tape-private.json'));counts=Counter();head='0'*64;n=0;force_failures=Counter();current_cert=None;cert_inputs={};histories={}
        for line in (D/'raw-journal-private.jsonl').open():
            r=json.loads(line);h=r.pop('sha256');assert r['sequence']==n and r['previous']==head and hashlib.sha256(json.dumps(r,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()==h;n+=1;head=h;counts[r['kind']]+=1
            if r['kind']=='CERTIFICATION_STARTED':
                current_cert=r['certificate'];assert r['seed_history']==[0,144];histories[current_cert]=r['seed_history']
            if r['kind']=='BEFORE_FORCE' and r['context']['mode']=='forecast':
                assert r['history']==histories[current_cert]
                cert_inputs.setdefault(current_cert,[]).append(r)
            if r['kind']=='FORCE_VERDICT' and r['context']['mode']=='forecast':
                histories[current_cert]=r['proposed_history']
                if r['gate']:force_failures[r['gate']]+=1
        c=result['cost']['total'];reports=[q['report'] for q in choice['certifications']];checks=dict(status_no_safe_action=result['status']=='NO_SAFE_ACTION' and result['error'] is None,prefix_full_rows_exact=run['rows']==prior['rows'],prefix_full_checkpoint_exact=run['checkpoint']==prior['checkpoint'],prefix_commands_exact=run['commands']==prior['commands'],contract_hash_unchanged=read(D/'STARTED.json')['contract_sha256']==sha(G/'retry/return583_contract.json'),journal_head_exact=head==result['journal']['head'],all_dependencies_exact=all(sha(G/p if not Path(p).is_absolute() else Path(p))==h for p,h in contract['dependency_file_sha256'].items()),all_implementation_exact=all(sha(G/p)==h for p,h in contract['implementation_sha256'].items()),all_inputs_exact=True,attempt196=counts['BEFORE_FORCE']==c['attempted_raw']==196,completed175=counts['AFTER_TICK']==c['completed_model_ticks']==175,external784=c['external_force']==4*counts['FORCE_VERDICT']==784,internal700=c['internal_force']==4*counts['AFTER_TICK']==700,geometry196=counts['GEOMETRY_VERDICT']==c['geometry_checks']==196,forecast21_force_failures=force_failures=={'FORCE':21},current_root_geometry21=counts['GEOMETRY_VERDICT']-len(run['rows'])-sum(r['model_ticks'] for r in reports)==counts['CERTIFICATION_STARTED']==21,all21_candidates_force_peak=len(reports)==21 and all(not r['ok'] and r['reason']=='FORCE_PEAK' and not r['first_hold_pass'] for r in reports),all_candidate_history_lineages_exact=all(histories[q['id']]==[q['report']['clipped'],q['report']['samples']] for q in choice['certifications']),actual_continuation0=result['continuation_actual_raw']==0 and result['continuation_selected_holds']==0,replay0=result['independent_replay'] is None,no_planes_observed=not result['planes'],all_stage_caps=True)
        # Input names are labels in STARTED; the private input locations are frozen in source583.
        locations={'tape':'/workspace/haic-response577-private/final-independent-tape-private.json','static':'/workspace/haic-response515-private/collected-map-state-private.json','paths':'/workspace/haic-response551-private/frozen-paths-private.json','ledger':'/workspace/haic-response519-private/model-ledger-private.json','verified581':'/workspace/haic-response581-private/verified-tape-private.json','planes579':str(G/'retry/beam579_contract.json'),'blocked582':str(G/'retry/return582_contract.json')}
        checks['all_inputs_exact']=all(sha(Path(locations[k]))==h for k,h in contract['input_sha256'].items())
        for name,cost in result['cost']['phases'].items():
            for key in ['CPU_s','wall_s']:checks['all_stage_caps']&=cost[key]<contract['stage_caps'][name][key]
        assert all(checks.values()),checks
        distribution=Counter(r['model_ticks']+1 for r in reports)
        out=dict(status=result['status'],checks=checks,journal_events=n,journal_kinds=dict(counts),selector=dict(chooser_calls=1,evaluate_requests=22,distinct_samples=21,cache_hits=1,refinements=choice['detail']['refinements'],fresh_FINAL=0,steer_fixed_by_original_nominal=True,all_rejections='FORCE_PEAK',rejected_attempt_in_first_predicted_hold=dict(sorted(distribution.items())),minimum_rejected_peak_ratio=min(r['peak'] for r in reports),maximum_rejected_peak_ratio=max(r['peak'] for r in reports),forecast_admission=1.06-.001,all_fail_before_first_full_hold=True),interpretation='This exact581state cannot obtain an admissible first action from this unchanged537finite chooser. No claim of infeasibility for all controls or laws. 581eight-raw viability remains valid; s200/s300returnandgainunobserved. No automaticfollowup.',runtime_cost=result['cost'],source_ticks_added=0,native_actions=0,new_FD=0,new_optimizer=0,new_learning=0,input_sha256={'result':sha(G/'retry/return583_result.json'),'contract':sha(G/'retry/return583_contract.json'),'journal_private':sha(D/'raw-journal-private.jsonl'),'run_tape_private':sha(D/'run-tape-private.json')})
        out['read_only_CPU_s']=time.process_time()-cpu;out['read_only_wall_s']=time.perf_counter()-wall;out['final_writer_and_validation_CPU_wall_charge_s']=.5;out['aggregate_CPU_s']=c['CPU_s']+out['read_only_CPU_s']+.5;out['aggregate_wall_s']=c['wall_s']+out['read_only_wall_s']+.5;out['aggregate_audit_CPU_s']=result['cost']['phases']['audit']['CPU_s']+out['read_only_CPU_s']+.5;out['aggregate_audit_wall_s']=result['cost']['phases']['audit']['wall_s']+out['read_only_wall_s']+.5
        assert out['aggregate_CPU_s']<1800 and out['aggregate_wall_s']<2400 and out['aggregate_audit_CPU_s']<15 and out['aggregate_audit_wall_s']<25
        with (G/'retry/return583_analysis.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
        print(json.dumps(dict(status=out['status'],checks=checks,selector=out['selector'],aggregate_CPU_s=out['aggregate_CPU_s'],aggregate_wall_s=out['aggregate_wall_s']),indent=2))
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
