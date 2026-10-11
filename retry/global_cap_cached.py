"""Saved DEV quartiles and an immediate two-site global28-to40 shadow.

No environment, Agent, model or renderer calls. Progress groups are coarse
labels on each trajectory, never matched states or causal lap decomposition.
"""
import argparse
import json
import math
from pathlib import Path
import time

import numpy as np


def pedals(target, speed):
    return np.asarray([np.clip(.08*(target-speed),0,.5),
                       np.clip(.04*(speed-target),0,.5)],np.float32)


def cap_shadow(curve, distance, speed):
    old, new = min(28.,curve,distance), min(40.,curve,distance)
    old_pedals, new_pedals = pedals(old,speed), pedals(new,speed)
    raised = new > old+1e-10
    names = [('curvature',curve),('distance',distance)]
    if not raised:
        group = 'unchanged_'+'+'.join(k for k,v in names if abs(v-old)<1e-10)
    elif new < 40.-1e-10:
        group = 'partial_'+'+'.join(k for k,v in names if abs(v-new)<1e-10)
    else:
        group = 'reaches40'
    return {'old':old,'new':new,'delta':new-old,'group':group,
            'old_pedals':old_pedals,'new_pedals':new_pedals,
            'pedal_delta':new_pedals.astype(float)-old_pedals.astype(float),
            'changed':not np.array_equal(old_pedals,new_pedals),
            'one_site_only_target':min(28.,40.,curve,distance)}


def analyze_case(spec):
    rows=[json.loads(s) for s in Path(spec['trace']).read_text().splitlines()]
    result=json.loads(Path(spec['result']).read_text())
    assert result['completed'] and result['coefficient']==spec['coefficient']
    assert len(rows)==result['charged_wrapper_actions']
    finish=rows[-1]['info']['finish_time_s']
    before=np.asarray([r['truth_before']['time'] for r in rows])
    after=np.asarray([r['truth_after']['time'] for r in rows])
    dt=np.maximum(0.,np.minimum(after,finish)-before)
    fraction=dt/(after-before)
    assert abs(dt.sum()-result['official_lap_ms']/1000)<1e-8
    assert np.allclose(before[1:],after[:-1],atol=1e-10,rtol=0)
    chords=np.asarray([math.dist(r['truth_before']['position'],r['truth_after']['position']) for r in rows])*fraction
    v0=np.asarray([r['truth_before']['speed_m_s'] for r in rows])
    v1=np.asarray([r['truth_after']['speed_m_s'] for r in rows])
    actual=v0+(v1-v0)*fraction/2
    actions=np.asarray([r['action'] for r in rows])
    bins=np.minimum(3,np.asarray([4*r['truth_before']['unique_tiles']/result['total_tiles'] for r in rows],int))
    shadows=[]
    for r in rows:
        response=r['policy_response'];t=response['route_telemetry'];d=response['curve_diagnostic']
        assert not t['actual_fallback_called'] and d['coefficient']==spec['coefficient']
        coefficient=spec['coefficient'] if d['gate'] else (5 if d['near'] else 7)
        curve=math.sqrt(coefficient/(abs(d['curvature'])+.003))
        distance=min((max(4.,math.sqrt(10*c)) for c in response['cap_diagnostic']['radial_clearances']),default=math.inf)
        shadow=cap_shadow(curve,distance,t['speed_estimate'])
        assert abs(shadow['old']-d['applied_final_target'])<1e-10
        assert np.array_equal(shadow['old_pedals'],np.asarray(r['action'][1:],np.float32))
        assert shadow['one_site_only_target']==shadow['old']
        shadows.append(shadow)
    targets=np.asarray([s['old'] for s in shadows]);delta=np.asarray([s['delta'] for s in shadows])
    raised=delta>1e-10;changed=np.asarray([s['changed'] for s in shadows])
    pedal_delta=np.asarray([s['pedal_delta'] for s in shadows])
    contact=np.asarray([bool(r['info']['collision']) for r in rows])
    def mean(x,w):return float(np.dot(x,w)/w.sum()) if w.sum() else None
    def summary(mask):
        w=dt*mask
        return {'seconds':float(w.sum()),'sampled_chord_m':float(chords[mask].sum()),
                'actual_speed_mean_m_s':mean(actual,w),'target_speed_mean_m_s':mean(targets,w),
                'throttle_mean':mean(actions[:,1],w),'brake_mean':mean(actions[:,2],w),
                'brake_on_s':float(w[actions[:,2]>0].sum()),'contact_actions':int((contact&mask&(dt>0)).sum())}
    exposure={'target_raised_s':float(dt[raised].sum()),'pedal_changed_s':float(dt[changed].sum()),
              'target_delta_mean_raised_m_s':mean(delta,dt*raised),'target_delta_max_m_s':float(delta.max()),
              'throttle_delta_mean_raised':mean(pedal_delta[:,0],dt*raised),
              'brake_delta_mean_raised':mean(pedal_delta[:,1],dt*raised),
              'throttle_delta_max':float(pedal_delta[:,0].max()),'brake_reduction_max':float(-pedal_delta[:,1].min()),
              'raised_but_pedals_same_s':float(dt[raised&~changed].sum()),
              'throttle_saturated_both_s':float(dt[raised&(actions[:,1]==.5)&~changed].sum()),
              'brake_saturated_both_s':float(dt[raised&(actions[:,2]==.5)&~changed].sum()),
              'target_constraint_groups_s':{label:float(dt[np.asarray([s['group']==label for s in shadows])].sum())
                                          for label in sorted({s['group'] for s in shadows})},
              'single_code_site_change_raises_target_s':0.,'arithmetic_only_not_performance_prediction':True}
    return {'condition':spec['condition'],'coefficient':spec['coefficient'],'rows':len(rows),
            'lap_s':result['official_lap_ms']/1000,'damage':result['damage'],
            'whole':summary(np.ones(len(rows),bool)),
            'quartiles':[{'progress_percent':[25*q,25*(q+1)],**summary(bins==q)} for q in range(4)],
            'global40_shadow':exposure,'extra_environment_policy_model_renderer_calls':0}


def analyze(manifest):
    cases=[analyze_case(spec) for spec in manifest['cases']]
    pairs=[]
    for condition in dict.fromkeys(r['condition'] for r in cases):
        base,candidate=sorted([r for r in cases if r['condition']==condition],key=lambda r:r['coefficient'])
        assert [base['coefficient'],candidate['coefficient']]==[7,14]
        deltas=[]
        for b,c in zip(base['quartiles'],candidate['quartiles']):
            deltas.append({'progress_percent':b['progress_percent'],**{key:c[key]-b[key] for key in b if key!='progress_percent'}})
        assert abs(sum(d['seconds'] for d in deltas)-(candidate['lap_s']-base['lap_s']))<1e-8
        pairs.append({'condition':condition,'lap_delta_s':candidate['lap_s']-base['lap_s'],
                      'quartile_deltas_14_minus_7':deltas})
    return {'stage':94,'cases':cases,'pairs':pairs,'cached_rows':sum(c['rows'] for c in cases),
            'new_environment_actions':0,'new_policy_model_renderer_calls':0,
            'grouping':'own pre-action unique_tiles/total_tiles quartiles; last bin includes completion approach',
            'distance':'saved position chords, final partial interval linearly scaled; not raw-tick path length',
            'actual_speed':'saved physical scalar speed, endpoint-clipped trapezoid approximation',
            'paired_bins_are_not_matched_states':True,'cause_not_identified':True}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--manifest',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    args=p.parse_args();start=time.perf_counter();out=analyze(json.loads(args.manifest.read_text()));out['analysis_wall_s']=time.perf_counter()-start
    args.output.write_text(json.dumps(out,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'rows':out['cached_rows'],'wall_s':out['analysis_wall_s'],'pairs':[{k:v for k,v in x.items() if k!='quartile_deltas_14_minus_7'} for x in out['pairs']]}))


if __name__=='__main__':main()
