"""Saved-only closure of444; no controller, model or physics calls."""
import datetime
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from retry.executor397 import canonical_projection


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(root):
    cpu, wall = time.process_time(), time.perf_counter()
    g = Path(__file__).resolve().parents[1]
    d = root/'stage444'
    original = read(d/'plan.json')
    fixed = read(Path(original['fixed_plan']))
    public = {}
    for name in ['H1','H2']:
        folder = d/name
        p, result = read(folder/'plan.json'), read(folder/'result.json')
        for files in [p['sources'],p['protected']]:
            for path, digest in files.items():
                assert sha(Path(path)) == digest, path
        assert sha(folder/'plan.json') == result['plan_sha256']
        budget = result['budget']
        assert budget['ticks'] == budget['reserved_ticks']
        assert budget['ticks'] <= p['caps']['ticks'] and budget['worlds'] <= p['caps']['worlds']
        assert budget['CPU_s'] < p['caps']['CPU_s'] and budget['execution_wall_s'] < p['caps']['wall_s']
        posts = sum(len(read(x)['posts']) for x in folder.glob('*-observer-private.json'))
        assert posts == budget['ticks']
        assert result['qualification']['passed']
        count = p['horizon']
        assert all(a['certified_prefix_actions']==count for a in result['qualification']['replays'])
        assert all(a['fresh_current_first_pass']>=1 for a in result['qualification']['replays'])
        out = {k:v for k,v in result.items() if k not in ['qualification','arms','budget']}
        out.update(caps=p['caps'], model_cost={k:budget[k] for k in ['ticks','reserved_ticks','worlds','confirmed_worlds','CPU_s','execution_wall_s']},
                   qualification_passed=True, actual_ledger_not_advanced=True,
                   source_and_observer_posts_reconciled=True,
                   arms=result['arms'])
        if name == 'H1':
            observations = {}
            for label in ['nominal1','fullgas1']:
                rows = read(folder/(label+'-private.json'))['rows']
                common = result['common_exit']['nominal' if label=='nominal1' else 'fullgas']
                wanted = common['rawtick_bracket']
                start = rows[0]['raw_hull'][0]['time']
                samples = []
                for row in rows:
                    for hull in row['raw_hull']:
                        tick = round((hull['time']-start)*50)
                        if tick not in wanted:
                            continue
                        k = hull['raw_tick']-1
                        tires = row['tires'][4*k:4*k+4]
                        q = canonical_projection(fixed['line'],hull['origin_position'],hull['COM_linear_velocity'],row['memory_after']['C']['phase'])
                        samples.append(dict(tick=tick, yaw_rad_s=hull['yaw'],path_error_m=q['path_error_m'],
                                            front_joint_rad=[z['joint_angle'] for z in tires[:2]],
                                            wheel_omega=[z['omega'] for z in tires],
                                            force_ratio=[z['force_ratio'] for z in tires]))
                observations[label] = samples
            (folder/'exit-state-samples-private.json').write_text(json.dumps(observations,indent=2)+'\n')
            out['common_exit_state_ranges'] = {}
            for label, samples in observations.items():
                summary = {}
                for field in ['yaw_rad_s','path_error_m','front_joint_rad','wheel_omega','force_ratio']:
                    values = []
                    for sample in samples:
                        value = sample[field]
                        values.extend(value if isinstance(value,list) else [value])
                    summary[field] = [min(values),max(values)]
                out['common_exit_state_ranges'][label] = summary
            for arm in out['common_exit'].values():
                for field in ['terminal_joint','terminal_omega','terminal_force_ratio']:
                    values = arm.pop(field)
                    arm[field+'_range'] = [min(values),max(values)]
            out['exit_state_warning'] = 'Bracketing raw samples only, not continuous-time bounds. End-of13 states are at the same1.04s but different positions; they are not matched-exit states.'
            out['terminal_debt_resolved'] = False
            out['all_four_arms_repeat_exact'] = (result['arms'][0]['signature']==result['arms'][1]['signature'] and result['arms'][2]['signature']==result['arms'][3]['signature'])
        else:
            assert result['status']=='TECHNICAL_STOP'
            a = read(folder/'predicate_nominal1-private.json')
            b = read(folder/'predicate_nominal2-private.json')
            assert a['rows']==b['rows'] and a['status']==b['status']=='UNSAFE'
            assert len(a['rows'])==14 and not any(x['safety'] for x in a['rows'][:13])
            assert a['rows'][13]['safety']==['path_error_over3m']
            own = read(folder/'B1-private.json')
            assert own['rows']==[]
            out.update(predicate_safe13_unsafe14=True,
                       transition14_path_error_m=a['rows'][13]['path_error_m'],
                       both_nominal_predicate_repeats_exact=True,
                       B_parent_actions=0, B_shadow_integrated_ticks=0,
                       B_result_unobserved=True,
                       failure_category='LEDGER_INPUT_TYPE_WIRING_NOT_PHYSICAL_REFUTATION',
                       failed_constructor_world_charged=True,
                       constructed_worlds_without_first_step=budget['worlds']-len(list(folder.glob('world*-before-first-step-private.json'))),
                       retry_or_post_error_model_fix=False)
        public[name] = out
        (g/f'retry/hypothesis444_{name}_result.json').write_text(json.dumps(out,indent=2)+'\n')
    assert public['H1']['model_cost']['ticks']==316 and public['H2']['model_cost']['ticks']==228
    cost = dict(stage=444,model_ticks=544,model_worlds=14,
                hypothesis_costs={name:x['model_cost'] for name,x in public.items()},
                new_actual_actions=0,new_resets=0,new_learning_seed_HOLDOUT_SEALED_reserve_paid=0,
                research_remaining=27516,reserve=84000,reserve_used=0,
                static_CPU_s=read(d/'static-result.json')['CPU_s'],
                static_wall_s=read(d/'static-result.json')['wall_s'],
                saved_closure_CPU_s=time.process_time()-cpu,saved_closure_wall_s=time.perf_counter()-wall,
                preparation_report_git_import_overhead_fully_measured=False,
                status='GLOBAL_STOP_AFTER_H2_TECHNICAL_ERROR_NO_RETRY')
    (d/'closure-cost-private.json').write_text(json.dumps(cost,indent=2)+'\n')
    summary = dict(stage=444,results=public,cost=cost,
                   deadline_utc='2026-10-20T10:01:55Z',
                   promotion_to_actual_or_pixel=False,
                   H1_gain_not_added_to_442=True)
    (g/'retry/experiments444_result.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(dict(status=cost['status'],H1_gain=public['H1']['gain_bracket_s'],
                         H2_predicate=True,H2_B_actions=0,total_model_ticks=544,total_worlds=14)))


if __name__=='__main__':
    run(Path(sys.argv[1]))
