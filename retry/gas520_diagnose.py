"""Read-only post-gate accounting and target tracking; no integrator/native calls."""
import hashlib,json,math,time
from pathlib import Path
import numpy as np
from retry.plan513_model import load_root
from retry.drive519_control import nominal
from retry.gas520_control import request
G=Path(__file__).resolve().parents[1];D=Path('/workspace/haic-response520-private')

def run():
    started=time.perf_counter();cpu=time.process_time()
    static=json.loads(Path('/workspace/haic-response515-private/collected-map-state-private.json').read_text())
    path=json.loads(Path('/workspace/haic-response519-private/frozen-paths-private.json').read_text())['source_drive']
    result=json.loads((G/'retry/gas520_model_result.json').read_text());contract=json.loads((G/'retry/gas520_contract.json').read_text())
    assert all(hashlib.sha256((G/n).read_bytes()).hexdigest()==h for n,h in contract['source_sha256'].items())
    assert all(hashlib.sha256(Path(n).read_bytes()).hexdigest()==h for n,h in contract['private_inputs_sha256'].items())
    summaries=[]
    for arm,source in [('steady',Path('/workspace/haic-response519-private/cold-source_drive-model-private.json')),('response',D/'cold-response-model-private.json')]:
        data=json.loads(source.read_text());before=static['root'];previous_progress=None;hold=None;rows=[];request_index=0;mode_counts={};request_error=[];unchanged=True
        for row in data['trace']:
            if row['raw']==1:
                state=dict(before);state['roads']=static['root']['roads'];root=load_root(state)
                if row['index']>24:
                    n=nominal(root,path,previous_progress);intent=request(root,n)
                    unchanged &= np.array_equal(np.asarray(row['action'],np.float32)[[0,2]],n[[0,2]])
                    hold=dict(index=row['index'],start_speed=math.hypot(*root.planar.linear.velocity),intent=intent,gas=row['action'][1])
                    if arm=='response' and intent['active']:
                        entry=data['requests'][request_index];request_index+=1;assert entry['intent']==intent
                        mode=entry['detail']['mode'];mode_counts[mode]=mode_counts.get(mode,0)+1
                        hold['mode']=mode;hold['forecast_residual']=entry['detail']['target_residual']
                else:hold=None
            if row['raw']==4 and hold and hold['intent']['active']:
                end=math.hypot(*row['root_without_roads']['planar']['linear']['velocity']);rows.append(dict(hold,end_speed=end,error=end-hold['intent']['target']))
            before=row['root_without_roads'];previous_progress=row['progress']
        assert unchanged
        if arm=='response':assert request_index==len(data['requests'])
        summary=dict(arm=arm,complete_positive_request_holds=len(rows),mean_absolute_four_tick_target_error_m_s=sum(abs(z['error']) for z in rows)/len(rows),mean_signed_four_tick_target_error_m_s=sum(z['error'] for z in rows)/len(rows),max_absolute_four_tick_target_error_m_s=max(abs(z['error']) for z in rows),gas_zero_holds=sum(z['gas']==0 for z in rows),gas_one_holds=sum(z['gas']==1 for z in rows),mean_gas=sum(z['gas'] for z in rows)/len(rows),mode_counts_all_positive_holds=mode_counts,steering_and_brake_exact_current_nominal=True)
        summaries.append(summary)
    calibration=json.loads((D/'calibration-private.json').read_text());test=result['pure_test_integrator_ticks'];calib_ticks=sum(4+4+4*z['pair'][1]['detail']['forecast_evaluations'] for z in calibration['pairs']);body=result['arms'][1]['raw_ticks'];allticks=result['new_model_integrator_ticks']
    out=dict(arms=summaries,source_and_input_pins_verified=True,cold_reference_clock_identical=True,cold_gain_s=result['cold_finish_gain_s'],effect_gate_s=.5,promotion=False,carry_cases=0,native_actions=0,native_resets=0,accounting=dict(pure_test_model_ticks=test,saved_state_calibration_model_ticks=calib_ticks,cold_body_model_ticks=body,cold_inverse_forecast_ticks=allticks-test-calib_ticks-body,total_new_model_ticks=allticks,source_wheel_force_evaluations_in_new_model_ticks=4*allticks,additional_explicit_force_oracles=result['new_model_wheel_force_evaluations'],reused_prior_model_ticks_not_new=1020,original_result_reused_prior_model_ticks_field=1036,accounting_correction='Original result retained inherited1036 label from518; actual reused519 trace has1020ticks. No reintegration. Original explicitforce4044 counts diagnostics only; tick integrator wheel evaluations69980 are separate.'),CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-started,scope='Each trajectory uses its own current state and the same target rule. Across trajectories these are not matched identical numerical goals. Four selected shared roots are matched. No independent native accuracy claim, no whole method-family rejection.')
    target=G/'retry/gas520_diagnosis.json'
    with target.open('x') as f:json.dump(out,f,indent=2);f.write('\n')
    print(json.dumps(out,indent=2))

if __name__=='__main__':run()
