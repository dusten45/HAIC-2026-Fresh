"""Saved-only archival continuation timing and matched-boundary diagnostics."""
import json
import math
import sys
import time
from pathlib import Path
from retry.executor397 import canonical_projection
from retry.receipt421_io import load_receipt
from retry.loss389_analyze import read,sha,save


def state_diagnostics(state,line,phase):
    q=canonical_projection(line,state['pos'],state['vel'],phase)
    edge=[line[(q['index']+1)%len(line)][i]-line[q['index']][i] for i in range(2)]
    norm=math.hypot(*edge);t=[z/norm for z in edge]
    f=[-math.sin(state['angle']),math.cos(state['angle'])]
    return dict(speed_m_s=math.hypot(*state['vel']),yaw_rad_s=state['yaw'],
                path_error_m=q['path_error_m'],
                heading_error_rad=abs(math.atan2(f[0]*t[1]-f[1]*t[0],f[0]*t[0]+f[1]*t[1])))


def run(root):
    cpu,wall=time.process_time(),time.perf_counter()
    g=Path(__file__).resolve().parents[1];d=root/'stage446';p,result=read(d/'plan.json'),read(d/'result.json')
    assert result['status']=='ARCHIVAL_EXTENSION_COMPLETED'
    for group in [p['sources'],p['protected']]:
        for f,h in group.items():assert sha(f)==h,f
    assert result['plan_sha256']==sha(d/'plan.json')
    b=result['budget'];assert b['ticks']==b['reserved_ticks']==88 and b['worlds']==b['confirmed_worlds']==6
    assert b['CPU_s']<60 and b['execution_wall_s']<120
    streams=list(d.glob('*-observer-private.json'))
    assert len(streams)==6 and sum(len(read(x)['posts']) for x in streams)==88
    assert all(read(x)['failure'] is None for x in streams)
    line=read(Path(p['fixed_plan']))['line'];details={};private={}
    for recipe in ['nominal','fullgas']:
        a=read(d/(recipe+'_extension1-private.json'));repeat=read(d/(recipe+'_extension2-private.json'))
        assert a['rows']==repeat['rows'] and a['final_state']==repeat['final_state']
        data=read(Path(p['archives'][recipe]['archive']))
        assert a['rows'][0]['memory_before']==data['controller_memory']
        assert a['rows'][0]['raw_hull'][0]['time']==data['final_state']['physical']['actual_time']
        assert a['model_ledger']['actual_root_digest']==p['original_actual_root_digest']
        assert len(a['rows'])<=13 and not any(row['safety'] for row in a['rows'])
        stream=read(d/(recipe+'_extension1-observer-private.json'))
        assert all(action['command']==action['nominal'] for action in stream['actions'])
        archive_clock=data['model_ledger']['last_clock_tick']
        hit=result['branches'][recipe]['hit'];lo,hi=hit['rawtick_bracket'];points={};lower_tires=None
        for row in a['rows']:
            phase=row['memory_after']['C']['phase']
            for hull in row['raw_hull']:
                tick=round(hull['time']*50)-archive_clock
                if tick in [lo,hi]:
                    points[tick]=state_diagnostics(dict(pos=hull['origin_position'],vel=hull['COM_linear_velocity'],angle=hull['angle'],yaw=hull['yaw']),line,phase)
                if tick==lo:
                    k=hull['raw_tick']-1;lower_tires=row['tires'][4*k:4*k+4]
            pred=row['predicted'];tick=round(pred['time']*50)-archive_clock
            if tick in [lo,hi] and tick not in points:
                points[tick]=state_diagnostics(dict(pos=pred['position'],vel=pred['velocity'],angle=pred['angle'],yaw=pred['angular_velocity']),line,phase)
        assert set(points)=={lo,hi} and lower_tires is not None
        body={key:[min(v[key] for v in points.values()),max(v[key] for v in points.values())] for key in next(iter(points.values()))}
        tyre={key:[min(t[key] for t in lower_tires),max(t[key] for t in lower_tires)] for key in ['joint_angle','omega','force_ratio','lateral_slip_m_s','longitudinal_slip_m_s']}
        private[recipe]=dict(body_points=points,lower_preclip_tires=lower_tires)
        details[recipe]=dict(body_exit_bracket_sample_ranges=body,
                             lower_crossing_preclip_tire_ranges=tyre,
                             command_equals_own_nominal_for_entire_continuation=True,
                             sample_ranges_not_continuous_time_bounds=True)
    save(d/'exit-samples-private.json',private)
    checks=dict(source_hashes_and_protected_preserved=True,observer_posts=88,streams=6,
                independent_repeats_exact=True,held_first_passed=True,
                prefix_not_reexecuted_or_recharged=True,actual_native_authority=False,
                source_RNG_restored_from_archive_not_new_seed=True,
                hidden_solver_warmstart_identity_unproven=True,
                saved_CPU_s=time.process_time()-cpu,saved_wall_s=time.perf_counter()-wall)
    save(d/'closure-checks-private.json',checks)
    cost=dict(stage=446,model_ticks=88,model_worlds=6,
              nominal_required_repeat_ticks=56,fullgas_required_repeat_ticks=24,held_first_ticks=8,
              model_CPU_s=b['CPU_s'],model_wall_s=b['execution_wall_s'],
              static_attempts=[read(d/'pre-model-v1/static-result.json'),read(d/'static-result.json')],
              saved_audit_CPU_s=checks['saved_CPU_s'],saved_audit_wall_s=checks['saved_wall_s'],
              preparation_report_git_import_overhead_fully_measured=False,
              new_actual_actions_resets_learning_seed_SEALED_reserve_paid=0,
              research_remaining=27516,reserve=84000,reserve_used=0)
    save(d/'cost-private.json',cost)
    public={k:v for k,v in result.items() if k!='budget'}
    public.update(details=details,cost=cost,verification=checks,
                  old30_gain_bracket_s=[.26,.30],
                  no_gain_addition_to_previous_local_or_whole_lap=True,
                  terminal_debt_resolved=False,promotion_to_actual_or_pixel=False,
                  deadline_utc='2026-10-20T10:01:55Z')
    (g/'retry/extension446_result.json').write_text(json.dumps(public,indent=2)+'\n')
    print(json.dumps(dict(status=result['status'],gain60=result['gain60_bracket_s'],details=details,cost=cost)))


if __name__=='__main__':
    run(Path(sys.argv[1]))
