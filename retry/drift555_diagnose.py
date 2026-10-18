"""No integrator: recover omitted rejected-force diagnostics from saved states."""
import datetime, hashlib, json, math, time
from pathlib import Path
import numpy as np
from retry.plan513_model import load_root
from retry.speed516_control import force_rows
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response555-recovery-private')
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x') as f:json.dump(x,f,indent=2,allow_nan=False)
    p.chmod(0o600 if D in p.parents else 0o644)
inputs=[D/'source-witnesses-private.json',D/'steady-branches-private.json',Path('/workspace/haic-response515-private/collected-map-state-private.json')]
contract=dict(registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),purpose='Read only two saved synthetic initial and rejected pre-force states; recover missing exact rejection values and analytic/source alignment. No alternate controls, propagation, relaxed gates or new candidates.',caps=dict(explicit_source_wheel_evaluations=16,model_ticks=0,CPU_s=10,wall_s=15),inputs_sha256={str(p):sha(p) for p in inputs},source_sha256=sha(Path(__file__)))
save(G/'retry/drift555_diagnostic_contract.json',contract)
save(D/'diagnostic-STARTED.json',dict(contract_sha256=sha(G/'retry/drift555_diagnostic_contract.json')))
cpu=time.process_time();wall=time.perf_counter();witness,branches,static=map(read,inputs);records=[];cost=0
assert len(witness)==2 and all(len(w['rows'])==1 for w in witness)
for w in witness:
    branch=branches[w['station']];action=np.array(w['action'],np.float32);detail={}
    for name,state in [('initial',w['initial_root_without_roads']),('rejected',w['rows'][-1]['root_without_roads'])]:
        assert time.process_time()-cpu<10 and time.perf_counter()-wall<15
        root=load_root(dict(state,roads=static['root']['roads']));fs=force_rows(root,action);cost+=4
        error=max(abs(fs[i]['vector'][j]-(math.cos(root.planar.angle)*branch['force'][i][0]-math.sin(root.planar.angle)*branch['force'][i][1] if j==0 else math.sin(root.planar.angle)*branch['force'][i][0]+math.cos(root.planar.angle)*branch['force'][i][1])) for i in range(4) for j in range(2)) if name=='initial' else None
        detail[name]=dict(force_rows=fs,peak=max(z['ratio'] for z in fs),clipped_wheels=sum(z['clipped'] for z in fs),global_force_guard_1_059_pass=max(z['ratio'] for z in fs)<=1.059,analytic_vector_max_error_N=error)
    records.append(dict(station=w['station'],**detail))
save(D/'diagnostic-forces-private.json',records)
public=dict(completed=True,cases=[dict(initial_peak=z['initial']['peak'],initial_analytic_source_vector_error_N=z['initial']['analytic_vector_max_error_N'],rejected_peak=z['rejected']['peak'],rejected_clipped_wheels=z['rejected']['clipped_wheels'],global_force_guard_pass=z['rejected']['global_force_guard_1_059_pass']) for z in records],cost=dict(explicit_source_wheel_evaluations=cost,model_ticks=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall),no_gate_relaxation_or_replay=True)
save(G/'retry/drift555_diagnostic.json',public);print(json.dumps(public,indent=2))
