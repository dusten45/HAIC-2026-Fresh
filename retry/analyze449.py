"""Saved-only +90m boundary metrics, mixed-clock accounting and source audit."""
import json,time
from pathlib import Path
from retry.loss389_analyze import read,save,sha
from retry.analyze446 import state_diagnostics
from retry.root449 import load_root449
from retry.receipt421_io import load_receipt


def run(root):
    cpu=time.process_time();g=Path(__file__).resolve().parents[1];d=root/'stage449';p=read(d/'plan.json');result=read(d/'result.json');budget=result['budget']
    assert result['status']=='MODEL90_COMPARISON_COMPLETED' and result['error'] is None
    for group in ['sources','protected','original408_preserve']:
        for f,h in p[group].items():assert sha(f)==h,f
    assert sha(d/'plan.json')==result['plan_sha256']==(d/'plan.sha256').read_text().strip()
    assert budget['ticks']==budget['reserved_ticks']==96 and budget['worlds']==budget['confirmed_worlds']==6
    assert budget['CPU_s']<60 and budget['execution_wall_s']<120
    streams=[read(f) for f in d.glob('*-observer-private.json')]
    assert len(streams)==6 and sum(len(s['posts']) for s in streams)==96 and all(s['failure'] is None for s in streams)
    fixed=read(Path(p['fixed_plan']));line=fixed['line'];details={};private={};proofs={}
    for arm in ['nominal','fullgas']:
        a=read(d/(arm+'1-private.json'));b=read(d/(arm+'2-private.json'));held=read(d/(arm+'_held-private.json'))
        native=load_root449(root,arm);source=read(d/(arm+'-source-proof-private.json'));branch=result['branches'][arm]
        assert a['rows']==b['rows'] and a['final_state']==b['final_state'] and a['controller_memory']==b['controller_memory']
        assert a['model_ledger']['actual_root_digest']==native['ledger'].digest()
        assert all(held['rows'][0][k]==a['rows'][0][k] for k in ['command','memory_before','memory_after'])
        assert source['global_RNG_verified_against_native_hashes'] and not a['model_ledger']['deadline_missed'] and not a['model_ledger']['done']
        for label in [arm+'1',arm+'2',arm+'_held']:
            observer=read(d/(label+'-observer-private.json'));assert all(action['command']==action['nominal'] for action in observer['actions'])
            proof=load_receipt(d/(label+'_inputs-before-integration-private.json'))
            assert proof['state']==native['state'] and proof['memory']==native['memory'] and proof['ledger']==__import__('dataclasses').asdict(native['ledger'])
        if arm=='nominal':
            assert len(source['source_audits'])==2
            for audit in source['source_audits']:
                assert audit['certified_prefix_actions']==len(a['rows']) and audit['fresh_current_first_pass']>=1
        hit=branch['model_tail_crossing'];lo,hi=hit['rawtick_bracket'];root_clock=native['ledger'].last_clock_tick;points={};lower=None
        for row in a['rows']:
            phase=row['memory_after']['C']['phase']
            for hull in row['raw_hull']:
                tick=round(hull['time']*50)-root_clock
                if tick in [lo,hi]:points[tick]=state_diagnostics(dict(pos=hull['origin_position'],vel=hull['COM_linear_velocity'],angle=hull['angle'],yaw=hull['yaw']),line,phase)
                if tick==lo:
                    k=hull['raw_tick']-1;lower=row['tires'][4*k:4*k+4]
            q=row['predicted'];tick=round(q['time']*50)-root_clock
            if tick in [lo,hi] and tick not in points:points[tick]=state_diagnostics(dict(pos=q['position'],vel=q['velocity'],angle=q['angle'],yaw=q['angular_velocity']),line,phase)
        assert set(points)=={lo,hi} and lower is not None
        body={key:[min(x[key] for x in points.values()),max(x[key] for x in points.values())] for key in next(iter(points.values()))}
        wheel={key:[min(x[key] for x in lower),max(x[key] for x in lower)] for key in ['joint_angle','omega','force_ratio','lateral_slip_m_s','longitudinal_slip_m_s']}
        cumulative=[(native['native_prefix_ticks']+tick)/50 for tick in hit['rawtick_bracket']]
        assert cumulative==branch['cumulative_from_original_root_s']
        old=read(g/'retry/transfer448_result.json');si=next(a for a in old['actual'] if a['arm']==arm)['crossing_from_original_root']['elapsed_bracket_s']
        details[arm]=dict(body_exit_bracket_sample_ranges=body,lower_crossing_preclip_tire_ranges=wheel,sample_ranges_not_continuous_time_bounds=True,elapsed60_to90_conservative_s=[cumulative[0]-si[1],cumulative[1]-si[0]])
        private[arm]=dict(body_points=points,lower_preclip=lower)
        proofs[arm]=dict(own_native_root_state_memory_ledger_RNG=True,independent_repeats_exact=True,held_first_passed=True,own_nominal_only=True,baseline_factual_source_rows=len(a['rows']) if arm=='nominal' else 0,baseline_fresh_current_first_pass=source['source_audits'][0]['fresh_current_first_pass'] if arm=='nominal' else None)
    old_gain=read(g/'retry/transfer448_result.json')['gain60_bracket_s'];gain=result['gain90_bracket_s'];change=[gain[0]-old_gain[1],gain[1]-old_gain[0]]
    save(d/'exit-samples-private.json',private)
    checks=dict(source_and_protected_hashes_preserved=True,observer_posts=96,streams=6,same_actual_wrapper_end_states=True,actual_native_calls=0,new_seed=0,baseline_before_candidate=True,source_qualification_not_new_native_future_for_candidate=True,saved_CPU_s=time.process_time()-cpu)
    save(d/'closure-checks-private.json',checks)
    public={k:v for k,v in result.items() if k not in ['budget','plan_sha256']}
    public.update(details=details,verification=proofs,closure_checks=checks,
        comparison_to60=dict(native60_gain_bracket_s=old_gain,mixed_native_model90_gain_bracket_s=gain,conservative_gain_change_s=change,increase_established=False,no_gain_addition=True),
        cost=dict(model_ticks=96,model_worlds=6,model_CPU_s=budget['CPU_s'],model_wall_s=budget['execution_wall_s'],static=read(d/'static-result.json'),saved_audit_CPU_s=checks['saved_CPU_s'],old_native_prefix_recharged=False,full_project_overhead_measured=False),
        terminal_debt_resolved=False,hidden_native_solver_warmstart_preserved=False,native90_transfer_or_wholelap_pixel_generalization_promoted=False,deadline_utc=p['deadline_utc'])
    save(g/'retry/continuation449_result.json',public)
    print(json.dumps(dict(status=result['status'],gain90=gain,change=change,details=details,proofs=proofs,cost=public['cost'])))

if __name__=='__main__':run(Path(__import__('sys').argv[1]))
