"""Before-source584 analysis of stored583 evidence and source equation identities."""
import time
START_CPU=time.process_time();START_WALL=time.perf_counter()
import json,math,hashlib
from pathlib import Path
from collections import Counter
import retry.beam579_model as b
from retry.cone584_math import wheel_formula,select,COUNTS
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response583-private');d=b.d

def main():
    assert not (G/'retry/cone584_forensic.json').exists()
    rows=[json.loads(l) for l in (D/'raw-journal-private.jsonl').open()];inputs={};verdicts={};after={};last_cert=None;errors=[];yawerrors=[];jointerrors=[];failure_rows=[];contactsets=set();frictions=set();torques=[];reactions=[];cert_report=d.rd(D/'choice-034-private.json')['certifications']
    for r in rows:
        if r['kind']=='CERTIFICATION_STARTED':last_cert=r['certificate']
        if r['kind']=='BEFORE_FORCE' and r['context']['mode']=='forecast':inputs[r['sha256']]=r
        if r['kind']=='FORCE_VERDICT' and r['context']['mode']=='forecast':verdicts[r['sha256']]=r
        if r['kind']=='AFTER_TICK' and r['context']['mode']=='forecast':after[r['force_event']]=r
    for event,v in verdicts.items():
        row=inputs[v['input_event']];root=row['root'];p=root['planar'];a=row['action'];computed=[wheel_formula(p,w,i,a[1],a[2]) for i,w in enumerate(p['linear']['wheels'])]
        errors.extend(abs(z['ratio']-f['ratio']) for z,f in zip(computed,v['forces']));errors.extend(abs(z['vector'][j]-f['vector'][j]) for z,f in zip(computed,v['forces']) for j in range(2));frictions.update(w['friction'] for w in p['linear']['wheels']);contactsets.add(json.dumps(root['current_contacts']))
        torque=sum(lever[0]*f['vector'][1]-lever[1]*f['vector'][0] for lever,f in zip(p['levers'],v['forces']))
        rates=[math.copysign(min(50*abs(p['steer']-q),3),p['steer']-q)*p['steering_multiplier'] if i<2 and p['steer']!=q else 0. for i,q in enumerate(p['joints'])]
        if event in after:
            q=after[event]['root']['planar'];pred=(p['angular_momentum']+.02*torque-sum(I*r for I,r in zip(p['wheel_inertias'],rates)))/p['inertia'];yawerrors.append(abs(pred-q['yaw']));jointerrors.extend(abs(max(-.4,min(.4,x+.02*r))-y) for x,r,y in zip(p['joints'],rates,q['joints']));torques.append(.02*torque/p['inertia']);reactions.append(-sum(I*r for I,r in zip(p['wheel_inertias'],rates))/p['inertia'])
        if v['gate']:
            i=max(range(4),key=lambda i:v['forces'][i]['ratio']);failure_rows.append(dict(certificate=row['context']['certificate'],raw_in_hold=row['context']['forecast_raw_offset']+1,peak_wheel=i,peak=v['forces'][i]['ratio'],longitudinal_ratio=computed[i]['longitudinal_ratio'],lateral_ratio=computed[i]['lateral_ratio']))
    seed=d.rd(D/'prefix-checkpoint-private.json');root=d.load_root(dict(seed['root_without_roads'],roads=d.rd(b.INPUTS['static'])['root']['roads']));nominal=b.base.policy.nominal(root,d.rd(b.INPUTS['paths'])['candidate'],seed['progress']);action,proxy=select(d.short(root),nominal)
    assert max(errors)<1e-10 and max(yawerrors)<1e-12 and max(jointerrors)<1e-12
    out=dict(status='STORED_EVIDENCE_ANALYZED_BEFORE_NEW_SOURCE',source_ticks=0,force_kernel_calls=0,native_actions=0,stored_forecast_attempts=len(inputs),stored_completed_ticks=len(after),pure_arithmetic_counts=dict(COUNTS),pure_transition_identity_checks=len(after),force_equation_max_abs_error=max(errors),yaw_balance_max_abs_error=max(yawerrors),joint_servo_max_abs_error=max(jointerrors),friction_values_N=sorted(frictions),distinct_stored_contact_memberships=len(contactsets),failed_raw_distribution=dict(Counter(r['raw_in_hold'] for r in failure_rows)),failed_peak_wheel_distribution=dict(Counter(r['peak_wheel'] for r in failure_rows)),failure_components=failure_rows,original_583_target_joint_rad=.3630639314651489,original_583_joint_sequence_rad=[.05772425979375839,.11772425979375839,.1777242597937584,.23772425979375839],observed_torque_yaw_increment_range_rad_s=[min(torques),max(torques)],servo_momentum_yaw_term_range_rad_s=[min(reactions),max(reactions)],initial_new_law_proxy=dict(path_joint_target_rad=proxy['path_joint_target_rad'],selected_joint_target_rad=proxy['selected_joint_target_rad'],common_intervals_rad=proxy['common_intervals_rad'],virtual_target_force_ratios=proxy['virtual_target_force_ratios'],nominal_pedals_unchanged=proxy['nominal_pedals_unchanged']),mechanism='Currentservo commanddoesnotchangefirstforce. Strongbrakeschangeomegaandfirstlongitudinalforce;PPtargetkeepsservoat3rad/s,subsequentjoint/headingandtorque/yawchangeviandviolationappearsraw3/4. Storedfriction400throughcontactchanges. Tinydirectservo-momentumreactionisnotdominanttorque-drivenyaw. Projectionboundstargetusingcurrentrolling/v/offset/frictionbutdoesnotpredictfutureyaw/omega/contact.',input_sha256={'journal_private':d.sha(D/'raw-journal-private.jsonl'),'checkpoint_private':d.sha(D/'prefix-checkpoint-private.json'),'choice_private':d.sha(D/'choice-034-private.json'),'verified581_private':d.sha(Path('/workspace/haic-response581-private/verified-tape-private.json'))},CPU_s=time.process_time()-START_CPU,wall_s=time.perf_counter()-START_WALL)
    with (G/'retry/cone584_forensic.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps({k:out[k] for k in ['status','pure_arithmetic_counts','force_equation_max_abs_error','yaw_balance_max_abs_error','failed_raw_distribution','initial_new_law_proxy','CPU_s','wall_s']},indent=2))
if __name__=='__main__':main()
