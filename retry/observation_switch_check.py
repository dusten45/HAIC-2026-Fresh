"""Trial-only checks: apply observation_switch_trial.patch in an isolated checkout."""
import json
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a
c=a.core


def main():
    assert hasattr(a,'observed_row_fallback_reference'), 'Apply retry/observation_switch_trial.patch in an isolated checkout first.'
    output=Path(sys.argv[1]);assert not output.exists();cpu=time.process_time();ticks=0
    road=((-100.,-100.),(100.,-100.),(100.,200.),(-100.,200.))
    scene=c.Scene([(road,1.)],list(zip(road,road[1:]+road[:1])),[])
    path=dict(points=[[0.,-10.],[0.,0.],[0.,100.]],arcs=[0.,10.,110.],
        ds=[10.,100.],length=110.,launch_squared=[100.,100.,100.],
        periodic_squared=[100.,100.],observed_open=True)
    obj=a.Agent();obj.speed=10.;root=obj._root(scene,0.)
    progress=c.project(root.center,path)['s']
    def planner():return dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0)
    counter=[0];plain_report=planner()
    original,baseline=a._BASELINE_CHOOSE(root,path,path,progress,counter,plain_report,10000,(0,0),scene.context())
    ticks+=counter[0];assert original is not None
    # Same geometric line with a different arc origin requires its OWN progress.
    shifted=dict(path,points=[[x,y-5.] for x,y in path['points']])
    alternate_progress=c.project(root.center,shifted)['s']
    assert abs(alternate_progress-progress-5.)<1e-12
    guarded=dict(path,observation_fallback=dict(high=shifted,low=shifted,progress=alternate_progress))
    counter=[0];cost=planner();original_certifier=c.certifier
    selected,report=a.choose_with_joint_feasibility(root,guarded,path,progress,counter,cost,10000,(0,0),scene.context())
    ticks+=counter[0]
    assert np.array_equal(selected,original) and report['final_recertified']
    final=report['reports'][-1]
    assert final['ok'] and final['observation_fallback']['ok']
    assert final['first_hold']==baseline['reports'][-1]['first_hold']
    assert cost['observation_fallback_forecast_calls']>0 and cost['forecast_calls']>0
    assert cost['forecast_ticks']==counter[0] and c.certifier is original_certifier
    # A primary-feasible command cannot escape an unsafe alternate constraint.
    unsafe=dict(path,launch_squared=[1.,1.,1.],periodic_squared=[1.,1.])
    rejected_path=dict(path,observation_fallback=dict(high=unsafe,low=unsafe,progress=progress))
    counter=[0];cost=planner()
    rejected,why=a.choose_with_joint_feasibility(root,rejected_path,path,progress,counter,cost,10000,(0,0),scene.context())
    ticks+=counter[0];assert rejected is None
    assert all(t['reason'].startswith('OBSERVATION_FALLBACK_') for t in why['trials'])
    assert c.certifier is original_certifier
    # The shadow builder equals the actual existing raw-reference branch.
    captured={};reference=a.reference_from_observed_width
    def capture(raw,*args,**kwargs):
        captured['raw']=np.asarray(raw).copy();return reference(raw,*args,**kwargs)
    a.reference_from_observed_width=capture
    obj=a.Agent();obj.speed=10.;obj.distance=200.
    try:_,high,low,s=obj._map(np.full((84,84),.4,np.float32))
    finally:a.reference_from_observed_width=reference
    assert not obj.uncertainty['observed_width_reference_used']
    expected=a.observed_row_fallback_reference(captured['raw'],[],obj.com,obj.distance)
    assert high==expected['high'] and low==expected['low'] and s==expected['progress']
    # Factory exceptions must restore the certifier and never emit a command.
    choose=a._choose_without_observation_guard
    def fail(*args,**kwargs):raise RuntimeError('SYNTHETIC_FACTORY_FAILURE')
    def invoke(r,h,l,s,count,cost,limit,history,geometry):
        return c.certifier(r,h,l,s,count,cost,geometry,limit,history)
    c.certifier=fail;a._choose_without_observation_guard=invoke
    try:
        try:a.choose_with_joint_feasibility(root,guarded,path,progress,[0],planner(),10000,(0,0),scene.context())
        except RuntimeError as exc:assert str(exc)=='SYNTHETIC_FACTORY_FAILURE'
        else:raise AssertionError('MISSING_FAILURE')
        assert c.certifier is fail
    finally:c.certifier=original_certifier;a._choose_without_observation_guard=choose
    result=dict(status='PASS',checks=['independent_alternate_progress','primary_objective_preserved',
        'both_certificates_required','all_model_work_charged','unsafe_alternate_veto',
        'raw_branch_exact_equivalence','exception_restores_certifier'],
        model_ticks=ticks,native_actions=0,CPU_s=time.process_time()-cpu)
    assert ticks<10000 and result['CPU_s']<30.
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
