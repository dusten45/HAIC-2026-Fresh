"""Publish saved443 timing diagnostics and two model-only proposals; no rollout."""
import json
import math
import sys
import time
from pathlib import Path
from retry.decompose412_analyze import Reference, projection


def read(path):
    return json.loads(path.read_text())


def run(root):
    cpu, wall = time.process_time(), time.perf_counter()
    g = Path(__file__).resolve().parents[1]
    d = root/'stage443'
    result = read(d/'result.json')
    fixed = read(Path(read(root/'stage442/plan.json')['fixed_plan']))
    ref = Reference(fixed, read(root/'stage404/profiles-private.json')['speed_nodes268'])
    rows = [json.loads(s) for s in (root/'stage442/actual_C0/trace-private.jsonl').read_text().splitlines()][:118]
    episodes = []
    for row in rows:
        if row['command'][2] <= 0:
            continue
        if episodes and episodes[-1]['last_step']+1 == row['step']:
            episode = episodes[-1]
        else:
            episode = dict(first_step=row['step'], last_step=row['step'], time_s=0.,
                           nominal_brake_time_s=0., guardian_override_time_s=0.)
            episodes.append(episode)
        episode['last_step'] = row['step']
        dt = row['post']['time']-row['pre']['time']
        episode['time_s'] += dt
        episode['nominal_brake_time_s'] += dt*(row['nominal'][2] > 0)
        episode['guardian_override_time_s'] += dt*(row['command'] != row['nominal'])
    below, ff_dom = [], []
    for row in rows:
        q = projection(ref.line, row['pre']['pos'], row['pre']['vel'], row['memory_before']['C']['phase'])
        j, u = q['index'], q['u']
        r = math.sqrt((1-u)*ref.nodes[j]**2+u*ref.nodes[j+1]**2)
        if row['nominal'][2] <= 0 or row['pre']['speed'] >= r:
            continue
        f = (ref.nodes[j+1]**2-ref.nodes[j]**2)/(2*ref.ds[j])
        ff = f*q['sigma']/r
        feedback = 1.5*(r-row['pre']['speed'])
        below.append(row['step'])
        if ff < 0 and feedback > 0 and ff+feedback < 0:
            ff_dom.append(row['step'])
    assert len(below) == len(ff_dom) == 23
    gate = read(root/'stage411/gate_Cpre91_queried/before-private.json')
    native = read(root/'stage442/actual_C0/C0_step91-before-native-private.json')
    assert all(gate[k] == native['full_pre_before_nominal'][k] for k in ['physical','RNG','observation_sha256','wrapper'])
    assert gate['controller']['before'] == native['full_pre_before_nominal']['controller']
    assert gate['controller']['after'] == native['full_pre_after_nominal']['controller']
    gas_lag_sum, gas_lag_max = 0., 0.
    for row in rows:
        for k in range(row['raw_ticks']):
            rear = row['raw_tire_samples'][4*k+2:4*k+4]
            lag = abs(sum(z['gas'] for z in rear)/2-row['command'][1])
            gas_lag_sum += .02*lag
            gas_lag_max = max(gas_lag_max, lag)
    # Grouped observations, never a physically recoverable-time estimate.
    diagnostics = dict(rear_gas_command_abs_lag_time_mean=gas_lag_sum/9.44, rear_gas_command_abs_lag_max=gas_lag_max, full_pre91_physical_rng_observation_wrapper_memory_match_411_gate=True, brake_episodes=episodes, nominal_brake_below_target_actions=len(below),
                       negative_feedforward_dominates_positive_feedback_actions=len(ff_dom),
                       nominal_brake_time_s=1.84, guardian_override_time_s=.08,
                       prefix_share_of_P_time=9.44/13.76,
                       gap_to_11_99_s=13.76-11.99, gap_to_11_00_s=13.76-11.,
                       full_prefix_long_query_upper_ticks=118*6*321*4,
                       not_a_recoverable_gain_or_physical_lower_bound=True)
    gates = dict(current_only=True, current_GT_not_pixel_legal=True,
                 H13_same_world_capture_before_diagnostic_transition14=True,
                 model_parent_steps_charged_actual_ledger_immutable=True,
                 known_condition_no_new_seed=True,
                 source_body_position_m=.1, source_speed_m_s=.5, yaw_rad_s=.05,
                 wheel_joint_rad=.01, wheel_omega_rad_s=1., wheel_slip_m_s=.5,
                 wheel_force_ratio_abs=.05, raw_time_s=1e-8,
                 discrete_phase_contact_grass_collision_damage_clip_count_exact=True,
                 fresh_input_pose_memory_nominal_RNG_and_ledger_binding=True,
                 independent_required_repeat=True,
                 ledger439_continuous_interval_and_discrete_exact=True,
                 progress_goal_m=3.24, progress_deadline_actions=13,
                 old_path_error_cap_m=3., parent_no_mutation=True,
                 counterfactual_states_not_actual_qualified=True,
                 no_actual_followup_authorized=True)
    hypotheses = [
        dict(id='H1', name='Early fixed-path acceleration/brake timing headroom',
             evidence='Prefix9.44s, signed reference-speed term3.354294s; brake1.92s. All23 nominal-brake actions below current target have negative feedforward dominating positive feedback. This may be necessary anticipation, not overbraking.',
             selection='Earliest current FIRST_LAP state in untouched prefix with nominal brake>0, 30<=current COM speed<current fixed target, forward progress>=0, current damage0 and four road contacts. No future exit/gain/clip selection. Stored first occurrence is pre23; freeze this single root. If fresh predicate fails, stop, no other anchor.',
             gates=gates,
             qualification='Full native pre23 snapshot; replay13 recorded actual commands twice for physical calibration only. Same root/clock/RNG/nominal memory; optional held-parent first action. These future recorded commands never enter candidate action selection.',
             arms='Own nominal C13 versus first action fullgas with unchanged nominal steering then own nominal C to13; independently repeated. Same path/profile/entry and original-reference common exit30m. No pulse grid, weight/target retuning or guardian injected from future logs.',
             worst_arithmetic='Calibration2*13*4=104; arms2*2*13*4=208; held parent4:316 ticks,7 worlds. Hard cap512ticks/8worlds/CPU90s/wall150s/sequential1. Unused headroom is not extra queries.',
             caps=dict(model_ticks=512, worlds=8, CPU_s=90, wall_s=150, planned_max_ticks=316, planned_max_worlds=7, actual=0),
             stop='First restore/source/numeric/domain/RNG/protocol/cost error stops all. If baseline13 unsafe, stop without candidate; candidate safety violation stops its branch and remaining experiment. No new root or retry. Missing common exit is censored, not a lap DNF.',
             learning='Validated unsafe/no-gain counterexample rejects only the naive first-gas opportunity at this root; it distinguishes necessary anticipatory braking from this primitive headroom. Both safe but overlapping crossing brackets remain inconclusive. No family-wide negative conclusion.',
             promote='Model-only local followup if both safe through13, exit within13, candidate arrival bracket upper<=baseline lower-.08s and candidate observed raw exit-speed endpoint min>=baseline endpoint max (not a continuous-time bound). Report yaw/joint/omega/path/force endpoint debt; unresolved debt blocks promotion. Not a full-lap planner receipt, actual permission, pixel296 promotion or11s claim.'),
        dict(id='H2', name='Deployment-conditional guardian policy versus nominal-C witness',
             evidence='Latest442 C0 equals historical nominal C through pre91; nominal13 at91 was unsafe while neutral13 was safe. Latest C0 uses only one neutral override91 and then nominal to official finish. Current long witness never includes a future guardian intervention.',
             selection='One frozen pre90 root suggested by historical safe C90 window and unsafe C91 window. Fresh current-state nominal13 must be safe and its one extra nominal transition14 unsafe; both predictions use only this root. The new current-model14 outcome is unobserved. If predicate differs stop before B, never choose a new root or use actual future commands.',
             gates=gates,
             qualification='Replay14 factual442 commands twice from pre90 to calibrate physical restore, not to choose B actions; root/nominal-memory exact. Historical C91 and neighboring C90 data are diagnostics, not a constructed model14 prediction.',
             arms='Two nominal-C14 diagnostic shadows versus two14-action model parents of B. B recomputes unchanged nominal13 twice at every current parent; only if invalid query unchanged neutral13 twice; execute its own qualified first command. Each shadow and parent step charged. No hardcoded step91 pulse, actual future commands or recursive planner.14 is a local observation horizon, not a new H13 safety rule or full finish/time ranking.',
             worst_arithmetic='B shadows2parents*14decisions*4children*13actions*4ticks=5824; B parent steps112; nominal pair112; calibration112; held4 =>6164ticks. Worlds112shadows+2parents+2nominal+2calibration+1held=119. Hard6656ticks/128worlds/CPU240s/wall480s/sequential1.',
             caps=dict(model_ticks=6656, worlds=128, CPU_s=240, wall_s=480, planned_max_ticks=6164, planned_max_worlds=119, actual=0),
             stop='First source/restore/numeric/domain/isolation/protocol/cost error stops all. Nominal model unsafe is a preplanned negative outcome, so stop that branch without padding/tail; it is not a protocol error. B parent safety/deadline failure stops B and remaining arms. No alternate backup, root or retry.',
             learning='Safe B14 versus nominal unsafe at14 after safe13 demonstrates a future conditional guardian intervention missing from the nominal witness. This is not a speed improvement. Both safe fails the gate and does not prove nominal-C finish. B unsafe leaves no qualified backup here, not a family-wide rejection.',
             promote='Only design a separately bounded full B continuation if required repeats and source gates pass, B14 safe/progress and first actual-record comparisons qualify. B14 cannot be passed to choose419 as a finish witness; no fake finish-time/cost, no actual or pixel promotion. Full B witness remains unobserved in the new model.')]
    assert hypotheses[0]['caps']['planned_max_ticks'] == 316
    assert hypotheses[1]['caps']['planned_max_ticks'] == 6164
    proposal = dict(stage=443, status='PROPOSALS_ONLY_NO_EXECUTION_NO_RESERVATION',
                    max_active_deep_lines=2, hypotheses=hypotheses,
                    shared_gates=gates, diagnostics=diagnostics,
                    combined_hard_model_ticks=7168, combined_hard_worlds=136,
                    gains_not_additive=True, eleven_second_achievability_unproven=True,
                    geometry_line='Direct prefix heading+body-slip term is only0.024422s; shortcut-only evidence is weak. Curvature could still constrain feasible speed through the speed term. This algebra does not reject joint path-speed planning; the stronger current witness mismatch is selected as H2.',
                    research_remaining=27516, reserve=84000, reserve_used=0,
                    deadline_utc='2026-10-20T10:01:55Z',
                    new_actual_model_learning_HOLDOUT_SEALED_seed_paid=0,
                    saved_design_CPU_s=time.process_time()-cpu, saved_design_wall_s=time.perf_counter()-wall)
    (g/'retry/hypotheses443_design.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=2)+'\n')
    (d/'design-private.json').write_text(json.dumps(proposal, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(diagnostics))


if __name__ == '__main__':
    run(Path(sys.argv[1]))
