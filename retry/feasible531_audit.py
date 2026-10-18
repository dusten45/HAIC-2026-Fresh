"""Read-only endpoint geometry/residual/cost audit, no solver or physics."""
import hashlib,json,time,math
from pathlib import Path
import numpy as np
from retry.feasible531_geometry import Geometry,geometric_constraints,shape,TARGET
from retry.line530_control import rebuild,choose
from retry.response528_control import choose as old_choose
from retry.line530_design import HALF_WIDTH,FRONT
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response531-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/feasible531_contract.json').read_text());design=json.loads((G/'retry/feasible531_design.json').read_text());static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());center=np.array([(p[2],p[3]) for p in static['track']]);g=Geometry(static,center);out={};locations={}
    for label in ('baseline','candidate'):
        p=paths[label];geom,detail=g.evaluate(p['points'],details=True);v=geometric_constraints(g,p['points']);ds,k=shape(p['points']);re=rebuild(p['points'],static);n=len(p['points']);minroad=int(np.argmin(geom[:,0]));obs_seg,obs_id=np.unravel_index(np.argmin(geom[:,1:]),geom[:,1:].shape)
        out[label]=dict(geometry=detail,nominal1_25_max_violation_m=float(max(0.,1.25-geom.min())),computational1_252_max_normalized_violation=float(max(0.,-v.min())),road_violating_segments=int(sum(geom[:,0]<1.25)),obstacle_violating_segment_pairs=int(sum((geom[:,1:]<1.25).ravel())),minimum_segment_length_m=float(ds.min()),max_abs_curvature=float(max(abs(k))),max_profile_rebuild_error=float(max(np.max(abs(np.array(p[x])-np.array(re[x]))) for x in ('ds','curvature','arcs','periodic_squared','launch_squared'))),worst_road_segment_obstacle_gap_m=float(min(geom[minroad,1:])),worst_obstacle_segment_road_gap_m=float(geom[obs_seg,0]),worst_road_and_obstacle_same_segment=bool(minroad==obs_seg));locations[label]=dict(worst_road_segment=minroad,worst_obstacle_segment=int(obs_seg),worst_obstacle_id=int(obs_id))
    radius=4.+float(np.linalg.norm(np.roll(center,-1,axis=0)-center,axis=1).max())/2+math.hypot(FRONT,HALF_WIDTH)+TARGET
    source_pins=all(hashlib.sha256((G/p).read_bytes()).hexdigest()==h for p,h in c['source_sha256'].items());private_pins=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in c['private_inputs_sha256'].items());assert source_pins and private_pins and choose is old_choose;assert radius<12
    assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==design['frozen_paths_sha256']
    out.update(source_pins_verified=source_pins,private_input_pins_verified=private_pins,controller_function_identity=True,geometry_filter_required_radius_upper_bound_m=radius,geometry_filter_radius_m=12.,model_started=(D/'MODEL_STARTED.json').exists(),native_started=(D/'NATIVE_STARTED.json').exists(),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,model_ticks=0,force_evaluations=0,native_actions=0,scope='Read-onlyresidualsnotglobalcorridorinfeasibilityproof. Feasibilitysuccessaloneisnoperformancegain.')
    with (D/'audit-locations-private.json').open('x') as f:json.dump(locations,f)
    with (G/'retry/feasible531_audit.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
