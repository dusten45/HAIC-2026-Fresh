"""Evaluator-only scalar DEV diagnostics from actual calls; bounded windows.

No policy replay, renderer, extra native step or input/action transformation.
GT speed and wheel labels describe behavior; they do not identify its cause.
"""
from collections import deque
import hashlib
import json
import time

import numpy as np


def scalar_row(trace, probe, elapsed):
    before, after, action = trace['truth_before'], trace['truth_after'], trace['action']
    duration=after['time']-before['time']
    return dict(step=trace['step'], native_elapsed_pre_s=elapsed,
        native_elapsed_post_s=elapsed+duration, dwell_s=duration,
        native_absolute_pre_s=before['time'],native_absolute_post_s=after['time'],
        speed_before_m_s=before['speed_m_s'], speed_after_m_s=after['speed_m_s'],
        feedback_m_s=probe['actual_feedback_speed_m_s'], target_m_s=probe['target_speed_m_s'],
        curvature=probe['curvature'], near=probe['near'],
        selected_lateral_budget=probe['controller_before']['lateral_acceleration'],
        steer=action[0], gas=action[1], brake=action[2],
        front_joint_residual_after_rad=[abs(w['joint_angle']+action[0]) for w in after['wheels'][:2]],
        offtrack_before=before['off_track_counter'], offtrack_after=after['off_track_counter'],
        damage_before=before['damage'], damage_after=after['damage'], collision=trace['collision'])


def window_summary(rows):
    if not rows:
        return None
    joints=[v for r in rows for v in r['front_joint_residual_after_rad']]
    targets=[r['target_m_s'] for r in rows if r['target_m_s'] is not None]
    pedals=[1 if r['gas']>1e-6 else -1 if r['brake']>1e-6 else 0 for r in rows]
    motions=[1 if r['speed_after_m_s']-r['speed_before_m_s']>0.1 else
             -1 if r['speed_after_m_s']-r['speed_before_m_s'] < -0.1 else 0 for r in rows]
    pedals,motions=[p for p in pedals if p],[m for m in motions if m]
    return dict(rows=len(rows), steps=[rows[0]['step'],rows[-1]['step']],
        native_elapsed_interval_s=[rows[0]['native_elapsed_pre_s'],rows[-1]['native_elapsed_post_s']],
        speed_range_m_s=[min(r['speed_before_m_s'] for r in rows),max(r['speed_before_m_s'] for r in rows)],
        target_range_m_s=[min(targets),max(targets)] if targets else None,
        near_rows=sum(r['near'] for r in rows),gas_rows=sum(r['gas']>1e-6 for r in rows),
        brake_rows=sum(r['brake']>1e-6 for r in rows),
        active_pedal_opposite_switches=sum(x!=y for x,y in zip(pedals,pedals[1:])),
        actual_speed_direction_switches=sum(x!=y for x,y in zip(motions,motions[1:])),
        joint_residual_mean_rad=sum(joints)/len(joints),joint_residual_max_rad=max(joints))


class ScalarStats:
    def __init__(self):
        self.rows=self.near=self.gas=self.brake=0
        self.pedal_switches=self.speed_switches=0
        self.last_pedal=self.last_motion=0
        self.elapsed=0.0
        self.window=deque(maxlen=20)
        self.first_damage=None
        self.first_window=None
        self.last=None
        self.before_last=[]

    def add(self, row):
        self.before_last=list(self.window)
        if self.first_damage is None and row['damage_after']-row['damage_before']>1e-12:
            self.first_damage=dict(row)
            self.first_window=list(self.window)
        self.rows+=1
        self.near+=bool(row['near'])
        self.gas+=row['gas']>1e-6
        self.brake+=row['brake']>1e-6
        pedal=1 if row['gas']>1e-6 else -1 if row['brake']>1e-6 else 0
        delta=row['speed_after_m_s']-row['speed_before_m_s']
        motion=1 if delta>0.1 else -1 if delta < -0.1 else 0
        if pedal:
            self.pedal_switches+=bool(self.last_pedal and pedal!=self.last_pedal)
            self.last_pedal=pedal
        if motion:
            self.speed_switches+=bool(self.last_motion and motion!=self.last_motion)
            self.last_motion=motion
        self.elapsed+=row['dwell_s']
        self.window.append(row)
        self.last=row

    def summary(self, completed):
        return dict(actual_rows=self.rows,observed_native_exposure_s=self.elapsed,
            near5_rows=self.near,normal_rows=self.rows-self.near,
            gas_rows=self.gas,brake_rows=self.brake,
            active_pedal_opposite_switches=self.pedal_switches,
            active_pedal_switches_per_s=self.pedal_switches/self.elapsed if self.elapsed else None,
            actual_speed_direction_switches=self.speed_switches,
            actual_speed_switches_per_s=self.speed_switches/self.elapsed if self.elapsed else None,
            first_damage_event=self.first_damage,first_damage_pre_window=self.first_window,
            first_damage_pre_summary=window_summary(self.first_window),
            last_action_if_not_completed=self.last if not completed else None,
            last_action_pre_window_if_not_completed=self.before_last if not completed else None,
            label_rule='Pedal>1e-6: successive nonneutral gas/brake command reversals. Speed delta>0.1m/s: successive nonsteady acceleration/deceleration labels. Rates use actual native observation time including terminal callbacks; official lap comes only from endpoint. Different trajectories; no cause proof.',
            joint_label='abs(front-wheel joint_angle+action[0]) after action; wheels0/1, target=-action[0]; not vehicle-path error.')


def compact_episode(plan_path, plan, case, initial_pairs, baseline_policy):
    from retry import diagnose, frozen_composite_runtime as runtime
    from retry.frozen_paired_evaluation import episode, write
    from retry.full_route_reproduction import truth

    original_factory,original_prepare=diagnose.make_env,runtime.prepare
    stats=ScalarStats()
    directory=plan_path.parent/'runs'/(case['id']+'__A')
    state={}
    observation_hash,action_hash=hashlib.sha256(),hashlib.sha256()
    first_divergence=None
    law=dict(rows=0,excluded_target_none=0,max_target_error_m_s=0.0,
        pedals_match_source=True,target_increased_vs_same_input_baseline_rows=0,
        pedals_changed_vs_same_input_baseline_rows=0,near_target_or_pedal_changes=0)
    normal=plan['diagnostic_normal_budget']
    base_normal=plan['diagnostic_baseline_normal_budget']
    started=time.perf_counter()

    def factory(*args,**kwargs):
        env=original_factory(*args,**kwargs)
        reset_original,step_original=env.reset,env.step
        def reset(*args,**kwargs):
            output=reset_original(*args,**kwargs)
            state['obs']=output[0]
            observation_hash.update(output[0].tobytes())
            return output
        def step(action):
            before=truth(env)
            response=state['response']
            assert state['input_sha']==hashlib.sha256(state['obs'].tobytes()).hexdigest()
            saved=np.asarray(action,dtype=np.float32).copy()
            assert saved.tobytes()==np.asarray(response['action'],dtype=np.float32).tobytes()
            output=step_original(action)
            obs,_,ended,truncated,info=output
            after=truth(env)
            assert np.array_equal(saved,action)
            trace=dict(step=stats.rows+1,truth_before=before,truth_after=after,
                action=saved.tolist(),collision=bool(info['collision']))
            stats.add(scalar_row(trace,response['contact_probe'],stats.elapsed))
            action_hash.update(saved.tobytes())
            observation_hash.update(obs.tobytes())
            state['obs']=obs
            return output
        env.reset,env.step=reset,step
        return env

    def prepare(*args,**kwargs):
        worker=original_prepare(*args,**kwargs)
        call_original=worker.call
        def call(operation,obs):
            nonlocal first_divergence
            response,elapsed=call_original(operation,obs)
            if operation=='act':
                cp=response['contact_probe']
                assert response['observer_extra_policy_calls']==0
                expected_budget=5.0 if cp['near'] else normal
                assert cp['controller_before']['lateral_acceleration']==expected_budget
                target=cp['target_speed_m_s'];law['rows']+=1
                if target is None:
                    law['excluded_target_none']+=1
                else:
                    k=max(abs(cp['curvature']),1e-6)
                    expected=min(40.0,float(np.sqrt(expected_budget/k)))
                    law['max_target_error_m_s']=max(law['max_target_error_m_s'],abs(target-expected))
                    assert abs(target-expected)<1e-12
                    def pedals(t):
                        feedback=cp['actual_feedback_speed_m_s']
                        return [float(np.float32(np.clip(.08*(t-feedback),0,.5))),float(np.float32(np.clip(.04*(feedback-t),0,.5)))]
                    assert response['action'][1:]==pedals(target)
                    same_base=min(40.0,float(np.sqrt((5.0 if cp['near'] else base_normal)/k)))
                    changed_target=target>same_base+1e-12
                    changed_pedals=response['action'][1:]!=pedals(same_base)
                    law['target_increased_vs_same_input_baseline_rows']+=changed_target
                    law['pedals_changed_vs_same_input_baseline_rows']+=changed_pedals
                    law['near_target_or_pedal_changes']+=bool(cp['near'] and (changed_target or changed_pedals))
                input_sha=hashlib.sha256(obs.tobytes()).hexdigest()
                if first_divergence is None and stats.rows<len(baseline_policy):
                    bp=baseline_policy[stats.rows];br=bp['response'];bc=br['contact_probe']
                    assert input_sha==bp['input_observation_sha256']
                    if response['action']!=br['action']:
                        keys=('old_HUD_speed_m_s','actual_feedback_speed_m_s','curvature','near','detected_path_xy','detected_obstacles_xyr','tracker_hazards_after')
                        same_route=all(response['speed_constraint_probe'][k]==v for k,v in br['speed_constraint_probe'].items())
                        same=all(cp[k]==bc[k] for k in keys) and same_route and response['connection_selection']==br['connection_selection'] and response['action'][0]==br['action'][0]
                        assert same
                        first_divergence=dict(step=stats.rows+1,same_input_path_HUD_tracking_route_and_steer=True,baseline_target_m_s=bc['target_speed_m_s'],candidate_target_m_s=target,baseline_action=br['action'],candidate_action=response['action'])
                state.update(response=response,input_sha=input_sha)
            return response,elapsed
        worker.call=call
        return worker

    diagnose.make_env,runtime.prepare=factory,prepare
    try:
        result=episode(plan_path,plan,case,'A',initial_pairs)
    finally:
        diagnose.make_env,runtime.prepare=original_factory,original_prepare
    if 'error' not in result:
        assert stats.rows==result['successful_wrapper_steps']
        assert action_hash.hexdigest()==result['action_sequence_sha256']
        assert observation_hash.hexdigest()==result['observation_sequence_sha256']
    diagnostic=stats.summary(result['completed'])
    finish=result.get('finish_time_s')
    diagnostic.update(actual_intervention=law,first_same_input_divergence=first_divergence,
        official_lap_ms=result.get('lap_ms'),
        first_damage_begins_after_official_finish=bool(stats.first_damage and finish is not None and stats.first_damage['native_absolute_pre_s']>=finish),
        last_twenty_rows_begin_after_official_finish=sum(finish is not None and r['native_absolute_pre_s']>=finish for r in stats.window),
        full_frame_GT_policy_streams_saved=0,extra_environment_policy_model_calls=0,
        actual_stream_hashes_match='error' not in result,wall_including_short_record_s=time.perf_counter()-started)
    write(directory/'compact-diagnostic.json',diagnostic,exclusive=True)
    return result
