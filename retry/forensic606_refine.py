"""Supplement stored servo-rate and H6 first-tick evidence, no evaluators."""
import time
CPU=time.process_time();WALL=time.perf_counter()
import hashlib,json,struct
from pathlib import Path
G=Path(__file__).resolve().parents[1];P=Path('/workspace/haic-response605-private')
def read(name):return json.loads((P/name).read_text())
def action(bits):return struct.unpack('<3f',bytes.fromhex(bits))
def main():
    rates=[];zero={r['global_raw_before']+1:r for r in read('zero-result-private.json')['rows']}
    for label in ['H0','H1','H2','H3','H4','H5','H7']:
        rows=read(label+'-result-private.json')['rows'];r=rows[-1];n=r['global_raw_before']+1
        p=r['before_root_without_roads']['planar'];z=zero[n]['before_root_without_roads']['planar']
        detail=read(f'{label}-hold-{r["index"]:03d}-private.json')['detail']
        def regime(bits):
            a=action(bits);return 'gas' if a[1]>0 else 'brake' if a[2]>0 else 'coast'
        rates.append(dict(label=label,raw=n,
            incumbent_pedal_regime=regime(detail['incumbent_bits']),applied_pedal_regime=regime(detail['action_bits']),
            front_servo_rate_cap_hits=sum(abs(v)==3*p['steering_multiplier'] for v in p['rates'][:2]),
            zero_front_servo_rate_cap_hits=sum(abs(v)==3*z['steering_multiplier'] for v in z['rates'][:2]),
            max_abs_front_rate=max(abs(v) for v in p['rates'][:2]),
            zero_max_abs_front_rate=max(abs(v) for v in z['rates'][:2])))
    h6=read('H6-hold-040-private.json');prev=read('H6-hold-039-private.json')['detail']
    zprev=read('zero-hold-039-private.json')['detail'];zh=read('zero-hold-040-private.json')['detail']
    starts=[x for x in h6['events'] if x['kind']=='TRACKING_TRIAL_START']
    traces=[];trial=None
    for e in h6['events']:
        if e['kind']=='TRACKING_TRIAL_START':trial=dict(after=None,gap=None)
        elif e['kind']=='AFTER_MODEL_TICK':trial['after']=e
        elif e['kind']=='SOURCE_GEOMETRY_DIAGNOSTIC':trial['gap']=e['footprint']
        elif e['kind']=='TRACKING_TRIAL_END':
            if trial['after'] is not None:
                p=trial['after']['root']['planar']
                traces.append(dict(footprint=trial['gap'],front_rate_cap_hits=sum(abs(v)==3*p['steering_multiplier'] for v in p['rates'][:2])))
    data=dict(study=606,stored_servo_rates=rates,
        H6_nominal_steer_step_from_previous_applied=action(starts[0]['action_bits'])[0]-action(prev['action_bits'])[0],
        zero_steer_step_at_same_transition=action(zh['incumbent_bits'])[0]-action(zprev['action_bits'])[0],
        H6_forecast_first_tick_footprint_range=[min(q['footprint'] for q in traces),max(q['footprint'] for q in traces)],
        H6_first_tick_front_rate_cap_count_distribution={str(k):sum(t['front_rate_cap_hits']==k for t in traces) for k in range(3)},
        H3_stored_margin_sequence=[dict(raw=r['global_raw_after'],candidate_margin=r['margin'],zero_margin=zero[r['global_raw_after']]['margin']) for r in read('H3-result-private.json')['rows'][-4:]],
        new_scientific_evaluations=0,time=dict(CPU_s=time.process_time()-CPU,wall_s=time.perf_counter()-WALL))
    (G/'retry/forensic606_refinement.json').write_text(json.dumps(data,indent=2)+'\n');print(json.dumps(data,indent=2))
if __name__=='__main__':main()
