"""Read-only530 geometry discrepancy audit, before531 optimization."""
import json,time,hashlib
from pathlib import Path
import numpy as np
from retry.feasible531_geometry import Geometry
from retry.line530_design import constraints,frames
from retry.brake506_geometry import point_segment
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response531-private')

def run():
    cpu=time.process_time();wall=time.perf_counter();s=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());p=json.loads(Path('/workspace/haic-response530-private/frozen-paths-private.json').read_text());center=np.array([(z[2],z[3]) for z in s['track']]);normal=frames(center)[1];width=min(min(point_segment(x,*edge) for edge in s['boundary']) for x in center);geo=Geometry(s,center);geo.fractions=np.linspace(0.,1.,25);out={}
    for label in ('baseline','candidate'):
        points=np.array(p[label]['points']);g,detail=geo.evaluate(points,details=True);a=constraints(points,center,normal,s['obstacles'],width);n=len(center)
        out[label]=dict(exact_sampled=detail,approx530_road_min_margin_m=float(a[:2*n].min()+1.25),approx530_obstacle_min_margin_m=float(a[4*n:].min()+1.25),nominal_1_25_max_violation_m=float(max(0.,1.25-g.min())),constraints_violating_1_25=int(sum((g<1.25).ravel())),old_outerbox_screen_pass=detail['minimum_outer_rectangle_margin_m']>=.75)
    out.update(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,model_ticks=0,force_evaluations=0,native_actions=0,interpretation='530normal-roadapproximationandnode/midpointorientationarenotactualpolygon-edgeclearance.531usessegment-tangentouterboxand25samples/segmentagainststoredunion/edges/circles;1.25nominalnotlowered.')
    with (G/'retry/feasible531_analysis.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
