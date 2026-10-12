"""Actual-call steering limit checks and bounded native evidence only."""
from collections import deque
import hashlib

import numpy as np

from retry.compact_dev_diagnostic import ScalarStats


class TransitionStats(ScalarStats):
    def __init__(self, state):
        super().__init__()
        self.state = state
        self.counts = dict(rows=0,near_rows=0,changed_rows=0,meaningful_changed_rows=0,
            changed_outside_near=0,pedal_changed_rows=0,source_steering_mismatches=0,
            near_applied_delta_max_rad=0.,source_to_previous_applied_delta_max_rad=0.,
            applied_correction_max_rad=0.,joint_residual_max_rad=0.)
        self.first_change = None
        self.first_change_pre = None
        self.samples = []

    def add(self, row):
        row.update(self.state['extra'])
        c=self.counts;c['rows']+=1;c['near_rows']+=bool(row['near'])
        changed=abs(row['applied_correction_rad'])>1e-7
        c['changed_rows']+=changed;c['meaningful_changed_rows']+=abs(row['applied_correction_rad'])>=.01
        c['changed_outside_near']+=bool(changed and not row['near'])
        c['pedal_changed_rows']+=row['pedals_changed']
        c['source_steering_mismatches']+=not row['source_steering_matches']
        c['source_to_previous_applied_delta_max_rad']=max(c['source_to_previous_applied_delta_max_rad'],abs(row['requested_delta_rad']))
        c['applied_correction_max_rad']=max(c['applied_correction_max_rad'],abs(row['applied_correction_rad']))
        c['joint_residual_max_rad']=max(c['joint_residual_max_rad'],max(row['front_joint_residual_after_rad']))
        if row['near']:
            c['near_applied_delta_max_rad']=max(c['near_applied_delta_max_rad'],abs(row['applied_delta_rad']))
            assert abs(row['applied_delta_rad']) <= .1800001
        else:
            assert not changed
        assert not row['pedals_changed'] and row['source_steering_matches']
        if changed:
            if self.first_change is None:
                self.first_change=dict(row);self.first_change_pre=list(self.window)
            if len(self.samples)<8:self.samples.append(dict(row))
        super().add(row)

    def summary(self,completed):
        d=super().summary(completed);d.pop('near5_rows',None)
        d.update(transition_checks=self.counts,first_transition=self.first_change,
            first_transition_pre_window=self.first_change_pre,limited_event_samples=self.samples,
            first_same_input_change=self.state['first_same_input_change'],
            original_prefix_identical_until_first_change=self.state['prefix_identical'],
            differing_observations_vs_saved_original_prefix=self.state['different_obs'],
            first125_candidate_hashes=self.state.get('prefix_hashes'),
            prefix_check_scope='Cached original170 prefix is used only by evaluator comparisons; no index/hash/GT reaches the actor. Full original-road run also checks its first125 rolling hashes against the candidate sanity run.',
            scope='One original policy call; output steering only. Same-input pedals, original controller memory and route code preserved; later observations and selected paths may differ.')
        return d


def transition_episode(plan_path,plan,case,initial_pairs,reference=None,candidate_prefix=None):
    from retry import diagnose,frozen_composite_runtime as runtime
    from retry.compact_dev_diagnostic import compact_episode

    old_factory,old_prepare=diagnose.make_env,runtime.prepare
    state=dict(index=0,previous_applied=0.,first_same_input_change=None,
        prefix_identical=True if reference is not None else None,different_obs=0)
    action_hash,obs_hash=hashlib.sha256(),hashlib.sha256()

    def factory(*args,**kwargs):
        env=old_factory(*args,**kwargs);old_reset,old_step=env.reset,env.step
        def reset(*args,**kwargs):
            out=old_reset(*args,**kwargs);obs_hash.update(out[0].tobytes());return out
        def step(action):
            out=old_step(action);i=state['index']+1
            if i<=125:
                action_hash.update(np.asarray(action,np.float32).tobytes());obs_hash.update(out[0].tobytes())
                if reference is not None:
                    state['different_obs']+=hashlib.sha256(out[0].tobytes()).hexdigest()!=reference['observation_sha256'][i]
                if i==125:
                    state['prefix_hashes']=dict(action_sha256=action_hash.hexdigest(),observation_sha256=obs_hash.hexdigest())
                    if candidate_prefix is not None:assert state['prefix_hashes']==candidate_prefix
            state['index']=i
            return out
        env.reset,env.step=reset,step
        return env

    def prepare(*args,**kwargs):
        worker=old_prepare(*args,**kwargs);old_call=worker.call
        def call(operation,observation):
            response,elapsed=old_call(operation,observation)
            if operation=='act':
                cp=response['contact_probe'];original=np.asarray(cp['controller_return_action'],np.float32)
                applied=np.asarray(response['action'],np.float32);near=cp['near'];previous=state['previous_applied']
                expected=original.copy()
                if near and abs(float(original[0])-previous)>.18:
                    expected[0]=previous+np.clip(float(original[0])-previous,-.18,.18)
                assert expected.tobytes()==applied.tobytes()
                before,after=cp['controller_before'],cp['controller_after']
                if cp['curvature'] is not None:
                    raw=float(np.clip(np.arctan(3.24*cp['curvature']),-.4,.4))
                    source=.8*raw+.2*before['previous_steer']
                    source_match=float(np.float32(source))==float(original[0]) and after['previous_steer']==source
                else:
                    source_match=float(np.float32(before['previous_steer']))==float(original[0]) and after['previous_steer']==before['previous_steer']
                changed=original[0].tobytes()!=applied[0].tobytes()
                i=state['index']+1
                if reference is not None and i<=125 and state['first_same_input_change'] is None:
                    assert hashlib.sha256(observation.tobytes()).hexdigest()==reference['observation_sha256'][i-1]
                    assert original.tobytes()==np.asarray(reference['actions'][i-1],np.float32).tobytes()
                    if changed:
                        state['first_same_input_change']=dict(step=i,original_action=original.tolist(),applied_action=applied.tolist(),near=near,
                            same_saved_input_and_original_action=True,original_controller_memory_preserved=source_match)
                state['extra']=dict(source_steer=float(original[0]),previous_applied_steer=previous,
                    requested_delta_rad=float(original[0])-previous,applied_delta_rad=float(applied[0])-previous,
                    applied_correction_rad=float(applied[0])-float(original[0]),
                    pedals_changed=original[1:].tobytes()!=applied[1:].tobytes(),source_steering_matches=source_match)
                state['previous_applied']=float(applied[0])
            return response,elapsed
        worker.call=call;return worker
    diagnose.make_env,runtime.prepare=factory,prepare
    try:
        return compact_episode(plan_path,plan,case,initial_pairs,[],stats_factory=lambda:TransitionStats(state))
    finally:
        diagnose.make_env,runtime.prepare=old_factory,old_prepare
