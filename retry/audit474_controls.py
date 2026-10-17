"""Saved-source474 steering audit; pure AST/math/IO, no simulation imports."""
import ast,hashlib,json,math,subprocess,time
from pathlib import Path

G=Path(__file__).resolve().parents[1]
HISTORICAL='3e584dff988f0b90fce3dd563b7f6351a13d21f8'
HISTORICAL_PATH='retry/static_control_audit_20261016.md'
SOURCES=['retry/paired417_common.py','retry/terminal410_run.py','retry/closed411_run.py','retry/cross404_common.py','retry/probe390_run.py','retry/pace265_run.py','retry/pace269_run.py','retry/signed417_executor.py','retry/scalar392_audit.py','retry/factorial401_run.py','retry/headroom413_run.py','retry/terminal410_model.py','core/vendor/car_dynamics.py','core/vendor/car_racing.py','retry/methods380_result.md','retry/hull_reference_dev179_result.md','retry/design466_next.json','retry/law473.py']


def build(root):
    start,cpu=time.perf_counter(),time.process_time();manifest={};parsed={}
    for name in SOURCES:
        raw=(G/name).read_bytes();manifest[name]=dict(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if name.endswith('.py'):parsed[name]=ast.parse(raw.decode('utf-8'),filename=name)
    historical=subprocess.run(['git','show',HISTORICAL+':'+HISTORICAL_PATH],cwd=G,check=True,capture_output=True).stdout
    manifest['git:'+HISTORICAL+':'+HISTORICAL_PATH]=dict(bytes=len(historical),sha256=hashlib.sha256(historical).hexdigest())
    # Confirm the source-only controller extraction inputs, not a running actor.
    steer_lines={name:next(line for line in (G/name).read_text().splitlines() if 'look=max(6.' in line) for name in ['retry/pace265_run.py','retry/pace269_run.py']}
    for text in steer_lines.values():
        assert 'look=max(6.,min(25.,3.24+.22*speed))' in text
        assert 'np.arctan(2*3.24*x/max(delta@delta,1e-6))' in text
        assert 'steer=.8*steer+.2*laststeer' in text
    car=(G/'core/vendor/car_dynamics.py').read_text()
    assert 'WHEELPOS = [(-55, +80), (+55, +80), (-55, -82), (+55, -82)]' in car
    assert 'dir * min(50.0 * val, 3.0) * self.steering_multiplier' in car
    assert 'self.car.steer(-action[0])' in (G/'retry/terminal410_model.py').read_text()
    assert 'self.car.steer(-action[0])' in (G/'core/vendor/car_racing.py').read_text()
    # Mathematical sign chain only: rotation of local forward by -a points
    # right when pursuit's bodyright target displacement and a are positive.
    a=.1;forward_after_negative_target=[math.sin(a),math.cos(a)]
    assert forward_after_negative_target[0]>0
    wheelbase=(80-(-82))*.02
    assert wheelbase==3.24
    facts=dict(steering_units='radians; direct desired front joint angle after env sign inversion',front_wheels=[0,1],wheelbase_m=wheelbase,rear_axle_local_m=[0.,-82*.02],pursuit_control_position='hull local origin',pursuit_velocity='COM linear velocity',steer_action_limit_rad=.4,front_joint_limits_rad=[-.4,.4],preview='clamp(3.24+0.22*COM_speed,6,25)m',controller_prefilter='0.8*current_pursuit+0.2*previous_steer',prefilter_mean_age_s=.08*.2/(1-.2),prefilter_pole_time_constant_s=-.08/math.log(.2),servo_error_gain_per_s=50.,servo_command_rate_limit_rad_s=3.,servo_rate_saturation_error_rad=3./50.,servo_multiplier_note='All servo gain/rate numbers are before steering_multiplier; requested motor speed is not guaranteed actual joint speed',wrapper_hold_s=.08,raw_dt_s=.02,steering_sign_chain_consistent=True,sign_check_kind='pure coordinate algebra; no physics response inferred',force_update_order=['set target steering/gas/brake','joint motorSpeed from current joint error','road/grip friction limit','wheel-local vf/vs','engine wheel omega update','brake omega update','force_long=(omega*radius-vf)*82 and force_lat=-vs*82','joint force-vector friction clipping','wheel omega reaction','ApplyForceToCenter','world.Step','tracker update'])
    checks=dict(AST_modules_parsed=len(parsed),fixed_source_formulas_checked=True,sign_math_passed=True,wheelbase_matches_formula=True,simulation_imports=0,new_constructor_step_reset_native_model=0)
    interpretation=dict(proven=['No explicit steering sign/radian mismatch in this control path','Formula wheelbase equals source axle separation','Pure-pursuit geometry uses hull origin rather than rear-axle point','Command prefilter, joint motor dynamics and80ms hold are separate delays','Longitudinal and lateral tyre demands share clipping'],unproven=['Actuator lag caused either473 failure','Removing smoothing improves lap or safety','Pure-pursuit origin choice is the dominant failure','P4 reference is exact tyre-feasible','All surviving steering errors are numerical or tracking error'],prior_limitations=['179 rear-axle geometry change failed previously; do not recycle as generic cure','380 did not obtain either requested original personal document; no direct original-methodology reread claim','Historical static audit is a local Git document, not the two missing personal originals'])
    candidate=dict(hypothesis='Additional action-boundary steering prefilter compounds existing servo/hold lag',single_change='Replace0.8*current+0.2*previous steering command by current clipped pursuit command; update laststeer to that dispatched natural steering command',fixed=['commonpre23 native state/memory/RNG','P4 immutable nodes and point-FF/feedback','line/pursuit geometry/preview and clamps','native raw physics/joint servo/80ms hold','original safety/progress/finish and authority gates'],not_authorized_to_run=True,requires_saved_evidence='Both failure and safe matched windows should show demand-direction changes and measured -steer versus frontjoint mismatch consistently before path error growth; retain counterexamples',falsification='If filter removal does not change stored state command where command/joint lag is implicated, stop implementation expansion; if a later independently qualified fixed-root comparison is unsafe or does not improve own remaining finish, retain negative and do not combine with reference/preview changes',no_gain_sweep=True,no_failure_location_pulse=True,no_threshold_relaxation=True,qualification='Stored arithmetic qualifies command differences only; future changed-steering model/source qualification and complete bounded cost contract required before integration')
    return dict(stage=474,scope='READ_ONLY_SOURCE_CONTROL_AUDIT',facts=facts,verification=checks,interpretation=interpretation,candidate=candidate,methodology_checks=['separate execution formula from physical feasibility','hold inputs/line/reference and change exactly one control assumption','same root baseline reproduction and command-change gate precede closed-loop claim','negative/overlap/domain/resource outcomes remain distinct','local endpoint improvement never substitutes for own full finish'],source_manifest=manifest,CPU_s=time.process_time()-cpu,wall_s=time.perf_counter()-start)


def run(root,output_directory):
    output_directory=Path(output_directory);output_directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    target=output_directory/'private474-control-audit.json'
    if target.exists():raise FileExistsError(str(target))
    value=build(Path(root))
    with target.open('x') as stream:json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    target.chmod(0o600)
    return value

if __name__=='__main__':
    import sys
    run(Path(sys.argv[1]),Path(sys.argv[2]))
