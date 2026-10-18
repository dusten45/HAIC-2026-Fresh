"""Read-only failure audit; no optimization, integration, source force or native."""
import hashlib,json,time,math
from pathlib import Path
import numpy as np
from retry.line530_control import rebuild,path_for,choose
from retry.response528_control import choose as old_choose
from retry.line530_design import constraints,frames,exact_screen
from retry.brake506_geometry import point_segment
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response530-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/line530_contract.json').read_text());static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());paths=json.loads((D/'frozen-paths-private.json').read_text());design=json.loads((G/'retry/line530_design.json').read_text());center=np.array([(x[2],x[3]) for x in static['track']]);normal=frames(center)[1];width=min(min(point_segment(x,*edge) for edge in static['boundary']) for x in center);n=len(center);out={}
    for label in ('baseline','candidate'):
        p=paths[label];v=constraints(p['points'],center,normal,static['obstacles'],width);parts={'road':v[:2*n],'segment_length':v[2*n:3*n],'curvature':v[3*n:4*n],'obstacles':v[4*n:]};re=rebuild(p['points'],static);err={k:float(np.max(abs(np.array(p[k])-np.array(re[k])))) for k in ('points','ds','curvature','arcs','periodic_squared','launch_squared')}
        out[label]=dict(constraints={k:dict(minimum=float(a.min()),violated_samples=int(sum(a< -1e-6))) for k,a in parts.items()},max_profile_rebuild_error=max(err.values()),geometry=design['geometry'] if label=='candidate' else exact_screen(p['points'],static),max_normal_offset_m=float(max(abs(((np.array(p['points'])-center)*normal).sum(axis=1)))))
    source_pins=all(hashlib.sha256((G/k).read_bytes()).hexdigest()==v for k,v in c['source_sha256'].items());private_pins=all(hashlib.sha256(Path(k).read_bytes()).hexdigest()==v for k,v in c['private_inputs_sha256'].items());assert source_pins and private_pins and choose is old_choose
    assert hashlib.sha256((D/'frozen-paths-private.json').read_bytes()).hexdigest()==design['frozen_paths_sha256'];assert not design['pass_design_gate'];assert not (D/'MODEL_STARTED.json').exists() and not (D/'NATIVE_STARTED.json').exists()
    out.update(source_pins_verified=source_pins,private_input_pins_verified=private_pins,controller_function_identity=True,optimizer_run_count=1,model_runs=0,native_runs=0,force_evaluations=0,model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,conclusion='Single SLSQP run not feasible/no scalar improvement; not proof corridor infeasible or path-design family ineffective. Frozen procedure stops before risk/full/native. No repair/restart/sweep.')
    with (G/'retry/line530_audit.json').open('x') as f:json.dump(out,f,indent=2)
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
