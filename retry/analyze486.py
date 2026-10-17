"""Saved-only geometric attribution. No path search, profile, world or RNG calls."""
import time
START=time.perf_counter()
import ast,datetime,hashlib,json,math,sys
from pathlib import Path
import numpy as np
import retry.racing258_plan as geometry_source

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def forbidden(*a,**k):raise AssertionError('486_NO_SOLVER_PROFILE_OR_OPTIMIZATION')

def run(root):
    root=Path(root);g=Path(__file__).resolve().parents[1];d=root/'stage486'
    assert not d.exists();d.mkdir(mode=0o700)
    assert not any(n.startswith(('Box2D','env_wrapper','core.vendor.car_racing')) for n in sys.modules)
    geometry_source.solve=forbidden;geometry_source.profile=forbidden
    plan485=read(root/'stage485/plan-private.json')
    for group in ('sources','protected','original408_preserve'):
        for p,h in plan485[group].items():assert sha(p)==h,p
    assert sha(plan485['ledger_path'])==plan485['ledger_sha256']
    raw=Path(plan485['native_dir'])/'D485-A'
    inputs=[raw/'initial-full-private.json',raw/'unsupported-geometry-private.json',root/'stage486-initial-reconstruction-private.json',root/'stage486-initial-feasibility-private.json',root/'stage486-math-audit-private.json']
    state=read(inputs[0])['physical'];saved=read(inputs[1]);initial=read(inputs[2]);initial_metrics=read(inputs[3]);math_audit=read(inputs[4])
    center,normal,obstacles,radii=geometry_source.geometry(state);B,arc,L=geometry_source.basis(center)
    line=np.asarray(saved['line']);theta=np.asarray(saved['coefficients']);offset=B@theta;bound=40/6-1.4-.35
    assert np.array_equal(center,np.asarray(saved['center']))
    assert np.array_equal(center+normal*offset[:,None],line)
    assert np.array_equal(np.asarray(initial['line']),center+normal*(B@np.asarray(initial['coefficients']))[:,None])
    a=line[:,None,:];v=(np.roll(line,-1,axis=0)-line)[:,None,:]
    fractions=np.clip(np.sum((obstacles[None]-a)*v,axis=2)/np.maximum(np.sum(v*v,axis=2),1e-9),0,1)
    distances=np.linalg.norm(a+fractions[:,:,None]*v-obstacles[None],axis=2)
    ix=np.argmin(distances,axis=0);nearest=distances[ix,np.arange(len(obstacles))]
    clearance=nearest-(radii+2.9+.25)
    assert np.array_equal(clearance,np.asarray(saved['free_clearance']))
    vertex_dist=np.min(np.linalg.norm(line[:,None]-obstacles[None],axis=2),axis=0)
    vertex_clear=vertex_dist-(radii+2.9+.25)
    k=np.asarray(saved['free_profile']['curvature']);limit=math.tan(.4)/3.24
    assert np.array_equal(geometry_source.curvature(line),k)
    components=dict(obstacle_squared=float(np.sum(np.maximum(-clearance,0)**2)),curvature_weighted_squared=float(np.sum(np.maximum(abs(k)-limit,0)**2)*100),offset_squared=float(np.sum(np.maximum(abs(offset)-bound,0)**2)))
    violation=sum(components.values());assert violation==saved['violation']
    time_term=saved['free_profile']['estimated_time_s'];rough=float(.001*np.sum((np.roll(theta,-1)-theta)**2))
    assert time_term+1000*violation+rough==saved['objective']
    # Read fixture constants through AST; importing the vehicle would load Box2D.
    constants={}
    tree=ast.parse((g/'core/vendor/car_dynamics.py').read_text())
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
            name=node.targets[0].id
            if name in ('SIZE','HULL_POLY1','HULL_POLY2','HULL_POLY3','HULL_POLY4','WHEELPOS','WHEEL_W','WHEEL_R'):constants[name]=ast.literal_eval(node.value)
    size=constants['SIZE'];hull_radius=max(math.hypot(*pt)*size for key in ('HULL_POLY1','HULL_POLY2','HULL_POLY3','HULL_POLY4') for pt in constants[key])
    wheel_outer_bound=max(math.hypot(*pt)*size for pt in constants['WHEELPOS'])+math.hypot(constants['WHEEL_W'],constants['WHEEL_R'])*size
    private_pairs=[dict(obstacle_index=int(j),nearest_segment=int(ix[j]),segment_fraction=float(fractions[ix[j],j]),minimum_distance_m=float(nearest[j]),required_inflated_radius_m=float(radii[j]+2.9+.25),clearance_m=float(clearance[j]),vertex_only_clearance_m=float(vertex_clear[j])) for j in range(len(obstacles))]
    save(d/'segment-attribution-private.json',dict(pairs=private_pairs,raw_coordinates_published=False))
    active=np.flatnonzero(clearance<0);interior=[j for j in active if 0<fractions[ix[j],j]<1]
    public=dict(stage=486,status='SAVED_ONLY_ANALYSIS_NO_NEW_EXPERIMENT',new_actual=0,new_resets=0,new_worlds=0,new_model_ticks=0,new_seed_draws=0,road_solver_calls=0,new_profile_calls=0,new_optimization_objective_calls=0,
      final=dict(min_clearance_m=float(clearance.min()),negative_obstacles=len(active),vertex_only_min_clearance_m=float(vertex_clear.min()),violating_minima_on_segment_interior=len(interior),max_segment_interpolation_clearance_drop_m=float(np.max(vertex_clear-clearance)),max_abs_curvature=float(abs(k).max()),curvature_limit=limit,max_abs_offset=float(abs(offset).max()),offset_bound=bound,violation_components=components,objective=dict(total=saved['objective'],estimated_time=time_term,penalty=1000*violation,roughness=rough)),
      initial=dict(provenance='Source-only reconstruction, not original durable intermediate. No coordinate search or speed-profile evaluation.',feasible=initial_metrics['initial_free_feasible_by_original_gate'],min_clearance_m=initial_metrics['initial_min_clearance_m'],negative_obstacles=initial_metrics['initial_negative_clearance_count'],max_abs_curvature=initial_metrics['initial_max_abs_curvature'],violation=initial_metrics['initial_aggregate_violation']),
      centerline=dict(min_clearance_m=min(saved['center_clearance']),safe_drop_in=False,interior_stop_profile_not_legal_lap_reference=True),
      inflation=dict(vehicle_disk_m=2.9,extra_clearance_m=.25,min_gap_with_vehicle_disk_but_without_extra_buffer_m=float((clearance+.25).min()),hull_vertex_radius_m=hull_radius,wheel_outer_radius_triangle_bound_m=wheel_outer_bound,fixture_skin_or_contact_tolerance_not_certified=True,buffer_not_relaxed=True,physical_impossibility_proved=False,dynamic_safety_proved=False),
      search=dict(dimension=16,knot_nominal_arc_spacing_m=float(L/16),evaluations=194,trial_evaluations=192,passes=6,initial_sides='one deterministic assignment; not an invariant homotopy proof',finite_schedule=True,convergence_or_optimality_certificate=False,feasible_initial_discarded=False,missing=['original initial objective','accepted-trial trace','intermediate paths','stationarity or completeness certificate']),
      research_remaining=26175,reserve=84000,reserve_used=0,HOLDOUT_SEALED_queries=0,first_DEV_status='485 preparation-ineligible; permanently exposed DEV',second_DEV_status='485 identity-frozen only; no native/solver opening',new_comparison_performed=False)
    save(g/'retry/geometry486_findings.json',public)
    receipt=dict(stage=486,at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),code_sha256=sha(__file__),source_sha256={str(p):sha(p) for p in [g/'retry/racing258_plan.py',g/'retry/racing258_feasibility.py',g/'core/vendor/car_dynamics.py',g/'retry/bootstrap485.py']},input_sha256={str(p):sha(p) for p in inputs},output_sha256=sha(g/'retry/geometry486_findings.json'),CPU_s=time.process_time(),wall_s=time.perf_counter()-START,new_physics=0,new_solver_calls=0,new_draws=0,old_485_sources_ledger_preserved=True)
    save(d/'analysis-private.json',receipt)
    print(json.dumps(dict(stage=486,status=public['status'],final=public['final'],CPU_s=time.process_time(),wall_s=time.perf_counter()-START,new_worlds=0,new_solver_calls=0)))

if __name__=='__main__':run(Path(sys.argv[1]))
