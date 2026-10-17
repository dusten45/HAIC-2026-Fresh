"""Saved-only long-continuation timing, common-braking tyre and actuator audit."""
import json,time,math
from pathlib import Path
from dataclasses import asdict
import numpy as np
from retry.loss389_analyze import read,save,sha
from retry.root449 import load_root449
from retry.analyze446 import state_diagnostics
from retry.receipt421_io import load_receipt
from retry.boundary434 import decode
from retry.pilot420_backend import fingerprint
from retry.executor397 import canonical_projection


def braking_window(rows,native,line,L):
    # A saved-analysis window containing factual first brake192.3..239.1m;
    # grouping only, not a new safety/promotion tolerance.
    s=native['ledger'].progress_m;origin=native['original']['progress_m'];prev=None;tires=[];commands=[];indices=set();speeds=[]
    for row in rows:
        phase=row['memory_after']['C']['phase']
        for h in row['raw_hull']:
            arc=canonical_projection(line,h['origin_position'],h['COM_linear_velocity'],phase)['arc']
            if prev is not None:s+=(arc-prev+L/2)%L-L/2
            prev=arc
            if 190<=s-origin<250:
                k=h['raw_tick']-1;tires.extend(row['tires'][4*k:4*k+4]);commands.append(row['command']);indices.add(row['offset']);speeds.append(math.hypot(*h['COM_linear_velocity']))
        q=row['predicted'];arc=canonical_projection(line,q['position'],q['velocity'],phase)['arc'];s+=(arc-prev+L/2)%L-L/2;prev=arc
    assert tires and len(tires)==4*len(commands)
    keys=['gas','brake','joint_angle','omega','force_ratio','lateral_slip_m_s','longitudinal_slip_m_s']
    return dict(common_original_root_arc_window_m=[190,250],phase='raw_preclip',raw_boundaries=len(commands),wrappers_touching_window=len(indices),wheel_samples=len(tires),clipped_wheel_samples=sum(t['clipped'] for t in tires),clipped_fraction=sum(t['clipped'] for t in tires)/len(tires),ranges={k:[min(t[k] for t in tires),max(t[k] for t in tires)] for k in keys},speed_sample_range_m_s=[min(speeds),max(speeds)],commanded_braking_raw_boundaries=sum(c[2]>0 for c in commands),commanded_fullgas_raw_boundaries=sum(c[1]==1 and c[2]==0 for c in commands),commanded_coast_raw_boundaries=sum(c[1]==0 and c[2]==0 for c in commands))


def run(root):
    cpu=time.process_time();g=Path(__file__).resolve().parents[1];d=root/'stage450';p=read(d/'plan.json');result=read(d/'result.json');b=result['budget']
    assert result['status']=='MODEL270_COMPARISON_COMPLETED' and result['error'] is None
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    assert sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
    assert b['ticks']==b['reserved_ticks']==568 and b['worlds']==b['confirmed_worlds']==6
    assert b['CPU_s']<90 and b['execution_wall_s']<150
    streams=[read(f) for f in d.glob('*-observer-private.json')]
    assert len(streams)==6 and sum(len(s['posts']) for s in streams)==568 and all(s['failure'] is None for s in streams)
    fixed=read(Path(p['fixed_plan']));line=fixed['line'];L=sum(fixed['free_profile']['ds']);details={};proofs={};private={}
    for arm in ['nominal','fullgas']:
        a=read(d/(arm+'1-private.json'));repeat=read(d/(arm+'2-private.json'));held=read(d/(arm+'_held-private.json'));native=load_root449(root,arm)
        source=read(d/(arm+'-source-proof-private.json'));branch=result['branches'][arm]
        assert a['rows']==repeat['rows'] and a['final_state']==repeat['final_state'] and a['controller_memory']==repeat['controller_memory']
        assert a['model_ledger']['actual_root_digest']==native['ledger'].digest() and not a['model_ledger']['deadline_missed'] and not a['model_ledger']['done']
        assert all(held['rows'][0][k]==a['rows'][0][k] for k in ['command','memory_before','memory_after'])
        assert all(not row['safety'] for row in a['rows']) and len(a['rows'])<=64
        for label in [arm+'1',arm+'2',arm+'_held']:
            observer=read(d/(label+'-observer-private.json'));assert all(action['command']==action['nominal'] for action in observer['actions'])
            inputs=load_receipt(d/(label+'_inputs-before-integration-private.json'));assert inputs['state']==native['state'] and inputs['memory']==native['memory'] and inputs['ledger']==asdict(native['ledger'])
        for rep in [1,2]:
            label=arm+str(rep);proof=load_receipt(d/(label+'-same-live-tail-private.json'));observer=read(d/(label+'-observer-private.json'))
            assert proof['H13_key']==proof['tail']['boundary_key']==observer['boundary_key']
            assert proof['child_id']==proof['tail']['child_id']==observer['link']['child_id']
            assert proof['prefix_digest']==fingerprint(a['rows'][:13])
            assert len(decode(proof['tail']['posts_bytes']))==4*(len(a['rows'])-13)
            assert len(decode(proof['tail']['actions_bytes']))==len(a['rows'])-13
            assert proof['tail']['policy']=='SIGNED_C_NOMINAL' and proof['tail']['outcome']=='ACTIVE'
        if arm=='nominal':
            for audit in source['source_audits']:
                assert audit['initial13']['certified_prefix_actions']==13
                assert audit['finite_continuation']['certified_prefix_actions']==len(a['rows'])
                assert audit['initial13']['fresh_current_first_pass']>=1
        old=read(root/'stage449'/(arm+'1-private.json'));prefix_exact=a['rows'][:len(old['rows'])]==old['rows'];assert prefix_exact
        hit=branch['model_tail_crossing'];lo,hi=hit['rawtick_bracket'];clock=native['ledger'].last_clock_tick;points={};lower=None
        for row in a['rows']:
            phase=row['memory_after']['C']['phase']
            for h in row['raw_hull']:
                tick=round(h['time']*50)-clock
                if tick in [lo,hi]:points[tick]=state_diagnostics(dict(pos=h['origin_position'],vel=h['COM_linear_velocity'],angle=h['angle'],yaw=h['yaw']),line,phase)
                if tick==lo:
                    k=h['raw_tick']-1;lower=row['tires'][4*k:4*k+4]
            q=row['predicted'];tick=round(q['time']*50)-clock
            if tick in [lo,hi] and tick not in points:points[tick]=state_diagnostics(dict(pos=q['position'],vel=q['velocity'],angle=q['angle'],yaw=q['angular_velocity']),line,phase)
        assert set(points)=={lo,hi} and lower is not None
        body={k:[min(x[k] for x in points.values()),max(x[k] for x in points.values())] for k in next(iter(points.values()))}
        wheel={k:[min(t[k] for t in lower),max(t[k] for t in lower)] for k in ['gas','brake','joint_angle','omega','force_ratio','lateral_slip_m_s','longitudinal_slip_m_s']}
        assert [(native['native_prefix_ticks']+tick)/50 for tick in hit['rawtick_bracket']]==branch['cumulative_from_original_root_s']
        details[arm]=dict(body_exit_bracket_sample_ranges=body,lower_crossing_preclip_tire_ranges=wheel,first_braking_window=braking_window(a['rows'],native,line,L),sample_ranges_not_continuous_time_bounds=True)
        private[arm]=dict(body_points=points,lower_preclip=lower)
        proofs[arm]=dict(native_root_state_memory_ledger_RNG_preserved=True,own_nominal_only=True,independent_repeat_exact=True,held_first_passed=True,same_live_H13_continuation=True,short449_prefix_exact=prefix_exact,initial_source_rows=13 if arm=='nominal' else 0,full_factual_source_rows=len(a['rows']) if arm=='nominal' else 0,new_candidate_native_future_qualified=False)
    save(d/'exit-and-braking-samples-private.json',private)
    gain=result['gain270_bracket_s'];old90=read(g/'retry/continuation449_result.json')['gain90_bracket_s'];old60=read(g/'retry/transfer448_result.json')['gain60_bracket_s']
    checks=dict(source_and_protected_preserved=True,observer_posts=568,streams=6,baseline_source_before_candidate=True,actual_actions_resets=0,saved_CPU_s=time.process_time()-cpu)
    save(d/'closure-checks-private.json',checks)
    public={k:v for k,v in result.items() if k not in ['budget','plan_sha256']}
    public.update(details=details,verification=proofs,closure_checks=checks,
        comparison=dict(native60_gain_s=old60,mixed90_gain_s=old90,mixed270_gain_s=gain,conservative_change_from90_s=[gain[0]-old90[1],gain[1]-old90[0]],conservative_change_from60_s=[gain[0]-old60[1],gain[1]-old60[0]],no_gain_addition=True),
        cost=dict(model_ticks=568,model_worlds=6,model_CPU_s=b['CPU_s'],model_wall_s=b['execution_wall_s'],static=read(d/'static-result.json'),saved_audit_CPU_s=checks['saved_CPU_s'],old_model_or_native_prefix_recharged=False,full_project_overhead_measured=False),
        single_hypothesis_only=True,all_branch_terminal_states_equal_required=False,terminal_debt_resolved=False,hidden_native_solver_warmstart_preserved=False,native270_or_wholelap_pixel_generalization_promoted=False,deadline_utc=p['deadline_utc'])
    save(g/'retry/continuation450_result.json',public)
    print(json.dumps(dict(status=result['status'],gain270=gain,details=details,cost=public['cost'])))

if __name__=='__main__':run(Path(__import__('sys').argv[1]))
