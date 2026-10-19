"""Saved605 failure magnitudes and complete geometry-cost decomposition."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import collections,json
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response605-private')
def read(p):return json.loads(p.read_text())
def main():
    r=read(D/'as-executed-result-private.json');failures=[];plane_queries=0
    for q in r['candidates']:
        data=read(D/(q['label']+'-result-private.json'))
        hits=q['crossings'];query_count=0
        for row in data['rows']:
            if row.get('pre_failure') or row.get('post_failure'):continue
            query_count+=3-sum(hit['after_raw']<=row['global_raw_before'] for hit in hits.values())
        plane_queries+=query_count
        if q['label']=='zero':
            # Zero validation repeats only saved world-plane arithmetic, not
            # the original physics or original margin evaluator.
            plane_queries+=query_count
            continue
        row=data['rows'][-1]
        if q['stop']=='INCUMBENT_NO_ADMISSIBLE_ACTION':
            report=q['failure']['report']
            failures.append(dict(label=q['label'],kind='INCUMBENT_POLICY_REJECTED',next_global_raw=q['global_raw']+1,
                finite_trial_reasons=dict(collections.Counter(t['reason'] for t in report.get('trials',[]))),
                interpretation='No modified action applied at this decision. Original537finitegrid/backupwitness returnednone; not an observed future applied collision/forcefailure.'))
        else:
            failures.append(dict(label=q['label'],kind=q['failure']['reason'],attempt_raw=row['global_raw_before']+1,
                completed_bad_raw=row.get('global_raw_after'),max_force_ratio=max(z['ratio'] for z in row['forces']),
                force_limit=1.059,clip_fraction=row['proposed_history'][0]/row['proposed_history'][1],
                footprint_m=row.get('margin'),footprint_limit_m=.5,
                tick_executed=row['tick_executed']))
    cost=r['cost'];geometry_kinds={k:v for k,v in cost.items() if k.startswith('geometry_')}
    decomposition=dict(named_margin_projection=sum(geometry_kinds.values()),
        helper_original_comparisons=cost['helper_original_comparisons'],world_plane_queries=plane_queries,
        residual_virtual_target_queries=cost.get('geometry_residual_projection',0),
        frozen_world_planes=3,initial_finish_tracker_geometry=1)
    assert sum(decomposition.values())==cost['geometry']
    zero=r['candidates'][0]
    result=dict(study=605,scope='Fixed eight Hadamard amplitude points only; no continuous-family/global feasibility or native conclusion.',
        nonzero_safe_endpoints=0,uncompleted=len(r['uncompleted']),failures=failures,
        zero_diagnostic_crossings=zero['crossings'],zero_crossing_hold_safe_through_raw=zero['global_raw'],
        geometry_decomposition=decomposition,geometry_total=sum(decomposition.values()),
        every_new_geometry_query_accounted=True,helper_compared_bitwise_queries=cost['helper_original_comparisons'],
        bracket_resolution_s=.02,interpolated_time_is_official_lap=False,
        read_only_CPU_s=time.process_time()-CPU,read_only_wall_s=time.perf_counter()-WALL,new_evaluations=0)
    (G/'retry/residual605_analysis.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['geometry_decomposition','geometry_total','read_only_CPU_s','read_only_wall_s']},indent=2))
if __name__=='__main__':main()
