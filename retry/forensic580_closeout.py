"""Read-only enrichment and one unexecuted experiment contract; no dynamics imports."""
import json,math,hashlib,time,signal
from pathlib import Path
from collections import Counter
import numpy as np
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response580-private')
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def lateral(root):
    v=root['planar']['linear']['velocity'];values=[]
    for w in root['planar']['linear']['wheels']:
        f=(-math.sin(w['heading']),math.cos(w['heading']));side=(f[1],-f[0]);values.append(abs(82.*sum((v[j]+w['offset'][j])*side[j] for j in range(2)))/w['friction'])
    return values

def main():
    cpu,wall=time.process_time(),time.perf_counter()
    def cap(*a):raise RuntimeError('580_READ_ONLY_CLOSEOUT_CAP')
    signal.signal(signal.SIGPROF,cap);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_PROF,10);signal.setitimer(signal.ITIMER_REAL,15)
    try:
        a=rd(G/'retry/forensic580_analysis.json');graph=rd(D/'derived-graph-private.json');edges,nodes,parents=[graph[k] for k in ['edges','nodes','parents']];baseline=rd(Path('/workspace/haic-response577-private/final-independent-tape-private.json'));old={r['index']:r['action'] for r in baseline['commands']}
        # Base analyzer publishes only three launch aggregates, never a command tape.
        assert 'launch_summary' in a and 'launch_profile' not in a
        force=[e for e in edges if e['failure']=='FORCE'];peak=Counter();lateral_only=0;rawin=Counter()
        for e in force:
            r=e['rows'][-1];peak[max(range(4),key=lambda j:r['forces'][j]['ratio'])]+=1;rawin[r['context']['raw']]+=1;lateral_only+=max(lateral(r['before']))>1.059
        dead=[]
        for p in parents:
            ee=[e for e in edges if e['parent_instance']==p['instance']]
            if p['hold']==32 and not p['factual']:
                assert len(ee)==13 and all(e['failure']=='FORCE' and e['rows'][-1]['context']['raw']==2 for e in ee)
                bounds=[max(lateral(e['rows'][-1]['before'])) for e in ee];dead.append(dict(parent_instance=p['instance'],all13_fail_raw=2,lateral_component_ratio_at_failed_raw_min=min(bounds),max=max(bounds)))
        a['failure_mechanism']=dict(force_peak_wheel_counts=dict(peak),force_failure_raw_within_hold=dict(rawin),force_failures_lateral_component_alone_above1point059=lateral_only,first_wall_hold32=dead,interpretation='All39loggedchildren of three fast parents fail raw2. Lateral component is arithmetic on their already recorded states; no new force_rows/wheel_response call. Does not prove unseen steering actions fail or alignment succeeds.')
        # A matched sibling example, selected from stored graph before any new experiment.
        slow=next(n for n in nodes if n['edge']==275);fast=next(n for n in nodes if n['edge']==274);assert slow['parent_instance']==fast['parent_instance']==21 and slow['classification']=='width_pruned' and fast['classification']=='retained'
        assert edges[274]['rows'][0]['action'][0]==edges[275]['rows'][0]['action'][0] and edges[274]['rows'][0]['action'][1]==edges[275]['rows'][0]['action'][1] and edges[274]['rows'][0]['action'][2]!=edges[275]['rows'][0]['action'][2]
        a['matched_preparation_example']=dict(parent_instance=21,hold=31,fast_edge=274,pruned_edge=275,shared_prefix_and_steering=True,only_last_pedal_differs=True,pruned_minus_retained={k:slow['feature'][k]-fast['feature'][k] for k in ['progress_m','speed_m_s','yaw_rad_s','rear_omega_mean_rad_s','clipped_samples']},pruned_progress_vs_factual_m=slow['delta']['progress_m'],max_lateral_component_ratio_pruned=max(lateral(slow['root'])),max_lateral_component_ratio_retained=max(lateral(fast['root'])),retained_next_hold_all13_failed=True,discarded_future_unobserved=True)
        selected=next(p for p in parents if p['instance']==25);pathids=selected['ids'];prefix=[]
        for depth in range(1,len(pathids)+1):
            e=next(e for e in edges if e['ids']==pathids[:depth]);assert not e['failure'] and len(e['rows'])==4;prefix.append(e)
        assert len(prefix)==7 and prefix[-1]['rows'][-1]['context']['global_raw']+1==124
        root=prefix[-1]['rows'][-1]['after'];v=root['planar']['linear']['velocity'];theta=[]
        for w in root['planar']['linear']['wheels'][:2]:
            vi=[v[j]+w['offset'][j] for j in range(2)];assert math.hypot(*vi)>1e-12;theta.append(math.atan2(-vi[0],vi[1]))
        sy=sum(math.sin(t) for t in theta);cx=sum(math.cos(t) for t in theta);assert math.hypot(sy,cx)>1e-12
        q=math.atan2(math.sin(math.atan2(sy,cx)-root['planar']['angle']),math.cos(math.atan2(sy,cx)-root['planar']['angle']));action=[float(np.float32(-max(-.4,min(.4,q)))),*old[32][1:]];oldedges=[e for e in edges if e['parent_instance']==25];duplicate=any(np.asarray(e['rows'][0]['action'],np.float32).tobytes()==np.asarray(action,np.float32).tobytes() for e in oldedges)
        commands=[dict(index=h,action=old[h]) for h in range(1,25)]+[dict(index=e['index'],action=e['rows'][0]['action']) for e in prefix]
        target=D/'selected-prefix-private.json';assert not target.exists();target.write_text(json.dumps(dict(parent_instance=25,commands=commands,branch_expected_rows=[r for e in prefix for r in e['rows']],baseline_prefix_input='/workspace/haic-response577-private/final-independent-tape-private.json',expected_available_end_state=dict(root=root,tracking=prefix[-1]['rows'][-1]['history'],progress=prefix[-1]['rows'][-1]['progress'],global_raw=124),full_tracker_visited_not_logged_in_branch='Rebuild by fresh original initial-source prefix; do not fabricate a stored full checkpoint or transplant pose.'),allow_nan=False)+'\n')
        a['selected_next_intervention']=dict(changed_assumption='Pursuit target required for short-horizon steering; replace it by full-state wheel-slip alignment feedback only for two holds.',method_family='Mechanical slip-regulating steering feedback, not a larger pursuit beam or a velocity-frame pursuit.',selected_parent_instance=25,selection_rule='Largest progress among the three first hold32competitiveparents whose13children allfailedraw2; tie lower instance. Fixed using stored579only.',prefix_raw=124,current_parent_progress_m=selected['feature']['progress_m'],current_parent_speed_m_s=selected['feature']['speed_m_s'],first_alignment_action_is_duplicate_of_old13=duplicate,first_alignment_steer_outside_old13_steer_range=not min(e['rows'][0]['action'][0] for e in oldedges)<=action[0]<=max(e['rows'][0]['action'][0] for e in oldedges),steering_distance_to_nearest_old_steer_rad=min(abs(action[0]-e['rows'][0]['action'][0]) for e in oldedges),private_prefix_sha256=sha(target),hypothesis_limits='No next trajectory simulated. Common two-wheel heading target is not exact simultaneous alignment or guaranteed force reduction; servo/joint/yaw reaction and corridor may invalidate it.')
        assert not duplicate
        # Public aggregates only. Actual commands and states stay in selected-prefix-private.
        a['closeout_CPU_s']=time.process_time()-cpu;a['closeout_wall_s']=time.perf_counter()-wall;a['auxiliary_reads_and_final_writer_conservative_CPU_wall_charge_s']=2.;a['aggregate_CPU_s']=a['analysis_CPU_s']+a['closeout_CPU_s']+2.;a['aggregate_wall_s']=a['analysis_wall_s']+a['closeout_wall_s']+2.;a['checks']['no_raw_launch_commands_in_public']=True
        (G/'retry/forensic580_analysis.json').write_text(json.dumps(a,indent=2,allow_nan=False)+'\n')
        print(json.dumps({k:a[k] for k in ['failure_mechanism','matched_preparation_example','selected_next_intervention','launch_summary','aggregate_CPU_s','aggregate_wall_s']},indent=2))
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
