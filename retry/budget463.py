"""All-in bounds for one fixed-first native pair, with no modeled parents."""
def calculate(c):
    e=c['execution'];h=e['horizon'];r=e['independent_copies'];n=len(e['order']);suffix=e['suffix_actions']
    assert (n,e['prefix_actions'],suffix,h,r)==(2,125,70,13,2)
    parts=dict(first_fixed=dict(queries=n,ticks=n*r*h*4,worlds=n*r),
        guardian=dict(queries=n*(suffix-1),ticks=n*(suffix-1)*2*r*h*4,worlds=n*(suffix-1)*2*r),
        qualification=dict(ticks=1242+216,worlds=35+6),
        model_parents=dict(ticks=0,worlds=0))
    ticks=sum(x['ticks'] for x in parts.values());worlds=sum(x['worlds'] for x in parts.values())
    actions=n*(e['prefix_actions']+suffix);s=c['storage']
    model=c['hard']['ticks']*s['model_bytes_per_tick']*s['empirical_margin']+worlds*s['fixed_bytes_per_world']+s['final_dump_reserve_bytes']
    native=actions*s['native_bytes_per_action']*s['empirical_margin']+s['final_dump_reserve_bytes']
    assert (ticks,worlds,actions)==(30370,597,390)
    assert ticks<=c['hard']['ticks'] and worlds<=c['hard']['worlds']
    return dict(parts=parts,ticks=ticks,worlds=worlds,actual_actions=actions,resets=2,
        raw_native_ticks_including_reset=actions*4+2*51,
        model_storage_bytes=model,native_storage_bytes=native,storage_estimate_is_not_a_guarantee=True)
