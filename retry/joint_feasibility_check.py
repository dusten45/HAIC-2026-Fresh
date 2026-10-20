"""Public synthetic safety, baseline-preservation and probe-lifecycle checks."""
import json
from pathlib import Path
import sys
import time

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'submit_core'))
import observation_agent as a
c=a.core


def main():
    output=Path(sys.argv[1]);assert not output.exists();cpu=time.process_time();ticks=0
    road=((-100.,-100.),(100.,-100.),(100.,200.),(-100.,200.))
    scene=c.Scene([(road,1.)],list(zip(road,road[1:]+road[:1])),[])
    path=dict(points=[[0.,-10.],[0.,0.],[0.,100.]],arcs=[0.,10.,110.],
        ds=[10.,100.],length=110.,launch_squared=[100.,100.,100.],
        periodic_squared=[100.,100.],observed_open=True)
    agent=a.Agent();agent.speed=10.;root=agent._root(scene,0.)
    original_backup=c.backup
    def planner():return dict(force_evaluations=0,forecast_calls=0,forecast_ticks=0,geometry_checks=0)
    # A successful baseline must return identical action/report with no repair.
    counter=[0];cost=planner()
    before,report=a._BASELINE_CHOOSE(root,path,path,10.,counter,cost,10000,(0,0),scene.context())
    ticks+=counter[0];assert before is not None
    counter=[0];cost=planner()
    after,other=a.choose_with_joint_feasibility(root,path,path,10.,counter,cost,10000,(0,0),scene.context())
    ticks+=counter[0];assert np.array_equal(before,after) and report==other
    assert 'joint_backup_checks' not in cost
    # Probe work is charged, but immutable state and original pedals survive.
    counter=[0];cost=planner();expected=a._BASELINE_BACKUP(root,path,path,10.)
    actual=a.force_feasible_backup(counter,cost,10000)(root,path,path,10.)
    assert np.array_equal(expected,actual) and counter[0]==4 and cost['forecast_ticks']==4
    assert root==agent._root(scene,0.);ticks+=counter[0]
    # Every supplemental branch still rejects a current unsafe footprint.
    narrow=((-0.2,-10.),(0.2,-10.),(0.2,110.),(-0.2,110.))
    unsafe=c.Scene([(narrow,1.)],list(zip(narrow,narrow[1:]+narrow[:1])),[])
    bad=agent._root(unsafe,0.);counter=[0];cost=planner()
    rejected,reason=a.choose_with_joint_feasibility(bad,path,path,10.,counter,cost,10000,(0,0),unsafe.context())
    ticks+=counter[0];assert rejected is None and reason['joint_fallback']
    assert all(t['reason']=='CURRENT_FOOTPRINT_MARGIN' for t in reason['trials'])
    # Any exception inside a supplemental forecast must restore original backup.
    original_certifier=c.certifier
    before_exception_ticks=ticks
    def fail(*args,**kwargs):
        def certify(action):
            assert action.dtype==np.float32 and abs(action[0])<=.4
            assert 0<=action[1]<=1 and 0<=action[2]<=1 and not action[1]*action[2]
            raise RuntimeError('SYNTHETIC_PROBE_FAILURE')
        return certify
    c.certifier=fail
    try:
        tilted=c.replace(root,planar=c.replace(root.planar,joints=(.1,.1,0.,0.)))
        try:a.joint_feasibility_fallback(tilted,path,path,10.,[0],planner(),10000,(0,0),scene.context(),dict(mode='NO_ADMISSIBLE_ACTION'))
        except RuntimeError as exc:assert str(exc)=='SYNTHETIC_PROBE_FAILURE'
        else:raise AssertionError('MISSING_FAILURE')
    finally:c.certifier=original_certifier
    assert c.backup is original_backup
    # An exhausted computational budget cannot be bypassed by backup probes.
    counter=a._TickCounter();counter.limit=2;cost=planner()
    try:a.force_feasible_backup(counter,cost,10000)(root,path,path,10.)
    except RuntimeError as exc:assert str(exc)=='ADAPTER_MODEL_TICK_BUDGET'
    else:raise AssertionError('BUDGET_NOT_ENFORCED')
    ticks+=counter[0];assert counter[0]==2
    assert c.HORIZON==12 and c.EXTERNAL_ADMISSION==1.06 and c.FORCE_BUFFER==.001
    assert c.ADMISSION==c.EXTERNAL_ADMISSION-c.FORCE_BUFFER and c.FOOTPRINT_ADMISSION==.5
    result=dict(status='PASS',checks=['successful_baseline_unchanged','original_backup_identity',
        'probe_cost_and_state_immutability','unsafe_road_rejected','exception_restores_backup',
        'action_domain','probe_budget_enforced','original_safety_constants'],
        model_ticks=ticks,deterministic_prefix_before_exception_ticks=before_exception_ticks,
        native_actions=0,CPU_s=time.process_time()-cpu)
    assert ticks<10000 and result['CPU_s']<30.
    output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))


if __name__=='__main__':main()
