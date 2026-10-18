"""Saved-only first tracking failure and cached-policy identity/cost audit."""
import json,hashlib,math,time
from pathlib import Path
from retry.drive519_control import reference
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response526-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/braking526_execution_contract.json').read_text())
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    ledger=json.loads((D/'corrected-ledger-private.json').read_text())
    for n,h in ledger['prefix_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    data=json.loads((D/'cold-candidate-model-private.json').read_text());path=json.loads((D/'frozen-paths-private.json').read_text())['candidate'];rows=data['trace'];last=rows[-1];hold=last['index'];first=next(i for i,z in enumerate(rows) if z['index']==hold);before=rows[first-1];after=rows[-1];command=next(z for z in data['commands'] if z['index']==hold);v0=math.hypot(*before['root_without_roads']['planar']['linear']['velocity']);v1=math.hypot(*after['root_without_roads']['planar']['linear']['velocity']);target0,ff0=reference(before['progress'],path);target1,ff1=reference(after['progress'],path)
    assert first>0 and last['index']==75 and last['raw']==4 and data['summary']['stop']=='REFERENCE_OVERSPEED'
    trace=[dict(raw=z['raw'],speed_m_s=math.hypot(*z['root_without_roads']['planar']['linear']['velocity']),reference_m_s=z['target'],overspeed_m_s=math.hypot(*z['root_without_roads']['planar']['linear']['velocity'])-z['target'],current_force_peak=max(w['ratio'] for w in z['forces'])) for z in rows[first:]]
    cached=ledger['reused_model_cost'];out=dict(source_input_and_prefix_pins_verified=True,first_failure=dict(action_index=hold,raw_in_hold=4,episode_s=.02*len(rows),mode=command['detail']['mode'],held_positive_gas=command['action'][1]>0,held_brake_zero=command['action'][2]==0,start_speed_m_s=v0,end_speed_m_s=v1,start_reference_m_s=target0,end_reference_m_s=target1,start_spatial_feedforward_m_s2=ff0,end_spatial_feedforward_m_s2=ff1,reference_drop_within_hold_m_s=target0-target1,speed_change_within_hold_m_s=v1-v0,overspeed_gate_m_s=5,observed_overspeed_m_s=v1-target1,governor_forecast_force_peak=command['detail']['reports'][-1]['peak']),failing_hold_raw=trace,interpretation='Hold began in top80 segment withff0,gaspositive,brake0. Held action crossed backward80 reference boundary; desiredspeedfell>5.6m/s during80ms whileactualspeedstayed~79.8. Failure precedes nextcontrollerupdate, not proof of insufficientphysicalbrakecapacity. Existinggovernorcertifiesforce/path butdoesnotcheckreferenceoverspeed; physicalsafetyalone doesnotcertifytrackingofsteepreference. No threshold relaxation/latecontinuation/newcandidate.',cached_baseline_body_ticks_not_new=sum(z['body_ticks'] for z in cached.values()),cached_baseline_forecast_ticks_not_new=sum(z['forecast_ticks'] for z in cached.values()),new_model_integrator_ticks=0,new_force_evaluations=0,native_actions=0,native_resets=0,research_remaining=24155,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    assert ff0==0 and command['action'][1]>0 and command['action'][2]==0 and v1-target1>5 and out['CPU_s']<30 and out['wall_s']<45
    with (G/'retry/braking526_failure_analysis.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
