"""Read-only force calibration/first-margin-failure audit, no integration."""
import json,hashlib,math,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response523-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/force523_contract.json').read_text())
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    cal=json.loads((G/'retry/force523_calibration.json').read_text());saved=json.loads((D/'calibration-traces-private.json').read_text())[0]['rows'];actual=[json.loads(Path(f'/workspace/haic-response522-private/raw-{i:04d}.json').read_text()) for i in range(1287,1291)]
    perraw=[max(abs(saved[k]['forces'][i]['ratio']-actual[k]['forces'][i]['ratio']) for i in range(4)) for k in range(4)]
    run=json.loads((D/'cold-shield-model-private.json').read_text());row=run['trace'][-1];prior=run['trace'][-2];paths=json.loads((D/'frozen-paths-private.json').read_text());L=paths['shield']['length'];s=prior['progress']%L
    old=json.loads(Path('/workspace/haic-response522-private/cold-capacity-model-private.json').read_text());static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text());previous=0.;state=static['root'];near=[]
    for z in old['trace']:
        if z['index']>24 and min(abs(previous%L-s),L-abs(previous%L-s))<=10.:
            near.append(dict(peak=max(w['ratio'] for w in z['forces']),speed=math.hypot(*state['planar']['linear']['velocity'])))
        previous=z['progress'];state=z['root_without_roads']
    assert near
    admission=cal['proposed_prediction_admission_ratio'];worst=max(row['forces'],key=lambda w:w['ratio'])
    out=dict(source_and_input_pins_verified=True,conditioned_force_error_max_by_raw=perraw,first_force_evaluation_matches_source_to_ratio_error=perraw[0],uncertainty_margin=cal['calibrated_empirical_force_margin'],admission_ratio=admission,first_cold_failure=run['summary']['first_failure'],first_failure_wheel=worst['wheel'],first_failure_predicted_ratio=worst['ratio'],predicted_plus_empirical_margin=worst['ratio']+cal['calibrated_empirical_force_margin'],physical_raw_force_gate=1.25,original_model_samples_within10m=len(near),original_model_local_max_ratio=max(z['peak'] for z in near),original_model_local_high_ratio_samples=sum(z['peak']>admission for z in near),interpretation='First force evaluation from exact actualroot matches; forceerrors appear after propagation, so accumulated coldinitialhistory alone is insufficient. Onehold and finite local sensitivity do not isolate unique heading/offset/yaw/spin defect. Static pooledhistory/squaredspeed scaling cannot certify force under changed closedloop trajectory. No threshold lowering or rescue.',model_integrator_ticks=0,explicit_force_evaluations=0,native_actions=0,native_resets=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    with (G/'retry/force523_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
