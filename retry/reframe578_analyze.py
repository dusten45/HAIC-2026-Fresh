"""Read-only time allocation and representation analysis; no simulator imports."""
import hashlib,json,math,signal,time
from pathlib import Path
from collections import Counter
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
INPUTS={
 'current':Path('/workspace/haic-response577-private/final-independent-tape-private.json'),
 'seed573':Path('/workspace/haic-response573-private/final-independent-tape-private.json'),
 '551':Path('/workspace/haic-response551-private/cold-candidate-private.json'),
 'paths':Path('/workspace/haic-response551-private/frozen-paths-private.json'),
 'static':Path('/workspace/haic-response515-private/collected-map-state-private.json'),
 '555branches':Path('/workspace/haic-response555-recovery-private/steady-branches-private.json'),
 '577basis':Path('/workspace/haic-response577-private/frozen-bases-private.npz'),
 '574linear':Path('/workspace/haic-response574-private/linear-1-private.npz')}
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def categories(rows,path,obstacles):
    arcs=np.asarray(path['arcs']);curv=np.asarray(path['curvature']);length=path['length'];last_zone_s=None;labels=[];last_progress=None
    for row in rows:
        s=row['progress'];root=row['root_without_roads'];pos=np.asarray(root['center']);j=min(len(curv)-1,max(0,int(np.searchsorted(arcs,s%length,side='right')-1)));near=min(np.linalg.norm(pos-np.asarray(center))-radius for center,radius in obstacles)<8.;turn=abs(curv[j])>=.0125
        if near or turn:last_zone_s=s
        if row['index']<=24:label='launch'
        elif near:label='avoidance_proximity'
        elif turn:label='corner_curvature'
        elif last_zone_s is not None and 0<=s-last_zone_s<=35.:label='recovery_window'
        else:label='straight_acceleration_or_cruise'
        labels.append(label);last_progress=s
    return labels

def allocation(rows,path,obstacles):
    labels=categories(rows,path,obstacles);out={}
    for label in ['launch','straight_acceleration_or_cruise','corner_curvature','avoidance_proximity','recovery_window']:
        selected=[r for r,k in zip(rows,labels) if k==label];dt=sum(r['episode_after_s']-r['episode_before_s'] for r in selected);v=np.asarray([math.hypot(*r['root_without_roads']['planar']['linear']['velocity']) for r in selected]);tracking=[r for r in selected if r['index']>24]
        proxy=sum((r['episode_after_s']-r['episode_before_s'])*max(0.,1.-math.hypot(*r['root_without_roads']['planar']['linear']['velocity'])/(math.hypot(*r['root_without_roads']['planar']['linear']['velocity'])-r['reference_overspeed']+4.85)) for r in tracking)
        out[label]=dict(raw=len(selected),elapsed_s=dt,COM_distance_m=sum(math.dist(r['before_root_without_roads']['center'],r['root_without_roads']['center']) for r in selected),median_COM_speed_m_s=float(np.median(v)) if len(v) else None,positive_acceleration_raw=sum(math.hypot(*r['root_without_roads']['planar']['linear']['velocity'])>math.hypot(*r['before_root_without_roads']['planar']['linear']['velocity'])+.001 for r in selected),fullgas_command_raw=sum(r['action'][1]>.999 for r in selected),tracking_near_reference_within_point1_raw=sum(4.85-r['reference_overspeed']<.1 for r in tracking),tracking_near_force_within_point009_raw=sum(max(f['ratio'] for f in r['forces'])>1.05 for r in tracking),footprint_below_point6_raw=sum(r['margin']<.6 for r in selected),path_above2point9_raw=sum(r['path_error']>2.9 for r in selected),reference_ceiling_saturation_proxy_s=proxy)
    return out

def cross(rows,s):
    previous=0.;pt=0.
    for row in rows:
        v=row['progress'];t=row['episode_after_s']
        if previous<s<=v:return pt+(t-pt)*(s-previous)/(v-previous)
        previous=v;pt=t
    return None

def plane_cross(rows,path,station):
    """One fixed world plane, bracketed by saved raw endpoints; no physics."""
    arcs=np.asarray(path['arcs']);points=np.asarray(path['points'])
    j=int(np.searchsorted(arcs,station,side='right')-1)
    p0=points[j];p1=points[(j+1)%len(points)];tangent=(p1-p0)/np.linalg.norm(p1-p0)
    center=p0+(p1-p0)*(station-arcs[j])/path['ds'][j]
    for r in rows:
        if r['index']<=24 or abs(r['progress']-station)>10:continue
        before=np.asarray(r['before_root_without_roads']['center']);after=np.asarray(r['root_without_roads']['center'])
        lo=float((before-center)@tangent);hi=float((after-center)@tangent)
        if lo<0<=hi:
            fraction=-lo/(hi-lo);v0=np.asarray(r['before_root_without_roads']['planar']['linear']['velocity']);v1=np.asarray(r['root_without_roads']['planar']['linear']['velocity'])
            return dict(station_m=station,center=center.tolist(),forward_normal=tangent.tolist(),raw=r['raw'],hold=r['index'],earliest_s=r['episode_before_s'],latest_s=r['episode_after_s'],linear_interpolated_s=r['episode_before_s']+fraction*(r['episode_after_s']-r['episode_before_s']),interpolated_COM_speed_m_s=float(np.linalg.norm(v0+fraction*(v1-v0))))
    raise ValueError('saved plane crossing missing')

def main():
    cpu,wall=time.process_time(),time.perf_counter()
    def limit(*a):raise RuntimeError('578_READ_ONLY_ANALYSIS_CAP')
    signal.signal(signal.SIGPROF,limit);signal.signal(signal.SIGALRM,limit);signal.setitimer(signal.ITIMER_PROF,30);signal.setitimer(signal.ITIMER_REAL,45)
    try:
        current,seed,baseline,paths,static,branches=[read(INPUTS[k]) for k in ['current','seed573','551','paths','static','555branches']];path=paths['candidate'];rows=current['rows'][:660];oldrows=[];previous=static['root'];elapsed=0.
        for old in baseline['trace'][:661]:
            v=dict(old);before=elapsed;elapsed+=.02;v.update(episode_before_s=before,episode_after_s=elapsed,before_root_without_roads=previous,reference_overspeed=math.hypot(*old['root_without_roads']['planar']['linear']['velocity'])-old['target']);oldrows.append(v);previous=v['root_without_roads']
        official={'577':current['checkpoint']['tracker']['finish_time_s']-1.02,'551':baseline['source_tracker']['finish_time_s']-1.02}
        allocation_now=allocation(rows,path,static['obstacles']);allocation_old=allocation(oldrows,path,static['obstacles']);stations=[100,200,300,400,500,600,700,800,900];times={name:[cross(rr,s) for s in stations]+[official[name]] for name,rr in [('577',rows),('551',oldrows)]};intervals=[]
        prior={'577':0.,'551':0.}
        for i,label in enumerate([str(s) for s in stations]+['official_finish']):
            t={k:v[i] for k,v in times.items()};intervals.append(dict(end_station=label,current_elapsed_s=t['577']-prior['577'],baseline551_elapsed_s=t['551']-prior['551'],interval_delta_ms=1000*((t['577']-prior['577'])-(t['551']-prior['551'])),cumulative_delta_ms=1000*(t['577']-t['551'])));prior=t
        commands={v['index']:np.asarray(v['action']) for v in current['commands']};oldcommands={v['index']:np.asarray(v['action']) for v in seed['commands']};delta=np.asarray([commands[h]-oldcommands[h] for h in range(35,167)]);changed=np.flatnonzero(np.any(delta!=0,axis=1));signed=np.asarray([v[1]-v[2] for v in delta]);B=np.load(INPUTS['577basis'])['B'];T=np.load(INPUTS['574linear'])['T']*np.tile([.003,.03],132)
        basis=[]
        for k,b in enumerate(B):
            ids=slice(44*k,44*(k+1));den=sum(abs(T[ids]));basis.append(dict(window=[35+22*k,56+22*k],unquantized_gain_per_unit_s=-float(T@b),fraction_of_unconstrained_box_gradient=float(-(T@b)/den) if den else None))
        # Saved reference profile clock and555's optimistic branch are proxies only.
        ds=np.asarray(path['ds']);q=np.asarray(path['launch_squared']);vref=np.sqrt(q[:len(ds)]);nextref=np.sqrt(q[1:len(ds)+1]);vc=np.minimum(90.,vref+4.85);wn=np.minimum(90.,nextref+4.85);saved555=np.asarray([v['speed'] for v in branches]);clamped=np.minimum(saved555,vc);clock555=sum(2*ds/(saved555+np.roll(saved555,-1)));clock_clamped=sum(2*ds/(clamped+np.roll(clamped,-1)));profileclock=sum(2*ds/(vref+nextref));ceilingclock=sum(2*ds/(vc+wn))
        source_now=official['577'];out=dict(source_ticks=0,force_evaluations=0,native_actions=0,HOLDOUT=0,SEALED=0,new_calibrations=0,new_FD=0,LP_solves=0,nonlinear_solves=0,source_score_s=source_now,confirmation_excluded_raw=1,legacy551_normalization='Originaltracehasnoepisodeclock/beforeroot. Accumulate.02perraw;previouspostCOM/velocityusedonlyfordistance/acceleration. Officialfinishfromsavedterminaltracker,notunconfirmedcrossingrow.',phase_rule=dict(launch='existinghold1..24',avoidance='COMtodiskclearance<8m;proximitylabel,notcausalavoidancecost',corner='absfrozenpathcurvature>=.0125/m',recovery='within35marcafterlastturn/proximity,unlesshigherprioritylabel',straight='remainingnonlaunchincludingacceleration/coast/braking',priority=['launch','avoidance','corner','recovery','straight']),allocation_current=allocation_now,allocation551=allocation_old,paired_spatial_intervals=intervals,allocation_is_elapsed_not_recoverable_loss=True,reference_proxy_is_not_gain_or_bound=True,reference_saturation_proxy_total_s=sum(v['reference_ceiling_saturation_proxy_s'] for v in allocation_now.values()),command_change=dict(changed_holds=len(changed),first_changed_hold=int(changed[0]+35),last_changed_hold=int(changed[-1]+35),maximum_steer_rad=float(max(abs(delta[:,0]))),rms_steer_rad=float(np.sqrt(np.mean(delta[:,0]**2))),maximum_signed_pedal=float(max(abs(signed))),rms_signed_pedal=float(np.sqrt(np.mean(signed**2))),maximum_steer_as_fraction_of_point4=float(max(abs(delta[:,0]))/.4)),basis_opportunity=basis,nominal_six_basis_radius_point012_linear_gain_s=.012*sum(abs(T@b) for b in B),clock_proxies=dict(saved551_profile_s=float(profileclock),reference_plus4point85_COMcap90_s=float(ceilingclock),saved555_unreachable_continuous_s=float(clock555),saved555_clamped_to_same_reference_cap90_s=float(clock_clamped),all_are_nonphysical_diagnostic_clocks=True),target=dict(to11point99_gap_source_s=source_now-11.99,required_same_distance_average_speed_increase=source_now/11.99-1,verified_one_second_recoverable_gain_evidence=False),checks=dict(phase_time_sums_to_score=abs(sum(v['elapsed_s'] for v in allocation_now.values())-source_now)<1e-9,source_score13point20=abs(source_now-13.2)<1e-9,all_common_spatial_gates_present=all(x is not None for values in times.values() for x in values),prefix136_exact=all(rows[i]['root_without_roads']==oldrows[i]['root_without_roads'] and rows[i]['forces']==oldrows[i]['forces'] for i in range(136)),original_first34_commands_fixed=all(commands[h].tolist()==oldcommands[h].tolist() for h in range(1,35))),input_sha256={k:sha(v) for k,v in INPUTS.items()},analysis_CPU_s=time.process_time()-cpu,analysis_wall_s=time.perf_counter()-wall)
        out['clock_proxies']['reference_plus4point85_without90cap_s']=float(sum(2*ds/(vref+nextref+9.7)))
        out['fixed_plane_baselines']=[plane_cross(rows,path,station) for station in [200.,300.]]
        out['read_only_recovery']={'legacy_schema_failure_preserved_private':True,'new_source_calls':0,'conservative_failed_attempt_CPU_wall_charge_s':1}
        out['pre_final_read_only_preparation_CPU_wall_charge_s']=5
        out['analysis_CPU_including_preparation_charge_s']=time.process_time()-cpu+5
        out['analysis_wall_including_preparation_charge_s']=time.perf_counter()-wall+5
        assert all(out['checks'].values());(ROOT/'retry/reframe578_analysis.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(out)
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)

if __name__=='__main__':main()
