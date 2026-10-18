"""One local speed-cap correction from per-wheel source-force history."""
import math
from retry.capacity522_control import path_for as capacity_path
from retry.drive519_control import drive


def paths_from_history(static,trace,calibration):
    baseline=capacity_path(static,'baseline');capacity=capacity_path(static,'capacity');admission=calibration['proposed_prediction_admission_ratio']
    if not 0<admission<1.25:raise ValueError('UNUSABLE_FORCE_UNCERTAINTY')
    L=capacity['length'];history=[];prior=static['root'];previous_progress=0.
    for row in trace:
        if row['index']>24:
            ratio=max(w['ratio'] for w in row['forces']);speed=math.hypot(*prior['planar']['linear']['velocity'])
            if ratio>admission:history.append((previous_progress%L,speed*speed*admission/ratio))
        prior=row['root_without_roads'];previous_progress=row['progress']
    # Source force history carries yaw, wheel omega/gas and per-wheel slip state.
    # Square-speed scaling is a falsifiable local approximation, not a certificate.
    caps=[min(80.**2,153.38431605269326/max(abs(k),1e-8)) for k in capacity['curvature']];original=caps.copy();affected=0
    for i,s in enumerate(capacity['arcs'][:-1]):
        nearby=[q for t,q in history if min(abs(s-t),L-abs(s-t))<=10.]
        if nearby:caps[i]=min(caps[i],min(nearby))
        if caps[i]<original[i]:affected+=1
    q=caps.copy();n=len(q);ds=capacity['ds']
    for rounds in range(2*n):
        old=q.copy()
        for i in range(n-1,-1,-1):q[i]=min(q[i],q[(i+1)%n]+90.*ds[i])
        for i in range(n):j=(i+1)%n;q[j]=min(q[j],q[i]+2*drive(q[i])*ds[i])
        if old==q:break
    else:raise ValueError('FORCE_PROFILE_NONCONVERGENCE')
    launch=[0.]
    for i,d in enumerate(ds):launch.append(min(q[(i+1)%n],launch[-1]+2*drive(launch[-1])*d))
    candidate=dict(capacity,periodic_squared=q,launch_squared=launch,periodic_pass_rounds=rounds+1)
    return dict(baseline=baseline,capacity=capacity,shield=candidate),dict(admission_force_ratio=admission,uncertainty_margin=calibration['calibrated_empirical_force_margin'],source_high_force_raw_samples=len(history),local_cap_affected_nodes=affected,total_nodes=n,pooling_radius_m=10.,history_from_model_only=True,actual_future_trace_in_policy=False)
