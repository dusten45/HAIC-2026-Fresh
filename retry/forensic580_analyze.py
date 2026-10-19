"""Stored-event graph forensics only. No dynamics/source/optimizer imports."""
import copy,hashlib,json,math,signal,time
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response580-private')
INPUTS={'journal':Path('/workspace/haic-response579-private/raw-journal-private.jsonl'),'prefix':Path('/workspace/haic-response579-private/prefix-checkpoint-private.json'),'terminals':Path('/workspace/haic-response579-private/A-terminals-private.json'),'baseline':Path('/workspace/haic-response577-private/final-independent-tape-private.json'),'path':Path('/workspace/haic-response551-private/frozen-paths-private.json'),'result579':G/'retry/beam579_result.json','contract579':G/'retry/beam579_contract.json'}
def rd(p):return json.loads(p.read_text())
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def physical(root):
    x=copy.deepcopy(root);x['planar'].pop('steer',None);return x

def project(position,path,previous):
    # Arithmetic-only copy of frozen projection; checks recorded ranking, not a rollout.
    rows=[];L=path['length']
    for i,a in enumerate(path['points']):
        b=path['points'][(i+1)%len(path['points'])];dx,dy=b[0]-a[0],b[1]-a[1];d=dx*dx+dy*dy;t=max(0.,min(1.,((position[0]-a[0])*dx+(position[1]-a[1])*dy)/d));p=(a[0]+t*dx,a[1]+t*dy);s=path['arcs'][i]+t*math.sqrt(d);s+=round((previous-s)/L)*L
        if previous-5<=s<=previous+30:rows.append(dict(s=s,distance=math.dist(position,p),tangent=(dx/math.sqrt(d),dy/math.sqrt(d))))
    return min(rows,key=lambda x:x['distance'])

def enumeration(parent,path,factual):
    # Reconstruct enumeration metadata for logged edges only; no new candidate evaluated.
    root=parent['root'];q=project(root['center'],path,parent['progress']);s=q['s']+max(7.,.3*math.hypot(*root['planar']['linear']['velocity']));u=s%path['length'];j=next((i for i in range(len(path['ds'])) if path['arcs'][i+1]>=u),len(path['ds'])-1);f=(u-path['arcs'][j])/path['ds'][j];p=tuple(path['points'][j][k]+f*(path['points'][(j+1)%len(path['points'])][k]-path['points'][j][k]) for k in range(2));v=np.asarray(path['points'][(j+1)%len(path['points'])])-path['points'][j];v=v/np.linalg.norm(v);normal=(-v[1],v[0]);a=root['planar']['angle'];out=[]
    for offset in [-.75,0.,.75]:
        dx,dy=[p[k]+offset*normal[k]-root['center'][k] for k in range(2)];delta=math.atan(6.48*(-math.sin(a)*dy-math.cos(a)*dx)/(dx*dx+dy*dy));steer=float(np.float32(-max(-.4,min(.4,delta))))
        for gas,brake in [(1,0),(0,0),(0,.125),(0,.25)]:out.append(np.asarray([steer,gas,brake],np.float32))
    out.append(np.asarray(factual,np.float32));seen=set();unique=[]
    for i,a in enumerate(out):
        key=a.tobytes()
        if key not in seen:seen.add(key);unique.append((i,a.tolist(),key==np.asarray(factual,np.float32).tobytes()))
    return unique

def state_key(n):return digest(dict(root=physical(n['root']),tracking=n['tracking'],launch=n['launch'],progress=n['progress'],global_raw=n['global_raw']))
def features(root,progress,tracking,path):
    p=root['planar'];v=p['linear']['velocity'];q=project(root['center'],path,progress);t=q['tangent'];normal=(-t[1],t[0]);rear=p['linear']['wheels'][2:];slips=[]
    for w in rear:
        forward=(-math.sin(w['heading']),math.cos(w['heading']));speed=sum((v[j]+w['offset'][j])*forward[j] for j in range(2));slips.append(.54*w['omega']-speed)
    return dict(progress_m=progress,speed_m_s=math.hypot(*v),forward_speed_m_s=sum(v[j]*t[j] for j in range(2)),lateral_speed_m_s=sum(v[j]*normal[j] for j in range(2)),yaw_rad_s=p['yaw'],angle_rad=p['angle'],front_joint_mean_rad=sum(p['joints'][:2])/2,front_rate_mean_rad_s=sum(p['rates'][:2])/2,rear_omega_mean_rad_s=sum(w['omega'] for w in rear)/2,rear_gas_mean=sum(w['gas'] for w in rear)/2,rear_slip_mean_m_s=sum(slips)/2,clipped_samples=tracking[0],tracking_samples=tracking[1],tracking_clip_fraction=tracking[0]/tracking[1] if tracking[1] else 0.)

def summarize(values):
    a=np.asarray(values,float)
    return dict(n=len(a),min=float(np.min(a)),p10=float(np.quantile(a,.1)),median=float(np.median(a)),p90=float(np.quantile(a,.9)),max=float(np.max(a))) if len(a) else {'n':0}

def main():
    cpu,wall=time.process_time(),time.perf_counter()
    def cap(*a):raise RuntimeError('580_READ_ONLY_ANALYSIS_CAP')
    signal.signal(signal.SIGPROF,cap);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.setitimer(signal.ITIMER_REAL,45)
    D.mkdir(mode=0o700,exist_ok=False)
    try:
        inputs={k:sha(p) for k,p in INPUTS.items()};(G/'retry/forensic580_contract.json').write_text(json.dumps(dict(study=580,scope='Read-only stored579 event/decision-graph analysis; no source/native/FD/optimizer/reintegration',caps={'CPU_s':30,'wall_s':45},input_sha256=inputs,source_ticks=0,native_actions=0,FD=0,optimizer=0,HOLDOUT=0,SEALED=0),indent=2)+'\n')
        baseline=rd(INPUTS['baseline']);path=rd(INPUTS['path'])['candidate'];old={r['index']:r['action'] for r in baseline['commands']};base_rows=baseline['rows'];prefix=rd(INPUTS['prefix']);start=dict(root=prefix['root_without_roads'],tracking=prefix['tracking'],launch=prefix['launch'],progress=prefix['progress'],global_raw=prefix['global_raw'],ids=[],factual=True,first_command_diff=None,first_physical_diff=None,first_history_diff=None)
        edges=[];recorded_depths=[];active=None;current=None;seq=0;head='0'*64
        for line in INPUTS['journal'].open():
            row=json.loads(line);own=row.pop('sha256');assert row['sequence']==seq and row['previous']==head and digest(row)==own;seq+=1;head=own;kind=row['kind']
            if kind=='BEFORE_FORCE':
                if row['context']['bucket']!='search':active=current=None;continue
                if row['context']['raw']==1:active=dict(rows=[],index=row['context']['index'],failure=None,edge=len(edges));edges.append(active)
                assert active is not None and active['index']==row['context']['index'];current=dict(before=row['root'],action=row['action'],history_before=row['history'],context=row['context']);active['rows'].append(current)
            elif kind=='FORCE_VERDICT' and current is not None:
                current.update(forces=row['forces'],history=row['proposed_history'],force_event=own)
                if row['gate']:active['failure']=row['gate']
            elif kind=='AFTER_TICK' and current is not None:
                assert current['force_event']==row['force_event'];current.update(after=row['root'],body=row['body'])
            elif kind=='RAW_VERDICT' and current is not None:
                assert current['force_event']==row['force_event'];current.update(progress=row['progress'],margin=row['margin'],path_error=row['path_error'],reference_overspeed=row['reference_overspeed'],failures=row['failures'])
                if row['failures']:active['failure']=row['failures'][0]
            elif kind=='BEAM_DEPTH':recorded_depths.append({k:row[k] for k in ['stage','depth','live','terminals','factual_frozen']})
        live=[start];cursor=0;parents=[];allnodes=[];depths=[];terminals=[];factual_frozen=False;raw_first_diff=Counter();action_first_diff=Counter();history_first_diff=Counter();fail_counts=Counter();fail_by_hold=defaultdict(Counter);fail_by_raw=defaultdict(Counter);fail_by_mode=defaultdict(Counter);servo=Counter()
        baseline_features={r['global_raw_after']:features(r['root_without_roads'],r['progress'],r['proposed_history'] if r['index']>24 else [0,0],path) for r in base_rows[96:196]}
        for depth,logged in enumerate(recorded_depths,1):
            candidates=[];protected=None;depth_nodes=[]
            for parent_slot,parent in enumerate(live):
                pid=len(parents);record=dict(instance=pid,depth=depth,hold=24+depth,slot=parent_slot,factual=parent['factual'],state_key=state_key(parent),ids=parent['ids'],failures=Counter(),safe_children=0,feature=features(parent['root'],parent['progress'],parent['tracking'],path));parents.append(record)
                for enum_id,action,fact_action in enumeration(parent,path,old[24+depth]):
                    edge=edges[cursor];cursor+=1;assert edge['index']==24+depth
                    assert np.asarray(action,np.float32).tobytes()==np.asarray(edge['rows'][0]['action'],np.float32).tobytes()
                    assert physical(edge['rows'][0]['before'])==physical(parent['root']) and edge['rows'][0]['history_before']==parent['tracking'] and edge['rows'][0]['context']['global_raw']==parent['global_raw']
                    edge.update(parent_instance=pid,depth=depth,enum_id=enum_id,ids=parent['ids']+[enum_id],factual=parent['factual'] and fact_action,parent_key=record['state_key'])
                    firstcommand=parent['first_command_diff']
                    if firstcommand is None and np.asarray(action,np.float32).tobytes()!=np.asarray(old[edge['index']],np.float32).tobytes():firstcommand=edge['index']
                    firstphysical=parent['first_physical_diff'];firsthistory=parent['first_history_diff']
                    for raw in edge['rows']:
                        if 'after' not in raw:continue
                        gr=raw['context']['global_raw']+1;reference=base_rows[gr-1]
                        if firstphysical is None and physical(raw['after'])!=physical(reference['root_without_roads']):firstphysical=gr
                        if firsthistory is None and raw['history']!=reference['proposed_history']:firsthistory=gr
                        p=raw['before']['planar'];err=[p['steer']-j for j in p['joints'][:2]];servo['front_joint_evaluations']+=2;servo['rate_saturated_front_joints']+=sum(abs(e)>=.06 for e in err)
                    edge.update(first_command_diff=firstcommand,first_physical_diff=firstphysical,first_history_diff=firsthistory)
                    if firstcommand is not None:action_first_diff[firstcommand]+=1
                    if firstphysical is not None:raw_first_diff[firstphysical]+=1
                    if firsthistory is not None:history_first_diff[firsthistory]+=1
                    if edge['failure']:
                        failure=edge['failure'];fail_counts[failure]+=1;fail_by_hold[failure][edge['index']]+=1;fail_by_raw[failure][edge['rows'][-1]['context']['global_raw']+1]+=1;mode='factual_action' if enum_id==12 else ['lane_minus','lane_zero','lane_plus'][enum_id//4]+'_'+['gas1','coast','brake125','brake25'][enum_id%4];fail_by_mode[failure][mode]+=1;record['failures'][failure]+=1;continue
                    assert len(edge['rows'])==4;last=edge['rows'][-1];record['safe_children']+=1
                    node=dict(root=last['after'],tracking=last['history'],launch=parent['launch'],progress=last['progress'],global_raw=last['context']['global_raw']+1,ids=edge['ids'],factual=edge['factual'],first_command_diff=firstcommand,first_physical_diff=firstphysical,first_history_diff=firsthistory,edge=edge['edge'],parent_instance=pid)
                    node['feature']=features(node['root'],node['progress'],node['tracking'],path);node['delta']={k:node['feature'][k]-baseline_features[node['global_raw']][k] for k in node['feature']};node['key']=state_key(node)
                    edge['safe_node']=len(allnodes);allnodes.append(node);depth_nodes.append(node)
                    # Logged stage25 has every safe edge terminal; assert against stored terminals later.
                    if depth==25:node['classification']='terminal';terminals.append(node);factual_frozen|=node['factual']
                    elif node['factual']:node['classification']='protected';protected=node
                    else:candidates.append(node)
            candidates.sort(key=lambda n:(-n['progress'],-n['feature']['forward_speed_m_s'],tuple(n['ids'])))
            for i,n in enumerate(candidates):n['classification']='retained' if i<3 else 'width_pruned'
            live=candidates[:3]
            if protected is not None:live.append(protected)
            assert len(live)==logged['live'] and len(terminals)==logged['terminals'] and factual_frozen==logged['factual_frozen']
            keys=[n['key'] for n in live];ref=base_rows[4*(24+depth)-1];referencekey=digest(dict(root=physical(ref['root_without_roads']),tracking=ref['proposed_history'],launch=prefix['launch'],progress=ref['progress'],global_raw=ref['global_raw_after']))
            depths.append(dict(depth=depth,hold=24+depth,safe_children=len(depth_nodes),live=len(live),unique_live_available_state_keys=len(set(keys)),live_equal_factual_available_state=sum(k==referencekey for k in keys),live_minmax_delta={k:[min((n['delta'][k] for n in live),default=None),max((n['delta'][k] for n in live),default=None)] for k in ['progress_m','speed_m_s','yaw_rad_s','rear_omega_mean_rad_s','clipped_samples']},safe_span={k:max(n['feature'][k] for n in depth_nodes)-min(n['feature'][k] for n in depth_nodes) for k in depth_nodes[0]['feature']}))
        assert cursor==len(edges)==1258 and len(parents)==97 and len(allnodes)==750
        stored=rd(INPUTS['terminals'])['terminals'];assert [n['ids'] for n in terminals]==[n['ids'] for n in stored]
        assert all(n['root']==t['checkpoint']['root_without_roads'] and n['tracking']==t['checkpoint']['tracking'] and n['progress']==t['checkpoint']['progress'] for n,t in zip(terminals,stored))
        groups={name:[n for n in allnodes if n['classification']==name] for name in ['protected','retained','width_pruned','terminal']};groupstats={}
        meaningful={'progress_m':.01,'speed_m_s':.1,'yaw_rad_s':.01,'angle_rad':.001,'front_joint_mean_rad':.001,'rear_omega_mean_rad_s':1.,'rear_slip_mean_m_s':.1,'clipped_samples':.5}
        for name,nodes in groups.items():groupstats[name]=dict(n=len(nodes),unique_available_state_keys=len({n['key'] for n in nodes}),delta_distributions={k:summarize([n['delta'][k] for n in nodes]) for k in nodes[0]['delta']},descriptive_nontrivial_delta_counts={k:sum(abs(n['delta'][k])>threshold for n in nodes) for k,threshold in meaningful.items()})
        parentkeys={p['state_key'] for p in parents};pruned=groups['width_pruned'];slow=[n for n in pruned if n['delta']['progress_m']<-.01];headroom=[n for n in slow if n['delta']['clipped_samples']<0 or abs(n['feature']['yaw_rad_s'])+ .01<abs(baseline_features[n['global_raw']]['yaw_rad_s'])]
        concentrations={}
        for reason in ['FORCE','REFERENCE']:
            ranked=sorted([p for p in parents if p['failures'][reason]],key=lambda p:(-p['failures'][reason],p['instance']));byphysical=Counter()
            for p in parents:byphysical[p['state_key']]+=p['failures'][reason]
            concentrations[reason]=dict(total=fail_counts[reason],parent_instances_affected=len(ranked),unique_available_parent_states_affected=sum(v>0 for v in byphysical.values()),top5_instance_fraction=sum(p['failures'][reason] for p in ranked[:5])/fail_counts[reason],top5_available_state_fraction=sum(sorted(byphysical.values(),reverse=True)[:5])/fail_counts[reason],top_parent_instances=[dict(instance=p['instance'],hold=p['hold'],slot=p['slot'],factual=p['factual'],failures=p['failures'][reason],safe_children=p['safe_children']) for p in ranked[:10]],by_hold=dict(sorted(fail_by_hold[reason].items())),by_global_raw=dict(sorted(fail_by_raw[reason].items())),by_action_mode=dict(fail_by_mode[reason]))
        launch=[]
        for h in range(1,25):
            rr=base_rows[4*(h-1):4*h];launch.append(dict(hold=h,command_gas=old[h][1],command_brake=old[h][2],clipped_wheel_samples=sum(f['clipped'] for r in rr for f in r['forces']),max_force=max(f['ratio'] for r in rr for f in r['forces']),end_speed_m_s=math.hypot(*rr[-1]['root_without_roads']['planar']['linear']['velocity']),end_progress_m=rr[-1]['progress']))
        launchgroups=[]
        for lo,hi in [(1,6),(7,16),(17,24)]:
            z=launch[lo-1:hi];launchgroups.append(dict(holds=[lo,hi],elapsed_s=.08*len(z),mean_command_gas=sum(v['command_gas'] for v in z)/len(z),clipped_wheel_samples=sum(v['clipped_wheel_samples'] for v in z),max_force=max(v['max_force'] for v in z),end_speed_m_s=z[-1]['end_speed_m_s']))
        launchsummary=dict(groups=launchgroups,total_clipped_samples=sum(v['clipped_wheel_samples'] for v in launch),total_wheel_samples=384,maximum_legal_integer_clips=57,remaining_integer_clips=57-sum(v['clipped_wheel_samples'] for v in launch),interpretation='Current launch already540-derived and near clipping budget, not an untouched fixed-gas baseline. No remaining lap-time gain inferred.')
        out=dict(study=580,source_ticks=0,native_actions=0,FD=0,optimizer=0,HOLDOUT=0,SEALED=0,method='Recorded decision graph reconstruction: parse stored roots and force/history verdicts; recompute frozen geometric enumeration/ranking metadata only; no source dynamics or trajectory reintegration.',identity_limit='Available-state keys include physical root excluding overwritten steer target, launch/tracking counts, progress and raw. Tracker and visited set are not in every journal event; do not claim full checkpoint/future equivalence.',checks=dict(full_journal_chain=True,all1258_edges_assigned=True,all97_parent_enumerations_and_initial_roots_exact=True,all25_recorded_live_counts_and_terminal_counts_exact=True,all52_terminal_ids_and_recorded_roots_histories_progress_exact=True,all750_safe_children_classified=True),event_count=seq,edge_count=len(edges),parent_instances=len(parents),unique_available_parent_states=len(parentkeys),classifications=groupstats,depths=depths,first_divergence=dict(command_hold=dict(sorted(action_first_diff.items())),physical_raw=dict(sorted(raw_first_diff.items())),tracking_history_raw=dict(sorted(history_first_diff.items())),counts_with_any_command_difference=sum(e['first_command_diff'] is not None for e in edges),counts_with_any_physical_difference=sum(e['first_physical_diff'] is not None for e in edges)),servo_counts=dict(servo),failure_concentration=concentrations,ranking_evidence=dict(width_pruned=len(pruned),slower_than_factual_by_more_than1cm=len(slow),slower_and_lower_clip_count_or_abs_yaw=len(headroom),pruned_available_state_key_later_appears_as_expanded_parent=sum(n['key'] in parentkeys for n in pruned),unobserved_distinct_pruned_available_states=len({n['key'] for n in pruned if n['key'] not in parentkeys}),observed_later_gain_from_strictly_slower_pruned_state=False,interpretation='Slow physically different safe states were removed. Better future corner/time outcomes of those discarded states were not observed; yaw/clipping headroom is a descriptor, not verified future usefulness.'),launch_summary=launchsummary,input_sha256=inputs)
        # Full derived graph remains private; public output contains aggregates only.
        (D/'derived-graph-private.json').write_text(json.dumps(dict(edges=edges,parents=parents,nodes=allnodes),allow_nan=False)+'\n')
        out['analysis_CPU_s']=time.process_time()-cpu;out['analysis_wall_s']=time.perf_counter()-wall
        (G/'retry/forensic580_analysis.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(json.dumps({k:out[k] for k in ['edge_count','parent_instances','unique_available_parent_states','ranking_evidence','servo_counts','analysis_CPU_s','analysis_wall_s']},indent=2))
    except BaseException as exc:
        (D/'failure-private.json').write_text(json.dumps(dict(error=type(exc).__name__+':'+str(exc),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall))+'\n');raise
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
