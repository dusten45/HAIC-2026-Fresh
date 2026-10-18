"""Read-only component diagnosis of recorded fixed failure; no propagation."""
import datetime,json,time
from pathlib import Path
from retry.clip561_core import atomic_write
from retry.plan513_model import load_root,margin as road_margin,polygons
from retry.corner515_model import obstacle_margin
from retry.brake508_corridor import bounds
from retry.brake510_common import boundary_index
from retry.period556_model import rd,sha
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response562-private')
inputs=[D/'fixed-suffix-private.json',Path('/workspace/haic-response515-private/collected-map-state-private.json'),Path('/workspace/haic-response551-private/cold-candidate-private.json')]
contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),scope='Existing fixed-suffix first footprint failure only: split road/obstacle margin and compare stored551sameclock root. No model/force/candidate/controller calls or gate changes.',caps=dict(model_ticks=0,force_calls=0,geometry_components=2,CPU_s=5,wall_s=10),inputs_sha256={str(p):sha(p) for p in inputs},source_sha256=sha(Path(__file__)))
atomic_write(G/'retry/handoff562_diagnostic_contract.json',contract);cpu,wall=time.process_time(),time.perf_counter();case,static,baseline=map(rd,inputs);row=case['failure']['row'];root=load_root(dict(row['root_without_roads'],roads=static['root']['roads']));road=road_margin(root,static['roads'],bounds(static['roads']),static['boundary'],boundary_index(static['boundary']));obstacle=obstacle_margin(polygons(root),static['obstacles']);ref=next(r for r in baseline['trace'] if r['index']==row['index'] and r['raw']==row['raw']);p=root.planar;q=ref['root_without_roads']['planar']
out=dict(road_margin_m=road,obstacle_margin_m=obstacle,recorded_margin_m=row['margin'],recorded_component_matches=abs(min(road,obstacle)-row['margin'])<1e-12,first_component='ROAD' if road<=obstacle else 'OBSTACLE',baseline_sameclock_margin_m=ref['margin'],COM_position_distance_m=sum((root.center[i]-ref['root_without_roads']['center'][i])**2 for i in range(2))**.5,COM_velocity_distance_m_s=sum((p.linear.velocity[i]-q['linear']['velocity'][i])**2 for i in range(2))**.5,body_angle_difference_rad=p.angle-q['angle'],yaw_difference_rad_s=p.yaw-q['yaw'],model_ticks=0,force_calls=0,geometry_components=2,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
assert out['CPU_s']<5 and out['wall_s']<10 and out['recorded_component_matches'];atomic_write(G/'retry/handoff562_diagnostic.json',out);print(json.dumps(out,indent=2))
