"""Saved-only460 closure: observer/cost and own model finish audit, no integration."""
import collections,datetime,json,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.executor397 import canonical_projection

def run(root):
    cpu=time.process_time();wall=time.perf_counter();d=root/'stage460';g=Path(__file__).resolve().parents[1];p=read(d/'plan.json');result=read(d/'result.json');budget=result['budget'];closed=read(d/'progress-private.json')
    assert closed['phase']=='CLOSED' and sha(d/'plan.json')==result['plan_sha256']
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    assert 0<=budget['ticks']<=budget['reserved_ticks']<=327680 and budget['worlds']<=1792
    streams=[read(f) for f in d.glob('*-observer-private.json')]
    posts=sum(len(s['posts']) for s in streams);assert posts==budget['ticks'];assert len(streams)==budget['confirmed_worlds']
    decisions=read(d/'decisions-private.json') if(d/'decisions-private.json').exists() else []
    details={};fixed=read(Path(p['fixed_plan']));line=fixed['line'];L=sum(fixed['free_profile']['ds']);native_rows=[json.loads(x) for x in (root/'stage453/actual_candidate/trace-private.jsonl').read_text().splitlines()];origin=native_rows[22]['progress_before'];crossings={}
    for arm in p['order']:
        path=d/('parent_'+arm+'-private.json')
        if not path.exists():continue
        parent=read(path);qs=[x for x in decisions if x['arm']==arm];rows=parent['rows'];finished=parent['status']=='FINISHED';finish=None
        ownstream=next(s for s in streams if s['link']['label']=='parent_'+arm);initial=ownstream['link']['model_ledger'];progress=initial['progress_m'];first=rows[0]['raw_hull'][0] if rows else None;crossings[arm]={}
        if first:
            arc=canonical_projection(line,first['origin_position'],first['COM_linear_velocity'],'FIRST_LAP')['arc'];previous_tick=0
            for post in ownstream['posts']:
                current=canonical_projection(line,post['position'],post['velocity'],post['phase'])['arc'];after=progress+(current-arc+L/2)%L-L/2;tick=post['raw_clock']-initial['last_clock_tick']
                for boundary in [510,570,630,690,750]:
                    if boundary not in crossings[arm] and progress-origin<boundary<=after-origin:crossings[arm][boundary]=[previous_tick/50,tick/50]
                progress=after;arc=current;previous_tick=tick
        if finished:
            finish=parent['finish_ticks'];assert finish and rows[-1]['predicted']['finished'] and parent['model_ledger']['done']
            tracker=parent['final_state']['finish_tracker'];assert tracker['finish_time_s']==rows[-1]['predicted']['finish_time_s'] and tracker['qualified_time_s'] is not None
        assert len(rows)<=100 and sum(x['planner_used'] for x in qs)<=8 and all(x['first_pass'] for x in qs)
        details[arm]=dict(status=parent['status'],error=parent['error'],observed_parent_actions=len(rows),verified_decisions=len(qs),recipe_counts=dict(collections.Counter(x['recipe'] for x in qs)),planner_recipe_counts=dict(collections.Counter(x['recipe'] for x in qs if x['planner_used'])),guardian_recipe_counts=dict(collections.Counter(x['recipe'] for x in qs if not x['planner_used'])),planner_status_counts=dict(collections.Counter(x['choice']['decision']['status'] for x in qs if x['planner_used'])),planner_decisions=sum(x['planner_used'] for x in qs),pending_queries=sum(x['route']=='REGISTERED_PENDING_GUARDIAN_ONLY' for x in qs),own_pending_confirmations=sum(x['own_pending'] is not None for x in qs),guardian_finish_certificates=sum(x['guardian_certificate'] is not None for x in qs),own_model_finish=finished,finish_ticks=finish,remaining_model_finish_s=None if finish is None else [finish['lo']/50,finish['hi']/50],actual_finish_witness=False)
    completed=result['status']=='FOUR_MODEL_PARENTS_COMPLETED_REPEAT_EXACT'
    if completed:
        assert len(result['policies'])==4 and all(x['official_model_finish'] for x in result['policies'])
        for base in ['NoPulse','Pulse']:
            pair=[x for x in result['policies'] if x['arm'].startswith(base+'-')];assert len(pair)==2 and pair[0]['signature']==pair[1]['signature']
    ledger=read(root/'project-effective-budget-v474.json')
    public=dict(stage=460,status=result['status'],error=result['error'],last_stage=result['last_stage'],closed_at_utc=closed['at_utc'],worker_pid=closed['pid'],policies=result['policies'],details=details,hybrid_total_NoPulse_minus_Pulse_bracket_s=result['hybrid_total_NoPulse_minus_Pulse_bracket_s'],four_full_model_arms_repeat_exact=completed,verification=dict(observer_posts=posts,observer_streams=len(streams),meter_consistent=True,source_protected_preserved=True,static=read(d/'static-result.json'),preflight=read(d/'preflight-private.json') if(d/'preflight-private.json').exists() else None),cost=dict(model_ticks=budget['ticks'],reserved_ticks=budget['reserved_ticks'],worlds=budget['worlds'],whole_modelworker_CPU_s=budget['CPU_s'],whole_modelworker_wall_s=budget['execution_wall_s'],ticks_by_tag=budget['ticks_by_tag'],worlds_by_tag=budget['worlds_by_tag'],whole_project_overhead_fully_measured=False),new_actual_actions=0,new_resets=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,actual_gate_opened=False,actual_finish_witness=False,original456_failure_preserved=True,research_remaining=ledger['research_remaining'],actual_cumulative_wrapper_actions=ledger['actual_cumulative_wrapper_actions'],reserve=ledger['final_reserved_actions'],reserve_used=ledger['final_reserve_used'],deadline_utc=p['deadline_utc'],plan_sha256=result['plan_sha256'])
    public['prefix_observed_elapsed_s']=p['prefix_elapsed_s']
    public['hybrid_total_brackets_s']={arm:[round(p['prefix_elapsed_s'][arm.split('-')[0]]+t,8) for t in z['remaining_model_finish_s']] for arm,z in details.items() if z['remaining_model_finish_s'] is not None}
    public['planned_cost']=p['budget_fixture']
    public['hybrid_is_not_native_lap']=True
    public['planner_alternative_pair_status_counts']=dict(collections.Counter(z['status'] for q in decisions if q['planner_used'] for z in q['choice']['recipes'].values()))
    public['saved_model_crossing_from_root_s']=crossings
    public['crossing_tail_NoPulse_minus_Pulse_bracket_s']={str(b):[crossings['NoPulse-1'][b][0]-crossings['Pulse-1'][b][1],crossings['NoPulse-1'][b][1]-crossings['Pulse-1'][b][0]] for b in [510,570,630,690,750] if 'NoPulse-1' in crossings and 'Pulse-1' in crossings and b in crossings['NoPulse-1'] and b in crossings['Pulse-1']}
    public['saved_audit_CPU_s']=time.process_time()-cpu;public['saved_audit_wall_s']=time.perf_counter()-wall
    save(d/'saved-closure-private.json',public);save(g/'retry/compare460_result.json',public)
    print(json.dumps({k:public[k] for k in ['status','error','details','hybrid_total_NoPulse_minus_Pulse_bracket_s','cost','saved_audit_CPU_s']},ensure_ascii=False))

if __name__=='__main__':run(Path(__import__('sys').argv[1]))
