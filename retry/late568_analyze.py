"""Read-only evidence audit and calibration-error localization; zero model ticks."""
import json,math,time
from pathlib import Path
import numpy as np
from retry.clip561_core import atomic_write
from retry.durable568 import digest

G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response568-private')
rd=lambda p:json.loads(p.read_text())

def main():
    cpu,wall=time.process_time(),time.perf_counter();result=rd(G/'retry/late568_result.json');contract=rd(G/'retry/late568_contract.json');frozen=rd(D/'frozen-interior-private.json');linear=rd(D/'linearization-01-private.json')
    tape=rd(Path('/workspace/haic-response565-private/final-tape-private.json'));rr=tape['rows'];x=np.array([v for q in tape['commands'] if 133<=q['index']<=152 for v in [q['action'][0],q['action'][1]-q['action'][2]]]);g=[]
    for i,row in enumerate(rr[528:]):
        previous=rr[527+i];delta=row['progress']-previous['progress'];limit=max(5.,2*math.dist(previous['root_without_roads']['center'],row['root_without_roads']['center']))
        g.extend([row['margin']-.5,3-row['path_error'],4.85-row['reference_overspeed'],*[1.059-f['ratio'] for f in row['forces']],100-row['body'],delta+.5,limit-delta])
    g=np.array(g);J=np.array(linear['J']);T=np.array(linear['T']);m=np.array(frozen['physical']);geometry=[]
    for offset,label in [(0,'footprint'),(1,'path')]:
        ids=np.arange(offset,len(g),10);j=int(ids[np.argmax((m-g)[ids])]);cal=[]
        for n in range(2):
            ev=rd(D/f'calibration-{n}-private.json');dx=np.array(ev['x'])-x;pred=g[j]+J[j]@dx
            cal.append(dict(pattern=n,predicted_slack=float(pred),actual_slack=float(ev['g'][j]),positive_slack_optimism=float(max(0,pred-ev['g'][j])),hull_time_prediction_error_ms=1000*(result['seed_times']['hull_finish']+T@dx-ev['times']['hull_finish'])))
        geometry.append(dict(label=label,raw=529+j//10,seed_slack=float(g[j]),frozen_interior=float(m[j]),seed_deficit=float(m[j]-g[j]),calibration=cal))
    head='0'*64;seq=0;before=None;force=None;tick=None;counts={};unsafe=0;force7=[];strict=0
    with open(D/'raw-journal-private.jsonl') as f:
        for line in f:
            r=json.loads(line);h=r.pop('sha256');assert r['previous']==head and r['sequence']==seq and digest(r)==h;head=h;seq+=1;kind=r['kind'];counts[kind]=counts.get(kind,0)+1
            if kind=='BEFORE_FORCE':
                assert r['state_id']==digest(r['root']) and r['action_id']==digest(r['action']) and r['history_id']==digest(r['history']);before=(h,r)
            elif kind=='FORCE_VERDICT':
                assert before and r['input_event']==before[0];old=before[1]['history'];forces=r['forces'];ratios=[q['ratio'] for q in forces];assert all(q['clipped']==(q['ratio']>1.) for q in forces)
                proposed=[old[0]+sum(q['clipped'] for q in forces),old[1]+4];assert proposed==r['proposed_history'];gate='FORCE' if max(ratios)>r['peak_limit'] else 'CLIP_HISTORY' if r['check_clip'] and proposed[0]/proposed[1]>r['clip_limit'] else None;assert gate==r['gate'];force=(h,r)
                if r['context']['label']=='FD-01-07' and gate:force7.append(dict(gate=gate,global_raw_before=r['context']['global_raw'],index=r['context']['index'],raw=r['context']['raw'],peak=max(ratios),peak_limit=r['peak_limit'],history_before=old,history_after=proposed))
            elif kind=='BEFORE_TICK':
                assert force and r['force_event']==force[0]
                if r['context']['mode']=='strict-policy':assert force[1]['gate'] is None
                tick=force[0]
            elif kind=='AFTER_TICK':
                assert r['force_event']==tick and r['body_domain_pass'] and math.isfinite(r['body']) and r['body']<100.
            elif kind=='RAW_VERDICT':
                assert r['force_event']==tick
                if r['context']['mode']=='diagnostic-probe':assert not r['policy_eligible'];unsafe+=bool(r['failures'])
                else:strict+=1
    assert counts['BEFORE_FORCE']==counts['FORCE_VERDICT']==counts['BEFORE_TICK']==counts['AFTER_TICK']==counts['RAW_VERDICT']==result['cost']['total']['ticks']
    integrity=dict(valid_chain=True,complete_inputs_before_every_force=True,exact_force_clip_verdicts=True,all_tick_inputs_durable=True,all_recorded_bodies_below100=True,unsafe_probes_never_policy_eligible=True,events=seq,head=head,raws=counts['RAW_VERDICT'],unsafe_raws=unsafe,strict_policy_raws=strict,FD01_column7_force_rejections=force7,source_hashes_match_contract=all(__import__('hashlib').sha256((G/p).read_bytes()).hexdigest()==h for p,h in contract['source_sha256'].items()))
    assert integrity['source_hashes_match_contract']
    progress=[dict(iteration=e['iteration'],relative_interior_reduction_percent=100*(e['old_interior_violation']-e['new_interior_violation'])/e['old_interior_violation'],exact_policy_gate_passed=e['local_physical_safe']) for e in result['events']]
    out=dict(record_audit=integrity,dominant_geometry_interiors=geometry,restoration_progress=progress,stop_interpretation='Original stop code TWO_NONDECREASING_RESTORATIONS denotes two reductions below the preregistered 10% required progress. Both measured residuals decreased slightly; this is not literal monotonic nondecrease or proof of directional/global infeasibility.',inference='The fixed two-pattern numerical interior was too demanding for this local restoration and trust region. This bounded run does not establish that the late-control direction, safe policies, or official raw improvement are impossible.',zero_model_ticks=True,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    # A path slack of 3-distance is universally <=3. Diagnose the target mapping,
    # rather than treating this numerical contradiction as a physical result.
    path_targets=m[1::10]
    out['path_interior_feasibility_proof']=dict(maximum_possible_path_slack=3.,maximum_frozen_target=float(max(path_targets)),targets_above_universal_bound=int(sum(path_targets>3.)),internal_target_inconsistent=bool(any(path_targets>3.)),physical_direction_infeasibility_established=False)
    from retry.handoff562_model import project
    path=rd(Path('/workspace/haic-response551-private/frozen-paths-private.json'))['candidate'];signed={}
    for name,rows,j in [('seed',rr,658),('calibration0',rd(D/'calibration-0-private.json')['rows'],130),('calibration1',rd(D/'calibration-1-private.json')['rows'],130)]:
        row=rows[j];point=row['root_without_roads']['center'];q=project(point,path,rows[j-1]['progress']);t=q['tangent'];a=q['point'];signed[name]=dict(raw=row['global_raw_after'],signed_lateral_m=t[0]*(point[1]-a[1])-t[1]*(point[0]-a[0]),path_distance_m=q['distance'])
    out['read_only_signed_geometry_at659']=signed
    atomic_write(G/'retry/late568_analysis.json',out)
    ledger=rd(G/'retry/late568_cost.json');ledger['finally_first_total']=ledger['total'];ledger['total']=result['cost']['total'];ledger['read_only_analysis']=dict(ticks=0,CPU_s=out['CPU_s'],wall_s=out['wall_s']);atomic_write(G/'retry/late568_cost.json',ledger,True)
    print(json.dumps(out,indent=2))

if __name__=='__main__':main()
