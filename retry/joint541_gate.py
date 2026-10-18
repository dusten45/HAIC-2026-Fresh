"""Read saved preregistered phase outcomes; admit native only after all three pass."""
import datetime,hashlib,json,time
from pathlib import Path

def run():
    cpu=time.process_time();wall=time.perf_counter();G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response541-private')
    read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();c=read(G/'retry/joint541_contract.json')
    assert datetime.datetime.now(datetime.timezone.utc)<datetime.datetime.fromisoformat(c['deadline_utc'])
    assert all(sha(G/p)==h for p,h in c['source_sha256'].items())
    assert all(sha(Path(p))==h for p,h in c['private_inputs_sha256'].items())
    phases={phase:read(G/f'retry/joint541_{phase}_result.json') for phase in ('pilot','cold','carry')}
    assert all(r['passed'] for r in phases.values())
    assert phases['pilot']['highspeed_window_covered'] and phases['cold']['gain_vs538_ms']>=500
    assert phases['carry']['gain_vs538_ms']>=0 and phases['carry']['carry_matches_cap90_only_policy']
    identity=read(D/'carry-function-input-identity-private.json');assert identity['same_tracking_function'] and identity['same_cap90_paths'] and identity['launch_branch_unreachable'] and not identity['prior539_carry_observed']
    assert not (D/'NATIVE_STARTED.json').exists()
    out=dict(status='JOINT541_MODEL_NATIVE_ELIGIBLE',native_pair_eligible=True,phase_sha256={phase:sha(G/f'retry/joint541_{phase}_result.json') for phase in phases},model_integrator_ticks=sum(r['model_integrator_ticks'] for r in phases.values()),explicit_force_evaluations=sum(r['explicit_force_evaluations'] for r in phases.values()),planner_cost=dict(geometry_checks=sum(r['planner_cost']['geometry_checks'] for r in phases.values())),CPU_s=sum(r['CPU_s'] for r in phases.values()),wall_s=sum(r['wall_s'] for r in phases.values()),gate_CPU_s=time.process_time()-cpu,gate_wall_s=time.perf_counter()-wall)
    for phase,r in phases.items():
        lim=c['phase_caps'][phase];assert r['model_integrator_ticks']<=lim['model_ticks'] and r['explicit_force_evaluations']<=lim['force'] and r['planner_cost']['geometry_checks']<=lim['geometry'] and r['CPU_s']<=lim['CPU_s'] and r['wall_s']<=lim['wall_s']
    with (G/'retry/joint541_gate_result.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    registration=dict(native_source_sha256=sha(G/'retry/joint541_native.py'),gate_source_sha256=sha(G/'retry/joint541_gate.py'),gate_result_sha256=sha(G/'retry/joint541_gate_result.json'),contract_sha256=sha(G/'retry/joint541_contract.json'),paths_sha256=c['fixed_path_sha256'],baseline538_paths_sha256=sha(Path('/workspace/haic-response538-private/frozen-paths-private.json')),phase_sha256=out['phase_sha256'])
    with (D/'native-registration-private.json').open('x') as f:json.dump(registration,f,indent=2);f.write('\n')
    print(json.dumps(out))
if __name__=='__main__':run()
