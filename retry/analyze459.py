"""Saved native trace comparison. Reads private inputs; never constructs a world.

Run: python -m retry.analyze459 PRIVATE_ROOT [PUBLIC_OUTPUT_JSON]
Private manifest and timing live under PRIVATE_ROOT/stage459. Public output contains
only aggregates; coordinates, commands, seeds, RNG and restored states stay private.
"""
import collections
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from retry.executor397 import canonical_projection


def analyze(root):
    cpu, wall = time.process_time(), time.perf_counter()
    manifest = {}
    def read(path, lines=False):
        raw = path.read_bytes()
        manifest[str(path)] = hashlib.sha256(raw).hexdigest()
        return [json.loads(x) for x in raw.splitlines()] if lines else json.loads(raw)
    plan = read(root/'stage453/plan.json')
    fixed = read(Path(plan['fixed_plan']))
    pace = read(Path(plan['pace_path']))['frozen268']
    nodes = np.asarray(fixed['free_profile']['speed'])*np.asarray(pace)
    line, ds, model = fixed['line'], fixed['free_profile']['ds'], fixed['model']
    length = sum(ds)
    bounds = [0, 60, 120, 180, 240, 270, 330, 390, 450, 510, 570, 630, 690, 750]
    cases = [('442P',442,'P',118,13.76), ('453B',453,'baseline',22,15.08),
             ('453P',453,'candidate',22,14.98), ('458P',458,'P',112,14.00)]
    traces, data, mismatches = {}, {}, []
    origin = None
    for label, stage, arm, prefix, lap in cases:
        directory = root/f'stage{stage}'/f'actual_{arm}'
        rows = read(directory/'trace-private.jsonl', True)
        traces[label] = rows
        queries = {x['relative_decision']+prefix:x for x in read(root/f'stage{stage}/query-records-private.json') if x['arm']==arm}
        origin = rows[22]['progress_before'] if origin is None else origin
        assert abs(rows[22]['progress_before']-origin)<1e-10
        start = rows[0]['pre']['time']
        samples, intervals, events, recipe_counts = [], [], [], collections.Counter()
        max_error, formula_rows, skipped = 0., 0, collections.Counter()
        for row in rows:
            n = row['step']; state = row['pre']
            receipt = read(directory/f'{arm}_step{n}-after-native-private.json')
            assert len(receipt['posts'])==row['raw_ticks']
            q = canonical_projection(line,state['pos'],state['vel'],'FIRST_LAP')
            phase = row['nominal_memory_after']['C']['phase']
            diag = None
            if phase=='FIRST_LAP' and n>1:
                j,u = q['index'],q['u']
                target = math.sqrt((1-u)*nodes[j]**2+u*nodes[j+1]**2)
                feed = (nodes[j+1]**2-nodes[j]**2)/(2*ds[j])*q['sigma']/target
                feedback = 1.5*(target-state['speed']); raw=feed+feedback
                commanded = min(model['rear_traction_accel'],max(-model['brake_accel'],raw))
                gas = min(1.,max(0.,model['effective_mass']*max(commanded,0)*(state['speed']+2.7)/80000))
                brake = min(1.,max(0.,model['effective_mass']*max(-commanded,0)/(4*1.6*15/(.02*.54))))
                error = float(np.max(np.abs(np.asarray([gas,brake],np.float32)-np.asarray(row['nominal'][1:],np.float32))))
                max_error=max(max_error,error);formula_rows+=1
                if error>1e-7:mismatches.append([label,n,error])
                diag=dict(target=target,feed=feed,feedback=feedback,raw=raw,commanded=commanded,
                          under_braking=state['speed']<target and raw<0,
                          efficiency=q['sigma']/state['speed'] if state['speed'] else 1.)
            else:skipped[phase]+=1
            record=queries.get(n)
            if record:
                authority='planner' if record.get('planner_used') else record.get('mode','guardian')
                recipe=record['selected_recipe']
            else:
                authority='archived_prefix'
                recipe='nominal' if np.array_equal(np.asarray(row['command'],np.float32),np.asarray(row['nominal'],np.float32)) else 'non_nominal'
            recipe_counts[authority+':'+recipe]+=1
            if recipe not in ['nominal']:
                events.append(dict(step=n,offset_m=round(row['progress_before']-origin,3),authority=authority,recipe=recipe))
            previous_s=row['progress_before']; previous_arc=q['arc']; previous_t=state['time']-start; previous_v=state['speed']
            samples.append(dict(s=previous_s-origin,t=previous_t,v=previous_v))
            for tick, post in enumerate(receipt['posts'],1):
                projected=canonical_projection(line,post['position'],post['velocity'],'FIRST_LAP')
                s=previous_s+(projected['arc']-previous_arc+length/2)%length-length/2
                t=post['time']-start; v=math.hypot(*post['velocity']);dt=t-previous_t
                assert abs(dt-.02)<1e-8
                duration=max(0.,min(t,lap)-min(previous_t,lap))
                intervals.append(dict(s=(s+previous_s)/2-origin,dt=duration,v=(v+previous_v)/2,
                                      brake=row['command'][2],gas=row['command'][1],nominal_brake=row['nominal'][2],
                                      path=projected['path_error_m'],diag=diag,observed_accel=(v-previous_v)/dt,
                                      clipped_wheels=sum(bool(w['clipped']) for w in row['raw_tire_samples'] if w['raw_tick']==tick),
                                      grass_wheels=sum(bool(w['grass']) for w in row['raw_tire_samples'] if w['raw_tick']==tick)))
                samples.append(dict(s=s-origin,t=t,v=v))
                previous_s,previous_arc,previous_t,previous_v=s,projected['arc'],t,v
            assert abs(previous_s-row['progress_after'])<1e-7
        crossings={'0':dict(time_s=[rows[22]['pre']['time']-start]*2)}
        for b in bounds[1:]:
            a,z=next((a,z) for a,z in zip(samples,samples[1:]) if a['s']<b<=z['s'])
            crossings[str(b)]=dict(time_s=[round(a['t'],8),round(z['t'],8)],speed_m_s=[round(min(a['v'],z['v']),5),round(max(a['v'],z['v']),5)])
        crossings['finish']=dict(time_s=[lap,lap])
        bins={}
        for lo,hi in zip(bounds,bounds[1:]+[math.inf]):
            subset=[x for x in intervals if lo<=x['s']<hi and x['dt']>0]
            duration=sum(x['dt'] for x in subset)
            qualified=[x for x in subset if x['diag'] is not None]
            def weighted(key):return sum(x[key]*x['dt'] for x in subset)/duration
            bins[str(lo)]=dict(duration_s=round(duration,8),mean_speed_m_s=weighted('v'),
                brake_on_s=sum(x['dt'] for x in subset if x['brake']>1e-8),brake_integral_s=sum(x['dt']*x['brake'] for x in subset),
                mean_gas=weighted('gas'),nominal_brake_on_s=sum(x['dt'] for x in subset if x['nominal_brake']>1e-8),
                under_target_reference_braking_s=sum(x['dt'] for x in qualified if x['diag']['under_braking']),
                mean_progress_efficiency=sum(x['dt']*x['diag']['efficiency'] for x in qualified)/sum(x['dt'] for x in qualified) if qualified else None,
                max_path_error_m=max(x['path'] for x in subset),
                mean_observed_speed_accel_m_s2=weighted('observed_accel'),
                any_wheel_clipped_s=sum(x['dt'] for x in subset if x['clipped_wheels']),
                any_wheel_grass_s=sum(x['dt'] for x in subset if x['grass_wheels']),
                mean_preaction_feed_m_s2=sum(x['dt']*x['diag']['feed'] for x in qualified)/sum(x['dt'] for x in qualified) if qualified else None,
                mean_preaction_feedback_m_s2=sum(x['dt']*x['diag']['feedback'] for x in qualified)/sum(x['dt'] for x in qualified) if qualified else None)
        trigger=next(x for x in rows if x['progress_before']>=origin+450)
        data[label]=dict(lap_s=lap,actions=len(rows),crossings=crossings,bins=bins,recipe_counts=dict(recipe_counts),non_nominal_events=events,
                         formula_audit=dict(rows=formula_rows,max_float32_pedal_error=max_error,skipped_phases=dict(skipped)),
                         trigger450=dict(native_step=trigger['step'],offset_m=round(trigger['progress_before']-origin,6),elapsed_s=round(trigger['pre']['time']-start,8)))
    assert all(traces[x][:22]==traces['442P'][:22] for x in traces)
    assert traces['453P']==read(root/'stage458/actual_C0/trace-private.jsonl',True)
    assert not mismatches, mismatches[:5]
    pairs={}
    for a,b in [('442P','458P'),('453B','453P'),('453P','458P')]:
        segments=[]
        for lo,hi in zip(bounds,bounds[1:]+['finish']):
            durations={}
            for x in [a,b]:
                first,last=data[x]['crossings'][str(lo)]['time_s'],data[x]['crossings'][str(hi)]['time_s']
                durations[x]=[last[0]-first[1],last[1]-first[0]]
            aa,bb=durations[a],durations[b]
            segments.append(dict(offset_m=[lo,hi],second_minus_first_s=[round(bb[0]-aa[1],8),round(bb[1]-aa[0],8)]))
        pairs[a+'_vs_'+b]=segments
    ledger=read(root/'project-effective-budget-v474.json')
    result=dict(stage=459,scope='SAVED_ONLY_DESCRIPTIVE_NO_CAUSAL_IDENTIFICATION',new_actual_actions=0,new_resets=0,new_model_ticks=0,new_model_worlds=0,new_learning=0,
        method='Common original pre23 root offsets. Raw 20ms first-crossing brackets without interpolation; bins use interval progress midpoint and clip duration at official event. Formula uses frozen268 pace; sampled exposures are descriptive, not actuator identification.',
        common_first22_exact=True,trace453P_exact458C0=True,data=data,pairs=pairs,
        budget={k:ledger[k] for k in ['actual_cumulative_wrapper_actions','research_remaining','final_reserved_actions','final_reserve_used']})
    assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest.items())
    private=root/'stage459';private.mkdir(exist_ok=True,mode=0o700)
    (private/'input-sha256-private.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (private/'analysis-cost.json').write_text(json.dumps(dict(CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall,files_read=len(manifest)),indent=2)+'\n')
    return result

if __name__=='__main__':
    result=analyze(Path(sys.argv[1]).resolve())
    output=Path(sys.argv[2]) if len(sys.argv)>2 else Path('retry/compare459_result.json')
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(status='PASS',output=str(output),formula={k:v['formula_audit'] for k,v in result['data'].items()})))
