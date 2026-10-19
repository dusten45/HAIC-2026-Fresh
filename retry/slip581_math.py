"""Pure wheel-heading alignment and stored-prefix comparisons; no integration."""
import math,json
import numpy as np


def alignment(root,pedals):
    p=root['planar'];v=p['linear']['velocity'];angles=[]
    for w in p['linear']['wheels'][:2]:
        vi=[v[j]+w['offset'][j] for j in range(2)]
        if not all(math.isfinite(x) for x in vi) or math.hypot(*vi)<=1e-12:raise RuntimeError('ALIGNMENT_DOMAIN_VELOCITY')
        angles.append(math.atan2(-vi[0],vi[1]))
    sy=sum(math.sin(t) for t in angles);cx=sum(math.cos(t) for t in angles)
    if not math.isfinite(sy+cx+p['angle']) or math.hypot(sy,cx)<=1e-12:raise RuntimeError('ALIGNMENT_DOMAIN_MEAN')
    difference=math.atan2(sy,cx)-p['angle'];q=math.atan2(math.sin(difference),math.cos(difference));a=np.asarray([-max(-.4,min(.4,q)),*pedals],np.float32)
    if not np.all(np.isfinite(a)):raise RuntimeError('ALIGNMENT_DOMAIN_ACTION')
    return a


def diagnostic(root):
    p=root['planar'];v=p['linear']['velocity'];ratios=[]
    for w in p['linear']['wheels']:
        forward=(-math.sin(w['heading']),math.cos(w['heading']));side=(forward[1],-forward[0]);ratios.append(abs(82.*sum((v[j]+w['offset'][j])*side[j] for j in range(2)))/w['friction'])
    return dict(COM_speed_m_s=math.hypot(*v),yaw_rad_s=p['yaw'],front_joint_mean_rad=sum(p['joints'][:2])/2,front_rate_mean_rad_s=sum(p['rates'][:2])/2,front_servo_error_abs_max_rad=max(abs(p['steer']-j) for j in p['joints'][:2]),maximum_lateral_component_ratio=max(ratios),front_lateral_component_ratio_max=max(ratios[:2]))


def branch_equal(row,expected,clock_row):
    pairs=[('before_root_without_roads','before'),('root_without_roads','after'),('forces','forces'),('tracking_history_before','history_before'),('proposed_history','history'),('progress','progress'),('margin','margin'),('path_error','path_error'),('reference_overspeed','reference_overspeed'),('body','body')]
    for key,other in pairs:
        if json.loads(json.dumps(row.get(key)))!=expected.get(other):return False
    return row['action']==expected['action'] and row['global_raw_before']==expected['context']['global_raw'] and row['global_raw_after']==expected['context']['global_raw']+1 and row['index']==expected['context']['index'] and row['raw']==expected['context']['raw'] and row['episode_before_s']==clock_row['episode_before_s'] and row['episode_after_s']==clock_row['episode_after_s']
