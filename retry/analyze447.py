"""Saved-only same-live H1 audit; no physics construction or new query."""
import json, math, sys, time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.analyze446 import state_diagnostics


def run(root):
    started=time.process_time();g=Path(__file__).resolve().parents[1];d=root/'stage447'
    p=read(d/'plan.json');result=read(d/'result.json');budget=result['budget']
    assert result['status']=='SAME_LIVE_STUDY_COMPLETED' and result['error'] is None
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    assert sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
    assert budget['ticks']==budget['reserved_ticks']==296 and budget['worlds']==budget['confirmed_worlds']==6
    assert budget['CPU_s']<90 and budget['execution_wall_s']<150
    streams=[read(f) for f in d.glob('*-observer-private.json')]
    assert len(streams)==6 and sum(len(s['posts']) for s in streams)==296
    assert all(s['failure'] is None for s in streams)
    line=read(Path(p['fixed_plan']))['line'];details={};private={};comparisons={}
    for recipe in ['nominal','fullgas']:
        a=read(d/(recipe+'1-private.json'));b=read(d/(recipe+'2-private.json'))
        archive=read(Path(p['archives'][recipe]));old=read(root/f'stage446/{recipe}_extension1-private.json')
        assert a['rows']==b['rows'] and a['final_state']==b['final_state'] and a['controller_memory']==b['controller_memory']
        held=read(d/(recipe+'_held-private.json'))['rows'][0]
        assert all(held[k]==a['rows'][0][k] for k in ['command','memory_before','memory_after'])
        assert a['rows'][:13]==archive['rows'] and a['end13']==archive['end13']
        assert a['model_ledger']['actual_root_digest']==archive['model_ledger']['actual_root_digest']
        assert not a['model_ledger']['done'] and not any(row['safety'] for row in a['rows'])
        for rep in [1,2]:
            observer=read(d/(recipe+str(rep)+'-observer-private.json'))
            assert all(action['command']==action['nominal'] for action in observer['actions'][1:])
            if recipe=='nominal':assert observer['actions'][0]['command']==observer['actions'][0]['nominal']
        rootclock=round(a['rows'][0]['raw_hull'][0]['time']*50)
        hit=result['branches'][recipe]['crossing_from_original_root'];lo,hi=hit['rawtick_bracket'];points={};lower=None
        for row in a['rows']:
            phase=row['memory_after']['C']['phase']
            for hull in row['raw_hull']:
                tick=round(hull['time']*50)-rootclock
                if tick in [lo,hi]:points[tick]=state_diagnostics(dict(pos=hull['origin_position'],vel=hull['COM_linear_velocity'],angle=hull['angle'],yaw=hull['yaw']),line,phase)
                if tick==lo:
                    k=hull['raw_tick']-1;lower=row['tires'][4*k:4*k+4]
            pred=row['predicted'];tick=round(pred['time']*50)-rootclock
            if tick in [lo,hi] and tick not in points:points[tick]=state_diagnostics(dict(pos=pred['position'],vel=pred['velocity'],angle=pred['angle'],yaw=pred['angular_velocity']),line,phase)
        assert set(points)=={lo,hi} and lower is not None
        body={key:[min(v[key] for v in points.values()),max(v[key] for v in points.values())] for key in next(iter(points.values()))}
        tyre={key:[min(v[key] for v in lower),max(v[key] for v in lower)] for key in ['joint_angle','omega','force_ratio','lateral_slip_m_s','longitudinal_slip_m_s']}
        tail=a['rows'][13:];assert len(tail)==len(old['rows'])
        rawdiff=[]
        def diff(x,y,path=''):
            if isinstance(x,dict) and isinstance(y,dict):
                for k in x.keys()|y.keys():
                    if k not in x or k not in y:rawdiff.append(dict(path=path+'/'+k,kind='missing'))
                    else:diff(x[k],y[k],path+'/'+k)
            elif isinstance(x,list) and isinstance(y,list) and len(x)==len(y):
                for i,(u,v) in enumerate(zip(x,y)):diff(u,v,path+'/'+str(i))
            elif x!=y:rawdiff.append(dict(path=path,absolute_delta=abs(x-y) if isinstance(x,(int,float)) and isinstance(y,(int,float)) else None))
        diff(a['final_state'],old['final_state'])
        metrics={key:max(fn(x['predicted'],y['predicted']) for x,y in zip(tail,old['rows'])) for key,fn in {
            'position_m':lambda x,y:math.dist(x['position'],y['position']),
            'speed_m_s':lambda x,y:abs(x['speed_m_s']-y['speed_m_s']),
            'yaw_rad_s':lambda x,y:abs(x['angular_velocity']-y['angular_velocity']),
            'time_s':lambda x,y:abs(x['time']-y['time'])}.items()}
        discrete=['collision','damage','wheel_road_contacts','raw_ticks','finished','terminated','truncated']
        comparisons[recipe]=dict(archival_tail_rows_exact=tail==old['rows'],archival_final_state_exact=a['final_state']==old['final_state'],final_state_different_scalar_fields=len(rawdiff),
            maximum_wrapper_endpoint_absolute_differences=metrics,
            endpoint_discrete_exact=all(x['predicted'][k]==y['predicted'][k] for x,y in zip(tail,old['rows']) for k in discrete),
            same_crossing_bracket_as446=hit['elapsed_bracket_s']==read(g/'retry/extension446_result.json')['branches'][recipe]['cumulative_from_original_root_s'],
            no_posthoc_tolerance_or_equivalence_claim=True)
        private[recipe]=dict(body_points=points,lower_preclip_tires=lower,archival_final_state_differences=rawdiff)
        details[recipe]=dict(body_exit_bracket_sample_ranges=body,lower_crossing_preclip_tire_ranges=tyre,sample_ranges_not_continuous_time_bounds=True)
    save(d/'comparison-and-exit-private.json',private)
    checks=dict(source_and_protected_preserved=True,historical_H13_exact=True,same_child_world_stream_across_H13=True,
        independent_repeats_exact=True,held_first_passed=True,baseline_source_gates_before_candidate=len(result['source_gates'])==2,
        observer_posts=296,streams=6,new_actual_native_authority=False,saved_CPU_s=time.process_time()-started)
    save(d/'closure-checks-private.json',checks)
    public={k:v for k,v in result.items() if k not in ['budget','source_gates','plan_sha256']}
    public.update(details=details,comparison_to446=comparisons,verification=checks,
        cost=dict(model_ticks=296,model_worlds=6,model_CPU_s=budget['CPU_s'],model_wall_s=budget['execution_wall_s'],static=read(d/'static-result.json'),saved_audit_CPU_s=checks['saved_CPU_s'],full_project_overhead_measured=False),
        terminal_debt_resolved=False,promotion_to_actual_or_pixel=False,no_gain_addition=True,deadline_utc=p['deadline_utc'])
    save(g/'retry/continuation447_result.json',public)
    print(json.dumps(dict(status=result['status'],comparison=comparisons,checks=checks)))

if __name__=='__main__':run(Path(sys.argv[1]))
