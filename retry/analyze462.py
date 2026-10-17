"""Closed462 saved audit; raw-post crossings, path/force/intervention, no integration."""
import collections,json,math,time,sys
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.executor397 import canonical_projection

def run(root):
    cpu,wall=time.process_time(),time.perf_counter();d=root/'stage462';g=Path(__file__).resolve().parents[1];p=read(d/'plan.json');result=read(d/'result.json');budget=result['budget'];closed=read(d/'progress-private.json')
    assert closed['phase']=='CLOSED' and sha(d/'plan.json')==result['plan_sha256']
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    assert 0<=budget['ticks']<=budget['reserved_ticks']<=p['caps']['ticks'] and budget['worlds']<=p['caps']['worlds']
    streams=[read(f) for f in d.glob('*-observer-private.json')];posts=sum(len(s['posts']) for s in streams);assert posts==budget['ticks'] and len(streams)==budget['confirmed_worlds']
    decisions=read(d/'decisions-private.json') if(d/'decisions-private.json').exists() else []
    fixed=read(p['fixed_plan']);pace=read(p['pace_path'])['frozen268'];nodes=[v*m for v,m in zip(fixed['free_profile']['speed'],pace)];line=fixed['line'];L=sum(fixed['free_profile']['ds']);native=[json.loads(x) for x in (root/'stage458/actual_P/trace-private.jsonl').read_text().splitlines()];origin=native[22]['progress_before'];details={};crossings={}
    for arm in p['order']:
        path=d/('parent_'+arm+'-private.json')
        if not path.exists():continue
        parent=read(path);qs=[x for x in decisions if x['arm']==arm];rows=parent['rows'];finished=parent['status']=='FINISHED';finish=parent['finish_ticks'] if finished else None
        stream=next(s for s in streams if s['link']['label']=='parent_'+arm);initial=stream['link']['model_ledger'];progress=initial['progress_m'];previous_tick=0;crossings[arm]={}
        if rows:
            h=rows[0]['raw_hull'][0];arc=canonical_projection(line,h['origin_position'],h['COM_linear_velocity'],'FIRST_LAP')['arc']
            for post in stream['posts']:
                current=canonical_projection(line,post['position'],post['velocity'],post['phase'])['arc'];after=progress+(current-arc+L/2)%L-L/2;tick=post['raw_clock']-initial['last_clock_tick']
                for boundary in [570,630,690,750]:
                    if boundary not in crossings[arm] and progress-origin<boundary<=after-origin:crossings[arm][boundary]=[previous_tick/50,tick/50]
                progress,arc,previous_tick=after,current,tick
        if finished:
            assert finish and rows[-1]['predicted']['finished'] and parent['model_ledger']['done'];tracker=parent['final_state']['finish_tracker'];assert tracker['finish_time_s']==rows[-1]['predicted']['finish_time_s'] and tracker['qualified_time_s'] is not None
        assert len(rows)<=p['execution']['parent_cap'] and sum(x['fixed_first'] for x in qs)<=1 and all(x['first_pass'] for x in qs)
        def metrics(frames):
            tires=[t for f in frames for t in f['tires']];ticks=sum(f['predicted']['raw_ticks'] for f in frames)
            return dict(observed_raw_ticks=ticks,max_path_error_m=max((f['path_error_m'] for f in frames),default=None),clipped_wheel_samples=sum(bool(t['clipped']) for t in tires),clipped_raw_ticks=sum(len(set(t['raw_tick'] for t in f['tires'] if t['clipped'])) for f in frames),grass_wheel_samples=sum(bool(t['grass']) for t in tires),max_force_ratio=max((t['force_ratio'] for t in tires),default=None),mean_abs_tire_lateral_slip_m_s=sum(abs(t['lateral_slip_m_s']) for t in tires)/len(tires) if tires else None)
        response={}
        if rows:
            v0=math.hypot(*rows[0]['raw_hull'][0]['COM_linear_velocity'])
            for index,name in [(0,'first80ms'),(min(12,len(rows)-1),'first13actions')]:
                f=rows[index];velocity=f['predicted']['velocity'];projection=canonical_projection(line,f['predicted']['position'],velocity,'FIRST_LAP');j,u=projection['index'],projection['u'];r=math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2)
                response[name]=dict(speed_change_m_s=math.hypot(*velocity)-v0,endpoint_speed_minus_reference_m_s=math.hypot(*velocity)-r,**metrics(rows[:index+1]))
        details[arm]=dict(status=parent['status'],error=parent['error'],observed_parent_actions=len(rows),verified_decisions=len(qs),recipe_counts=dict(collections.Counter(x['recipe'] for x in qs)),fixed_first_recipe=next((x['recipe'] for x in qs if x['fixed_first']),None),guardian_recipe_counts=dict(collections.Counter(x['recipe'] for x in qs if not x['fixed_first'])),pending_queries=sum(x['route']=='REGISTERED_PENDING_GUARDIAN_ONLY' for x in qs),own_pending_confirmations=sum(x['own_pending'] is not None for x in qs),guardian_finish_certificates=sum(x['guardian_certificate'] is not None for x in qs),own_model_finish=finished,finish_ticks=finish,remaining_model_finish_s=None if finish is None else [finish['lo']/50,finish['hi']/50],observed_parent=metrics(rows),response=response,whole_arm_repeated=False,actual_finish_witness=False)
    completed=result['status']=='TWO_MODEL_PARENTS_COMPLETED_NO_ARM_REPEAT'
    if completed:assert len(result['policies'])==2 and all(x['official_model_finish'] for x in result['policies'])
    ledger=read(root/'project-effective-budget-v474.json')
    public=dict(stage=462,status=result['status'],error=result['error'],last_stage=result['last_stage'],closed_at_utc=closed['at_utc'],worker_pid=closed['pid'],policies=result['policies'],details=details,model_tail_Original_minus_SecantOnce_bracket_s=result['model_tail_Original_minus_SecantOnce_bracket_s'],whole_arm_repeated=False,independent_query_copies=2,verification=dict(observer_posts=posts,observer_streams=len(streams),meter_consistent=True,source_protected_preserved=True,static=read(d/'static-result.json'),preflight=read(d/'preflight-private.json') if(d/'preflight-private.json').exists() else None),cost=dict(model_ticks=budget['ticks'],reserved_ticks=budget['reserved_ticks'],worlds=budget['worlds'],whole_modelworker_CPU_s=budget['CPU_s'],whole_modelworker_wall_s=budget['execution_wall_s'],ticks_by_tag=budget['ticks_by_tag'],worlds_by_tag=budget['worlds_by_tag'],whole_project_overhead_fully_measured=False),new_actual_actions=0,new_resets=0,new_seed_learning_HOLDOUT_SEALED_reserve_paid=0,actual_gate_opened=False,actual_finish_witness=False,research_remaining=ledger['research_remaining'],actual_cumulative_wrapper_actions=ledger['actual_cumulative_wrapper_actions'],reserve=ledger['final_reserved_actions'],reserve_used=ledger['final_reserve_used'],deadline_utc=p['deadline_utc'],plan_sha256=result['plan_sha256'],observed_prefix_elapsed_s=10.0,planned_cost=p['budget_fixture'],saved_model_crossing_from_root_s=crossings)
    public['crossing_model_gain_bracket_s']={str(b):[crossings['Original'][b][0]-crossings['SecantOnce'][b][1],crossings['Original'][b][1]-crossings['SecantOnce'][b][0]] for b in [570,630,690,750] if all(arm in crossings and b in crossings[arm] for arm in ['Original','SecantOnce'])}
    public['saved_audit_CPU_s']=time.process_time()-cpu;public['saved_audit_wall_s']=time.perf_counter()-wall;save(d/'saved-closure-private.json',public);save(g/'retry/compare462_result.json',public)
    print(json.dumps({k:public[k] for k in ['status','error','details','model_tail_Original_minus_SecantOnce_bracket_s','cost','saved_audit_CPU_s']},ensure_ascii=False))

if __name__=='__main__':run(Path(sys.argv[1]))
