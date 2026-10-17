"""Pure planned budget fixture, bound to the exact two-arm next-design schedule."""
import copy,json,sys
from pathlib import Path


def calculate(p):
    assert len(p['order'])==2 and [x['arm'] for x in p['order']]==['Original','SecantOnce']
    assert [x['first_recipe'] for x in p['order']]==['nominal','fullgas']
    assert p['whole_arm_repeats_per_policy']==1 and p['first_fixed_queries_per_arm']==1
    arms=len(p['order']);first=arms*p['first_fixed_queries_per_arm'];guardian=arms*p['parent_cap']-first
    h,t=p['H'],p['raw_ticks_per_action_max'];q=p['qualification']
    parts=dict(first_fixed=dict(queries=first,ticks=first*p['first_fixed_copies']*h*t,worlds=first*p['first_fixed_copies']),
        guardian=dict(queries=guardian,ticks=guardian*p['guardian_recipes_max']*p['guardian_copies']*h*t,worlds=guardian*p['guardian_recipes_max']*p['guardian_copies']),
        parents=dict(actions=arms*p['parent_cap'],ticks=arms*p['parent_cap']*t,worlds=arms),
        qualification=dict(ticks=q['old_ticks']+q['root_ticks'],worlds=q['old_worlds']+q['root_worlds']))
    out=dict(parts=parts,ticks=sum(x['ticks'] for x in parts.values()),worlds=sum(x['worlds'] for x in parts.values()))
    assert out['ticks']<=p['hard']['ticks'] and out['worlds']<=p['hard']['worlds']
    assert p['hard']['actual_actions']==0 and p['hard']['max_parallel']==1
    s=p['storage'];out['empirical_raw_bytes_at_hard_with_margin_and_reserve']=p['hard']['ticks']*s['observed_max_bytes_per_tick']*s['empirical_margin']+s['final_dump_reserve_bytes']
    out['storage_estimate_is_not_a_guarantee']=True
    return out

if __name__=='__main__':
    path=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).with_name('design461_next.json');p=json.loads(path.read_text());result=calculate(p)
    assert (result['ticks'],result['worlds'])==(43650,839)
    assert (result['parts']['first_fixed']['queries'],result['parts']['guardian']['queries'])==(2,198)
    bad=copy.deepcopy(p);bad['hard']['ticks']=43649
    try:calculate(bad)
    except AssertionError:pass
    else:raise AssertionError('Planned-over-hard must fail before integration')
    print(json.dumps(dict(passed=True,scope='STATIC_ONLY_NO_INTEGRATION',planned=result)))
