"""Read-only closeout of stored579; no physical/source imports or evaluations."""
import json,time,signal,hashlib
from pathlib import Path
from collections import Counter
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response579-private')
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    cpu,wall=time.process_time(),time.perf_counter()
    def cap(*a):raise RuntimeError('579_READ_ONLY_AUDIT_CAP')
    signal.signal(signal.SIGPROF,cap);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_PROF,5);signal.setitimer(signal.ITIMER_REAL,8)
    try:
        result=read(G/'retry/beam579_result.json');contract=read(G/'retry/beam579_contract.json');stored=read(D/'A-terminals-private.json');terminals=stored['terminals'];counts=Counter();pruning=Counter();safe=Counter();external_attempts=0;depths=[];head='0'*64;events=0
        for line in (D/'raw-journal-private.jsonl').open():
            row=json.loads(line);actual=row.pop('sha256');expected=hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest();assert actual==expected and row['sequence']==events and row['previous']==head;head=actual;events+=1;kind=row['kind'];counts[kind]+=1
            if kind=='BEFORE_FORCE' and row['context']['bucket']=='search' and row['context']['raw']==1:external_attempts+=1
            if kind=='FORCE_VERDICT' and row['gate']:pruning[row['gate']]+=1
            if kind=='RAW_VERDICT':
                if row['failures']:pruning[row['failures'][0]]+=1
                else:safe['raw']+=1
            if kind=='BEAM_DEPTH':depths.append({k:row[k] for k in ['stage','depth','live','terminals','factual_frozen']})
        A=contract['gates']['A'];plane=contract['gates']['planes'][0];timepass=lambda h:A['baseline_before_raw']-h['after_raw']>=A['minimum_raw_gain'];speedpass=lambda h:h['COM_speed_m_s']>=A['minimum_interpolated_COM_speed_m_s'];hits=[n['crossing'] for n in terminals]
        bracket_counts=Counter((h['before_raw'],h['after_raw']) for h in hits)
        gains=[plane['linear_interpolated_s']-(h['before_s']+h['fraction']*(h['after_s']-h['before_s'])) for h in hits]
        counts_actual=result['cost']['total'];checks={'journal_chain_valid':True,'journal_head_exact':head==result['journal']['head'],'external_actual_calls_equal4force_verdicts':counts_actual['external_force']==4*counts['FORCE_VERDICT'],'internal_actual_calls_equal4completed_ticks':counts_actual['internal_force']==4*counts_actual['completed_model_ticks'],'attempts_equal_before_force_events':counts_actual['attempted_raw']==counts['BEFORE_FORCE'],'completed_ticks_equal_after_tick_events':counts_actual['completed_model_ticks']==counts['AFTER_TICK'],'source_pruning_matches_runtime':all(result['A']['pruning'].get(k,0)==v for k,v in pruning.items()),'terminals_saved_before_live_empty':len(terminals)==52 and depths[-1]['live']==0 and depths[-1]['factual_frozen'],'all_terminal_holds_complete':all(n['checkpoint']['global_raw']%4==0 and n['checkpoint']['global_raw']>=n['crossing']['after_raw'] for n in terminals),'A_no_time_pass':not any(timepass(h) for h in hits),'no_B_or_replay':result.get('B') is None and result['independent_replay'] is None,'contract_untouched':read(D/'STARTED.json')['contract_sha256']==sha(G/'retry/beam579_contract.json')}
        assert all(checks.values()),checks
        out={'status':result['status'],'checks':checks,'evaluated_search_children':external_attempts,'source_pruning':dict(pruning),'beam_width_pruned':result['A']['pruning']['BEAM_WIDTH'],'terminal_gate_rejections':result['A']['pruning']['TERMINAL_GATE'],'terminal_count':len(terminals),'completed_depths':len(depths),'terminal_raw_brackets':[{'before_raw':k[0],'after_raw':k[1],'count':v} for k,v in sorted(bracket_counts.items())],'terminal_speed_m_s':{'min':min(h['COM_speed_m_s'] for h in hits),'max':max(h['COM_speed_m_s'] for h in hits)},'terminal_gate_counts':{'time_pass':sum(timepass(h) for h in hits),'speed_pass':sum(speedpass(h) for h in hits),'eligible':sum(h['eligible'] for h in hits),'both_pass':sum(timepass(h) and speedpass(h) and h['eligible'] for h in hits)},'baseline_plane_interpolated_s':plane['linear_interpolated_s'],'diagnostic_continuous_gain_s':{'min':min(gains),'max':max(gains),'not_acceptance_metric':True},'B':{'executed':False,'reason':'A gate failed; no continuation or alternative experiment'},'replay':{'executed':False,'reason':'No passing selected A/B plan'},'runtime_cost':result['cost'],'new_source_ticks':0,'new_force_calls':0,'new_native_actions':0,'HOLDOUT':0,'SEALED':0,'input_sha256':{str(p.relative_to(G)) if p.is_relative_to(G) else p.name:sha(p) for p in [G/'retry/beam579_result.json',G/'retry/beam579_contract.json',D/'A-terminals-private.json',D/'raw-journal-private.jsonl']}}
        elapsed_cpu=time.process_time()-cpu;elapsed_wall=time.perf_counter()-wall;out['read_only_analysis_CPU_s']=elapsed_cpu;out['read_only_analysis_wall_s']=elapsed_wall;out['final_writer_and_validation_conservative_CPU_wall_charge_s']=1.;out['aggregate_CPU_s']=result['cost']['total']['CPU_s']+elapsed_cpu+1.;out['aggregate_wall_s']=result['cost']['total']['wall_s']+elapsed_wall+1.;out['aggregate_audit_CPU_s']=result['cost']['phases']['audit']['CPU_s']+elapsed_cpu+1.;out['aggregate_audit_wall_s']=result['cost']['phases']['audit']['wall_s']+elapsed_wall+1.
        assert out['aggregate_audit_CPU_s']<10 and out['aggregate_audit_wall_s']<15 and out['aggregate_CPU_s']<400 and out['aggregate_wall_s']<540
        target=G/'retry/beam579_analysis.json'
        with target.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
        print(json.dumps({k:out[k] for k in ['status','evaluated_search_children','terminal_raw_brackets','terminal_speed_m_s','terminal_gate_counts','diagnostic_continuous_gain_s','aggregate_CPU_s','aggregate_wall_s','checks']},indent=2))
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
