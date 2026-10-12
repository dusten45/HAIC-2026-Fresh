"""Actual-call checks for isolated target-to-steering reference correction."""
import numpy as np
from retry.compact_dev_diagnostic import ScalarStats


def path_curvature(path,lookahead):
    """Signed three-point curvature over one wheelbase around current target.

    Diagnostic only; no preview speed law or control input. Missing support
    returns None rather than extrapolating beyond the currently selected path.
    """
    p=np.asarray(path,float).reshape(-1,2)
    if len(p)<3:return None
    s=np.r_[0.,np.cumsum(np.linalg.norm(np.diff(p,axis=0),axis=1))]
    if lookahead<1.62 or lookahead+1.62>s[-1]:return None
    q=np.column_stack([np.interp([lookahead-1.62,lookahead,lookahead+1.62],s,p[:,i]) for i in (0,1)])
    u,v=q[1]-q[0],q[2]-q[1];denom=float(np.linalg.norm(u)*np.linalg.norm(v)*np.linalg.norm(u+v))
    return -2*float(u[0]*v[1]-u[1]*v[0])/denom if denom>1e-9 else None


class HullStats(ScalarStats):
    def __init__(self,state):
        super().__init__();self.state=state;self.samples=[];self.focus=[];self.first_change=None
        self.checks=dict(rows=0,target_rows=0,changed_steering_rows=0,meaningful_corrections=0,
            nominal_planner_memory_mismatches=0,pedal_mismatches=0,tracking_formula_mismatches=0,
            original_raw_saturated_rows=0,corrected_raw_saturated_rows=0,maximum_correction_rad=0.)

    def add(self,row):
        row.update(self.state['extra']);c=self.checks;c['rows']+=1
        if row['tracking_curvature'] is not None:
            c['target_rows']+=1;c['original_raw_saturated_rows']+=abs(row['nominal_raw'])>=.4
            c['corrected_raw_saturated_rows']+=abs(row['tracking_raw'])>=.4
        correction=abs(row['steer']-row['nominal_requested_steer'])
        c['changed_steering_rows']+=correction>1e-7;c['meaningful_corrections']+=correction>=.01
        c['maximum_correction_rad']=max(c['maximum_correction_rad'],correction)
        if correction>1e-7 and self.first_change is None:self.first_change=dict(row)
        if correction>=.01 and len(self.samples)<5:self.samples.append(dict(row))
        if 110<=row['step']<=119:self.focus.append(dict(row))
        super().add(row)

    def summary(self,completed):
        d=super().summary(completed);d.pop('near5_rows',None)
        d.update(hull_reference_checks=self.checks,first_correction=self.first_change,
            first_five_meaningful_corrections=self.samples,focus_rows=self.focus,
            scope='Original route-ranking previous_steer follows its unchanged nominal law; separate tracking state retains unchanged .8/.2 smoothing. Same actual target and original target speed/pedals. GT motion is evaluator-only; changed trajectories are not identical-state comparisons.')
        return d


def hull_episode(plan_path,plan,case,initial_pairs):
    from retry import frozen_composite_runtime as runtime,compact_dev_diagnostic as compact
    old_prepare,old_scalar=runtime.prepare,compact.scalar_row
    state={}
    def scalar(trace,probe,elapsed):
        row=old_scalar(trace,probe,elapsed);a,b=trace['truth_before'],trace['truth_after']
        row.update(front_steer_before=-float(np.mean([w['joint_angle'] for w in a['wheels'][:2]])),
            front_steer_after=-float(np.mean([w['joint_angle'] for w in b['wheels'][:2]])),
            right_heading_change_rad=-(b['angle']-a['angle']))
        return row
    def prepare(*args,**kwargs):
        worker=old_prepare(*args,**kwargs);old_call=worker.call
        def call(operation,observation):
            response,elapsed=old_call(operation,observation)
            if operation=='act':
                cp=response['contact_probe'];p=response['near_curvature_probe'];before,after=cp['controller_before'],cp['controller_after']
                raw=tracking_raw=k=None
                if cp['curvature'] is None:
                    nominal=before['previous_steer'];expected=nominal
                    assert after['previous_steer']==nominal and after['tracking_previous_steer']==nominal
                else:
                    x,y=p['target_x'],p['target_forward']
                    assert y>=0
                    raw=float(np.clip(np.arctan(3.24*cp['curvature']),-.4,.4))
                    nominal=.8*raw+.2*before['previous_steer']
                    k=2*x/max(x*x+y*y+2*1.64*y,1e-6)
                    tracking_raw=float(np.clip(np.arctan(3.24*k),-.4,.4))
                    expected=.8*tracking_raw+.2*before['tracking_previous_steer']
                    assert after['previous_steer']==nominal and after['tracking_previous_steer']==expected
                assert float(np.float32(expected))==response['action'][0]
                assert response['action']==cp['controller_return_action']
                q=response['speed_constraint_probe']
                state['extra']=dict(nominal_requested_steer=float(np.float32(nominal)),nominal_raw=raw,
                    tracking_raw=tracking_raw,tracking_curvature=k,
                    selected_path_curvature_at_target=path_curvature(q['selected_path_body'],q.get('desired_lookahead_m',0)),
                    lookahead_m=q.get('desired_lookahead_m'),nominal_previous_steer=before['previous_steer'],
                    tracking_previous_steer=before['tracking_previous_steer'])
            return response,elapsed
        worker.call=call;return worker
    runtime.prepare,compact.scalar_row=prepare,scalar
    try:return compact.compact_episode(plan_path,plan,case,initial_pairs,[],stats_factory=lambda:HullStats(state))
    finally:runtime.prepare,compact.scalar_row=old_prepare,old_scalar
