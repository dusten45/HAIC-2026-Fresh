"""Render derived diagnostic series and findings; reads saved 482 scalars only."""
import time
START=time.perf_counter()
import hashlib,json,sys,os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR','/tmp/haic-stage482-matplotlib-cache')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

G=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def classify_ties(series,ties):
    values=[]
    for t in ties:
        x=series[t['action']-1];chosen=next(o for o in x['options'] if o['aliases']==x['selected_aliases'])
        values.append(dict(action=t['action'],selected_M80=chosen['risk']['M80']))
    return [x for x in values if x['selected_M80']==0],[x for x in values if x['selected_M80']>0]
def run(root):
    d=root/'stage482/analysis1';private=d/'timeseries-private.json';cost=json.loads((d/'analysis-cost-private.json').read_text());record=next(x for x in cost['files'] if Path(x['path'])==private)
    assert sha(private)==record['sha256'];data=json.loads(private.read_text());s=data['series'];pub=json.loads((G/'retry/diagnostic482_summary.json').read_text());window=s[117:125];xs=[x['action'] for x in window]
    fig,axes=plt.subplots(4,2,figsize=(12,13),sharex=True);a=axes.ravel()
    a[0].plot(xs,[x['post']['signed_error_m'] for x in window],'-o',label='post signed error')
    a[0].plot(xs,[x['own_risk']['max_guard_path_error_m'] for x in window],'--',label='hold max |error|')
    a[0].axhline(3,color='r',ls=':',label='3 m guard');a[0].set_ylabel('m');a[0].set_title('Path and guard (own observations)')
    a[1].plot(xs,[x['post']['normal_velocity_m_s'] for x in window],'-o',label='normal velocity m/s')
    a[1].plot(xs,[x['post']['heading_error_deg'] for x in window],'-s',label='heading error deg');a[1].set_title('Path-frame motion; tangent changes at vertices')
    for name in ('front','rear'):
        a[2].plot(xs,[x['own_tire'][name]['max_force_ratio'] for x in window],'-o',label=name)
        a[5].plot(xs,[x['own_tire'][name]['max_abs_lateral_slip_m_s'] for x in window],'-o',label=name)
    a[2].axhline(1,color='r',ls=':');a[2].set_ylabel('pre-clamp force / limit');a[2].set_title('Maximum force demand within hold')
    a[3].plot(xs,[x['own_tire']['steering']['target_joint_rad'] for x in window],'-o',label='joint target')
    a[3].plot(xs,[x['own_tire']['steering']['last_pre_force_joint_rad'] for x in window],'--x',label='last pre-force joint');a[3].set_ylabel('rad');a[3].set_title('Actuator tracks target; this does not certify path')
    a[4].plot(xs,[x['pre_speed_m_s'] for x in window],'-o',label='pre speed')
    a[4].plot(xs,[x['reference_speed_m_s'] for x in window],'-s',label='same-pre P4 reference');a[4].set_ylabel('m/s');a[4].set_title('Speed and reference (same pre boundary)')
    axk=a[4].twinx();axk.plot(xs,[x['reference_node_curvature_m_inv'] for x in window],':',color='grey',label='profile node curvature');axk.set_ylabel('profile curvature 1/m');axk.legend(loc='lower left',fontsize=7)
    a[5].set_ylabel('max |lateral slip| m/s');a[5].set_title('Front versus rear slip within hold')
    a[6].step(xs,[x['selected_command'][1] for x in window],where='mid',label='gas')
    a[6].step(xs,[x['selected_command'][2] for x in window],where='mid',label='brake')
    a[6].plot(xs,[x['nominal'][2] for x in window],':',label='nominal brake');a[6].set_ylabel('pedal');a[6].set_title('Selected pedal; cuts at 122 and 123')
    a[7].plot(xs,[x['own_risk']['M80'] for x in window],'-o',label='own M80')
    a[7].plot(xs,[x['post_yaw_rad_s'] for x in window],'-s',label='post yaw rad/s');a[7].set_title('Risk proxy and observed yaw')
    for ax in a:
        ax.grid(alpha=.2);ax.legend(fontsize=7);ax.set_xlim(117.7,126.3);ax.axvline(126,color='grey',ls=':');ax.set_xticks(range(118,127));ax.set_xlabel('online own action; query 126 NOT dispatched')
    fig.suptitle('481 saved evidence: last safe segment (482, no new physics)\nTrace maxima are pre-force; pose is post-hold. Curvature is a stored profile descriptor.',fontsize=12)
    fig.tight_layout(rect=(0,0,1,.95));image=G/'retry/diagnostic482_timeseries.png';assert not image.exists();fig.savefig(image,dpi=140);plt.close(fig)
    strict=[x for x in pub['minM80_margin_tradeoffs_over1mm'] if x['M80_advantage']>0];ties=[x for x in pub['minM80_margin_tradeoffs_over1mm'] if x['M80_advantage']==0]
    zero_ties,positive_ties=classify_ties(s,ties)
    rawwindow=[x for x in data['raw_series'] if x['action']>=118];q126=s[-1]
    arcs=[x['arc_m'] for x in rawwindow]+[s[124]['post']['arc_m']]
    # Include candidate raw post coordinates only through derived scalar geometry.
    q126fail=[]
    for opt in q126['options']:
        first=next(x for x in opt['raw_diagnostics'] if x['guard_path_error_m']>3)
        loss=next((x for x in opt['raw_diagnostics'] if x['road_contacts']<4 or x['grass']),None)
        q126fail.append(dict(aliases=opt['aliases'],first_path_guard_raw_tick=first['raw_tick'],first_path_guard_time_s=first['time_s'],path_error_at_first_guard_m=first['guard_path_error_m'],signed_error_at_first_guard_m=first['signed_error_m'],normal_velocity_at_first_guard_m_s=first['normal_velocity_m_s'],heading_at_first_guard_deg=first['heading_error_deg'],yaw_at_first_guard_rad_s=first['yaw_rad_s'],road_contacts_at_first_guard=first['road_contacts'],first_road_loss_raw_tick=None if loss is None else loss['raw_tick'],grass_any=any(x['grass'] for x in opt['raw_diagnostics'])))
        assert first['raw_tick']==2 and first['road_contacts']==4 and loss['raw_tick']==4
    points=[]
    for x in window:
        points.append(dict(action=x['action'],pre_time_s=x['pre_time_s'],pre_speed_m_s=x['pre_speed_m_s'],pre_reference_m_s=x['reference_speed_m_s'],speed_excess_m_s=x['speed_minus_reference_m_s'],pre_profile_curvature_m_inv=x['reference_node_curvature_m_inv'],pre_smoothing_delta_rad=x['steering_smoothing_delta_rad'],post_time_s=x['post_time_s'],post_signed_error_m=x['post']['signed_error_m'],hold_guard_max_error_m=x['own_risk']['max_guard_path_error_m'],post_normal_m_s=x['post']['normal_velocity_m_s'],post_heading_deg=x['post']['heading_error_deg'],post_yaw_rad_s=x['post_yaw_rad_s'],front=x['own_tire']['front'],rear=x['own_tire']['rear'],steering=x['own_tire']['steering'],own_M80=x['own_risk']['M80']))
    findings=dict(stage=482,source_private_sha256=sha(private),source_analyzer_sha256=cost['source_code_sha256'],source_renderer_sha256=sha(__file__),new_physics=0,new_worlds=0,baseline_safe_prefix=73,baseline_unsafe_action=74,online_safe_actions=125,
        strict_eligible_margin_tradeoffs_over1mm=strict,exact_equal_M80_tie_margin_tradeoffs_over1mm=len(ties),exact_zero_M80_tie_margin_tradeoffs_over1mm=len(zero_ties),exact_positive_M80_ties=positive_ties,tie_actions=[x['action'] for x in ties],
        timeline=points,query126_guard_sequence=q126fail,last_segment_projection=dict(actions=[118,125],all_pre_force_interior=all(x['projection_side']=='interior' for x in rawwindow),strictly_increasing_projected_arc=all(b>a for a,b in zip(arcs,arcs[1:])),raw_arc_delta_range_m=[min(b-a for a,b in zip(arcs,arcs[1:])),max(b-a for a,b in zip(arcs,arcs[1:]))],own_all_four_road_contacts=all(x['road_contacts']==4 for x in rawwindow),own_grass_any=any(x['grass'] for x in rawwindow),interpretation='Changing tangent at consecutive polyline segments explains signed normal/heading jumps. No projection tie/branch discontinuity observed in this window; not a smooth curvature derivative.'),
        all125_max_last_pre_force_servo_lag_rad=max(x['own_tire']['steering']['last_pre_force_lag_rad'] for x in s[:-1]),
        limits=['Unselected forecasts observed once; differences are saved cold model observations, not repeated warm counterfactuals.','No continuation after query126 was observed.','80ms versus longer horizon not experimentally compared.','472 success suffix begins from another state; no cross-run causal inference.'])
    save(G/'retry/diagnostic482_findings.json',findings)
    save(d/'render-cost-private.json',dict(CPU_s=time.process_time(),wall_s=time.perf_counter()-START,source_code_sha256=sha(__file__),input_sha256=sha(private),image_sha256=sha(image),image_bytes=image.stat().st_size,new_physics=0,new_worlds=0))
    print(json.dumps(dict(stage=482,image_bytes=image.stat().st_size,strict_tradeoffs=len(strict),ties=len(ties),CPU_s=time.process_time(),wall_s=time.perf_counter()-START)))
if __name__=='__main__':run(Path(sys.argv[1]))
