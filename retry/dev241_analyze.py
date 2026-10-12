"""Analyze only newly declaredDEV241 caches; no HOLDOUT, fit or policy search."""
import argparse
import json
from pathlib import Path
import numpy as np

FEATURE_NAMES=['target_missing','target_x','target_forward','HUD_speed','pedal_feedback_speed',
    'curvature','target_speed','previous_shadow_steer','near_hazard','route_length',
    'path_point_count','obstacle_count','nearest_pixel_hazard_range','nominal_steer','nominal_gas','nominal_brake']


def analyze(directory):
    p=json.loads((directory/'plan.json').read_text());o=json.loads((directory/'outcome.json').read_text());out={}
    for item in o['records']:
        r=item['result'];folder=directory/'runs'/r['role'];d=json.loads((folder/'diagnostic.json').read_text());scene=json.loads((folder/'scene-private.json').read_text());c=np.load(folder/'legal-cache.npz');rows=d['actual_steps'];features=c['features']
        assert len(c['observations'])==len(features)+1==len(rows)+1
        assert all(features[j,7]==c['nominal_memory_after'][j-1] for j in range(1,len(features)))
        def legal_row(i):
            f=features[i];return dict(action=i+1,observation_index=i,target_missing=bool(f[0]),HUD_speed=float(f[3]),feedback_speed=float(f[4]),curvature=float(f[5]),nominal_target_speed=float(f[6]),near_hazard=bool(f[8]),route_length=float(f[9]),path_points=int(f[10]),obstacles=int(f[11]),nearest_pixel_hazard_range=float(f[12]),nominal_pedals=c['nominal'][i,1:].tolist(),base232_pedals=c['base232'][i,1:].tolist(),executed240_pedals=c['executed'][i,1:].tolist())
        contact=next((i for i,x in enumerate(rows) if x['collision']),None)
        streak=0;stagnation=None;previous=scene['initial']['unique_tiles'];longest=0;lastnew=0
        for i,x in enumerate(rows):
            if x['visited']>previous:streak=0;lastnew=x['action']
            else:streak+=1
            previous=x['visited'];longest=max(longest,streak)
            if streak>=5 and stagnation is None:stagnation=i
        reverse=next((i for i,x in enumerate(rows) if x['speed_m_s']>=1 and x['nearest_road_tangent_speed']<0),None)
        def event(i):
            if i is None:return None
            x=rows[i];return dict(action=i+1,poststep_actual_speed_m_s=x['speed_m_s'],poststep_damage=x['damage'],visited=x['visited'],wheel_road_contacts=x['wheel_road_contacts'],preaction_legal_features=legal_row(i),preceding_legal_window=[legal_row(j) for j in range(max(0,i-4),i+1)],scope='Legalfeaturesbeforecurrentaction; event/GTstateafteraction diagnostic only, notfuturepolicyinput. Pixelmax80ms beforeevent within4rawticks.')
        fvalid=features[:,0]==0;v=features[:,4];lateral=v*v*np.abs(features[:,5]);near=features[:,8]>0
        out[item['road']]=dict(completed=r['completed'],censored=r['censored'],lap_ms=r['lap_ms'],damage=r['damage'],retire_reason=r['retire_reason'],native_actions=r['charged_wrapper_actions'],visited=r['unique_tiles'],total_tiles=r['total_tiles'],unvisited=r['total_tiles']-r['unique_tiles'],first_contact=event(contact),first_stagnation_5_no_new_tiles=event(stagnation),first_moving_nearest_tangent_reverse=event(reverse),last_new_tile_action=lastnew,longest_no_new_tile_streak=longest,stationary_actions=sum(x['speed_m_s']<=.001 for x in rows),valid_target_actions=int(fvalid.sum()),target_missing_actions=int((~fvalid).sum()),near_hazard_actions=int(near.sum()),valid_target_lateral_proxy_over24_actions=int(np.sum(fvalid&(lateral>24))),curvature_abs_median=float(np.median(np.abs(features[fvalid,5]))) if fvalid.any() else None,feedback_speed_median=float(np.median(v)),source_startline_crossings=d['source_startline_crossings'],features_are_actual_legal_calls=True,cache_bytes=item['cache_bytes'])
    result=dict(stage=241,cases=out,feature_mapping=dict(curvature=dict(index=5,formula='2*x/max(forward^2+x^2,1e-6), selectedpixel-route target; zeroiffallback target missing, notGTcurvature'),hazard=dict(near_index=8,obstacle_count_index=11,range_index=12,formula='Trackedimageobstacle aheadwithin clip(4+.35*HUDspeed,6,14)+2.6+radius; nearsetsnominal lateral8vs24. Range=minhypot(pixelbodyx,y),default100.'),speed=dict(HUD_index=3,formula='max(0,11.4142485314592*sum(image[74:83,9:14])-6.545558315185489)',feedback_index=4,feedback='ExistingHUDtemplate decoder, fallbacktoHUDspeed; currentnominalpedalcall argument'),target_missing_index=0),hypothesis=dict(status='Proposeone futurefalsification only, nottrainedorimplemented',policy_basis='Keep240 gas/head/steering/memory. Twolearnedglobalcoefficients mayscale brakeonly usingvalid-target curvature-speed lateral demand andexistingnear_hazard. Curvebasis canusebounded excessof feedback_speed^2*abs(curvature) overexistingnominal lateral24; hazardbasis=near_hazard. Bothinactiveonvalidstraight/nonhazard input; route_missing notclassifiedstraight.',guard='Useonly16legalpreactionfeatures. NoGTgeometry, futurecollision/damage, progresscounter orposteventvariables aspolicyinputs. Thisdoesnotrepairroutefinding/steeringorprovecontactavoidance.',evaluation='Iflaterauthorized, directactualcompletion/time objective onDEV; noimitation-error reward, noHOLDOUTretuning. No newconditionalparameters now.'),HOLDOUT_opened=False,SEALED_opened=False,champion_changed=False)
    q=directory/'analysis.json'
    with q.open('x') as f:json.dump(result,f,indent=2,allow_nan=False);f.write('\n')
    q.chmod(0o600);print(json.dumps({k:dict(completed=v['completed'],lap_ms=v['lap_ms'],first_contact=v['first_contact']['action'] if v['first_contact'] else None,first_stagnation=v['first_stagnation_5_no_new_tiles']['action'] if v['first_stagnation_5_no_new_tiles'] else None,first_reverse=v['first_moving_nearest_tangent_reverse']['action'] if v['first_moving_nearest_tangent_reverse'] else None) for k,v in out.items()}))


if __name__=='__main__':
    a=argparse.ArgumentParser(description=__doc__);a.add_argument('--directory',type=Path,required=True);analyze(a.parse_args().directory)
