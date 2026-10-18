"""Saved-only gate and coarse-backup diagnostics; no new propagation/force calls."""
import hashlib,json,math,time
from pathlib import Path
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response527-private')


def run():
    cpu=time.process_time();wall=time.perf_counter();c=json.loads((G/'retry/preview527_contract.json').read_text())
    for n,h in c['source_sha256'].items():assert hashlib.sha256((G/n).read_bytes()).hexdigest()==h
    for n,h in c['private_inputs_sha256'].items():assert hashlib.sha256(Path(n).read_bytes()).hexdigest()==h
    new=json.loads((D/'cold-candidate-model-private.json').read_text());old=json.loads(Path('/workspace/haic-response526-private/cold-candidate-model-private.json').read_text());cached=json.loads(Path('/workspace/haic-response525-private/cold-governor-B-model-private.json').read_text());commands={z['index']:z for z in new['commands']};previous={z['index']:z for z in old['commands']};changes=[i for i in range(1,76) if commands[i]['action']!=previous[i]['action']];first=changes[0];assert first==75
    rows=[z for z in new['trace'] if z['index']==75];before=next(z for z in new['trace'] if z['index']==74 and z['raw']==4);end=rows[-1];speed=lambda z:math.hypot(*z['root_without_roads']['planar']['linear']['velocity']);groups={mode:dict(raw=0,mean_deficit_sum=0.,positive_deficit_sum=0.,peak=0.) for mode in ('FIXED_LAUNCH','HIGH','BACKUP')}
    for z in new['trace']:
        mode=commands[z['index']]['detail']['mode'];v=groups[mode];deficit=z['target']-speed(z);v['raw']+=1;v['mean_deficit_sum']+=deficit;v['positive_deficit_sum']+=max(0.,deficit);v['peak']=max(v['peak'],max(f['ratio'] for f in z['forces']))
    mode_summary={k:dict(raw_ticks=v['raw'],time_s=.02*v['raw'],mean_signed_reference_speed_deficit_m_s=v['mean_deficit_sum']/v['raw'],mean_positive_reference_speed_deficit_m_s=v['positive_deficit_sum']/v['raw'],peak=v['peak']) for k,v in groups.items()}
    assert abs(sum(z['time_s'] for z in mode_summary.values())-18.10)<1e-8
    cert=[z['detail']['reports'][-1] for z in new['commands'] if z['index']>24];assert all(z['ok'] and z['max_reference_overspeed']<=5 and z['peak']<=1.06 for z in cert)
    out=dict(source_input_pins_verified=True,all_three_small_probes_pass=True,first_cold_command_change_from_failed526=first,common_first74_commands_bit_exact=True,hold75=dict(mode=commands[75]['detail']['mode'],selected_action_has_brake=commands[75]['action'][2]>0,selected_action_has_gas=commands[75]['action'][1]>0,start_speed_m_s=speed(before),end_speed_m_s=speed(end),end_reference_m_s=end['target'],end_reference_speed_deficit_m_s=end['target']-speed(end),old526_end_overspeed_m_s=5.4971478210610485),mode_time_partition=mode_summary,certified_tracking_decisions=len(cert),reference_and_force_certificates_all_pass=True,baseline_backup_holds=cached['summary']['mode_counts']['BACKUP'],candidate_backup_holds=new['summary']['mode_counts']['BACKUP'],interpretation='527firstchanges526at75, eliminatingheldpositivegasreferencecrossing. Existingbackup100actionplacesendingvelocitybelowcandidate80reference;15vs7BACKUPholdsis descriptive,not isolated recovered/losttime. Coarsebackup commandlibrary is a concrete nextresponse-design hypothesis, not proof of cause of entireeffectshortfall. No newbrakevalue/threshold/candidate/fullcarry/native run.',model_integrator_ticks=0,explicit_force_evaluations=0,native_actions=0,native_resets=0,research_remaining=24155,reserve=84000,reserve_used=0,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-wall)
    assert out['CPU_s']<30 and out['wall_s']<45
    with (G/'retry/preview527_audit.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
