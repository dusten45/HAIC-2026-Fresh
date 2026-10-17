"""Saved trial algebra audit; no solve/profile/repair or physics invocation.

Profile provenance and stored-array checks are distinct: this does not replay
the eight speed-envelope passes or claim an independent pass certificate.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import numpy as np

G=Path(__file__).resolve().parents[1]

def require(value,reason):
    if not value:raise ValueError('487_AUDIT:'+reason)
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def array_sha(value):return hashlib.sha256(np.asarray(value,dtype='<f8').tobytes(order='C')).hexdigest()
def canonical_sha(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def load(path):return json.loads(Path(path).read_text())
def finite(value,shape=None):
    a=np.asarray(value,float)
    require(np.isfinite(a).all() and (shape is None or a.shape==shape),'finite_array_shape')
    return a
def exact(a,b,reason):require(array_sha(a)==array_sha(b),reason)

def geometry(snapshot):
    roads=sorted(snapshot['roads'],key=lambda row:row['idx']);quads=[finite(row['fixture']['geometry']['vertices']) for row in roads];center=[]
    for i,q in enumerate(quads):
        edges=np.linalg.norm(np.roll(q,-1,axis=0)-q,axis=1)
        ends=[(q[j]+q[(j+1)%4])/2 for j in np.argsort(edges)[-2:]]
        nxt=quads[(i+1)%len(quads)].mean(0)
        center.append(min(ends,key=lambda point:np.linalg.norm(point-nxt)))
    center=np.asarray(center);tangent=np.roll(center,-1,axis=0)-np.roll(center,1,axis=0)
    tangent/=np.linalg.norm(tangent,axis=1)[:,None];normal=np.c_[tangent[:,1],-tangent[:,0]]
    ds=np.linalg.norm(np.roll(center,-1,axis=0)-center,axis=1)
    arc=np.r_[0,np.cumsum(ds[:-1])];L=ds.sum();u=arc/L*16;B=np.zeros((len(center),16))
    for j in range(16):
        delta=np.abs((u-j+8)%16-8)
        B[:,j]=np.where(delta<1,(4-6*delta**2+3*delta**3)/6,np.where(delta<2,(2-delta)**3/6,0))
    distance=np.minimum(arc,L-arc);taper=np.minimum(distance/10,1);taper=taper*taper*(3-2*taper)
    obstacles=np.asarray([o['body']['position'] for o in snapshot['obstacles']])
    radii=np.asarray([o['fixture']['radius'] for o in snapshot['obstacles']])
    return center,normal,B*taper[:,None],obstacles,radii

def path_algebra(path,obstacles,radii):
    a=path-np.roll(path,1,axis=0);b=np.roll(path,-1,axis=0)-path;c=a+b
    cross=a[:,0]*b[:,1]-a[:,1]*b[:,0]
    curvature=2*cross/np.maximum(np.linalg.norm(a,axis=1)*np.linalg.norm(b,axis=1)*np.linalg.norm(c,axis=1),1e-9)
    ds=np.linalg.norm(np.roll(path,-1,axis=0)-path,axis=1)
    start=path[:,None,:];edge=(np.roll(path,-1,axis=0)-path)[:,None,:]
    fraction=np.clip(np.sum((obstacles[None]-start)*edge,axis=2)/np.maximum(np.sum(edge*edge,axis=2),1e-9),0,1)
    near=start+fraction[:,:,None]*edge
    clearance=np.min(np.linalg.norm(near-obstacles[None],axis=2),axis=0)-(radii+2.9+.25)
    return ds,curvature,clearance

def stored_profile(profile,path,ds,curvature,model):
    """Validate existing arrays and report constraints; never form a new v."""
    n=len(path);v=finite(profile['speed'],(n+1,));finite(profile['ds'],(n,));finite(profile['curvature'],(n,))
    exact(profile['ds'],ds,'profile_ds_not_path');exact(profile['curvature'],curvature,'profile_curvature_not_path')
    require(profile['max_abs_curvature']==float(np.max(abs(curvature))),'profile_max_curvature')
    require(v[0]==0 and np.all(v>=0),'profile_speed_domain')
    elapsed=float((2*ds/np.maximum(v[:-1]+v[1:],1e-8)).sum())
    require(profile['estimated_time_s']==elapsed,'stored_profile_time_algebra')
    limits=np.minimum(100.,np.sqrt(model['lateral_accel']/np.maximum(abs(curvature),1e-6)))
    traction=np.minimum(model['rear_traction_accel'],80000/(v[:-1]+2.7)/model['effective_mass'])
    # Report residuals without adding a convergence or new feasibility gate to
    # the original finite four-pass algorithm.
    return dict(speed_limit_excess_m_s=float(max(0.,np.max(v[:-1]-limits),v[-1]-limits[0])),
       braking_squared_speed_excess=float(max(0.,np.max(v[:-1]**2-v[1:]**2-2*model['brake_accel']*ds))),
       traction_squared_speed_excess=float(max(0.,np.max(v[1:]**2-v[:-1]**2-2*traction*ds))),
       zero_length_segments=int(np.sum(ds==0)),nonlaunch_zero_nodes=int(np.sum(v[1:]==0)),
       interpreted_as_new_hard_gate=False)

def audit(directory,plan,quota):
    d=Path(directory)
    pins=plan['source_pins'];source_paths=[]
    for name,h in pins.items():
        p=Path(name);p=p if p.is_absolute() else G/p
        require(sha(p)==h,'source_pin:'+str(p));source_paths.append(p)
    source=G/'retry/racing258_plan.py';tree=ast.parse(source.read_text())
    original=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='solve')
    original_solve_AST_sha=hashlib.sha256(ast.dump(original,include_attributes=False).encode()).hexdigest()
    expected=copy.deepcopy(original)
    evaluate=next(node for node in expected.body if isinstance(node,ast.FunctionDef) and node.name=='evaluate')
    score=next(node for node in evaluate.body if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='score' for t in node.targets))
    score.value=ast.parse("(violation,p['estimated_time_s']+.001*np.sum((np.roll(theta,-1)-theta)**2))",mode='eval').body
    semantic=ast.dump(expected,include_attributes=False)
    semantic_sha=hashlib.sha256(semantic.encode()).hexdigest()
    require(semantic_sha==plan['candidate_semantic_ast_sha256'],'registered_candidate_semantics')
    transform=load(d/'source-transform-private.json')
    require(transform['source']==sha(source) and transform['semantic_sha256']==semantic_sha,'transform_source_provenance')
    transformed=ast.parse(transform['transformed_source']);require(len(transformed.body)==1 and isinstance(transformed.body[0],ast.FunctionDef),'transformed_function_schema')
    clean=transformed.body[0];captures=[]
    for node in ast.walk(clean):
        if hasattr(node,'body') and isinstance(node.body,list):
            kept=[]
            for stmt in node.body:
                if isinstance(stmt,ast.Expr) and isinstance(stmt.value,ast.Call) and isinstance(stmt.value.func,ast.Name) and stmt.value.func.id in ('capture_evaluation','capture_accepted','capture_initial'):
                    captures.append(stmt.value.func.id)
                else:kept.append(stmt)
            node.body[:]=kept
    require(sorted(captures)==['capture_accepted','capture_evaluation','capture_initial'],'exact_three_capture_sites')
    require(ast.dump(clean,include_attributes=False)==semantic,'only_registered_score_semantic_change')
    profile_AST=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='profile')
    profile_AST_sha=hashlib.sha256(ast.dump(profile_AST,include_attributes=False).encode()).hexdigest()
    require(profile_AST_sha==plan['profile_ast_sha256']==transform['profile_ast_sha256'],'unchanged_profile_AST')
    require(source in source_paths,'original_profile_source_unpinned')
    repair_source=G/'retry/racing258_feasibility.py';require(repair_source in source_paths,'original_repair_source_unpinned')
    repair_tree=ast.parse(repair_source.read_text())
    repair_fn=next(n for n in repair_tree.body if isinstance(n,ast.FunctionDef) and n.name=='project')
    repair_AST=ast.dump(repair_fn,include_attributes=False);repair_AST_sha=hashlib.sha256(repair_AST.encode()).hexdigest()
    require(transform['repair_original_ast_sha256']==repair_AST_sha,'original_repair_AST_hash')
    instrumented_repair=ast.parse(transform['repair_transformed_source'])
    require(len(instrumented_repair.body)==1 and isinstance(instrumented_repair.body[0],ast.FunctionDef),'repair_transform_schema')
    repair_clean=instrumented_repair.body[0];capture_indices=[i for i,n in enumerate(repair_clean.body) if isinstance(n,ast.Expr) and isinstance(n.value,ast.Call) and isinstance(n.value.func,ast.Name) and n.value.func.id=='capture_repair']
    require(len(capture_indices)==1,'repair_capture_count')
    ci=capture_indices[0];require(ci+1<len(repair_clean.body) and isinstance(repair_clean.body[ci+1],ast.Assert),'repair_capture_before_original_exit')
    del repair_clean.body[ci]
    require(ast.dump(repair_clean,include_attributes=False)==repair_AST,'repair_has_no_semantic_changes')
    snapshot_path=Path(plan['snapshot_path']);baseline_path=Path(plan['baseline_path'])
    require(sha(snapshot_path)==plan['snapshot_sha256'] and sha(baseline_path)==plan['baseline_sha256'],'input_byte_hash')
    snapshot=load(snapshot_path);snapshot=snapshot.get('physical',snapshot)
    baseline=load(baseline_path);model=baseline['model']
    center,normal,B,obstacles,radii=geometry(snapshot)
    require(len(obstacles)==6,'six_frozen_obstacles')
    journals=plan.get('evaluation_paths')
    paths=[Path(p) for p in journals] if journals is not None else sorted(d.glob('evaluations-*.json'))
    require(bool(paths),'evaluation_journal_missing')
    evaluations=[]
    for p in paths:
        packet=load(p);require(type(packet['evaluations']) is list and 1<=len(packet['evaluations'])<=20,'journal_chunk_size')
        evaluations.extend(packet['evaluations'])
    require(len(evaluations)==194 and [r['number'] for r in evaluations]==list(range(1,195)),'exact194_ordered_evaluations')
    require(array_sha(evaluations[0]['theta'])==plan['initial_theta_sha'],'frozen_initial_theta')
    bound=40/6-1.4-.35;limit=np.tan(.4)/3.24;residuals=[]

    def verify(theta,profile,clearance_record=None,components_record=None):
        theta=finite(theta,(16,));offset=B@theta;path=center+normal*offset[:,None]
        ds,curvature,clearance=path_algebra(path,obstacles,radii)
        components=dict(obstacle_squared=float(np.sum(np.maximum(-clearance,0)**2)),
          curvature_weighted_squared=float(np.sum(np.maximum(abs(curvature)-limit,0)**2)*100),
          offset_squared=float(np.sum(np.maximum(abs(offset)-bound,0)**2)))
        if clearance_record is not None:exact(clearance_record,clearance,'trial_clearance_algebra')
        if components_record is not None:require(components_record==components,'trial_violation_components')
        violation=sum(components.values());rough=float(.001*np.sum((np.roll(theta,-1)-theta)**2))
        residual=stored_profile(profile,path,ds,curvature,model)
        return path,clearance,violation,rough,components,residual

    for r in evaluations:
        path,clear,V,rough,components,residual=verify(r['theta'],r['profile'],r['clearance'],r['components'])
        require(array_sha(path)==r['path_sha256'] and canonical_sha(r['profile'])==r['profile_sha256'],'trial_path_or_profile_hash')
        require(r['violation']==V and r['time_term']==r['profile']['estimated_time_s'] and r['roughness']==rough,'trial_objective_terms')
        require(r['key']==[V,r['time_term']+rough],'exact_two_tuple_objective')
        residuals.append(residual)

    accepted=load(d/'accepted-private.json')['accepted'];require(len(accepted)==96,'accepted_coordinate_count')
    theta=np.asarray(evaluations[0]['theta'],float);key=tuple(evaluations[0]['key']);schedule=[2.,2.,1.,1.,.4,.4]
    for index,a in enumerate(accepted):
        coordinate=index%16;step=schedule[index//16];chosen=theta.copy();chosen_key=key
        for direction,r in zip((-1,1),evaluations[1+2*index:3+2*index]):
            trial=theta.copy();trial[coordinate]=np.clip(trial[coordinate]+direction*step,-bound,bound)
            exact(r['theta'],trial,'fixed_coordinate_trial_schedule')
            candidate_key=tuple(r['key'])
            if candidate_key<chosen_key:chosen=trial;chosen_key=candidate_key
        require(a['calls']==3+2*index and a['coordinate']==coordinate and a['step']==step,'accepted_schedule_identity')
        exact(a['theta'],chosen,'strict_accepted_coefficients');require(tuple(a['key'])==chosen_key,'strict_accepted_key')
        theta=chosen;key=chosen_key
    exact(evaluations[-1]['theta'],theta,'final_reevaluation_theta');require(tuple(evaluations[-1]['key'])==key,'final_reevaluation_key')
    pre=evaluations[-1];pre_feasible=min(pre['clearance'])>=-1e-6 and pre['violation']<=1e-8
    prerepair=load(d/'pre-repair-private.json')
    exact(prerepair['coefficients'],theta,'pre_repair_theta_not_final_trial')
    require(canonical_sha(prerepair['free_profile'])==pre['profile_sha256'] and prerepair['objective']==pre['key'] and prerepair['free_feasible']==pre_feasible,'pre_repair_final_trial_binding')
    final=load(d/'candidate-final-private.json');repair=final.get('numerical_projection')
    final_path,final_clear,V,rough,components,final_residual=verify(final['coefficients'],final['free_profile'],final['free_clearance'])
    exact(final['line'],final_path,'candidate_final_path');exact(final['center'],center,'candidate_original_center')
    require(final['objective']==pre['key'],'candidate_original_objective_binding')
    repair_failed=False
    if repair is None:
        exact(final['coefficients'],theta,'candidate_not_final_trial')
        require(canonical_sha(final['free_profile'])==pre['profile_sha256'],'candidate_profile_not_final_trial')
        require(final['free_feasible']==pre_feasible,'unchanged_source_free_gate')
    else:
        require(not pre_feasible and min(pre['clearance'])>=-.001 and pre['profile']['max_abs_curvature']<=limit,'repair_entry_changed')
        require(type(repair['geometry_evaluations']) is int and 1<=repair['geometry_evaluations']<=100,'repair_evaluation_cap')
        observation_path=d/'repair-observation-private.json';observation=load(observation_path)
        observed_path,observed_clear,_,_,_,observed_residual=verify(observation['coefficients'],observation['profile'],observation['clearance'])
        exact(observation['line'],observed_path,'observed_repair_path');residuals.append(observed_residual)
        require(observation['geometry_evaluations']==repair['geometry_evaluations'],'observed_repair_counter')
        require(np.all(abs(np.asarray(observation['coefficients']))<=bound),'repair_coefficients_outside_bound')
        change=float(abs(np.asarray(observation['coefficients'])-theta).max())
        require(observation['max_coefficient_change']==change,'observed_repair_coefficient_change')
        exit_pass=bool(min(observed_clear)>=0 and observation['profile']['max_abs_curvature']<=limit)
        repair_failed=repair.get('failed',False)
        if repair_failed:
            require(repair_failed is True and repair.get('geometric_exit_assertion_failed') is True and not exit_pass,'failed_repair_without_failed_geometric_predicate')
            require(Path(repair['observation_path']).resolve()==observation_path.resolve() and repair['observation_sha256']==sha(observation_path),'failed_repair_observation_binding')
            exact(final['coefficients'],theta,'failed_repair_changed_candidate_theta')
            require(canonical_sha(final['free_profile'])==pre['profile_sha256'] and final['free_feasible'] is False,'failed_repair_changed_candidate_profile_or_eligibility')
        else:
            require(exit_pass and min(final_clear)>=0 and final['free_profile']['max_abs_curvature']<=limit and final['free_feasible'] is True,'repair_exit_changed')
            exact(final['coefficients'],observation['coefficients'],'repaired_candidate_observation_theta')
            require(canonical_sha(final['free_profile'])==canonical_sha(observation['profile']),'repaired_candidate_observation_profile')
    profile_count=plan['profile_calls']
    require(type(profile_count) is int and profile_count==195+(repair is not None) and profile_count<=196,'profile_invocation_count')
    counts=plan['counts'];require(counts['road_solver']==1 and counts['objectives']==194 and counts['profiles']==profile_count and counts['repair_calls']==int(repair is not None),'runtime_invocation_counts')
    require(type(counts['repair_clearance']) is int and 0<=counts['repair_clearance']<=100 and (repair is not None or counts['repair_clearance']==0),'runtime_repair_clearance_count')
    if repair is not None:require(repair['geometry_evaluations']==counts['repair_clearance'],'repair_counter_receipt_join')
    result=dict(stage=487,passed=True,ordered_objectives_checked=194,accepted_coordinates_checked=96,
      original_solve_AST_sha256=original_solve_AST_sha,candidate_semantic_AST_sha256=semantic_sha,original_profile_AST_sha256=profile_AST_sha,
      original_profile_source_sha256=sha(source),profile_calls_recorded=profile_count,
      profile_source_provenance_checked=True,stored_full_profile_geometry_hash_time_constraints_checked=True,
      independent_eight_pass_reexecution_certificate=False,new_profile_calls_by_audit=0,new_objective_evaluations_by_audit=0,
      new_solve_calls_by_audit=0,new_geometry_draws=0,new_worlds=0,new_actual=0,new_resets=0,
      final_geometry_eligible=bool(final['free_feasible']),final_min_clearance_m=float(min(final_clear)),
      final_aggregate_violation=V,final_violation_components=components,conditional_repair_used=repair is not None,
      original_repair_AST_sha256=repair_AST_sha,repair_geometric_exit_failure_validated=repair_failed,
      max_profile_residuals={k:max(r[k] for r in residuals+[final_residual]) for k in ('speed_limit_excess_m_s','braking_squared_speed_excess','traction_squared_speed_excess','zero_length_segments','nonlaunch_zero_nodes')},
      profile_residuals_are_diagnostics_not_new_gates=True,
      limitation='Stored final profiles plus frozen original profile source/counter are authenticated. No independent replay of the eight source speed-envelope passes is certified.',
      evaluated_journal_hashes={str(p):sha(p) for p in paths})
    quota.write_json('audit-private.json',result,exclusive=True)
    return result
