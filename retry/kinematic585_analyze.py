"""585 stored-state kinematics and geometry only. No dynamics imports or rollouts."""
import ast,copy,hashlib,json,math,signal,time
from collections import Counter
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response585-recovery-private')
INPUTS={'graph580':Path('/workspace/haic-response580-private/derived-graph-private.json'),'prefix580':Path('/workspace/haic-response580-private/selected-prefix-private.json'),'factual577':Path('/workspace/haic-response577-private/final-independent-tape-private.json'),'escape581':Path('/workspace/haic-response581-private/verified-tape-private.json'),'journal583':Path('/workspace/haic-response583-private/raw-journal-private.jsonl'),'checkpoint583':Path('/workspace/haic-response583-private/prefix-checkpoint-private.json'),'actual584':Path('/workspace/haic-response584-private/run-tape-private.json'),'paths':Path('/workspace/haic-response551-private/frozen-paths-private.json'),'static':Path('/workspace/haic-response515-private/collected-map-state-private.json'),'result584':G/'retry/cone584_result.json'}
SOURCE_REFS=['core/vendor/car_dynamics.py','retry/plan513_model.py','retry/brake506_geometry.py','retry/lap518_control.py','retry/brake504_planar.py','retry/plan512_control.py','retry/closure524_control.py']
COUNTS=Counter()
def rd(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def wrap(x):return math.atan2(math.sin(x),math.cos(x))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def pp(p,a,b):
    z=sub(b,a);d=dot(z,z);t=max(0.,min(1.,dot(sub(p,a),z)/d)) if d else 0.;return [a[j]+t*z[j] for j in range(2)]
def bounds(poly):return [min(p[0] for p in poly),max(p[0] for p in poly),min(p[1] for p in poly),max(p[1] for p in poly)]
def project(pos,path,previous):
    rows=[]
    for i,a in enumerate(path['points']):
        b=path['points'][(i+1)%len(path['points'])];q=pp(pos,a,b);t=math.dist(a,q)/path['ds'][i];s=path['arcs'][i]+t*path['ds'][i];s+=round((previous-s)/path['length'])*path['length']
        if previous-5<=s<=previous+30:
            tangent=[(b[j]-a[j])/path['ds'][i] for j in range(2)];normal=[-tangent[1],tangent[0]];rows.append(dict(s=s,segment=i,point=q,tangent=tangent,normal=normal,distance=math.dist(pos,q),signed=dot(sub(pos,q),normal)))
    return min(rows,key=lambda q:q['distance'])
def constants():
    want={'SIZE','WHEELPOS','HULL_POLY1','HULL_POLY2','HULL_POLY3','HULL_POLY4'};out={}
    for node in ast.parse((G/'core/vendor/car_dynamics.py').read_text()).body:
        if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in want:out[node.targets[0].id]=ast.literal_eval(node.value)
    assert set(out)==want;return out

def polygons(root,c):
    p=root['planar'];ca,sa=math.cos(p['angle']),math.sin(p['angle']);rot=lambda q:[ca*q[0]-sa*q[1],sa*q[0]+ca*q[1]];origins=[]
    for lever,(wx,wy) in zip(p['levers'],c['WHEELPOS']):
        r=rot((wx*c['SIZE'],wy*c['SIZE']));origins.append([root['center'][j]+lever[j]-r[j] for j in range(2)])
    origin=[sum(o[j] for o in origins)/4 for j in range(2)];out=[]
    for k in range(1,5):out.append([[origin[j]+rot((x*c['SIZE'],y*c['SIZE']))[j] for j in range(2)] for x,y in c['HULL_POLY'+str(k)]])
    for lever,w in zip(p['levers'],p['linear']['wheels']):
        ca,sa=math.cos(w['heading']),math.sin(w['heading']);center=[root['center'][j]+lever[j] for j in range(2)];out.append([[center[0]+ca*x-sa*y,center[1]+sa*x+ca*y] for x,y in [(-.28,-.54),(.28,-.54),(.28,.54),(-.28,.54)]])
    return out

def nearest_body_boundary(root,static,c,edge_bounds):
    ps=polygons(root,c);best=(math.inf,None,None,None,None)
    for bi,poly in enumerate(ps):
        box=bounds(poly)
        for ei,((a,b),eb) in enumerate(zip(static['boundary'],edge_bounds)):
            lower=math.hypot(max(0.,eb[0]-box[1],box[0]-eb[1]),max(0.,eb[2]-box[3],box[2]-eb[3]))
            if lower>=best[0]:continue
            for p in poly:
                q=pp(p,a,b);dist=math.dist(p,q)
                if dist<best[0]:best=(dist,bi,ei,p,q)
            for endpoint in [a,b]:
                for p,q in zip(poly,poly[1:]+poly[:1]):
                    bp=pp(endpoint,p,q);dist=math.dist(endpoint,bp)
                    if dist<best[0]:best=(dist,bi,ei,bp,endpoint)
    gap,bi,ei,bodypoint,edgepoint=best;a,b=static['boundary'][ei];length=math.dist(a,b);t=[(b[j]-a[j])/length for j in range(2)];normal=[-t[1],t[0]]
    if dot(sub(root['center'],edgepoint),normal)<0:normal=[-x for x in normal]
    p=root['planar'];v=p['linear']['velocity'];lever=sub(bodypoint,root['center']);velocity=[v[0]-p['yaw']*lever[1],v[1]+p['yaw']*lever[0]]
    if bi>=4:
        i=bi-4;local=sub(bodypoint,[root['center'][j]+p['levers'][i][j] for j in range(2)]);w=p['linear']['wheels'][i];rate=p['yaw']+p['rates'][i];velocity=[v[0]+w['offset'][0]-rate*local[1],v[1]+w['offset'][1]+rate*local[0]]
    closing=-dot(velocity,normal);center_gap=dot(sub(root['center'],edgepoint),normal)
    return dict(gap_m=gap,body_index=bi,edge_index=ei,boundary_tangent=t,inward_normal=normal,COM_normal_closing_m_s=-dot(v,normal),critical_point_normal_closing_m_s=closing,COM_signed_line_distance_m=center_gap,frozen_first_order_floor_time_s=(gap-.5)/closing if closing>0 else None,body_point_velocity_world_m_s=velocity),ps

def feature(root,progress,history,static,path,c,eb,expected_margin=None):
    COUNTS['static_state_features']+=1;p=root['planar'];v=p['linear']['velocity'];q=project(root['center'],path,progress);geom,_=nearest_body_boundary(root,static,c,eb);heading=math.atan2(v[1],v[0]);ph=math.atan2(q['tangent'][1],q['tangent'][0]);body=p['angle']+math.pi/2;wheels=[]
    for w in p['linear']['wheels']:
        vi=[v[j]+w['offset'][j] for j in range(2)];vf=-math.sin(w['heading'])*vi[0]+math.cos(w['heading'])*vi[1];vs=math.cos(w['heading'])*vi[0]+math.sin(w['heading'])*vi[1]
        wheels.append(dict(forward_heading_rad=wrap(w['heading']+math.pi/2),velocity_heading_rad=math.atan2(vi[1],vi[0]),slip_heading_rad=wrap(math.atan2(vi[1],vi[0])-w['heading']-math.pi/2),lateral_speed_m_s=vs,rolling_slip_m_s=.54*w['omega']-vf,frozen_lateral_component_ratio=abs(82*vs)/w['friction'],friction_N=w['friction']))
    curvature=path['curvature'][q['segment']];a_ceiling=sum(max(root['floor'],400*max(mu for poly,mu in static['root']['roads'])) for _ in range(4))/p['linear']['mass'];closing=max(0.,geom['COM_normal_closing_m_s']);error=abs(geom['gap_m']-expected_margin) if expected_margin is not None else None
    return dict(progress_m=progress,COM_speed_m_s=math.hypot(*v),COM_velocity_world_m_s=v,COM_velocity_path_tangent_m_s=dot(v,q['tangent']),COM_velocity_path_left_normal_m_s=dot(v,q['normal']),signed_path_position_left_m=q['signed'],path_distance_m=q['distance'],path_tangent_world=q['tangent'],path_heading_rad=ph,body_forward_heading_rad=wrap(body),velocity_heading_rad=heading,velocity_path_heading_deficit_rad=wrap(ph-heading),body_path_heading_deficit_rad=wrap(ph-body),sideslip_heading_rad=wrap(heading-body),yaw_rad_s=p['yaw'],front_joints_rad=p['joints'][:2],front_rates_rad_s=p['rates'][:2],wheels=wheels,geometry=geom,logged_margin_m=expected_margin,road_margin_reproduction_abs_error_m=error,path_node_curvature_proxy_rad_m=curvature,constant_speed_path_normal_acceleration_proxy_m_s2=math.hypot(*v)**2*abs(curvature),source_force_norm_acceleration_ceiling_m_s2=a_ceiling,linear_mass_kg=p['linear']['mass'],straight_flat_point_normal_stop_time_lower_s=closing/a_ceiling,straight_flat_point_normal_stop_distance_lower_m=closing*closing/(2*a_ceiling),tracking_history=history)

def row_state(row):return dict(root=row['root_without_roads'],progress=row['progress'],tracking=row['proposed_history'],global_raw=row['global_raw_after'],margin=row['margin'])
def direction_change(start,end,path):
    a,b=start['planar'],end['planar'];return dict(body_turn_rad=wrap(b['angle']-a['angle']),velocity_turn_rad=wrap(math.atan2(*reversed(b['linear']['velocity']))-math.atan2(*reversed(a['linear']['velocity']))),sideslip_change_rad=wrap(math.atan2(*reversed(b['linear']['velocity']))-(b['angle']+math.pi/2)-math.atan2(*reversed(a['linear']['velocity']))+(a['angle']+math.pi/2)))

def main():
    cpu,wall=time.process_time(),time.perf_counter()
    def cap(*a):raise RuntimeError('585_STORED_ONLY_ANALYSIS_CAP')
    signal.signal(signal.SIGPROF,cap);signal.signal(signal.SIGALRM,cap);signal.setitimer(signal.ITIMER_PROF,30);signal.setitimer(signal.ITIMER_REAL,45);D.mkdir(mode=0o700,exist_ok=False)
    contract=dict(study=585,scope='Storedstateandgeometryonly.No newlaw/source/native/FD/optimizer or counterfactualintegration. Oneunexecutednext-experimentproposal.',registered_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),deadline_utc='2026-10-20T10:01:55Z',caps=dict(CPU_s=30,wall_s=45),input_sha256={k:sha(p) for k,p in INPUTS.items()},implementation_sha256={str(Path(__file__).relative_to(G)):sha(Path(__file__))},source_reference_sha256={p:sha(G/p) for p in SOURCE_REFS},source_ticks=0,force_kernel_calls=0,forecast_ticks=0,native_actions=0,new_FD=0,new_optimizer=0,new_learning=0,new_law_executed=0,HOLDOUT=0,SEALED=0,actual_incumbent_s=13.66,source_incumbent_s=13.20,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0,privacy='Raw roots/commands/journals/privateperrawfeaturesoutsiderepo;publictechnicalcomparisonsandaggregatesonly.')
    (G/'retry/kinematic585_contract.json').write_text(json.dumps(contract,indent=2)+'\n')
    try:
        graph=rd(INPUTS['graph580']);prefix=rd(INPUTS['prefix580']);base=rd(INPUTS['factual577']);esc=rd(INPUTS['escape581']);actual=rd(INPUTS['actual584']);static=rd(INPUTS['static']);path=rd(INPUTS['paths'])['candidate'];c=constants();eb=[bounds(edge) for edge in static['boundary']];parents=graph['parents'];p25=next(p for p in parents if p['instance']==25);fast=next(n for n in graph['nodes'] if n['key']==p25['state_key']);slow=next(n for n in graph['nodes'] if n['edge']==275);assert fast['edge']==274 and fast['parent_instance']==slow['parent_instance']==21
        fedge,sedge=[graph['edges'][i] for i in [274,275]];assert fedge['rows'][0]['before']==sedge['rows'][0]['before'] and fedge['rows'][0]['action'][:2]==sedge['rows'][0]['action'][:2] and fedge['rows'][0]['action'][2]!=sedge['rows'][0]['action'][2]
        common={}
        for name,n in [('fast_parent25',fast),('matched_slow_pruned275',slow)]:common[name]=feature(n['root'],n['progress'],n['tracking'],static,path,c,eb,graph['edges'][n['edge']]['rows'][-1]['margin'])
        br=base['rows'][123];common['factual577']=feature(br['root_without_roads'],br['progress'],br['proposed_history'],static,path,c,eb,br['margin'])
        cohort=[]
        for n in graph['nodes']:
            if n['global_raw']==124:
                f=feature(n['root'],n['progress'],n['tracking'],static,path,c,eb,graph['edges'][n['edge']]['rows'][-1]['margin']);cohort.append(dict(edge=n['edge'],immediate_parent=n['parent_instance'],classification=n['classification'],same_immediate_parent_as25=n['parent_instance']==21,feature=f))
        traces={};snapshot_raw=[112,120,124,128,132,135,136,139,140]
        for name,tape in [('factual577',base),('fast_escape581',esc),('fast_escape_then584',actual)]:
            series=[]
            for raw in range(112,min(140,len(tape['rows']))+1):
                r=tape['rows'][raw-1];f=feature(r['root_without_roads'],r['progress'],r['proposed_history'],static,path,c,eb,r['margin']);series.append(dict(raw=raw,feature=f))
            traces[name]=series
        # Rebuild only saved583nominalforecast metadata, not any state transition.
        events=[json.loads(l) for l in INPUTS['journal583'].open()];checkpoint=rd(INPUTS['checkpoint583']);oldnominal=next(z['nominal_action'] for z in [json.loads(l) for l in Path('/workspace/haic-response584-private/raw-journal-private.jsonl').open()] if z['kind']=='BEFORE_LAW');cert=next(z['context']['certificate'] for z in events if z['kind']=='BEFORE_FORCE' and z['context'].get('mode')=='forecast' and z['context']['forecast_raw_offset']==0 and z['action'][1:]==oldnominal[1:]);oldforces=[z for z in events if z['kind']=='FORCE_VERDICT' and z['context'].get('certificate')==cert];geom={z['state_id']:z['margin'] for z in events if z['kind']=='GEOMETRY_VERDICT'};s=checkpoint['progress'];oldseries=[]
        for z in events:
            if z['kind']=='AFTER_TICK' and z['context'].get('certificate')==cert:
                q=project(z['root']['center'],path,s);s=q['s'];history=next(v['proposed_history'] for v in oldforces if v['sha256']==z['force_event']);raw=z['context']['global_raw']+1;f=feature(z['root'],s,history,static,path,c,eb,geom[digest(z['root'])]);oldseries.append(dict(raw=raw,feature=f))
        traces['stored583_nominal_forecast']=oldseries
        # Rotation totals use observed states and sampled polyline tangent changes only.
        changes={}
        for name,tape in [('factual577',base),('escape581',esc)]:
            r0,r1=tape['rows'][123],tape['rows'][131];turn=direction_change(r0['root_without_roads'],r1['root_without_roads'],path);q0,q1=[project(r['root_without_roads']['center'],path,r['progress']) for r in [r0,r1]];pathturn=wrap(math.atan2(q1['tangent'][1],q1['tangent'][0])-math.atan2(q0['tangent'][1],q0['tangent'][0]));turn.update(raws=[124,132],duration_s=.16,progress_change_m=r1['progress']-r0['progress'],path_polyline_tangent_turn_rad=pathturn,velocity_turn_shortfall_vs_path_rad=pathturn-turn['velocity_turn_rad'],sum_source_yaw_dt_rad=sum(.02*r['root_without_roads']['planar']['yaw'] for r in tape['rows'][124:132]));assert abs(turn['body_turn_rad']-turn['sum_source_yaw_dt_rad'])<1e-12;changes[name]=turn
        r0,r1=actual['rows'][131],actual['rows'][139];turn=direction_change(r0['root_without_roads'],r1['root_without_roads'],path);q0,q1=[project(r['root_without_roads']['center'],path,r['progress']) for r in [r0,r1]];turn.update(raws=[132,140],duration_s=.16,path_polyline_tangent_turn_rad=wrap(math.atan2(q1['tangent'][1],q1['tangent'][0])-math.atan2(q0['tangent'][1],q0['tangent'][0])));changes['cone584_to_first_failure']=turn
        # Fixed actual-failure road segment line, never treated as a global corridor.
        failure_feature=traces['fast_escape_then584'][-1]['feature'];ei=failure_feature['geometry']['edge_index'];normal=failure_feature['geometry']['inward_normal'];anchor=static['boundary'][ei][0];fixedline={}
        for name,tape in [('factual577',base),('escape_then584',actual)]:
            fixedline[name]=[]
            for raw in [124,132,136,139,140]:
                z=tape['rows'][raw-1]['root_without_roads'];ps=polygons(z,c);gap=min(dot(sub(v,anchor),normal) for poly in ps for v in poly);fixedline[name].append(dict(raw=raw,COM_line_distance_m=dot(sub(z['center'],anchor),normal),finite_body_support_line_gap_m=gap,COM_line_closing_speed_m_s=-dot(z['planar']['linear']['velocity'],normal)))
        allf=[v for v in common.values()]+[z['feature'] for z in cohort]+[z['feature'] for series in traces.values() for z in series];maxmarginerror=max(f['road_margin_reproduction_abs_error_m'] for f in allf if f['road_margin_reproduction_abs_error_m'] is not None);assert maxmarginerror<1e-8,maxmarginerror
        checks=dict(matched_parent_and_steering_exact=True,all_available_raw124_nodes14=len(cohort)==14,common_raw124_exact=True,all_reproduced_road_margins_match=maxmarginerror<1e-8,all_581_prefix_rows_match_584=esc['rows']==actual['rows'][:132],original_583_nominal_first_failure_attempt136=oldforces[-1]['gate']=='FORCE' and oldforces[-1]['context']['global_raw']+1==136,source_yaw_sums_match_observed_body_turn=True,all_input_hashes_unchanged=all(sha(INPUTS[k])==h for k,h in contract['input_sha256'].items()),no_dynamics_imports=True)
        assert all(checks.values()),checks
        # Established579fixeds200plane and factual timestamp give a reviewable future boundary.
        plane=rd(G/'retry/beam579_contract.json')['gates']['planes'][0];target=None
        for row in base['rows']:
            a0,a1=[dot(sub(row[k]['center'],plane['center']),plane['forward_normal']) for k in ['before_root_without_roads','root_without_roads']]
            if a0<0<=a1 and abs(row['progress']-200)<=10:target=dict(before_raw=row['global_raw_before'],after_raw=row['global_raw_after'],whole_hold_end_raw=4*row['index'],station_m=200);break
        assert target==dict(before_raw=192,after_raw=193,whole_hold_end_raw=196,station_m=200)
        proposal=dict(status='PROPOSAL_ONLY_NOT_AUTHORIZATION_OR_EXECUTION',recommendation='Onepairedtwo-startjointsteering/pedalprefix-planningexperiment;prioritizeearlierreachablepreparationinsteadofanotherescape/recoverypatch.',arms={'EARLY':dict(initial_replay_to_raw=112,first_planned_raw=113,start='Exactselectedparent25ancestorafterhold28;identicalfastprefixsofar'),'LATE':dict(initial_replay_to_raw=124,first_planned_raw=125,start='Exactparent25afterhold31;no581alignmentprefix')},comparison='Samejointsteer/pedalcomplete-programparameterization,candidatecapandstrictsafetyforbotharms;futureimplementationandactualprogrambasisMUSTbefrozenbeforeanysource. No newlaworprogramgenerated/executedby585.',fixed_boundary=target,criteria='Primaryboundedquestion:safefirstforwardcrossingexisting579s200planein±10progress/pathcorridorwithwholecrossingholdsafe;factualtimestampafter_raw<=193 andwholeholdend<=196defineincumbentnonlaterbound. Reportanypurelocalviabilityseparately;misseddeadlineisnotphysicalirrecoverability. No required100/80msgain.No wholepromotionfromlocalresult.',max_complete_joint_programs_per_arm=16,max_independent_exact_replays_per_arm=1,source_worst=dict(candidate_runs=32,max_raw_each_fresh_initial_run=196,candidate_attempts_max=6272,replay_attempts_max=392,all_attempts_and_completed_max=6664,actual_external_force_max=26656,actual_internal_force_max=26656,total_force_max=53312,raw_geometry_max=6664,additional_current_state_geometry_max=32,all_geometry_max=6696,forecast_ticks=0,hidden_calls_allowed=False),proposed_hard_caps=dict(attempted_raw=6700,completed_model_ticks=6700,external_force=26800,internal_force=26800,total_force=53600,geometry_checks=6800,CPU_s=240,wall_s=320),cost_interpretation='Allsource/failedattempts/forecasts/FINALiflateraddedMUSTfitcounts;currentproposalhasnoforecastor537chooser.Ifimplementationaddsrollouts,renegotiatetheboundbeforerun. CPU/wallarehardstopcapsnotruntimeguarantees;budgetstopiscensoring.',interpretations={'EARLY_success_LATE_failure':'Supportsvalueofearlierjointpreparationunderthisfiniteplannerandincumbentdeadline;doesnotproveparent25unrecoverable.','LATE_success':'Refutesirrecoverabilityofparent25withinthisboundedquestion;currentpatchfailureswerelaw/representation-specific.','both_success':'Bothstartsworkunderaricherjointprogram;comparedefinedworldplane/time,notprogress-onlyranking.','both_failure':'Finiteplanner/windowfailed;cannotseparateintrinsicrecoverylossfrominsufficientrepresentation. Stop,do not growcandidatecapautomatically.'},execution_in_585=False,source_ticks=0,native_actions=0,new_FD=0,new_optimizer=0,new_learning=0,whole=0,HOLDOUT=0,SEALED=0,incumbent_preserved=True,no_automatic_followup=True)
        out=dict(study=585,status='STORED_ANALYSIS_COMPLETE_SOURCE0',checks=checks,common_raw124=common,raw124_cohort=dict(total=14,width_pruned=sum(z['classification']=='width_pruned' for z in cohort),slower_than_parent25_and_pruned=sum(z['classification']=='width_pruned' and z['feature']['COM_speed_m_s']<common['fast_parent25']['COM_speed_m_s'] for z in cohort),same_immediate_parent_safe_children=3,matched_slow_minus_fast={k:common['matched_slow_pruned275'][k]-common['fast_parent25'][k] for k in ['progress_m','COM_speed_m_s','yaw_rad_s','signed_path_position_left_m','COM_velocity_path_left_normal_m_s','velocity_path_heading_deficit_rad']},future_of_discarded_state_observed=False),direction_changes=changes,escape_minus_factual_turns_rad={k:changes['escape581'][k]-changes['factual577'][k] for k in ['body_turn_rad','velocity_turn_rad','velocity_turn_shortfall_vs_path_rad']},selected_snapshots={name:[z for z in series if z['raw'] in snapshot_raw] for name,series in traces.items()},fixed_failure_boundary_line=dict(edge_index=ei,inward_normal=normal,normal_heading_rad=math.atan2(normal[1],normal[0]),comparison=fixedline,meaning='Actual584failedroadsegmentextendedasaninfinitestraightline;coordinatecomparisononly,notglobalroadbarrier.'),maximum_road_margin_reproduction_error_m=maxmarginerror,assumptions=['Onlysavedstatesandstaticgeometry/arithmetic;nointegratedcounterfactual.','Polylineheadingchangesatvertices;nodecurvatureisageometricproxy,notaninstantaneousrequiredsteering/yawbound.','v/yawisnotvelocityturnradiuswhensideslipchanges;servo3rad/sisnotbodyyawcap.','Forceceilingusesactualsource-linearmassandfourclippedwheelvectors,globalmaxroadfriction400N;itignoresforce-direction,longitudinal,yaw/contactcouplinganddoesnotcertifynativerecoverability.','Straightflatpointnormalstoptime/distanceassumesavailablefullnormalaccelerationandfixedboundarynormal;finitebodyshape/orientation,futurecurvature,servo,history/referenceconstraintsinvalidateitasa reachabilitycertificate.','Frozenfirst-ordercritical-pointfloor-timeusesinstantaneousrigidvelocityandfixedlocaledge;notanexacttimetoexit.','Sibling275futureunobserved;factualvs581initialstatesandspeedsdiffer;directiondifferencesarenotwholealignmentcausaleffects.','Positivefootprintgapbelow.5iscontractmarginfailure,notobservedcollision.'],source_ticks=0,force_kernel_calls=0,forecast_ticks=0,native_actions=0,new_FD=0,new_optimizer=0,new_law_executed=0,new_learning=0,whole=0,HOLDOUT=0,SEALED=0,actual_incumbent_s=13.66,source_incumbent_s=13.20,research_remaining=22758,reserve=84000,reserve_used=0,paid_compute=0,static_arithmetic_counts=dict(COUNTS),input_sha256=contract['input_sha256'])
        (D/'derived-features-private.json').write_text(json.dumps(dict(traces=traces,cohort=cohort),allow_nan=False)+'\n');(G/'retry/kinematic585_proposal.json').write_text(json.dumps(proposal,indent=2)+'\n');out['CPU_s']=time.process_time()-cpu;out['wall_s']=time.perf_counter()-wall;out['final_writer_validation_CPU_wall_charge_s']=1.;out['prior_read_only_failure']=rd(Path('/workspace/haic-response585-private/failure-private.json'));out['aggregate_CPU_s']=out['CPU_s']+out['prior_read_only_failure']['CPU_s']+1.;out['aggregate_wall_s']=out['wall_s']+out['prior_read_only_failure']['wall_s']+1.;(G/'retry/kinematic585_analysis.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n');print(json.dumps(dict(status=out['status'],checks=checks,turns=changes,common_raw124={k:{f:v[f] for f in ['progress_m','COM_speed_m_s','yaw_rad_s','signed_path_position_left_m','velocity_path_heading_deficit_rad','geometry','linear_mass_kg']} for k,v in common.items()},aggregate_CPU_s=out['aggregate_CPU_s'],aggregate_wall_s=out['aggregate_wall_s']),indent=2))
    except BaseException as exc:
        (D/'failure-private.json').write_text(json.dumps(dict(error=type(exc).__name__+':'+str(exc),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall))+'\n');raise
    finally:signal.setitimer(signal.ITIMER_PROF,0);signal.setitimer(signal.ITIMER_REAL,0)
if __name__=='__main__':main()
