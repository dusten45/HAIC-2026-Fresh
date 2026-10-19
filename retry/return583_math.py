"""Read-only plane descriptors and cache accounting; no physics."""
import math
from retry.beam579_math import crossing
from retry.slip581_math import diagnostic


def plane_observation(row,plane):
    h=crossing(row,plane)
    if h is None:return None
    f=h['fraction'];before=row['before_root_without_roads'];after=row['root_without_roads'];a=diagnostic(before);b=diagnostic(after)
    values={k:a[k]+f*(b[k]-a[k]) for k in ['yaw_rad_s','front_joint_mean_rad','front_rate_mean_rad_s']}
    for name,field in [('rear_omega_mean_rad_s','omega'),('rear_gas_mean','gas')]:
        x=sum(w[field] for w in before['planar']['linear']['wheels'][2:])/2;y=sum(w[field] for w in after['planar']['linear']['wheels'][2:])/2;values[name]=x+f*(y-x)
    return dict(h,station_m=plane['station_m'],interpolated=values,tracking_before_raw=row['tracking_history_before'],tracking_after_raw=row['proposed_history'],margin_after_raw_m=row['margin'],path_error_after_raw_m=row['path_error'],reference_overspeed_after_raw_m_s=row['reference_overspeed'],body_after_raw_m_s=row['body'],crossing_hold_safe=False)


def bracket_comparison(candidate,baseline):
    return dict(candidate_before_raw=candidate['before_raw'],candidate_after_raw=candidate['after_raw'],baseline_before_raw=baseline['before_raw'],baseline_after_raw=baseline['after_raw'],gain_lower_raw=baseline['before_raw']-candidate['after_raw'],gain_upper_raw=baseline['after_raw']-candidate['before_raw'],gain_lower_s=.02*(baseline['before_raw']-candidate['after_raw']),gain_upper_s=.02*(baseline['after_raw']-candidate['before_raw']),COM_speed_delta_m_s=candidate['COM_speed_m_s']-baseline['COM_speed_m_s'],interpolated_deltas={k:candidate['interpolated'][k]-baseline['interpolated'][k] for k in candidate['interpolated']},margin_after_raw_delta_m=candidate['margin_after_raw_m']-baseline['margin_after_raw_m'])


def cache_accounting(detail,certificates):
    sample=sum(c['role']=='SAMPLE' for c in certificates);final=sum(c['role']=='FINAL' for c in certificates)
    if certificates and certificates[0]['report']['ok']:requests=1
    elif 'coarse_points' in detail:requests=1+detail['coarse_points']+detail['refinements']
    else:requests=next(c['evaluate_requests'] for c in certificates if c['role']=='FINAL')
    if sample>requests:raise RuntimeError('CACHE_ACCOUNTING_IDENTITY')
    return dict(evaluate_requests=requests,sample_cache_misses=sample,cache_hits=requests-sample,fresh_FINAL_calls=final,actual_certification_calls=len(certificates),derivation='Requestsfromexecutedoriginaldetail;cachemissandFINALfromactualfactorycalls,noevaluationreexecution.')
