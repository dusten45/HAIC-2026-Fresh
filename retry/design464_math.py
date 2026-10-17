"""Pure saved-state proposal arithmetic; no controller/world/runtime entrypoint."""
import math
import numpy as np
from retry.signed417_executor import canonical_projection
from retry.scalar392_audit import pedals

def saved_secant_terms(fixed,pace,row):
    if row['nominal_memory_after']['C']['phase']!='FIRST_LAP':return dict(eligible=False,reason='phase')
    line=np.asarray(fixed['line']);ds=np.asarray(fixed['free_profile']['ds']);nodes=np.asarray(fixed['free_profile']['speed'])*pace;arc=np.r_[0,np.cumsum(ds)]
    z=canonical_projection(line,row['pre']['pos'],row['pre']['vel'],'FIRST_LAP');s=z['arc'];sigma=z['sigma'];ahead=s+.08*sigma
    if not(0<s<ahead<arc[-1]):return dict(eligible=False,reason='strict_interior_positive_progress')
    j=z['index'];u=z['u'];r=math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2)
    def ref(where):
        k=min(len(ds)-1,int(np.searchsorted(arc,where,side='right')-1));fraction=(where-arc[k])/ds[k]
        return math.sqrt((1-fraction)*nodes[k]**2+fraction*nodes[k+1]**2)
    end=ref(ahead);ff=(end-r)/.08;v=row['pre']['speed'];raw=ff+1.5*(r-v);mapped=pedals(raw,v,fixed['model'])
    command=np.asarray(row['nominal'],np.float32).copy();command[1:]=[mapped['gas'],mapped['brake']]
    interior=[float(nodes[k]) for k in range(1,len(nodes)-1) if s<arc[k]<ahead]
    point_ff=(nodes[j+1]**2-nodes[j]**2)/(2*ds[j])*sigma/r
    return dict(eligible=True,command=command.tolist(),changed_from_nominal=not np.array_equal(command,np.asarray(row['nominal'],np.float32)),
        changed_from_dispatched=not np.array_equal(command,np.asarray(row['command'],np.float32)),crossed_nodes=len(interior),
        ff_secant=ff,ff_point=point_ff,raw=raw,brake=float(command[2]),gas=float(command[1]),
        endpoint_below_current_reference=end<r,interior_reference_valley=bool(interior and min(interior)<min(r,end)),
        interior_target_below_current_speed=bool(interior and min(interior)<v),
        endpoint_drives_despite_interior_target_below_speed=bool(raw>0 and interior and min(interior)<v))

def calculate(c):
    e=c['selected_contract'];assert (e['actions_per_trajectory'],e['independent_trajectories_per_arm'],len(e['arms']))==(13,2,2)
    old=e['old_source_cap'];parts=dict(old_source=dict(ticks=old['ticks'],worlds=old['worlds']))
    for arm in e['arms']:
        parts[arm+'_trajectories']=dict(ticks=2*13*4,worlds=2)
        parts[arm+'_held_first']=dict(ticks=4,worlds=1)
    ticks=sum(x['ticks'] for x in parts.values());worlds=sum(x['worlds'] for x in parts.values())
    assert (ticks,worlds)==(1458,41)
    hard=e['hard'];s=c['storage'];payload=hard['ticks']*s['observed_max_model_bytes_per_tick']*s['empirical_margin']+worlds*s['observed_fixed_bytes_per_world']
    # Allocate the full forecast raw payload for a private archive; do not rely on compression.
    archive=payload*s['archive_payload_margin']+s['archive_metadata_allowance_bytes']
    return dict(parts=parts,ticks=ticks,worlds=worlds,trajectory_worlds=4,held_first_worlds=2,separate_main_parent_worlds=0,
        actual_actions=0,resets=0,model_payload_forecast_bytes=payload,model_volume_required_bytes=payload+s['reserve_bytes'],
        archive_forecast_bytes=archive,workspace_required_bytes=archive+s['reserve_bytes'],
        current_model_volume_fits=c['storage']['free_bytes']['/tmp']>=payload+s['reserve_bytes'],
        current_workspace_retention_fits=c['storage']['free_bytes']['/workspace']>=archive+s['reserve_bytes'],
        estimates_are_not_guaranteed_bounds=True)
